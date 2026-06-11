# Celery worker for studio image generation (generation_queue)
$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location (Join-Path $Root "backend")

Copy-Item (Join-Path $Root ".env") (Join-Path $PWD ".env") -Force

$py = Join-Path $PWD ".venv\Scripts\python.exe"
$celery = Join-Path $PWD ".venv\Scripts\celery.exe"
if (-not (Test-Path $py)) {
    Write-Host "Creating venv..."
    py -3.12 -m venv .venv
    & .\.venv\Scripts\pip install -r requirements.txt -q
}

Write-Host "Celery generation worker (studio)" -ForegroundColor Cyan
Write-Host "Queue: generation_queue" -ForegroundColor DarkGray
Write-Host "Requires Redis on CELERY_BROKER_URL (default redis://127.0.0.1:6379/3)" -ForegroundColor Yellow
Write-Host "Start Redis: docker compose up -d redis" -ForegroundColor Yellow
& $celery -A app.workers.celery_app worker -Q generation_queue -P solo -c 1 --loglevel=info -n generation@host
