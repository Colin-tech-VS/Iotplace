"""URL slugs and helpers for IoT domain landing pages."""

from __future__ import annotations

from data.iot_sectors import IOT_SECTOR_IDS, sector_stars

# SEO-friendly URL slugs (kebab-case)
DOMAIN_SLUGS: dict[str, str] = {
    "smart_energy": "smart-energy",
    "asset_tracking": "asset-tracking",
    "predictive_maintenance": "predictive-maintenance",
    "smart_building": "smart-building",
    "cold_chain_monitoring": "cold-chain-monitoring",
}

SLUG_TO_DOMAIN_ID: dict[str, str] = {v: k for k, v in DOMAIN_SLUGS.items()}


def domain_slug(domain_id: str) -> str:
    return DOMAIN_SLUGS.get(domain_id, domain_id.replace("_", "-"))


def resolve_domain_id(slug: str | None) -> str | None:
    if not slug:
        return None
    normalized = slug.strip().lower()
    if normalized in SLUG_TO_DOMAIN_ID:
        return SLUG_TO_DOMAIN_ID[normalized]
    if normalized in IOT_SECTOR_IDS:
        return normalized
    return None


def all_domain_slugs() -> list[tuple[str, str]]:
    """(domain_id, url_slug) in catalog order."""
    return [(domain_id, DOMAIN_SLUGS[domain_id]) for domain_id in IOT_SECTOR_IDS]


def domain_stars_label(domain_id: str) -> str:
    return "⭐" * sector_stars(domain_id)
