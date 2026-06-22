"""Scoring and recommendations between startups, enterprises and projects."""

from __future__ import annotations

import re
from typing import Any

# Reason codes returned to templates (translated via i18n)
REASON_SECTOR = "sector"
REASON_SKILLS = "skills"
REASON_NEEDS = "needs"
REASON_SPECIALTY = "specialty"
REASON_DOMAIN = "domain"
REASON_PRIORITY = "priority"

PRO_ENTERPRISE_MATCH_BOOST = 10
PRO_ENTERPRISE_THRESHOLD_REDUCTION = 4

SKILL_ALIASES: dict[str, set[str]] = {
    "firmware": {"firmware", "embedded", "embed", "mcu", "microcontroller", "microcontrôleur", "esp32", "stm32"},
    "lorawan": {"lorawan", "lora", "lpwan", "sigfox", "nb-iot"},
    "mqtt": {"mqtt", "mosquitto", "pubsub"},
    "cloud": {"cloud", "aws", "azure", "gcp", "iot core", "thingsboard"},
    "ai": {"ai", "ml", "machine learning", "edge ai", "ia", "intelligence artificielle"},
    "hardware": {"hardware", "pcb", "capteur", "sensor", "iot device"},
}


def _pro_enterprise_boost(enterprise: dict | None) -> int:
    if not enterprise:
        return 0
    from payments.pricing_plans import is_pro_enterprise

    return PRO_ENTERPRISE_MATCH_BOOST if is_pro_enterprise(enterprise) else 0


def _apply_pro_priority(score: int, reasons: list[dict], enterprise: dict | None) -> tuple[int, list[dict]]:
    boost = _pro_enterprise_boost(enterprise)
    if not boost:
        return score, reasons
    reasons = [{"code": REASON_PRIORITY, "detail": ["Pro"]}, *reasons]
    return min(100, score + boost), reasons


def _normalize_token(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower())


def _token_set(*sources) -> set[str]:
    tokens: set[str] = set()
    for source in sources:
        if not source:
            continue
        if isinstance(source, (list, tuple, set)):
            for item in source:
                if item:
                    tokens.add(_normalize_token(str(item)))
        else:
            for part in re.split(r"[,;/|]", str(source)):
                token = _normalize_token(part)
                if len(token) >= 2:
                    tokens.add(token)
    tokens = {t for t in tokens if t}
    expanded = set(tokens)
    for token in tokens:
        for aliases in SKILL_ALIASES.values():
            if token in aliases:
                expanded |= aliases
            elif any(token in alias or alias in token for alias in aliases if len(alias) >= 3):
                expanded |= aliases
    return expanded


def _overlap(a: set[str], b: set[str]) -> set[str]:
    if not a or not b:
        return set()
    exact = a & b
    if exact:
        return exact
    fuzzy: set[str] = set()
    for ta in a:
        for tb in b:
            if len(ta) >= 3 and len(tb) >= 3 and (ta in tb or tb in ta):
                fuzzy.add(ta)
    return fuzzy


def _sector_match(sector_a: str | None, sector_b: str | None) -> bool:
    if not sector_a or not sector_b:
        return False
    return sector_a.strip().lower() == sector_b.strip().lower()


def _score_overlap(
    left: set[str],
    right: set[str],
    max_points: int,
    reason: str,
    *,
    reason_detail: list[str] | None = None,
) -> tuple[int, list[dict]]:
    shared = _overlap(left, right)
    if not shared:
        return 0, []
    ratio = len(shared) / max(len(left), len(right), 1)
    points = min(max_points, int(max_points * (0.45 + 0.55 * ratio)) + min(3, len(shared) - 1))
    detail = reason_detail if reason_detail is not None else sorted(shared)[:4]
    return points, [{"code": reason, "detail": detail}]


def score_startup_for_project(
    startup: dict,
    project: dict,
    enterprise: dict | None = None,
) -> tuple[int, list[dict]]:
    """Return (score 0-100, reasons) for a startup vs project."""
    ent = enterprise or {}
    score = 0
    reasons: list[dict] = []

    startup_skills = _token_set(
        startup.get("skills"),
        startup.get("specialty"),
        startup.get("sector"),
    )
    project_skills = _token_set(project.get("skills"))
    enterprise_needs = _token_set(ent.get("needs"))

    if _sector_match(startup.get("sector_id"), ent.get("sector_id")):
        score += 25
        reasons.append({"code": REASON_SECTOR, "detail": [ent.get("sector") or startup.get("sector") or ""]})

    pts, r = _score_overlap(startup_skills, project_skills, 40, REASON_SKILLS)
    score += pts
    reasons.extend(r)

    pts, r = _score_overlap(startup_skills, enterprise_needs, 20, REASON_NEEDS)
    score += pts
    reasons.extend(r)

    specialty = _normalize_token(startup.get("specialty") or "")
    haystack = _normalize_token(
        f"{project.get('title', '')} {project.get('description', '')} {' '.join(project.get('skills') or [])}"
    )
    if specialty and len(specialty) >= 3 and specialty in haystack:
        score += 10
        reasons.append({"code": REASON_SPECIALTY, "detail": [startup.get("specialty") or ""]})

    sector_label = _normalize_token(startup.get("sector") or "")
    if sector_label and len(sector_label) >= 3 and sector_label in haystack:
        score += 5
        reasons.append({"code": REASON_DOMAIN, "detail": [startup.get("sector") or ""]})

    if startup.get("featured"):
        score += 3
    rating = float(startup.get("rating") or 0)
    if rating > 0:
        score += min(5, int(rating))

    return min(100, score), reasons


