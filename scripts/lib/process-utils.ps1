# Shared helpers: stop Veluna host processes and start services without extra CMD windows.

function Stop-VelunaHostServices {
    param(
        [switch]$KeepTunnel
    )

    foreach ($port in 3000, 3001, 8000, 8010, 8011) {
        Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
            ForEach-Object {
                $proc = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue
                if ($proc -and $proc.ProcessName -in @("node", "python")) {
                    Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
                }
            }
    }

    Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -match 'app\.bot\.main|uvicorn app\.main|celery.*app\.workers' } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

    Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -match 'watch-bot\.ps1' } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

    Get-CimInstance Win32_Process -Filter "Name='celery.exe'" -ErrorAction SilentlyContinue |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

    if (-not $KeepTunnel) {
        Get-CimInstance Win32_Process -Filter "Name='ssh.exe'" -ErrorAction SilentlyContinue |
            Where-Object { $_.CommandLine -match 'pinggy' } |
            ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
    }

    Start-Sleep -Seconds 1
    Stop-VelunaShellWindows
}

function Stop-VelunaShellWindows {
    Get-Process -Name powershell, pwsh, cmd -ErrorAction SilentlyContinue |
        Where-Object {
            $t = $_.MainWindowTitle
            $t -and $t -match 'Veluna'
        } |
        ForEach-Object {
            Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
        }

    Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -match 'Veluna Pinggy|Veluna Celery|Veluna Bot' } |
        ForEach-Object {
            Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        }
}

function Ensure-LogDir([string]$Root) {
    $dir = Join-Path $Root "logs"
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    return $dir
}

function Resolve-NodeExe {
    foreach ($path in @(
            "${env:ProgramFiles}\nodejs\node.exe",
            "${env:ProgramFiles(x86)}\nodejs\node.exe"
        )) {
        if (Test-Path $path) { return $path }
    }

    $node = Get-Command node -ErrorAction SilentlyContinue
    if ($node -and $node.Source -notmatch 'cursor|brackets') {
        return $node.Source
    }

    throw "Node.js not found. Install from https://nodejs.org or add it to PATH before Cursor's bundled node."
}

function Get-NpmLaunch {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$NpmArgs
    )

    $node = Resolve-NodeExe
    $nodeDir = Split-Path $node -Parent
    $npmCli = Join-Path $nodeDir "node_modules\npm\bin\npm-cli.js"
    if (Test-Path $npmCli) {
        return @{
            FilePath     = $node
            ArgumentList = @($npmCli) + $NpmArgs
        }
    }

    $npmCmd = Join-Path $nodeDir "npm.cmd"
    if (Test-Path $npmCmd) {
        return @{
            FilePath     = $npmCmd
            ArgumentList = $NpmArgs
        }
    }

    throw "npm not found next to node at $nodeDir"
}

function Start-FrontendHidden {
    param(
        [string]$WorkingDirectory,
        [string]$Root,
        [int]$BackendPort = 8020
    )

    $prep = Join-Path $WorkingDirectory "scripts\prepare-standalone.ps1"
    if (Test-Path $prep) {
        & $prep
    }

    $node = Resolve-NodeExe
    $standaloneDir = Join-Path $WorkingDirectory ".next\standalone"
    $serverJs = Join-Path $standaloneDir "server.js"
    if (-not (Test-Path $serverJs)) {
        throw "Missing $serverJs - run npm run build in frontend/"
    }

    $env:BACKEND_PORT = "$BackendPort"
    $env:PORT = "3000"
    $env:HOSTNAME = "0.0.0.0"
    return Start-HiddenProcess -FilePath $node -ArgumentList @("server.js") `
        -WorkingDirectory $standaloneDir -LogBaseName "frontend" -Root $Root
}

function Start-NpmHidden {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$NpmArgs,
        [string]$WorkingDirectory,
        [string]$LogBaseName,
        [string]$Root
    )

    $node = Resolve-NodeExe
    $nodeDir = Split-Path $node -Parent
    $npmCmd = Join-Path $nodeDir "npm.cmd"
    if (-not (Test-Path $npmCmd)) {
        throw "npm.cmd not found at $npmCmd"
    }

    $npmLine = "`"$npmCmd`" " + ($NpmArgs -join " ")
    return Start-HiddenProcess -FilePath "cmd.exe" -ArgumentList @("/c", $npmLine) `
        -WorkingDirectory $WorkingDirectory -LogBaseName $LogBaseName -Root $Root
}

function Start-HiddenProcess {
    param(
        [string]$FilePath,
        [string[]]$ArgumentList,
        [string]$WorkingDirectory,
        [string]$LogBaseName,
        [string]$Root
    )

    $logDir = Ensure-LogDir $Root
    $outLog = Join-Path $logDir "$LogBaseName.log"
    $errLog = Join-Path $logDir "$LogBaseName.err.log"

    $proc = Start-Process -FilePath $FilePath `
        -ArgumentList $ArgumentList `
        -WorkingDirectory $WorkingDirectory `
        -WindowStyle Hidden `
        -PassThru `
        -RedirectStandardOutput $outLog `
        -RedirectStandardError $errLog

    return $proc
}
