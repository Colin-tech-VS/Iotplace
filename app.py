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
    SEND_FILE_MAX_AGE_DEFAULT=31536000,
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


@app.after_request
def optimize_response_headers(response):
    """Long-cache versioned static assets; short-cache uploaded logos."""
    if response.status_code != 200:
        return response
    path = request.path or ""
    if path.startswith(("/vitrine/static/", "/crm/static/")):
        response.headers.setdefault("Cache-Control", "public, max-age=31536000, immutable")
    elif path.startswith("/media/logos/"):
        response.headers.setdefault("Cache-Control", "public, max-age=86400")
    return response


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

    if not stripe_service.is_checkout_ready():
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


@app.route("/health")
def health_check():
    """Lightweight liveness + persistence probe for monitoring."""
    from flask import jsonify

    info = {"status": "ok"}
    try:
        _persist_info = persistence_info()
        info["backend"] = _persist_info.get("backend")
    except Exception:
        info["backend"] = "unknown"
    return jsonify(info)


def _render_error_page(status, title, message):
    """Render the standalone error page; fall back to plain HTML if even that fails."""
    from flask import render_template

    try:
        return render_template("error.html", status=status, title=title, message=message), status
    except Exception:
        logging.exception("Error page render failed")
        return (
            f"<!doctype html><meta charset='utf-8'>"
            f"<title>Erreur {status}</title>"
            f"<body style='font-family:sans-serif;text-align:center;padding:60px'>"
            f"<h1>{title}</h1><p>{message}</p><a href='/'>Retour à l'accueil</a></body>",
            status,
        )


@app.errorhandler(404)
def handle_404(error):
    return _render_error_page(
        404,
        "Page introuvable",
        "Cette page n'existe pas ou a été déplacée.",
    )


@app.errorhandler(500)
@app.errorhandler(Exception)
def handle_500(error):
    from werkzeug.exceptions import HTTPException

    # Let real HTTP errors (403, 404, 405…) keep their own status/handling.
    if isinstance(error, HTTPException) and error.code and error.code < 500:
        return error
    logging.exception("Unhandled error on %s", request.path if request else "?")
    return _render_error_page(
        500,
        "Une erreur est survenue",
        "Un incident technique a interrompu votre requête. "
        "Réessayez dans un instant — nos équipes ont été notifiées.",
    )


@app.context_processor
def inject_globals():
    from data.site_config import CONTACT_EMAIL

    return {
        "countries": store.get_startup_countries(),
        "current_user": auth.get_current_user(),
        "contact_email": CONTACT_EMAIL,
    }


if __name__ == "__main__":
    app.run(debug=True, port=5050)
