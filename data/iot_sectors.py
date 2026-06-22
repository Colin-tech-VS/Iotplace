"""IoT B2B focus domains — Iotplace marketplace."""

from __future__ import annotations

IOT_SECTOR_IDS = (
    "smart_energy",
    "asset_tracking",
    "predictive_maintenance",
    "smart_building",
    "cold_chain_monitoring",
)

DEMAND_LEVELS = ("very_high", "high")

DEMAND_STARS: dict[str, int] = {
    "very_high": 5,
    "high": 4,
}

SECTOR_DEMAND: dict[str, str] = {
    "smart_energy": "very_high",
    "asset_tracking": "very_high",
    "predictive_maintenance": "very_high",
    "smart_building": "high",
    "cold_chain_monitoring": "high",
}


def sector_demand(sector_id: str | None) -> str | None:
    if not sector_id:
        return None
    return SECTOR_DEMAND.get(sector_id.strip())


def sector_stars(sector_id: str | None) -> int:
    demand = sector_demand(sector_id)
    return DEMAND_STARS.get(demand or "", 0)


def is_valid_sector_id(sector_id: str | None) -> bool:
    return bool(sector_id and sector_id in SECTOR_DEMAND)


def list_domains_for_template(translate) -> list[dict]:
    from data.domain_pages import domain_slug

    items = []
    for sector_id in IOT_SECTOR_IDS:
        demand = sector_demand(sector_id)
        stars = DEMAND_STARS.get(demand or "", 0)
        items.append({
            "id": sector_id,
            "slug": domain_slug(sector_id),
            "demand": demand,
            "stars": stars,
            "stars_label": "⭐" * stars,
            "name": translate(f"sectors.items.{sector_id}.name", default=sector_id),
            "tagline": translate(f"sectors.items.{sector_id}.tagline", default=""),
        })
    return sorted(items, key=lambda x: (-x["stars"], x["name"]))


def sector_groups_for_template(translate) -> list[dict]:
    """Flat single group — 5 focus domains only."""
    return [{
        "demand": None,
        "label": None,
        "items": list_domains_for_template(translate),
    }]
