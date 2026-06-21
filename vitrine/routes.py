from flask import render_template, request, redirect, url_for, flash, session, jsonify, Response, abort

import uuid

import auth
from data import store
from vitrine import vitrine_bp
from vitrine.i18n import get_locale, t, translate_status

ENDPOINT_PAGE_SLUG = {
    "vitrine.index": "home",
    "vitrine.enterprises": "enterprises",
    "vitrine.startups": "startups",
    "vitrine.projects": "projects",
    "vitrine.about": "about",
    "vitrine.contact": "contact",
    "vitrine.pricing": "pricing",
}


@vitrine_bp.route("/projets")
def legacy_projects():
    return redirect(url_for("vitrine.projects", **request.args), code=301)


@vitrine_bp.route("/a-propos")
def legacy_about():
    return redirect(url_for("vitrine.about", **request.args), code=301)


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
    site_url = store.get_site_url()
    seo_overrides = {}
    breadcrumbs_extra = None
    if request.endpoint == "vitrine.startups" and request.args.get("country"):
        country = request.args.get("country")
        seo_overrides = store.get_startups_country_seo(country)
        breadcrumbs_extra = {
            "name": f"Startups {country}",
            "url": store.build_canonical_url(site_url, request.path, request.query_string),
        }
    canonical = store.build_canonical_url(
        site_url,
        request.path,
        request.query_string if request.args.get("country") else b"",
    )
    breadcrumbs = store.build_breadcrumbs(slug, site_url, breadcrumbs_extra, get_locale())
    faq = store.get_page_faq(slug, get_locale())
    user = auth.get_current_user()
    locale = get_locale()
    return {
        "countries": store.get_startup_countries(),
        "seo": store.get_seo_for_vitrine(slug, overrides=seo_overrides or None, locale=locale),
        "seo_canonical": canonical,
        "seo_site_url": site_url,
        "seo_page_slug": slug,
        "seo_json_ld": store.build_json_ld(slug, canonical, site_url, faq=faq, breadcrumbs=breadcrumbs, locale=locale),
        "seo_faq": faq,
        "seo_breadcrumbs": breadcrumbs,
        "page": store.get_page_content(slug, locale),
        "analytics_page_slug": slug if enabled else "",
        "analytics_session": sid if enabled else "",
        "analytics_enabled": enabled,
        "current_user": user,
        "unread_count": store.get_unread_count(user["id"]) if user else 0,
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


@vitrine_bp.route("/robots.txt")
def robots_txt():
    return Response(store.get_robots_txt(), mimetype="text/plain")


@vitrine_bp.route("/sitemap.xml")
def sitemap_xml():
    entries = store.get_sitemap_entries()
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for entry in entries:
        lines.append("  <url>")
        lines.append(f"    <loc>{entry['loc']}</loc>")
        lines.append(f"    <changefreq>{entry['changefreq']}</changefreq>")
        lines.append(f"    <priority>{entry['priority']}</priority>")
        lines.append("  </url>")
    lines.append("</urlset>")
    return Response("\n".join(lines), mimetype="application/xml")


@vitrine_bp.route("/")
def index():
    if not _check_published("home"):
        return render_template("unpublished.html"), 404
    return render_template(
        "index.html",
        stats=store.get_stats(),
        featured_startups=store.get_featured_startups(),
        featured_projects=store.get_featured_projects(),
        page=store.get_page_content("home", get_locale()),
    )


@vitrine_bp.route("/enterprises")
def enterprises():
    if not _check_published("enterprises"):
        return render_template("unpublished.html"), 404
    return render_template(
        "enterprises.html",
        enterprises=store.get_public_enterprises(),
        projects=store.get_projects(),
        page=store.get_page_content("enterprises", get_locale()),
    )


@vitrine_bp.route("/enterprises/<enterprise_id>")
def enterprise_detail(enterprise_id):
    enterprise = store.get_public_enterprise(enterprise_id)
    if not enterprise:
        abort(404)
    site_url = store.get_site_url()
    path = f"/enterprises/{enterprise_id}"
    canonical = store.build_canonical_url(site_url, path)
    seo_overrides = store.get_enterprise_detail_seo(enterprise)
    locale = get_locale()
    breadcrumbs_extra = {"name": enterprise.get("name", "Enterprise"), "url": canonical}
    breadcrumbs = store.build_breadcrumbs("enterprises", site_url, breadcrumbs_extra, locale)
    related = store.get_projects_for_enterprise(enterprise["id"], enterprise.get("name", ""))
    return render_template(
        "enterprise_detail.html",
        enterprise=enterprise,
        related_projects=related,
        seo=store.get_seo_for_vitrine("enterprises", overrides=seo_overrides, locale=locale),
        seo_canonical=canonical,
        seo_breadcrumbs=breadcrumbs,
        seo_json_ld=store.build_json_ld("enterprises", canonical, site_url, breadcrumbs=breadcrumbs, locale=locale),
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
        page=store.get_page_content("startups", get_locale()),
    )


@vitrine_bp.route("/startups/<startup_id>")
def startup_detail(startup_id):
    startup = store.get_public_startup(startup_id)
    if not startup:
        abort(404)
    site_url = store.get_site_url()
    path = f"/startups/{startup_id}"
    canonical = store.build_canonical_url(site_url, path)
    seo_overrides = store.get_startup_detail_seo(startup)
    locale = get_locale()
    breadcrumbs_extra = {"name": startup.get("name", "Startup"), "url": canonical}
    breadcrumbs = store.build_breadcrumbs("startups", site_url, breadcrumbs_extra, locale)
    return render_template(
        "startup_detail.html",
        startup=startup,
        seo=store.get_seo_for_vitrine("startups", overrides=seo_overrides, locale=locale),
        seo_canonical=canonical,
        seo_breadcrumbs=breadcrumbs,
        seo_json_ld=store.build_json_ld("startups", canonical, site_url, breadcrumbs=breadcrumbs, locale=locale),
    )


@vitrine_bp.route("/projects")
def projects():
    if not _check_published("projects"):
        return render_template("unpublished.html"), 404
    return render_template(
        "projects.html",
        projects=store.get_projects(),
        page=store.get_page_content("projects", get_locale()),
    )


@vitrine_bp.route("/projects/<project_id>")
def project_detail(project_id):
    project = store.get_public_project(project_id)
    if not project:
        abort(404)
    enterprise = None
    if project.get("enterprise_id"):
        enterprise = store.get_public_enterprise(project["enterprise_id"])
    site_url = store.get_site_url()
    path = f"/projects/{project_id}"
    canonical = store.build_canonical_url(site_url, path)
    seo_overrides = store.get_project_detail_seo(project)
    locale = get_locale()
    breadcrumbs_extra = {"name": project.get("title", "Project"), "url": canonical}
    breadcrumbs = store.build_breadcrumbs("projects", site_url, breadcrumbs_extra, locale)
    return render_template(
        "project_detail.html",
        project=project,
        enterprise=enterprise,
        seo=store.get_seo_for_vitrine("projects", overrides=seo_overrides, locale=locale),
        seo_canonical=canonical,
        seo_breadcrumbs=breadcrumbs,
        seo_json_ld=store.build_json_ld("projects", canonical, site_url, breadcrumbs=breadcrumbs, locale=locale),
    )


@vitrine_bp.route("/tarifs")
def legacy_pricing_fr():
    return redirect(url_for("vitrine.pricing", **request.args), code=301)


@vitrine_bp.route("/pricing")
@vitrine_bp.route("/vitrine/pricing")
def pricing():
    if not _check_published("pricing"):
        return render_template("unpublished.html"), 404
    from payments.pricing_plans import get_pricing_numbers

    return render_template(
        "pricing.html",
        page=store.get_page_content("pricing", get_locale()),
        pricing=get_pricing_numbers(),
    )


@vitrine_bp.route("/about")
def about():
    if not _check_published("about"):
        return render_template("unpublished.html"), 404
    return render_template("about.html", page=store.get_page_content("about", get_locale()))


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
        flash(t("contact.flash_success"), "success")
        return redirect(url_for("vitrine.contact"))
    return render_template("contact.html", page=store.get_page_content("contact", get_locale()))


@vitrine_bp.route("/api/advisor/chat", methods=["POST"])
def advisor_chat():
    from vitrine import advisor_ai

    if not advisor_ai.is_configured():
        return jsonify({"ok": False, "error": t("advisor.not_configured")}), 503

    payload = request.get_json(silent=True) or {}
    try:
        result = advisor_ai.chat(
            user_type=payload.get("user_type", "enterprise"),
            message=payload.get("message", ""),
            history=payload.get("history", []),
            site_url=store.get_site_url(),
            locale=get_locale(),
        )
    except advisor_ai.AdvisorError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400

    return jsonify({"ok": True, **result})
