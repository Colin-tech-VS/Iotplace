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
            "sector_id": "smart_cities",
            "country": "France",
            "city": "Paris",
            "has_project": "yes",
            "project_title": "PoC capteurs",
            "project_engagement_phase": "poc",
            "project_description": "Test flow",
            "project_budget": "10000",
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
            "specialty": "Capteurs",
            "sector_id": "industry_40",
            "team_size": "5",
            "projects_done": "2",
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

    if errors:
        print("ÉCHEC flow_check :", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print("flow_check OK — entreprise, startup, candidatures, advisor")
    return 0


if __name__ == "__main__":
    sys.exit(main())
