"""Smoke tests — parcours entreprise & startup (exécuter en local ou CI)."""
from __future__ import annotations

import os
import sys
import uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault("FLASK_ENV", "development")
os.environ.setdefault("SECRET_KEY", "flow-check-secret")
os.environ.setdefault("CRM_ADMIN_USERNAME", "flow_admin")
os.environ.setdefault("CRM_ADMIN_PASSWORD", "flow_check_pass_123")


def main() -> int:
    from app import app
    from data import store

    client = app.test_client()
    errors: list[str] = []
    uid = uuid.uuid4().hex[:8]

    public_paths = (
        "/",
        "/pricing",
        "/inscription/entreprise",
        "/inscription/startup",
        "/connexion",
    )
    for path in public_paths:
        r = client.get(path)
        if r.status_code != 200:
            errors.append(f"GET {path} → {r.status_code}")

    email_e = f"ent_{uid}@flow.test"
    r = client.post(
        "/inscription/entreprise",
        data={
            "email": email_e,
            "password": "password123",
            "password_confirm": "password123",
            "company_name": "Flow Test Corp",
            "contact_name": "Jean Dupont",
            "sector_id": "smart_energy",
        },
        follow_redirects=True,
    )
    if "/compte/entreprise" not in r.request.path:
        errors.append(f"Inscription entreprise → {r.status_code} ({r.request.path})")

    r = client.get("/compte/entreprise")
    if r.status_code != 200:
        errors.append(f"Dashboard entreprise → {r.status_code}")

    client.get("/deconnexion")

    email_s = f"st_{uid}@flow.test"
    r = client.post(
        "/inscription/startup",
        data={
            "email": email_s,
            "password": "password123",
            "password_confirm": "password123",
            "startup_name": "Flow IoT Startup",
            "country": "France",
            "sector_id": "asset_tracking",
        },
        follow_redirects=True,
    )
    if "/compte/startup" not in r.request.path:
        errors.append(f"Inscription startup → {r.status_code} ({r.request.path})")

    r = client.get("/compte/startup")
    if r.status_code != 200:
        errors.append(f"Dashboard startup → {r.status_code}")

    open_projects = [p for p in store.get_projects() if p.get("status") == "Ouvert"]
    poc_proj = next((p for p in open_projects if p.get("engagement_phase") == "poc"), None)
    scale_proj = next((p for p in open_projects if p.get("engagement_phase") == "scale"), None)

    if poc_proj:
        pid = poc_proj["id"]
        r = client.post(
            f"/compte/startup/projet/{pid}/postuler",
            data={"message": "Candidature PoC flow check"},
            follow_redirects=False,
        )
        if r.status_code not in (302, 200):
            errors.append(f"Candidature PoC → {r.status_code}")

    if scale_proj:
        pid = scale_proj["id"]
        r = client.post(
            f"/compte/startup/projet/{pid}/postuler",
            data={"message": "Candidature scale flow check"},
            follow_redirects=True,
        )
        if r.status_code != 200:
            errors.append(f"Candidature scale → {r.status_code}")

    r = client.post(
        "/api/advisor/chat",
        json={"message": "Bonjour", "profile": "enterprise"},
        content_type="application/json",
    )
    if r.status_code not in (200, 503):
        errors.append(f"Advisor API → {r.status_code}")

    # ── Suivi d'avancement : la startup publie un point sur une mission active ──
    st_user = store.get_user_by_email(email_s)
    st_profile = store.get_startup_for_user(st_user["id"]) if st_user else None
    ref_proj = scale_proj or poc_proj
    if st_profile and ref_proj:
        eng = store.create_engagement({
            "application_message_id": "",
            "project_id": ref_proj["id"],
            "enterprise_id": ref_proj.get("enterprise_id", ""),
            "startup_id": st_profile["id"],
            "amount_cents": 1_000_000,
            "platform_fee_cents": 100_000,
            "startup_payout_cents": 900_000,
            "currency": "eur",
            "status": "escrowed",
        })
        r = client.post(
            f"/compte/engagements/{eng['id']}/avancement",
            data={"progress_percent": "40", "body": "Prototype firmware livré, tests en cours."},
            follow_redirects=False,
        )
        if r.status_code not in (302, 200):
            errors.append(f"Avancement mission → {r.status_code}")
        updates = store.get_engagement_updates(eng["id"])
        if not updates or updates[0].get("progress_percent") != 40:
            errors.append("Avancement non enregistré")
        refreshed = store.get_engagement(eng["id"])
        if (refreshed or {}).get("progress_percent") != 40:
            errors.append("Progression mission non synchronisée")

    if errors:
        print("ÉCHEC flow_check :", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print("flow_check OK — entreprise, startup, candidatures, advisor, suivi d'avancement")
    return 0


if __name__ == "__main__":
    sys.exit(main())
