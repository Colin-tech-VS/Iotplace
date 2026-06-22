from functools import wraps

from flask import flash, g, redirect, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from data import store


def hash_password(password):
    return generate_password_hash(password)


def verify_password(password_hash, password):
    return check_password_hash(password_hash, password)


def login_user(user):
    session["user_id"] = user["id"]
    session["user_role"] = user["role"]


def logout_user():
    session.pop("user_id", None)
    session.pop("user_role", None)


def get_current_user():
    if hasattr(g, "current_user"):
        return g.current_user
    user_id = session.get("user_id")
    if not user_id:
        g.current_user = None
        return None
    g.current_user = store.get_user(user_id)
    return g.current_user


def login_required(role=None):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user = get_current_user()
            if not user:
                flash("Connectez-vous pour accéder à cette page.", "error")
                return redirect(url_for("compte.login", next=request.url))
            if role and user.get("role") != role:
                flash("Accès non autorisé.", "error")
                return redirect(url_for("compte.home"))
            return view(*args, **kwargs)

        return wrapped

    return decorator
