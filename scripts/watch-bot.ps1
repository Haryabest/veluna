# Keeps the Telegram bot alive: restarts on crash / Telegram conflict / network blips.
$ErrorActionPreference = "Continue"
$Root = Split-Path $PSScriptRoot -Parent
$Backend = Join-Path $Root "backend"
$Python = Join-Path $Backend ".venv-bot\Scripts\python.exe"
$LogDir = Join-Path $Root "logs"
$WatchLog = Join-Path $LogDir "bot-watch.log"
$BotLog = Join-Path $LogDir "bot.log"

if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

function Write-Watch([string]$Msg) {
    $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $Msg"
    Add-Content -Path $WatchLog -Value $line -Encoding utf8
}

Set-Location $Backend
Copy-Item (Join-Path $Root ".env") (Join-Path $Backend ".env") -Force -ErrorAction SilentlyContinue

$mutex = New-Object System.Threading.Mutex($false, "Global\VelunaBotSupervisor")
if (-not $mutex.WaitOne(0, $false)) {
    Add-Content -Path $WatchLog -Value "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') Another supervisor already running, exit." -Encoding utf8
    exit 0
}

Write-Watch "Supervisor started (pid $PID)"

while ($true) {
    Write-Watch "Starting bot..."
    Add-Content -Path $BotLog -Value "`n=== $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') bot start ===`n" -Encoding utf8

    Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -match 'app\.bot\.main' } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

    $proc = Start-Process -FilePath $Python -ArgumentList @("-u", "-m", "app.bot.main") `
        -WorkingDirectory $Backend -PassThru -NoNewWindow -Wait `
        -RedirectStandardOutput $BotLog -RedirectStandardError (Join-Path $LogDir "bot.err.log")
    $code = if ($proc) { $proc.ExitCode } else { 1 }

    Write-Watch "Bot exited (code $code), restart in 5s"
    Start-Sleep -Seconds 5
}
