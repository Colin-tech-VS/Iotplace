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

    from data.persistence import resolve_backend_name, resolve_database_url, resolve_data_file

    backend = resolve_backend_name()
    if backend != "postgres":
        print(
            "WARNING: DATABASE_URL not set — data is stored in a local JSON file and will NOT "
            "persist across Scalingo deploys or restarts. Add Scalingo PostgreSQL or Supabase "
            "(DATABASE_URL / SUPABASE_DB_URL).",
            file=sys.stderr,
        )
        data_file = resolve_data_file()
        print(f"WARNING: JSON path: {data_file}", file=sys.stderr)
        return 0

    if not resolve_database_url():
        print("ERROR: postgres backend selected but DATABASE_URL is empty.", file=sys.stderr)
        return 1

    print("Persistent storage: PostgreSQL (Supabase-ready)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
