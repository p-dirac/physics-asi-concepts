<#
.SYNOPSIS
    Installs everything the Pre-1900 Gravity Model Selection demo needs: a
    Python venv with the pinned requirements, the two Ollama models it
    calls, and the frontend's npm dependencies.

.NOTES
    Run from anywhere -- paths are resolved relative to this script's
    location, not the current directory. If script execution is blocked,
    run: powershell -ExecutionPolicy Bypass -File install.ps1
#>

. "$PSScriptRoot\common.ps1"

Write-Host "== Pre-1900 Gravity Model Selection: install ==" -ForegroundColor Cyan

# 1. Python
Write-Host "`n[1/5] Checking Python..." -ForegroundColor Yellow
$pythonCmd = @("python", "python3", "py") | Where-Object { Test-CommandExists $_ } | Select-Object -First 1
if (-not $pythonCmd) {
    Write-Error "Python was not found on PATH. Install Python 3.13 from https://www.python.org/downloads/ and re-run."
    exit 1
}
$pyVersion = & $pythonCmd --version
Write-Host "  Found $pyVersion ($pythonCmd)"

# 2. Virtual environment
Write-Host "`n[2/5] Setting up the virtual environment..." -ForegroundColor Yellow
if (-not (Test-Path $VenvDir)) {
    & $pythonCmd -m venv $VenvDir
    if ($LASTEXITCODE -ne 0) { Write-Error "Failed to create the virtual environment."; exit 1 }
    Write-Host "  Created $VenvDir"
} else {
    Write-Host "  Already exists at $VenvDir"
}

# 3. Python dependencies
Write-Host "`n[3/5] Installing Python dependencies (this can take a few minutes)..." -ForegroundColor Yellow
& $VenvPython -m pip install --upgrade pip --quiet
& $VenvPython -m pip install -r (Join-Path $ProjectRoot "requirements.txt")
if ($LASTEXITCODE -ne 0) { Write-Error "pip install failed -- see output above."; exit 1 }

# 4. Ollama models
Write-Host "`n[4/5] Checking Ollama and pulling models..." -ForegroundColor Yellow
if (-not (Test-CommandExists "ollama")) {
    Write-Warning "Ollama was not found on PATH. Install it from https://ollama.com, then run:"
    Write-Warning "  ollama pull qwen2.5:7b"
    Write-Warning "  ollama pull nomic-embed-text"
    Write-Warning "...and re-run this script (or just those two commands) before using run.ps1."
} else {
    Write-Host "  Pulling qwen2.5:7b (this is a multi-GB download the first time)..."
    ollama pull qwen2.5:7b
    Write-Host "  Pulling nomic-embed-text..."
    ollama pull nomic-embed-text
}

# 5. Frontend dependencies
Write-Host "`n[5/5] Installing frontend dependencies..." -ForegroundColor Yellow
if (-not (Test-CommandExists "npm")) {
    Write-Error "npm was not found on PATH. Install Node.js 18+ from https://nodejs.org/ and re-run."
    exit 1
}
Push-Location $FrontendDir
try {
    npm install
    if ($LASTEXITCODE -ne 0) { Write-Error "npm install failed -- see output above."; exit 1 }
} finally {
    Pop-Location
}

Write-Host "`nDone. Start the app with: .\scripts\run.ps1" -ForegroundColor Green
