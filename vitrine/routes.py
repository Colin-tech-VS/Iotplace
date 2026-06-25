from flask import render_template, request, redirect, url_for, flash, session, jsonify, Response, abort

import json
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
    "vitrine.privacy": "privacy",
    "vitrine.legal": "legal",
    "vitrine.terms": "terms",
    "vitrine.cookies": "cookies",
}


def _has_analytics_consent():
    raw = request.cookies.get("iot_consent", "")
    if not raw:
        return False
    try:
        return bool(json.loads(raw).get("analytics"))
    except (json.JSONDecodeError, TypeError):
        return False


@vitrine_bp.route("/projets")
def legacy_projects():
    return redirect(url_for("vitrine.projects", **request.args), code=301)


@vitrine_bp.route("/a-propos")
def legacy_about():
    return redirect(url_for("vitrine.about", **request.args), code=301)


@vitrine_bp.route("/politique-de-confidentialite")
def legacy_privacy():
    return redirect(url_for("vitrine.privacy", **request.args), code=301)


@vitrine_bp.route("/mentions-legales")
def legacy_legal():
    return redirect(url_for("vitrine.legal", **request.args), code=301)


@vitrine_bp.route("/conditions-generales")
def legacy_terms():
    return redirect(url_for("vitrine.terms", **request.args), code=301)


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
    if not _has_analytics_consent():
        return
    slug = _resolve_page_slug()
    if not slug:
        return
    from time import time

    now = time()
    last = session.get("_analytics_ts")
    if last and now - float(last) < 45:
        return
    session["_analytics_ts"] = now
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
    analytics_consent = _has_analytics_consent()
    enabled = _analytics_enabled() and analytics_consent
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
        "analytics_consent": analytics_consent,
        "current_user": user,
        "unread_count": store.get_unread_count(user["id"]) if user else 0,
    }


@vitrine_bp.route("/api/analytics/ping", methods=["POST"])
def analytics_ping():
    if not _has_analytics_consent():
        return jsonify({"ok": True, "skipped": True, "reason": "no_consent"})
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


def _directory_page_context(slug: str) -> dict:
    locale = get_locale()
    site_url = store.get_site_url()
    q = request.args.get("q", "").strip()
    sector = request.args.get("sector", "").strip() or None
    country = request.args.get("country", "").strip() or None
    phase = request.args.get("phase", "").strip() or None

    if slug == "enterprises":
        items = store.filter_enterprises_directory(q or None, sector)
        filters = {"sector": sector} if sector else {}
    elif slug == "startups":
        items = store.filter_startups_directory(q or None, country)
        filters = {"country": country} if country else {}
    else:
        items = store.filter_projects_directory(q or None, phase)
        filters = {"phase": phase} if phase else {}

    seo_overrides = store.get_directory_seo_overrides(slug, locale, q, filters, len(items))
    robots = "noindex, follow" if q else "index, follow"
    canonical = store.build_canonical_url(
        site_url,
        request.path,
        store.canonical_query_without(request.query_string, "q"),
    )
    breadcrumbs_extra = None
    if country and slug == "startups":
        breadcrumbs_extra = {
            "name": f"Startups {country}",
            "url": canonical,
        }
    breadcrumbs = store.build_breadcrumbs(slug, site_url, breadcrumbs_extra, locale)
    faq = store.get_page_faq(slug, locale)
    return {
        "directory_q": q,
        "directory_count": len(items),
        "seo": store.get_seo_for_vitrine(slug, overrides=seo_overrides, robots=robots, locale=locale),
        "seo_canonical": canonical,
        "seo_json_ld": store.build_directory_json_ld(
            slug, canonical, site_url, items, locale, faq=faq, breadcrumbs=breadcrumbs,
        ),
        "seo_breadcrumbs": breadcrumbs,
        "seo_faq": faq,
        "directory_items": items,
        "selected_sector": sector or "",
        "selected_country": country or "",
        "selected_phase": phase or "",
    }


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
        if entry.get("lastmod"):
            lines.append(f"    <lastmod>{entry['lastmod']}</lastmod>")
        lines.append(f"    <changefreq>{entry['changefreq']}</changefreq>")
        lines.append(f"    <priority>{entry['priority']}</priority>")
        lines.append("  </url>")
    lines.append("</urlset>")
    return Response("\n".join(lines), mimetype="application/xml")


@vitrine_bp.route("/llms.txt")
def llms_txt():
    from data.geo import build_llms_txt

    return Response(
        build_llms_txt(store.get_site_url()),
        mimetype="text/plain; charset=utf-8",
        headers={"Cache-Control": "public, max-age=3600"},
    )


