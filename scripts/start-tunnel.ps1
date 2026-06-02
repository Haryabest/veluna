# HTTPS tunnel to local nginx:80 for Telegram Mini App (no Serveo warning page).
# URL changes each run — update .env and rebuild frontend after restart.
#
# Optional: set NGROK_AUTHTOKEN in .env and use ngrok instead (stable domain on paid plan).

param(
    [ValidateSet("localhost.run", "ngrok", "serveo")]
    [string]$Provider = "localhost.run"
)

switch ($Provider) {
    "ngrok" {
        $token = $env:NGROK_AUTHTOKEN
        if (-not $token) {
            $envFile = Join-Path (Split-Path $PSScriptRoot -Parent) ".env"
            if (Test-Path $envFile) {
                Get-Content $envFile | ForEach-Object {
                    if ($_ -match '^NGROK_AUTHTOKEN=(.+)$') { $token = $matches[1].Trim() }
                }
            }
        }
        if (-not $token) {
            Write-Error "Set NGROK_AUTHTOKEN in .env — get it from https://dashboard.ngrok.com/get-started/your-authtoken"
            exit 1
        }
        ngrok config add-authtoken $token
        Write-Host "Starting ngrok http 80 — copy https URL to .env"
        ngrok http 80
    }
    "serveo" {
        Write-Host "Serveo shows a browser warning on free tunnels (bad for Mini App)."
        ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -R 80:127.0.0.1:80 serveo.net
    }
    default {
        Write-Host "Starting localhost.run -> http://127.0.0.1:80"
        Write-Host "Copy the https://....lhr.life URL into .env then:"
        Write-Host "  docker compose up -d --build frontend telegram-bot backend"
        ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -R 80:127.0.0.1:80 nokey@localhost.run
    }
}
