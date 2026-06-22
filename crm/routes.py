from flask import Flask, jsonify, render_template, request, redirect, url_for, flash

from crm import auth as crm_auth
from crm import crm_bp
from data import store


def _nav_stats():
    data = store.get_all()
    stats = store.get_stats()
    stats["contacts"] = store.count_new_contacts() or len(data["contacts"])
    stats["contacts_total"] = len(data["contacts"])
    stats["social_drafts"] = len([p for p in data.get("social_posts", []) if p.get("status") == "draft"])
    stats["mail_drafts"] = len([c for c in data.get("mail_campaigns", []) if c.get("status") == "draft"])
    stats["users"] = len(data.get("users", []))
    return stats


@crm_bp.context_processor
def inject_crm_nav():
    return {"nav_stats": _nav_stats()}


@crm_bp.before_request
def protect_crm():
    endpoint = request.endpoint or ""
    if endpoint in ("crm.login", "crm.logout") or endpoint.startswith("crm.static"):
        return None
    if not crm_auth.is_crm_configured():
        if endpoint.startswith("crm.") and "api" in endpoint:
            return jsonify({"ok": False, "error": "CRM non configuré."}), 503
        return redirect(url_for("crm.login"))
    if not crm_auth.is_crm_authenticated():
        return redirect(url_for("crm.login", next=request.path))


@crm_bp.after_request
def crm_security_headers(response):
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
    response.headers["Pragma"] = "no-cache"
    return response


@crm_bp.route("/login", methods=["GET", "POST"])
def login():
    if not crm_auth.is_crm_configured():
        return render_template("crm/login.html", configured=False, locked=False, csrf_token="", next_url=""), 503

    if crm_auth.is_crm_authenticated():
        return redirect(crm_auth.safe_next_url(request.args.get("next")))

    locked = crm_auth.is_login_locked()
    next_url = crm_auth.safe_next_url(request.args.get("next") or request.form.get("next"))

    if request.method == "POST":
        if locked:
            flash("Trop de tentatives. Réessayez plus tard.", "error")
            return render_template(
                "crm/login.html",
                configured=True,
                locked=True,
                csrf_token=crm_auth.get_csrf_token(),
                next_url=next_url,
            ), 429

        if not crm_auth.validate_csrf(request.form.get("csrf_token", "")):
            flash("Session expirée. Réessayez.", "error")
            return render_template(
                "crm/login.html",
                configured=True,
                locked=False,
                csrf_token=crm_auth.get_csrf_token(),
                next_url=next_url,
            ), 400

        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if crm_auth.verify_crm_login(username, password):
            crm_auth.clear_login_attempts()
            crm_auth.login_crm_admin()
            flash("Connexion réussie.", "success")
            return redirect(next_url)

        crm_auth.record_failed_login()
        flash("Identifiant ou mot de passe incorrect.", "error")
        locked = crm_auth.is_login_locked()

    return render_template(
        "crm/login.html",
        configured=True,
        locked=locked,
        csrf_token=crm_auth.get_csrf_token(),
        next_url=next_url,
    )


@crm_bp.route("/logout", methods=["POST"])
def logout():
    crm_auth.logout_crm_admin()
    flash("Vous êtes déconnecté.", "success")
    return redirect(url_for("crm.login"))


# ── Dashboard ──

@crm_bp.route("/")
def dashboard():
    data = store.get_all()
    stats = _nav_stats()
    analytics = store.get_analytics()
    open_projects = [p for p in data["projects"] if p.get("status") == "Ouvert"]
    featured_startups = [s for s in data["startups"] if s.get("featured")]
    return render_template(
        "crm/dashboard.html",
        stats=stats,
        analytics=analytics,
        contacts=data["contacts"][:6],
        open_projects=open_projects[:5],
        featured_startups=featured_startups[:4],
    )


# ── Pages ──

@crm_bp.route("/pages")
def pages():
    from data.site_pages import get_pages_by_group

    return render_template(
        "crm/pages.html",
        pages=store.get_all_pages(),
        page_groups=get_pages_by_group(),
    )


