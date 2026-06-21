"""Vitrine internationalization — English is the primary locale."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

DEFAULT_LOCALE = "en"
LOCALES_DIR = Path(__file__).parent / "locales"

STATUS_LABELS = {
    "Ouvert": "Open",
    "En cours": "In progress",
    "Clôturé": "Closed",
    "Fermé": "Closed",
    "Open": "Open",
    "In progress": "In progress",
    "Closed": "Closed",
}


@lru_cache(maxsize=4)
def _load_catalog(locale: str) -> dict:
    path = LOCALES_DIR / f"{locale}.json"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def get_locale() -> str:
    return DEFAULT_LOCALE


def t(key: str, default: str = "", **kwargs) -> str:
    parts = key.split(".")
    node = _load_catalog(DEFAULT_LOCALE)
    for part in parts:
        if not isinstance(node, dict):
            node = None
            break
        node = node.get(part)
    if isinstance(node, list):
        return node
    value = node if isinstance(node, str) else (default or key)
    if kwargs:
        try:
            return value.format(**kwargs)
        except (KeyError, ValueError):
            return value
    return value


def translate_status(status: str) -> str:
    return STATUS_LABELS.get(status or "", status or "")
