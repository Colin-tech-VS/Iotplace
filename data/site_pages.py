"""Central registry of public vitrine pages for CRM, SEO, sitemap and advisor.

Static pages are listed in STATIC_PAGE_CATALOG. Domain landing pages are
generated automatically from data.iot_sectors — new sectors appear in CRM
without editing this file.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from data.iot_sectors import IOT_SECTOR_IDS

LOCALES_DIR = Path(__file__).resolve().parent.parent / "vitrine" / "locales"

# Editable CMS pages (content in store / content.json)
STATIC_PAGE_CATALOG = [
    {"slug": "home", "name": "Accueil", "path": "/", "vitrine_endpoint": "vitrine.index", "kind": "cms", "group": "vitrine", "sort": 10},
    {"slug": "enterprises", "name": "Entreprises", "path": "/enterprises", "vitrine_endpoint": "vitrine.enterprises", "kind": "cms", "group": "vitrine", "sort": 20},
    {"slug": "startups", "name": "Startups", "path": "/startups", "vitrine_endpoint": "vitrine.startups", "kind": "cms", "group": "vitrine", "sort": 30},
    {"slug": "projects", "name": "Projets", "path": "/projects", "vitrine_endpoint": "vitrine.projects", "kind": "cms", "group": "vitrine", "sort": 40},
    {"slug": "pricing", "name": "Tarifs", "path": "/pricing", "vitrine_endpoint": "vitrine.pricing", "kind": "cms", "group": "vitrine", "sort": 50},
    {"slug": "about", "name": "À propos", "path": "/about", "vitrine_endpoint": "vitrine.about", "kind": "cms", "group": "vitrine", "sort": 60},
    {"slug": "contact", "name": "Contact", "path": "/contact", "vitrine_endpoint": "vitrine.contact", "kind": "cms", "group": "vitrine", "sort": 70},
]

GROUP_LABELS = {
    "vitrine": "Pages vitrine",
    "domaines": "Guides domaines IoT",
}

KIND_LABELS = {
    "cms": "Éditable",
    "locale": "Contenu i18n",
    "domain": "Guide domaine",
}


def domain_page_slug(domain_id: str) -> str:
    return f"domain-{domain_id}"


def parse_domain_page_slug(slug: str | None) -> str | None:
    if not slug or not slug.startswith("domain-"):
        return None
    domain_id = slug[len("domain-") :]
    return domain_id if domain_id in IOT_SECTOR_IDS else None


@lru_cache(maxsize=2)
def _sector_names(locale: str = "fr") -> dict[str, str]:
    path = LOCALES_DIR / f"sectors_{locale}.json"
    if not path.exists():
        path = LOCALES_DIR / "sectors_en.json"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    items = data.get("items") or {}
    return {key: (value.get("name") or key) for key, value in items.items()}


@lru_cache(maxsize=2)
def _domains_catalog(locale: str = "fr") -> dict:
    path = LOCALES_DIR / f"domains_{locale}.json"
    if not path.exists():
        path = LOCALES_DIR / "domains_en.json"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _domain_index_entry() -> dict:
    catalog = _domains_catalog("fr")
    return {
        "slug": "domains",
        "name": catalog.get("index_title") or "Domaines IoT",
        "path": "/domaines",
        "vitrine_endpoint": "vitrine.domains_index",
        "kind": "locale",
        "group": "domaines",
        "sort": 100,
        "editable": False,
    }


def _domain_detail_entries() -> list[dict]:
    from data.domain_pages import all_domain_slugs

    names = _sector_names("fr")
    items = []
    for index, (domain_id, url_slug) in enumerate(all_domain_slugs()):
        items.append({
            "slug": domain_page_slug(domain_id),
            "name": names.get(domain_id, domain_id.replace("_", " ").title()),
            "path": f"/domaines/{url_slug}",
            "vitrine_endpoint": "vitrine.domain_detail",
            "domain_id": domain_id,
            "url_slug": url_slug,
            "kind": "domain",
            "group": "domaines",
            "sort": 110 + index,
            "editable": False,
        })
    return items


def build_page_catalog() -> list[dict]:
    """Full public page list: static CMS pages + auto-generated domain pages."""
    pages: list[dict] = []
    for entry in STATIC_PAGE_CATALOG:
        pages.append({**entry, "editable": True})
    pages.append(_domain_index_entry())
    pages.extend(_domain_detail_entries())
    return sorted(pages, key=lambda p: (p.get("sort", 999), p.get("name", "")))


def get_page_entry(slug: str | None) -> dict | None:
    if not slug:
        return None
    return next((p for p in build_page_catalog() if p["slug"] == slug), None)


def get_pages_by_group() -> list[dict]:
    """Grouped catalog for CRM display."""
    groups: dict[str, list[dict]] = {}
    for page in build_page_catalog():
        group = page.get("group", "vitrine")
        groups.setdefault(group, []).append(page)
    return [
        {"id": group_id, "label": GROUP_LABELS.get(group_id, group_id), "pages": items}
        for group_id, items in sorted(
            groups.items(),
            key=lambda item: item[1][0].get("sort", 999) if item[1] else 999,
        )
    ]


def get_domain_seo_defaults(slug: str, locale: str = "fr") -> dict:
    """SEO defaults for domain hub and domain detail pages (from locale JSON)."""
    catalog = _domains_catalog(locale)
    if slug == "domains":
        return {
            "title": catalog.get("index_seo_title", ""),
            "description": catalog.get("index_seo_description", ""),
            "keywords": catalog.get("index_seo_keywords", ""),
        }
    domain_id = parse_domain_page_slug(slug)
    if not domain_id:
        return {}
    item = (catalog.get("items") or {}).get(domain_id, {})
    return {
        "title": item.get("seo_title", ""),
        "description": item.get("seo_description", ""),
        "keywords": item.get("seo_keywords", ""),
    }


def is_sitemap_page(entry: dict, published: bool = True) -> bool:
    if not published:
        return False
    return entry.get("kind") in ("cms", "locale", "domain")
