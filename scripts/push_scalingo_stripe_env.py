#!/usr/bin/env python3
"""Push Stripe env vars from .env to Scalingo via API (no CLI required).

Usage:
  set SCALINGO_API_TOKEN=tk-us-...   # from https://dashboard.scalingo.com/account/tokens
  python scripts/push_scalingo_stripe_env.py

Optional: SCALINGO_APP=iotplace (default), SCALINGO_API_URL=api.osc-fr1.scalingo.com
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

VARS = (
    "SITE_URL",
    "STRIPE_SECRET_KEY",
    "STRIPE_PUBLISHABLE_KEY",
    "STRIPE_WEBHOOK_SECRET",
    "STRIPE_PRO_PRICE_ID",
    "IOTPLACE_COMMISSION_PERCENT",
    "IOTPLACE_POC_APPLICATION_FEE_EUR",
    "IOTPLACE_POC_APPLICATION_COMMISSION_PERCENT",
    "IOTPLACE_PRO_COMMISSION_PERCENT",
    "IOTPLACE_PRO_PRICE_EUR",
)


def _load_dotenv() -> None:
    path = ROOT / ".env"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip()
        if key and key not in os.environ:
            os.environ[key] = value


def _exchange_bearer(api_token: str) -> str:
    req = urllib.request.Request(
        "https://auth.scalingo.com/v1/tokens/exchange",
        method="POST",
        headers={"Accept": "application/json", "Content-Type": "application/json"},
    )
    import base64

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


def main() -> int:
    _load_dotenv()
    api_token = (os.environ.get("SCALINGO_API_TOKEN") or "").strip()
    if not api_token:
        print("SCALINGO_API_TOKEN missing. Create one at https://dashboard.scalingo.com/account/tokens", file=sys.stderr)
        return 1

    app = (os.environ.get("SCALINGO_APP") or "iotplace").strip()
    api_url = (os.environ.get("SCALINGO_API_URL") or "api.osc-fr1.scalingo.com").strip()

    to_set = {name: (os.environ.get(name) or "").strip() for name in VARS}
    missing = [k for k, v in to_set.items() if not v and k.startswith("STRIPE_")]
    if missing:
        print(f"Missing in .env: {', '.join(missing)}", file=sys.stderr)
        return 1

    print(f"Exchanging Scalingo API token…")
    bearer = _exchange_bearer(api_token)

    print(f"Fetching existing variables for {app}…")
    existing = {
        item["name"]: item["id"]
        for item in _api_request(bearer, api_url, "GET", f"/v1/apps/{app}/variables").get("variables", [])
    }

    for name, value in to_set.items():
        if not value:
            continue
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

    print("Done. Restart the app: scalingo --app", app, "restart (or redeploy from dashboard).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
