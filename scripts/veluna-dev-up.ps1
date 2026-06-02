# Full local dev bootstrap: tunnels + .env sync + service hints
$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

$cf = "${env:ProgramFiles(x86)}\cloudflared\cloudflared.exe"
if (-not (Test-Path $cf)) { $cf = "$env:ProgramFiles\Cloudflare\cloudflared\cloudflared.exe" }
if (-not (Test-Path $cf)) { throw "cloudflared not found. Run: winget install Cloudflare.cloudflared" }

function Get-TunnelUrl($logPath, $timeoutSec = 90) {
    $deadline = (Get-Date).AddSeconds($timeoutSec)
    while ((Get-Date) -lt $deadline) {
        if (Test-Path $logPath) {
            $m = Select-String -Path $logPath -Pattern "https://[a-z0-9-]+\.trycloudflare\.com" -AllMatches |
                ForEach-Object { $_.Matches } | Select-Object -Last 1
            if ($m) { return $m.Value }
        }
        Start-Sleep 2
    }
    return $null
}

function Set-EnvUrls($frontUrl, $backUrl) {
    $files = @(
        (Join-Path $Root ".env"),
        (Join-Path $Root "backend\.env")
    )
    foreach ($f in $files) {
        if (-not (Test-Path $f)) { continue }
        $c = Get-Content $f -Raw
        $c = $c -replace 'NEXT_PUBLIC_API_URL=https://[^\r\n]+', "NEXT_PUBLIC_API_URL=$backUrl/api/v1"
        $c = $c -replace 'NEXT_PUBLIC_WS_URL=wss://[^\r\n]+', "NEXT_PUBLIC_WS_URL=$($backUrl -replace '^https','wss')/ws"
        $c = $c -replace 'TELEGRAM_WEBAPP_URL=https://[^\r\n]+', "TELEGRAM_WEBAPP_URL=$frontUrl"
        if ($c -match 'CORS_ORIGINS=') {
            $c = $c -replace 'CORS_ORIGINS=.*', "CORS_ORIGINS=http://localhost:3000,$frontUrl"
        }
        Set-Content -Path $f -Value $c.TrimEnd() -NoNewline
        Add-Content -Path $f -Value ""
    }
    $local = Join-Path $Root "frontend\.env.local"
    @(
        "NEXT_PUBLIC_API_URL=$backUrl/api/v1",
        "NEXT_PUBLIC_WS_URL=$($backUrl -replace '^https','wss')/ws",
        ""
    ) | Set-Content $local
    Write-Host "Updated: .env, backend/.env, frontend/.env.local"
}

Get-Process cloudflared -ErrorAction SilentlyContinue | Stop-Process -Force
$frontLog = Join-Path $Root ".cf-front-live.err"
$backLog = Join-Path $Root ".cf-back-live.err"
Remove-Item $frontLog, $backLog -Force -ErrorAction SilentlyContinue

$backendPort = 8002
if (-not (Get-NetTCPConnection -LocalPort $backendPort -State Listen -ErrorAction SilentlyContinue)) {
    Write-Host "Start backend in another terminal:"
    Write-Host "  cd backend; .\.venv\Scripts\uvicorn app.main:app --reload --host 0.0.0.0 --port $backendPort"
}

Write-Host "Starting Cloudflare tunnels (keep windows open)..."
Start-Process $cf -ArgumentList "tunnel","--protocol","http2","--url","http://127.0.0.1:3000" `
    -RedirectStandardError $frontLog -WindowStyle Minimized
Start-Process $cf -ArgumentList "tunnel","--protocol","http2","--url","http://127.0.0.1:$backendPort" `
    -RedirectStandardError $backLog -WindowStyle Minimized

$frontUrl = Get-TunnelUrl $frontLog
$backUrl = Get-TunnelUrl $backLog
if (-not $frontUrl -or -not $backUrl) {
    Write-Warning "Cloudflare edge blocked (VPN?). Falling back to localtunnel..."
    Get-Process cloudflared -ErrorAction SilentlyContinue | Stop-Process -Force
    $ltFront = Start-Process "npx" -ArgumentList "--yes","localtunnel","--port","3000" -PassThru -WindowStyle Hidden -RedirectStandardOutput (Join-Path $Root ".lt-front.log")
    $ltBack = Start-Process "npx" -ArgumentList "--yes","localtunnel","--port",$backendPort -PassThru -WindowStyle Hidden -RedirectStandardOutput (Join-Path $Root ".lt-back.log")
    Start-Sleep 12
    $frontUrl = (Get-Content (Join-Path $Root ".lt-front.log") -ErrorAction SilentlyContinue | Select-String "https://.*\.loca\.lt").Matches.Value
    $backUrl = (Get-Content (Join-Path $Root ".lt-back.log") -ErrorAction SilentlyContinue | Select-String "https://.*\.loca\.lt").Matches.Value
    if (-not $frontUrl -or -not $backUrl) {
        Write-Warning "Tunnel failed. Disable FlClashX or use ngrok."
        exit 1
    }
}

Write-Host "Frontend: $frontUrl"
Write-Host "Backend:  $backUrl"
Set-EnvUrls $frontUrl $backUrl
Write-Host "Done. Restart: npm run dev (frontend), python -m app.bot.main (bot)"
