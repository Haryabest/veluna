# Run Telegram bot on Windows host (not Docker).
# Docker containers often cannot reach api.telegram.org when VPN/TUN is active.
param([switch]$Background)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$Scripts = $PSScriptRoot
Set-Location (Join-Path $Root "backend")

$py = $null
foreach ($v in @("3.12", "3.11", "3.13")) {
    try { $py = & py "-$v" -c "import sys; print(sys.executable)" 2>$null; if ($py) { break } } catch {}
}
if (-not $py) {
    Write-Host "Installing Python 3.12..."
    winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements
    $py = & py -3.12 -c "import sys; print(sys.executable)"
}

$venv = Join-Path $PWD ".venv-bot"
if (-not (Test-Path "$venv\Scripts\python.exe")) {
    & py -3.12 -m venv $venv
    & "$venv\Scripts\pip" install -r requirements.txt -q
}

Copy-Item (Join-Path $Root ".env") (Join-Path $PWD ".env") -Force

function Stop-BotProcesses {
    Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -match 'app\.bot\.main' } |
        ForEach-Object {
            Write-Host "Stopping bot pid=$($_.ProcessId)..."
            Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        }
    Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -match 'watch-bot\.ps1' } |
        ForEach-Object {
            Write-Host "Stopping bot supervisor pid=$($_.ProcessId)..."
            Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        }
    Start-Sleep -Seconds 2
}

function Test-BotSupervisorRunning {
    return [bool](
        Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" -ErrorAction SilentlyContinue |
            Where-Object { $_.CommandLine -match 'watch-bot\.ps1' }
    )
}

Stop-BotProcesses

if ($Background) {
    . (Join-Path $Scripts "lib\process-utils.ps1")
    Write-Host "Starting bot supervisor (auto-restart, logs in logs/bot.log + logs/bot-watch.log)..."
    Start-HiddenProcess -FilePath "powershell.exe" `
        -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", (Join-Path $Scripts "watch-bot.ps1")) `
        -WorkingDirectory $Root -LogBaseName "bot-supervisor" -Root $Root | Out-Null
    Start-Sleep -Seconds 4
    if (Test-BotSupervisorRunning) {
        Write-Host "Bot supervisor OK." -ForegroundColor Green
    } else {
        Write-Warning "Supervisor may have failed - check logs/bot-supervisor.err.log"
    }
    exit 0
}

Write-Host "Starting bot on host with supervisor (Ctrl+C to stop)..."
& (Join-Path $Scripts "watch-bot.ps1")