@vitrine_bp.route("/llms-full.txt")
def llms_full_txt():
    from data.geo import build_llms_full_txt

    return Response(
        build_llms_full_txt(store.get_site_url()),
        mimetype="text/plain; charset=utf-8",
        headers={"Cache-Control": "public, max-age=3600"},
    )


@vitrine_bp.route("/ai.txt")
def ai_txt():
    from data.geo import build_ai_txt

    return Response(
        build_ai_txt(store.get_site_url()),
        mimetype="text/plain; charset=utf-8",
        headers={"Cache-Control": "public, max-age=3600"},
    )


@vitrine_bp.route("/knowledge.json")
def knowledge_json():
    from data.geo import knowledge_json_bytes

    return Response(
        knowledge_json_bytes(store.get_site_url(), get_locale()),
        mimetype="application/json; charset=utf-8",
        headers={"Cache-Control": "public, max-age=1800"},
    )


@vitrine_bp.route("/.well-known/llms.txt")
def wellknown_llms_txt():
    return redirect(url_for("vitrine.llms_txt"), code=301)


@vitrine_bp.route("/knowledge")
def knowledge_page():
    from data.geo import build_knowledge_document

    locale = get_locale()
    site_url = store.get_site_url()
    doc = build_knowledge_document(site_url, locale=locale)
    canonical = f"{site_url}/knowledge"
    title = "Iotplace — base de connaissances" if locale == "fr" else "Iotplace — knowledge base"
    description = (
        "Informations structurées sur Iotplace pour moteurs de recherche et assistants IA."
        if locale == "fr"
        else "Structured facts about Iotplace for search engines and AI assistants."
    )
    seo = store.get_seo_for_vitrine("about", locale=locale)
    seo = {**seo, "title": title, "description": description, "robots": "index, follow"}
    breadcrumbs = [
        {"name": "Accueil" if locale == "fr" else "Home", "url": site_url + "/"},
        {"name": title, "url": canonical},
    ]
    return render_template(
        "knowledge.html",
        knowledge=doc,
        seo=seo,
        seo_canonical=canonical,
        seo_breadcrumbs=breadcrumbs,
        seo_json_ld=store.build_json_ld("about", canonical, site_url, breadcrumbs=breadcrumbs, locale=locale),
    )


@vitrine_bp.route("/mail/o/<campaign_id>/<token>")
def mail_track_open(campaign_id, token):
    from crm.email_service import TRACKING_GIF

    store.record_mail_open(campaign_id, token.replace(".gif", ""))
    return Response(TRACKING_GIF, mimetype="image/gif")


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
    ctx = _directory_page_context("enterprises")
    return render_template(
        "enterprises.html",
        enterprises=ctx["directory_items"],
        sectors=store.get_enterprise_sectors(),
        page=store.get_page_content("enterprises", get_locale()),
        **ctx,
    )


@vitrine_bp.route("/enterprises/<enterprise_id>")
def enterprise_detail(enterprise_id):
    enterprise = store.get_public_enterprise(enterprise_id)
    if not enterprise:
        abort(404)
    site_url = store.get_site_url()
    path = f"/enterprises/{enterprise_id}"
    canonical = store.build_canonical_url(site_url, path)
    seo_overrides = store.get_enterprise_detail_seo(enterprise, get_locale())
    locale = get_locale()
    breadcrumbs_extra = {"name": enterprise.get("name", "Enterprise"), "url": canonical}
    breadcrumbs = store.build_breadcrumbs("enterprises", site_url, breadcrumbs_extra, locale)
    related = store.get_projects_for_enterprise(enterprise["id"], enterprise.get("name", ""))
    from data.geo import build_enterprise_profile_json_ld

    json_ld = store.build_json_ld("enterprises", canonical, site_url, breadcrumbs=breadcrumbs, locale=locale)
    json_ld.append(build_enterprise_profile_json_ld(enterprise, canonical, site_url))
    return render_template(
        "enterprise_detail.html",
        enterprise=enterprise,
        related_projects=related,
        seo=store.get_seo_for_vitrine("enterprises", overrides=seo_overrides, locale=locale),
        seo_canonical=canonical,
        seo_breadcrumbs=breadcrumbs,
        seo_json_ld=json_ld,
    )


@vitrine_bp.route("/startups")
def startups():
    if not _check_published("startups"):
        return render_template("unpublished.html"), 404
    ctx = _directory_page_context("startups")
    return render_template(
        "startups.html",
        startups=ctx["directory_items"],
        countries=store.get_startup_countries(),
        page=store.get_page_content("startups", get_locale()),
        **ctx,
    )


