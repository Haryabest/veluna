# One-time setup: copy env templates for local development
$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

function Copy-IfMissing($src, $dst) {
    if (Test-Path $dst) {
        Write-Host "Skip (exists): $dst"
    } else {
        Copy-Item $src $dst
        Write-Host "Created: $dst"
    }
}

Copy-IfMissing ".env.example" ".env"
Copy-IfMissing "frontend\.env.local.example" "frontend\.env.local"

# Patch root .env for local dev (127.0.0.1 instead of Docker hostnames)
$envFile = Join-Path $Root ".env"
$content = Get-Content $envFile -Raw
$content = $content -replace '@postgres:5432', '@127.0.0.1:5432'
$content = $content -replace 'redis://redis:', 'redis://127.0.0.1:'
$content = $content -replace 'MINIO_ENDPOINT=minio:9000', 'MINIO_ENDPOINT=127.0.0.1:9000'
$content = $content -replace 'NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1', 'NEXT_PUBLIC_API_URL='
Set-Content -Path $envFile -Value $content.TrimEnd()
Add-Content -Path $envFile -Value ""

# Backend reads .env from its own directory
Copy-Item $envFile (Join-Path $Root "backend\.env") -Force
Write-Host "Synced: backend\.env"

Write-Host ""
Write-Host "=== Veluna local setup ===" -ForegroundColor Cyan
Write-Host "1. Start infra:  docker compose up postgres redis minio -d"
Write-Host "2. Backend:      cd backend; python -m venv .venv; .\.venv\Scripts\pip install -r requirements.txt"
Write-Host "                 .\.venv\Scripts\alembic upgrade head"
Write-Host "                 .\.venv\Scripts\uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
Write-Host "3. Frontend:     cd frontend; npm run dev"
Write-Host ""
Write-Host "Telegram Mini App tunnel:  .\scripts\dev-miniapp-up.ps1"
Write-Host "  -> updates TELEGRAM_WEBAPP_URL + NEXT_PUBLIC_API_URL automatically"
