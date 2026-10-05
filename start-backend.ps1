<#
.SYNOPSIS
    Sets up and starts the EV Battery SoH FastAPI backend on http://127.0.0.1:8000.

.DESCRIPTION
    - Verifies Python is on PATH.
    - Uses backend\.venv or backend\venv if one already exists (and activates
      it); otherwise uses the system Python interpreter directly, since the
      backend currently ships with no virtual environment and the required
      packages are already installed globally in this environment.
    - Installs backend\requirements.txt (idempotent - safe to re-run).
    - Runs the DB seed (python -m app.seed) only if backend\data\app.db does
      not exist yet. app\seed.py is itself idempotent, so running it again
      manually is also safe.
    - Starts uvicorn on port 8000.

.NOTES
    Windows PowerShell 5.1. Run from the repo root:
        .\start-backend.ps1
    If execution policy blocks this script, run:
        powershell -ExecutionPolicy Bypass -File start-backend.ps1
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
$backendDir = Join-Path $root "backend"

Say "== EV Battery SoH backend launcher =="

if (-not (Test-Path $backendDir)) {
    Fail "Backend directory not found at '$backendDir'."
}

Set-Location $backendDir

try {
    # 1. Verify Python exists. Try 'python' first, then the 'py' launcher.
    $pythonCmd = $null
    foreach ($candidate in @("python", "py")) {
        $found = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($found) {
            $pythonCmd = $candidate
            break
        }
    }
    if (-not $pythonCmd) {
        Fail "Python was not found on PATH ('python' and 'py' both failed). Install Python 3.11+ and re-run this script."
    }
    $pyVersionOutput = & $pythonCmd --version
    Say "Using '$pythonCmd' ($pyVersionOutput)"

    # 2. Venv detection. This project does not currently ship a venv (no
    # backend\.venv or backend\venv folder) - the required packages
    # (pandas, scikit-learn, numpy, FastAPI, ...) are already installed into
    # the system Python. If a venv appears later, prefer and activate it
    # automatically instead of assuming either way.
    $venvDir = $null
    foreach ($candidate in @(".venv", "venv")) {
        $candidatePath = Join-Path $backendDir $candidate
        $candidatePython = Join-Path $candidatePath "Scripts\python.exe"
        if (Test-Path $candidatePython) {
            $venvDir = $candidatePath
            break
        }
    }

    if ($venvDir) {
        Say "Found existing virtual environment at '$venvDir' - activating it."
        $activateScript = Join-Path $venvDir "Scripts\Activate.ps1"
        if (-not (Test-Path $activateScript)) {
            Fail "Found a venv at '$venvDir' but its Scripts\Activate.ps1 is missing or corrupt. Delete the folder and re-run."
        }
        . $activateScript
        $pythonExe = Join-Path $venvDir "Scripts\python.exe"
    } else {
        Say "No backend\.venv or backend\venv found. Using the system '$pythonCmd' interpreter directly."
        $pythonExe = $pythonCmd
    }

    # 3. Install dependencies. pip skips packages that are already
    # satisfied, so this is safe to re-run every time.
    Say "Installing backend\requirements.txt ..."
    & $pythonExe -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Fail "pip install failed (exit code $LASTEXITCODE). See output above."
    }

    # 4. Seed the database if it does not exist yet.
    $dbPath = Join-Path $backendDir "data\app.db"
    if (-not (Test-Path $dbPath)) {
        Say "No database found at '$dbPath' - running the seed script (python -m app.seed) ..."
        & $pythonExe -m app.seed
        if ($LASTEXITCODE -ne 0) {
            Fail "Database seed failed (exit code $LASTEXITCODE). See output above."
        }
    } else {
        Say "Database already exists at '$dbPath' - skipping seed."
        Say "(To force a reseed, delete that file and re-run this script, or run 'python -m app.seed' manually - it is idempotent.)"
    }

    # 5. Start uvicorn. This call blocks until the server is stopped (Ctrl+C).
    Say "Starting uvicorn on http://127.0.0.1:8000 (Ctrl+C to stop) ..."
    & $pythonExe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
    if ($LASTEXITCODE -ne 0) {
        Fail "uvicorn exited with code $LASTEXITCODE. Is port 8000 already in use by another process?"
    }
}
catch {
    Fail $_.Exception.Message
}