def score_startup_for_enterprise(startup: dict, enterprise: dict) -> tuple[int, list[dict]]:
    """Match startup to enterprise profile (no specific project)."""
    score = 0
    reasons: list[dict] = []

    startup_skills = _token_set(
        startup.get("skills"),
        startup.get("specialty"),
        startup.get("sector"),
    )
    enterprise_needs = _token_set(enterprise.get("needs"))

    if _sector_match(startup.get("sector_id"), enterprise.get("sector_id")):
        score += 35
        reasons.append({"code": REASON_SECTOR, "detail": [enterprise.get("sector") or ""]})

    pts, r = _score_overlap(startup_skills, enterprise_needs, 45, REASON_NEEDS)
    score += pts
    reasons.extend(r)

    besoin = _normalize_token(enterprise.get("besoin") or "")
    if besoin:
        for token in startup_skills:
            if len(token) >= 3 and token in besoin:
                score += 8
                reasons.append({"code": REASON_SKILLS, "detail": [token]})
                break

    if startup.get("featured"):
        score += 3

    return min(100, score), reasons


def _min_project_threshold(project: dict, *, enterprise: dict | None = None) -> int:
    base = 12 if project.get("skills") else 8
    reduction = PRO_ENTERPRISE_THRESHOLD_REDUCTION if _pro_enterprise_boost(enterprise) else 0
    return max(5, base - reduction)


def match_projects_for_startup(
    startup: dict,
    projects: list[dict],
    enterprises_by_id: dict[str, dict],
) -> list[dict]:
    results: list[dict] = []
    for project in projects:
        if project.get("status") != "Ouvert":
            continue
        ent = enterprises_by_id.get(project.get("enterprise_id") or "")
        score, reasons = score_startup_for_project(startup, project, ent)
        score, reasons = _apply_pro_priority(score, reasons, ent)
        if score < _min_project_threshold(project, enterprise=ent):
            continue
        results.append({
            **project,
            "match_score": score,
            "match_reasons": reasons,
            "match_enterprise_sector": (ent or {}).get("sector"),
            "match_enterprise_pro": bool(_pro_enterprise_boost(ent)),
        })
    results.sort(key=lambda item: (-item["match_score"], item.get("title") or ""))
    return results


def _public_startups(startups: list[dict]) -> list[dict]:
    from data.store import _is_vitrine_profile_public

    return [s for s in startups if _is_vitrine_profile_public(s)]


def match_startups_for_enterprise(
    enterprise: dict,
    projects: list[dict],
    startups: list[dict],
    *,
    exclude_startup_ids: set[str] | None = None,
    limit: int = 50,
) -> list[dict]:
    """Best startup match per startup across open enterprise projects."""
    exclude = exclude_startup_ids or set()
    pro_enterprise = _pro_enterprise_boost(enterprise) > 0
    ent_sector = enterprise.get("sector_id")
    open_projects = [
        p for p in projects
        if p.get("enterprise_id") == enterprise.get("id") and p.get("status") == "Ouvert"
    ]
    candidates = _public_startups(startups)
    if ent_sector:
        sector_matched = [s for s in candidates if s.get("sector_id") == ent_sector]
        if sector_matched:
            candidates = sector_matched
    best: dict[str, dict] = {}

    if open_projects:
        for project in open_projects:
            for startup in candidates:
                sid = startup.get("id")
                if not sid or sid in exclude:
                    continue
                score, reasons = score_startup_for_project(startup, project, enterprise)
                if pro_enterprise:
                    score, reasons = _apply_pro_priority(score, reasons, enterprise)
                if score < _min_project_threshold(project, enterprise=enterprise):
                    continue
                prev = best.get(sid)
                if not prev or score > prev["match_score"]:
                    best[sid] = {
                        **startup,
                        "match_score": score,
                        "match_reasons": reasons,
                        "match_project_id": project.get("id"),
                        "match_project_title": project.get("title"),
                    }
    else:
        for startup in candidates:
            sid = startup.get("id")
            if not sid or sid in exclude:
                continue
            score, reasons = score_startup_for_enterprise(startup, enterprise)
            if score < 15:
                continue
            best[sid] = {
                **startup,
                "match_score": score,
                "match_reasons": reasons,
                "match_project_id": None,
                "match_project_title": None,
            }

    results = list(best.values())
    results.sort(key=lambda item: (-item["match_score"], item.get("name") or ""))
    return results[: max(1, limit)]


def match_label_tier(score: int) -> str:
    if score >= 75:
        return "high"
    if score >= 45:
        return "medium"
    return "low"
