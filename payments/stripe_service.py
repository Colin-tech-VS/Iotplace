"""Stripe Connect + invoicing for Iotplace engagements."""

from __future__ import annotations

import os
from typing import Any

import stripe

DEFAULT_CURRENCY = "eur"
DEFAULT_COMMISSION_PERCENT = 10
DEFAULT_POC_APPLICATION_FEE_EUR = 49
DEFAULT_POC_APPLICATION_COMMISSION_PERCENT = 100


class PaymentError(Exception):
    pass


def is_configured() -> bool:
    """Server-side Checkout / Connect — secret key required; publishable recommended."""
    return bool((os.environ.get("STRIPE_SECRET_KEY") or "").strip())


def is_checkout_ready() -> bool:
    """Full payment UX (PoC fee, Pro, escrow invoices)."""
    return is_configured() and bool((os.environ.get("STRIPE_PUBLISHABLE_KEY") or "").strip())


def is_webhook_configured() -> bool:
    return bool((os.environ.get("STRIPE_WEBHOOK_SECRET") or "").strip())


def _client() -> None:
    key = (os.environ.get("STRIPE_SECRET_KEY") or "").strip()
    if not key:
        raise PaymentError("Stripe n'est pas configuré (STRIPE_SECRET_KEY).")
    stripe.api_key = key


def get_publishable_key() -> str:
    return (os.environ.get("STRIPE_PUBLISHABLE_KEY") or "").strip()


def get_commission_percent() -> float:
    raw = os.environ.get("IOTPLACE_COMMISSION_PERCENT", str(DEFAULT_COMMISSION_PERCENT))
    try:
        return float(raw)
    except ValueError:
        return DEFAULT_COMMISSION_PERCENT


def get_pro_commission_percent() -> float:
    raw = os.environ.get("IOTPLACE_PRO_COMMISSION_PERCENT", "7")
    try:
        return float(raw)
    except ValueError:
        return 7.0


def get_commission_percent_for_enterprise(enterprise: dict | None) -> float:
    from payments.pricing_plans import is_pro_enterprise

    if is_pro_enterprise(enterprise):
        return get_pro_commission_percent()
    return get_commission_percent()


def get_poc_application_fee_cents() -> int:
    raw = os.environ.get("IOTPLACE_POC_APPLICATION_FEE_EUR", str(DEFAULT_POC_APPLICATION_FEE_EUR))
    try:
        return int(round(float(raw) * 100))
    except ValueError:
        return int(DEFAULT_POC_APPLICATION_FEE_EUR * 100)


def format_poc_application_fee() -> str:
    cents = get_poc_application_fee_cents()
    euros = cents / 100
    if euros == int(euros):
        return f"{int(euros)} €"
    return f"{euros:.2f} €".replace(".", ",")


def get_poc_application_commission_percent() -> float:
    """Share of the PoC application fee retained by Iotplace (default 100 %)."""
    raw = os.environ.get(
        "IOTPLACE_POC_APPLICATION_COMMISSION_PERCENT",
        str(DEFAULT_POC_APPLICATION_COMMISSION_PERCENT),
    )
    try:
        return float(raw)
    except ValueError:
        return DEFAULT_POC_APPLICATION_COMMISSION_PERCENT


def _site_url() -> str:
    from data import store

    return store.get_site_url() or "http://localhost:5050"


def ensure_enterprise_customer(enterprise: dict, user: dict) -> str:
    _client()
    existing = (enterprise.get("stripe_customer_id") or "").strip()
    if existing:
        return existing

    customer = stripe.Customer.create(
        email=user.get("email", ""),
        name=enterprise.get("name", ""),
        metadata={
            "iotplace_enterprise_id": enterprise.get("id", ""),
            "iotplace_user_id": user.get("id", ""),
        },
    )
    from data import store

    store.update_enterprise(enterprise["id"], {"stripe_customer_id": customer.id})
    return customer.id


