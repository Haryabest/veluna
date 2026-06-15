param(
    [Parameter(Mandatory)][string]$Url,
    [switch]$SkipMenuButton
)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$Url = $Url.TrimEnd("/")

if ($Url -notmatch "^https://") { throw "URL must start with https://" }

foreach ($f in @(".env", "backend\.env")) {
    $p = Join-Path $Root $f
    if (-not (Test-Path $p)) { continue }
    $c = Get-Content $p -Raw
    $c = $c -replace 'TELEGRAM_WEBAPP_URL=https://[^\r\n]+', "TELEGRAM_WEBAPP_URL=$Url"
    if ($c -match 'CORS_ORIGINS=') {
        $c = $c -replace 'CORS_ORIGINS=.*', "CORS_ORIGINS=http://localhost:3000,$Url"
    }
    Set-Content -Path $p -Value $c.TrimEnd()
    Add-Content -Path $p -Value ""
}

$envLocal = Join-Path $Root "frontend\.env.local"
$backendPort = "8010"

function Test-BackendHealthy([string]$Port) {
    try {
        $health = Invoke-WebRequest "http://127.0.0.1:$Port/health" -UseBasicParsing -TimeoutSec 3
        if ($health.StatusCode -ne 200) { return $false }
        $chars = Invoke-WebRequest "http://127.0.0.1:$Port/api/v1/characters" -UseBasicParsing -TimeoutSec 5
        return $chars.StatusCode -eq 200
    } catch {
        return $false
    }
}

# Host-only Veluna uses :8010 (avoids zombie listeners on :8000 from uvicorn --reload).
$dockerPort = $null
try {
    docker info 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $running = docker inspect -f "{{.State.Status}}" veluna-backend 2>$null
        if ($running -eq "running") {
            $mapped = docker port veluna-backend 8000/tcp 2>$null
            if ($mapped -match ':(\d+)->') {
                $dockerPort = $matches[1]
            } else {
                $dockerPort = "8020"
            }
        }
    }
} catch {}

if (Test-BackendHealthy "8010") {
    $backendPort = "8010"
} elseif ($dockerPort -and (Test-BackendHealthy $dockerPort)) {
    $backendPort = $dockerPort
} elseif (Test-BackendHealthy "8000") {
    $backendPort = "8000"
} else {
    $rootEnv = Join-Path $Root ".env"
    if (Test-Path $rootEnv) {
        Get-Content $rootEnv | ForEach-Object {
            if ($_ -match '^BACKEND_PORT=(.+)$') { $backendPort = $matches[1].Trim() }
        }
    }
}
@(
    "# Single-tunnel (Pinggy): API proxied by Next.js",
    "NEXT_PUBLIC_API_URL=/api/v1",
    "NEXT_PUBLIC_WS_URL=",
    "BACKEND_HOST=127.0.0.1",
    "BACKEND_PORT=$backendPort",
    ""
) | Set-Content $envLocal

Set-Content -Path (Join-Path $Root ".tunnel-url") -Value $Url

Write-Host "Updated: .env, backend/.env, frontend/.env.local" -ForegroundColor Green
Write-Host "TELEGRAM_WEBAPP_URL=$Url"

if (-not $SkipMenuButton) {
    $token = $null
    Get-Content (Join-Path $Root ".env") | ForEach-Object {
        if ($_ -match '^TELEGRAM_BOT_TOKEN=(.+)$') { $token = $matches[1].Trim() }
    }
    if ($token) {
        $body = @{
            menu_button = @{
                type    = "web_app"
                text    = "Open Veluna"
                web_app = @{ url = $Url }
            }
        }
        $jsonBody = $body | ConvertTo-Json -Depth 5 -Compress
        $utf8Body = [System.Text.Encoding]::UTF8.GetBytes($jsonBody)
        try {
            Invoke-RestMethod -Uri "https://api.telegram.org/bot$token/setChatMenuButton" `
                -Method Post -ContentType "application/json; charset=utf-8" -Body $utf8Body | Out-Null
            Write-Host "Telegram Menu Button updated automatically." -ForegroundColor Green
        } catch {
            Write-Warning "Could not set Menu Button via API: $_"
            Write-Host "Set manually in BotFather or restart bot: .\scripts\run-bot-local.ps1"
        }
    }
}

Write-Host "BACKEND_PORT=$backendPort in frontend/.env.local" -ForegroundColor Green
Write-Host "Restart frontend (required after port change): stop :3000, then npm run dev or npm run start" -ForegroundColor Yellow