@crm_bp.route("/pages/<slug>", methods=["GET", "POST"])
def edit_page(slug):
    meta = store.get_page_meta(slug)
    if not meta:
        flash("Page introuvable.", "error")
        return redirect(url_for("crm.pages"))
    if not meta.get("editable", meta.get("kind") == "cms"):
        flash("Cette page est gérée via les fichiers i18n (domaines) — utilisez le dépôt ou le SEO CRM.", "error")
        return redirect(url_for("crm.pages"))

    content = store.get_page_content(slug)
    if request.method == "POST":
        fields = {k: v for k, v in request.form.items() if k != "published"}
        fields["published"] = request.form.get("published") == "on"
        store.update_page(slug, fields)
        flash("Page mise à jour.", "success")
        return redirect(url_for("crm.pages"))
    from crm import mistral_ai

    return render_template(
        "crm/page_edit.html",
        meta=meta,
        content=content,
        mistral_configured=mistral_ai.is_configured(),
    )


@crm_bp.route("/api/pages/<slug>/generate", methods=["POST"])
def api_page_generate(slug):
    from crm import mistral_ai

    if not mistral_ai.is_configured():
        return jsonify({"ok": False, "error": "MISTRAL_API_KEY is not configured."}), 503

    meta = store.get_page_meta(slug)
    if not meta:
        return jsonify({"ok": False, "error": "Page not found."}), 404
    if not meta.get("editable", meta.get("kind") == "cms"):
        return jsonify({"ok": False, "error": "Page content is managed via locale files."}), 400

    payload = request.get_json(silent=True) or {}
    try:
        result = mistral_ai.generate_page_content(
            slug=slug,
            page_name=meta["name"],
            page_path=meta["path"],
            user_prompt=payload.get("prompt", ""),
            current_content=store.get_page_content(slug),
            include_seo=payload.get("include_seo", True),
            include_faq=payload.get("include_faq", True),
        )
    except mistral_ai.MistralError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 502

    if payload.get("save"):
        store.update_page(slug, result["content"])
        if result.get("seo"):
            store.update_seo_page(slug, result["seo"])
        if result.get("faq"):
            store.update_page_faq(slug, result["faq"])

    return jsonify({"ok": True, **result})


# ── SEO ──

@crm_bp.route("/seo", methods=["GET", "POST"])
def seo():
    if request.method == "POST":
        form_type = request.form.get("form_type")
        if form_type == "global":
            store.update_seo_global({
                "site_name": request.form.get("site_name", ""),
                "site_url": request.form.get("site_url", "").strip().rstrip("/"),
                "title_suffix": request.form.get("title_suffix", ""),
                "meta_description": request.form.get("meta_description", ""),
                "keywords": request.form.get("keywords", ""),
                "og_image": request.form.get("og_image", ""),
                "twitter_handle": request.form.get("twitter_handle", ""),
                "google_analytics_id": request.form.get("google_analytics_id", ""),
            })
            flash("SEO global enregistré.", "success")
        elif form_type == "page":
            slug = request.form.get("page_slug")
            store.update_seo_page(slug, {
                "title": request.form.get("title", ""),
                "description": request.form.get("description", ""),
                "keywords": request.form.get("keywords", ""),
            })
            flash(f"SEO de la page enregistré.", "success")
        return redirect(url_for("crm.seo", page=request.form.get("page_slug", request.args.get("page", "home"))))

    selected = request.args.get("page", "home")
    return render_template(
        "crm/seo.html",
        global_seo=store.get_seo_global(),
        page_catalog=store.get_page_catalog(),
        page_seo=store.get_seo_page(selected),
        selected_page=selected,
    )


# ── Analytics ──

@crm_bp.route("/analytics")
def analytics():
    return render_template("crm/analytics.html", analytics=store.get_analytics())


@crm_bp.route("/api/analytics/realtime")
def api_analytics_realtime():
    return jsonify(store.get_realtime_analytics())


