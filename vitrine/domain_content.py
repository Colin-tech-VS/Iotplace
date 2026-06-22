"""Load per-domain SEO landing content from locale catalogs."""

from __future__ import annotations

from vitrine.i18n import _load_catalog, get_locale


def get_domain_item(domain_id: str, locale: str | None = None) -> dict:
    loc = locale or get_locale()
    catalog = _load_catalog(loc)
    return (catalog.get("domains") or {}).get("items", {}).get(domain_id, {})


def get_domains_meta(locale: str | None = None) -> dict:
    loc = locale or get_locale()
    catalog = _load_catalog(loc)
    domains = catalog.get("domains") or {}
    return {k: v for k, v in domains.items() if k != "items"}
