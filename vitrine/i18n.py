"""Site-wide internationalization (English + French)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from flask import has_request_context, request, session

SUPPORTED_LOCALES = ("en", "fr")
DEFAULT_LOCALE = "en"
LOCALES_DIR = Path(__file__).parent / "locales"

STATUS_LABELS = {
    "en": {
        "Ouvert": "Open",
        "En cours": "In progress",
        "Clôturé": "Closed",
        "Fermé": "Closed",
        "Open": "Open",
        "In progress": "In progress",
        "Closed": "Closed",
    },
    "fr": {
        "Ouvert": "Ouvert",
        "En cours": "En cours",
        "Clôturé": "Clôturé",
        "Fermé": "Fermé",
        "Open": "Ouvert",
        "In progress": "En cours",
        "Closed": "Clôturé",
    },
}


@lru_cache(maxsize=8)
def _load_catalog(locale: str) -> dict:
    path = LOCALES_DIR / f"{locale}.json"
    if not path.exists():
        path = LOCALES_DIR / f"{DEFAULT_LOCALE}.json"
    with open(path, encoding="utf-8") as handle:
        catalog = json.load(handle)
    sectors_path = LOCALES_DIR / f"sectors_{locale}.json"
    if not sectors_path.exists() and locale != DEFAULT_LOCALE:
        sectors_path = LOCALES_DIR / f"sectors_{DEFAULT_LOCALE}.json"
    if sectors_path.exists():
        with open(sectors_path, encoding="utf-8") as handle:
            catalog["sectors"] = json.load(handle)
    return catalog


def get_locale() -> str:
    if not has_request_context():
        return DEFAULT_LOCALE
    lang = request.args.get("lang")
    if lang in SUPPORTED_LOCALES:
        session["locale"] = lang
    loc = session.get("locale", DEFAULT_LOCALE)
    return loc if loc in SUPPORTED_LOCALES else DEFAULT_LOCALE


def locale_url(target_locale: str) -> str:
    if not has_request_context():
        return "/"
    path = request.path
    args = request.args.to_dict(flat=True)
    args["lang"] = target_locale
    query = "&".join(f"{k}={v}" for k, v in args.items())
    return f"{path}?{query}" if query else path


def t(key: str, default: str = "", **kwargs):
    parts = key.split(".")
    locale = get_locale()
    node = _load_catalog(locale)
    for part in parts:
        if not isinstance(node, dict):
            node = None
            break
        node = node.get(part)
    if isinstance(node, list):
        return node
    if node is None and locale != DEFAULT_LOCALE:
        node = _load_catalog(DEFAULT_LOCALE)
        for part in parts:
            if not isinstance(node, dict):
                node = None
                break
            node = node.get(part)
    value = node if isinstance(node, str) else (default or key)
    if kwargs:
        try:
            return value.format(**kwargs)
        except (KeyError, ValueError):
            return value
    return value


def translate_status(status: str) -> str:
    locale = get_locale()
    labels = STATUS_LABELS.get(locale, STATUS_LABELS[DEFAULT_LOCALE])
    return labels.get(status or "", status or "")


def translate_phase(phase: str) -> str:
    if not phase:
        return ""
    key = f"engagement.phases.{phase}.short_label"
    label = t(key, default="")
    if label and label != key:
        return label
    return phase


def inject_i18n_context():
    from data.engagement_phases import ENGAGEMENT_PHASES, STARTUP_JOURNEY_STEPS
    from data.iot_sectors import list_domains_for_template, sector_groups_for_template
    from vitrine import advisor_ai

    return {
        "t": t,
        "locale": get_locale(),
        "translate_status": translate_status,
        "translate_phase": translate_phase,
        "engagement_phases": ENGAGEMENT_PHASES,
        "startup_journey_steps": STARTUP_JOURNEY_STEPS,
        "iot_sector_groups": sector_groups_for_template(t),
        "iot_domains": list_domains_for_template(t),
        "locale_url_en": locale_url("en"),
        "locale_url_fr": locale_url("fr"),
        "advisor_enabled": advisor_ai.is_configured(),
        "advisor_suggestions_enterprise": advisor_ai.get_suggestions("enterprise", get_locale()),
        "advisor_suggestions_startup": advisor_ai.get_suggestions("startup", get_locale()),
    }
