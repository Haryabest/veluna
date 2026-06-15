# Keeps Pinggy tunnel alive: restarts when DNS/HTTP fails (~60 min free TTL).
$ErrorActionPreference = "Continue"
$Root = Split-Path $PSScriptRoot -Parent
$Scripts = $PSScriptRoot
$LogDir = Join-Path $Root "logs"
$WatchLog = Join-Path $LogDir "tunnel-watch.log"

if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

function Write-Watch([string]$Msg) {
    $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $Msg"
    Add-Content -Path $WatchLog -Value $line -Encoding utf8
}

function Get-SavedTunnelUrl {
    $file = Join-Path $Root ".tunnel-url"
    if (Test-Path $file) {
        return (Get-Content $file -Raw -ErrorAction SilentlyContinue).Trim()
    }
    return $null
}

function Test-TunnelAlive([string]$Url) {
    if (-not $Url) { return $false }
    try {
        $tunnelHost = ([Uri]$Url).Host
        Resolve-DnsName $tunnelHost -ErrorAction Stop | Out-Null
    } catch {
        return $false
    }
    try {
        $r = Invoke-WebRequest -Uri $Url -TimeoutSec 15 -UseBasicParsing
        return $r.StatusCode -ge 200 -and $r.StatusCode -lt 500
    } catch {
        return $false
    }
}

function Restart-Tunnel {
    Write-Watch "Restarting Pinggy tunnel..."
    & (Join-Path $Scripts "dev-miniapp-up.ps1") 2>&1 | ForEach-Object { Write-Watch $_ }
    if (Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue) {
        & (Join-Path $Scripts "restart-frontend.ps1") 2>&1 | ForEach-Object { Write-Watch $_ }
    }
    $url = Get-SavedTunnelUrl
    Write-Watch "New URL: $url"
}

$mutex = New-Object System.Threading.Mutex($false, "Global\VelunaTunnelSupervisor")
if (-not $mutex.WaitOne(0, $false)) {
    Write-Watch "Another tunnel supervisor already running, exit."
    exit 0
}

Write-Watch "Tunnel supervisor started (pid $PID)"
Set-Location $Root

$checkSec = 120
while ($true) {
    $url = Get-SavedTunnelUrl
    if (-not (Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue)) {
        Write-Watch "Frontend :3000 down — skip tunnel check"
    } elseif (-not (Test-TunnelAlive $url)) {
        Write-Watch "Tunnel dead ($url)"
        try {
            Restart-Tunnel
        } catch {
            Write-Watch "Restart failed: $_"
        }
    }
    Start-Sleep -Seconds $checkSec
}
