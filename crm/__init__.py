from flask import Blueprint

crm_bp = Blueprint(
    "crm",
    __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/crm",
)

from crm import routes  # noqa: E402, F401
