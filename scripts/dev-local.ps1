# Veluna local dev: infra in Docker + backend/frontend/tunnels on host
# Usage: .\scripts\dev-local.ps1

$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

Write-Host "1. Infra (postgres, redis, minio)..."
docker compose up postgres redis minio -d

Write-Host "2. Cloudflare tunnels (Docker)..."
docker rm -f veluna-cf-front veluna-cf-back 2>$null
docker run -d --name veluna-cf-front cloudflare/cloudflared:latest tunnel --protocol http2 --url http://host.docker.internal:3000 | Out-Null
docker run -d --name veluna-cf-back cloudflare/cloudflared:latest tunnel --protocol http2 --url http://host.docker.internal:8000 | Out-Null
Start-Sleep -Seconds 12
$front = (docker logs veluna-cf-front 2>&1 | Select-String -Pattern "https://[a-z0-9-]+\.trycloudflare\.com" | Select-Object -Last 1).Matches.Value
$back = (docker logs veluna-cf-back 2>&1 | Select-String -Pattern "https://[a-z0-9-]+\.trycloudflare\.com" | Select-Object -Last 1).Matches.Value
Write-Host "Frontend tunnel: $front"
Write-Host "Backend tunnel:  $back"
Write-Host "Update frontend/.env.local and .env with these URLs, then run backend + frontend in separate terminals."