# ── Comptes / base de données ──

@crm_bp.route("/comptes")
def accounts():
    search = request.args.get("q", "").strip()
    accounts_list = store.get_crm_accounts(search=search or None)
    return render_template("crm/accounts.html", accounts=accounts_list, search=search)


@crm_bp.route("/comptes/<user_id>")
def account_detail(user_id):
    account = store.get_crm_account_detail(user_id)
    if not account:
        flash("Compte introuvable.", "error")
        return redirect(url_for("crm.accounts"))
    return render_template("crm/account_detail.html", account=account)


@crm_bp.route("/comptes/<user_id>/delete", methods=["POST"])
def delete_account(user_id):
    if store.delete_crm_account(user_id):
        flash("Compte supprimé avec son profil et les données liées.", "success")
    else:
        flash("Compte introuvable.", "error")
    return redirect(url_for("crm.accounts"))


@crm_bp.route("/comptes/supprimer-tous", methods=["POST"])
def delete_all_accounts():
    count = store.delete_all_crm_accounts()
    if count:
        flash(f"{count} compte(s) supprimé(s) avec leurs profils et données liées.", "success")
    else:
        flash("Aucun compte à supprimer.", "info")
    return redirect(url_for("crm.accounts"))


# ── Réseaux sociaux ──

@crm_bp.route("/reseaux")
def social():
    return render_template("crm/social.html", posts=store.get_social_posts())


@crm_bp.route("/reseaux/nouveau", methods=["GET", "POST"])
def new_social():
    if request.method == "POST":
        store.add_social_post({
            "platform": request.form.get("platform", "linkedin"),
            "content": request.form.get("content", ""),
            "status": request.form.get("status", "draft"),
            "scheduled_at": request.form.get("scheduled_at", ""),
            "link": request.form.get("link", ""),
        })
        flash("Publication créée.", "success")
        return redirect(url_for("crm.social"))
    return render_template("crm/social_form.html", entry=None, is_new=True)


@crm_bp.route("/reseaux/<entry_id>/edit", methods=["GET", "POST"])
def edit_social(entry_id):
    entry = next((p for p in store.get_social_posts() if p["id"] == entry_id), None)
    if not entry:
        flash("Publication introuvable.", "error")
        return redirect(url_for("crm.social"))
    if request.method == "POST":
        store.update_social_post(entry_id, {
            "platform": request.form.get("platform", "linkedin"),
            "content": request.form.get("content", ""),
            "status": request.form.get("status", "draft"),
            "scheduled_at": request.form.get("scheduled_at", ""),
            "link": request.form.get("link", ""),
        })
        flash("Publication mise à jour.", "success")
        return redirect(url_for("crm.social"))
    return render_template("crm/social_form.html", entry=entry, is_new=False)


@crm_bp.route("/reseaux/<entry_id>/delete", methods=["POST"])
def delete_social(entry_id):
    store.delete_social_post(entry_id)
    flash("Publication supprimée.", "success")
    return redirect(url_for("crm.social"))


# ── Mailing (SMTP / IMAP) ──

_MAILING_TABS = frozenset({"campaigns", "inbox", "settings"})


def _mailing_active_tab():
    tab = (request.args.get("tab") or "campaigns").strip().lower()
    return tab if tab in _MAILING_TABS else "campaigns"


def _mailing_hub_context():
    from crm import email_service
    from data.site_config import CONTACT_EMAIL

    settings = store.get_mail_settings()
    smtp = email_service.get_smtp_config()
    return {
        "active_tab": _mailing_active_tab(),
        "campaigns": store.get_mail_campaigns(),
        "analytics": store.get_mail_analytics(),
        "messages": store.get_mail_inbox_cache(),
        "last_sync": settings.get("last_inbox_sync", ""),
        "settings": settings,
        "contact_email": CONTACT_EMAIL,
        "platform_from": smtp.get("from_email") or CONTACT_EMAIL,
        "smtp_configured": email_service.is_smtp_configured(),
        "imap_configured": email_service.is_imap_configured(),
        "smtp_config": smtp,
        "imap_config": email_service.get_imap_config(),
    }


