"""Fail the Scalingo release phase if CRM admin credentials are missing in production."""
import os
import sys


def main():
    is_prod = os.environ.get("FLASK_ENV") == "production" or os.environ.get("SCALINGO_APP")
    if not is_prod:
        return 0

    username = (os.environ.get("CRM_ADMIN_USERNAME") or "").strip()
    password = (os.environ.get("CRM_ADMIN_PASSWORD") or "").strip()
    password_hash = (os.environ.get("CRM_ADMIN_PASSWORD_HASH") or "").strip()

    if username and (password or password_hash):
        print("CRM admin credentials: OK")
        return 0

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


if __name__ == "__main__":
    sys.exit(main())
