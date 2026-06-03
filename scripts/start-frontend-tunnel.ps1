# Production frontend for Pinggy (dev mode chunks often timeout through free tunnel).
$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location (Join-Path $Root "frontend")

foreach ($port in 3000, 3001) {
    Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
        ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
}
Start-Sleep 2

Write-Host "Building Next.js (production)..." -ForegroundColor Cyan
npm run build
if ($LASTEXITCODE -ne 0) { throw "next build failed" }

Write-Host "Starting on http://0.0.0.0:3000 ..." -ForegroundColor Green
Start-Process -FilePath "powershell.exe" `
    -ArgumentList "-NoExit", "-NoProfile", "-Command", "cd '$PWD'; npm run start" `
    -WindowStyle Normal | Out-Null

Start-Sleep 4
try {
    $r = Invoke-WebRequest -Uri "http://127.0.0.1:3000" -UseBasicParsing -TimeoutSec 30
    Write-Host "Frontend OK: $($r.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "Warning: frontend not ready yet - wait a few seconds" -ForegroundColor Yellow
}
Write-Host "Next: .\scripts\dev-miniapp-up.ps1" -ForegroundColor Cyan
