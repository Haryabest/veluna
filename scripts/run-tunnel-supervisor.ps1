# Start Pinggy tunnel + auto-restart supervisor (background).
param([switch]$Foreground)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$Scripts = $PSScriptRoot
Set-Location $Root

function Stop-TunnelSupervisor {
    Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -match 'watch-tunnel\.ps1' } |
        ForEach-Object {
            Write-Host "Stopping tunnel supervisor pid=$($_.ProcessId)..."
            Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        }
}

Stop-TunnelSupervisor
& (Join-Path $Scripts "dev-miniapp-up.ps1")

if ($Foreground) {
    & (Join-Path $Scripts "watch-tunnel.ps1")
} else {
    Write-Host "Starting tunnel supervisor (checks every 2 min, log: logs/tunnel-watch.log)..."
    Start-Process powershell -ArgumentList @(
        "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", (Join-Path $Scripts "watch-tunnel.ps1")
    ) -WindowStyle Hidden
    Write-Host "Tunnel supervisor OK."
}
