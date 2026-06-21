from functools import wraps

from flask import jsonify

import auth


def api_login_required(role=None):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user = auth.get_current_user()
            if not user:
                return jsonify({"ok": False, "error": "Connexion requise."}), 401
            if role and user.get("role") != role:
                return jsonify({"ok": False, "error": "Accès non autorisé."}), 403
            return view(*args, user=user, **kwargs)

        return wrapped

    return decorator
