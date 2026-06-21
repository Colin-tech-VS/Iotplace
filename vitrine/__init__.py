from flask import Blueprint

vitrine_bp = Blueprint(
    "vitrine",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/vitrine/static",
)

from vitrine import routes  # noqa: E402, F401
