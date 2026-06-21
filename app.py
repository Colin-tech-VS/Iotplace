from flask import Flask
import os

import auth
from crm import crm_bp
from compte import compte_bp
from data import store
from vitrine import vitrine_bp

app = Flask(__name__)
app.secret_key = os.environ.get(
    "SECRET_KEY",
    os.environ.get("FLASK_SECRET_KEY", "iotplace-dev-secret-change-in-production"),
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
