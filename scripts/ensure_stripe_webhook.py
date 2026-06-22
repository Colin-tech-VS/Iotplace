#!/usr/bin/env python3
"""Ensure Stripe webhook endpoint points to the canonical site URL."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

STRIPE_EVENTS = [
    "checkout.session.completed",
    "checkout.session.expired",
    "invoice.paid",
    "invoice.payment_failed",
    "account.updated",
    "customer.subscription.created",
    "customer.subscription.updated",
    "customer.subscription.deleted",
]


def main() -> int:
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass

    from data.store import get_site_url

    secret = (os.environ.get("STRIPE_SECRET_KEY") or "").strip()
    if not secret:
        print("STRIPE_SECRET_KEY missing", file=sys.stderr)
        return 1

    import stripe

    stripe.api_key = secret
    target = f"{get_site_url().rstrip('/')}/webhooks/stripe"
    fallback = "https://iotplace.osc-fr1.scalingo.io/webhooks/stripe"

    endpoints = stripe.WebhookEndpoint.list(limit=50)
    for endpoint in endpoints.data:
        if endpoint.url in (target, fallback):
            print(f"Webhook OK: {endpoint.id} -> {endpoint.url}")
            return 0

    for endpoint in endpoints.data:
        if "iotplace" in (endpoint.url or ""):
            stripe.WebhookEndpoint.delete(endpoint.id)
            print(f"Deleted old webhook: {endpoint.url}")

    for candidate in (target, fallback):
        if candidate == fallback and candidate == target:
            continue
        try:
            created = stripe.WebhookEndpoint.create(url=candidate, enabled_events=STRIPE_EVENTS)
            print(f"Created webhook: {created.id} -> {candidate}")
            print(f"STRIPE_WEBHOOK_SECRET={created.secret}")
            if candidate == fallback and target != fallback:
                print("Note: iotplace.fr not reachable yet — recreate webhook after DNS with:")
                print("  SITE_URL=https://iotplace.fr python scripts/ensure_stripe_webhook.py")
            return 0
        except stripe.error.InvalidRequestError as exc:
            if "publicly accessible" in str(exc) and candidate != fallback:
                print(f"Skip {candidate} (not public yet)")
                continue
            raise

    print("Could not create webhook", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
