#!/usr/bin/env python3
"""Push .env variables to Scalingo via API (no CLI required).

Usage:
  set SCALINGO_API_TOKEN=tk-us-...   # https://dashboard.scalingo.com/account/tokens
  python scripts/push_scalingo_env.py

Optional: SCALINGO_APP=iotplace, SCALINGO_API_URL=api.osc-fr1.scalingo.com

Production overrides (always applied on Scalingo):
  FLASK_ENV=production
  SITE_URL=https://iotplace.fr (or SCALINGO_SITE_URL if set)
"""

from __future__ import annotations

import base64
import json
import os
import secrets
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Never push these keys to the app environment
SKIP_KEYS = frozenset({
    "SCALINGO_API_TOKEN",
    "SCALINGO_APP",
    "SCALINGO_API_URL",
    "SCALINGO_SITE_URL",
})

PROD_OVERRIDES = {
    "FLASK_ENV": "production",
}


def _load_dotenv() -> dict[str, str]:
    path = ROOT / ".env"
    if not path.exists():
        return {}
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip()
        if key:
            out[key] = value
    return out


def _exchange_bearer(api_token: str) -> str:
    req = urllib.request.Request(
        "https://auth.scalingo.com/v1/tokens/exchange",
        method="POST",
        headers={"Accept": "application/json", "Content-Type": "application/json"},
    )
    auth = base64.b64encode(f":{api_token}".encode()).decode()
    req.add_header("Authorization", f"Basic {auth}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())
    token = data.get("token") or data.get("access_token")
    if not token:
        raise RuntimeError(f"Bearer exchange failed: {data}")
    return token


def _api_request(bearer: str, api_url: str, method: str, path: str, body: dict | None = None) -> dict:
    url = f"https://{api_url}{path}"
    payload = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url,
        data=payload,
        method=method,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {bearer}",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode()
        return json.loads(raw) if raw else {}


def _build_vars() -> dict[str, str]:
    to_set = {k: v for k, v in _load_dotenv().items() if k not in SKIP_KEYS and v}

    to_set.update(PROD_OVERRIDES)
    site = (os.environ.get("SCALINGO_SITE_URL") or to_set.get("SITE_URL") or "https://iotplace.fr").strip()
    if site.startswith("http://localhost"):
        site = "https://iotplace.fr"
    to_set["SITE_URL"] = site

    secret = to_set.get("SECRET_KEY", "")
    if not secret or secret in ("dev-secret-change-me", "iotplace-dev-secret-change-in-production"):
        to_set["SECRET_KEY"] = secrets.token_urlsafe(48)
        print("Generated new SECRET_KEY for production (not printed).")

    return to_set


def main() -> int:
    api_token = (os.environ.get("SCALINGO_API_TOKEN") or _load_dotenv().get("SCALINGO_API_TOKEN") or "").strip()
    if not api_token:
        print(
            "SCALINGO_API_TOKEN missing. Add it to .env or env, then re-run.\n"
            "Create: https://dashboard.scalingo.com/account/tokens",
            file=sys.stderr,
        )
        return 1

    app = (os.environ.get("SCALINGO_APP") or _load_dotenv().get("SCALINGO_APP") or "iotplace").strip()
    api_url = (os.environ.get("SCALINGO_API_URL") or _load_dotenv().get("SCALINGO_API_URL") or "api.osc-fr1.scalingo.com").strip()
    to_set = _build_vars()

    if not to_set:
        print("No variables to push.", file=sys.stderr)
        return 1

    print(f"Exchanging Scalingo API token…")
    bearer = _exchange_bearer(api_token)

    print(f"Fetching existing variables for {app}…")
    existing = {
        item["name"]: item["id"]
        for item in _api_request(bearer, api_url, "GET", f"/v1/apps/{app}/variables").get("variables", [])
    }

    for name in sorted(to_set):
        value = to_set[name]
        if name in existing:
            print(f"PATCH {name}")
            _api_request(
                bearer,
                api_url,
                "PATCH",
                f"/v1/apps/{app}/variables/{existing[name]}",
                {"variable": {"value": value}},
            )
        else:
            print(f"POST {name}")
            _api_request(
                bearer,
                api_url,
                "POST",
                f"/v1/apps/{app}/variables",
                {"variable": {"name": name, "value": value}},
            )

    print(f"Done — {len(to_set)} variable(s) synced. Restart: scalingo --app {app} restart")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
