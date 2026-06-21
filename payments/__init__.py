from flask import Blueprint

payments_bp = Blueprint("payments", __name__)

from payments import routes  # noqa: E402, F401