def ensure_startup_connect_account(startup: dict, user: dict) -> str:
    _client()
    existing = (startup.get("stripe_connect_account_id") or "").strip()
    if existing:
        return existing

    try:
        account = stripe.Account.create(
            type="express",
            country=_connect_country(startup),
            email=user.get("email", ""),
            capabilities={
                "card_payments": {"requested": True},
                "transfers": {"requested": True},
            },
            business_type="company",
            metadata={
                "iotplace_startup_id": startup.get("id", ""),
                "iotplace_user_id": user.get("id", ""),
            },
        )
    except stripe.error.InvalidRequestError as exc:
        msg = str(exc)
        if "signed up for Connect" in msg or "Connect" in msg:
            raise PaymentError(
                "Stripe Connect n'est pas activé sur le compte plateforme. "
                "Activez-le sur https://dashboard.stripe.com/connect/settings."
            ) from exc
        raise PaymentError(msg) from exc
    from data import store

    store.update_startup(startup["id"], {
        "stripe_connect_account_id": account.id,
        "stripe_onboarding_complete": False,
    })
    return account.id


def _connect_country(startup: dict) -> str:
    mapping = {
        "vietnam": "VN",
        "indonésie": "ID",
        "indonesia": "ID",
        "thaïlande": "TH",
        "thailand": "TH",
        "philippines": "PH",
        "france": "FR",
        "singapore": "SG",
        "singapour": "SG",
    }
    country = (startup.get("country") or "").strip().lower()
    return mapping.get(country, "FR")


def create_connect_onboarding_link(startup: dict, user: dict) -> str:
    _client()
    account_id = ensure_startup_connect_account(startup, user)
    site = _site_url()
    link = stripe.AccountLink.create(
        account=account_id,
        refresh_url=f"{site}/compte/startup/stripe/refresh",
        return_url=f"{site}/compte/startup/stripe/return",
        type="account_onboarding",
    )
    return link.url


def refresh_connect_status(startup: dict) -> bool:
    account_id = (startup.get("stripe_connect_account_id") or "").strip()
    if not account_id or not is_configured():
        return False
    _client()
    account = stripe.Account.retrieve(account_id)
    complete = bool(account.get("charges_enabled") and account.get("payouts_enabled"))
    from data import store

    store.update_startup(startup["id"], {"stripe_onboarding_complete": complete})
    return complete


def create_escrow_invoice(
    engagement: dict,
    enterprise: dict,
    user: dict,
    project: dict,
    startup: dict,
) -> dict[str, Any]:
    """Create and finalize a Stripe invoice for the enterprise (funds held on platform)."""
    _client()
    customer_id = ensure_enterprise_customer(enterprise, user)
    amount_cents = int(engagement.get("amount_cents") or 0)
    if amount_cents <= 0:
        raise PaymentError(
            "Montant de la mission invalide (0 €). Vérifiez le budget du projet "
            "avant de générer la facture de séquestre."
        )
    currency = engagement.get("currency", DEFAULT_CURRENCY)
    description = (
        f"Iotplace — Mission IoT : {project.get('title', 'Projet')} "
        f"(startup : {startup.get('name', '')})"
    )

    # Avoid leaving an orphan/duplicate invoice behind when regenerating: void
    # any previous still-open invoice for this engagement.
    previous_invoice_id = (engagement.get("stripe_invoice_id") or "").strip()
    if previous_invoice_id:
        try:
            previous = stripe.Invoice.retrieve(previous_invoice_id)
            prev_status = previous.get("status")
            if prev_status == "open":
                stripe.Invoice.void_invoice(previous_invoice_id)
            elif prev_status == "draft":
                stripe.Invoice.delete(previous_invoice_id)
        except stripe.error.StripeError:
            pass

    # Create the invoice first, then attach the line item explicitly so the
    # amount can't be dropped: recent Stripe API versions no longer auto-pull
    # pending invoice items, which finalized the escrow invoice at 0 €.
    invoice = stripe.Invoice.create(
        customer=customer_id,
        collection_method="send_invoice",
        days_until_due=14,
        pending_invoice_items_behavior="exclude",
        metadata={
            "engagement_id": engagement["id"],
            "project_id": engagement.get("project_id", ""),
            "startup_id": engagement.get("startup_id", ""),
        },
        description=(
            f"Commission Iotplace : {get_commission_percent_for_enterprise(enterprise):g}% prélevée à la libération des fonds. "
            "Les fonds restent en séquestre jusqu'à validation de la mission."
        ),
    )
    stripe.InvoiceItem.create(
        customer=customer_id,
        invoice=invoice.id,
        amount=amount_cents,
        currency=currency,
        description=description,
        metadata={"engagement_id": engagement["id"]},
    )
    invoice = stripe.Invoice.finalize_invoice(invoice.id)

    from data import store

    store.update_engagement(engagement["id"], {
        "stripe_invoice_id": invoice.id,
        "stripe_hosted_invoice_url": invoice.hosted_invoice_url,
        "status": "pending_payment",
    })
    return {
        "invoice_id": invoice.id,
        "hosted_invoice_url": invoice.hosted_invoice_url,
        "status": invoice.status,
    }


