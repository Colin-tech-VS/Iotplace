"""Canonical public site identity — single source of truth for URLs and contact."""

from __future__ import annotations

PRODUCTION_SITE_URL = "https://iotplace.fr"
PRODUCTION_SITE_HOST = "iotplace.fr"
CONTACT_EMAIL = "hello@iotplace.fr"

# Hosts that should 301 to PRODUCTION_SITE_HOST (GET only, production).
ALIASES_TO_CANONICAL = frozenset({
    "www.iotplace.fr",
})


def canonical_host() -> str:
    return PRODUCTION_SITE_HOST


def is_scalingo_host(host: str) -> bool:
    h = (host or "").lower().split(":")[0]
    return h.endswith(".osc-fr1.scalingo.io") or h.endswith(".scalingo.io")
