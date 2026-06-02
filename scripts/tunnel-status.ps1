# Quick check: is Pinggy tunnel alive?
$Root = Split-Path $PSScriptRoot -Parent
$url = $null
if (Test-Path (Join-Path $Root ".tunnel-url")) {
    $url = (Get-Content (Join-Path $Root ".tunnel-url") -Raw).Trim()
} elseif (Test-Path (Join-Path $Root ".env")) {
    Get-Content (Join-Path $Root ".env") | ForEach-Object {
        if ($_ -match '^TELEGRAM_WEBAPP_URL=(.+)$') { $url = $matches[1].Trim() }
    }
}

$ssh = Get-CimInstance Win32_Process -Filter "Name='ssh.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -match "pinggy" }

Write-Host "Frontend :3000" (Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue | Measure-Object).Count -gt 0
Write-Host "Pinggy ssh running:" ([bool]$ssh)
Write-Host "Saved URL:" $url

if ($url) {
    try {
        $host = ([Uri]$url).Host
        Resolve-DnsName $host -ErrorAction Stop | Out-Null
        Write-Host "DNS:" $host "OK" -ForegroundColor Green
        try {
            $r = Invoke-WebRequest -Uri $url -TimeoutSec 15 -UseBasicParsing
            Write-Host "HTTP:" $r.StatusCode -ForegroundColor Green
        } catch {
            Write-Host "HTTP: FAIL - tunnel window closed?" -ForegroundColor Red
        }
    } catch {
        Write-Host "DNS: FAIL - tunnel dead. Run: .\scripts\dev-miniapp-up.ps1" -ForegroundColor Red
    }
}
