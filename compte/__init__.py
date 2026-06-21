from flask import Blueprint

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

    return {
        "countries": store.get_startup_countries(),
        "seo": store.get_seo_for_vitrine("home"),
        "page": store.get_page_content("home"),
        "analytics_enabled": False,
        "analytics_page_slug": "",
        "analytics_session": "",
        "current_user": auth.get_current_user(),
    }