@crm_bp.route("/mailing")
def mailing():
    return render_template("crm/mailing.html", **_mailing_hub_context())


@crm_bp.route("/mailing/parametres", methods=["GET", "POST"])
def mailing_settings():
    if request.method == "GET":
        return redirect(url_for("crm.mailing", tab="settings"))
    store.update_mail_settings({
        "signature": request.form.get("signature", "").strip(),
        "reply_to": request.form.get("reply_to", "").strip(),
    })
    flash("Paramètres email enregistrés.", "success")
    return redirect(url_for("crm.mailing", tab="settings"))


@crm_bp.route("/mailing/boite")
def mailing_inbox():
    return redirect(url_for("crm.mailing", tab="inbox"))


@crm_bp.route("/mailing/nouveau", methods=["GET", "POST"])
def new_mailing():
    from crm import email_service
    from crm import mistral_ai

    if request.method == "POST":
        custom_raw = request.form.get("custom_recipients", "")
        custom = [e.strip() for e in custom_raw.replace(";", ",").split(",") if e.strip()]
        camp = store.add_mail_campaign({
            "name": request.form.get("name", "").strip() or request.form.get("subject", "").strip()[:80],
            "subject": request.form.get("subject", "").strip(),
            "body_html": request.form.get("body_html", "").strip(),
            "body_text": request.form.get("body_text", "").strip(),
            "audience": request.form.get("audience", "contacts"),
            "custom_recipients": custom,
            "status": request.form.get("status", "draft"),
            "scheduled_at": request.form.get("scheduled_at", ""),
            "source": request.form.get("source", "manual"),
            "ai_prompt": request.form.get("ai_prompt", ""),
            "locale": request.form.get("locale", "fr"),
        })
        if request.form.get("action") == "send":
            if not email_service.is_smtp_configured():
                flash("SMTP non configuré — configurez les variables d'environnement.", "error")
                return redirect(url_for("crm.edit_mailing", entry_id=camp["id"]))
            try:
                result = store.send_mail_campaign(camp["id"])
                flash(f"Campagne envoyée : {result['sent']} succès, {result['failed']} échec(s).", "success")
            except ValueError as exc:
                flash(str(exc), "error")
                return redirect(url_for("crm.edit_mailing", entry_id=camp["id"]))
        else:
            flash("Campagne enregistrée.", "success")
        return redirect(url_for("crm.mailing"))
    return render_template(
        "crm/mailing_form.html",
        entry=None,
        is_new=True,
        mistral_configured=mistral_ai.is_configured(),
        smtp_configured=email_service.is_smtp_configured(),
        audience_counts=_mail_audience_counts(),
    )


@crm_bp.route("/mailing/<entry_id>/edit", methods=["GET", "POST"])
def edit_mailing(entry_id):
    from crm import email_service
    from crm import mistral_ai

    entry = store.get_mail_campaign(entry_id)
    if not entry:
        flash("Campagne introuvable.", "error")
        return redirect(url_for("crm.mailing"))
    if request.method == "POST":
        custom_raw = request.form.get("custom_recipients", "")
        custom = [e.strip() for e in custom_raw.replace(";", ",").split(",") if e.strip()]
        store.update_mail_campaign(entry_id, {
            "name": request.form.get("name", "").strip(),
            "subject": request.form.get("subject", "").strip(),
            "body_html": request.form.get("body_html", "").strip(),
            "body_text": request.form.get("body_text", "").strip(),
            "audience": request.form.get("audience", "contacts"),
            "custom_recipients": custom,
            "status": request.form.get("status", entry.get("status", "draft")),
            "scheduled_at": request.form.get("scheduled_at", ""),
            "source": request.form.get("source", entry.get("source", "manual")),
            "ai_prompt": request.form.get("ai_prompt", ""),
            "locale": request.form.get("locale", entry.get("locale", "fr")),
        })
        if request.form.get("action") == "send":
            if not email_service.is_smtp_configured():
                flash("SMTP non configuré.", "error")
                return redirect(url_for("crm.edit_mailing", entry_id=entry_id))
            try:
                result = store.send_mail_campaign(entry_id)
                flash(f"Campagne envoyée : {result['sent']} succès, {result['failed']} échec(s).", "success")
            except ValueError as exc:
                flash(str(exc), "error")
                return redirect(url_for("crm.edit_mailing", entry_id=entry_id))
        else:
            flash("Campagne mise à jour.", "success")
        return redirect(url_for("crm.mailing"))
    return render_template(
        "crm/mailing_form.html",
        entry=entry,
        is_new=False,
        mistral_configured=mistral_ai.is_configured(),
        smtp_configured=email_service.is_smtp_configured(),
        audience_counts=_mail_audience_counts(),
    )


