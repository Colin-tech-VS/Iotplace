"""Reset a stuck escrow engagement so a fresh invoice can be generated.

Usage:
    python scripts/reset_engagement_invoice.py            # list engagements
    python scripts/reset_engagement_invoice.py <eng_id>   # reset one engagement

Clears the Stripe invoice references and puts the engagement back to "draft"
so the enterprise can regenerate a correct escrow invoice. Safe to run on
Scalingo: `scalingo --app iotplace run python scripts/reset_engagement_invoice.py <id>`
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault("FLASK_ENV", "development")


def main() -> int:
    from data import store

    engagements = store._load_raw().get("engagements", [])

    if len(sys.argv) < 2:
        if not engagements:
            print("Aucun engagement.")
            return 0
        print(f"{len(engagements)} engagement(s) :")
        for e in engagements:
            print(
                f"  {e['id']}  status={e.get('status'):<16} "
                f"amount={(e.get('amount_cents') or 0) / 100:.2f} € "
                f"invoice={e.get('stripe_invoice_id')}"
            )
        print("\nRelancez avec un id pour réinitialiser : "
              "python scripts/reset_engagement_invoice.py <eng_id>")
        return 0

    eng_id = sys.argv[1].strip()
    engagement = store.get_engagement(eng_id)
    if not engagement:
        print(f"Engagement introuvable : {eng_id}")
        return 1

    store.update_engagement(eng_id, {
        "status": "draft",
        "stripe_invoice_id": None,
        "stripe_hosted_invoice_url": None,
        "paid_at": None,
        "notes": "",
    })
    print(
        f"Engagement {eng_id} réinitialisé (status=draft, facture effacée). "
        "L'entreprise peut maintenant régénérer une facture correcte."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
