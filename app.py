from datetime import timedelta
from flask import Flask
import os

import auth
from crm import crm_bp
from compte import compte_bp
from data import store
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


@app.context_processor
def inject_globals():
    return {
        "countries": store.get_startup_countries(),
        "current_user": auth.get_current_user(),
    }


if __name__ == "__main__":
    app.run(debug=True, port=5050)
