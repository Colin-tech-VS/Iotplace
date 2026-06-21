"""One-shot: import data/content.json (or IOTPLACE_DATA_DIR) into PostgreSQL / Supabase."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.persistence import PostgresBackend, resolve_data_file, resolve_database_url  # noqa: E402


def main() -> int:
    url = resolve_database_url()
    if not url:
        print("ERROR: set DATABASE_URL or SUPABASE_DB_URL", file=sys.stderr)
        return 1

    source = resolve_data_file()
    if not source.exists():
        source = Path(__file__).resolve().parents[1] / "data" / "content.json"
    if not source.exists():
        print(f"ERROR: no JSON file at {source}", file=sys.stderr)
        return 1

    with open(source, encoding="utf-8") as handle:
        data = json.load(handle)

    backend = PostgresBackend(url)
    backend.save(data)
    print(f"migrate_json_to_postgres: imported {source} → PostgreSQL ({len(data)} top-level keys)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
