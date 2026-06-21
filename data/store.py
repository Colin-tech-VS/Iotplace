import json
import os
import uuid
from urllib.parse import quote
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

DATA_FILE = Path(__file__).parent / "content.json"

PAGE_CATALOG = [
    {"slug": "home", "name": "Home", "path": "/", "vitrine_endpoint": "vitrine.index"},
    {"slug": "enterprises", "name": "Enterprises", "path": "/enterprises", "vitrine_endpoint": "vitrine.enterprises"},
    {"slug": "startups", "name": "Startups", "path": "/startups", "vitrine_endpoint": "vitrine.startups"},
    {"slug": "projects", "name": "Projects", "path": "/projects", "vitrine_endpoint": "vitrine.projects"},
    {"slug": "about", "name": "About", "path": "/about", "vitrine_endpoint": "vitrine.about"},
    {"slug": "contact", "name": "Contact", "path": "/contact", "vitrine_endpoint": "vitrine.contact"},
    {"slug": "pricing", "name": "Pricing", "path": "/pricing", "vitrine_endpoint": "vitrine.pricing"},
]

DEFAULT_PAGE_CONTENT = {
    "home": {
        "hero_badge": "B2B IoT Marketplace — Asia × World Subcontracting",
        "hero_title": "IoT subcontracting: connect enterprises and Asian startups",
        "hero_highlight": "IoT subcontracting",
        "hero_subtitle": "Enterprises outsource firmware, hardware and cloud. IoT startups access missions from large groups. Iotplace structures this B2B subcontracting across Southeast Asia.",
        "cta_primary": "I'm an enterprise",
        "cta_secondary": "I'm a startup",
    },
    "enterprises": {
        "title": "Subcontract your IoT projects to qualified startups",
        "subtitle": "Outsource firmware, hardware and cloud to IoT startups in Vietnam, Indonesia and Southeast Asia — quickly and securely.",
    },
    "startups": {
        "title": "IoT startups: find subcontracting missions",
        "subtitle": "Access IoT projects published by large enterprises looking to outsource firmware, PCB, cloud and integration.",
    },
    "projects": {
        "title": "Open IoT subcontracting projects",
        "subtitle": "Missions published by enterprises outsourcing IoT development to qualified startups.",
    },
    "about": {
        "title": "About Iotplace",
        "subtitle": "The platform structuring IoT subcontracting between the West and Southeast Asia.",
        "mission_1": "The Internet of Things is growing exponentially. Large enterprises have massive needs in hardware, firmware and cloud development.",
        "mission_2": "Iotplace bridges this gap with a B2B marketplace dedicated to IoT subcontracting.",
    },
    "contact": {
        "title": "Contact us",
        "subtitle": "Enterprise or IoT startup: start your subcontracting journey on Iotplace.",
        "email": "hello@iotplace.io",
    },
    "pricing": {
        "title": "Pricing & offers",
        "subtitle": "Free to join. Pay only on success — commission on signed IoT missions, optional Pro for high volume.",
    },
}

DEFAULT_PAGE_CONTENT_FR = {
    "home": {
        "hero_badge": "Marketplace IoT B2B — Sous-traitance Asie × Monde",
        "hero_title": "Sous-traitance IoT : connectez entreprises et startups d'Asie",
        "hero_highlight": "Sous-traitance IoT",
        "hero_subtitle": "Les entreprises externalisent firmware, hardware et cloud. Les startups IoT accèdent aux missions des grands groupes. Iotplace structure cette sous-traitance B2B en Asie du Sud-Est.",
        "cta_primary": "Je suis une entreprise",
        "cta_secondary": "Je suis une startup",
    },
    "enterprises": {
        "title": "Sous-traiter vos projets IoT à des startups qualifiées",
        "subtitle": "Externalisez firmware, hardware et cloud vers des startups IoT en Vietnam, Indonésie et Asie du Sud-Est — rapidement et en toute sécurité.",
    },
    "startups": {
        "title": "Startups IoT : trouvez des missions de sous-traitance",
        "subtitle": "Accédez aux projets IoT publiés par les grandes entreprises qui cherchent à externaliser firmware, PCB, cloud et intégration.",
    },
    "projects": {
        "title": "Projets IoT ouverts à la sous-traitance",
        "subtitle": "Missions publiées par les entreprises qui externalisent leur développement IoT vers des startups qualifiées.",
    },
    "about": {
        "title": "À propos d'Iotplace",
        "subtitle": "La plateforme qui structure la sous-traitance IoT entre l'Occident et l'Asie du Sud-Est.",
        "mission_1": "L'Internet des Objets connaît une croissance exponentielle. Les grandes entreprises ont des besoins massifs en développement hardware, firmware et cloud.",
        "mission_2": "Iotplace comble ce fossé en offrant une marketplace B2B dédiée à la sous-traitance IoT.",
    },
    "contact": {
        "title": "Nous contacter",
        "subtitle": "Entreprise ou startup IoT : démarrez votre sous-traitance sur Iotplace.",
        "email": "hello@iotplace.io",
    },
    "pricing": {
        "title": "Tarifs & offres",
        "subtitle": "Inscription gratuite. Payez uniquement au succès — commission sur les missions IoT signées, option Pro pour les gros volumes.",
    },
}

DEFAULT_SEO_PAGES = {
    "home": {
        "title": "B2B IoT Subcontracting — Enterprises & Asian Startups",
        "description": (
            "Iotplace, B2B IoT marketplace: enterprises outsource firmware, hardware and cloud "
            "to qualified startups in Southeast Asia. IoT startups access subcontracting missions "
            "from large enterprises."
        ),
        "keywords": (
            "IoT subcontracting, IoT outsourcing, B2B IoT marketplace, Asian IoT startups, "
            "Vietnam IoT, Indonesia IoT, IoT firmware, connected hardware, enterprise IoT missions"
        ),
    },
    "enterprises": {
        "title": "Outsource your IoT projects — Subcontract startups",
        "description": (
            "IoT enterprise: publish your needs and subcontract firmware, PCB, cloud and integration "
            "to qualified Vietnamese and Asian startups. Matching, contracts and tracking on Iotplace."
        ),
        "keywords": (
            "enterprise IoT subcontracting, IoT project outsourcing, firmware subcontracting, "
            "offshore IoT development, Vietnam IoT startups, IoT client"
        ),
    },
    "startups": {
        "title": "IoT Startups — Enterprise subcontracting missions",
        "description": (
            "IoT startup in Southeast Asia: find subcontracting projects published by "
            "large enterprises — firmware, PCB, LoRaWAN, IoT cloud, hardware integration."
        ),
        "keywords": (
            "IoT startup missions, IoT subcontracting startup, enterprise IoT project, "
            "Vietnam IoT development, connected hardware startup, B2B IoT freelance"
        ),
    },
    "projects": {
        "title": "Open IoT projects — Subcontracting missions",
        "description": (
            "List of open IoT subcontracting projects: firmware, sensors, cloud, "
            "integration. IoT startups, apply to missions published by enterprises on Iotplace."
        ),
        "keywords": (
            "open IoT projects, IoT subcontracting mission, IoT RFP, "
            "firmware startup project, IoT outsourcing budget"
        ),
    },
    "about": {
        "title": "About — B2B IoT subcontracting marketplace",
        "description": (
            "Iotplace structures IoT subcontracting between global enterprises and startups "
            "in Southeast Asia: Vietnam, Indonesia, Thailand, Philippines."
        ),
        "keywords": (
            "IoT marketplace, Asian IoT subcontracting, Vietnam IoT hub, "
            "hardware firmware outsourcing, B2B IoT platform"
        ),
    },
    "contact": {
        "title": "Contact — Start IoT subcontracting",
        "description": (
            "Contact Iotplace: enterprise looking to subcontract an IoT project or IoT startup "
            "looking for missions. Response within 48 hours."
        ),
        "keywords": (
            "IoT subcontracting contact, join IoT marketplace, "
            "publish IoT project, IoT startup signup"
        ),
    },
    "pricing": {
        "title": "Pricing — IoT subcontracting marketplace",
        "description": (
            "Iotplace pricing: free startup access, free enterprise tier, 10% success commission "
            "on signed missions, escrow payments and Enterprise Pro for unlimited projects."
        ),
        "keywords": (
            "IoT marketplace pricing, subcontracting commission, B2B IoT fees, "
            "escrow IoT payment, enterprise Pro outsourcing"
        ),
    },
}

COMPTE_SEO_PAGES = {
    "compte.register_enterprise": {
        "title": "Inscription entreprise — Sous-traiter des startups IoT",
        "description": (
            "Créez votre compte entreprise sur Iotplace : publiez vos projets IoT et "
            "sous-traitez firmware, hardware et cloud à des startups qualifiées en Asie."
        ),
        "keywords": "inscription entreprise IoT, publier projet sous-traitance, externalisation IoT",
        "robots": "index, follow",
    },
    "compte.register_startup": {
        "title": "Inscription startup IoT — Missions de sous-traitance",
        "description": (
            "Inscrivez votre startup IoT sur Iotplace : accédez aux projets de sous-traitance "
            "des grandes entreprises en firmware, PCB, cloud et intégration."
        ),
        "keywords": "inscription startup IoT, missions IoT entreprise, startup Vietnam IoT",
        "robots": "index, follow",
    },
}

