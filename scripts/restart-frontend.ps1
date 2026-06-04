# Reload frontend with correct BACKEND_PORT from .env.local
param([switch]$Rebuild)
$ErrorActionPreference = "Continue"
$Root = Split-Path $PSScriptRoot -Parent
$envLocal = Join-Path $Root "frontend\.env.local"
$port = "8020"
if (Test-Path $envLocal) {
    Get-Content $envLocal | ForEach-Object {
        if ($_ -match '^BACKEND_PORT=(.+)$') { $port = $matches[1].Trim() }
    }
}
Write-Host "Restarting frontend (proxy -> 127.0.0.1:$port)..." -ForegroundColor Cyan
Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue |
    ForEach-Object {
        $p = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue
        if ($p -and $p.ProcessName -eq "node") {
            Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
        }
    }
Start-Sleep -Seconds 2
$feDir = Join-Path $Root "frontend"
if ($Rebuild -or -not (Test-Path (Join-Path $feDir ".next"))) {
    Write-Host "Rebuilding Next.js (picks up API error text + proxy port)..." -ForegroundColor Cyan
    Push-Location $feDir
    $env:BACKEND_PORT = $port
    npm run build
    if ($LASTEXITCODE -ne 0) { Pop-Location; throw "next build failed" }
    Pop-Location
}
Start-Process powershell.exe -ArgumentList @(
    "-NoExit", "-NoProfile", "-Command",
    "cd '$feDir'; `$host.UI.RawUI.WindowTitle='Veluna Frontend'; `$env:BACKEND_PORT='$port'; npm run start"
) -WindowStyle Normal | Out-Null
Start-Sleep -Seconds 6
try {
    $h = Invoke-WebRequest "http://127.0.0.1:$port/health" -UseBasicParsing -TimeoutSec 5
    Write-Host "Backend :$port -> $($h.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "Backend :$port not reachable. Run .\scripts\veluna-up.ps1" -ForegroundColor Red
}
try {
    $f = Invoke-WebRequest "http://127.0.0.1:3000" -UseBasicParsing -TimeoutSec 10
    Write-Host "Frontend :3000 -> $($f.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "Frontend still starting..." -ForegroundColor Yellow
}