@crm_bp.route("/mailing/<entry_id>/envoyer", methods=["POST"])
def send_mailing(entry_id):
    from crm import email_service

    if not email_service.is_smtp_configured():
        flash("SMTP non configuré.", "error")
        return redirect(url_for("crm.edit_mailing", entry_id=entry_id))
    try:
        result = store.send_mail_campaign(entry_id)
        flash(f"Campagne envoyée : {result['sent']} succès, {result['failed']} échec(s).", "success")
    except ValueError as exc:
        flash(str(exc), "error")
        return redirect(url_for("crm.edit_mailing", entry_id=entry_id))
    return redirect(url_for("crm.mailing"))


@crm_bp.route("/mailing/<entry_id>/delete", methods=["POST"])
def delete_mailing(entry_id):
    store.delete_mail_campaign(entry_id)
    flash("Campagne supprimée.", "success")
    return redirect(url_for("crm.mailing"))


def _mail_audience_counts():
    return {
        "contacts": len(store.resolve_mail_recipients("contacts")),
        "enterprises": len(store.resolve_mail_recipients("enterprises")),
        "startups": len(store.resolve_mail_recipients("startups")),
        "all_users": len(store.resolve_mail_recipients("all_users")),
    }


@crm_bp.route("/api/mailing/generate", methods=["POST"])
def api_mailing_generate():
    from crm import email_service
    from crm import mistral_ai

    if not mistral_ai.is_configured():
        return jsonify({"ok": False, "error": "MISTRAL_API_KEY non configurée."}), 503
    payload = request.get_json(silent=True) or {}
    locale = (payload.get("locale") or "fr").strip().lower()
    if locale not in ("fr", "en"):
        locale = "fr"
    try:
        result = mistral_ai.generate_email_content(
            audience=payload.get("audience", "contacts"),
            user_prompt=payload.get("prompt", ""),
            subject_hint=payload.get("subject_hint", ""),
            tone=payload.get("tone", "professional"),
            locale=locale,
        )
        preview_html = email_service.build_branded_preview(
            result["body_html"],
            subject=result["subject"],
            locale=locale,
            site_url=store.get_site_url(),
        )
        return jsonify({"ok": True, **result, "locale": locale, "preview_html": preview_html})
    except mistral_ai.MistralError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 502


@crm_bp.route("/api/mailing/preview", methods=["POST"])
def api_mailing_preview():
    from crm import email_service

    payload = request.get_json(silent=True) or {}
    locale = (payload.get("locale") or "fr").strip().lower()
    if locale not in ("fr", "en"):
        locale = "fr"
    body_html = (payload.get("body_html") or "").strip()
    subject = (payload.get("subject") or "").strip()
    if not body_html:
        return jsonify({"ok": False, "error": "Contenu HTML requis pour l'aperçu."}), 400
    preview_html = email_service.build_branded_preview(
        body_html,
        subject=subject,
        locale=locale,
        site_url=store.get_site_url(),
    )
    return jsonify({"ok": True, "preview_html": preview_html, "locale": locale})


