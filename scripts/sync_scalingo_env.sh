#!/usr/bin/env bash
# Sync Scalingo env vars from .env — requires scalingo CLI (scalingo login)
set -euo pipefail
APP="${1:-iotplace}"
ENV_FILE="${2:-.env}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! command -v scalingo >/dev/null 2>&1; then
  echo "Install Scalingo CLI: https://doc.scalingo.com/platform/cli/start" >&2
  exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing $ENV_FILE — copy from .env.example" >&2
  exit 1
fi

SKIP_REGEX='^(FLASK_ENV)='
count=0
while IFS= read -r line || [[ -n "$line" ]]; do
  line="${line%%#*}"
  line="$(echo "$line" | xargs)"
  [[ -z "$line" ]] && continue
  [[ "$line" != *"="* ]] && continue
  key="${line%%=*}"
  val="${line#*=}"
  val="${val%\"}"; val="${val#\"}"
  [[ "$key" =~ $SKIP_REGEX ]] && continue
  [[ -z "$val" ]] && { echo "skip empty: $key"; continue; }
  echo "→ $key"
  scalingo --app "$APP" env-set "$key=$val"
  count=$((count + 1))
done < "$ENV_FILE"

echo "Synced $count variables to $APP"
echo "Restart: scalingo --app $APP restart"