PAGE_FAQ = {
    "home": [
        {
            "q": "How can an enterprise subcontract an IoT project on Iotplace?",
            "a": "Create an enterprise account, describe your need (firmware, hardware, cloud) and publish your project. Iotplace connects you with qualified IoT startups in Southeast Asia.",
        },
        {
            "q": "How does an IoT startup find subcontracting missions?",
            "a": "Sign up your startup, list your IoT skills and browse open projects published by enterprises. Apply directly to missions that match your expertise.",
        },
        {
            "q": "What types of IoT projects can be subcontracted?",
            "a": "Embedded firmware, PCB design, connected sensors, LoRaWAN/MQTT protocols, cloud backends, IoT mobile apps and full system integration.",
        },
        {
            "q": "Why outsource to IoT startups in Southeast Asia?",
            "a": "Competitive costs, agile teams, hardware expertise inherited from consumer electronics and favorable time zones for European and American enterprises.",
        },
    ],
    "enterprises": [
        {
            "q": "What are the benefits of outsourcing an IoT project to a startup?",
            "a": "Reduced time-to-market, controlled costs, access to specialized firmware and hardware talent without in-house hiring, with flexibility on mission duration.",
        },
        {
            "q": "How does Iotplace secure IoT subcontracting?",
            "a": "NDAs, structured contracts, project tracking via the platform and secure payments. You keep control over deliverables and intellectual property.",
        },
        {
            "q": "What IoT skills are available among partner startups?",
            "a": "C/C++ firmware, RTOS, PCB design, IoT cloud (AWS, Azure), LoRaWAN, BLE, MQTT, rapid prototyping and small-batch production.",
        },
    ],
    "startups": [
        {
            "q": "How do I access enterprise IoT subcontracting projects?",
            "a": "Create your startup profile on Iotplace, list your skills and browse open projects. Apply to missions that match your technical stack.",
        },
        {
            "q": "What IoT startup profiles are sought after?",
            "a": "Teams skilled in embedded firmware, electronics, IoT cloud or end-to-end integration, ideally based in Vietnam, Indonesia, Thailand or the ASEAN region.",
        },
        {
            "q": "Are missions structured B2B subcontracting?",
            "a": "Yes. Enterprises publish specifications with budget and timeline. Iotplace facilitates matching, contracting and tracking through delivery.",
        },
    ],
    "projects": [
        {
            "q": "How do I apply to an open IoT project?",
            "a": "Create a startup account, complete your profile with your skills and contact the enterprise via Iotplace or apply directly from your dashboard.",
        },
        {
            "q": "Who publishes IoT subcontracting projects?",
            "a": "Large enterprises and industrial groups on Iotplace that outsource part of their IoT development to qualified startups.",
        },
    ],
    "pricing": [
        {
            "q": "Is Iotplace free for startups?",
            "a": "Yes, 100%. Startups never pay a subscription or commission. They receive the mission amount when the enterprise releases escrow funds after delivery validation.",
        },
        {
            "q": "When does the enterprise pay?",
            "a": "When you accept a startup application, Iotplace automatically generates a Stripe invoice. Payment puts funds in escrow until you validate the mission is complete.",
        },
        {
            "q": "What is the commission rate?",
            "a": "10% on each signed mission for Free plans, deducted at fund release. Enterprise Pro reduces this to 7% with unlimited projects.",
        },
        {
            "q": "How does escrow work?",
            "a": "Funds are held securely after invoice payment. The startup is paid via Stripe Connect only when the enterprise confirms delivery — protecting both parties.",
        },
        {
            "q": "Can I try Iotplace without paying?",
            "a": "Yes. Sign up free, publish one project (enterprise) or apply to missions (startup). Commission applies only when a mission is actually signed and paid.",
        },
    ],
}

BREADCRUMB_LABELS = {
    "home": "Home",
    "enterprises": "Enterprises",
    "startups": "IoT Startups",
    "projects": "IoT Projects",
    "about": "About",
    "contact": "Contact",
    "pricing": "Pricing",
}

BREADCRUMB_LABELS_FR = {
    "home": "Accueil",
    "enterprises": "Entreprises",
    "startups": "Startups IoT",
    "projects": "Projets IoT",
    "about": "À propos",
    "contact": "Contact",
    "pricing": "Tarifs",
}

PAGE_FAQ_FR = {
    "home": [
        {"q": "Comment une entreprise peut-elle sous-traiter un projet IoT sur Iotplace ?", "a": "Créez un compte entreprise, décrivez votre besoin (firmware, hardware, cloud) et publiez votre projet. Iotplace vous met en relation avec des startups IoT qualifiées en Asie du Sud-Est."},
        {"q": "Comment une startup IoT trouve-t-elle des missions de sous-traitance ?", "a": "Inscrivez votre startup, renseignez vos compétences IoT et parcourez les projets ouverts publiés par les entreprises."},
        {"q": "Quels types de projets IoT peut-on sous-traiter ?", "a": "Firmware embarqué, conception PCB, capteurs connectés, LoRaWAN/MQTT, backends cloud, applications mobiles IoT et intégration système."},
        {"q": "Pourquoi externaliser vers des startups IoT en Asie du Sud-Est ?", "a": "Coûts compétitifs, équipes agiles, expertise hardware et fuseaux horaires favorables pour les entreprises européennes et américaines."},
    ],
    "enterprises": [
        {"q": "Quels avantages pour externaliser un projet IoT vers une startup ?", "a": "Time-to-market réduit, coûts maîtrisés, accès à des talents firmware et hardware sans recruter en interne."},
        {"q": "Comment Iotplace sécurise la sous-traitance IoT ?", "a": "NDA, contrats encadrés, suivi de projet via la plateforme et paiements sécurisés."},
        {"q": "Quelles compétences IoT sont disponibles ?", "a": "Firmware C/C++, RTOS, PCB design, cloud IoT (AWS, Azure), LoRaWAN, BLE, MQTT, prototypage rapide."},
    ],
    "startups": [
        {"q": "Comment accéder aux projets de sous-traitance IoT ?", "a": "Créez votre profil startup, listez vos compétences et consultez la page Projets ouverts."},
        {"q": "Quels profils de startups IoT sont recherchés ?", "a": "Équipes expertes en firmware, électronique, cloud IoT ou intégration bout-en-bout en Asie du Sud-Est."},
        {"q": "Les missions sont-elles encadrées en B2B ?", "a": "Oui. Les entreprises publient cahier des charges, budget et délais. Iotplace facilite le matching et le suivi."},
    ],
    "projects": [
        {"q": "Comment postuler à un projet IoT ouvert ?", "a": "Créez un compte startup, complétez votre profil et postulez depuis votre tableau de bord."},
        {"q": "Qui publie les projets de sous-traitance IoT ?", "a": "Les grandes entreprises inscrites sur Iotplace qui externalisent leur développement IoT."},
    ],
    "pricing": [
        {"q": "Iotplace est-il gratuit pour les startups ?", "a": "Oui, à 100 %. Aucun abonnement ni commission côté startup. Le paiement arrive quand l'entreprise libère le séquestre après validation de la livraison."},
        {"q": "Quand l'entreprise paie-t-elle ?", "a": "À l'acceptation d'une candidature, Iotplace génère automatiquement une facture Stripe. Le paiement place les fonds en séquestre jusqu'à validation de la mission."},
        {"q": "Quel est le taux de commission ?", "a": "10 % par mission signée sur les offres Gratuit, prélevé à la libération des fonds. L'offre Pro entreprise descend à 7 % avec projets illimités."},
        {"q": "Comment fonctionne le séquestre ?", "a": "Les fonds sont conservés en sécurité après paiement de la facture. La startup est payée via Stripe Connect uniquement quand l'entreprise confirme la livraison."},
        {"q": "Puis-je tester sans payer ?", "a": "Oui. Inscription gratuite, un projet publié (entreprise) ou des candidatures (startup). La commission ne s'applique que lorsqu'une mission est réellement signée et payée."},
    ],
}

DEFAULT_DATA = {
    "enterprises": [],
    "startups": [],
    "projects": [],
    "contacts": [],
    "pages": {},
    "seo": {
        "global": {
            "site_name": "Iotplace",
            "site_url": "",
            "title_suffix": " | Marketplace IoT B2B",
            "meta_description": (
                "Iotplace: B2B IoT subcontracting marketplace. Enterprises outsource projects "
                "to qualified startups in Asia. IoT startups find missions from large enterprises."
            ),
            "keywords": (
                "IoT subcontracting, IoT outsourcing, B2B IoT marketplace, Asian IoT startups, "
                "Vietnam, Indonesia, firmware, connected hardware, IoT missions"
            ),
            "og_image": "",
            "twitter_handle": "",
            "google_analytics_id": "",
        },
        "pages": {},
    },
    "analytics": {
        "total_views": 0,
        "daily": {},
        "hourly": {},
        "pages": {},
        "paths": {},
        "recent": [],
        "sessions": {},
        "unique_visitors": {},
    },
    "social_posts": [],
    "users": [],
    "messages": [],
    "engagements": [],
}


