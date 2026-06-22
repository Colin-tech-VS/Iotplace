"""SEO keyword clusters — enterprise buyers & IoT provider startups."""

from __future__ import annotations

# Top 10 high-intent B2B project keywords (EN)
TOP_PROJECT_KEYWORDS_EN = (
    "Predictive Maintenance",
    "Energy Monitoring",
    "Industrial IoT",
    "Asset Tracking",
    "Smart Metering",
    "Condition Monitoring",
    "Building Automation",
    "Industrial AI",
    "Supply Chain Visibility",
    "Cold Chain Monitoring",
)

TOP_PROJECT_KEYWORDS_FR = (
    "Maintenance prédictive",
    "Energy Monitoring",
    "IoT industriel",
    "Asset Tracking",
    "Smart Metering",
    "Condition Monitoring",
    "Building Automation",
    "IA industrielle",
    "Supply Chain Visibility",
    "Cold Chain Monitoring",
)

ENTERPRISE_SOLUTION_CATEGORIES_EN = {
    "smart_energy": "Energy Monitoring Solutions",
    "predictive_maintenance": "Predictive Maintenance Solutions",
    "asset_tracking": "Asset Tracking Solutions",
    "smart_building": "Smart Building Solutions",
    "cold_chain_monitoring": "Cold Chain Monitoring Solutions",
}

ENTERPRISE_SOLUTION_CATEGORIES_FR = {
    "smart_energy": "Solutions Energy Monitoring",
    "predictive_maintenance": "Solutions Maintenance prédictive",
    "asset_tracking": "Solutions Asset Tracking",
    "smart_building": "Solutions Smart Building",
    "cold_chain_monitoring": "Solutions Cold Chain Monitoring",
}

PROVIDER_CATEGORIES_EN = (
    "LoRaWAN Experts",
    "Industrial IoT Developers",
    "Embedded Systems Engineers",
    "Edge AI Specialists",
    "Smart Metering Providers",
    "Industrial Sensor Integrators",
    "IoT Platform Developers",
)

PROVIDER_CATEGORIES_FR = (
    "Experts LoRaWAN",
    "Développeurs IoT industriel",
    "Ingénieurs systèmes embarqués",
    "Spécialistes Edge AI",
    "Intégrateurs Smart Metering",
    "Intégrateurs capteurs industriels",
    "Développeurs plateforme IoT",
)

DOMAIN_KEYWORDS = {
    "smart_energy": {
        "enterprise_en": (
            "Energy Management, Energy Monitoring, Energy Optimization, Industrial Energy Efficiency, "
            "Smart Metering, Carbon Reduction, ESG Reporting, Sustainability Monitoring, Utility Monitoring, "
            "Energy Analytics, cost reduction, CO2 reduction, ESG compliance"
        ),
        "startup_en": (
            "LoRaWAN, Smart Meter, MQTT, Modbus, BACnet, Energy Dashboard, Edge Computing, "
            "Industrial Sensors, Real-Time Monitoring"
        ),
        "enterprise_fr": (
            "Energy Management, Energy Monitoring, optimisation énergétique, efficacité énergétique industrielle, "
            "Smart Metering, réduction CO₂, reporting ESG, monitoring durabilité, utility monitoring, "
            "energy analytics, réduction des coûts, conformité ESG"
        ),
        "startup_fr": (
            "LoRaWAN, Smart Meter, MQTT, Modbus, BACnet, Energy Dashboard, Edge Computing, "
            "capteurs industriels, monitoring temps réel"
        ),
    },
    "asset_tracking": {
        "enterprise_en": (
            "Asset Tracking, Fleet Management, Supply Chain Visibility, Inventory Tracking, "
            "Warehouse Automation, Logistics Monitoring, Real-Time Location Tracking, RTLS, Connected Assets, "
            "material loss, productivity, logistics visibility"
        ),
        "startup_en": (
            "GPS Tracking, BLE Beacon, LoRaWAN Tracking, RFID, UWB Positioning, Geofencing, Asset Monitoring"
        ),
        "enterprise_fr": (
            "Asset Tracking, Fleet Management, visibilité supply chain, suivi inventaire, "
            "automatisation entrepôt, monitoring logistique, RTLS, actifs connectés, "
            "perte de matériel, productivité, visibilité logistique"
        ),
        "startup_fr": (
            "GPS Tracking, BLE Beacon, LoRaWAN Tracking, RFID, UWB Positioning, Geofencing, Asset Monitoring"
        ),
    },
    "predictive_maintenance": {
        "enterprise_en": (
            "Predictive Maintenance, Condition Monitoring, Industrial Analytics, Machine Health Monitoring, "
            "Equipment Monitoring, Operational Efficiency, Asset Reliability, Industrial AI, "
            "avoid production downtime, reduce maintenance costs"
        ),
        "startup_en": (
            "Vibration Sensors, Edge AI, Industrial IoT, Digital Twin, Machine Learning, Anomaly Detection, "
            "SCADA Integration, OPC-UA"
        ),
        "enterprise_fr": (
            "Maintenance prédictive, Condition Monitoring, analytics industriel, monitoring santé machine, "
            "monitoring équipement, efficacité opérationnelle, fiabilité actifs, IA industrielle, "
            "éviter arrêts production, réduire coûts maintenance"
        ),
        "startup_fr": (
            "Capteurs vibrations, Edge AI, IoT industriel, Digital Twin, Machine Learning, détection anomalies, "
            "intégration SCADA, OPC-UA"
        ),
    },
    "smart_building": {
        "enterprise_en": (
            "Building Automation, Smart Building, Energy Efficiency, Occupancy Analytics, Facility Management, "
            "Building Performance, Indoor Air Quality Monitoring"
        ),
        "startup_en": (
            "BACnet, KNX, Building IoT, HVAC Monitoring, Smart Lighting, Environmental Sensors"
        ),
        "enterprise_fr": (
            "Building Automation, Smart Building, efficacité énergétique, analytics occupation, "
            "Facility Management, performance bâtiment, qualité air intérieur"
        ),
        "startup_fr": (
            "BACnet, KNX, Building IoT, monitoring HVAC, éclairage connecté, capteurs environnementaux"
        ),
    },
    "cold_chain_monitoring": {
        "enterprise_en": (
            "Cold Chain Monitoring, Temperature Compliance, Pharmaceutical Monitoring, Food Safety Monitoring, "
            "Environmental Monitoring, Regulatory Compliance, compliance, audits, quality"
        ),
        "startup_en": (
            "Temperature Sensors, IoT Monitoring, Data Logger, LoRaWAN Sensors, Real-Time Alerts, "
            "Environmental Monitoring"
        ),
        "enterprise_fr": (
            "Cold Chain Monitoring, conformité température, monitoring pharma, sécurité alimentaire, "
            "monitoring environnemental, conformité réglementaire, audits, qualité"
        ),
        "startup_fr": (
            "Capteurs température, monitoring IoT, data logger, capteurs LoRaWAN, alertes temps réel, "
            "monitoring environnemental"
        ),
    },
}


def keywords_csv(*parts: str) -> str:
    seen: set[str] = set()
    out: list[str] = []
    for part in parts:
        for token in part.replace("\n", ",").split(","):
            word = token.strip()
            if word and word.lower() not in seen:
                seen.add(word.lower())
                out.append(word)
    return ", ".join(out)
