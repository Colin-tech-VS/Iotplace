# Sync Stripe variables from .env to Scalingo (requires Scalingo CLI + login).
# Usage: .\scripts\set_scalingo_stripe_env.ps1 [-App iotplace]

param(
    [string]$App = "iotplace",
    [string]$EnvFile = ".env"
)

if (-not (Get-Command scalingo -ErrorAction SilentlyContinue)) {
    Write-Error "Scalingo CLI not found. Install: https://doc.scalingo.com/cli"
    exit 1
}

if (-not (Test-Path $EnvFile)) {
    Write-Error "Missing $EnvFile"
    exit 1
}

$keys = @(
    "SITE_URL",
    "STRIPE_SECRET_KEY",
    "STRIPE_PUBLISHABLE_KEY",
    "STRIPE_WEBHOOK_SECRET",
    "STRIPE_PRO_PRICE_ID",
    "IOTPLACE_COMMISSION_PERCENT",
    "IOTPLACE_POC_APPLICATION_FEE_EUR",
    "IOTPLACE_POC_APPLICATION_COMMISSION_PERCENT",
    "IOTPLACE_PRO_COMMISSION_PERCENT",
    "IOTPLACE_PRO_PRICE_EUR"
)

$vars = @{}
Get-Content $EnvFile | ForEach-Object {
    if ($_ -match '^\s*#' -or $_ -notmatch '=') { return }
    $parts = $_ -split '=', 2
    $name = $parts[0].Trim()
    $value = $parts[1].Trim()
    if ($keys -contains $name -and $value) {
        $vars[$name] = $value
    }
}

foreach ($name in $keys) {
    if (-not $vars.ContainsKey($name)) {
        Write-Warning "Skip $name (not set in $EnvFile)"
        continue
    }
    Write-Host "Setting $name on $App..."
    scalingo --app $App env-set "$name=$($vars[$name])"
}

Write-Host "Done. Redeploy if needed: scalingo --app $App restart"