def invoice_is_payable(invoice_id: str) -> bool:
    """True if the invoice still exists, is open and carries a positive amount."""
    invoice_id = (invoice_id or "").strip()
    if not invoice_id or not is_configured():
        return False
    _client()
    try:
        invoice = stripe.Invoice.retrieve(invoice_id)
    except stripe.error.StripeError:
        return False
    if invoice.get("status") != "open":
        return False
    amount_due = int(invoice.get("amount_due") or 0)
    return amount_due > 0


def release_escrow_to_startup(engagement: dict, startup: dict) -> dict[str, Any]:
    """Transfer startup share after mission validation (escrow release)."""
    _client()
    account_id = (startup.get("stripe_connect_account_id") or "").strip()
    if not account_id:
        raise PaymentError("La startup n'a pas terminé l'onboarding Stripe Connect.")
    if not startup.get("stripe_onboarding_complete"):
        refresh_connect_status(startup)
        from data import store as data_store
        startup = data_store.get_startup(startup["id"])
        if not startup.get("stripe_onboarding_complete"):
            raise PaymentError("Le compte Stripe de la startup n'est pas encore activé.")

    payout = int(engagement.get("startup_payout_cents") or 0)
    if payout <= 0:
        raise PaymentError("Montant de versement invalide.")

    transfer = stripe.Transfer.create(
        amount=payout,
        currency=engagement.get("currency", DEFAULT_CURRENCY),
        destination=account_id,
        metadata={
            "engagement_id": engagement["id"],
            "project_id": engagement.get("project_id", ""),
        },
        description=f"Iotplace — paiement mission {engagement.get('project_id', '')}",
    )

    from data import store

    store.update_engagement(engagement["id"], {
        "status": "released",
        "stripe_transfer_id": transfer.id,
        "released_at": store._now().isoformat(),
    })
    return {"transfer_id": transfer.id, "amount_cents": payout}


def create_poc_application_checkout(
    checkout: dict,
    user: dict,
    startup: dict,
    project: dict,
) -> Any:
    """One-time Stripe Checkout for a startup applying to a PoC project."""
    _client()
    site = _site_url()
    fee_cents = int(checkout["amount_cents"])
    session = stripe.checkout.Session.create(
        mode="payment",
        client_reference_id=checkout["id"],
        customer_email=(user.get("email") or "").strip() or None,
        line_items=[{
            "price_data": {
                "currency": checkout.get("currency", DEFAULT_CURRENCY),
                "product_data": {
                    "name": f"Candidature PoC — {project.get('title', 'Projet IoT')}",
                    "description": (
                        "Frais de candidature phase PoC sur Iotplace "
                        f"({startup.get('name', '')})"
                    ),
                },
                "unit_amount": fee_cents,
            },
            "quantity": 1,
        }],
        metadata={
            "iotplace_checkout_id": checkout["id"],
            "iotplace_type": "poc_application",
            "project_id": project.get("id", ""),
            "startup_id": startup.get("id", ""),
        },
        success_url=(
            f"{site}/compte/startup/projet/{project['id']}/candidature/succes"
            "?session_id={CHECKOUT_SESSION_ID}"
        ),
        cancel_url=(
            f"{site}/compte/startup/projet/{project['id']}/candidature/annule"
            "?session_id={CHECKOUT_SESSION_ID}"
        ),
    )
    return session


