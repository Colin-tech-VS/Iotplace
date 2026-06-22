"""Fail the Scalingo release phase if CRM admin credentials are missing in production."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def main():
    is_prod = os.environ.get("FLASK_ENV") == "production" or os.environ.get("SCALINGO_APP")
    if not is_prod:
        return 0

    username = (os.environ.get("CRM_ADMIN_USERNAME") or "").strip()
    password = (os.environ.get("CRM_ADMIN_PASSWORD") or "").strip()
    password_hash = (os.environ.get("CRM_ADMIN_PASSWORD_HASH") or "").strip()

    if not (username and (password or password_hash)):
        print(
            "ERROR: CRM_ADMIN_USERNAME and CRM_ADMIN_PASSWORD (or CRM_ADMIN_PASSWORD_HASH) "
            "must be set in Scalingo environment variables.",
            file=sys.stderr,
        )
        print(
            "Do not put them in scalingo.json with an empty value — that wipes them on deploy.",
            file=sys.stderr,
        )
        return 1

    print("CRM admin credentials: OK")

    from payments import stripe_service

    if stripe_service.is_checkout_ready():
        print("Stripe payments: OK (secret + publishable keys)")
        if not stripe_service.is_webhook_configured():
            print(
                "WARNING: STRIPE_WEBHOOK_SECRET missing — checkout success URL still works, "
                "but invoice/subscription webhooks will fail.",
                file=sys.stderr,
            )
    else:
        print(
            "WARNING: STRIPE_SECRET_KEY and STRIPE_PUBLISHABLE_KEY not set — "
            "PoC application payments and Pro checkout will be disabled. "
            "Set them in Scalingo Environment (see scripts/scalingo_stripe.env.example).",
            file=sys.stderr,
        )

    from data.persistence import resolve_backend_name, resolve_database_url, resolve_data_file

    backend = resolve_backend_name()
    if backend not in ("postgres", "supabase"):
        print(
            "WARNING: DATABASE_URL / SUPABASE_URL not set — data is stored in a local JSON file and will NOT "
            "persist across Scalingo deploys or restarts. Add Scalingo PostgreSQL or Supabase "
            "(DATABASE_URL / SUPABASE_DB_URL / SUPABASE_URL+SUPABASE_KEY).",
            file=sys.stderr,
        )
        data_file = resolve_data_file()
        print(f"WARNING: JSON path: {data_file}", file=sys.stderr)
        return 0

    if backend == "postgres":
        if not resolve_database_url():
            print("ERROR: postgres backend selected but DATABASE_URL is empty.", file=sys.stderr)
            return 1
        print("Persistent storage: PostgreSQL (Supabase-ready)")
        return 0

    from data.persistence import resolve_supabase_rest_config

    if not resolve_supabase_rest_config():
        print("ERROR: supabase backend selected but SUPABASE_URL / SUPABASE_KEY are empty.", file=sys.stderr)
        return 1

    print("Persistent storage: Supabase REST API")
    return 0


if __name__ == "__main__":
    sys.exit(main())
