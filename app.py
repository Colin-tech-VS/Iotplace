from datetime import timedelta
from flask import Flask, redirect, request
import logging
import os

if os.environ.get("FLASK_ENV") != "production" and not os.environ.get("SCALINGO_APP"):
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass

import auth
from crm import crm_bp
from compte import compte_bp
from data import store
from payments import payments_bp
from vitrine import vitrine_bp

app = Flask(__name__)
_is_prod = os.environ.get("FLASK_ENV") == "production" or os.environ.get("SCALINGO_APP") is not None
app.secret_key = os.environ.get(
    "SECRET_KEY",
    os.environ.get("FLASK_SECRET_KEY", "iotplace-dev-secret-change-in-production"),
)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=_is_prod or os.environ.get("SESSION_COOKIE_SECURE") == "1",
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
)

app.register_blueprint(crm_bp)
app.register_blueprint(vitrine_bp)
app.register_blueprint(compte_bp)
app.register_blueprint(payments_bp)

if _is_prod:
    try:
        from werkzeug.middleware.proxy_fix import ProxyFix

        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    except ImportError:
        pass


@app.before_request
def enforce_canonical_host():
    """Redirect www and Scalingo default host to SITE_URL (SEO + Stripe return URLs)."""
    if not _is_prod or request.method not in ("GET", "HEAD"):
        return None
    from data.site_config import ALIASES_TO_CANONICAL, is_scalingo_host
    from data.store import get_site_url

    host = (request.host or "").split(":")[0].lower()
    canonical = get_site_url().replace("https://", "").replace("http://", "").rstrip("/")
    if not canonical:
        return None
    if host == canonical:
        return None
    if host in ALIASES_TO_CANONICAL or is_scalingo_host(host):
        return redirect(f"https://{canonical}{request.full_path}", code=301)
    return None


@app.context_processor
def inject_i18n():
    from vitrine.i18n import inject_i18n_context

    return inject_i18n_context()


from vitrine.i18n import t, translate_phase, translate_status

app.jinja_env.globals["t"] = t
app.jinja_env.globals["translate_phase"] = translate_phase
app.jinja_env.globals["translate_status"] = translate_status


if _is_prod:
    from crm import auth as crm_auth

    if not crm_auth.is_crm_configured():
        logging.warning(
            "CRM non configuré: définissez CRM_ADMIN_USERNAME et CRM_ADMIN_PASSWORD "
            "dans les variables Scalingo (pas dans scalingo.json avec une valeur vide)."
        )
    from payments import stripe_service

    if not stripe_service.is_configured():
        logging.warning(
            "Stripe non configuré: définissez STRIPE_SECRET_KEY et STRIPE_PUBLISHABLE_KEY "
            "dans les variables Scalingo."
        )
    elif not stripe_service.is_webhook_configured():
        logging.warning(
            "STRIPE_WEBHOOK_SECRET manquant — les webhooks Stripe ne seront pas vérifiés. "
            "Endpoint: /webhooks/stripe"
        )


from data.persistence import persistence_info

_persist = persistence_info()
logging.info("Iotplace persistence backend=%s", _persist.get("backend"))
if _persist.get("path"):
    logging.info("Iotplace data file=%s", _persist.get("path"))


@app.context_processor
def inject_globals():
    return {
        "countries": store.get_startup_countries(),
        "current_user": auth.get_current_user(),
    }


if __name__ == "__main__":
    app.run(debug=True, port=5050)
