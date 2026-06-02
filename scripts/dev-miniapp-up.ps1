# Pinggy single tunnel for Telegram Mini App
param([string]$Url)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

function Stop-Pinggy {
    Get-CimInstance Win32_Process -Filter "Name='ssh.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -match "pinggy" } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
}

function Strip-Ansi([string]$Text) {
    if (-not $Text) { return "" }
    return [regex]::Replace($Text, "\x1B\[[0-9;?]*[ -/]*[@-~]", "")
}

function Find-PinggyUrl([string]$Text) {
    $Text = Strip-Ansi $Text
    if (-not $Text) { return $null }
    foreach ($m in [regex]::Matches($Text, "https?://[^\s""'\[\]()<>]+")) {
        $u = $m.Value.TrimEnd('/.,;')
        if ($u -match "dashboard\.pinggy\.io|pinggy\.io/docs") { continue }
        if ($u -match "pinggy-free\.link|\.pinggy\.online|free\.pinggy") {
            return ($u -replace '^http://', 'https://')
        }
    }
    return $null
}

function Test-TunnelAlive($tunnelUrl) {
    try {
        $h = ([Uri]$tunnelUrl).Host
        Resolve-DnsName $h -ErrorAction Stop | Out-Null
        return $true
    } catch { return $false }
}

function Ensure-SshKey {
    $key = Join-Path $env:USERPROFILE ".ssh\id_rsa"
    if (-not (Test-Path $key)) {
        Write-Host "Creating SSH key..."
        New-Item -ItemType Directory -Force -Path (Split-Path $key) | Out-Null
        ssh-keygen -t rsa -b 4096 -N '""' -f $key -q
    }
}

if (-not (Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue)) {
    throw "Frontend not on :3000. Run first: cd frontend; npm run dev"
}

if ($Url) {
    & (Join-Path $PSScriptRoot "set-miniapp-url.ps1") -Url $Url
    Write-Host "Mini App URL: $Url" -ForegroundColor Cyan
    exit 0
}

$existing = $null
$tunnelFile = Join-Path $Root ".tunnel-url"
if (Test-Path $tunnelFile) {
    $existing = (Get-Content $tunnelFile -Raw).Trim()
}
$sshRunning = Get-CimInstance Win32_Process -Filter "Name='ssh.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -match "pinggy" }
if ($existing -and $sshRunning -and (Test-TunnelAlive $existing)) {
    Write-Host "Tunnel already running: $existing" -ForegroundColor Green
    & (Join-Path $PSScriptRoot "set-miniapp-url.ps1") -Url $existing
    exit 0
}

Ensure-SshKey
Stop-Pinggy
$log = Join-Path $Root ".pinggy.log"
Remove-Item $log -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "=== Pinggy tunnel ===" -ForegroundColor Cyan
Write-Host "1. A NEW PowerShell window will open (check the taskbar: 'Veluna Pinggy')." -ForegroundColor Yellow
Write-Host "2. In that window: if 'password' is asked -> press ENTER (empty)." -ForegroundColor Yellow
Write-Host "3. Wait for https://....pinggy-free.link in that window." -ForegroundColor Yellow
Write-Host "4. Keep that window OPEN while using the Mini App." -ForegroundColor Yellow
Write-Host ""

$sshArgs = @(
    "-p", "443", "-T",
    "-R0:127.0.0.1:3000",
    "-o", "StrictHostKeyChecking=no",
    "-o", "ServerAliveInterval=30",
    "-o", "ServerAliveCountMax=3",
    "free.pinggy.io"
)

$logEscaped = $log.Replace("'", "''")
$inner = @"
`$host.UI.RawUI.WindowTitle = 'Veluna Pinggy'
Write-Host '=== Veluna Pinggy ===' -ForegroundColor Cyan
Write-Host 'Password? Press ENTER (leave empty).' -ForegroundColor Yellow
Write-Host ''
ssh -p 443 -T -R0:127.0.0.1:3000 -o StrictHostKeyChecking=no -o ServerAliveInterval=30 -o ServerAliveCountMax=3 free.pinggy.io 2>&1 | ForEach-Object {
  Write-Host `$_
  Add-Content -LiteralPath '$logEscaped' -Value `$_ -Encoding utf8 -ErrorAction SilentlyContinue
}
Write-Host ''
Write-Host 'Tunnel stopped or disconnected.' -ForegroundColor Red
Read-Host 'Press Enter to close'
"@

try {
    Start-Process -FilePath "powershell.exe" `
        -ArgumentList "-NoExit", "-NoProfile", "-Command", $inner `
        -WindowStyle Normal | Out-Null
    Write-Host "Pinggy window started." -ForegroundColor Green
} catch {
    throw "Could not open Pinggy window: $_`nRun manually: ssh -p 443 -T -R0:127.0.0.1:3000 free.pinggy.io"
}

$found = $null
$deadline = (Get-Date).AddSeconds(90)
$waited = 0
while ((Get-Date) -lt $deadline -and -not $found) {
    if (Test-Path $log) {
        $found = Find-PinggyUrl (Get-Content $log -Raw -Encoding utf8 -ErrorAction SilentlyContinue)
    }
    if (-not $found) {
        Start-Sleep 2
        $waited += 2
        if ($waited % 10 -eq 0) {
            Write-Host "  Waiting for URL... ${waited}s / 90s (see 'Veluna Pinggy' window)" -ForegroundColor DarkGray
        }
    }
}

if (-not $found) {
    Write-Host ""
    Write-Host "URL not detected automatically." -ForegroundColor Yellow
    Write-Host "Copy https://....pinggy-free.link from the 'Veluna Pinggy' window." -ForegroundColor Yellow
    Write-Host "Or run: .\scripts\dev-miniapp-up.ps1 -Url https://YOUR-URL.pinggy-free.link"
    Write-Host ""
    $manual = Read-Host "Paste URL here (Enter to cancel)"
    if (-not $manual) { throw "Cancelled. Start tunnel in Pinggy window, then pass -Url." }
    $found = Find-PinggyUrl $manual
    if (-not $found) { $found = $manual.Trim().TrimEnd("/") }
    if ($found -notmatch "^https://") { $found = "https://" + $found.TrimStart("http://") }
}

& (Join-Path $PSScriptRoot "set-miniapp-url.ps1") -Url $found
Write-Host ""
Write-Host "Mini App URL: $found" -ForegroundColor Green
Write-Host "Keep the 'Veluna Pinggy' window OPEN. Open the bot -> menu button." -ForegroundColor Cyan
