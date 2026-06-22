import hashlib
import json
import os
import secrets
import uuid
from urllib.parse import quote
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Legacy path — runtime storage via data.persistence (JSON or PostgreSQL)
DATA_FILE = Path(__file__).parent / "content.json"

from data.site_pages import STATIC_PAGE_CATALOG as PAGE_CATALOG, build_page_catalog, get_domain_seo_defaults, get_page_entry, parse_domain_page_slug

from data.site_config import CONTACT_EMAIL, PRODUCTION_SITE_URL

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
        "email": CONTACT_EMAIL,
    },
    "pricing": {
        "title": "Pricing & offers",
        "subtitle": "Free to join. Pay only on success — commission on signed IoT missions, optional Pro for high volume.",
    },
    "privacy": {
        "title": "Privacy policy",
        "subtitle": "How Iotplace collects and protects your personal data.",
    },
    "legal": {
        "title": "Legal notice",
        "subtitle": "Publisher, hosting and terms of use for iotplace.fr.",
    },
    "cookies": {
        "title": "Cookie policy",
        "subtitle": "Cookies used on Iotplace and how to manage your preferences.",
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
        "email": CONTACT_EMAIL,
    },
    "pricing": {
        "title": "Tarifs & offres",
        "subtitle": "Inscription gratuite. Payez uniquement au succès — commission sur les missions IoT signées, option Pro pour les gros volumes.",
    },
    "privacy": {
        "title": "Politique de confidentialité",
        "subtitle": "Comment Iotplace collecte et protège vos données personnelles.",
    },
    "legal": {
        "title": "Mentions légales",
        "subtitle": "Éditeur, hébergement et conditions d'utilisation du site iotplace.fr.",
    },
    "cookies": {
        "title": "Politique cookies",
        "subtitle": "Cookies utilisés sur Iotplace et gestion de vos préférences.",
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
    "privacy": {
        "title": "Privacy policy — Iotplace",
        "description": "How Iotplace processes personal data: contact form, accounts, analytics and your GDPR rights.",
        "keywords": "Iotplace privacy, GDPR, personal data, IoT marketplace",
    },
    "legal": {
        "title": "Legal notice — Iotplace",
        "description": "Legal publisher information, hosting and intellectual property for iotplace.fr.",
        "keywords": "Iotplace legal notice, SARL, RCS Nanterre, terms",
    },
    "cookies": {
        "title": "Cookie policy — Iotplace",
        "description": "Cookies and trackers used on Iotplace and how to manage your consent preferences.",
        "keywords": "Iotplace cookies, consent, analytics, GDPR",
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
            "q": "What strategy works to sell to large enterprises?",
            "a": "The most effective path: find a pilot client, deliver a paid PoC, turn it into a framework contract, then build a strategic partnership. Iotplace structures these steps via PoC, Scale and Partnership project phases.",
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
            "a": "Signup and Scale/Partnership applications are free. PoC project applications require a one-time application fee (via Stripe). Mission payout arrives when the enterprise releases escrow funds.",
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
    "about": [
        {
            "q": "What is Iotplace?",
            "a": "Iotplace is a B2B marketplace where enterprises subcontract IoT projects (firmware, hardware, cloud) to qualified startups, mainly in Southeast Asia, with structured PoC-to-partnership journeys and Stripe escrow payments.",
        },
        {
            "q": "Who is Iotplace for?",
            "a": "Industrial groups and large enterprises that outsource IoT development, and IoT startups seeking B2B missions from enterprise clients.",
        },
        {
            "q": "Where is Iotplace based?",
            "a": "Iotplace operates at https://iotplace.fr with a European client focus and a startup talent pool across Vietnam, Indonesia, Thailand and the ASEAN region.",
        },
        {
            "q": "How do I contact Iotplace?",
            "a": "Use the contact form at /contact or email contact@iotplace.fr for partnerships, support and press inquiries.",
        },
    ],
    "contact": [
        {
            "q": "How can I reach the Iotplace team?",
            "a": "Email contact@iotplace.fr or use the contact form on /contact. Enterprise and startup accounts can also use in-platform messaging after signup.",
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
    "privacy": "Privacy",
    "legal": "Legal notice",
    "cookies": "Cookies",
}

BREADCRUMB_LABELS_FR = {
    "home": "Accueil",
    "enterprises": "Entreprises",
    "startups": "Startups IoT",
    "projects": "Projets IoT",
    "about": "À propos",
    "contact": "Contact",
    "pricing": "Tarifs",
    "privacy": "Confidentialité",
    "legal": "Mentions légales",
    "cookies": "Cookies",
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
        {"q": "Quelle stratégie pour vendre aux grands groupes ?", "a": "Le parcours le plus efficace : trouver un client pilote, réaliser un PoC payé, le transformer en contrat cadre, puis construire un partenariat stratégique. Iotplace structure ces étapes via les phases PoC, Scale et Partenariat."},
        {"q": "Quels profils de startups IoT sont recherchés ?", "a": "Équipes expertes en firmware, électronique, cloud IoT ou intégration bout-en-bout en Asie du Sud-Est."},
        {"q": "Les missions sont-elles encadrées en B2B ?", "a": "Oui. Les entreprises publient cahier des charges, budget et délais. Iotplace facilite le matching, le paiement séquestre et le suivi."},
    ],
    "projects": [
        {"q": "Comment postuler à un projet IoT ouvert ?", "a": "Créez un compte startup, complétez votre profil et postulez depuis votre tableau de bord."},
        {"q": "Qui publie les projets de sous-traitance IoT ?", "a": "Les grandes entreprises inscrites sur Iotplace qui externalisent leur développement IoT."},
    ],
    "pricing": [
        {"q": "Iotplace est-il gratuit pour les startups ?", "a": "L'inscription et les candidatures sur projets Scale ou Partenariat sont gratuites. Les candidatures sur projets phase PoC sont payantes (frais de candidature via Stripe) — commission plateforme incluse. Le paiement mission arrive quand l'entreprise libère le séquestre."},
        {"q": "Combien coûte une candidature PoC ?", "a": "Un frais de candidature unique est facturé à la startup lors du dépôt sur un projet en phase PoC (montant configurable, ex. 49 €). Iotplace prélève une commission sur ce paiement. Les autres phases restent gratuites à la candidature."},
        {"q": "Quand l'entreprise paie-t-elle ?", "a": "À l'acceptation d'une candidature, Iotplace génère automatiquement une facture Stripe. Le paiement place les fonds en séquestre jusqu'à validation de la mission."},
        {"q": "Quel est le taux de commission ?", "a": "10 % par mission signée sur les offres Gratuit, prélevé à la libération des fonds. L'offre Pro entreprise descend à 7 % avec projets illimités."},
        {"q": "Comment fonctionne le séquestre ?", "a": "Les fonds sont conservés en sécurité après paiement de la facture. La startup est payée via Stripe Connect uniquement quand l'entreprise confirme la livraison."},
        {"q": "Puis-je tester sans payer ?", "a": "Oui. Inscription gratuite, un projet publié (entreprise) ou des candidatures (startup). La commission ne s'applique que lorsqu'une mission est réellement signée et payée."},
    ],
    "about": [
        {"q": "Qu'est-ce qu'Iotplace ?", "a": "Iotplace est une marketplace B2B où les entreprises sous-traitent des projets IoT (firmware, hardware, cloud) à des startups qualifiées, principalement en Asie du Sud-Est, avec un parcours PoC → scale → partenariat et paiements séquestre Stripe."},
        {"q": "À qui s'adresse Iotplace ?", "a": "Aux grands groupes et entreprises qui externalisent du développement IoT, et aux startups IoT qui cherchent des missions B2B auprès d'entreprises clientes."},
        {"q": "Où est basé Iotplace ?", "a": "Iotplace opère sur https://iotplace.fr avec une clientèle européenne et un vivier de startups au Vietnam, en Indonésie, en Thaïlande et dans l'ASEAN."},
        {"q": "Comment contacter Iotplace ?", "a": "Formulaire sur /contact ou e-mail contact@iotplace.fr pour partenariats, support et presse."},
    ],
    "contact": [
        {"q": "Comment joindre l'équipe Iotplace ?", "a": "Écrivez à contact@iotplace.fr ou utilisez le formulaire sur /contact. Les comptes entreprise et startup peuvent aussi utiliser la messagerie après inscription."},
    ],
}

BRAND_OG_IMAGE = "/vitrine/static/brand/og-image.png"
BRAND_LOGO_IMAGE = "/vitrine/static/brand/logo-512.png"
BRAND_MARK_SVG = "/vitrine/static/brand/iotplace-mark.svg"

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
            "og_image": BRAND_OG_IMAGE,
            "twitter_handle": "",
            "google_analytics_id": "",
            "same_as": "",
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
    "mail_campaigns": [],
    "mail_events": [],
    "mail_settings": {
        "signature": "",
        "reply_to": "",
        "last_inbox_sync": "",
    },
    "users": [],
    "messages": [],
    "engagements": [],
    "application_checkouts": [],
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
    from flask import g, has_request_context

    if has_request_context() and getattr(g, "_iotplace_data", None) is not None:
        return g._iotplace_data

    from data.persistence import load_state

    data = load_state()
    for key, value in DEFAULT_DATA.items():
        if key not in data:
            data[key] = value

    if has_request_context():
        g._iotplace_data = data

    return data


def _save_raw(data):
    from flask import g, has_request_context
    from data.persistence import save_state

    save_state(data)
    if has_request_context():
        g._iotplace_data = data


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


def _is_vitrine_profile_public(profile: dict | None) -> bool:
    """Profiles linked to a registered account appear in public directories."""
    if not profile:
        return False
    if profile.get("published") is True:
        return True
    if profile.get("published") is False:
        return bool(profile.get("user_id"))
    return True


def get_public_enterprises():
    return [e for e in get_enterprises() if _is_vitrine_profile_public(e)]


def get_public_startups(country=None):
    startups = get_startups(country)
    return [s for s in startups if _is_vitrine_profile_public(s)]


def get_enterprise_sectors():
    sectors = sorted({
        (e.get("sector") or "").strip()
        for e in get_public_enterprises()
        if (e.get("sector") or "").strip()
    })
    return sectors


def _directory_match_q(item: dict, q: str, fields: tuple[str, ...]) -> bool:
    needle = q.strip().lower()
    if not needle:
        return True
    parts: list[str] = []
    for field in fields:
        value = item.get(field)
        if isinstance(value, list):
            parts.extend(str(v) for v in value if v)
        elif value:
            parts.append(str(value))
    return needle in " ".join(parts).lower()


def enrich_enterprise_directory_item(enterprise: dict) -> dict:
    projects = get_projects_for_enterprise(enterprise["id"], enterprise.get("name", ""))
    open_projects = [p for p in projects if p.get("status") == "Ouvert"]
    needs = enterprise.get("needs") or []
    search_blob = " ".join([
        enterprise.get("name", ""),
        enterprise.get("sector", ""),
        enterprise.get("description", ""),
        enterprise.get("country", ""),
        enterprise.get("city", ""),
        " ".join(needs),
    ]).strip()
    return {
        **enterprise,
        "projects_count": len(projects),
        "open_projects_count": len(open_projects),
        "search_text": search_blob.lower(),
    }


def enrich_startup_directory_item(startup: dict) -> dict:
    skills = startup.get("skills") or []
    search_blob = " ".join([
        startup.get("name", ""),
        startup.get("sector", ""),
        startup.get("specialty", ""),
        startup.get("description", ""),
        startup.get("country", ""),
        startup.get("city", ""),
        " ".join(skills),
    ]).strip()
    return {**startup, "search_text": search_blob.lower()}


def enrich_project_directory_item(project: dict) -> dict:
    skills = project.get("skills") or []
    search_blob = " ".join([
        project.get("title", ""),
        project.get("enterprise", ""),
        project.get("description", ""),
        project.get("budget", ""),
        project.get("duration", ""),
        project.get("engagement_phase", ""),
        project.get("status", ""),
        " ".join(skills),
    ]).strip()
    return {**project, "search_text": search_blob.lower()}


def filter_enterprises_directory(q: str | None = None, sector: str | None = None) -> list:
    items = [enrich_enterprise_directory_item(e) for e in get_public_enterprises()]
    if sector:
        sector_l = sector.strip().lower()
        items = [e for e in items if (e.get("sector") or "").strip().lower() == sector_l]
    if q:
        items = [e for e in items if _directory_match_q(e, q, ("name", "sector", "description", "country", "city", "needs"))]
    return sorted(items, key=lambda e: (-(e.get("open_projects_count") or 0), e.get("name", "").lower()))


def filter_startups_directory(q: str | None = None, country: str | None = None) -> list:
    items = [enrich_startup_directory_item(s) for s in get_public_startups(country)]
    if q:
        items = [s for s in items if _directory_match_q(s, q, ("name", "sector", "specialty", "description", "country", "city", "skills"))]
    return sorted(items, key=lambda s: s.get("name", "").lower())


def filter_projects_directory(q: str | None = None, phase: str | None = None) -> list:
    from data.engagement_phases import normalize_phase

    norm = normalize_phase(phase) if phase else None
    items = [enrich_project_directory_item(p) for p in get_projects(phase=norm)]
    if q:
        items = [p for p in items if _directory_match_q(p, q, ("title", "enterprise", "description", "budget", "duration", "engagement_phase", "status", "skills"))]
    status_order = {"Ouvert": 0, "En cours": 1}
    return sorted(
        items,
        key=lambda p: (status_order.get(p.get("status", ""), 9), p.get("title", "").lower()),
    )


def get_directory_seo_overrides(slug: str, locale: str = "fr", q: str = "", filters: dict | None = None, count: int = 0) -> dict:
    filters = filters or {}
    if locale == "fr":
        titles = {
            "enterprises": "Annuaire des entreprises IoT — Donneurs d'ordre B2B",
            "startups": "Annuaire des startups IoT — Sous-traitance B2B",
            "projects": "Annuaire des projets IoT ouverts — Missions de sous-traitance",
        }
        descriptions = {
            "enterprises": "Annuaire des entreprises IoT sur Iotplace : profils, secteurs, besoins et projets de sous-traitance publiés en Asie et en Europe.",
            "startups": "Annuaire des startups IoT qualifiées : pays, compétences firmware, hardware, cloud et missions B2B disponibles.",
            "projects": "Annuaire des projets IoT ouverts à la sous-traitance : PoC, Scale, Partenariat — budgets, compétences et entreprises donneuses d'ordre.",
        }
        q_title = f"Recherche « {q} » — "
        q_desc = f"{count} résultat(s) pour « {q} ». "
    else:
        titles = {
            "enterprises": "IoT Enterprise Directory — B2B clients",
            "startups": "IoT Startup Directory — B2B subcontractors",
            "projects": "Open IoT Projects Directory — Subcontracting missions",
        }
        descriptions = {
            "enterprises": "Browse IoT enterprises on Iotplace: sectors, outsourcing needs and published subcontracting projects.",
            "startups": "Directory of qualified IoT startups: countries, firmware, hardware, cloud skills and B2B missions.",
            "projects": "Directory of open IoT subcontracting projects: PoC, Scale, Partnership — budgets, skills and enterprise clients.",
        }
        q_title = f"Search “{q}” — "
        q_desc = f"{count} result(s) for “{q}”. "

    title = titles.get(slug, "Iotplace")
    description = descriptions.get(slug, "")
    if filters.get("sector"):
        title = f"{filters['sector']} — {title}" if locale == "fr" else f"{filters['sector']} — {title}"
    if filters.get("country"):
        title = f"{filters['country']} — {title}" if locale == "fr" else f"{filters['country']} — {title}"
    if filters.get("phase"):
        phase_label = filters["phase"].upper() if filters["phase"] in ("poc",) else filters["phase"].title()
        title = f"{phase_label} — {title}"
    if q:
        title = f"{q_title}{title}"
        description = f"{q_desc}{description}"
    return {
        "title": title[:120],
        "description": description[:320],
        "keywords": f"IoT directory, {slug}, subcontracting, B2B marketplace, {q}, {', '.join(str(v) for v in filters.values())}".strip(", "),
    }


def build_directory_json_ld(
    slug: str,
    canonical_url: str,
    site_url: str,
    items: list,
    locale: str = "fr",
    faq=None,
    breadcrumbs=None,
):
    graphs = build_json_ld(slug, canonical_url, site_url, faq=faq, breadcrumbs=breadcrumbs, locale=locale)
    lang_tag = "fr-FR" if locale == "fr" else "en-US"
    list_name = {
        "enterprises": "IoT enterprises directory",
        "startups": "IoT startups directory",
        "projects": "Open IoT projects directory",
    }.get(slug, "Directory")

    if items:
        item_elements = []
        for i, row in enumerate(items[:50]):
            if slug == "enterprises":
                url = f"{site_url}/enterprises/{row['id']}"
                name = row.get("name", "Enterprise")
            elif slug == "startups":
                url = f"{site_url}/startups/{row['id']}"
                name = row.get("name", "Startup")
            else:
                url = f"{site_url}/projects/{row['id']}"
                name = row.get("title", "Project")
            item_elements.append({
                "@type": "ListItem",
                "position": i + 1,
                "url": url,
                "name": name,
            })
        graphs.append({
            "@context": "https://schema.org",
            "@type": "ItemList",
            "name": list_name,
            "numberOfItems": len(items),
            "itemListElement": item_elements,
        })
        graphs.append({
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "name": list_name,
            "url": canonical_url,
            "inLanguage": lang_tag,
            "isPartOf": {"@type": "WebSite", "url": site_url},
            "mainEntity": {"@type": "ItemList", "numberOfItems": len(items)},
        })
    return graphs


def canonical_query_without(search_query_string, *drop_keys: str):
    """Rebuild query string excluding sensitive or duplicate SEO params (e.g. q)."""
    if not search_query_string:
        return b""
    if isinstance(search_query_string, bytes):
        raw = search_query_string.decode("utf-8")
    else:
        raw = str(search_query_string)
    if not raw:
        return b""
    from urllib.parse import parse_qsl, urlencode

    pairs = [(k, v) for k, v in parse_qsl(raw, keep_blank_values=True) if k not in drop_keys]
    if not pairs:
        return b""
    return urlencode(pairs).encode("utf-8")


def get_public_startup(startup_id):
    startup = get_startup(startup_id)
    if not startup or not _is_vitrine_profile_public(startup):
        return None
    return startup


def get_public_enterprise(enterprise_id):
    ent = get_enterprise(enterprise_id)
    if not ent or not _is_vitrine_profile_public(ent):
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


def get_projects(phase=None):
    projects = _load_raw()["projects"]
    norm = None
    if phase:
        from data.engagement_phases import normalize_phase
        norm = normalize_phase(phase)
    if norm:
        projects = [p for p in projects if p.get("engagement_phase") == norm]
    return projects


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
        "status": "new",
        "replies": [],
        **fields,
    }
    data["contacts"].append(entry)
    _save_raw(data)
    return entry


def get_contact(entry_id):
    return next((c for c in get_contacts() if c["id"] == entry_id), None)


def update_contact(entry_id, fields):
    data = _load_raw()
    for i, contact in enumerate(data["contacts"]):
        if contact["id"] == entry_id:
            data["contacts"][i] = {**contact, **fields}
            _save_raw(data)
            return data["contacts"][i]
    return None


def add_contact_reply(entry_id, body, *, email_sent=False, sent_via="crm"):
    contact = get_contact(entry_id)
    if not contact:
        return None
    reply = {
        "id": _new_id(),
        "body": body.strip(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "email_sent": bool(email_sent),
        "sent_via": sent_via,
    }
    replies = list(contact.get("replies") or [])
    replies.append(reply)
    return update_contact(entry_id, {"replies": replies, "status": "replied", "replied_at": reply["created_at"]})


def count_new_contacts():
    return len([c for c in get_contacts() if c.get("status", "new") == "new"])


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


PASSWORD_RESET_HOURS = 24


def _hash_password_reset_token(token: str) -> str:
    return hashlib.sha256((token or "").encode()).hexdigest()


def _parse_iso_datetime(value: str):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def issue_password_reset_token(email: str) -> tuple[str, dict] | tuple[None, None]:
    user = get_user_by_email(email)
    if not user:
        return None, None
    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(hours=PASSWORD_RESET_HOURS)
    data = _load_raw()
    for i, u in enumerate(data.get("users", [])):
        if u["id"] == user["id"]:
            updated = {
                **u,
                "password_reset_token_hash": _hash_password_reset_token(token),
                "password_reset_expires_at": expires.isoformat(),
            }
            data["users"][i] = updated
            _save_raw(data)
            return token, updated
    return None, None


def get_user_by_password_reset_token(token: str):
    if not token:
        return None
    token_hash = _hash_password_reset_token(token)
    now = datetime.now(timezone.utc)
    for user in _load_raw().get("users", []):
        if user.get("password_reset_token_hash") != token_hash:
            continue
        expires = _parse_iso_datetime(user.get("password_reset_expires_at", ""))
        if not expires or expires < now:
            return None
        return user
    return None


def clear_password_reset_token(user_id: str):
    data = _load_raw()
    for i, user in enumerate(data.get("users", [])):
        if user["id"] == user_id:
            updated = dict(user)
            updated.pop("password_reset_token_hash", None)
            updated.pop("password_reset_expires_at", None)
            data["users"][i] = updated
            _save_raw(data)
            return updated
    return None


def update_user_password(user_id: str, password_hash: str):
    data = _load_raw()
    for i, user in enumerate(data.get("users", [])):
        if user["id"] == user_id:
            updated = {
                **user,
                "password_hash": password_hash,
            }
            updated.pop("password_reset_token_hash", None)
            updated.pop("password_reset_expires_at", None)
            data["users"][i] = updated
            _save_raw(data)
            return updated
    return None


def get_enterprise(entry_id):
    return next((e for e in get_enterprises() if e["id"] == entry_id), None)


def get_startup(entry_id):
    return next((s for s in _load_raw()["startups"] if s["id"] == entry_id), None)


def get_enterprise_for_user(user_id):
    ent = next((e for e in get_enterprises() if e.get("user_id") == user_id), None)
    return ent


def get_startup_for_user(user_id):
    startup = next((s for s in _load_raw()["startups"] if s.get("user_id") == user_id), None)
    if startup:
        return startup
    user = get_user(user_id)
    profile_id = (user or {}).get("profile_id")
    if profile_id:
        return get_startup(profile_id)
    return None


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


def _purge_crm_account_from_data(data: dict, user: dict) -> None:
    """Remove a user account and linked profile data from an in-memory state dict."""
    uid = user["id"]
    profile_id = user.get("profile_id")
    role = user.get("role")
    project_ids: set[str] = set()

    if role == "enterprise" and profile_id:
        project_ids = {
            p["id"] for p in data.get("projects", []) if p.get("enterprise_id") == profile_id
        }
        data["projects"] = [p for p in data.get("projects", []) if p.get("enterprise_id") != profile_id]
        data["engagements"] = [
            e for e in data.get("engagements", []) if e.get("enterprise_id") != profile_id
        ]
        data["enterprises"] = [e for e in data.get("enterprises", []) if e["id"] != profile_id]
    elif role == "startup" and profile_id:
        data["engagements"] = [
            e for e in data.get("engagements", []) if e.get("startup_id") != profile_id
        ]
        data["startups"] = [s for s in data.get("startups", []) if s["id"] != profile_id]

    def _drop_message(msg: dict) -> bool:
        if msg.get("from_user_id") == uid or msg.get("to_user_id") == uid:
            return True
        if role == "startup" and profile_id:
            if msg.get("kind") == "application" and msg.get("from_profile_id") == profile_id:
                return True
        if msg.get("project_id") in project_ids:
            return True
        return False

    removed_message_ids = {m["id"] for m in data.get("messages", []) if _drop_message(m)}
    data["messages"] = [m for m in data.get("messages", []) if m["id"] not in removed_message_ids]
    data["engagements"] = [
        e for e in data.get("engagements", [])
        if e.get("application_message_id") not in removed_message_ids
    ]
    data["application_checkouts"] = [
        c for c in data.get("application_checkouts", [])
        if c.get("application_message_id") not in removed_message_ids
    ]
    data["users"] = [u for u in data.get("users", []) if u["id"] != uid]


def delete_crm_account(user_id: str) -> bool:
    data = _load_raw()
    user = next((u for u in data.get("users", []) if u["id"] == user_id), None)
    if not user:
        return False
    _purge_crm_account_from_data(data, user)
    _save_raw(data)
    return True


def delete_all_crm_accounts() -> int:
    data = _load_raw()
    users = list(data.get("users", []))
    if not users:
        return 0
    for user in users:
        _purge_crm_account_from_data(data, user)
    _save_raw(data)
    return len(users)


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
        "plan": enterprise_fields.get("plan") or "free_enterprise",
        "published": True,
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
        from data.engagement_phases import normalize_phase, phase_defaults

        budget = project_fields.get("budget", "")
        phase = normalize_phase(project_fields.get("engagement_phase"))
        defaults = phase_defaults(phase) if phase else {}
        if not budget and defaults.get("budget"):
            budget = defaults["budget"]
        duration = project_fields.get("duration", "") or defaults.get("duration", "")
        add_project({
            "title": project_fields["title"],
            "enterprise": name,
            "enterprise_id": enterprise["id"],
            "description": project_fields.get("description", ""),
            "budget": budget,
            "budget_cents": defaults.get("budget_cents") or resolve_budget_cents(budget),
            "currency": "eur",
            "duration": duration,
            "skills": project_fields.get("skills") or [],
            "status": "Ouvert",
            "engagement_phase": phase,
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
    from data.matching import match_projects_for_startup

    enterprises = {e["id"]: e for e in get_enterprises()}
    return match_projects_for_startup(startup, get_projects(), enterprises)


def get_matching_startups_for_enterprise(enterprise):
    from data.matching import match_startups_for_enterprise

    engaged_ids = {
        e.get("startup_id")
        for e in get_engagements_for_enterprise(enterprise["id"])
        if e.get("status") not in ("cancelled", "released")
    }
    return match_startups_for_enterprise(
        enterprise,
        get_projects(),
        get_startups(),
        exclude_startup_ids=engaged_ids,
    )


def get_project(project_id):
    return next((p for p in get_projects() if p["id"] == project_id), None)


def count_open_projects_for_enterprise(enterprise_id: str) -> int:
    return sum(
        1
        for project in get_projects()
        if project.get("enterprise_id") == enterprise_id and project.get("status") == "Ouvert"
    )


def can_enterprise_add_open_project(enterprise, locale: str | None = None) -> tuple[bool, str | None]:
    from payments.pricing_plans import FREE_ENTERPRISE_MAX_OPEN_PROJECTS, is_pro_enterprise
    from vitrine.i18n import get_locale, t

    if is_pro_enterprise(enterprise):
        return True, None
    if count_open_projects_for_enterprise(enterprise["id"]) >= FREE_ENTERPRISE_MAX_OPEN_PROJECTS:
        return False, t(
            "compte.flash_project_limit",
            max=FREE_ENTERPRISE_MAX_OPEN_PROJECTS,
        )
    return True, None


def get_enterprise_plan_label(enterprise, locale: str = "fr") -> str:
    from payments.pricing_plans import ENTERPRISE_PLAN_PRO, get_enterprise_plan_id

    if get_enterprise_plan_id(enterprise) == ENTERPRISE_PLAN_PRO:
        return "Entreprise Pro" if locale == "fr" else "Enterprise Pro"
    return "Entreprise Gratuit" if locale == "fr" else "Enterprise Free"


def add_project_for_enterprise(enterprise, fields):
    from data.engagement_phases import normalize_phase, phase_defaults
    from payments.pricing_plans import FREE_ENTERPRISE_MAX_OPEN_PROJECTS, is_pro_enterprise

    status = fields.get("status", "Ouvert")
    if status == "Ouvert" and not is_pro_enterprise(enterprise):
        open_count = count_open_projects_for_enterprise(enterprise["id"])
        if open_count >= FREE_ENTERPRISE_MAX_OPEN_PROJECTS:
            raise ValueError(
                f"Limite atteinte : {FREE_ENTERPRISE_MAX_OPEN_PROJECTS} projet ouvert sur l'offre Gratuit. "
                "Passez en Pro ou archivez un projet existant."
            )

    budget = fields.get("budget", "").strip()
    phase = normalize_phase(fields.get("engagement_phase"))
    defaults = phase_defaults(phase) if phase else {}
    if not budget and defaults.get("budget"):
        budget = defaults["budget"]
    duration = fields.get("duration", "").strip() or defaults.get("duration", "")
    budget_cents = fields.get("budget_cents") or resolve_budget_cents(budget)
    return add_project({
        "title": fields.get("title", "").strip(),
        "enterprise": enterprise.get("name", ""),
        "enterprise_id": enterprise["id"],
        "description": fields.get("description", "").strip(),
        "budget": budget,
        "budget_cents": budget_cents,
        "currency": fields.get("currency", "eur"),
        "duration": duration,
        "skills": fields.get("skills") or [],
        "status": fields.get("status", "Ouvert"),
        "engagement_phase": phase,
    })


def update_project_for_enterprise(enterprise, project_id, fields):
    from data.engagement_phases import normalize_phase, phase_defaults

    project = get_project(project_id)
    if not project or project.get("enterprise_id") != enterprise.get("id"):
        return None

    budget = fields.get("budget", "").strip()
    phase = normalize_phase(fields.get("engagement_phase")) or project.get("engagement_phase")
    defaults = phase_defaults(phase) if phase else {}
    if not budget and defaults.get("budget"):
        budget = defaults["budget"]
    duration = fields.get("duration", "").strip() or defaults.get("duration", project.get("duration", ""))
    budget_cents = fields.get("budget_cents") or resolve_budget_cents(budget or project.get("budget", ""))
    status = fields.get("status", project.get("status", "Ouvert")).strip() or project.get("status", "Ouvert")

    return update_project(project_id, {
        "title": fields.get("title", "").strip(),
        "enterprise": enterprise.get("name", project.get("enterprise", "")),
        "description": fields.get("description", "").strip(),
        "budget": budget,
        "budget_cents": budget_cents,
        "duration": duration,
        "skills": fields.get("skills") or [],
        "status": status,
        "engagement_phase": phase,
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


def get_enterprise_by_stripe_customer(customer_id: str):
    if not customer_id:
        return None
    return next(
        (e for e in get_enterprises() if e.get("stripe_customer_id") == customer_id),
        None,
    )


def get_enterprise_by_subscription_id(subscription_id: str):
    if not subscription_id:
        return None
    return next(
        (e for e in get_enterprises() if e.get("stripe_subscription_id") == subscription_id),
        None,
    )


def format_engagement_label(status: str, locale: str | None = None) -> str:
    from vitrine.i18n import translate_engagement_status
    return translate_engagement_status(status or "", locale)


def _format_cents_eur(cents: int | None) -> str:
    if not cents:
        return "—"
    value = cents / 100
    if value == int(value):
        return f"{int(value):,} €".replace(",", "\u202f")
    return f"{value:,.2f} €".replace(",", "\u202f")


def enrich_engagement_for_dashboard(engagement: dict, viewer_role: str, locale: str | None = None) -> dict:
    project = get_project(engagement.get("project_id", ""))
    startup = get_startup(engagement.get("startup_id", ""))
    enterprise = get_enterprise(engagement.get("enterprise_id", ""))
    status = engagement.get("status", "")
    return {
        **engagement,
        "project_title": (project or {}).get("title", "Projet IoT"),
        "project_phase": (project or {}).get("engagement_phase", ""),
        "project_status": (project or {}).get("status", ""),
        "startup_name": (startup or {}).get("name", "—"),
        "enterprise_name": (enterprise or {}).get("name", "—"),
        "counterpart_name": (startup or {}).get("name", "—") if viewer_role == "enterprise" else (enterprise or {}).get("name", "—"),
        "status_label": format_engagement_label(status, locale),
        "status_tone": {
            "draft": "muted",
            "pending_payment": "warn",
            "escrowed": "info",
            "released": "success",
            "payment_error": "danger",
            "cancelled": "muted",
        }.get(status, "muted"),
        "amount_label": _format_cents_eur(engagement.get("amount_cents")),
        "payout_label": _format_cents_eur(engagement.get("startup_payout_cents")),
        "message_id": engagement.get("application_message_id"),
    }


def _project_pipeline(projects: list) -> dict:
    open_projects, active_projects, closed_projects = [], [], []
    for project in projects:
        status = project.get("status", "")
        if status == "Ouvert":
            open_projects.append(project)
        elif status == "En cours":
            active_projects.append(project)
        else:
            closed_projects.append(project)
    return {
        "open": open_projects,
        "active": active_projects,
        "closed": closed_projects,
        "counts": {
            "open": len(open_projects),
            "active": len(active_projects),
            "closed": len(closed_projects),
            "total": len(projects),
        },
    }


def _partnership_pipeline(engagements: list) -> dict:
    billing, escrowed, completed, other = [], [], [], []
    for engagement in engagements:
        status = engagement.get("status", "")
        if status in ("draft", "pending_payment", "payment_error"):
            billing.append(engagement)
        elif status == "escrowed":
            escrowed.append(engagement)
        elif status == "released":
            completed.append(engagement)
        else:
            other.append(engagement)
    return {
        "billing": billing,
        "escrowed": escrowed,
        "completed": completed,
        "other": other,
        "counts": {
            "billing": len(billing),
            "escrowed": len(escrowed),
            "completed": len(completed),
            "active": len(billing) + len(escrowed),
            "total": len(engagements),
        },
    }


def _build_dashboard_activity(applications: list, engagements: list, locale: str | None = None) -> list:
    from vitrine.i18n import get_locale, t
    loc = locale or get_locale()
    default_project = t("compte.dashboard.default_project_title", default="IoT project")
    default_partnership = t("compte.dashboard.default_partnership_title", default="Partnership")
    items = []
    for app in applications:
        items.append({
            "type": "application",
            "at": app.get("created_at", ""),
            "title": app.get("project_title") or default_project,
            "subtitle": app.get("counterpart_name", ""),
            "status": app.get("status", ""),
            "status_label": app.get("status_label", ""),
            "message_id": app.get("id"),
            "project_id": app.get("project_id"),
        })
    for eng in engagements:
        items.append({
            "type": "partnership",
            "at": eng.get("created_at", ""),
            "title": eng.get("project_title", default_partnership),
            "subtitle": eng.get("counterpart_name", ""),
            "status": eng.get("status", ""),
            "status_label": eng.get("status_label", ""),
            "message_id": eng.get("message_id"),
            "engagement_id": eng.get("id"),
        })
    items.sort(key=lambda row: row.get("at") or "", reverse=True)
    return items[:12]


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


def send_message(from_user, to_user, subject, body, kind="contact", project=None, status="pending", **extra):
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
        **extra,
    }
    if from_user.get("role") == "startup":
        fields["from_profile_id"] = from_user.get("profile_id")
    if from_user.get("role") == "enterprise":
        fields["from_profile_id"] = from_user.get("profile_id")
    if project:
        fields["project_id"] = project["id"]
        fields["project_title"] = project.get("title", "")
    return add_message(fields)


def apply_to_project(startup_user, startup, project, message_body, *, poc_fee_cents=None, poc_checkout_id=None):
    from data.engagement_phases import requires_startup_application_fee

    if startup_already_applied(startup["id"], project["id"]):
        raise ValueError("Vous avez déjà candidaté à ce projet.")
    if requires_startup_application_fee(project.get("engagement_phase")) and not poc_fee_cents:
        raise ValueError(
            "Les frais de candidature PoC doivent être réglés avant d'envoyer la candidature."
        )
    enterprise_user = _user_for_enterprise_id(project.get("enterprise_id"))
    if not enterprise_user:
        raise ValueError("Entreprise destinataire introuvable.")
    subject = f"Candidature — {project.get('title', 'Projet IoT')}"
    extra = {}
    if poc_fee_cents:
        extra["poc_application_fee_cents"] = int(poc_fee_cents)
        extra["poc_application_fee_paid"] = True
    if poc_checkout_id:
        extra["poc_application_checkout_id"] = poc_checkout_id
    return send_message(
        startup_user,
        enterprise_user,
        subject,
        message_body,
        kind="application",
        project=project,
        status="pending",
        **extra,
    )


def create_application_checkout(fields: dict) -> dict:
    data = _load_raw()
    entry = {
        "id": _new_id(),
        "created_at": _now().isoformat(),
        "status": "pending",
        "currency": "eur",
        **fields,
    }
    data.setdefault("application_checkouts", []).append(entry)
    _save_raw(data)
    return entry


def get_application_checkout(checkout_id: str):
    return next(
        (c for c in _load_raw().get("application_checkouts", []) if c.get("id") == checkout_id),
        None,
    )


def get_application_checkout_by_session(stripe_session_id: str):
    if not stripe_session_id:
        return None
    return next(
        (
            c for c in _load_raw().get("application_checkouts", [])
            if c.get("stripe_session_id") == stripe_session_id
        ),
        None,
    )


def update_application_checkout(checkout_id: str, fields: dict) -> dict | None:
    data = _load_raw()
    for checkout in data.get("application_checkouts", []):
        if checkout.get("id") == checkout_id:
            checkout.update(fields)
            _save_raw(data)
            return checkout
    return None


def enrich_message_for_view(msg, current_user_id, locale: str | None = None):
    from vitrine.i18n import translate_application_status, translate_message_kind
    direction = "in" if msg.get("to_user_id") == current_user_id else "out"
    return {
        **msg,
        "direction": direction,
        "kind_label": translate_message_kind(msg.get("kind"), locale),
        "status_label": translate_application_status(msg.get("status"), locale),
        "counterpart_name": msg.get("from_name") if direction == "in" else msg.get("to_name"),
    }


def get_dashboard_data_for_enterprise(user, profile, locale: str | None = None):
    from vitrine.i18n import get_locale
    loc = locale or get_locale()
    projects = get_projects_for_enterprise(profile["id"], profile.get("name", ""))
    inbox = get_inbox_for_user(user["id"])
    sent = get_sent_for_user(user["id"])
    applications = get_applications_for_enterprise(profile["id"])
    engagements_raw = get_engagements_for_enterprise(profile["id"])
    platform_contacts = get_contacts_for_user(user)
    projects_enriched = []
    for p in projects:
        apps = get_applications_for_project(p["id"])
        engagement = next((e for e in engagements_raw if e.get("project_id") == p["id"]), None)
        projects_enriched.append({
            **p,
            "applications_count": len(apps),
            "applications_pending": sum(1 for a in apps if a.get("status") == "pending"),
            "has_engagement": bool(engagement),
            "engagement_status": engagement.get("status") if engagement else None,
        })
    applications_view = [enrich_message_for_view(m, user["id"], loc) for m in applications]
    engagements = [
        enrich_engagement_for_dashboard(e, "enterprise", loc) for e in engagements_raw
    ]
    engagements.sort(key=lambda e: e.get("created_at") or "", reverse=True)
    pipeline = _project_pipeline(projects_enriched)
    partnerships = _partnership_pipeline(engagements)
    pending_apps = sum(1 for a in applications if a.get("status") == "pending")
    accepted_apps = sum(1 for a in applications if a.get("status") == "accepted")
    matching_startups = get_matching_startups_for_enterprise(profile)
    applied_startup_ids = {a.get("from_profile_id") for a in applications}
    matching_enriched = []
    for s in matching_startups:
        matching_enriched.append({
            **s,
            "already_applied": s.get("id") in applied_startup_ids,
            "user_id_for_chat": s.get("user_id"),
        })
    top_recommendations = [s for s in matching_enriched if not s.get("already_applied")][:8]
    return {
        "projects": projects_enriched,
        "pipeline": pipeline,
        "partnerships": partnerships,
        "engagements": engagements,
        "activity": _build_dashboard_activity(applications_view, engagements, loc),
        "inbox": [enrich_message_for_view(m, user["id"], loc) for m in inbox],
        "sent": [enrich_message_for_view(m, user["id"], loc) for m in sent],
        "applications": applications_view,
        "platform_contacts": platform_contacts,
        "matching_startups": matching_enriched,
        "top_recommendations": top_recommendations,
        "unread_count": get_unread_count(user["id"]),
        "stats": {
            "projects": len(projects),
            "projects_open": pipeline["counts"]["open"],
            "projects_active": pipeline["counts"]["active"],
            "partnerships": partnerships["counts"]["total"],
            "partnerships_active": partnerships["counts"]["active"],
            "messages": len(inbox) + len(sent),
            "applications": len(applications),
            "applications_pending": pending_apps,
            "applications_accepted": accepted_apps,
            "unread": get_unread_count(user["id"]),
            "contacts": len(platform_contacts),
            "matching_startups": len(matching_enriched),
            "matching_startups_top": len(top_recommendations),
        },
    }


def get_dashboard_data_for_startup(user, profile, locale: str | None = None):
    from vitrine.i18n import get_locale
    loc = locale or get_locale()
    matching = get_matching_projects_for_startup(profile)
    inbox = get_inbox_for_user(user["id"])
    sent = get_sent_for_user(user["id"])
    applications = get_applications_for_startup(profile["id"])
    engagements_raw = get_engagements_for_startup(profile["id"])
    applied_ids = {a.get("project_id") for a in applications}
    matching_enriched = []
    for p in matching:
        matching_enriched.append({
            **p,
            "already_applied": p["id"] in applied_ids,
        })
    applications_view = [enrich_message_for_view(m, user["id"], loc) for m in applications]
    engagements = [
        enrich_engagement_for_dashboard(e, "startup", loc) for e in engagements_raw
    ]
    engagements.sort(key=lambda e: e.get("created_at") or "", reverse=True)
    partnerships = _partnership_pipeline(engagements)
    pending_apps = sum(1 for a in applications if a.get("status") == "pending")
    accepted_apps = sum(1 for a in applications if a.get("status") == "accepted")
    open_matching = [p for p in matching_enriched if p.get("status") == "Ouvert" and not p.get("already_applied")]
    open_matching.sort(key=lambda p: (-(p.get("match_score") or 0), p.get("title") or ""))
    matching_enriched.sort(key=lambda p: (-(p.get("match_score") or 0), p.get("title") or ""))
    return {
        "matching_projects": matching_enriched,
        "open_matching": open_matching,
        "partnerships": partnerships,
        "engagements": engagements,
        "activity": _build_dashboard_activity(applications_view, engagements, loc),
        "inbox": [enrich_message_for_view(m, user["id"], loc) for m in inbox],
        "sent": [enrich_message_for_view(m, user["id"], loc) for m in sent],
        "applications": applications_view,
        "platform_contacts": get_contacts_for_user(user),
        "unread_count": get_unread_count(user["id"]),
        "stats": {
            "applications": len(applications),
            "applications_pending": pending_apps,
            "applications_accepted": accepted_apps,
            "messages": len(inbox) + len(sent),
            "matching": len(matching_enriched),
            "matching_open": len(open_matching),
            "partnerships": partnerships["counts"]["total"],
            "partnerships_active": partnerships["counts"]["active"],
            "unread": get_unread_count(user["id"]),
        },
    }


def get_page_catalog():
    return build_page_catalog()


def get_page_meta(slug):
    return get_page_entry(slug)


def get_page_content(slug, locale="en"):
    if slug in ("domains",) or parse_domain_page_slug(slug):
        return {"published": True}
    data = _load_raw()
    saved = data.get("pages", {}).get(slug, {})
    defaults = (DEFAULT_PAGE_CONTENT_FR if locale == "fr" else DEFAULT_PAGE_CONTENT).get(slug, {})
    if slug in ("privacy", "legal", "cookies") and "body_html" not in defaults:
        from data.legal_content import get_legal_body

        defaults = {**defaults, "body_html": get_legal_body(slug, locale)}
    meta_keys = {"published", "updated_at", "en", "fr"}
    if isinstance(saved.get(locale), dict):
        return {**defaults, **saved[locale], "published": saved.get("published", True)}
    legacy = {k: v for k, v in saved.items() if k not in meta_keys}
    return {**defaults, **legacy, "published": saved.get("published", True)}


def get_all_pages():
    rows = []
    for page in build_page_catalog():
        row = {
            "slug": page["slug"],
            "name": page["name"],
            "path": page["path"],
            "kind": page.get("kind", "cms"),
            "group": page.get("group", "vitrine"),
            "editable": page.get("editable", page.get("kind") == "cms"),
            **get_page_content(page["slug"]),
        }
        rows.append(row)
    return rows


def update_page(slug, fields):
    data = _load_raw()
    if "pages" not in data:
        data["pages"] = {}
    current = data["pages"].get(slug, {})
    data["pages"][slug] = {**current, **fields, "updated_at": datetime.now(timezone.utc).isoformat()}
    _save_raw(data)
    return data["pages"][slug]


# ── SEO ──


def default_og_image() -> str:
    return BRAND_OG_IMAGE


def get_site_url():
    env_url = os.environ.get("SITE_URL", "").strip().rstrip("/")
    if env_url:
        return env_url
    global_seo = get_seo_global()
    saved = (global_seo.get("site_url") or "").strip().rstrip("/")
    if saved:
        return saved
    return PRODUCTION_SITE_URL


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
            "privacy": {"title": "Politique de confidentialité — Iotplace", "description": "Traitement des données personnelles sur Iotplace : formulaire, comptes, analytics et vos droits RGPD.", "keywords": "confidentialité Iotplace, RGPD, données personnelles"},
            "legal": {"title": "Mentions légales — Iotplace", "description": "Éditeur, hébergement et propriété intellectuelle du site iotplace.fr.", "keywords": "mentions légales Iotplace, SARL, RCS Nanterre"},
            "cookies": {"title": "Politique cookies — Iotplace", "description": "Cookies utilisés sur Iotplace et gestion de vos préférences de consentement.", "keywords": "cookies Iotplace, consentement, analytics"},
        }
    else:
        defaults_map = DEFAULT_SEO_PAGES
    defaults = defaults_map.get(slug, {})
    if slug == "domains" or parse_domain_page_slug(slug):
        locale_defaults = get_domain_seo_defaults(slug, locale)
        defaults = {**locale_defaults, **defaults}
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
            "og_image": BRAND_OG_IMAGE,
            "og_image_abs": f"{get_site_url()}{BRAND_OG_IMAGE}",
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
    og_image = global_seo.get("og_image", "") or BRAND_OG_IMAGE
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
    from data.geo import organization_schema_extras

    lang_tag = "fr-FR" if locale == "fr" else "en-US"
    global_seo = get_seo_global()
    site_name = global_seo.get("site_name", "Iotplace")
    seo = get_seo_for_vitrine(slug, locale=locale)
    graphs = []

    org = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": site_name,
        "url": site_url,
        "logo": f"{site_url}{BRAND_LOGO_IMAGE}" if site_url else "",
        "description": global_seo.get("meta_description", ""),
    }
    org.update(organization_schema_extras(site_url))
    graphs.append(org)

    graphs.append({
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": site_name,
        "url": site_url,
        "description": global_seo.get("meta_description", ""),
        "inLanguage": lang_tag,
        "potentialAction": {
            "@type": "SearchAction",
            "target": f"{site_url}/projects?q={{search_term_string}}",
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

    if slug in ("home", "enterprises", "startups", "projects"):
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

    if slug == "pricing":
        graphs.append({
            "@context": "https://schema.org",
            "@type": "Product",
            "name": "Iotplace Enterprise Pro",
            "description": "Unlimited IoT projects, 7% commission, priority matching and dedicated support.",
            "brand": {"@type": "Brand", "name": site_name},
            "url": canonical_url,
        })

    return graphs


def get_sitemap_entries():
    site_url = get_site_url()
    entries = []
    for page in build_page_catalog():
        content = get_page_content(page["slug"])
        if not content.get("published", True):
            continue
        if page.get("kind") not in ("cms", "locale", "domain"):
            continue
        priority = "1.0" if page["slug"] == "home" else "0.85" if page.get("group") == "domaines" else "0.8"
        entries.append({
            "loc": f"{site_url}{page['path']}",
            "changefreq": "weekly" if page["slug"] == "home" else "monthly",
            "priority": priority,
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
    from data.engagement_phases import ENGAGEMENT_PHASES
    for phase in ENGAGEMENT_PHASES:
        entries.append({
            "loc": f"{site_url}/projects?phase={phase}",
            "changefreq": "weekly",
            "priority": "0.75",
        })
    for startup in get_public_startups():
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
    for geo_path in ("/llms.txt", "/llms-full.txt", "/knowledge", "/knowledge.json", "/ai.txt"):
        entries.append({
            "loc": f"{site_url}{geo_path}",
            "changefreq": "weekly",
            "priority": "0.5",
        })
    for page in build_page_catalog():
        if page.get("kind") not in ("cms", "locale", "domain"):
            continue
        for lang in ("fr", "en"):
            base = page["path"]
            sep = "&" if "?" in base else "?"
            entries.append({
                "loc": f"{site_url}{base}{sep}lang={lang}",
                "changefreq": "monthly",
                "priority": "0.75" if page["slug"] == "home" else "0.65",
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
    from data.geo import build_robots_txt

    return build_robots_txt(get_site_url())


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


# ── CRM Mailing ──

def get_mail_settings():
    data = _load_raw()
    defaults = {**DEFAULT_DATA["mail_settings"], "reply_to": CONTACT_EMAIL}
    saved = data.get("mail_settings") or {}
    merged = {**defaults, **saved}
    if not (merged.get("reply_to") or "").strip():
        merged["reply_to"] = CONTACT_EMAIL
    return merged


def update_mail_settings(fields: dict) -> dict:
    data = _load_raw()
    current = get_mail_settings()
    data["mail_settings"] = {**current, **fields}
    _save_raw(data)
    return data["mail_settings"]


def get_mail_campaigns():
    return sorted(
        _load_raw().get("mail_campaigns", []),
        key=lambda c: c.get("updated_at") or c.get("created_at", ""),
        reverse=True,
    )


def get_mail_campaign(campaign_id: str):
    return next((c for c in get_mail_campaigns() if c["id"] == campaign_id), None)


def _empty_mail_stats():
    return {"recipients": 0, "sent": 0, "failed": 0, "opened": 0, "clicked": 0}


def add_mail_campaign(fields):
    data = _load_raw()
    now = datetime.now(timezone.utc).isoformat()
    entry = {
        "id": _new_id(),
        "created_at": now,
        "updated_at": now,
        "status": "draft",
        "source": fields.get("source", "manual"),
        "stats": _empty_mail_stats(),
        "sends": [],
        **fields,
    }
    data.setdefault("mail_campaigns", []).append(entry)
    _save_raw(data)
    return entry


def update_mail_campaign(campaign_id: str, fields: dict):
    data = _load_raw()
    for i, camp in enumerate(data.get("mail_campaigns", [])):
        if camp["id"] == campaign_id:
            updated = {
                **camp,
                **fields,
                "id": campaign_id,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            data["mail_campaigns"][i] = updated
            _save_raw(data)
            return updated
    return None


def delete_mail_campaign(campaign_id: str):
    data = _load_raw()
    data["mail_campaigns"] = [c for c in data.get("mail_campaigns", []) if c["id"] != campaign_id]
    data["mail_events"] = [e for e in data.get("mail_events", []) if e.get("campaign_id") != campaign_id]
    _save_raw(data)


def log_mail_event(campaign_id: str, event_type: str, email: str = "", meta: dict | None = None):
    data = _load_raw()
    entry = {
        "id": _new_id(),
        "campaign_id": campaign_id,
        "type": event_type,
        "email": (email or "").strip().lower(),
        "at": datetime.now(timezone.utc).isoformat(),
        "meta": meta or {},
    }
    data.setdefault("mail_events", []).append(entry)
    _save_raw(data)
    return entry


def record_mail_open(campaign_id: str, token: str) -> bool:
    camp = get_mail_campaign(campaign_id)
    if not camp:
        return False
    email_addr = ""
    already = False
    sends = list(camp.get("sends") or [])
    for send in sends:
        if send.get("token") == token:
            email_addr = send.get("email", "")
            if send.get("opened_at"):
                already = True
            else:
                send["opened_at"] = datetime.now(timezone.utc).isoformat()
            break
    if already:
        return True
    stats = {**_empty_mail_stats(), **(camp.get("stats") or {})}
    stats["opened"] = int(stats.get("opened") or 0) + 1
    update_mail_campaign(campaign_id, {"sends": sends, "stats": stats})
    log_mail_event(campaign_id, "open", email_addr, {"token": token})
    return True


def resolve_mail_recipients(audience: str, custom_recipients: list | None = None) -> list[dict]:
    custom_recipients = custom_recipients or []
    seen: set[str] = set()
    out: list[dict] = []

    def add(email: str, name: str = "", source: str = ""):
        email_l = (email or "").strip().lower()
        if not email_l or "@" not in email_l or email_l in seen:
            return
        seen.add(email_l)
        out.append({"email": email_l, "name": name or email_l, "source": source})

    if audience == "custom":
        for raw in custom_recipients:
            if isinstance(raw, dict):
                add(raw.get("email", ""), raw.get("name", ""), "custom")
            else:
                add(str(raw), "", "custom")
        return out

    if audience == "contacts":
        for c in get_contacts():
            add(c.get("email", ""), c.get("name", ""), "contact")
    elif audience == "enterprises":
        for u in get_all_users():
            if u.get("role") != "enterprise":
                continue
            ent = get_enterprise(u.get("profile_id"))
            add(u.get("email", ""), (ent or {}).get("name", ""), "enterprise")
    elif audience == "startups":
        for u in get_all_users():
            if u.get("role") != "startup":
                continue
            st = get_startup(u.get("profile_id"))
            add(u.get("email", ""), (st or {}).get("name", ""), "startup")
    elif audience == "all_users":
        for u in get_all_users():
            profile_name = ""
            if u.get("role") == "enterprise":
                ent = get_enterprise(u.get("profile_id"))
                profile_name = (ent or {}).get("name", "")
            elif u.get("role") == "startup":
                st = get_startup(u.get("profile_id"))
                profile_name = (st or {}).get("name", "")
            add(u.get("email", ""), profile_name, u.get("role", "user"))
    return out


def send_mail_campaign(campaign_id: str) -> dict:
    from crm.email_service import EmailError, get_smtp_config, is_smtp_configured, recipient_token, send_email

    if not is_smtp_configured():
        raise ValueError("SMTP non configuré — vérifiez les variables d'environnement.")

    camp = get_mail_campaign(campaign_id)
    if not camp:
        raise ValueError("Campagne introuvable.")
    if camp.get("status") == "sent":
        raise ValueError("Cette campagne a déjà été envoyée.")

    recipients = resolve_mail_recipients(camp.get("audience", "contacts"), camp.get("custom_recipients"))
    if not recipients:
        raise ValueError("Aucun destinataire pour cette audience.")

    settings = get_mail_settings()
    site_url = get_site_url().rstrip("/")
    subject = (camp.get("subject") or "").strip()
    body_html = (camp.get("body_html") or "").strip()
    if not subject or not body_html:
        raise ValueError("Objet et contenu HTML requis.")

    locale = (camp.get("locale") or "fr").strip().lower()
    if locale not in ("fr", "en"):
        locale = "fr"

    signature = (settings.get("signature") or "").strip()
    if signature and signature not in body_html:
        body_html = (
            f"{body_html}"
            f"<p style='margin-top:24px;padding-top:16px;border-top:1px solid rgba(0,232,200,0.15);color:#8b95a8;font-size:13px;'>"
            f"{signature}</p>"
        )

    reply_to = (settings.get("reply_to") or "").strip() or get_platform_email()
    sends = []
    sent = 0
    failed = 0

    update_mail_campaign(campaign_id, {"status": "sending", "stats": {**_empty_mail_stats(), "recipients": len(recipients)}})

    for rec in recipients:
        token = recipient_token(campaign_id, rec["email"])
        tracking_url = f"{site_url}/mail/o/{campaign_id}/{token}.gif"
        send_row = {
            "email": rec["email"],
            "name": rec.get("name", ""),
            "source": rec.get("source", ""),
            "token": token,
            "status": "pending",
        }
        try:
            send_email(
                rec["email"],
                subject,
                body_html,
                body_text=camp.get("body_text") or "",
                reply_to=reply_to,
                tracking_url=tracking_url,
                site_url=site_url,
                locale=locale,
            )
            send_row["status"] = "sent"
            send_row["sent_at"] = datetime.now(timezone.utc).isoformat()
            sent += 1
            log_mail_event(campaign_id, "sent", rec["email"])
        except EmailError as exc:
            send_row["status"] = "failed"
            send_row["error"] = str(exc)
            failed += 1
            log_mail_event(campaign_id, "failed", rec["email"], {"error": str(exc)})
        sends.append(send_row)

    stats = {
        "recipients": len(recipients),
        "sent": sent,
        "failed": failed,
        "opened": (camp.get("stats") or {}).get("opened", 0),
        "clicked": (camp.get("stats") or {}).get("clicked", 0),
    }
    update_mail_campaign(campaign_id, {
        "status": "sent" if sent else "failed",
        "sent_at": datetime.now(timezone.utc).isoformat(),
        "sends": sends,
        "stats": stats,
    })
    return {"sent": sent, "failed": failed, "recipients": len(recipients)}


def get_mail_analytics():
    campaigns = get_mail_campaigns()
    events = _load_raw().get("mail_events", [])
    totals = _empty_mail_stats()
    totals["campaigns"] = len(campaigns)
    totals["drafts"] = sum(1 for c in campaigns if c.get("status") == "draft")
    for camp in campaigns:
        stats = camp.get("stats") or {}
        for key in ("recipients", "sent", "failed", "opened", "clicked"):
            totals[key] = totals.get(key, 0) + int(stats.get(key) or 0)
    recent_events = sorted(events, key=lambda e: e.get("at", ""), reverse=True)[:30]
    return {
        "totals": totals,
        "campaigns": campaigns[:12],
        "recent_events": recent_events,
    }


def sync_mail_inbox(limit: int = 40) -> list[dict]:
    from crm.email_service import fetch_inbox

    messages = fetch_inbox(limit=limit)
    update_mail_settings({
        "last_inbox_sync": datetime.now(timezone.utc).isoformat(),
        "inbox_cache": messages,
    })
    return messages


def get_mail_inbox_cache():
    settings = get_mail_settings()
    return settings.get("inbox_cache") or []
