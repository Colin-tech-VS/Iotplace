"""Apply supabase/migrations/*.sql when SUPABASE_DB_URL or SUPABASE_DB_PASSWORD is set."""

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

from data.persistence import PostgresBackend, resolve_database_url  # noqa: E402


def main() -> int:
    url = resolve_database_url()
    if not url:
        print(
            "supabase_apply_schema: skip — set SUPABASE_DB_URL, DATABASE_URL, or "
            "SUPABASE_DB_PASSWORD (from Supabase Dashboard > Settings > Database).",
            file=sys.stderr,
        )
        print(
            "Alternatively, run supabase/migrations/001_iotplace_state.sql in the Supabase SQL Editor.",
            file=sys.stderr,
        )
        return 1

    migration = ROOT / "supabase" / "migrations" / "001_iotplace_state.sql"
    if not migration.exists():
        print(f"ERROR: missing {migration}", file=sys.stderr)
        return 1

    sql = migration.read_text(encoding="utf-8")
    import psycopg

    backend = PostgresBackend(url)
    with psycopg.connect(url) as conn:
        backend._ensure_schema(conn)
        for statement in _split_sql(sql):
            conn.execute(statement)
        conn.commit()

    print("supabase_apply_schema: OK (iotplace_state schema ready)")
    return 0


def _split_sql(sql: str) -> list[str]:
    statements: list[str] = []
    for chunk in sql.split(";"):
        stmt = chunk.strip()
        if not stmt or stmt.startswith("--"):
            continue
        statements.append(stmt)
    return statements


if __name__ == "__main__":
    sys.exit(main())
