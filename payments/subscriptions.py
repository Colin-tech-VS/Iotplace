"""Stripe subscriptions — Enterprise Pro plan automation."""

from __future__ import annotations

import os
from typing import Any

from payments import stripe_service
from payments.pricing_plans import ENTERPRISE_PLAN_FREE, ENTERPRISE_PLAN_PRO

PRO_PRICE_LOOKUP_KEY = "iotplace_pro_enterprise_monthly"
PRO_CHECKOUT_TYPE = "pro_subscription"
ACTIVE_SUBSCRIPTION_STATUSES = frozenset({"active", "trialing", "past_due"})
INACTIVE_SUBSCRIPTION_STATUSES = frozenset({
    "canceled",
    "unpaid",
    "incomplete_expired",
    "incomplete",
})


def subscription_grants_pro(status: str | None) -> bool:
    return (status or "").strip() in ACTIVE_SUBSCRIPTION_STATUSES


def get_or_create_pro_price_id() -> str:
    """Resolve Stripe Price for Pro monthly subscription (env or auto-provision)."""
    env_id = (os.environ.get("STRIPE_PRO_PRICE_ID") or "").strip()
    if env_id:
        return env_id

    stripe_service._client()
    import stripe

    prices = stripe.Price.list(lookup_keys=[PRO_PRICE_LOOKUP_KEY], active=True, limit=1)
    if prices.data:
        return prices.data[0].id

    from payments.pricing_plans import get_pricing_numbers

    pro_price_eur = int(get_pricing_numbers()["pro_price_eur"])
    product = stripe.Product.create(
        name="Iotplace Enterprise Pro",
        description="Projets illimités et commission réduite sur les missions IoT.",
        metadata={"iotplace_product": "pro_enterprise"},
    )
    price = stripe.Price.create(
        product=product.id,
        unit_amount=pro_price_eur * 100,
        currency="eur",
        recurring={"interval": "month"},
        lookup_key=PRO_PRICE_LOOKUP_KEY,
        transfer_lookup_key=True,
        metadata={"iotplace_plan": ENTERPRISE_PLAN_PRO},
    )
    return price.id


def create_pro_subscription_checkout(enterprise: dict, user: dict) -> str:
    """Return Stripe Checkout URL for Enterprise Pro subscription."""
    if subscription_grants_pro(enterprise.get("stripe_subscription_status")):
        raise stripe_service.PaymentError("L'offre Pro est déjà active sur ce compte.")

    stripe_service._client()
    import stripe

    customer_id = stripe_service.ensure_enterprise_customer(enterprise, user)
    site = stripe_service._site_url()
    price_id = get_or_create_pro_price_id()

    session = stripe.checkout.Session.create(
        mode="subscription",
        customer=customer_id,
        client_reference_id=enterprise.get("id", ""),
        line_items=[{"price": price_id, "quantity": 1}],
        allow_promotion_codes=True,
        metadata={
            "iotplace_type": PRO_CHECKOUT_TYPE,
            "iotplace_enterprise_id": enterprise.get("id", ""),
            "iotplace_user_id": user.get("id", ""),
        },
        subscription_data={
            "metadata": {
                "iotplace_plan": ENTERPRISE_PLAN_PRO,
                "iotplace_enterprise_id": enterprise.get("id", ""),
            },
        },
        success_url=(
            f"{site}/compte/entreprise/abonnement/succes"
            "?session_id={CHECKOUT_SESSION_ID}"
        ),
        cancel_url=f"{site}/compte/entreprise?billing=cancel",
    )
    return session.url


def create_billing_portal_session(enterprise: dict, user: dict) -> str:
    """Stripe Customer Portal — manage subscription, payment method, invoices."""
    stripe_service._client()
    import stripe

    customer_id = stripe_service.ensure_enterprise_customer(enterprise, user)
    site = stripe_service._site_url()
    portal = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=f"{site}/compte/entreprise",
    )
    return portal.url


def apply_subscription_to_enterprise(enterprise_id: str, subscription: dict) -> dict | None:
    """Sync enterprise plan fields from a Stripe Subscription object."""
    from data import store

    status = (subscription.get("status") or "").strip()
    sub_id = subscription.get("id", "")
    fields: dict[str, Any] = {
        "stripe_subscription_id": sub_id,
        "stripe_subscription_status": status,
    }
    if subscription_grants_pro(status):
        fields["plan"] = ENTERPRISE_PLAN_PRO
    elif status in INACTIVE_SUBSCRIPTION_STATUSES:
        fields["plan"] = ENTERPRISE_PLAN_FREE

    return store.update_enterprise(enterprise_id, fields)


def resolve_enterprise_id_from_subscription(subscription: dict) -> str | None:
    meta = subscription.get("metadata") or {}
    enterprise_id = (meta.get("iotplace_enterprise_id") or "").strip()
    if enterprise_id:
        return enterprise_id

    from data import store

    sub_id = subscription.get("id", "")
    ent = store.get_enterprise_by_subscription_id(sub_id)
    if ent:
        return ent["id"]

    customer_id = subscription.get("customer")
    if isinstance(customer_id, dict):
        customer_id = customer_id.get("id")
    if customer_id:
        ent = store.get_enterprise_by_stripe_customer(str(customer_id))
        if ent:
            return ent["id"]
    return None


def handle_subscription_event(subscription: dict) -> dict[str, Any]:
    enterprise_id = resolve_enterprise_id_from_subscription(subscription)
    if not enterprise_id:
        return {"ok": False, "reason": "enterprise_not_found"}

    updated = apply_subscription_to_enterprise(enterprise_id, subscription)
    return {
        "ok": True,
        "enterprise_id": enterprise_id,
        "plan": (updated or {}).get("plan"),
        "status": subscription.get("status"),
    }


def complete_checkout_subscription(session: dict) -> dict[str, Any]:
    """Finalize Pro plan after subscription Checkout."""
    if (session.get("metadata") or {}).get("iotplace_type") != PRO_CHECKOUT_TYPE:
        return {"ok": False, "reason": "not_pro_checkout"}

    if session.get("mode") != "subscription":
        return {"ok": False, "reason": "not_subscription_mode"}

    enterprise_id = (session.get("metadata") or {}).get("iotplace_enterprise_id", "")
    if not enterprise_id:
        enterprise_id = session.get("client_reference_id") or ""

    sub_id = session.get("subscription")
    if not sub_id:
        return {"ok": False, "reason": "missing_subscription"}

    stripe_service._client()
    import stripe

    subscription = stripe.Subscription.retrieve(sub_id)
    if not enterprise_id:
        enterprise_id = resolve_enterprise_id_from_subscription(subscription) or ""

    if not enterprise_id:
        return {"ok": False, "reason": "enterprise_not_found"}

    updated = apply_subscription_to_enterprise(enterprise_id, subscription)
    return {
        "ok": True,
        "enterprise_id": enterprise_id,
        "plan": (updated or {}).get("plan"),
        "subscription_id": sub_id,
    }


def sync_enterprise_subscription(enterprise: dict) -> dict | None:
    """Refresh plan from Stripe if a subscription id is stored."""
    sub_id = (enterprise.get("stripe_subscription_id") or "").strip()
    if not sub_id or not stripe_service.is_configured():
        return enterprise

    stripe_service._client()
    import stripe

    try:
        subscription = stripe.Subscription.retrieve(sub_id)
    except Exception:
        return enterprise

    return apply_subscription_to_enterprise(enterprise["id"], subscription)
