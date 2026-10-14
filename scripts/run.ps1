<#
.SYNOPSIS
    Starts Ollama (if not already running), the FastAPI backend, and the
    Vite frontend dev server, then opens the app in your default browser.
    All three run detached in the background -- use stop.ps1 to stop them.

.NOTES
    Run from anywhere. If script execution is blocked, run:
    powershell -ExecutionPolicy Bypass -File run.ps1
#>

. "$PSScriptRoot\common.ps1"
Reset-RunLogs

$BackendUrl  = "http://localhost:8001"
$FrontendUrl = "http://localhost:5174"

Write-Host "== Pre-1900 Gravity Model Selection: run ==" -ForegroundColor Cyan

# Children launched below only redirect stdout/stderr. Without stdin
# redirected too, a hidden console child on Windows doesn't get a console
# of its own and instead shares the input buffer of THIS window -- if the
# child touches console input modes on startup (Node/Vite in particular),
# it can leave this window's keyboard input dead even though nothing has
# crashed. Redirecting stdin fully detaches each child.
#
# Start-Process -RedirectStandardInput needs an existing file to read
# from -- it won't accept a device name like "NUL" or "/dev/null"
# directly (PowerShell resolves it as a relative filename first, which
# fails with FileNotFoundException since no such file exists). So we
# create a real, permanently-empty file once and point every child at
# that; reading from an empty file behaves the same as reading from the
# null device -- it reports EOF immediately. On non-Windows the actual
# null device also happens to work fine as a plain path, but using the
# same empty-file trick everywhere keeps this one code path for both.
New-RunDir
$NullDevice = Join-Path $RunDir "empty.stdin"
if (-not (Test-Path $NullDevice)) {
    New-Item -ItemType File -Path $NullDevice -Force | Out-Null
}

if (-not (Test-Path $VenvPython)) {
    Write-Error "Virtual environment not found. Run .\scripts\install.ps1 first."
    exit 1
}

# --- Ollama --------------------------------------------------------------
Write-Host "`n[1/3] Ollama..." -ForegroundColor Yellow
if (Test-PortOpen -Url "http://localhost:11434") {
    Write-Host "  Already running -- leaving it alone."
} elseif (Test-CommandExists "ollama") {
    Write-Host "  Not running -- starting 'ollama serve' in the background..."
    $ollamaArgs = @{
        FilePath               = "ollama"
        ArgumentList            = "serve"
        RedirectStandardOutput  = (Join-Path $RunDir "logs\ollama.out.log")
        RedirectStandardError   = (Join-Path $RunDir "logs\ollama.err.log")
        RedirectStandardInput   = $NullDevice
        PassThru                = $true
    }
    if ($OnWindows) { $ollamaArgs.WindowStyle = "Hidden" }
    $ollamaProc = Start-Process @ollamaArgs
    Save-ProcessId -Name "ollama" -ProcessId $ollamaProc.Id
    if (-not (Wait-ForPort -Url "http://localhost:11434" -TimeoutSec 20)) {
        Write-Warning "  Ollama didn't come up within 20s -- check .run/logs/ollama.err.log"
    } else {
        Write-Host "  Started (PID $($ollamaProc.Id))."
    }
} else {
    Write-Warning "  Ollama not found on PATH and not already running. Install it from https://ollama.com."
}

# --- Backend ---------------------------------------------------------------
Write-Host "`n[2/3] Backend (FastAPI)..." -ForegroundColor Yellow
$backendArgs = @{
    FilePath               = $VenvPython
    ArgumentList            = @("-m", "uvicorn", "backend.main:app", "--port", "8001")
    WorkingDirectory        = $ProjectRoot
    RedirectStandardOutput  = (Join-Path $RunDir "logs\backend.out.log")
    RedirectStandardError   = (Join-Path $RunDir "logs\backend.err.log")
    RedirectStandardInput   = $NullDevice
    PassThru                = $true
}
if ($OnWindows) { $backendArgs.WindowStyle = "Hidden" }
$backendProc = Start-Process @backendArgs
Save-ProcessId -Name "backend" -ProcessId $backendProc.Id
if (Wait-ForPort -Url "$BackendUrl/api/health" -TimeoutSec 30) {
    Write-Host "  Up at $BackendUrl (PID $($backendProc.Id))."
} else {
    Write-Warning "  Backend didn't respond within 20s -- check .run/logs/backend.err.log"
}

# --- Frontend ----------------------------------------------------------
Write-Host "`n[3/3] Frontend (Vite)..." -ForegroundColor Yellow
$npmCmd = if ($OnWindows) { "npm.cmd" } else { "npm" }
$frontendArgs = @{
    FilePath               = $npmCmd
    ArgumentList            = @("run", "dev")
    WorkingDirectory        = $FrontendDir
    RedirectStandardOutput  = (Join-Path $RunDir "logs\frontend.out.log")
    RedirectStandardError   = (Join-Path $RunDir "logs\frontend.err.log")
    RedirectStandardInput   = $NullDevice
    PassThru                = $true
}
if ($OnWindows) { $frontendArgs.WindowStyle = "Hidden" }
$frontendProc = Start-Process @frontendArgs
Save-ProcessId -Name "frontend" -ProcessId $frontendProc.Id
if (Wait-ForPort -Url $FrontendUrl -TimeoutSec 60) {
    Write-Host "  Up at $FrontendUrl (PID $($frontendProc.Id))."
} else {
    Write-Warning "  Frontend didn't respond within 60s -- check .run/logs/frontend.err.log (Vite's first cold start can be slow on Windows, especially the first run after install -- if the log is empty, it may just still be starting; check $FrontendUrl in a moment)"
}

Write-Host "`nOpening $FrontendUrl ..." -ForegroundColor Green
try {
    Start-Process $FrontendUrl
} catch {
    Write-Warning "  Could not auto-open a browser -- open $FrontendUrl manually."
}

Write-Host "`nRunning. Logs are in .run\logs\. Stop everything with: .\scripts\stop.ps1" -ForegroundColor Green
