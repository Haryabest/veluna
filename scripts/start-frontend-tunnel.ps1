# Production frontend for Pinggy (dev mode chunks often timeout through free tunnel).
$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$backendPort = "8020"
$envLocal = Join-Path $Root "frontend\.env.local"
if (Test-Path $envLocal) {
    Get-Content $envLocal | ForEach-Object {
        if ($_ -match '^BACKEND_PORT=(.+)$') { $backendPort = $matches[1].Trim() }
    }
}
try {
    $running = docker inspect -f "{{.State.Status}}" veluna-backend 2>$null
    if ($running -eq "running") {
        $mapped = docker port veluna-backend 8000/tcp 2>$null
        if ($mapped -match ':(\d+)->') { $backendPort = $matches[1] }
    }
} catch {}
Set-Location (Join-Path $Root "frontend")
$env:BACKEND_PORT = $backendPort
Write-Host "API proxy target: 127.0.0.1:$backendPort" -ForegroundColor DarkGray

foreach ($port in 3000, 3001) {
    Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
        ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
}
Start-Sleep 2

Write-Host "Building Next.js (production)..." -ForegroundColor Cyan
npm run build
if ($LASTEXITCODE -ne 0) { throw "next build failed" }

Write-Host "Starting on http://0.0.0.0:3000 (background, logs in logs/frontend.*)..." -ForegroundColor Green
. (Join-Path $PSScriptRoot "lib\process-utils.ps1")
Start-FrontendHidden -WorkingDirectory $PWD -Root $Root -BackendPort ([int]$backendPort) | Out-Null

Start-Sleep 4
try {
    $r = Invoke-WebRequest -Uri "http://127.0.0.1:3000" -UseBasicParsing -TimeoutSec 30
    Write-Host "Frontend OK: $($r.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "Warning: frontend not ready yet - wait a few seconds" -ForegroundColor Yellow
}
Write-Host "Next: .\scripts\dev-miniapp-up.ps1" -ForegroundColor Cyan
