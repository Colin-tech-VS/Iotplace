"""Simplify db_migrate — schema via PostgreSQL or Supabase REST check."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.persistence import (  # noqa: E402
    PostgresBackend,
    SupabaseRestBackend,
    resolve_backend_name,
    resolve_database_url,
)


def main() -> int:
    backend_name = resolve_backend_name()
    if backend_name == "postgres":
        url = resolve_database_url()
        if not url:
            print("db_migrate: skip (no DATABASE_URL)")
            return 0

        backend = PostgresBackend(url)
        import psycopg

        with psycopg.connect(url) as conn:
            backend._ensure_schema(conn)
            conn.commit()

        print("db_migrate: OK (iotplace_state schema ready)")
        return 0

    if backend_name == "supabase":
        try:
            SupabaseRestBackend().load()
        except Exception as exc:
            print(f"db_migrate: ERROR — {exc}", file=sys.stderr)
            print(
                "Create tables first: run scripts/supabase_apply_schema.py "
                "(needs SUPABASE_DB_PASSWORD) or execute "
                "supabase/migrations/001_iotplace_state.sql in the Supabase SQL Editor.",
                file=sys.stderr,
            )
            return 1

        print("db_migrate: OK (Supabase iotplace_state reachable)")
        return 0

    print("db_migrate: skip (JSON backend)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
