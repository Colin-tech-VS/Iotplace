import json
import os
import uuid
from urllib.parse import quote
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

DATA_FILE = Path(__file__).parent / "content.json"

PAGE_CATALOG = [
    {"slug": "home", "name": "Accueil", "path": "/", "vitrine_endpoint": "vitrine.index"},
    {"slug": "enterprises", "name": "Entreprises", "path": "/entreprises", "vitrine_endpoint": "vitrine.enterprises"},
    {"slug": "startups", "name": "Startups", "path": "/startups", "vitrine_endpoint": "vitrine.startups"},
    {"slug": "projects", "name": "Projets", "path": "/projets", "vitrine_endpoint": "vitrine.projects"},
    {"slug": "about", "name": "À propos", "path": "/a-propos", "vitrine_endpoint": "vitrine.about"},
    {"slug": "contact", "name": "Contact", "path": "/contact", "vitrine_endpoint": "vitrine.contact"},
]

DEFAULT_PAGE_CONTENT = {
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
}

DEFAULT_SEO_PAGES = {
    "home": {
        "title": "Sous-traitance IoT B2B — Entreprises & Startups Asie",
        "description": (
            "Iotplace, marketplace IoT B2B : entreprises, externalisez firmware, hardware et cloud "
            "vers des startups qualifiées en Asie du Sud-Est. Startups IoT, accédez aux missions "
            "de sous-traitance des grands groupes."
        ),
        "keywords": (
            "sous-traitance IoT, externalisation IoT, marketplace IoT B2B, startups IoT Asie, "
            "Vietnam IoT, Indonésie IoT, firmware IoT, hardware connecté, missions IoT entreprise"
        ),
    },
    "enterprises": {
        "title": "Externaliser vos projets IoT — Sous-traiter des startups",
        "description": (
            "Entreprise IoT : publiez vos besoins et sous-traitez firmware, PCB, cloud et intégration "
            "à des startups vietnamiennes et asiatiques qualifiées. Matching, contrats et suivi sur Iotplace."
        ),
        "keywords": (
            "entreprise sous-traiter IoT, externalisation projet IoT, sous-traitance firmware, "
            "développement IoT offshore, startups IoT Vietnam, donneur d'ordre IoT"
        ),
    },
    "startups": {
        "title": "Startups IoT — Missions de sous-traitance entreprises",
        "description": (
            "Startup IoT en Asie du Sud-Est : trouvez des projets de sous-traitance publiés par "
            "les grandes entreprises — firmware, PCB, LoRaWAN, cloud IoT, intégration hardware."
        ),
        "keywords": (
            "startup IoT missions, sous-traitance IoT startup, projet IoT entreprise, "
            "Vietnam développement IoT, startup hardware connecté, freelance IoT B2B"
        ),
    },
    "projects": {
        "title": "Projets IoT ouverts — Missions de sous-traitance",
        "description": (
            "Liste des projets IoT ouverts à la sous-traitance : firmware, capteurs, cloud, "
            "intégration. Startups IoT, postulez aux missions publiées par les entreprises sur Iotplace."
        ),
        "keywords": (
            "projets IoT ouverts, mission sous-traitance IoT, appel d'offres IoT, "
            "projet firmware startup, budget IoT externalisation"
        ),
    },
    "about": {
        "title": "À propos — Marketplace sous-traitance IoT B2B",
        "description": (
            "Iotplace structure la sous-traitance IoT entre entreprises mondiales et startups "
            "d'Asie du Sud-Est : Vietnam, Indonésie, Thaïlande, Philippines."
        ),
        "keywords": (
            "marketplace IoT, sous-traitance IoT Asie, hub IoT Vietnam, "
            "externalisation hardware firmware, plateforme B2B IoT"
        ),
    },
    "contact": {
        "title": "Contact — Démarrer une sous-traitance IoT",
        "description": (
            "Contactez Iotplace : entreprise cherchant à sous-traiter un projet IoT ou startup "
            "IoT cherchant des missions. Réponse sous 48 h."
        ),
        "keywords": (
            "contact sous-traitance IoT, rejoindre marketplace IoT, "
            "publier projet IoT, inscription startup IoT"
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
            "q": "Comment une entreprise peut-elle sous-traiter un projet IoT sur Iotplace ?",
            "a": "Créez un compte entreprise, décrivez votre besoin (firmware, hardware, cloud) et publiez votre projet. Iotplace vous met en relation avec des startups IoT qualifiées en Asie du Sud-Est.",
        },
        {
            "q": "Comment une startup IoT trouve-t-elle des missions de sous-traitance ?",
            "a": "Inscrivez votre startup, renseignez vos compétences IoT et parcourez les projets ouverts publiés par les entreprises. Postulez directement aux missions qui correspondent à votre expertise.",
        },
        {
            "q": "Quels types de projets IoT peut-on sous-traiter ?",
            "a": "Firmware embarqué, conception PCB, capteurs connectés, protocoles LoRaWAN/MQTT, backends cloud, applications mobiles IoT et intégration système complète.",
        },
        {
            "q": "Pourquoi externaliser vers des startups IoT en Asie du Sud-Est ?",
            "a": "Coûts compétitifs, équipes agiles, expertise hardware héritée de l'électronique grand public et fuseaux horaires favorables pour les entreprises européennes et américaines.",
        },
    ],
    "enterprises": [
        {
            "q": "Quels avantages pour externaliser un projet IoT vers une startup ?",
            "a": "Time-to-market réduit, coûts maîtrisés, accès à des talents spécialisés firmware et hardware sans recruter en interne, avec flexibilité sur la durée des missions.",
        },
        {
            "q": "Comment Iotplace sécurise la sous-traitance IoT ?",
            "a": "NDA, contrats encadrés, suivi de projet via la plateforme et paiements sécurisés. Vous gardez le contrôle sur les livrables et la propriété intellectuelle.",
        },
        {
            "q": "Quelles compétences IoT sont disponibles chez les startups partenaires ?",
            "a": "Firmware C/C++, RTOS, PCB design, IoT cloud (AWS, Azure), LoRaWAN, BLE, MQTT, prototypage rapide et production en petite série.",
        },
    ],
    "startups": [
        {
            "q": "Comment accéder aux projets de sous-traitance IoT des entreprises ?",
            "a": "Créez votre profil startup sur Iotplace, listez vos compétences et consultez la page Projets ouverts. Postulez aux missions qui correspondent à votre stack technique.",
        },
        {
            "q": "Quels profils de startups IoT sont recherchés ?",
            "a": "Équipes expertes en firmware embarqué, électronique, cloud IoT ou intégration bout-en-bout, idéalement basées au Vietnam, en Indonésie, en Thaïlande ou dans la région ASEAN.",
        },
        {
            "q": "Les missions sont-elles en sous-traitance B2B encadrée ?",
            "a": "Oui. Les entreprises publient des cahiers des charges avec budget et délais. Iotplace facilite le matching, la contractualisation et le suivi jusqu'à la livraison.",
        },
    ],
    "projects": [
        {
            "q": "Comment postuler à un projet IoT ouvert ?",
            "a": "Créez un compte startup, complétez votre profil avec vos compétences et contactez l'entreprise via Iotplace ou postulez directement depuis votre tableau de bord.",
        },
        {
            "q": "Qui publie les projets de sous-traitance IoT ?",
            "a": "Les grandes entreprises et groupes industriels inscrits sur Iotplace qui externalisent une partie de leur développement IoT vers des startups qualifiées.",
        },
    ],
}

