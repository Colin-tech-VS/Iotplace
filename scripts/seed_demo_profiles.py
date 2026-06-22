"""Seed demo enterprise & startup accounts for marketplace testing.

Usage:
  python scripts/seed_demo_profiles.py
  python scripts/seed_demo_profiles.py --enterprises 50 --startups 50 --with-projects

All accounts share the password below (change in production demos).
"""
from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault("FLASK_ENV", "development")

DEMO_PASSWORD = "DemoIotplace2025!"
EMAIL_DOMAIN = "demo.iotplace.test"

ENTERPRISE_NAMES = [
    "Helios Industrie", "NordGrid Utilities", "Axiom Logistics", "Verdant Foods",
    "PharmaCold SA", "Metro Facilities", "Titan Manufacturing", "EcoPulse Energy",
    "TransRail Europe", "BlueHarbor Shipping", "CoreSteel Group", "AgriSense Coop",
    "UrbanTech Realty", "VoltEdge Networks", "Precision Parts GmbH", "Lumina Retail",
    "HydroNova", "FleetOne Mobility", "BuildSmart Holdings", "FreshChain Europe",
    "MedDevice Corp", "Alpine Energy", "PortLink Operations", "SmartFactory Lyon",
    "GreenTower Assets", "CryoLogix", "OmniProcess", "DataCenter Nord", "RailSense",
    "ChemPlant Solutions", "WindField Ops", "PackTrack International", "CityCare FM",
    "ThermoTrust", "MineGuard Systems", "AeroParts Industries", "SolarGrid France",
    "BeverageFlow", "Warehouse IQ", "PulseHealth Campus", "SteelTrack Logistics",
    "BioReactor Labs", "MobilityHub", "CleanRoom Pharma", "InfraWatch Utilities",
    "FoodGuard Monitoring", "AssetCore Mining", "HVAC United", "ColdStore Prime",
    "NextGen Plant",
]

STARTUP_NAMES = [
    "Sensoria Labs", "LoRaWorks", "EdgePulse", "MeterIQ", "TrackFlow",
    "VibeSense", "TwinFactory", "ModbusBridge", "BeaconTrack", "ColdSense",
    "GridAnalytics", "IoTForge",     "Nebula Sensors", "PredictaIoT", "AirQuality Pro",
    "FleetBeacon", "NanoEdge AI", "BACnet Connect", "RFID Vision", "MQTT Hub",
    "ChainGuard", "BuildSense", "EnergyDash", "VibrationAI", "OPC Link",
    "SmartMeter Co", "UWB Locate", "EnviroLog", "IndustrialML", "LoRaTrack",
    "HVAC Insight", "AssetPulse", "PharmaTemp", "SCADA Sync", "EdgeTwin",
    "PowerScope", "GeoFence IoT", "SensorStack", "MachineWatch", "DataLogger Pro",
    "ConnectEdge", "ThermalGuard", "FleetOS", "BuildingIQ", "AnomalyLab",
    "Modular IoT", "SenseGrid", "PredictOps", "ColdChain AI", "PlatformIoT",
]

COUNTRIES = [
    "France", "Germany", "Belgium", "Switzerland", "Netherlands",
    "Spain", "Italy", "United Kingdom", "Sweden", "Portugal",
]

CITIES = {
    "France": ["Paris", "Lyon", "Marseille", "Toulouse", "Nantes", "Lille"],
    "Germany": ["Berlin", "Munich", "Hamburg", "Frankfurt", "Cologne"],
    "Belgium": ["Brussels", "Antwerp", "Ghent"],
    "Switzerland": ["Zurich", "Geneva", "Basel"],
    "Netherlands": ["Amsterdam", "Rotterdam", "Utrecht"],
    "Spain": ["Madrid", "Barcelona", "Valencia"],
    "Italy": ["Milan", "Turin", "Rome"],
    "United Kingdom": ["London", "Manchester", "Bristol"],
    "Sweden": ["Stockholm", "Gothenburg"],
    "Portugal": ["Lisbon", "Porto"],
}

SECTOR_IDS = (
    "smart_energy",
    "asset_tracking",
    "predictive_maintenance",
    "smart_building",
    "cold_chain_monitoring",
)

SKILLS_BY_SECTOR = {
    "smart_energy": ["LoRaWAN", "MQTT", "Smart Metering", "Modbus", "Energy Dashboard"],
    "asset_tracking": ["GPS Tracking", "BLE Beacon", "RFID", "Geofencing", "RTLS"],
    "predictive_maintenance": ["Vibration Sensors", "Edge AI", "OPC-UA", "SCADA", "Anomaly Detection"],
    "smart_building": ["BACnet", "KNX", "HVAC Monitoring", "Occupancy Analytics", "BMS"],
    "cold_chain_monitoring": ["Temperature Sensors", "LoRaWAN", "Real-Time Alerts", "Data Logger", "Compliance"],
}

NEEDS_BY_SECTOR = {
    "smart_energy": ["Energy Monitoring", "Smart Metering", "ESG Reporting"],
    "asset_tracking": ["Asset Tracking", "Fleet Management", "Supply Chain Visibility"],
    "predictive_maintenance": ["Predictive Maintenance", "Condition Monitoring", "Industrial AI"],
    "smart_building": ["Building Automation", "Facility Management", "Energy Efficiency"],
    "cold_chain_monitoring": ["Cold Chain Monitoring", "Temperature Compliance", "Regulatory Compliance"],
}

