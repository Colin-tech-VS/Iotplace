from flask import Blueprint, request

compte_bp = Blueprint(
    "compte",
    __name__,
    template_folder="templates",
    url_prefix="",
)

from compte import routes  # noqa: E402, F401


@compte_bp.context_processor
def inject_compte_context():
    import auth
    from data import store

    from vitrine.i18n import compte_js_i18n, get_locale, inject_i18n_context

    endpoint = request.endpoint or ""
    site_url = store.get_site_url()
    canonical = store.build_canonical_url(site_url, request.path, b"")
    seo = store.get_compte_seo(endpoint)
    indexed = seo.get("robots", "").startswith("index")
    slug = "home"
    if endpoint == "compte.register_enterprise":
        slug = "enterprises"
    elif endpoint == "compte.register_startup":
        slug = "startups"
    return {
        **inject_i18n_context(),
        "compte_i18n": compte_js_i18n(),
        "countries": store.get_startup_countries(),
        "seo": seo,
        "seo_canonical": canonical,
        "seo_site_url": site_url,
        "seo_page_slug": slug,
        "seo_json_ld": store.build_json_ld(slug, canonical, site_url) if indexed else [],
        "seo_faq": store.get_page_faq(slug, get_locale()) if indexed else [],
        "seo_breadcrumbs": store.build_breadcrumbs(slug, site_url, locale=get_locale()),
        "page": store.get_page_content(slug if indexed else "home", get_locale()),
        "analytics_enabled": False,
        "analytics_page_slug": "",
        "analytics_session": "",
        "current_user": auth.get_current_user(),
        "unread_count": store.get_unread_count(auth.get_current_user()["id"]) if auth.get_current_user() else 0,
    }