BREADCRUMB_LABELS = {
    "home": "Accueil",
    "enterprises": "Entreprises",
    "startups": "Startups IoT",
    "projects": "Projets IoT",
    "about": "À propos",
    "contact": "Contact",
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
                "Iotplace : marketplace B2B de sous-traitance IoT. Entreprises, externalisez vos projets "
                "vers des startups qualifiées en Asie. Startups IoT, trouvez des missions des grands groupes."
            ),
            "keywords": (
                "sous-traitance IoT, externalisation IoT, marketplace IoT B2B, startups IoT Asie, "
                "Vietnam, Indonésie, firmware, hardware connecté, missions IoT"
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
    },
    "social_posts": [],
    "users": [],
    "messages": [],
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
        add_project({
            "title": project_fields["title"],
            "enterprise": name,
            "enterprise_id": enterprise["id"],
            "description": project_fields.get("description", ""),
            "budget": project_fields.get("budget", ""),
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
    return add_project({
        "title": fields.get("title", "").strip(),
        "enterprise": enterprise.get("name", ""),
        "enterprise_id": enterprise["id"],
        "description": fields.get("description", "").strip(),
        "budget": fields.get("budget", "").strip(),
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
    return {
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


def get_page_content(slug):
    data = _load_raw()
    saved = data.get("pages", {}).get(slug, {})
    defaults = DEFAULT_PAGE_CONTENT.get(slug, {})
    return {**defaults, **saved, "published": saved.get("published", True)}


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


def get_seo_page(slug):
    data = _load_raw()
    saved = data.get("seo", {}).get("pages", {}).get(slug, {})
    defaults = DEFAULT_SEO_PAGES.get(slug, {})
    meta = get_page_meta(slug) or {}
    base = {
        "title": defaults.get("title") or meta.get("name", slug),
        "description": defaults.get("description", ""),
        "keywords": defaults.get("keywords", ""),
    }
    return {**base, **saved}


def get_startups_country_seo(country):
    return {
        "title": f"Startups IoT {country} — Sous-traitance entreprises",
        "description": (
            f"Startups IoT au {country} : trouvez des missions de sous-traitance publiées par "
            f"les grandes entreprises — firmware, PCB, cloud et intégration hardware sur Iotplace."
        ),
        "keywords": (
            f"startup IoT {country}, sous-traitance IoT {country}, "
            f"externalisation IoT, développement firmware {country}"
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
            "locale": "fr_FR",
        }
    return get_seo_for_vitrine(
        "home",
        title=defaults.get("title"),
        description=defaults.get("description"),
        keywords=defaults.get("keywords"),
        robots=defaults.get("robots", "noindex, follow"),
    )


def get_seo_for_vitrine(slug, page_title="", overrides=None, robots="index, follow", **kwargs):
    global_seo = get_seo_global()
    page_seo = get_seo_page(slug)
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
        "locale": "fr_FR",
    }


def get_page_faq(slug):
    return PAGE_FAQ.get(slug, [])


def build_breadcrumbs(slug, site_url, extra=None):
    items = [{"name": "Accueil", "url": f"{site_url}/"}]
    if slug != "home":
        label = BREADCRUMB_LABELS.get(slug, slug)
        meta = get_page_meta(slug)
        path = meta["path"] if meta else f"/{slug}"
        items.append({"name": label, "url": f"{site_url}{path}"})
    if extra:
        items.append(extra)
    return items


def build_json_ld(slug, canonical_url, site_url, faq=None, breadcrumbs=None):
    global_seo = get_seo_global()
    site_name = global_seo.get("site_name", "Iotplace")
    seo = get_seo_for_vitrine(slug)
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
        "inLanguage": "fr-FR",
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
        "inLanguage": "fr-FR",
    })

    crumbs = breadcrumbs or build_breadcrumbs(slug, site_url)
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

    faq_items = faq if faq is not None else get_page_faq(slug)
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
            "name": "Marketplace sous-traitance IoT B2B",
            "provider": {"@type": "Organization", "name": site_name},
            "areaServed": ["Vietnam", "Indonésie", "Thaïlande", "Philippines", "Asie du Sud-Est"],
            "serviceType": "Sous-traitance et externalisation de projets IoT",
            "audience": [
                {"@type": "BusinessAudience", "audienceType": "Entreprises IoT cherchant à sous-traiter"},
                {"@type": "BusinessAudience", "audienceType": "Startups IoT cherchant des missions"},
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
    return entries


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