PROJECT_TITLES = {
    "smart_energy": "Déploiement compteurs intelligents & dashboard énergie",
    "asset_tracking": "Solution de traçabilité assets industriels",
    "predictive_maintenance": "Maintenance prédictive capteurs vibration",
    "smart_building": "Monitoring HVAC & qualité d'air bâtiment tertiaire",
    "cold_chain_monitoring": "Surveillance chaîne du froid temps réel",
}


def _load_env() -> None:
    try:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(ROOT, ".env"))
    except ImportError:
        pass


def _sector_label(sector_id: str) -> str:
    from vitrine.i18n import t
    return t(f"sectors.items.{sector_id}.name", default=sector_id)


def seed(
    *,
    n_enterprises: int,
    n_startups: int,
    with_projects: bool,
    password: str,
) -> dict:
    import auth
    from data import store
    from data.engagement_phases import phase_defaults

    created = {"enterprises": 0, "startups": 0, "skipped_ent": 0, "skipped_st": 0, "projects": 0}
    pw_hash = auth.hash_password(password)

    for i in range(1, n_enterprises + 1):
        email = f"demo-ent-{i:03d}@{EMAIL_DOMAIN}"
        if store.email_exists(email):
            created["skipped_ent"] += 1
            continue
        sector_id = SECTOR_IDS[(i - 1) % len(SECTOR_IDS)]
        country = COUNTRIES[(i - 1) % len(COUNTRIES)]
        city = CITIES.get(country, ["—"])[(i - 1) % max(1, len(CITIES.get(country, [])))]
        name = ENTERPRISE_NAMES[(i - 1) % len(ENTERPRISE_NAMES)]
        if i > len(ENTERPRISE_NAMES):
            name = f"{name} {i}"

        project_fields = None
        if with_projects:
            phase = "poc" if i % 3 == 0 else ("scale" if i % 3 == 1 else "partnership")
            defaults = phase_defaults(phase)
            project_fields = {
                "title": PROJECT_TITLES[sector_id],
                "description": (
                    f"Projet démo Iotplace — {name} recherche une startup IoT "
                    f"pour {NEEDS_BY_SECTOR[sector_id][0].lower()}."
                ),
                "budget": defaults.get("budget", ""),
                "duration": defaults.get("duration", ""),
                "skills": SKILLS_BY_SECTOR[sector_id][:3],
                "engagement_phase": phase,
            }

        store.register_enterprise_account(
            {"email": email, "password_hash": pw_hash},
            {
                "name": name,
                "sector_id": sector_id,
                "sector": _sector_label(sector_id),
                "sector_other": "",
                "contact_name": f"Contact {name.split()[0]}",
                "email": email,
                "country": country,
                "city": city,
                "description": (
                    f"Groupe industriel démo — besoins {NEEDS_BY_SECTOR[sector_id][0]} "
                    f"et {NEEDS_BY_SECTOR[sector_id][1]}."
                ),
                "needs": NEEDS_BY_SECTOR[sector_id],
            },
            project_fields,
        )
        created["enterprises"] += 1
        if project_fields:
            created["projects"] += 1

    for i in range(1, n_startups + 1):
        email = f"demo-st-{i:03d}@{EMAIL_DOMAIN}"
        if store.email_exists(email):
            created["skipped_st"] += 1
            continue
        sector_id = SECTOR_IDS[(i - 1) % len(SECTOR_IDS)]
        country = COUNTRIES[(i + 2) % len(COUNTRIES)]
        city = CITIES.get(country, ["—"])[(i - 1) % max(1, len(CITIES.get(country, [])))]
        name = STARTUP_NAMES[(i - 1) % len(STARTUP_NAMES)]
        if i > len(STARTUP_NAMES):
            name = f"{name} {i}"
        sector_label = _sector_label(sector_id)
        skills = SKILLS_BY_SECTOR[sector_id]

        store.register_startup_account(
            {"email": email, "password_hash": pw_hash},
            {
                "name": name,
                "sector_id": sector_id,
                "sector": sector_label,
                "sector_other": "",
                "country": country,
                "city": city,
                "specialty": skills[0],
                "skills": skills,
                "team_size": str(4 + (i % 12)),
                "description": (
                    f"Startup IoT démo — expertise {skills[0]}, {skills[1]} "
                    f"et intégrations industrielles."
                ),
                "published": True,
            },
        )
        created["startups"] += 1

    return created


def main() -> int:
    _load_env()
    parser = argparse.ArgumentParser(description="Seed demo Iotplace profiles")
    parser.add_argument("--enterprises", type=int, default=50)
    parser.add_argument("--startups", type=int, default=50)
    parser.add_argument("--with-projects", action="store_true", default=True)
    parser.add_argument("--no-projects", action="store_true", help="Skip demo projects")
    parser.add_argument("--password", default=DEMO_PASSWORD)
    args = parser.parse_args()
    with_projects = args.with_projects and not args.no_projects

    from data.persistence import resolve_backend_name

    backend = resolve_backend_name()
    print(f"Backend: {backend}")
    print(f"Seeding {args.enterprises} enterprises + {args.startups} startups …")

    stats = seed(
        n_enterprises=args.enterprises,
        n_startups=args.startups,
        with_projects=with_projects,
        password=args.password,
    )

    print(
        f"Done — enterprises: {stats['enterprises']} (+{stats['skipped_ent']} skipped), "
        f"startups: {stats['startups']} (+{stats['skipped_st']} skipped), "
        f"projects: {stats['projects']}"
    )
    print(f"Login: demo-ent-001@{EMAIL_DOMAIN} / demo-st-001@{EMAIL_DOMAIN}")
    print(f"Password (all demo accounts): {args.password}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
