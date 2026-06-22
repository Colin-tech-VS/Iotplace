import hmac
import os
import secrets
import time
from functools import wraps

from flask import abort, flash, redirect, request, session, url_for
from werkzeug.security import check_password_hash

CRM_SESSION_TOKEN = "crm_admin_token"
CRM_SESSION_AT = "crm_admin_at"
CRM_CSRF_KEY = "crm_csrf_token"
SESSION_MAX_AGE = 8 * 3600  # 8 h
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_SECONDS = 15 * 60

_login_attempts = {}


def _env(name):
    return (os.environ.get(name) or "").strip()


def get_crm_credentials():
    return _env("CRM_ADMIN_USERNAME"), _env("CRM_ADMIN_PASSWORD")


def get_crm_password_hash():
    return _env("CRM_ADMIN_PASSWORD_HASH")


def is_crm_configured():
    username = _env("CRM_ADMIN_USERNAME")
    if not username:
        return False
    return bool(_env("CRM_ADMIN_PASSWORD") or get_crm_password_hash())


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
    count, locked_until = _login_attempts.get(ip, (0, 0))
    if time.time() >= locked_until:
        count = 0
    count += 1
    locked_until = time.time() + LOCKOUT_SECONDS if count >= MAX_LOGIN_ATTEMPTS else 0
    _login_attempts[ip] = (count, locked_until)


def clear_login_attempts(ip=None):
    _login_attempts.pop(ip or _client_ip(), None)


def verify_crm_login(username, password):
    expected_user, expected_pass = get_crm_credentials()
    password_hash = get_crm_password_hash()
    if not expected_user or (not expected_pass and not password_hash):
        return False
    user_ok = hmac.compare_digest((username or "").strip(), expected_user)
    if password_hash:
        pass_ok = check_password_hash(password_hash, password or "")
    else:
        pass_ok = hmac.compare_digest(password or "", expected_pass)
    return user_ok and pass_ok


def login_crm_admin():
    session[CRM_SESSION_TOKEN] = secrets.token_urlsafe(48)
    session[CRM_SESSION_AT] = time.time()
    session.permanent = True
    session.pop(CRM_CSRF_KEY, None)


def logout_crm_admin():
    session.pop(CRM_SESSION_TOKEN, None)
    session.pop(CRM_SESSION_AT, None)
    session.pop(CRM_CSRF_KEY, None)


def is_crm_authenticated():
    token = session.get(CRM_SESSION_TOKEN)
    issued = session.get(CRM_SESSION_AT)
    if not token or not issued:
        return False
    if time.time() - float(issued) > SESSION_MAX_AGE:
        logout_crm_admin()
        return False
    return True


def get_csrf_token():
    if CRM_CSRF_KEY not in session:
        session[CRM_CSRF_KEY] = secrets.token_hex(32)
    return session[CRM_CSRF_KEY]


def validate_csrf(token):
    expected = session.get(CRM_CSRF_KEY, "")
    return bool(token and expected and hmac.compare_digest(token, expected))


def safe_next_url(next_url):
    if not next_url:
        return url_for("crm.dashboard")
    if next_url.startswith("/crm") and not next_url.startswith("//"):
        return next_url
    return url_for("crm.dashboard")


def crm_login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not is_crm_configured():
            abort(503)
        if not is_crm_authenticated():
            if session.get(CRM_SESSION_TOKEN):
                flash("Session expirée. Reconnectez-vous.", "warning")
            return redirect(url_for("crm.login", next=request.path))
        return view(*args, **kwargs)

    return wrapped
