<#
.SYNOPSIS
  One-click Veluna: Docker (or fallback), backend, frontend, Pinggy, bot, Celery.

.EXAMPLE
  .\scripts\veluna-up.ps1

.EXAMPLE
  .\scripts\veluna-up.ps1 -SkipBuild -SkipTunnel   # quick restart, localhost only
#>
param(
    [switch]$SkipBuild,
    [switch]$SkipTunnel,
    [switch]$Dev
)

$ErrorActionPreference = "Continue"
$Root = Split-Path $PSScriptRoot -Parent
$Scripts = $PSScriptRoot
Set-Location $Root

function Invoke-External {
    param([scriptblock]$Command)
    $items = & $Command 2>&1
    foreach ($line in $items) {
        if ($line) { Write-Host $line }
    }
    return $LASTEXITCODE
}

function Write-Step([string]$Msg) {
    Write-Host ""
    Write-Host "==> $Msg" -ForegroundColor Cyan
}

function Test-TcpPort([int]$Port) {
    $c = New-Object System.Net.Sockets.TcpClient
    try {
        $c.Connect("127.0.0.1", $Port)
        $c.Close()
        return $true
    } catch {
        return $false
    }
}

function Stop-Port([int]$Port, [string[]]$Names = @("node", "python")) {
    Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
        ForEach-Object {
            $proc = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue
            if ($proc -and ($Names -contains $proc.ProcessName)) {
                Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
            }
        }
}