def _deep_merge(base, override):
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _load_raw():
    if not DATA_FILE.exists():
        _save_raw(DEFAULT_DATA.copy())
    with open(DATA_FILE, encoding="utf-8") as f:
        data = json.load(f)
    for key, value in DEFAULT_DATA.items():
        if key not in data:
            data[key] = value
    return data


def _save_raw(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_all():
    return _load_raw()


def get_stats():
    data = _load_raw()
    countries = {s["country"] for s in data["startups"] if s.get("country")}
    return {
        "enterprises": len(data["enterprises"]),
        "startups": len(data["startups"]),
        "projects": len(data["projects"]),
        "countries": len(countries),
    }


# ── Entreprises / Startups / Projets / Contacts ──

def get_enterprises():
    return _load_raw()["enterprises"]


def get_public_enterprises():
    return [e for e in get_enterprises() if e.get("published", True)]


def get_public_startup(startup_id):
    return get_startup(startup_id)


def get_public_enterprise(enterprise_id):
    ent = get_enterprise(enterprise_id)
    if not ent or not ent.get("published", True):
        return None
    return ent


def get_public_project(project_id):
    return get_project(project_id)


def get_startups(country=None):
    startups = _load_raw()["startups"]
    if country:
        startups = [s for s in startups if s.get("country", "").lower() == country.lower()]
    return startups


def get_startup_countries():
    return sorted({s["country"] for s in _load_raw()["startups"] if s.get("country")})


def get_projects():
    return _load_raw()["projects"]


def get_contacts():
    return sorted(_load_raw()["contacts"], key=lambda c: c.get("created_at", ""), reverse=True)


def get_featured_startups(limit=3):
    data = _load_raw()["startups"]
    featured = [s for s in data if s.get("featured")]
    pool = featured if featured else data
    return pool[:limit]


def get_featured_projects(limit=3):
    data = _load_raw()["projects"]
    open_projects = [p for p in data if p.get("status") == "Ouvert"]
    pool = open_projects if open_projects else data
    return pool[:limit]


def _new_id():
    return str(uuid.uuid4())[:8]


def add_enterprise(fields):
    data = _load_raw()
    entry = {"id": _new_id(), **fields}
    data["enterprises"].append(entry)
    _save_raw(data)
    return entry


def update_enterprise(entry_id, fields):
    data = _load_raw()
    for i, ent in enumerate(data["enterprises"]):
        if ent["id"] == entry_id:
            data["enterprises"][i] = {**ent, **fields, "id": entry_id}
            _save_raw(data)
            return data["enterprises"][i]
    return None


def delete_enterprise(entry_id):
    data = _load_raw()
    data["enterprises"] = [e for e in data["enterprises"] if e["id"] != entry_id]
    _save_raw(data)


def add_startup(fields):
    data = _load_raw()
    entry = {"id": _new_id(), **fields}
    data["startups"].append(entry)
    _save_raw(data)
    return entry


def update_startup(entry_id, fields):
    data = _load_raw()
    for i, s in enumerate(data["startups"]):
        if s["id"] == entry_id:
            data["startups"][i] = {**s, **fields, "id": entry_id}
            _save_raw(data)
            return data["startups"][i]
    return None


def delete_startup(entry_id):
    data = _load_raw()
    data["startups"] = [s for s in data["startups"] if s["id"] != entry_id]
    _save_raw(data)


def add_project(fields):
    data = _load_raw()
    entry = {"id": _new_id(), **fields}
    data["projects"].append(entry)
    _save_raw(data)
    return entry


def update_project(entry_id, fields):
    data = _load_raw()
    for i, p in enumerate(data["projects"]):
        if p["id"] == entry_id:
            data["projects"][i] = {**p, **fields, "id": entry_id}
            _save_raw(data)
            return data["projects"][i]
    return None


def delete_project(entry_id):
    data = _load_raw()
    data["projects"] = [p for p in data["projects"] if p["id"] != entry_id]
    _save_raw(data)


def add_contact(fields):
    data = _load_raw()
    entry = {
        "id": _new_id(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        **fields,
    }
    data["contacts"].append(entry)
    _save_raw(data)
    return entry


def delete_contact(entry_id):
    data = _load_raw()
    data["contacts"] = [c for c in data["contacts"] if c["id"] != entry_id]
    _save_raw(data)


def parse_list_field(value):
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _initials(name):
    parts = [p for p in (name or "").split() if p]
    if not parts:
        return "??"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[1][0]).upper()


# ── Utilisateurs / comptes ──

def get_user(user_id):
    return next((u for u in _load_raw().get("users", []) if u["id"] == user_id), None)


def get_user_by_email(email):
    email_l = (email or "").strip().lower()
    return next((u for u in _load_raw().get("users", []) if u.get("email", "").lower() == email_l), None)


def email_exists(email):
    return get_user_by_email(email) is not None


def create_user(email, password_hash, role, profile_id):
    data = _load_raw()
    entry = {
        "id": _new_id(),
        "email": email.strip().lower(),
        "password_hash": password_hash,
        "role": role,
        "profile_id": profile_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    data.setdefault("users", []).append(entry)
    _save_raw(data)
    return entry


def get_enterprise(entry_id):
    return next((e for e in get_enterprises() if e["id"] == entry_id), None)


def get_startup(entry_id):
    return next((s for s in _load_raw()["startups"] if s["id"] == entry_id), None)


def get_enterprise_for_user(user_id):
    ent = next((e for e in get_enterprises() if e.get("user_id") == user_id), None)
    return ent


def get_startup_for_user(user_id):
    return next((s for s in _load_raw()["startups"] if s.get("user_id") == user_id), None)


def get_all_users():
    return _load_raw().get("users", [])


def _short_hash(password_hash):
    h = password_hash or ""
    if len(h) > 56:
        return h[:56] + "…"
    return h


def _enrich_crm_account(user, search=None):
    role = user.get("role")
    profile = None
    profile_name = "—"
    extra = {}

    if role == "enterprise":
        profile = get_enterprise(user.get("profile_id"))
        if profile:
            profile_name = profile.get("name", "—")
            projects = get_projects_for_enterprise(profile["id"], profile.get("name", ""))
            active = [p for p in projects if p.get("status") in ("Ouvert", "En cours")]
            apps = get_applications_for_enterprise(profile["id"])
            extra = {
                "projects": projects,
                "projects_total": len(projects),
                "projects_active": len(active),
                "projects_active_list": active,
                "applications": apps,
                "applications_count": len(apps),
                "published": profile.get("published", False),
                "country": profile.get("country", ""),
                "sector": profile.get("sector", ""),
            }
    elif role == "startup":
        profile = get_startup(user.get("profile_id"))
        if profile:
            profile_name = profile.get("name", "—")
            apps = get_applications_for_startup(profile["id"])
            pending = [a for a in apps if a.get("status") == "pending"]
            extra = {
                "applications": apps,
                "applications_total": len(apps),
                "applications_pending": len(pending),
                "applications_pending_list": pending,
                "featured": profile.get("featured", False),
                "country": profile.get("country", ""),
                "specialty": profile.get("specialty", ""),
                "matching_projects": get_matching_projects_for_startup(profile),
            }

    inbox = get_inbox_for_user(user["id"])
    sent = get_sent_for_user(user["id"])
    entry = {
        "user_id": user["id"],
        "email": user.get("email", ""),
        "password_hash": user.get("password_hash", ""),
        "password_hash_short": _short_hash(user.get("password_hash", "")),
        "role": role,
        "role_label": "Entreprise" if role == "enterprise" else "Startup",
        "profile_id": user.get("profile_id"),
        "profile_name": profile_name,
        "created_at": user.get("created_at", ""),
        "messages_in": inbox,
        "messages_out": sent,
        "messages_in_count": len(inbox),
        "messages_out_count": len(sent),
        "messages_unread": get_unread_count(user["id"]),
        "profile": profile,
        **extra,
    }

    if search:
        q = search.lower()
        haystack = " ".join([
            profile_name, entry["email"], role or "",
            extra.get("country", ""), extra.get("sector", ""), extra.get("specialty", ""),
        ]).lower()
        if q not in haystack:
            return None
    return entry


def get_crm_accounts(search=None):
    accounts = []
    for user in get_all_users():
        entry = _enrich_crm_account(user, search=search)
        if entry:
            accounts.append(entry)
    return sorted(accounts, key=lambda a: a.get("created_at", ""), reverse=True)


def get_crm_account_detail(user_id):
    user = get_user(user_id)
    if not user:
        return None
    return _enrich_crm_account(user)


def get_projects_for_enterprise(enterprise_id, enterprise_name=""):
    projects = get_projects()
    return [
        p for p in projects
        if p.get("enterprise_id") == enterprise_id
        or (enterprise_name and p.get("enterprise") == enterprise_name)
    ]


def register_enterprise_account(user_fields, enterprise_fields, project_fields=None):
    if email_exists(user_fields.get("email")):
        raise ValueError("Cet email est déjà utilisé.")

    name = enterprise_fields.get("name", "").strip()
    enterprise = add_enterprise({
        **enterprise_fields,
        "name": name,
        "logo_initials": enterprise_fields.get("logo_initials") or _initials(name),
        "needs": enterprise_fields.get("needs") or [],
        "published": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    user = create_user(
        user_fields["email"],
        user_fields["password_hash"],
        "enterprise",
        enterprise["id"],
    )
    update_enterprise(enterprise["id"], {"user_id": user["id"]})

    if project_fields and project_fields.get("title"):
        budget = project_fields.get("budget", "")
        add_project({
            "title": project_fields["title"],
            "enterprise": name,
            "enterprise_id": enterprise["id"],
            "description": project_fields.get("description", ""),
            "budget": budget,
            "budget_cents": resolve_budget_cents(budget),
            "currency": "eur",
            "duration": project_fields.get("duration", ""),
            "skills": project_fields.get("skills") or [],
            "status": "Ouvert",
        })

    return user, get_enterprise(enterprise["id"])


def register_startup_account(user_fields, startup_fields):
    if email_exists(user_fields.get("email")):
        raise ValueError("Cet email est déjà utilisé.")

    startup = add_startup({
        **startup_fields,
        "skills": startup_fields.get("skills") or [],
        "featured": False,
        "rating": startup_fields.get("rating") or 0,
        "projects_done": startup_fields.get("projects_done") or 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    user = create_user(
        user_fields["email"],
        user_fields["password_hash"],
        "startup",
        startup["id"],
    )
    update_startup(startup["id"], {"user_id": user["id"]})
    return user, get_startup(startup["id"])


def update_enterprise_profile(entry_id, fields):
    return update_enterprise(entry_id, fields)


def update_startup_profile(entry_id, fields):
    return update_startup(entry_id, fields)


def get_matching_projects_for_startup(startup):
    skills = {s.lower() for s in startup.get("skills", [])}
    if not skills:
        return [p for p in get_projects() if p.get("status") == "Ouvert"]
    matched = []
    for project in get_projects():
        if project.get("status") != "Ouvert":
            continue
        project_skills = {s.lower() for s in project.get("skills", [])}
        if not project_skills or skills & project_skills:
            matched.append(project)
    return matched


def get_project(project_id):
    return next((p for p in get_projects() if p["id"] == project_id), None)


def add_project_for_enterprise(enterprise, fields):
    budget = fields.get("budget", "").strip()
    budget_cents = fields.get("budget_cents") or resolve_budget_cents(budget)
    return add_project({
        "title": fields.get("title", "").strip(),
        "enterprise": enterprise.get("name", ""),
        "enterprise_id": enterprise["id"],
        "description": fields.get("description", "").strip(),
        "budget": budget,
        "budget_cents": budget_cents,
        "currency": fields.get("currency", "eur"),
        "duration": fields.get("duration", "").strip(),
        "skills": fields.get("skills") or [],
        "status": fields.get("status", "Ouvert"),
    })


# ── Messages & candidatures ──

def _profile_name_for_user(user):
    if not user:
        return "Utilisateur"
    if user.get("role") == "enterprise":
        ent = get_enterprise(user.get("profile_id"))
        return ent.get("name", user.get("email", "")) if ent else user.get("email", "")
    startup = get_startup(user.get("profile_id"))
    return startup.get("name", user.get("email", "")) if startup else user.get("email", "")


def _user_for_enterprise_id(enterprise_id):
    ent = get_enterprise(enterprise_id)
    if not ent or not ent.get("user_id"):
        return None
    return get_user(ent["user_id"])


def _user_for_startup_id(startup_id):
    startup = get_startup(startup_id)
    if not startup or not startup.get("user_id"):
        return None
    return get_user(startup["user_id"])


def _thread_key(counterpart_user_id, project_id=None):
    return f"{counterpart_user_id}:{project_id or ''}"


def _is_b2b_message(msg):
    roles = {msg.get("from_role"), msg.get("to_role")}
    return roles == {"enterprise", "startup"}


def users_can_message(from_user, to_user, project_id=None):
    if not from_user or not to_user or from_user["id"] == to_user["id"]:
        return False
    if {from_user.get("role"), to_user.get("role")} != {"enterprise", "startup"}:
        return False

    a, b = from_user["id"], to_user["id"]
    for msg in _load_raw().get("messages", []):
        if _is_b2b_message(msg) and {msg.get("from_user_id"), msg.get("to_user_id")} == {a, b}:
            return True

    if project_id:
        project = get_project(project_id)
        if not project:
            return False
        ent_user = _user_for_enterprise_id(project.get("enterprise_id"))
        if from_user["role"] == "enterprise" and ent_user and ent_user["id"] == from_user["id"]:
            return True
        if from_user["role"] == "startup":
            if startup_already_applied(from_user.get("profile_id"), project_id):
                return True

    if from_user["role"] == "startup":
        for app in get_applications_for_startup(from_user.get("profile_id")):
            project = get_project(app.get("project_id"))
            if not project:
                continue
            ent_user = _user_for_enterprise_id(project.get("enterprise_id"))
            if ent_user and ent_user["id"] == to_user["id"]:
                return True

    if from_user["role"] == "enterprise":
        for app in get_applications_for_enterprise(from_user.get("profile_id")):
            startup_user = _user_for_startup_id(app.get("from_profile_id"))
            if startup_user and startup_user["id"] == to_user["id"]:
                return True

    return False


def serialize_message_api(msg, current_user_id):
    enriched = enrich_message_for_view(msg, current_user_id)
    engagement = get_engagement_by_message(msg["id"]) if msg.get("kind") == "application" else None
    payload = {
        "id": msg["id"],
        "body": msg.get("body", ""),
        "subject": msg.get("subject", ""),
        "kind": msg.get("kind", "contact"),
        "kind_label": enriched["kind_label"],
        "status": msg.get("status", ""),
        "status_label": enriched["status_label"],
        "direction": enriched["direction"],
        "counterpart_name": enriched["counterpart_name"],
        "from_user_id": msg.get("from_user_id"),
        "to_user_id": msg.get("to_user_id"),
        "from_name": msg.get("from_name", ""),
        "to_name": msg.get("to_name", ""),
        "project_id": msg.get("project_id"),
        "project_title": msg.get("project_title", ""),
        "read": bool(msg.get("read")),
        "created_at": msg.get("created_at", ""),
        "is_mine": msg.get("from_user_id") == current_user_id,
    }
    if engagement:
        payload["engagement"] = {
            "id": engagement["id"],
            "status": engagement.get("status"),
            "status_label": format_engagement_label(engagement.get("status")),
            "invoice_url": engagement.get("stripe_hosted_invoice_url"),
            "amount_cents": engagement.get("amount_cents"),
        }
    return payload


def get_conversations(user_id):
    user = get_user(user_id)
    if not user:
        return []

    threads = {}
    for msg in get_messages_for_user(user_id):
        if not _is_b2b_message(msg):
            continue
        counterpart_id = msg["from_user_id"] if msg.get("to_user_id") == user_id else msg["to_user_id"]
        project_id = msg.get("project_id") or ""
        key = _thread_key(counterpart_id, project_id or None)

        counterpart = get_user(counterpart_id)
        if not counterpart:
            continue

        preview = (msg.get("body") or "")[:100]
        last_at = msg.get("created_at", "")

        if key not in threads or last_at > threads[key]["last_at"]:
            threads[key] = {
                "thread_key": key,
                "counterpart_user_id": counterpart_id,
                "counterpart_name": _profile_name_for_user(counterpart),
                "counterpart_role": counterpart.get("role", ""),
                "project_id": project_id or None,
                "project_title": msg.get("project_title", ""),
                "last_message": preview,
                "last_at": last_at,
                "last_kind": msg.get("kind", ""),
                "unread": 0,
            }

    for msg in get_inbox_for_user(user_id):
        if not _is_b2b_message(msg) or msg.get("read"):
            continue
        counterpart_id = msg.get("from_user_id")
        project_id = msg.get("project_id") or ""
        key = _thread_key(counterpart_id, project_id or None)
        if key in threads:
            threads[key]["unread"] += 1

    return sorted(threads.values(), key=lambda t: t["last_at"], reverse=True)


def get_thread_messages(user_id, counterpart_user_id, project_id=None):
    messages = [
        m for m in _load_raw().get("messages", [])
        if _is_b2b_message(m)
        and user_id in (m.get("from_user_id"), m.get("to_user_id"))
        and counterpart_user_id in (m.get("from_user_id"), m.get("to_user_id"))
    ]
    if project_id:
        messages = [m for m in messages if m.get("project_id") == project_id]
    return sorted(messages, key=lambda m: m.get("created_at", ""))


def mark_thread_read(user_id, counterpart_user_id, project_id=None):
    data = _load_raw()
    changed = False
    for i, msg in enumerate(data.get("messages", [])):
        if (
            msg.get("to_user_id") == user_id
            and msg.get("from_user_id") == counterpart_user_id
            and not msg.get("read")
            and _is_b2b_message(msg)
        ):
            if project_id is None or msg.get("project_id") == project_id:
                data["messages"][i] = {**msg, "read": True}
                changed = True
    if changed:
        _save_raw(data)
    return changed


def get_messaging_poll(user_id, since_iso=""):
    since = since_iso or ""
    user = get_user(user_id)
    new_incoming = [
        m for m in get_inbox_for_user(user_id)
        if _is_b2b_message(m) and m.get("created_at", "") > since
    ]
    return {
        "unread": get_unread_count(user_id),
        "conversations": get_conversations(user_id),
        "notifications": [serialize_message_api(m, user_id) for m in new_incoming],
        "server_time": datetime.now(timezone.utc).isoformat(),
    }


def send_b2b_message(from_user, to_user, body, project_id=None, subject=None, kind="reply"):
    if not body or not body.strip():
        raise ValueError("Le message ne peut pas être vide.")
    if not users_can_message(from_user, to_user, project_id):
        raise ValueError("Vous ne pouvez pas contacter cet utilisateur.")
    project = get_project(project_id) if project_id else None
    if not subject:
        if project:
            subject = f"Échange — {project.get('title', 'Projet IoT')}"
        else:
            subject = "Message Iotplace"
    return send_message(from_user, to_user, subject, body.strip(), kind=kind, project=project)


def add_message(fields):
    data = _load_raw()
    entry = {
        "id": _new_id(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "read": False,
        "status": fields.get("status", "pending"),
        **fields,
    }
    data.setdefault("messages", []).append(entry)
    _save_raw(data)
    return entry


def get_message(message_id):
    return next((m for m in _load_raw().get("messages", []) if m["id"] == message_id), None)


def get_messages_for_user(user_id):
    messages = _load_raw().get("messages", [])
    return sorted(
        [m for m in messages if m.get("from_user_id") == user_id or m.get("to_user_id") == user_id],
        key=lambda m: m.get("created_at", ""),
        reverse=True,
    )


def get_inbox_for_user(user_id):
    return [m for m in get_messages_for_user(user_id) if m.get("to_user_id") == user_id]


def get_sent_for_user(user_id):
    return [m for m in get_messages_for_user(user_id) if m.get("from_user_id") == user_id]


def get_unread_count(user_id):
    return sum(1 for m in get_inbox_for_user(user_id) if not m.get("read"))


def mark_message_read(message_id, user_id):
    data = _load_raw()
    for i, msg in enumerate(data.get("messages", [])):
        if msg["id"] == message_id and msg.get("to_user_id") == user_id:
            data["messages"][i] = {**msg, "read": True}
            _save_raw(data)
            return data["messages"][i]
    return None


def update_message_status(message_id, user_id, status):
    data = _load_raw()
    for i, msg in enumerate(data.get("messages", [])):
        if msg["id"] == message_id and msg.get("to_user_id") == user_id:
            data["messages"][i] = {**msg, "status": status, "read": True}
            _save_raw(data)
            return data["messages"][i]
    return None


def update_message_status_direct(message_id, status):
    data = _load_raw()
    for i, msg in enumerate(data.get("messages", [])):
        if msg["id"] == message_id:
            data["messages"][i] = {**msg, "status": status, "read": True}
            _save_raw(data)
            return data["messages"][i]
    return None


# ── Budget & engagements (Stripe escrow) ──

BUDGET_CENTS_MAP = {
    "< 10k€": 500_000,
    "10k–50k€": 3_000_000,
    "50k–150k€": 10_000_000,
    "150k–500k€": 32_500_000,
    "500k€+": 50_000_000,
    "< 10k": 500_000,
    "10k-50k": 3_000_000,
    "50k-150k": 10_000_000,
}


def resolve_budget_cents(budget_label: str) -> int:
    label = (budget_label or "").strip()
    if label in BUDGET_CENTS_MAP:
        return BUDGET_CENTS_MAP[label]
    return 5_000_000


def resolve_project_amount_cents(project: dict) -> int:
    if project.get("budget_cents"):
        return int(project["budget_cents"])
    return resolve_budget_cents(project.get("budget", ""))


def create_engagement(fields: dict) -> dict:
    data = _load_raw()
    entry = {
        "id": _new_id(),
        "created_at": _now().isoformat(),
        "paid_at": None,
        "released_at": None,
        "stripe_invoice_id": None,
        "stripe_hosted_invoice_url": None,
        "stripe_transfer_id": None,
        "notes": "",
        **fields,
    }
    data.setdefault("engagements", []).append(entry)
    _save_raw(data)
    return entry


def get_engagement(engagement_id: str):
    return next((e for e in _load_raw().get("engagements", []) if e["id"] == engagement_id), None)


def get_engagement_by_message(message_id: str):
    return next(
        (e for e in _load_raw().get("engagements", []) if e.get("application_message_id") == message_id),
        None,
    )


def get_engagements_for_enterprise(enterprise_id: str) -> list:
    return [
        e for e in _load_raw().get("engagements", [])
        if e.get("enterprise_id") == enterprise_id
    ]


def get_engagements_for_startup(startup_id: str) -> list:
    return [
        e for e in _load_raw().get("engagements", [])
        if e.get("startup_id") == startup_id
    ]


def update_engagement(engagement_id: str, fields: dict):
    data = _load_raw()
    for i, entry in enumerate(data.get("engagements", [])):
        if entry["id"] == engagement_id:
            data["engagements"][i] = {**entry, **fields, "id": engagement_id}
            _save_raw(data)
            return data["engagements"][i]
    return None


def get_startup_by_connect_account(account_id: str):
    if not account_id:
        return None
    return next(
        (s for s in get_startups() if s.get("stripe_connect_account_id") == account_id),
        None,
    )


def format_engagement_label(status: str) -> str:
    labels = {
        "draft": "Brouillon",
        "pending_payment": "Facture envoyée — en attente de paiement",
        "escrowed": "Fonds en séquestre",
        "released": "Versement effectué à la startup",
        "payment_error": "Erreur de paiement",
        "cancelled": "Annulé",
    }
    return labels.get(status or "", status or "—")


def get_contacts_for_user(user):
    email = (user.get("email") or "").strip().lower()
    role = user.get("role", "")
    contacts = []
    for c in get_contacts():
        c_email = (c.get("email") or "").strip().lower()
        c_type = c.get("type", "")
        if c_email == email:
            contacts.append({**c, "source": "vitrine"})
        elif role == "enterprise" and c_type == "enterprise" and c_email == email:
            contacts.append({**c, "source": "vitrine"})
        elif role == "startup" and c_type == "startup" and c_email == email:
            contacts.append({**c, "source": "vitrine"})
    return contacts


def get_applications_for_project(project_id):
    return [
        m for m in _load_raw().get("messages", [])
        if m.get("kind") == "application" and m.get("project_id") == project_id
    ]


def get_applications_for_startup(startup_id):
    return [
        m for m in _load_raw().get("messages", [])
        if m.get("kind") == "application" and m.get("from_profile_id") == startup_id
    ]


def get_applications_for_enterprise(enterprise_id):
    project_ids = {p["id"] for p in get_projects_for_enterprise(enterprise_id)}
    return [
        m for m in _load_raw().get("messages", [])
        if m.get("kind") == "application" and m.get("project_id") in project_ids
    ]


def startup_already_applied(startup_id, project_id):
    return any(
        m.get("from_profile_id") == startup_id and m.get("project_id") == project_id
        for m in _load_raw().get("messages", [])
        if m.get("kind") == "application"
    )


def send_message(from_user, to_user, subject, body, kind="contact", project=None, status="pending"):
    from_name = _profile_name_for_user(from_user)
    to_name = _profile_name_for_user(to_user)
    fields = {
        "kind": kind,
        "from_user_id": from_user["id"],
        "to_user_id": to_user["id"],
        "from_name": from_name,
        "to_name": to_name,
        "from_role": from_user.get("role"),
        "to_role": to_user.get("role"),
        "subject": subject,
        "body": body,
        "status": status,
    }
    if from_user.get("role") == "startup":
        fields["from_profile_id"] = from_user.get("profile_id")
    if from_user.get("role") == "enterprise":
        fields["from_profile_id"] = from_user.get("profile_id")
    if project:
        fields["project_id"] = project["id"]
        fields["project_title"] = project.get("title", "")
    return add_message(fields)


def apply_to_project(startup_user, startup, project, message_body):
    if startup_already_applied(startup["id"], project["id"]):
        raise ValueError("Vous avez déjà candidaté à ce projet.")
    enterprise_user = _user_for_enterprise_id(project.get("enterprise_id"))
    if not enterprise_user:
        raise ValueError("Entreprise destinataire introuvable.")
    subject = f"Candidature — {project.get('title', 'Projet IoT')}"
    return send_message(
        startup_user,
        enterprise_user,
        subject,
        message_body,
        kind="application",
        project=project,
        status="pending",
    )


def enrich_message_for_view(msg, current_user_id):
    direction = "in" if msg.get("to_user_id") == current_user_id else "out"
    kind_labels = {
        "application": "Candidature",
        "contact": "Prise de contact",
        "reply": "Réponse",
    }
    status_labels = {
        "pending": "En attente",
        "accepted": "Acceptée",
        "declined": "Refusée",
        "closed": "Clôturée",
    }
    return {
        **msg,
        "direction": direction,
        "kind_label": kind_labels.get(msg.get("kind"), msg.get("kind", "Message")),
        "status_label": status_labels.get(msg.get("status"), msg.get("status", "")),
        "counterpart_name": msg.get("from_name") if direction == "in" else msg.get("to_name"),
    }


def get_dashboard_data_for_enterprise(user, profile):
    projects = get_projects_for_enterprise(profile["id"], profile.get("name", ""))
    inbox = get_inbox_for_user(user["id"])
    sent = get_sent_for_user(user["id"])
    applications = get_applications_for_enterprise(profile["id"])
    platform_contacts = get_contacts_for_user(user)
    projects_enriched = []
    for p in projects:
        apps = get_applications_for_project(p["id"])
        projects_enriched.append({
            **p,
            "applications_count": len(apps),
            "applications_pending": sum(1 for a in apps if a.get("status") == "pending"),
        })
    return {
        "projects": projects_enriched,
        "inbox": [enrich_message_for_view(m, user["id"]) for m in inbox],
        "sent": [enrich_message_for_view(m, user["id"]) for m in sent],
        "applications": [enrich_message_for_view(m, user["id"]) for m in applications],
        "platform_contacts": platform_contacts,
        "unread_count": get_unread_count(user["id"]),
        "stats": {
            "projects": len(projects),
            "messages": len(inbox) + len(sent),
            "applications": len(applications),
            "unread": get_unread_count(user["id"]),
            "contacts": len(platform_contacts),
        },
    }


def get_dashboard_data_for_startup(user, profile):
    matching = get_matching_projects_for_startup(profile)
    inbox = get_inbox_for_user(user["id"])
    sent = get_sent_for_user(user["id"])
    applications = get_applications_for_startup(profile["id"])
    applied_ids = {a.get("project_id") for a in applications}
    matching_enriched = []
    for p in matching:
        matching_enriched.append({
            **p,
            "already_applied": p["id"] in applied_ids,
        })
    return {
        "matching_projects": matching_enriched,
        "inbox": [enrich_message_for_view(m, user["id"]) for m in inbox],
        "sent": [enrich_message_for_view(m, user["id"]) for m in sent],
        "applications": [enrich_message_for_view(m, user["id"]) for m in applications],
        "platform_contacts": get_contacts_for_user(user),
        "unread_count": get_unread_count(user["id"]),
        "stats": {
            "applications": len(applications),
            "messages": len(inbox) + len(sent),
            "matching": len(matching),
            "unread": get_unread_count(user["id"]),
        },
    }


def get_page_catalog():
    return PAGE_CATALOG


def get_page_meta(slug):
    return next((p for p in PAGE_CATALOG if p["slug"] == slug), None)


def get_page_content(slug, locale="en"):
    data = _load_raw()
    saved = data.get("pages", {}).get(slug, {})
    defaults = (DEFAULT_PAGE_CONTENT_FR if locale == "fr" else DEFAULT_PAGE_CONTENT).get(slug, {})
    meta_keys = {"published", "updated_at", "en", "fr"}
    if isinstance(saved.get(locale), dict):
        return {**defaults, **saved[locale], "published": saved.get("published", True)}
    legacy = {k: v for k, v in saved.items() if k not in meta_keys}
    return {**defaults, **legacy, "published": saved.get("published", True)}


def get_all_pages():
    return [{"slug": p["slug"], "name": p["name"], "path": p["path"], **get_page_content(p["slug"])} for p in PAGE_CATALOG]


def update_page(slug, fields):
    data = _load_raw()
    if "pages" not in data:
        data["pages"] = {}
    current = data["pages"].get(slug, {})
    data["pages"][slug] = {**current, **fields, "updated_at": datetime.now(timezone.utc).isoformat()}
    _save_raw(data)
    return data["pages"][slug]


# ── SEO ──


def get_site_url():
    env_url = os.environ.get("SITE_URL", "").strip().rstrip("/")
    if env_url:
        return env_url
    global_seo = get_seo_global()
    saved = (global_seo.get("site_url") or "").strip().rstrip("/")
    if saved:
        return saved
    return "https://iotplace.osc-fr1.scalingo.io"


def build_canonical_url(site_url, path, query_string=b""):
    url = f"{site_url.rstrip('/')}{path}"
    if query_string:
        qs = query_string.decode("utf-8") if isinstance(query_string, bytes) else str(query_string)
        if qs:
            url = f"{url}?{qs}"
    return url


def get_seo_global():
    data = _load_raw()
    return _deep_merge(DEFAULT_DATA["seo"]["global"], data.get("seo", {}).get("global", {}))


def get_seo_page(slug, locale="en"):
    data = _load_raw()
    saved = data.get("seo", {}).get("pages", {}).get(slug, {})
    if locale == "fr":
        defaults_map = {
            "home": {"title": "Sous-traitance IoT B2B — Entreprises & Startups Asie", "description": "Iotplace, marketplace IoT B2B : entreprises et startups IoT en Asie du Sud-Est.", "keywords": "sous-traitance IoT, externalisation IoT, marketplace IoT B2B"},
            "enterprises": {"title": "Externaliser vos projets IoT — Sous-traiter des startups", "description": "Publiez vos besoins et sous-traitez firmware, PCB, cloud à des startups qualifiées.", "keywords": "entreprise sous-traiter IoT, externalisation projet IoT"},
            "startups": {"title": "Startups IoT — Missions de sous-traitance", "description": "Trouvez des projets de sous-traitance publiés par les grandes entreprises.", "keywords": "startup IoT missions, sous-traitance IoT"},
            "projects": {"title": "Projets IoT ouverts — Missions de sous-traitance", "description": "Liste des projets IoT ouverts à la sous-traitance sur Iotplace.", "keywords": "projets IoT ouverts, mission sous-traitance IoT"},
            "about": {"title": "À propos — Marketplace sous-traitance IoT B2B", "description": "Iotplace structure la sous-traitance IoT entre entreprises et startups d'Asie.", "keywords": "marketplace IoT, sous-traitance IoT Asie"},
            "contact": {"title": "Contact — Démarrer une sous-traitance IoT", "description": "Contactez Iotplace pour sous-traiter ou trouver des missions IoT.", "keywords": "contact sous-traitance IoT"},
        }
    else:
        defaults_map = DEFAULT_SEO_PAGES
    defaults = defaults_map.get(slug, {})
    meta = get_page_meta(slug) or {}
    base = {
        "title": defaults.get("title") or meta.get("name", slug),
        "description": defaults.get("description", ""),
        "keywords": defaults.get("keywords", ""),
    }
    return {**base, **saved}


def get_startups_country_seo(country):
    return {
        "title": f"IoT Startups in {country} — Enterprise subcontracting",
        "description": (
            f"IoT startups in {country}: find subcontracting missions published by "
            f"large enterprises — firmware, PCB, cloud and hardware integration on Iotplace."
        ),
        "keywords": (
            f"IoT startup {country}, IoT subcontracting {country}, "
            f"IoT outsourcing, firmware development {country}"
        ),
    }


def get_compte_seo(endpoint):
    defaults = COMPTE_SEO_PAGES.get(endpoint, {})
    if not defaults:
        global_seo = get_seo_global()
        suffix = global_seo.get("title_suffix", "")
        return {
            "title": f"Espace membre{suffix}",
            "description": global_seo.get("meta_description", ""),
            "keywords": "",
            "og_image": "",
            "og_image_abs": "",
            "google_analytics_id": global_seo.get("google_analytics_id", ""),
            "site_name": global_seo.get("site_name", "Iotplace"),
            "twitter_handle": global_seo.get("twitter_handle", ""),
            "robots": "noindex, follow",
            "locale": "en_US",
        }
    return get_seo_for_vitrine(
        "home",
        title=defaults.get("title"),
        description=defaults.get("description"),
        keywords=defaults.get("keywords"),
        robots=defaults.get("robots", "noindex, follow"),
    )


def get_seo_for_vitrine(slug, page_title="", overrides=None, robots="index, follow", locale="en", **kwargs):
    global_seo = get_seo_global()
    page_seo = get_seo_page(slug, locale)
    if overrides:
        page_seo = {**page_seo, **overrides}
    title = kwargs.get("title") or page_seo.get("title") or page_title or global_seo.get("site_name", "Iotplace")
    suffix = global_seo.get("title_suffix", "")
    full_title = title if suffix and suffix.strip() in title else f"{title}{suffix}" if suffix else title
    description = kwargs.get("description") or page_seo.get("description") or global_seo.get("meta_description", "")
    keywords = kwargs.get("keywords") or page_seo.get("keywords") or global_seo.get("keywords", "")
    og_image = global_seo.get("og_image", "")
    site_url = get_site_url()
    return {
        "title": full_title,
        "description": description[:320],
        "keywords": keywords,
        "og_image": og_image,
        "og_image_abs": f"{og_image}" if og_image.startswith("http") else f"{site_url}{og_image}" if og_image else "",
        "google_analytics_id": global_seo.get("google_analytics_id", ""),
        "site_name": global_seo.get("site_name", "Iotplace"),
        "twitter_handle": global_seo.get("twitter_handle", ""),
        "robots": kwargs.get("robots", robots),
        "locale": "fr_FR" if locale == "fr" else "en_US",
    }


def get_page_faq(slug, locale="en"):
    data = _load_raw()
    saved = data.get("faq", {}).get(slug)
    if saved:
        return saved
    if locale == "fr":
        return PAGE_FAQ_FR.get(slug, PAGE_FAQ.get(slug, []))
    return PAGE_FAQ.get(slug, [])


def update_page_faq(slug, items):
    data = _load_raw()
    if "faq" not in data:
        data["faq"] = {}
    data["faq"][slug] = items
    _save_raw(data)
    return items


def build_breadcrumbs(slug, site_url, extra=None, locale="en"):
    labels = BREADCRUMB_LABELS_FR if locale == "fr" else BREADCRUMB_LABELS
    home = labels.get("home", "Home")
    items = [{"name": home, "url": f"{site_url}/"}]
    if slug != "home":
        label = labels.get(slug, slug)
        meta = get_page_meta(slug)
        path = meta["path"] if meta else f"/{slug}"
        items.append({"name": label, "url": f"{site_url}{path}"})
    if extra:
        items.append(extra)
    return items


def build_json_ld(slug, canonical_url, site_url, faq=None, breadcrumbs=None, locale="en"):
    lang_tag = "fr-FR" if locale == "fr" else "en-US"
    global_seo = get_seo_global()
    site_name = global_seo.get("site_name", "Iotplace")
    seo = get_seo_for_vitrine(slug, locale=locale)
    graphs = []

    graphs.append({
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": site_name,
        "url": site_url,
        "logo": f"{site_url}/vitrine/static/favicon.ico" if site_url else "",
        "description": global_seo.get("meta_description", ""),
        "sameAs": [],
    })

    graphs.append({
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": site_name,
        "url": site_url,
        "description": global_seo.get("meta_description", ""),
        "inLanguage": lang_tag,
        "potentialAction": {
            "@type": "SearchAction",
            "target": f"{site_url}/startups?country={{search_term_string}}",
            "query-input": "required name=search_term_string",
        },
    })

    graphs.append({
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": seo["title"],
        "description": seo["description"],
        "url": canonical_url,
        "isPartOf": {"@type": "WebSite", "name": site_name, "url": site_url},
        "inLanguage": lang_tag,
    })

    crumbs = breadcrumbs or build_breadcrumbs(slug, site_url, locale=locale)
    if len(crumbs) > 1:
        graphs.append({
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": i + 1,
                    "name": c["name"],
                    "item": c["url"],
                }
                for i, c in enumerate(crumbs)
            ],
        })

    faq_items = faq if faq is not None else get_page_faq(slug, locale)
    if faq_items:
        graphs.append({
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": item["q"],
                    "acceptedAnswer": {"@type": "Answer", "text": item["a"]},
                }
                for item in faq_items
            ],
        })

    if slug in ("home", "enterprises", "startups"):
        graphs.append({
            "@context": "https://schema.org",
            "@type": "Service",
            "name": "B2B IoT subcontracting marketplace",
            "provider": {"@type": "Organization", "name": site_name},
            "areaServed": ["Vietnam", "Indonesia", "Thailand", "Philippines", "Southeast Asia"],
            "serviceType": "IoT project subcontracting and outsourcing",
            "audience": [
                {"@type": "BusinessAudience", "audienceType": "Enterprises looking to subcontract IoT"},
                {"@type": "BusinessAudience", "audienceType": "IoT startups looking for missions"},
            ],
        })

    return graphs


def get_sitemap_entries():
    site_url = get_site_url()
    entries = []
    for page in PAGE_CATALOG:
        content = get_page_content(page["slug"])
        if not content.get("published", True):
            continue
        entries.append({
            "loc": f"{site_url}{page['path']}",
            "changefreq": "weekly" if page["slug"] == "home" else "monthly",
            "priority": "1.0" if page["slug"] == "home" else "0.8",
        })
    entries.append({
        "loc": f"{site_url}/inscription/entreprise",
        "changefreq": "monthly",
        "priority": "0.9",
    })
    entries.append({
        "loc": f"{site_url}/inscription/startup",
        "changefreq": "monthly",
        "priority": "0.9",
    })
    for country in get_startup_countries():
        entries.append({
            "loc": f"{site_url}/startups?country={quote(country)}",
            "changefreq": "weekly",
            "priority": "0.7",
        })
    for startup in get_startups():
        entries.append({
            "loc": f"{site_url}/startups/{startup['id']}",
            "changefreq": "monthly",
            "priority": "0.6",
        })
    for enterprise in get_public_enterprises():
        entries.append({
            "loc": f"{site_url}/enterprises/{enterprise['id']}",
            "changefreq": "monthly",
            "priority": "0.6",
        })
    for project in get_projects():
        entries.append({
            "loc": f"{site_url}/projects/{project['id']}",
            "changefreq": "weekly",
            "priority": "0.7",
        })
    return entries


def get_startup_detail_seo(startup):
    name = startup.get("name", "Startup")
    country = startup.get("country", "")
    return {
        "title": f"{name} — IoT Startup Profile",
        "description": (startup.get("description") or f"IoT startup {name} profile on Iotplace.")[:300],
        "keywords": f"IoT startup {name}, {country} IoT, subcontracting, {', '.join(startup.get('skills', [])[:5])}",
    }


def get_enterprise_detail_seo(enterprise):
    name = enterprise.get("name", "Enterprise")
    return {
        "title": f"{name} — Enterprise Profile",
        "description": (enterprise.get("description") or f"{name} enterprise profile on Iotplace.")[:300],
        "keywords": f"IoT enterprise {name}, {enterprise.get('sector', '')}, subcontracting client",
    }


def get_project_detail_seo(project):
    title = project.get("title", "Project")
    return {
        "title": f"{title} — Open IoT Project",
        "description": (project.get("description") or f"IoT subcontracting project: {title}.")[:300],
        "keywords": f"IoT project {title}, subcontracting, {', '.join(project.get('skills', [])[:5])}",
    }


def get_robots_txt():
    site_url = get_site_url()
    return f"""User-agent: *
Allow: /
Disallow: /crm/
Disallow: /compte/
Disallow: /connexion
Disallow: /deconnexion

Sitemap: {site_url}/sitemap.xml
"""


def update_seo_global(fields):
    data = _load_raw()
    if "seo" not in data:
        data["seo"] = {"global": {}, "pages": {}}
    data["seo"]["global"] = {**data["seo"].get("global", {}), **fields}
    _save_raw(data)


def update_seo_page(slug, fields):
    data = _load_raw()
    if "seo" not in data:
        data["seo"] = {"global": {}, "pages": {}}
    if "pages" not in data["seo"]:
        data["seo"]["pages"] = {}
    current = data["seo"]["pages"].get(slug, {})
    data["seo"]["pages"][slug] = {**current, **fields}
    _save_raw(data)


# ── Analytics ──

ACTIVE_MINUTES = 5
REALTIME_MINUTES = 30
MAX_UNIQUE_VISITORS = 50000


def _now():
    return datetime.now(timezone.utc)


def _page_label(slug):
    meta = get_page_meta(slug)
    return meta["name"] if meta else slug


def _ensure_analytics(data):
    analytics = data.setdefault("analytics", {})
    for key, default in DEFAULT_DATA["analytics"].items():
        if key not in analytics:
            analytics[key] = default.copy() if isinstance(default, dict) else default
    return analytics


def _prune_unique_visitors(visitors):
    if len(visitors) <= MAX_UNIQUE_VISITORS:
        return visitors
    ranked = sorted(visitors.items(), key=lambda item: item[1].get("first_seen", ""))
    keep = dict(ranked[-MAX_UNIQUE_VISITORS:])
    return keep


def _record_unique_visitor(analytics, session_id, now_iso, converted=None):
    if not session_id:
        return
    visitors = analytics.setdefault("unique_visitors", {})
    existing = visitors.get(session_id, {})
    visitors[session_id] = {
        "first_seen": existing.get("first_seen", now_iso),
        "last_seen": now_iso,
        "converted": converted or existing.get("converted"),
    }
    analytics["unique_visitors"] = _prune_unique_visitors(visitors)


def track_signup_conversion(role, session_id=None):
    if role not in ("enterprise", "startup"):
        return
    data = _load_raw()
    analytics = _ensure_analytics(data)
    now_iso = _now().isoformat()
    if session_id:
        _record_unique_visitor(analytics, session_id, now_iso, converted=role)
    events = analytics.setdefault("signup_events", [])
    events.insert(0, {
        "role": role,
        "at": now_iso,
        "session_id": (session_id or "")[:12] or None,
    })
    analytics["signup_events"] = events[:500]
    _save_raw(data)


def get_conversion_analytics():
    data = _load_raw()
    analytics = _ensure_analytics(data)
    unique_count = len(analytics.get("unique_visitors", {}))
    users = data.get("users", [])
    enterprise_signups = sum(1 for u in users if u.get("role") == "enterprise")
    startup_signups = sum(1 for u in users if u.get("role") == "startup")
    total_signups = enterprise_signups + startup_signups

    def _rate(numerator, denominator):
        if denominator <= 0:
            return 0.0
        return round(numerator / denominator * 100, 2)

    visitors = analytics.get("unique_visitors", {})
    tracked_ent = sum(1 for v in visitors.values() if v.get("converted") == "enterprise")
    tracked_st = sum(1 for v in visitors.values() if v.get("converted") == "startup")

    return {
        "unique_visitors": unique_count,
        "enterprise_signups": enterprise_signups,
        "startup_signups": startup_signups,
        "total_signups": total_signups,
        "conversion_enterprise_pct": _rate(enterprise_signups, unique_count),
        "conversion_startup_pct": _rate(startup_signups, unique_count),
        "conversion_total_pct": _rate(total_signups, unique_count),
        "tracked_enterprise_conversions": tracked_ent,
        "tracked_startup_conversions": tracked_st,
        "recent_signups": analytics.get("signup_events", [])[:10],
    }


def _prune_analytics(analytics):
    cutoff = _now() - timedelta(minutes=REALTIME_MINUTES)
    cutoff_iso = cutoff.isoformat()
    sessions = analytics.get("sessions", {})
    analytics["sessions"] = {
        sid: s for sid, s in sessions.items()
        if s.get("last_seen", "") >= cutoff_iso
    }
    analytics["recent"] = [
        e for e in analytics.get("recent", [])
        if e.get("at", "") >= cutoff_iso
    ][-500:]


def track_page_view(page_slug, path="/", session_id=None, referrer=""):
    if _is_excluded_analytics(path=path, referrer=referrer):
        return None
    return track_hit(page_slug, path, session_id=session_id, referrer=referrer, source="server")


def _is_excluded_analytics(path="", referrer=""):
    path = path or ""
    if path.startswith("/crm") or path.startswith("/api/"):
        return True
    if path.startswith("/vitrine/static/"):
        return True
    if path.startswith("/compte") or path.startswith("/inscription") or path.startswith("/connexion"):
        return True
    ref = (referrer or "").lower()
    if "/crm" in ref:
        return True
    return False


def track_hit(page_slug, path="/", session_id=None, referrer="", source="server"):
    if _is_excluded_analytics(path=path, referrer=referrer):
        return None
    data = _load_raw()
    analytics = _ensure_analytics(data)
    now = _now()
    now_iso = now.isoformat()
    today = now.strftime("%Y-%m-%d")
    hour_key = now.strftime("%Y-%m-%dT%H")

    analytics["total_views"] = analytics.get("total_views", 0) + 1
    analytics["daily"][today] = analytics["daily"].get(today, 0) + 1
    analytics["hourly"][hour_key] = analytics["hourly"].get(hour_key, 0) + 1
    analytics["pages"][page_slug] = analytics["pages"].get(page_slug, 0) + 1
    analytics["paths"][path] = analytics["paths"].get(path, 0) + 1

    sid = session_id or f"anon-{_new_id()}"
    sessions = analytics.setdefault("sessions", {})
    existing = sessions.get(sid, {})
    sessions[sid] = {
        "first_seen": existing.get("first_seen", now_iso),
        "last_seen": now_iso,
        "page": page_slug,
        "path": path,
        "hits": existing.get("hits", 0) + 1,
    }
    _record_unique_visitor(analytics, sid, now_iso)

    event = {
        "page": page_slug,
        "page_label": _page_label(page_slug),
        "path": path,
        "session_id": sid[:8],
        "at": now_iso,
        "referrer": (referrer or "")[:200],
        "source": source,
    }
    analytics["recent"].insert(0, event)
    _prune_analytics(analytics)
    _save_raw(data)
    return sid


def track_ping(session_id, page_slug=None, path=None):
    if not session_id:
        return
    if _is_excluded_analytics(path=path or ""):
        return
    data = _load_raw()
    analytics = _ensure_analytics(data)
    now_iso = _now().isoformat()
    sessions = analytics.setdefault("sessions", {})
    if session_id in sessions:
        sessions[session_id]["last_seen"] = now_iso
        if page_slug:
            sessions[session_id]["page"] = page_slug
        if path:
            sessions[session_id]["path"] = path
    else:
        sessions[session_id] = {
            "first_seen": now_iso,
            "last_seen": now_iso,
            "page": page_slug or "unknown",
            "path": path or "/",
            "hits": 0,
        }
    _prune_analytics(analytics)
    _save_raw(data)


def get_realtime_analytics():
    data = _load_raw()
    analytics = _ensure_analytics(data)
    now = _now()
    active_cutoff = (now - timedelta(minutes=ACTIVE_MINUTES)).isoformat()
    realtime_cutoff = (now - timedelta(minutes=REALTIME_MINUTES)).isoformat()

    sessions = analytics.get("sessions", {})
    active_sessions = [
        {**s, "session_id": sid[:8]}
        for sid, s in sessions.items()
        if s.get("last_seen", "") >= active_cutoff
    ]
    recent = [e for e in analytics.get("recent", []) if e.get("at", "") >= realtime_cutoff]

    minute_chart = []
    for i in range(REALTIME_MINUTES - 1, -1, -1):
        t = now - timedelta(minutes=i)
        key = t.strftime("%H:%M")
        count = sum(
            1 for e in recent
            if e.get("at", "")[:16] == t.strftime("%Y-%m-%dT%H:%M")
        )
        minute_chart.append({"label": key, "views": count})

    pages_rt = Counter(e.get("page", "unknown") for e in recent)
    pages_realtime = [
        {"slug": slug, "label": _page_label(slug), "views": count}
        for slug, count in pages_rt.most_common()
    ]

    return {
        "active_users": len(active_sessions),
        "views_last_30min": len(recent),
        "minute_chart": minute_chart,
        "live_feed": recent[:40],
        "pages_realtime": pages_realtime,
        "active_sessions": sorted(active_sessions, key=lambda s: s.get("last_seen", ""), reverse=True)[:20],
        "updated_at": now.isoformat(),
    }


def get_analytics():
    data = _load_raw()
    analytics = _ensure_analytics(data)
    realtime = get_realtime_analytics()
    today = _now().strftime("%Y-%m-%d")
    daily = analytics.get("daily", {})
    last_7 = sorted(daily.items())[-7:]
    pages_labeled = [
        {"slug": slug, "label": _page_label(slug), "views": count}
        for slug, count in sorted(analytics.get("pages", {}).items(), key=lambda x: x[1], reverse=True)
    ]
    return {
        "total_views": analytics.get("total_views", 0),
        "today": daily.get(today, 0),
        "pages": analytics.get("pages", {}),
        "pages_labeled": pages_labeled,
        "paths": analytics.get("paths", {}),
        "daily_chart": last_7,
        "recent": analytics.get("recent", [])[:30],
        "contacts_count": len(data.get("contacts", [])),
        "realtime": realtime,
        "conversion": get_conversion_analytics(),
    }


# ── Réseaux sociaux ──

def get_social_posts():
    return sorted(_load_raw().get("social_posts", []), key=lambda p: p.get("created_at", ""), reverse=True)


def add_social_post(fields):
    data = _load_raw()
    entry = {
        "id": _new_id(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "draft",
        **fields,
    }
    data.setdefault("social_posts", []).append(entry)
    _save_raw(data)
    return entry


def update_social_post(entry_id, fields):
    data = _load_raw()
    for i, post in enumerate(data.get("social_posts", [])):
        if post["id"] == entry_id:
            data["social_posts"][i] = {**post, **fields, "id": entry_id}
            if fields.get("status") == "published" and not post.get("published_at"):
                data["social_posts"][i]["published_at"] = datetime.now(timezone.utc).isoformat()
            _save_raw(data)
            return data["social_posts"][i]
    return None


def delete_social_post(entry_id):
    data = _load_raw()
    data["social_posts"] = [p for p in data.get("social_posts", []) if p["id"] != entry_id]
    _save_raw(data)
