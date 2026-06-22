"""Profile form parsing and verification reset helpers."""

from __future__ import annotations

import re

from data import store
from vitrine.i18n import t
from vitrine.sectors import parse_sector_fields


def digits_only(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def enterprise_profile_fields(form) -> dict:
    sector_fields = parse_sector_fields(form, t)
    return {
        "name": form.get("company_name", "").strip(),
        **sector_fields,
        "country": form.get("country", "").strip(),
        "city": form.get("city", "").strip(),
        "company_size": form.get("company_size", "").strip(),
        "contact_name": form.get("contact_name", "").strip(),
        "contact_role": form.get("contact_role", "").strip(),
        "phone": form.get("phone", "").strip(),
        "website": form.get("website", "").strip(),
        "linkedin_url": form.get("linkedin_url", "").strip(),
        "description": form.get("description", "").strip(),
        "besoin": form.get("besoin", "").strip(),
        "needs": store.parse_list_field(form.get("needs")),
        "legal_name": form.get("legal_name", "").strip(),
        "siren": digits_only(form.get("siren", "")),
        "siret": digits_only(form.get("siret", "")),
        "vat_number": form.get("vat_number", "").strip(),
        "annual_iot_budget": form.get("annual_iot_budget", "").strip(),
        "iot_protocols": store.parse_list_field(form.get("iot_protocols")),
        "certifications": store.parse_list_field(form.get("certifications")),
    }


def startup_profile_fields(form) -> dict:
    sector_fields = parse_sector_fields(form, t)
    founded = form.get("founded_year", "").strip()
    return {
        "name": form.get("startup_name", "").strip(),
        **sector_fields,
        "country": form.get("country", "").strip(),
        "flag": form.get("flag", "").strip(),
        "city": form.get("city", "").strip(),
        "contact_name": form.get("contact_name", "").strip(),
        "phone": form.get("phone", "").strip(),
        "specialty": form.get("specialty", "").strip(),
        "team_size": int(form.get("team_size") or 0) or None,
        "projects_done": int(form.get("projects_done") or 0),
        "founded_year": int(founded) if founded.isdigit() else None,
        "availability": form.get("availability", "").strip(),
        "rate_range": form.get("rate_range", "").strip(),
        "website": form.get("website", "").strip(),
        "linkedin_url": form.get("linkedin_url", "").strip(),
        "github_url": form.get("github_url", "").strip(),
        "description": form.get("description", "").strip(),
        "besoin": form.get("besoin", "").strip(),
        "skills": store.parse_list_field(form.get("skills")),
        "legal_name": form.get("legal_name", "").strip(),
        "siren": digits_only(form.get("siren", "")),
        "siret": digits_only(form.get("siret", "")),
        "vat_number": form.get("vat_number", "").strip(),
        "tech_stack": store.parse_list_field(form.get("tech_stack")),
        "hardware_platforms": store.parse_list_field(form.get("hardware_platforms")),
        "cloud_platforms": store.parse_list_field(form.get("cloud_platforms")),
        "certifications": store.parse_list_field(form.get("certifications")),
    }


def maybe_reset_verification(profile: dict, fields: dict) -> dict:
    if profile.get("verification_status") != "verified":
        return fields
    for key in ("name", "legal_name", "siren", "siret"):
        if key in fields and str(fields.get(key) or "") != str(profile.get(key) or ""):
            return {
                **fields,
                "verification_status": "none",
                "verified": False,
                "verification_message": "",
                "verification_ai_summary": "",
            }
    return fields


def user_profile_record(user):
    if user["role"] == "enterprise":
        return store.get_enterprise_for_user(user["id"]), "enterprise", store.update_enterprise_profile
    return store.get_startup_for_user(user["id"]), "startup", store.update_startup_profile


def _filled(value) -> bool:
    if value is None:
        return False
    if isinstance(value, list):
        return len(value) > 0
    return bool(str(value).strip())


def compute_profile_completion(profile: dict, role: str) -> dict:
    """Profile completeness for dashboard UX (percent + checklist)."""
    if role == "enterprise":
        checks = [
            ("logo", _filled(profile.get("logo_url"))),
            ("identity", _filled(profile.get("name")) and _filled(profile.get("sector_id")) and _filled(profile.get("country"))),
            ("description", _filled(profile.get("description"))),
            ("contact", _filled(profile.get("contact_name"))),
            ("web", _filled(profile.get("website")) or _filled(profile.get("linkedin_url"))),
            ("legal", _filled(profile.get("siren")) or _filled(profile.get("siret"))),
            ("verified", bool(profile.get("verified"))),
            ("iot", _filled(profile.get("iot_protocols")) or _filled(profile.get("annual_iot_budget"))),
            ("matching", _filled(profile.get("needs"))),
        ]
    else:
        checks = [
            ("logo", _filled(profile.get("logo_url"))),
            ("identity", _filled(profile.get("name")) and _filled(profile.get("country")) and _filled(profile.get("specialty"))),
            ("description", _filled(profile.get("description"))),
            ("team", _filled(profile.get("team_size"))),
            ("web", _filled(profile.get("website")) or _filled(profile.get("linkedin_url")) or _filled(profile.get("github_url"))),
            ("legal", _filled(profile.get("siren")) or _filled(profile.get("siret"))),
            ("verified", bool(profile.get("verified"))),
            ("tech", _filled(profile.get("tech_stack")) or _filled(profile.get("hardware_platforms"))),
            ("matching", _filled(profile.get("skills"))),
        ]
    done = sum(1 for _key, ok in checks if ok)
    total = len(checks)
    percent = int(round(100 * done / total)) if total else 0
    return {
        "percent": percent,
        "done": done,
        "total": total,
        "checklist": [{"key": key, "done": ok} for key, ok in checks],
    }
