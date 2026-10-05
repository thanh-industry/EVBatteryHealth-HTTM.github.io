<#
.SYNOPSIS
    Starts the full EV Battery SoH stack: backend in a separate PowerShell
    window, then the frontend in this window once the backend is confirmed up.

.DESCRIPTION
    - Launches start-backend.ps1 in a new PowerShell window.
    - Polls GET http://127.0.0.1:8000/api/config/thresholds until it responds
      with HTTP 200, or until a timeout is reached. Does not blindly sleep.
    - On success, runs start-frontend.ps1 in this window (so its logs and
      Ctrl+C are in the terminal you launched start-all.ps1 from).
    - On failure to reach the backend in time, prints a clear error and
      exits non-zero; the backend window is left open so its output can be
      inspected.

.NOTES
    Windows PowerShell 5.1. Run from the repo root:
        .\start-all.ps1
    If execution policy blocks this script, run:
        powershell -ExecutionPolicy Bypass -File start-all.ps1
#>

$ErrorActionPreference = "Stop"

function Fail {
    param([string]$Message)
    Write-Host "ERROR: $Message" -ForegroundColor Red
    exit 1
}

function Say {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Cyan
}

$root = $PSScriptRoot
$backendScript = Join-Path $root "start-backend.ps1"
$frontendScript = Join-Path $root "start-frontend.ps1"
$healthUrl = "http://127.0.0.1:8000/api/config/thresholds"
$timeoutSeconds = 90
$pollIntervalSeconds = 2

Say "== EV Battery SoH: start-all =="

if (-not (Test-Path $backendScript)) {
    Fail "Cannot find '$backendScript'."
}
if (-not (Test-Path $frontendScript)) {
    Fail "Cannot find '$frontendScript'."
}

try {
    Say "Launching backend in a new PowerShell window ..."
    Start-Process -FilePath "powershell.exe" -ArgumentList @(
        "-NoExit",
        "-ExecutionPolicy", "Bypass",
        "-File", "`"$backendScript`""
    ) | Out-Null

    Say "Waiting for the backend to respond at $healthUrl (timeout ${timeoutSeconds}s) ..."
    $elapsed = 0
    $ready = $false
    while ($elapsed -lt $timeoutSeconds) {
        try {
            $response = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 5
            if ($response.StatusCode -eq 200) {
                $ready = $true
                break
            }
        }
        catch {
            # Backend not reachable yet (still installing deps, seeding the
            # DB, booting uvicorn, or port in use) - keep polling until the
            # timeout instead of failing on the first attempt.
        }
        Start-Sleep -Seconds $pollIntervalSeconds
        $elapsed += $pollIntervalSeconds
        Say "  ... still waiting ($elapsed/${timeoutSeconds}s)"
    }

    if (-not $ready) {
        Fail "Backend did not respond at $healthUrl within $timeoutSeconds seconds. Check the backend PowerShell window for errors (missing Python, failed 'pip install', failed seed, or port 8000 already in use)."
    }

    Say "Backend is up."
    Say "Starting frontend in this window (Ctrl+C to stop) ..."
    & $frontendScript
    if ($LASTEXITCODE -ne 0) {
        Fail "Frontend launcher exited with code $LASTEXITCODE."
    }
}
catch {
    Fail $_.Exception.Message
}
