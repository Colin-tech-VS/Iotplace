"""Verify Supabase connection and print setup steps if schema is missing."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if os.environ.get("FLASK_ENV") != "production" and not os.environ.get("SCALINGO_APP"):
    try:
        from dotenv import load_dotenv

        load_dotenv(ROOT / ".env")
    except ImportError:
        pass

from data.persistence import (  # noqa: E402
    persistence_info,
    resolve_backend_name,
    resolve_supabase_rest_config,
)


def main() -> int:
    info = persistence_info()
    print(f"backend={info.get('backend')} project={info.get('project', '-')}")

    if resolve_backend_name() != "supabase":
        print("Supabase REST not selected — set SUPABASE_URL and SUPABASE_KEY in .env")
        return 1

    if not resolve_supabase_rest_config():
        print("ERROR: SUPABASE_URL / SUPABASE_KEY missing")
        return 1

    from supabase import create_client

    url, key = resolve_supabase_rest_config()
    client = create_client(url, key)
    try:
        result = client.table("iotplace_state").select("id").limit(1).execute()
        print(f"OK — table iotplace_state reachable ({len(result.data)} row(s))")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}")
        migration = ROOT / "supabase" / "migrations" / "001_iotplace_state.sql"
        print("")
        print("Next steps:")
        print("1. Supabase Dashboard > SQL Editor > New query")
        print(f"2. Paste and run: {migration}")
        print("3. Integrations > Data API > expose table iotplace_state for anon role")
        print("4. Re-run: python scripts/supabase_check.py")
        return 1


if __name__ == "__main__":
    sys.exit(main())
