# Synchronise les variables d'environnement Scalingo depuis un fichier .env local.
# Prérequis : CLI Scalingo installé et authentifié (scalingo login)
# Usage : .\scripts\sync_scalingo_env.ps1 [-App iotplace] [-EnvFile .env] [-DryRun]

param(
    [string]$App = "iotplace",
    [string]$EnvFile = ".env",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command scalingo -ErrorAction SilentlyContinue)) {
    Write-Error "CLI Scalingo introuvable. Installez-le : https://doc.scalingo.com/platform/cli/start"
}

$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$envPath = Join-Path $root $EnvFile

if (-not (Test-Path $envPath)) {
    Write-Error "Fichier introuvable : $envPath (copiez .env.example vers .env et renseignez les secrets)"
}

# Variables gérées par scalingo.json (valeurs non secrètes) — ne pas écraser depuis .env sauf override explicite
$skipFromEnv = @(
    "FLASK_ENV"
)

$lines = Get-Content $envPath -Encoding UTF8
$pairs = @()

foreach ($line in $lines) {
    $line = $line.Trim()
    if (-not $line -or $line.StartsWith("#")) { continue }
    $idx = $line.IndexOf("=")
    if ($idx -lt 1) { continue }
    $key = $line.Substring(0, $idx).Trim()
    $val = $line.Substring($idx + 1).Trim()
    if ($val.StartsWith('"') -and $val.EndsWith('"')) { $val = $val.Substring(1, $val.Length - 2) }
    if ($skipFromEnv -contains $key) { continue }
    if ([string]::IsNullOrWhiteSpace($val)) {
        Write-Warning "Ignoré (vide) : $key"
        continue
    }
    $pairs += @{ Key = $key; Value = $val }
}

if ($pairs.Count -eq 0) {
    Write-Error "Aucune variable à synchroniser dans $envPath"
}

Write-Host "App Scalingo : $App"
Write-Host "Variables à pousser : $($pairs.Count)"

foreach ($p in $pairs) {
    $arg = "$($p.Key)=$($p.Value)"
    if ($DryRun) {
        Write-Host "[dry-run] scalingo --app $App env-set $($p.Key)=***"
    } else {
        Write-Host "→ $($p.Key)"
        & scalingo --app $App env-set $arg
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    }
}

if (-not $DryRun) {
    Write-Host ""
    Write-Host "OK — redémarrez l'app si besoin : scalingo --app $App restart"
    Write-Host "Vérifiez l'addon PostgreSQL : scalingo --app $App addons"
}
