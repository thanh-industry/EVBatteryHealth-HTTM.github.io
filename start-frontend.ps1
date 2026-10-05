<#
.SYNOPSIS
    Installs dependencies (if needed) and starts the Vite dev server for the
    EV Battery SoH frontend on http://localhost:5173.

.DESCRIPTION
    - Verifies Node.js (and npm) are on PATH.
    - Warns clearly (does not block) if the Node major version is below 18,
      since this project is pinned to Vite 5 + React 18 for Node 18.17
      compatibility (Next.js 15 needs 18.18+, Vite 7 needs 20+).
    - Runs 'npm install' only when frontend\node_modules is missing, or when
      frontend\package.json is newer than frontend\node_modules.
    - Runs 'npm run dev'.

.NOTES
    Windows PowerShell 5.1. Run from the repo root:
        .\start-frontend.ps1
    If execution policy blocks this script, run:
        powershell -ExecutionPolicy Bypass -File start-frontend.ps1
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
$frontendDir = Join-Path $root "frontend"

Say "== EV Battery SoH frontend launcher =="

if (-not (Test-Path $frontendDir)) {
    Fail "Frontend directory not found at '$frontendDir'."
}

Set-Location $frontendDir

try {
    # 1. Verify Node exists.
    $nodeCmd = Get-Command node -ErrorAction SilentlyContinue
    if (-not $nodeCmd) {
        Fail "Node.js was not found on PATH. Install Node 18+ and re-run this script."
    }
    $npmCmd = Get-Command npm -ErrorAction SilentlyContinue
    if (-not $npmCmd) {
        Fail "npm was not found on PATH (it normally ships with Node.js)."
    }

    $nodeVersionRaw = (& node --version).Trim()
    Say "Found Node $nodeVersionRaw"

    $versionDigits = $nodeVersionRaw.TrimStart("v")
    $majorVersionText = $versionDigits.Split(".")[0]
    $majorVersion = 0
    $parsed = [int]::TryParse($majorVersionText, [ref]$majorVersion)
    if ($parsed -and $majorVersion -lt 18) {
        Write-Host "WARNING: Node major version is $majorVersion, below the 18 this project requires (Vite 5 + React 18 need Node 18+). npm install / npm run dev may fail or misbehave. Upgrade Node before continuing." -ForegroundColor Yellow
    } elseif (-not $parsed) {
        Write-Host "WARNING: could not parse Node version string '$nodeVersionRaw'. Continuing anyway." -ForegroundColor Yellow
    }

    # 2. npm install only when node_modules is missing or package.json is newer.
    $nodeModules = Join-Path $frontendDir "node_modules"
    $packageJson = Join-Path $frontendDir "package.json"
    $needsInstall = $false

    if (-not (Test-Path $nodeModules)) {
        $needsInstall = $true
        Say "node_modules not found - installing dependencies."
    } else {
        $pkgTime = (Get-Item $packageJson).LastWriteTimeUtc
        $modulesTime = (Get-Item $nodeModules).LastWriteTimeUtc
        if ($pkgTime -gt $modulesTime) {
            $needsInstall = $true
            Say "package.json is newer than node_modules - reinstalling dependencies."
        }
    }

    if ($needsInstall) {
        npm install
        if ($LASTEXITCODE -ne 0) {
            Fail "npm install failed (exit code $LASTEXITCODE). See output above."
        }
    } else {
        Say "node_modules is up to date - skipping npm install."
    }

    # 3. Start the Vite dev server. This call blocks until stopped (Ctrl+C).
    Say "Starting Vite dev server on http://localhost:5173 (Ctrl+C to stop) ..."
    npm run dev
    if ($LASTEXITCODE -ne 0) {
        Fail "npm run dev exited with code $LASTEXITCODE. Is port 5173 already in use by another process?"
    }
}
catch {
    Fail $_.Exception.Message
}
