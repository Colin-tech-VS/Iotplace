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
    return bool((os.environ.get("STRIPE_SECRET_KEY") or "").strip())


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
    amount_cents = int(engagement["amount_cents"])
    currency = engagement.get("currency", DEFAULT_CURRENCY)
    description = (
        f"Iotplace — Mission IoT : {project.get('title', 'Projet')} "
        f"(startup : {startup.get('name', '')})"
    )

    stripe.InvoiceItem.create(
        customer=customer_id,
        amount=amount_cents,
        currency=currency,
        description=description,
        metadata={"engagement_id": engagement["id"]},
    )
    invoice = stripe.Invoice.create(
        customer=customer_id,
        collection_method="send_invoice",
        days_until_due=14,
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
        cancel_url=f"{site}/compte/startup/projet/{project['id']}",
    )
    return session


def retrieve_checkout_session(session_id: str) -> Any:
    _client()
    return stripe.checkout.Session.retrieve(session_id)


def handle_webhook_event(payload: bytes, sig_header: str) -> dict[str, Any]:
    _client()
    secret = (os.environ.get("STRIPE_WEBHOOK_SECRET") or "").strip()
    if not secret:
        raise PaymentError("STRIPE_WEBHOOK_SECRET manquant.")

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
        if (session.get("metadata") or {}).get("iotplace_type") == "poc_application":
            from payments import poc_application

            completion = poc_application.complete_from_stripe_session(session)
            result.update(completion)
            result["handled"] = completion.get("ok", False)

    return result
