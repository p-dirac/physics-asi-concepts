# Shared helpers for install.ps1 / run.ps1 / stop.ps1. Dot-sourced, not run
# directly.

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$RunDir      = Join-Path $ProjectRoot ".run"
$VenvDir     = Join-Path $ProjectRoot ".venv"
$FrontendDir = Join-Path $ProjectRoot "frontend"

# .venv layout differs by OS (Scripts\ on Windows, bin/ on Linux/macOS) --
# branching on $OnWindows here is what let this be tested for real on Linux
# during development, not just eyeballed for Windows syntax.
#
# $OnWindows, not the automatic $IsWindows: $IsWindows only exists on
# PowerShell 6+ ("PowerShell Core"). Windows PowerShell 5.1 -- the version
# built into Windows by default, and what most people get by typing
# `powershell` without having separately installed PowerShell 7 -- has no
# such variable, so `if ($IsWindows)` there silently evaluates $null as
# false and skips every Windows-specific branch below, even though the
# script IS running on Windows. Since 5.1 only ever runs on Windows, its
# absence itself is proof positive of the platform.
$OnWindows = if (Get-Variable -Name IsWindows -ErrorAction SilentlyContinue) { $IsWindows } else { $true }

if ($OnWindows) {
    $VenvPython = Join-Path $VenvDir "Scripts\python.exe"
} else {
    $VenvPython = Join-Path $VenvDir "bin/python"
}

function New-RunDir {
    if (-not (Test-Path $RunDir)) {
        New-Item -ItemType Directory -Path $RunDir | Out-Null
    }
    $logsDir = Join-Path $RunDir "logs"
    if (-not (Test-Path $logsDir)) {
        New-Item -ItemType Directory -Path $logsDir | Out-Null
    }
}

function Reset-RunLogs {
    <#
    Clears old log files at the start of a run. Without this, a log file
    from an earlier run can still be sitting there the next time
    something goes wrong -- confirmed directly: a stale ollama.err.log
    from a run before a bug fix was still visible and confusing on a
    later, successful run, because "already running, nothing to start"
    never touches that file. Every log the user looks at should be from
    the run they're actually looking at.
    #>
    New-RunDir
    $logsDir = Join-Path $RunDir "logs"
    Get-ChildItem -Path $logsDir -Filter "*.log" -ErrorAction SilentlyContinue | Remove-Item -Force
}

function Test-CommandExists {
    param([Parameter(Mandatory)][string]$Name)
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Test-PortOpen {
    <#
    Checks readiness by raw TCP connect rather than an HTTP request. This
    matters: Invoke-WebRequest goes through the HTTP stack, which on
    Windows means it can be tripped up by things that have nothing to do
    with whether the target server is actually up -- a system/corporate
    proxy intercepting even localhost requests, or `localhost` resolving
    to ::1 (IPv6) first when the target only bound 127.0.0.1. Both can
    make Invoke-WebRequest throw against a server that is, in fact,
    running and reachable. A TCP-level connect sidesteps that whole class
    of problem, and it's all that "is something listening on this port"
    actually needs -- it doesn't require parsing a response.
    #>
    param([Parameter(Mandatory)][string]$Url, [int]$TimeoutMs = 2000)
    $uri = [System.Uri]$Url
    $port = if ($uri.Port -gt 0) { $uri.Port } else { 80 }
    try {
        $client = [System.Net.Sockets.TcpClient]::new()
        $connectTask = $client.ConnectAsync($uri.Host, $port)
        $completed = $connectTask.Wait($TimeoutMs)
        $isOpen = $completed -and $client.Connected
        $client.Close()
        return $isOpen
    } catch {
        return $false
    }
}

function Wait-ForPort {
    param([Parameter(Mandatory)][string]$Url, [int]$TimeoutSec = 30)
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        if (Test-PortOpen -Url $Url -TimeoutMs 2000) { return $true }
        Start-Sleep -Milliseconds 500
    }
    return $false
}

function Save-ProcessId {
    param([Parameter(Mandatory)][string]$Name, [Parameter(Mandatory)][int]$ProcessId)
    New-RunDir
    Set-Content -Path (Join-Path $RunDir "$Name.pid") -Value $ProcessId
}

function Get-SavedProcessId {
    param([Parameter(Mandatory)][string]$Name)
    $path = Join-Path $RunDir "$Name.pid"
    if (Test-Path $path) {
        return [int](Get-Content $path -Raw).Trim()
    }
    return $null
}

function Remove-SavedProcessId {
    param([Parameter(Mandatory)][string]$Name)
    $path = Join-Path $RunDir "$Name.pid"
    if (Test-Path $path) { Remove-Item $path -Force }
}

function Stop-ProcessTree {
    <#
    Stops a process and its children -- "npm run dev" spawns a node/vite
    child process (often through more than one level: npm -> a shell ->
    the actual vite process), and stopping only the top-level PID can
    leave that child running, which was confirmed directly during
    development: killing just the parent left the Vite dev server still
    answering requests. Win32_Process/CIM is the Windows mechanism;
    `ps --ppid` is the fallback for non-Windows PowerShell, so this same
    function is correct (and was actually tested) on both.
    #>
    param([Parameter(Mandatory)][int]$ProcessId)

    $childIds = @()
    if ($OnWindows) {
        try {
            $childIds = (Get-CimInstance Win32_Process -Filter "ParentProcessId=$ProcessId" -ErrorAction SilentlyContinue) |
                ForEach-Object { $_.ProcessId }
        } catch {
            # CIM not available for some reason -- fall through to stopping
            # just the parent rather than failing the whole script.
        }
    } else {
        try {
            $childIds = (ps --ppid $ProcessId -o pid= 2>$null) | ForEach-Object { [int]($_.Trim()) }
        } catch {
            # non-Windows without a usable `ps` -- same fallback as above.
        }
    }

    foreach ($childId in $childIds) {
        Stop-ProcessTree -ProcessId $childId
    }

    Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
}
