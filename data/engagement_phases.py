"""Three-phase enterprise outsourcing model (PoC → scale → partnership)."""

from __future__ import annotations

ENGAGEMENT_PHASES = ("poc", "scale", "partnership")

PHASE_DEFAULTS = {
    "poc": {
        "duration": "3–6 mois",
        "budget": "10k–50k€",
        "budget_cents": 3_000_000,
    },
    "scale": {
        "duration": "6–12 mois",
        "budget": "150k–500k€",
        "budget_cents": 32_500_000,
    },
    "partnership": {
        "duration": "12+ mois",
        "budget": "500k€+",
        "budget_cents": 50_000_000,
    },
}


def normalize_phase(value: str | None) -> str | None:
    if not value:
        return None
    key = (value or "").strip().lower()
    return key if key in ENGAGEMENT_PHASES else None


def phase_defaults(phase: str | None) -> dict:
    return PHASE_DEFAULTS.get(normalize_phase(phase) or "", {})