@crm_bp.route("/api/mailing/test-smtp", methods=["POST"])
def api_mailing_test_smtp():
    from crm import email_service

    payload = request.get_json(silent=True) or {}
    to = (payload.get("to") or "").strip()
    locale = (payload.get("locale") or "fr").strip().lower()
    if locale not in ("fr", "en"):
        locale = "fr"
    try:
        if to:
            email_service.send_test_email(to, locale=locale, site_url=store.get_site_url())
            return jsonify({"ok": True, "message": f"Email de test envoyé à {to}."})
        info = email_service.test_smtp_connection()
        return jsonify({"ok": True, "message": "Connexion SMTP OK.", **info})
    except email_service.EmailError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@crm_bp.route("/api/mailing/test-imap", methods=["POST"])
def api_mailing_test_imap():
    from crm import email_service

    try:
        info = email_service.test_imap_connection()
        return jsonify({"ok": True, "message": "Connexion IMAP OK.", **info})
    except email_service.EmailError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@crm_bp.route("/api/mailing/sync-inbox", methods=["POST"])
def api_mailing_sync_inbox():
    try:
        messages = store.sync_mail_inbox(limit=40)
        return jsonify({"ok": True, "count": len(messages), "messages": messages})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


# ── Entreprises ──

@crm_bp.route("/entreprises")
def enterprises():
    q = request.args.get("q", "").strip().lower()
    items = store.get_enterprises()
    if q:
        items = [e for e in items if q in e.get("name", "").lower() or q in e.get("sector", "").lower()]
    return render_template("crm/enterprises.html", enterprises=items, search=q)


@crm_bp.route("/entreprises/nouveau", methods=["GET", "POST"])
def new_enterprise():
    if request.method == "POST":
        store.add_enterprise({
            "name": request.form["name"],
            "sector": request.form.get("sector", ""),
            "logo_initials": request.form.get("logo_initials", "")[:3].upper(),
            "description": request.form.get("description", ""),
            "needs": store.parse_list_field(request.form.get("needs", "")),
            "plan": "free_enterprise",
        })
        flash("Entreprise créée.", "success")
        return redirect(url_for("crm.enterprises"))
    return render_template("crm/enterprise_form.html", entry=None, is_new=True)


@crm_bp.route("/entreprises/<entry_id>/edit", methods=["GET", "POST"])
def edit_enterprise(entry_id):
    entry = next((e for e in store.get_enterprises() if e["id"] == entry_id), None)
    if not entry:
        flash("Entreprise introuvable.", "error")
        return redirect(url_for("crm.enterprises"))
    if request.method == "POST":
        store.update_enterprise(entry_id, {
            "name": request.form["name"],
            "sector": request.form.get("sector", ""),
            "logo_initials": request.form.get("logo_initials", "")[:3].upper(),
            "description": request.form.get("description", ""),
            "needs": store.parse_list_field(request.form.get("needs", "")),
        })
        flash("Entreprise mise à jour.", "success")
        return redirect(url_for("crm.enterprises"))
    return render_template("crm/enterprise_form.html", entry=entry, is_new=False)


@crm_bp.route("/entreprises/<entry_id>/delete", methods=["POST"])
def delete_enterprise(entry_id):
    store.delete_enterprise(entry_id)
    flash("Entreprise supprimée.", "success")
    return redirect(url_for("crm.enterprises"))


# ── Startups ──

@crm_bp.route("/startups")
def startups():
    q = request.args.get("q", "").strip().lower()
    country = request.args.get("country", "")
    items = store.get_startups(country or None)
    if q:
        items = [s for s in items if q in s.get("name", "").lower() or q in s.get("country", "").lower()]
    return render_template(
        "crm/startups.html", startups=items, search=q,
        selected_country=country, countries=store.get_startup_countries(),
    )