function Test-DockerOk {
    try {
        $null = docker ps -q 2>&1
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

function Wait-Docker([int]$Minutes = 4) {
    $deadline = (Get-Date).AddMinutes($Minutes)
    while ((Get-Date) -lt $deadline) {
        if (Test-DockerOk) { return $true }
        Start-Sleep -Seconds 6
    }
    return $false
}

function Try-StartDockerDesktop {
    $paths = @(
        "${env:ProgramFiles}\Docker\Docker\Docker Desktop.exe",
        "${env:ProgramFiles(x86)}\Docker\Docker\Docker Desktop.exe"
    )
    foreach ($p in $paths) {
        if (Test-Path $p) {
            Write-Host "Starting Docker Desktop..." -ForegroundColor Yellow
            Start-Process $p -ErrorAction SilentlyContinue
            return
        }
    }
}

function Set-FrontendBackendPort([int]$Port) {
    $envLocal = Join-Path $Root "frontend\.env.local"
    @(
        "# Auto: veluna-up.ps1",
        "NEXT_PUBLIC_API_URL=/api/v1",
        "NEXT_PUBLIC_WS_URL=",
        "BACKEND_HOST=127.0.0.1",
        "BACKEND_PORT=$Port",
        ""
    ) | Set-Content -Path $envLocal -Encoding utf8
}

function Start-FrontendProcess([int]$BackendPort, [string]$NpmScript) {
    . (Join-Path $Scripts "lib\process-utils.ps1")
    $feDir = Join-Path $Root "frontend"
    if ($NpmScript -eq "start") {
        Start-FrontendHidden -WorkingDirectory $feDir -Root $Root -BackendPort $BackendPort | Out-Null
        return
    }
    $env:BACKEND_PORT = "$BackendPort"
    Start-NpmHidden -NpmArgs @("run", $NpmScript) `
        -WorkingDirectory $feDir -LogBaseName "frontend" -Root $Root | Out-Null
}

function Sync-EnvFiles {
    Copy-Item (Join-Path $Root ".env") (Join-Path $Root "backend\.env") -Force
}

function Invoke-Migrations {
    if (Test-DockerOk) {
        $status = docker inspect -f "{{.State.Status}}" veluna-backend 2>$null
        if ($status -eq "running") {
            $code = Invoke-External { docker exec veluna-backend alembic upgrade head }
            if ($code -eq 0) {
                Write-Host "Migrations OK (Docker)" -ForegroundColor Green
                return
            }
        }
    }
    $py = Join-Path $Root "backend\.venv\Scripts\python.exe"
    if (-not (Test-Path $py)) {
        Write-Host "Skip migrations: no backend\.venv" -ForegroundColor DarkGray
        return
    }
    Push-Location (Join-Path $Root "backend")
    try {
        $code = Invoke-External { & $py -m alembic upgrade head }
        if ($code -eq 0) {
            Write-Host "Migrations OK (local venv)" -ForegroundColor Green
        } else {
            Write-Host "Migrations warning (exit $code)" -ForegroundColor Yellow
        }
    } finally {
        Pop-Location
    }
}

function Test-ContainerRunning([string]$Name) {
    $s = docker inspect -f "{{.State.Status}}" $Name 2>$null
    return $s -eq "running"
}

function Start-DockerStack {
    Write-Step "Docker: postgres, redis, minio, backend, celery"
    Invoke-External { docker compose up -d postgres redis minio backend celery-worker-generation } | Out-Null
    # exit code ignored: compose may warn while containers are already up

    $deadline = (Get-Date).AddSeconds(120)
    $healthy = $false
    do {
        if (Test-ContainerRunning "veluna-backend") {
            $h = docker inspect -f "{{.State.Health.Status}}" veluna-backend 2>$null
            if ($h -eq "healthy" -or $h -eq "") { $healthy = $true; break }
        }
        Start-Sleep -Seconds 3
    } while ((Get-Date) -lt $deadline)

    if (-not (Test-ContainerRunning "veluna-backend")) {
        throw "veluna-backend container is not running"
    }

    $mapped = docker port veluna-backend 8000/tcp 2>$null
    if ($mapped -match ':(\d+)->') {
        return [int]$matches[1]
    }
    return 8020
}

function Start-BackendLocal {
    Write-Step "Backend on host (port 8000)"
    Stop-Port 8000 @("python")
    Sync-EnvFiles
    $run = Join-Path $Scripts "run-backend-local.ps1"
    Start-Process powershell.exe -ArgumentList @(
        "-NoExit", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $run
    ) -WindowStyle Normal | Out-Null

    $deadline = (Get-Date).AddSeconds(45)
    do {
        try {
            $r = Invoke-WebRequest "http://127.0.0.1:8000/health" -UseBasicParsing -TimeoutSec 5
            if ($r.StatusCode -eq 200) { return 8000 }
        } catch {}
        Start-Sleep -Seconds 2
    } while ((Get-Date) -lt $deadline)
    throw "Backend on :8000 did not become healthy"
}

function Start-CeleryHost {
    if (Test-DockerOk) {
        $w = docker ps --filter "name=veluna-worker-generation" --format "{{.Status}}" 2>$null
        if ($w -match "Up") {
            Write-Host "Celery generation worker already in Docker." -ForegroundColor DarkGray
            return
        }
    }
    Write-Step "Celery worker (host, generation_queue)"
    $inner = @"
`$host.UI.RawUI.WindowTitle = 'Veluna Celery'
Set-Location '$Root\backend'
Copy-Item '..\.env' '.env' -Force
if (-not (Test-Path '.venv\Scripts\python.exe')) { py -3.12 -m venv .venv; .\.venv\Scripts\pip install -r requirements.txt -q }
.\.venv\Scripts\celery -A app.workers.celery_app worker -Q generation_queue -c 1 --loglevel=info -n generation@host
"@
    Start-Process powershell.exe -ArgumentList "-NoExit", "-NoProfile", "-Command", $inner -WindowStyle Normal | Out-Null
}

function Start-Frontend([int]$BackendPort) {
    Set-FrontendBackendPort $BackendPort
    if ($Dev) {
        Write-Step "Frontend dev (npm run dev) -> backend :$BackendPort"
        Stop-Port 3000 @("node")
        Start-Sleep -Seconds 2
        Start-FrontendProcess $BackendPort "dev"
        Start-Sleep -Seconds 8
        return
    }
    if ($SkipBuild -and (Test-Path (Join-Path $Root "frontend\.next"))) {
        Write-Step "Frontend production (skip build) -> backend :$BackendPort"
        Stop-Port 3000 @("node")
        Start-Sleep -Seconds 2
        Start-FrontendProcess $BackendPort "start"
        Start-Sleep -Seconds 6
    } else {
        $prev = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        try {
            & (Join-Path $Scripts "start-frontend-tunnel.ps1")
            if ($LASTEXITCODE -ne 0 -and $null -ne $LASTEXITCODE) {
                throw "frontend build/start failed (exit $LASTEXITCODE)"
            }
        } finally {
            $ErrorActionPreference = $prev
        }
    }
    try {
        $fe = Invoke-WebRequest "http://127.0.0.1:3000" -UseBasicParsing -TimeoutSec 20
        Write-Host "Frontend OK: $($fe.StatusCode)" -ForegroundColor Green
    } catch {
        Write-Host "Frontend starting... open http://127.0.0.1:3000 in a few seconds" -ForegroundColor Yellow
    }
}

function Test-TelegramApi {
    try {
        $r = Invoke-WebRequest "https://api.telegram.org" -UseBasicParsing -TimeoutSec 12
        return $r.StatusCode -ge 200 -and $r.StatusCode -lt 500
    } catch {
        return $false
    }
}

function Start-Bot {
    Write-Step "Telegram bot (host)"
    if (-not (Test-TelegramApi)) {
        Write-Host ""
        Write-Host "WARNING: api.telegram.org is not reachable from this PC." -ForegroundColor Yellow
        Write-Host "  Bot will retry in its window. Common fixes:" -ForegroundColor Yellow
        Write-Host "    - Turn off VPN or enable split tunnel for Telegram" -ForegroundColor Yellow
        Write-Host "    - Check firewall / antivirus" -ForegroundColor Yellow
        Write-Host "    - Try another network (mobile hotspot)" -ForegroundColor Yellow
        Write-Host "  Mini App still works if you open the tunnel URL in Telegram WebView." -ForegroundColor DarkGray
        Write-Host ""
    }
    Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -match 'app\.bot\.main' } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
    Start-Sleep -Seconds 1
    & (Join-Path $Scripts "run-bot-local.ps1") -Background
}

# --- main ---
Write-Host ""
Write-Host "========================================" -ForegroundColor Magenta
Write-Host "  Veluna - full stack startup" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta
Write-Host ""

Sync-EnvFiles

$backendPort = 8000
$dockerMode = $false

if (-not (Test-DockerOk)) {
    Try-StartDockerDesktop
}

if (Wait-Docker -Minutes 3) {
    try {
        $backendPort = Start-DockerStack
        Invoke-Migrations
        $dockerMode = $true
        Write-Host "Backend via Docker on port $backendPort" -ForegroundColor Green
    } catch {
        Write-Host "Docker compose failed: $_" -ForegroundColor Yellow
    }
}

if (-not $dockerMode) {
    if (-not (Test-TcpPort 5433)) {
        Write-Host ""
        Write-Host "ERROR: Postgres is not on :5433 and Docker is unavailable." -ForegroundColor Red
        Write-Host "Start Docker Desktop, wait until it is ready, then run:" -ForegroundColor Yellow
        Write-Host "  .\scripts\veluna-up.ps1" -ForegroundColor Yellow
        exit 1
    }
    if (-not (Test-TcpPort 6379)) {
        Write-Host "WARNING: Redis port 6379 is down - Celery/cache may fail." -ForegroundColor Yellow
    }
    $backendPort = Start-BackendLocal
    Invoke-Migrations
    Start-CeleryHost
}

Set-FrontendBackendPort $backendPort
Start-Frontend $backendPort

if (-not $SkipTunnel) {
    Write-Step "Pinggy tunnel + Telegram menu URL"
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        & (Join-Path $Scripts "dev-miniapp-up.ps1")
    } finally {
        $ErrorActionPreference = $prev
    }
} else {
    Write-Host "Tunnel skipped (-SkipTunnel). Local: http://127.0.0.1:3000" -ForegroundColor Yellow
}

