import time
from functools import wraps
from urllib.parse import urlparse

from flask import flash, g, redirect, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from data import store


def hash_password(password):
    return generate_password_hash(password)


def verify_password(password_hash, password):
    return check_password_hash(password_hash, password)


def safe_next_url(next_url, fallback_endpoint="compte.home"):
    """Only allow same-origin relative redirects (blocks open-redirect phishing)."""
    fallback = url_for(fallback_endpoint)
    if not next_url:
        return fallback
    # Reject absolute URLs, protocol-relative (//evil.com) and non-path targets.
    parsed = urlparse(next_url)
    if parsed.scheme or parsed.netloc:
        return fallback
    if not next_url.startswith("/") or next_url.startswith("//"):
        return fallback
    return next_url


# ── Login brute-force throttle (per client IP, shared across this process) ──
MAX_LOGIN_ATTEMPTS = 8
LOCKOUT_SECONDS = 15 * 60
_login_attempts: dict[str, tuple[int, float]] = {}


def _client_ip():
    forwarded = (request.headers.get("X-Forwarded-For") or "").split(",")[0].strip()
    return forwarded or request.remote_addr or "unknown"


def is_login_locked(ip=None):
    ip = ip or _client_ip()
    entry = _login_attempts.get(ip)
    if not entry:
        return False
    count, locked_until = entry
    if time.time() < locked_until:
        return True
    if count >= MAX_LOGIN_ATTEMPTS:
        _login_attempts.pop(ip, None)
    return False


def record_failed_login(ip=None):
    ip = ip or _client_ip()
    count, locked_until = _login_attempts.get(ip, (0, 0.0))
    # Reset the counter only after a previous lockout window has expired; while
    # not locked (locked_until == 0) the failures must keep accumulating.
    if locked_until and time.time() >= locked_until:
        count = 0
        locked_until = 0.0
    count += 1
    if count >= MAX_LOGIN_ATTEMPTS:
        locked_until = time.time() + LOCKOUT_SECONDS
    _login_attempts[ip] = (count, locked_until)


def clear_login_attempts(ip=None):
    _login_attempts.pop(ip or _client_ip(), None)


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
