# Run Telegram bot on Windows host (not Docker).
# Docker containers often cannot reach api.telegram.org when VPN/TUN is active.
$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
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
Write-Host "Starting bot on host (Ctrl+C to stop)..."
& "$venv\Scripts\python" -m app.bot.main