@crm_bp.route("/startups/nouveau", methods=["GET", "POST"])
def new_startup():
    if request.method == "POST":
        store.add_startup({
            "name": request.form["name"], "country": request.form.get("country", ""),
            "flag": request.form.get("flag", ""), "city": request.form.get("city", ""),
            "specialty": request.form.get("specialty", ""),
            "team_size": int(request.form.get("team_size") or 0),
            "rating": float(request.form.get("rating") or 0),
            "projects_done": int(request.form.get("projects_done") or 0),
            "skills": store.parse_list_field(request.form.get("skills", "")),
            "description": request.form.get("description", ""),
            "featured": request.form.get("featured") == "on",
        })
        flash("Startup créée.", "success")
        return redirect(url_for("crm.startups"))
    return render_template("crm/startup_form.html", entry=None, is_new=True)


@crm_bp.route("/startups/<entry_id>/edit", methods=["GET", "POST"])
def edit_startup(entry_id):
    entry = next((s for s in store.get_startups() if s["id"] == entry_id), None)
    if not entry:
        flash("Startup introuvable.", "error")
        return redirect(url_for("crm.startups"))
    if request.method == "POST":
        store.update_startup(entry_id, {
            "name": request.form["name"], "country": request.form.get("country", ""),
            "flag": request.form.get("flag", ""), "city": request.form.get("city", ""),
            "specialty": request.form.get("specialty", ""),
            "team_size": int(request.form.get("team_size") or 0),
            "rating": float(request.form.get("rating") or 0),
            "projects_done": int(request.form.get("projects_done") or 0),
            "skills": store.parse_list_field(request.form.get("skills", "")),
            "description": request.form.get("description", ""),
            "featured": request.form.get("featured") == "on",
        })
        flash("Startup mise à jour.", "success")
        return redirect(url_for("crm.startups"))
    return render_template("crm/startup_form.html", entry=entry, is_new=False)


@crm_bp.route("/startups/<entry_id>/delete", methods=["POST"])
def delete_startup(entry_id):
    store.delete_startup(entry_id)
    flash("Startup supprimée.", "success")
    return redirect(url_for("crm.startups"))


# ── Projets ──

@crm_bp.route("/projets")
def projects():
    q = request.args.get("q", "").strip().lower()
    status = request.args.get("status", "")
    items = store.get_projects()
    if status:
        items = [p for p in items if p.get("status") == status]
    if q:
        items = [p for p in items if q in p.get("title", "").lower() or q in p.get("enterprise", "").lower()]
    return render_template("crm/projects.html", projects=items, search=q, selected_status=status)


@crm_bp.route("/projets/nouveau", methods=["GET", "POST"])
def new_project():
    if request.method == "POST":
        store.add_project({
            "title": request.form["title"], "enterprise": request.form.get("enterprise", ""),
            "budget": request.form.get("budget", ""), "duration": request.form.get("duration", ""),
            "status": request.form.get("status", "Ouvert"),
            "skills": store.parse_list_field(request.form.get("skills", "")),
        })
        flash("Projet créé.", "success")
        return redirect(url_for("crm.projects"))
    return render_template("crm/project_form.html", entry=None, is_new=True, enterprises=store.get_enterprises())


@crm_bp.route("/projets/<entry_id>/edit", methods=["GET", "POST"])
def edit_project(entry_id):
    entry = next((p for p in store.get_projects() if p["id"] == entry_id), None)
    if not entry:
        flash("Projet introuvable.", "error")
        return redirect(url_for("crm.projects"))
    if request.method == "POST":
        store.update_project(entry_id, {
            "title": request.form["title"], "enterprise": request.form.get("enterprise", ""),
            "budget": request.form.get("budget", ""), "duration": request.form.get("duration", ""),
            "status": request.form.get("status", "Ouvert"),
            "skills": store.parse_list_field(request.form.get("skills", "")),
        })
        flash("Projet mis à jour.", "success")
        return redirect(url_for("crm.projects"))
    return render_template("crm/project_form.html", entry=entry, is_new=False, enterprises=store.get_enterprises())


@crm_bp.route("/projets/<entry_id>/delete", methods=["POST"])
def delete_project(entry_id):
    store.delete_project(entry_id)
    flash("Projet supprimé.", "success")
    return redirect(url_for("crm.projects"))


