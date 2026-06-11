<#
.SYNOPSIS
  One-command Veluna redeploy: stop, pull (optional), rebuild frontend, backend, Celery, Pinggy, bot.

.EXAMPLE
  .\scripts\redeploy.ps1
  Full redeploy with git pull, frontend rebuild, Pinggy tunnel.

.EXAMPLE
  .\scripts\redeploy.ps1 -Quick
  Restart without rebuilding frontend (faster).

.EXAMPLE
  .\scripts\redeploy.ps1 -SkipTunnel
  Redeploy for localhost only (no Pinggy).
#>
param(
    [switch]$Pull,
    [switch]$Quick,
    [switch]$SkipTunnel,
    [switch]$Dev
)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$Scripts = $PSScriptRoot
Set-Location $Root

. (Join-Path $Scripts "lib\process-utils.ps1")

Write-Host ""
Write-Host "========================================" -ForegroundColor Magenta
Write-Host "  Veluna redeploy" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta
Write-Host ""

if ($Pull) {
    Write-Host "==> git pull origin main" -ForegroundColor Cyan
    git pull origin main
    if ($LASTEXITCODE -ne 0) {
        throw "git pull failed (exit $LASTEXITCODE)"
    }
    Write-Host ""
}

Write-Host "==> Stopping host services" -ForegroundColor Cyan
Stop-VelunaHostServices -KeepTunnel:($SkipTunnel.IsPresent)
Write-Host ""

& (Join-Path $Scripts "veluna-up.ps1") -HostOnly -SkipBuild:$Quick.IsPresent -SkipTunnel:$SkipTunnel.IsPresent -Dev:$Dev.IsPresent
