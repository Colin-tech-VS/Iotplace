"""Sector form parsing for registration and profile edits."""

from __future__ import annotations

from data.iot_sectors import is_valid_sector_id


def parse_sector_fields(form_data, translate) -> dict:
    sector_id = (form_data.get("sector_id") or "").strip()
    sector_other = (form_data.get("sector_other") or "").strip()

    if not sector_id:
        return {"sector_id": "", "sector": "", "sector_other": ""}

    if not is_valid_sector_id(sector_id):
        return {"sector_id": "", "sector": "", "sector_other": ""}

    if sector_id == "other":
        label = sector_other or translate("sectors.items.other.name", default="Autres")
        return {"sector_id": sector_id, "sector": label, "sector_other": sector_other}

    label = translate(f"sectors.items.{sector_id}.name", default=sector_id)
    return {"sector_id": sector_id, "sector": label, "sector_other": ""}
