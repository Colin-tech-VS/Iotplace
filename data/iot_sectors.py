"""IoT B2B sectors ranked by market demand (enterprise & startup signup)."""

from __future__ import annotations

IOT_SECTOR_IDS = (
    "industry_40",
    "logistics",
    "energy",
    "smart_buildings",
    "smart_cities",
    "health",
    "mobility",
    "retail",
    "agriculture",
    "security",
    "smart_home",
    "environment",
    "maritime",
    "mining",
    "defense",
    "other",
)

DEMAND_LEVELS = ("very_high", "high", "medium", "lower")

SECTOR_DEMAND: dict[str, str | None] = {
    "industry_40": "very_high",
    "logistics": "very_high",
    "energy": "very_high",
    "smart_buildings": "high",
    "smart_cities": "high",
    "health": "high",
    "mobility": "high",
    "retail": "medium",
    "agriculture": "medium",
    "security": "medium",
    "smart_home": "lower",
    "environment": "lower",
    "maritime": "lower",
    "mining": "lower",
    "defense": "lower",
    "other": None,
}


def sector_demand(sector_id: str | None) -> str | None:
    if not sector_id:
        return None
    return SECTOR_DEMAND.get(sector_id.strip())


def is_valid_sector_id(sector_id: str | None) -> bool:
    return bool(sector_id and sector_id in SECTOR_DEMAND)


def sector_groups_for_template(translate) -> list[dict]:
    """Grouped sectors for <optgroup> rendering (demand high → low, then Other)."""
    buckets: dict[str, list[dict]] = {level: [] for level in DEMAND_LEVELS}
    other_items: list[dict] = []

    for sector_id in IOT_SECTOR_IDS:
        demand = sector_demand(sector_id)
        item = {
            "id": sector_id,
            "demand": demand,
            "name": translate(f"sectors.items.{sector_id}.name", default=sector_id),
            "demand_label": translate(f"sectors.demand.{demand}") if demand else "",
            "tagline": translate(f"sectors.items.{sector_id}.tagline", default=""),
            "applications": translate(f"sectors.items.{sector_id}.applications", default=""),
            "clients": translate(f"sectors.items.{sector_id}.clients", default=""),
        }
        if demand:
            buckets[demand].append(item)
        else:
            other_items.append(item)

    groups = []
    for level in DEMAND_LEVELS:
        if buckets[level]:
            groups.append({
                "demand": level,
                "label": translate(f"sectors.demand.{level}"),
                "items": buckets[level],
            })
    if other_items:
        groups.append({"demand": None, "label": None, "items": other_items})
    return groups
