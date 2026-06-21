from flask import render_template, request, redirect, url_for, flash, jsonify

from data import store
from crm import crm_bp


def _nav_stats():
    data = store.get_all()
    stats = store.get_stats()
    stats["contacts"] = len(data["contacts"])
    stats["social_drafts"] = len([p for p in data.get("social_posts", []) if p.get("status") == "draft"])
    stats["users"] = len(data.get("users", []))
    return stats


@crm_bp.context_processor
def inject_crm_nav():
    return {"nav_stats": _nav_stats()}


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
    return render_template("crm/pages.html", pages=store.get_all_pages())


@crm_bp.route("/pages/<slug>", methods=["GET", "POST"])
def edit_page(slug):
    meta = store.get_page_meta(slug)
    if not meta:
        flash("Page introuvable.", "error")
        return redirect(url_for("crm.pages"))

    content = store.get_page_content(slug)
    if request.method == "POST":
        fields = {k: v for k, v in request.form.items() if k != "published"}
        fields["published"] = request.form.get("published") == "on"
        store.update_page(slug, fields)
        flash("Page mise à jour.", "success")
        return redirect(url_for("crm.pages"))
    return render_template("crm/page_edit.html", meta=meta, content=content)


# ── SEO ──

@crm_bp.route("/seo", methods=["GET", "POST"])
def seo():
    if request.method == "POST":
        form_type = request.form.get("form_type")
        if form_type == "global":
            store.update_seo_global({
                "site_name": request.form.get("site_name", ""),
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
    items = store.get_contacts()
    if type_filter:
        items = [c for c in items if c.get("type") == type_filter]
    if q:
        items = [c for c in items if q in c.get("name", "").lower() or q in c.get("email", "").lower()]
    return render_template("crm/contacts.html", contacts=items, search=q, selected_type=type_filter)


@crm_bp.route("/contacts/<entry_id>")
def contact_detail(entry_id):
    entry = next((c for c in store.get_contacts() if c["id"] == entry_id), None)
    if not entry:
        flash("Contact introuvable.", "error")
        return redirect(url_for("crm.contacts"))
    return render_template("crm/contact_detail.html", contact=entry)


@crm_bp.route("/contacts/<entry_id>/delete", methods=["POST"])
def delete_contact(entry_id):
    store.delete_contact(entry_id)
    flash("Contact supprimé.", "success")
    return redirect(url_for("crm.contacts"))
