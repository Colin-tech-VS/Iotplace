import json
import uuid
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
        "hero_badge": "Marketplace IoT B2B — Asie × Monde",
        "hero_title": "Connectez les géants de l'IoT aux startups d'Asie du Sud-Est",
        "hero_highlight": "géants de l'IoT",
        "hero_subtitle": "Iotplace met en relation les grandes entreprises qui sous-traitent leurs projets IoT avec les startups vietnamiennes, indonésiennes et d'Asie du Sud-Est.",
        "cta_primary": "Je suis une entreprise",
        "cta_secondary": "Je suis une startup",
    },
    "enterprises": {
        "title": "Pour les grandes entreprises",
        "subtitle": "Externalisez vos projets IoT vers des startups qualifiées en Asie du Sud-Est.",
    },
    "startups": {
        "title": "Startups IoT d'Asie",
        "subtitle": "Des équipes expertes en Asie du Sud-Est, prêtes à être sous-traitées.",
    },
    "projects": {
        "title": "Projets de sous-traitance",
        "subtitle": "Missions IoT publiées par les grandes entreprises.",
    },
    "about": {
        "title": "À propos d'Iotplace",
        "subtitle": "La plateforme qui structure la sous-traitance IoT entre l'Occident et l'Asie du Sud-Est.",
        "mission_1": "L'Internet des Objets connaît une croissance exponentielle. Les grandes entreprises ont des besoins massifs en développement hardware, firmware et cloud.",
        "mission_2": "Iotplace comble ce fossé en offrant une marketplace B2B dédiée à la sous-traitance IoT.",
    },
    "contact": {
        "title": "Nous contacter",
        "subtitle": "Entreprise ou startup, rejoignez Iotplace et commencez à collaborer.",
        "email": "hello@iotplace.io",
    },
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
            "title_suffix": " — Marketplace IoT B2B",
            "meta_description": "Iotplace connecte les grandes entreprises IoT aux startups d'Asie du Sud-Est.",
            "keywords": "IoT, sous-traitance, startups, Vietnam, Indonésie, B2B",
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

def get_seo_global():
    data = _load_raw()
    return _deep_merge(DEFAULT_DATA["seo"]["global"], data.get("seo", {}).get("global", {}))


def get_seo_page(slug):
    data = _load_raw()
    saved = data.get("seo", {}).get("pages", {}).get(slug, {})
    meta = get_page_meta(slug) or {}
    defaults = {
        "title": meta.get("name", slug),
        "description": "",
        "keywords": "",
    }
    return {**defaults, **saved}


def get_seo_for_vitrine(slug, page_title=""):
    global_seo = get_seo_global()
    page_seo = get_seo_page(slug)
    title = page_seo.get("title") or page_title or global_seo.get("site_name", "Iotplace")
    suffix = global_seo.get("title_suffix", "")
    full_title = f"{title}{suffix}" if suffix and suffix not in title else title
    return {
        "title": full_title,
        "description": page_seo.get("description") or global_seo.get("meta_description", ""),
        "keywords": page_seo.get("keywords") or global_seo.get("keywords", ""),
        "og_image": global_seo.get("og_image", ""),
        "google_analytics_id": global_seo.get("google_analytics_id", ""),
    }


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
