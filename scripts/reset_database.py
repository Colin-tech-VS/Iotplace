"""Reset the whole Iotplace state to an empty baseline (DEFAULT_DATA).

Backs up the current state to a timestamped JSON file before wiping.

Usage:
    python scripts/reset_database.py --backup-dir <dir>   # dry-run preview
    python scripts/reset_database.py --backup-dir <dir> --yes   # actually wipe

WARNING: irreversible. Deletes all accounts, projects, messages, engagements.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import sys
from datetime import datetime, timezone
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backup-dir", default=str(ROOT / "backups"))
    parser.add_argument("--yes", action="store_true", help="confirm the wipe")
    args = parser.parse_args()

    from data.persistence import load_state, save_state, persistence_info
    from data.store import DEFAULT_DATA

    info = persistence_info()
    print(f"Backend cible : {info}")

    current = load_state()
    counts = {
        k: len(current.get(k, []))
        for k in ("users", "enterprises", "startups", "projects",
                  "messages", "engagements", "contacts")
        if isinstance(current.get(k), list)
    }
    print(f"État actuel : {counts}")

    backup_dir = Path(args.backup_dir)
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = backup_dir / f"iotplace_state_{stamp}.json"
    with open(backup_path, "w", encoding="utf-8") as handle:
        json.dump(current, handle, ensure_ascii=False, indent=2)
    print(f"Sauvegarde écrite : {backup_path}")

    if not args.yes:
        print("\nDRY-RUN. Rien n'a été effacé. Relancez avec --yes pour réinitialiser.")
        return 0

    save_state(copy.deepcopy(DEFAULT_DATA))
    print("\nOK - Base reinitialisee a DEFAULT_DATA (vide). Repart de 0.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