# set-miniapp-url may rewrite .env.local - restore API proxy port and reload frontend
Set-FrontendBackendPort $backendPort
if (-not $SkipTunnel -and -not $Dev) {
    Write-Host "Reloading frontend (API proxy -> :$backendPort)..." -ForegroundColor Cyan
    Stop-Port 3000 @("node")
    Start-Sleep -Seconds 2
    Start-FrontendProcess $backendPort "start"
    Start-Sleep -Seconds 5
}

Start-Bot

$tunnelUrl = $null
$tunnelFile = Join-Path $Root ".tunnel-url"
if (Test-Path $tunnelFile) {
    $tunnelUrl = (Get-Content $tunnelFile -Raw).Trim()
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Veluna is up" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Frontend:  http://127.0.0.1:3000"
Write-Host "  API proxy: http://127.0.0.1:3000/api/v1  -> 127.0.0.1:$backendPort"
if ($tunnelUrl) {
    Write-Host "  Mini App:  $tunnelUrl" -ForegroundColor Cyan
    Write-Host "  Telegram:  bot -> Open Veluna /start"
    Write-Host "  Pinggy runs in background (logs/pinggy.log)." -ForegroundColor DarkGray
}
Write-Host ""
Write-Host "  Services run in background (no extra CMD windows). Logs: $Root\logs\" -ForegroundColor DarkGray
Write-Host "  To stop host services: .\scripts\stop-veluna-host.ps1" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  Quick restart (no rebuild):" -ForegroundColor DarkGray
Write-Host "    .\scripts\veluna-up.ps1 -SkipBuild"
Write-Host ""
