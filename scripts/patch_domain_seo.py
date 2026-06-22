#!/usr/bin/env python3
"""Patch domain locale JSON with SEO keyword clusters."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.seo_keywords import (
    DOMAIN_KEYWORDS,
    ENTERPRISE_SOLUTION_CATEGORIES_EN,
    ENTERPRISE_SOLUTION_CATEGORIES_FR,
    TOP_PROJECT_KEYWORDS_EN,
    TOP_PROJECT_KEYWORDS_FR,
    keywords_csv,
)


def patch_domains(path: Path, lang: str) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    top = ", ".join(TOP_PROJECT_KEYWORDS_EN if lang == "en" else TOP_PROJECT_KEYWORDS_FR)
    cats = ENTERPRISE_SOLUTION_CATEGORIES_EN if lang == "en" else ENTERPRISE_SOLUTION_CATEGORIES_FR

    if lang == "en":
        data["index_seo_title"] = (
            "B2B IoT Domains — Predictive Maintenance, Energy Monitoring, Asset Tracking | Iotplace"
        )
        data["index_seo_description"] = (
            "Enterprise guides for Predictive Maintenance, Energy Monitoring, Asset Tracking, Smart Building and "
            "Cold Chain Monitoring. Outsource Industrial IoT, Smart Metering, Condition Monitoring and Industrial AI."
        )
        data["index_seo_keywords"] = keywords_csv(top, "Industrial IoT, B2B IoT marketplace, subcontracting, LoRaWAN, Edge AI")
        data["index_sub"] = (
            "Energy Monitoring Solutions, Predictive Maintenance, Asset Tracking, Smart Building & Cold Chain — "
            "market guides and qualified startup matching on Iotplace."
        )
    else:
        data["index_seo_title"] = (
            "Domaines IoT B2B — Maintenance prédictive, Energy Monitoring, Asset Tracking | Iotplace"
        )
        data["index_seo_description"] = (
            "Guides entreprises : maintenance prédictive, energy monitoring, asset tracking, smart building et cold chain. "
            "Externalisez IoT industriel, smart metering, condition monitoring et IA industrielle."
        )
        data["index_seo_keywords"] = keywords_csv(top, "IoT industriel, marketplace IoT B2B, sous-traitance, LoRaWAN, Edge AI")
        data["index_sub"] = (
            "Solutions Energy Monitoring, Maintenance prédictive, Asset Tracking, Smart Building et Cold Chain — "
            "guides marché et matching startups sur Iotplace."
        )

    seo_titles = {
        "smart_energy": {
            "en": "Energy Monitoring & Smart Metering Solutions — B2B IoT | Iotplace",
            "fr": "Energy Monitoring & Smart Metering — Solutions IoT entreprises | Iotplace",
        },
        "asset_tracking": {
            "en": "Asset Tracking & Fleet Management — RTLS & Supply Chain IoT | Iotplace",
            "fr": "Asset Tracking & Fleet Management — RTLS & supply chain | Iotplace",
        },
        "predictive_maintenance": {
            "en": "Predictive Maintenance & Condition Monitoring — Industrial IoT | Iotplace",
            "fr": "Maintenance prédictive & Condition Monitoring — IoT industriel | Iotplace",
        },
        "smart_building": {
            "en": "Smart Building & Building Automation — HVAC & Occupancy IoT | Iotplace",
            "fr": "Smart Building & Building Automation — HVAC & occupation | Iotplace",
        },
        "cold_chain_monitoring": {
            "en": "Cold Chain Monitoring — Pharma & Food Safety IoT | Iotplace",
            "fr": "Cold Chain Monitoring — Pharma & conformité alimentaire | Iotplace",
        },
    }

    for sid, item in data["items"].items():
        kw = DOMAIN_KEYWORDS[sid]
        ent = kw["enterprise_en" if lang == "en" else "enterprise_fr"]
        st = kw["startup_en" if lang == "en" else "startup_fr"]
        item["name"] = cats[sid]
        item["seo_title"] = seo_titles[sid][lang]
        item["seo_keywords"] = keywords_csv(ent, st, top, "IoT subcontracting, B2B marketplace")
        if lang == "en":
            item["seo_description"] = (
                f"Outsource {cats[sid]}: {ent[:140]}. Match LoRaWAN, MQTT, Modbus and Edge AI startups on Iotplace."
            )[:320]
        else:
            item["seo_description"] = (
                f"Externalisez {cats[sid]} : {ent[:140]}. Startups LoRaWAN, MQTT, Modbus et Edge AI sur Iotplace."
            )[:320]

        extra: list[dict] = []
        if sid == "smart_energy":
            extra = [{
                "q": "Energy Monitoring ou Smart Metering ?" if lang == "fr" else "Energy Monitoring vs Smart Metering?",
                "a": (
                    "Energy Monitoring couvre dashboards, analytics et alerting multi-sites. Smart Metering cible "
                    "compteurs AMI et télérelève. Publiez votre besoin sur Iotplace."
                    if lang == "fr"
                    else "Energy Monitoring covers dashboards, analytics and multi-site alerting. Smart Metering targets AMI meters and remote reading. Publish on Iotplace."
                ),
            }]
        elif sid == "predictive_maintenance":
            extra = [{
                "q": "Comment lancer un projet Predictive Maintenance ?" if lang == "fr" else "How to launch Predictive Maintenance?",
                "a": (
                    "PoC Condition Monitoring sur 10–50 machines : capteurs vibrations, edge AI, SCADA/OPC-UA. "
                    "Publiez le périmètre sur Iotplace."
                    if lang == "fr"
                    else "Condition Monitoring PoC on 10–50 machines: vibration sensors, edge AI, SCADA/OPC-UA. Publish scope on Iotplace."
                ),
            }]
        item["faq"] = extra + (item.get("faq") or [])

    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"patched {path}")


if __name__ == "__main__":
    patch_domains(ROOT / "vitrine/locales/domains_en.json", "en")
    patch_domains(ROOT / "vitrine/locales/domains_fr.json", "fr")