# ── Contacts ──

@crm_bp.route("/contacts")
def contacts():
    q = request.args.get("q", "").strip().lower()
    type_filter = request.args.get("type", "")
    status_filter = request.args.get("status", "")
    items = store.get_contacts()
    if type_filter:
        items = [c for c in items if c.get("type") == type_filter]
    if status_filter:
        items = [c for c in items if c.get("status", "new") == status_filter]
    if q:
        items = [
            c for c in items
            if q in c.get("name", "").lower()
            or q in c.get("email", "").lower()
            or q in c.get("message", "").lower()
        ]
    return render_template(
        "crm/contacts.html",
        contacts=items,
        search=q,
        selected_type=type_filter,
        selected_status=status_filter,
    )


@crm_bp.route("/contacts/<entry_id>")
def contact_detail(entry_id):
    from crm import email_service

    entry = store.get_contact(entry_id)
    if not entry:
        flash("Contact introuvable.", "error")
        return redirect(url_for("crm.contacts"))
    if entry.get("status") == "new":
        store.update_contact(entry_id, {"status": "read"})
        entry = store.get_contact(entry_id)
    return render_template(
        "crm/contact_detail.html",
        contact=entry,
        smtp_configured=email_service.is_smtp_configured(),
    )


@crm_bp.route("/contacts/<entry_id>/reply", methods=["POST"])
def contact_reply(entry_id):
    from crm import email_service

    entry = store.get_contact(entry_id)
    if not entry:
        flash("Contact introuvable.", "error")
        return redirect(url_for("crm.contacts"))

    body = request.form.get("reply_body", "").strip()
    if not body:
        flash("Le message de réponse est vide.", "error")
        return redirect(url_for("crm.contact_detail", entry_id=entry_id))

    email_sent = False
    if email_service.is_smtp_configured():
        subject = f"Re: Votre message — Iotplace"
        original = (entry.get("message") or "")[:200]
        html = (
            f"<p>Bonjour {entry.get('name', '')},</p>"
            f"<p>{body.replace(chr(10), '<br>')}</p>"
            f"<hr style='border:none;border-top:1px solid #e5e7eb;margin:1.5rem 0'>"
            f"<p style='color:#6b7280;font-size:0.9em'>Votre message initial :<br>"
            f"{original.replace(chr(10), '<br>')}</p>"
        )
        try:
            settings = store.get_mail_settings()
            email_service.send_email(
                entry["email"],
                subject,
                html,
                reply_to=(settings.get("reply_to") or "").strip() or email_service.get_platform_email() or None,
                site_url=store.get_site_url(),
                locale="fr",
            )
            email_sent = True
        except email_service.EmailError as exc:
            flash(f"Réponse enregistrée mais email non envoyé : {exc}", "warning")
    else:
        flash("Réponse enregistrée. Configurez SMTP dans Mailing pour envoyer par email.", "info")

    store.add_contact_reply(entry_id, body, email_sent=email_sent, sent_via="smtp" if email_sent else "crm")
    flash("Réponse envoyée." if email_sent else "Réponse enregistrée.", "success")
    return redirect(url_for("crm.contact_detail", entry_id=entry_id))


@crm_bp.route("/contacts/<entry_id>/status", methods=["POST"])
def contact_status(entry_id):
    status = request.form.get("status", "").strip()
    if status not in ("new", "read", "replied", "archived"):
        flash("Statut invalide.", "error")
        return redirect(url_for("crm.contact_detail", entry_id=entry_id))
    if not store.update_contact(entry_id, {"status": status}):
        flash("Contact introuvable.", "error")
        return redirect(url_for("crm.contacts"))
    flash("Statut mis à jour.", "success")
    return redirect(url_for("crm.contact_detail", entry_id=entry_id))


@crm_bp.route("/contacts/<entry_id>/delete", methods=["POST"])
def delete_contact(entry_id):
    store.delete_contact(entry_id)
    flash("Contact supprimé.", "success")
    return redirect(url_for("crm.contacts"))
