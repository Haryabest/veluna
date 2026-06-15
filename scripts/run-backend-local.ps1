# FastAPI on host — port 8010 avoids zombie listeners on :8000 from uvicorn --reload
param([int]$Port = 8010)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location (Join-Path $Root "backend")

Copy-Item (Join-Path $Root ".env") (Join-Path $PWD ".env") -Force

$py = Join-Path $PWD ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    Write-Host "Creating venv..."
    py -3.12 -m venv .venv
    & .\.venv\Scripts\pip install -r requirements.txt -q
}

Write-Host "Backend: http://127.0.0.1:$Port (API http://127.0.0.1:$Port/api/v1)" -ForegroundColor Cyan
Write-Host "Need Postgres :5434 and Redis :6380 (docker compose up -d postgres redis minio)" -ForegroundColor Yellow
Write-Host "Celery: .\scripts\run-celery-generation.ps1" -ForegroundColor Yellow
& $py -m uvicorn app.main:app --host 0.0.0.0 --port $Port
