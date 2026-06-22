"""Public pricing plans — amounts from environment, copy from i18n."""

from __future__ import annotations

import os

PLAN_IDS = (
    "free_startup",
    "free_enterprise",
    "commission",
    "pro_enterprise",
)

ENTERPRISE_PLAN_IDS = ("free_enterprise", "commission", "pro_enterprise")
STARTUP_PLAN_IDS = ("free_startup",)

ENTERPRISE_PLAN_FREE = "free_enterprise"
ENTERPRISE_PLAN_PRO = "pro_enterprise"
FREE_ENTERPRISE_MAX_OPEN_PROJECTS = 1


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
    try:
        poc_fee_eur = float(os.environ.get("IOTPLACE_POC_APPLICATION_FEE_EUR", "49"))
    except ValueError:
        poc_fee_eur = 49.0

    from payments import stripe_service

    return {
        "commission_percent": commission,
        "pro_commission_percent": pro_commission,
        "pro_price_eur": pro_price,
        "poc_application_fee_eur": poc_fee_eur,
        "poc_application_fee_label": stripe_service.format_poc_application_fee(),
        "free_enterprise_max_projects": FREE_ENTERPRISE_MAX_OPEN_PROJECTS,
        "plan_ids": PLAN_IDS,
        "enterprise_plan_ids": ENTERPRISE_PLAN_IDS,
        "startup_plan_ids": STARTUP_PLAN_IDS,
    }


def get_enterprise_plan_id(enterprise: dict | None) -> str:
    plan = ((enterprise or {}).get("plan") or ENTERPRISE_PLAN_FREE).strip()
    if plan == ENTERPRISE_PLAN_PRO:
        return ENTERPRISE_PLAN_PRO
    return ENTERPRISE_PLAN_FREE


def is_pro_enterprise(enterprise: dict | None) -> bool:
    if not enterprise:
        return False
    from payments.subscriptions import subscription_grants_pro

    if subscription_grants_pro(enterprise.get("stripe_subscription_status")):
        return True
    sub_id = (enterprise.get("stripe_subscription_id") or "").strip()
    if sub_id:
        return False
    return get_enterprise_plan_id(enterprise) == ENTERPRISE_PLAN_PRO


def build_pricing_page_context(locale: str = "fr") -> dict:
    pricing = get_pricing_numbers()
    comm = int(pricing["commission_percent"])
    pro_comm = int(pricing["pro_commission_percent"])
    pro_price = pricing["pro_price_eur"]
    poc = pricing["poc_application_fee_label"]
    max_proj = pricing["free_enterprise_max_projects"]

    if locale == "fr":
        pricing["compare_rows"] = [
            {"feature": "Abonnement mensuel", "free": "0 €", "commission": "0 €", "pro": f"À partir de {pro_price} €/mois"},
            {"feature": "Projets ouverts", "free": f"{max_proj} actif", "commission": f"{max_proj} actif", "pro": "Illimités"},
            {"feature": "Commission par mission", "free": f"{comm} %", "commission": f"{comm} %", "pro": f"{pro_comm} %"},
            {"feature": "Séquestre & facture auto", "free": "✓", "commission": "✓", "pro": "✓"},
            {"feature": "Matching prioritaire", "free": "—", "commission": "—", "pro": "✓"},
            {"feature": "Support dédié", "free": "—", "commission": "—", "pro": "✓"},
        ]
        pricing["startup_fee_rows"] = [
            {"phase": "PoC", "apply": f"{poc} (Stripe)", "mission": "Séquestre → Stripe Connect à la livraison"},
            {"phase": "Scale", "apply": "Gratuit", "mission": "Séquestre → Stripe Connect à la livraison"},
            {"phase": "Partenariat", "apply": "Gratuit", "mission": "Séquestre → Stripe Connect à la livraison"},
        ]
    else:
        pricing["compare_rows"] = [
            {"feature": "Monthly fee", "free": "€0", "commission": "€0", "pro": f"From €{pro_price}/mo"},
            {"feature": "Open projects", "free": f"{max_proj} active", "commission": f"{max_proj} active", "pro": "Unlimited"},
            {"feature": "Commission per mission", "free": f"{comm}%", "commission": f"{comm}%", "pro": f"{pro_comm}%"},
            {"feature": "Escrow & auto-invoice", "free": "✓", "commission": "✓", "pro": "✓"},
            {"feature": "Priority matching", "free": "—", "commission": "—", "pro": "✓"},
            {"feature": "Dedicated support", "free": "—", "commission": "—", "pro": "✓"},
        ]
        pricing["startup_fee_rows"] = [
            {"phase": "PoC", "apply": f"{poc} (Stripe)", "mission": "Escrow → Stripe Connect on delivery"},
            {"phase": "Scale", "apply": "Free", "mission": "Escrow → Stripe Connect on delivery"},
            {"phase": "Partnership", "apply": "Free", "mission": "Escrow → Stripe Connect on delivery"},
        ]

    return pricing
