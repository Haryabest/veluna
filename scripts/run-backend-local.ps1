# FastAPI on host (port 8000) — matches frontend/.env.local BACKEND_PORT=8000
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

Write-Host "Backend: http://127.0.0.1:8000 (API http://127.0.0.1:8000/api/v1)" -ForegroundColor Cyan
Write-Host "Need Postgres :5433 and Redis :6379 (docker compose up -d postgres redis minio)" -ForegroundColor Yellow
& $py -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
