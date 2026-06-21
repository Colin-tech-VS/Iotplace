from flask import render_template, request, redirect, url_for, flash, session, jsonify
import uuid

import auth
from data import store
from vitrine import vitrine_bp

ENDPOINT_PAGE_SLUG = {
    "vitrine.index": "home",
    "vitrine.enterprises": "enterprises",
    "vitrine.startups": "startups",
    "vitrine.projects": "projects",
    "vitrine.about": "about",
    "vitrine.contact": "contact",
}


def _resolve_page_slug():
    return ENDPOINT_PAGE_SLUG.get(request.endpoint)


def _analytics_enabled():
    if request.endpoint not in ENDPOINT_PAGE_SLUG:
        return False
    ref = (request.referrer or "").lower()
    if "/crm" in ref:
        return False
    return True


def _get_or_create_session_id():
    if "analytics_sid" not in session:
        session["analytics_sid"] = uuid.uuid4().hex[:12]
    return session["analytics_sid"]


@vitrine_bp.before_request
def track_visit():
    if request.method != "GET":
        return
    if request.path.startswith("/api/") or request.path.startswith("/vitrine/static/"):
        return
    if not _analytics_enabled():
        return
    slug = _resolve_page_slug()
    if not slug:
        return
    sid = _get_or_create_session_id()
    store.track_page_view(
        slug,
        path=request.full_path.rstrip("?") if request.query_string else request.path,
        session_id=sid,
        referrer=request.referrer or "",
    )


@vitrine_bp.context_processor
def inject_vitrine_context():
    slug = ENDPOINT_PAGE_SLUG.get(request.endpoint, "home")
    sid = session.get("analytics_sid", "")
    enabled = _analytics_enabled()
    return {
        "countries": store.get_startup_countries(),
        "seo": store.get_seo_for_vitrine(slug),
        "page": store.get_page_content(slug),
        "analytics_page_slug": slug if enabled else "",
        "analytics_session": sid if enabled else "",
        "analytics_enabled": enabled,
        "current_user": auth.get_current_user(),
    }


@vitrine_bp.route("/api/analytics/ping", methods=["POST"])
def analytics_ping():
    payload = request.get_json(silent=True) or {}
    path = payload.get("path") or ""
    if store._is_excluded_analytics(path=path):
        return jsonify({"ok": True, "skipped": True})
    sid = payload.get("session_id") or session.get("analytics_sid")
    if not sid:
        sid = _get_or_create_session_id()
    store.track_ping(sid, payload.get("page"), payload.get("path"))
    return jsonify({"ok": True})


def _check_published(slug):
    content = store.get_page_content(slug)
    return content.get("published", True)


@vitrine_bp.route("/")
def index():
    if not _check_published("home"):
        return render_template("unpublished.html"), 404
    return render_template(
        "index.html",
        stats=store.get_stats(),
        featured_startups=store.get_featured_startups(),
        featured_projects=store.get_featured_projects(),
        page=store.get_page_content("home"),
    )


@vitrine_bp.route("/entreprises")
def enterprises():
    if not _check_published("enterprises"):
        return render_template("unpublished.html"), 404
    return render_template(
        "enterprises.html",
        enterprises=store.get_enterprises(),
        projects=store.get_projects(),
        page=store.get_page_content("enterprises"),
    )


@vitrine_bp.route("/startups")
def startups():
    if not _check_published("startups"):
        return render_template("unpublished.html"), 404
    country = request.args.get("country", "")
    return render_template(
        "startups.html",
        startups=store.get_startups(country or None),
        countries=store.get_startup_countries(),
        selected_country=country,
        page=store.get_page_content("startups"),
    )


@vitrine_bp.route("/projets")
def projects():
    if not _check_published("projects"):
        return render_template("unpublished.html"), 404
    return render_template(
        "projects.html",
        projects=store.get_projects(),
        page=store.get_page_content("projects"),
    )


@vitrine_bp.route("/a-propos")
def about():
    if not _check_published("about"):
        return render_template("unpublished.html"), 404
    return render_template("about.html", page=store.get_page_content("about"))


@vitrine_bp.route("/contact", methods=["GET", "POST"])
def contact():
    if not _check_published("contact"):
        return render_template("unpublished.html"), 404
    if request.method == "POST":
        store.add_contact({
            "type": request.form.get("type", ""),
            "name": request.form.get("name", ""),
            "email": request.form.get("email", ""),
            "country": request.form.get("country", ""),
            "message": request.form.get("message", ""),
        })
        flash("Merci ! Votre message a bien été envoyé. Nous vous recontacterons sous 48h.", "success")
        return redirect(url_for("vitrine.contact"))
    return render_template("contact.html", page=store.get_page_content("contact"))
