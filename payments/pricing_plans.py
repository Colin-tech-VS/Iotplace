"""Public pricing plans — amounts from environment, copy from i18n."""

from __future__ import annotations

import os

PLAN_IDS = (
    "free_startup",
    "free_enterprise",
    "commission",
    "pro_enterprise",
)


def get_pricing_numbers() -> dict:
    try:
        commission = float(os.environ.get("IOTPLACE_COMMISSION_PERCENT", "10"))
    except ValueError:
        commission = 10.0
    try:
        pro_commission = float(os.environ.get("IOTPLACE_PRO_COMMISSION_PERCENT", "7"))
    except ValueError:
        pro_commission = 7.0
    try:
        pro_price = int(os.environ.get("IOTPLACE_PRO_PRICE_EUR", "399"))
    except ValueError:
        pro_price = 399
    return {
        "commission_percent": commission,
        "pro_commission_percent": pro_commission,
        "pro_price_eur": pro_price,
        "plan_ids": PLAN_IDS,
    }
