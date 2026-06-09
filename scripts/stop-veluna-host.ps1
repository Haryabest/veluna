# Stop Veluna host processes and close leftover Veluna CMD/PowerShell windows.
$ErrorActionPreference = "Continue"
$Root = Split-Path $PSScriptRoot -Parent
. (Join-Path $PSScriptRoot "lib\process-utils.ps1")

Write-Host "Stopping Veluna host services..." -ForegroundColor Cyan
Stop-VelunaHostServices
Write-Host "Done. Logs remain in $Root\logs" -ForegroundColor Green
