"""Simplify db_migrate — schema only via PostgresBackend."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.persistence import PostgresBackend, resolve_database_url  # noqa: E402


def main() -> int:
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


if __name__ == "__main__":
    sys.exit(main())