def retrieve_checkout_session(session_id: str) -> Any:
    _client()
    try:
        return stripe.checkout.Session.retrieve(session_id)
    except stripe.error.StripeError as exc:
        raise PaymentError(str(exc)) from exc


def handle_webhook_event(payload: bytes, sig_header: str) -> dict[str, Any]:
    _client()
    secret = (os.environ.get("STRIPE_WEBHOOK_SECRET") or "").strip()
    if not secret:
        raise PaymentError(
            "STRIPE_WEBHOOK_SECRET manquant. Créez un endpoint webhook vers "
            f"{_site_url().rstrip('/')}/webhooks/stripe dans le dashboard Stripe."
        )

    event = stripe.Webhook.construct_event(payload, sig_header, secret)
    from data import store

    result = {"type": event["type"], "handled": False}

    if event["type"] == "invoice.paid":
        invoice = event["data"]["object"]
        engagement_id = (invoice.get("metadata") or {}).get("engagement_id")
        if engagement_id:
            store.update_engagement(engagement_id, {
                "status": "escrowed",
                "paid_at": store._now().isoformat(),
                "stripe_invoice_id": invoice.get("id"),
            })
            result["handled"] = True
            result["engagement_id"] = engagement_id

    elif event["type"] == "account.updated":
        account = event["data"]["object"]
        startup = store.get_startup_by_connect_account(account.get("id"))
        if startup:
            complete = bool(account.get("charges_enabled") and account.get("payouts_enabled"))
            store.update_startup(startup["id"], {"stripe_onboarding_complete": complete})
            result["handled"] = True

    elif event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        meta = session.get("metadata") or {}
        if meta.get("iotplace_type") == "poc_application":
            from payments import poc_application

            completion = poc_application.complete_from_stripe_session(session)
            result.update(completion)
            result["handled"] = completion.get("ok", False)
        elif meta.get("iotplace_type") == "pro_subscription" or session.get("mode") == "subscription":
            from payments import subscriptions

            completion = subscriptions.complete_checkout_subscription(session)
            result.update(completion)
            result["handled"] = completion.get("ok", False)

    elif event["type"] == "checkout.session.expired":
        session = event["data"]["object"]
        meta = session.get("metadata") or {}
        if meta.get("iotplace_type") == "poc_application":
            from payments import poc_application

            completion = poc_application.mark_checkout_cancelled(session)
            result.update(completion)
            result["handled"] = completion.get("ok", False)

    elif event["type"] in (
        "customer.subscription.created",
        "customer.subscription.updated",
        "customer.subscription.deleted",
    ):
        from payments import subscriptions

        subscription = event["data"]["object"]
        completion = subscriptions.handle_subscription_event(subscription)
        result.update(completion)
        result["handled"] = completion.get("ok", False)

    elif event["type"] == "invoice.payment_failed":
        invoice = event["data"]["object"]
        subscription_id = invoice.get("subscription")
        if subscription_id:
            from payments import subscriptions

            stripe_sub = stripe.Subscription.retrieve(subscription_id)
            completion = subscriptions.handle_subscription_event(stripe_sub)
            result.update(completion)
            result["handled"] = completion.get("ok", False)

    return result
