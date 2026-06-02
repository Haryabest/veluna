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

@(
    "# Single-tunnel (Pinggy): API proxied by Next.js",
    "NEXT_PUBLIC_API_URL=/api/v1",
    "NEXT_PUBLIC_WS_URL=",
    ""
) | Set-Content (Join-Path $Root "frontend\.env.local")

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

Write-Host "Restart frontend if already running: cd frontend; npm run dev"
