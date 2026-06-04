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
$backendPort = "8000"
$dockerBackend = $false
# Docker backend maps container :8000 -> host :8020 (ignore stale BACKEND_PORT in .env)
try {
    docker info 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $running = docker inspect -f "{{.State.Status}}" veluna-backend 2>$null
        if ($running -eq "running") {
            $dockerBackend = $true
            $mapped = docker port veluna-backend 8000/tcp 2>$null
            if ($mapped -match ':(\d+)->') {
                $backendPort = $matches[1]
            } else {
                $backendPort = "8020"
            }
        }
    }
} catch {}
if (-not $dockerBackend) {
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
                text    = "Открыть Veluna"
                web_app = @{ url = $Url }
            }
        } | ConvertTo-Json -Depth 5 -Compress
        try {
            Invoke-RestMethod -Uri "https://api.telegram.org/bot$token/setChatMenuButton" `
                -Method Post -ContentType "application/json; charset=utf-8" -Body $body | Out-Null
            Write-Host "Telegram Menu Button updated automatically." -ForegroundColor Green
        } catch {
            Write-Warning "Could not set Menu Button via API: $_"
            Write-Host "Set manually in BotFather or restart bot: .\scripts\run-bot-local.ps1"
        }
    }
}

Write-Host "BACKEND_PORT=$backendPort in frontend/.env.local" -ForegroundColor Green
Write-Host "Restart frontend (required after port change): stop :3000, then npm run dev or npm run start" -ForegroundColor Yellow