@vitrine_bp.route("/startups/<startup_id>")
def startup_detail(startup_id):
    startup = store.get_public_startup(startup_id)
    if not startup:
        abort(404)
    site_url = store.get_site_url()
    path = f"/startups/{startup_id}"
    canonical = store.build_canonical_url(site_url, path)
    seo_overrides = store.get_startup_detail_seo(startup, get_locale())
    locale = get_locale()
    breadcrumbs_extra = {"name": startup.get("name", "Startup"), "url": canonical}
    breadcrumbs = store.build_breadcrumbs("startups", site_url, breadcrumbs_extra, locale)
    from data.geo import build_startup_profile_json_ld

    json_ld = store.build_json_ld("startups", canonical, site_url, breadcrumbs=breadcrumbs, locale=locale)
    json_ld.append(build_startup_profile_json_ld(startup, canonical, site_url))
    return render_template(
        "startup_detail.html",
        startup=startup,
        seo=store.get_seo_for_vitrine("startups", overrides=seo_overrides, locale=locale),
        seo_canonical=canonical,
        seo_breadcrumbs=breadcrumbs,
        seo_json_ld=json_ld,
    )


@vitrine_bp.route("/projects")
def projects():
    if not _check_published("projects"):
        return render_template("unpublished.html"), 404
    ctx = _directory_page_context("projects")
    return render_template(
        "projects.html",
        projects=ctx["directory_items"],
        page=store.get_page_content("projects", get_locale()),
        **ctx,
    )


