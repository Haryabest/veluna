# Celery worker for async chat AI replies (chat_queue)
$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location (Join-Path $Root "backend")

Copy-Item (Join-Path $Root ".env") (Join-Path $PWD ".env") -Force

$celery = Join-Path $PWD ".venv\Scripts\celery.exe"
if (-not (Test-Path $celery)) {
    Write-Host "Creating venv..."
    py -3.12 -m venv .venv
    & .\.venv\Scripts\pip install -r requirements.txt -q
}

Write-Host "Celery chat worker" -ForegroundColor Cyan
Write-Host "Queue: chat_queue" -ForegroundColor DarkGray
Write-Host "Requires Redis (CELERY_BROKER_URL)" -ForegroundColor Yellow
& $celery -A app.workers.celery_app worker -Q chat_queue -c 2 --loglevel=info -n chat@host