@vitrine_bp.route("/recherche")
@vitrine_bp.route("/search")
def search():
    """Unified cross-directory search: startups + projects + enterprises."""
    locale = get_locale()
    site_url = store.get_site_url()
    q = request.args.get("q", "").strip()

    PER_GROUP = 12
    startups = projects = enterprises = []
    if q:
        startups = store.filter_startups_directory(q or None)[:PER_GROUP]
        projects = store.filter_projects_directory(q or None)[:PER_GROUP]
        enterprises = store.filter_enterprises_directory(q or None)[:PER_GROUP]
    total = len(startups) + len(projects) + len(enterprises)

    canonical = store.build_canonical_url(site_url, request.path)
    breadcrumbs = store.build_breadcrumbs("home", site_url, locale=locale)
    title = t("search.title_query", q=q) if q else t("search.title")
    seo = store.get_seo_for_vitrine(
        "home",
        overrides={"title": title, "description": t("search.meta_description")},
        robots="noindex, follow",
        locale=locale,
    )
    return render_template(
        "search.html",
        query=q,
        startups=startups,
        projects=projects,
        enterprises=enterprises,
        total=total,
        seo=seo,
        seo_canonical=canonical,
        seo_breadcrumbs=breadcrumbs,
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
    locale = get_locale()
    seo_overrides = store.get_project_detail_seo(project, locale)
    robots = "index, follow" if project.get("status") in ("Ouvert", "Open") else "noindex, follow"
    breadcrumbs_extra = {"name": project.get("title", "Project"), "url": canonical}
    breadcrumbs = store.build_breadcrumbs("projects", site_url, breadcrumbs_extra, locale)
    from data.geo import build_project_job_json_ld

    json_ld = store.build_json_ld("projects", canonical, site_url, breadcrumbs=breadcrumbs, locale=locale)
    job_ld = build_project_job_json_ld(project, canonical, site_url)
    if job_ld:
        json_ld.append(job_ld)
    return render_template(
        "project_detail.html",
        project=project,
        enterprise=enterprise,
        seo=store.get_seo_for_vitrine("projects", overrides=seo_overrides, robots=robots, locale=locale),
        seo_canonical=canonical,
        seo_breadcrumbs=breadcrumbs,
        seo_json_ld=json_ld,
    )


@vitrine_bp.route("/tarifs")
def legacy_pricing_fr():
    return redirect(url_for("vitrine.pricing", **request.args), code=301)


@vitrine_bp.route("/pricing")
@vitrine_bp.route("/vitrine/pricing")
def pricing():
    if not _check_published("pricing"):
        return render_template("unpublished.html"), 404
    from payments.pricing_plans import build_pricing_page_context
    from vitrine.i18n import get_locale

    locale = get_locale()
    return render_template(
        "pricing.html",
        page=store.get_page_content("pricing", locale),
        pricing=build_pricing_page_context(locale),
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
        if request.form.get("website"):
            flash(t("contact.flash_success"), "success")
            return redirect(url_for("vitrine.contact"))
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        message = request.form.get("message", "").strip()
        privacy_ok = request.form.get("privacy_consent")
        if not name or not email or not message:
            flash(t("contact.flash_error_required"), "error")
            return render_template(
                "contact.html",
                page=store.get_page_content("contact", get_locale()),
                form=dict(request.form),
            )
        if not privacy_ok:
            flash(t("contact.flash_error_privacy"), "error")
            return render_template(
                "contact.html",
                page=store.get_page_content("contact", get_locale()),
                form=dict(request.form),
            )
        store.add_contact({
            "type": request.form.get("type", ""),
            "name": name,
            "email": email,
            "country": request.form.get("country", ""),
            "message": message,
        })
        flash(t("contact.flash_success"), "success")
        return redirect(url_for("vitrine.contact"))
    return render_template(
        "contact.html",
        page=store.get_page_content("contact", get_locale()),
        form={},
    )


def _render_legal_page(slug):
    if not _check_published(slug):
        return render_template("unpublished.html"), 404
    locale = get_locale()
    return render_template(
        "legal_page.html",
        page=store.get_page_content(slug, locale),
        page_slug=slug,
    )


@vitrine_bp.route("/privacy")
def privacy():
    return _render_legal_page("privacy")


@vitrine_bp.route("/legal")
def legal():
    return _render_legal_page("legal")


@vitrine_bp.route("/terms")
def terms():
    return _render_legal_page("terms")


@vitrine_bp.route("/cookies")
def cookies():
    return _render_legal_page("cookies")


def _domain_breadcrumbs(domain_name: str, canonical: str, locale: str):
    from vitrine.domain_content import get_domains_meta

    site_url = store.get_site_url()
    home = "Accueil" if locale == "fr" else "Home"
    meta = get_domains_meta(locale)
    return [
        {"name": home, "url": f"{site_url}/"},
        {"name": meta.get("breadcrumb", "IoT Domains"), "url": f"{site_url}/domaines"},
        {"name": domain_name, "url": canonical},
    ]


def _domain_seo(item: dict, locale: str):
    global_seo = store.get_seo_global()
    site_name = global_seo.get("site_name", "Iotplace")
    site_url = store.get_site_url()
    title = item.get("seo_title") or item.get("name", "IoT Domain")
    suffix = global_seo.get("title_suffix", "")
    full_title = title if suffix and suffix in title else f"{title}{suffix}" if suffix else title
    og_image = global_seo.get("og_image", "") or store.BRAND_OG_IMAGE
    return {
        "title": full_title,
        "description": (item.get("seo_description") or "")[:320],
        "keywords": item.get("seo_keywords", ""),
        "og_image": og_image,
        "og_image_abs": f"{og_image}" if og_image.startswith("http") else f"{site_url}{og_image}" if og_image else "",
        "google_analytics_id": global_seo.get("google_analytics_id", ""),
        "site_name": site_name,
        "twitter_handle": global_seo.get("twitter_handle", ""),
        "robots": "index, follow",
        "locale": "fr_FR" if locale == "fr" else "en_US",
    }


@vitrine_bp.route("/domains")
def domains_redirect():
    return redirect(url_for("vitrine.domains_index"), code=301)


@vitrine_bp.route("/domaines")
def domains_index():
    locale = get_locale()
    site_url = store.get_site_url()
    from vitrine.domain_content import get_domains_meta

    meta = get_domains_meta(locale)
    canonical = f"{site_url}/domaines"
    seo = _domain_seo(
        {
            "seo_title": meta.get("index_seo_title"),
            "seo_description": meta.get("index_seo_description"),
            "seo_keywords": meta.get("index_seo_keywords"),
        },
        locale,
    )
    breadcrumbs = [
        {"name": "Accueil" if locale == "fr" else "Home", "url": f"{site_url}/"},
        {"name": meta.get("breadcrumb", "IoT Domains"), "url": canonical},
    ]
    return render_template(
        "domains_index.html",
        seo=seo,
        seo_canonical=canonical,
        seo_breadcrumbs=breadcrumbs,
        seo_json_ld=store.build_json_ld("home", canonical, site_url, breadcrumbs=breadcrumbs, locale=locale),
    )


@vitrine_bp.route("/domaines/<slug>")
def domain_detail(slug):
    from data.domain_pages import domain_slug, resolve_domain_id
    from data.iot_sectors import list_domains_for_template, sector_stars
    from vitrine.domain_content import get_domain_item

    domain_id = resolve_domain_id(slug)
    if not domain_id:
        abort(404)

    locale = get_locale()
    item = get_domain_item(domain_id, locale)
    if not item:
        abort(404)

    site_url = store.get_site_url()
    canonical_slug = item.get("slug") or domain_slug(domain_id)
    canonical = f"{site_url}/domaines/{canonical_slug}"
    seo = _domain_seo(item, locale)
    breadcrumbs = _domain_breadcrumbs(item.get("name", domain_id), canonical, locale)
    faq = item.get("faq") or []
    stars_label = "⭐" * sector_stars(domain_id)
    other_domains = [d for d in list_domains_for_template(t) if d["id"] != domain_id]
    from data.geo import build_article_json_ld

    json_ld = store.build_json_ld(
        f"domain-{domain_id}", canonical, site_url, faq=faq, breadcrumbs=breadcrumbs, locale=locale
    )
    json_ld.append(build_article_json_ld(
        headline=item.get("name", domain_id),
        description=item.get("seo_description") or item.get("intro", ""),
        url=canonical,
        site_url=site_url,
        locale=locale,
        keywords=item.get("seo_keywords"),
    ))

    return render_template(
        "domain_detail.html",
        domain_id=domain_id,
        domain=item,
        stars_label=stars_label,
        other_domains=other_domains,
        domain_projects=store.get_open_projects_for_sector(domain_id, limit=8),
        seo=seo,
        seo_canonical=canonical,
        seo_breadcrumbs=breadcrumbs,
        seo_json_ld=json_ld,
    )


@vitrine_bp.route("/api/directory/search")
def directory_search_api():
    """Lightweight JSON search for advisor and live filters."""
    kind = (request.args.get("type") or "startups").strip().lower()
    q = (request.args.get("q") or "").strip() or None
    try:
        limit = min(20, max(1, int(request.args.get("limit") or 8)))
    except (TypeError, ValueError):
        limit = 8
    if kind == "enterprises":
        items = store.filter_enterprises_directory(q)[:limit]
    elif kind == "projects":
        items = store.filter_projects_directory(q)[:limit]
    else:
        items = store.filter_startups_directory(q)[:limit]
    site_url = store.get_site_url().rstrip("/")
    results = []
    for row in items:
        if kind == "projects":
            results.append({
                "name": row.get("title"),
                "url": f"{site_url}/projects/{row.get('id')}",
                "score": row.get("_match_score"),
                "meta": row.get("enterprise"),
            })
        else:
            results.append({
                "name": row.get("name"),
                "url": f"{site_url}/{kind}/{row.get('id')}",
                "score": row.get("_match_score"),
                "meta": row.get("specialty") or row.get("sector"),
            })
    return jsonify({"ok": True, "type": kind, "results": results})


@vitrine_bp.route("/api/advisor/chat", methods=["POST"])
def advisor_chat():
    from vitrine import advisor_ai

    if not advisor_ai.is_configured():
        return jsonify({"ok": False, "error": t("advisor.not_configured")}), 503

    if not advisor_ai.rate_limit_ok():
        return jsonify({"ok": False, "error": t("advisor.rate_limited")}), 429

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


@vitrine_bp.route("/api/advisor/chat/stream", methods=["POST"])
def advisor_chat_stream():
    """Server-Sent Events stream of the advisor reply for a fluid, live answer."""
    from flask import Response, stream_with_context

    from vitrine import advisor_ai

    if not advisor_ai.is_configured():
        return jsonify({"ok": False, "error": t("advisor.not_configured")}), 503
    if not advisor_ai.rate_limit_ok():
        return jsonify({"ok": False, "error": t("advisor.rate_limited")}), 429

    payload = request.get_json(silent=True) or {}
    user_type = payload.get("user_type", "enterprise")
    message = payload.get("message", "")
    history = payload.get("history", [])
    site_url = store.get_site_url()
    locale = get_locale()

    def event_stream():
        try:
            for kind, value in advisor_ai.stream(
                user_type=user_type,
                message=message,
                history=history,
                site_url=site_url,
                locale=locale,
            ):
                if kind == "meta":
                    yield f"event: meta\ndata: {json.dumps(value, ensure_ascii=False)}\n\n"
                else:
                    yield f"event: delta\ndata: {json.dumps({'text': value}, ensure_ascii=False)}\n\n"
            yield "event: done\ndata: {}\n\n"
        except advisor_ai.AdvisorError as exc:
            yield f"event: error\ndata: {json.dumps({'error': str(exc)}, ensure_ascii=False)}\n\n"
        except Exception:
            import logging

            logging.exception("advisor stream failed")
            yield f"event: error\ndata: {json.dumps({'error': t('advisor.error_generic', default='AI error.')}, ensure_ascii=False)}\n\n"

    return Response(
        stream_with_context(event_stream()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
