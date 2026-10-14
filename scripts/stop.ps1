<#
.SYNOPSIS
    Stops the backend, frontend, and (only if this project started it)
    Ollama, using the PIDs run.ps1 saved. Safe to run even if nothing is
    running -- it just reports what it finds.
#>

. "$PSScriptRoot\common.ps1"

Write-Host "== Pre-1900 Gravity Model Selection: stop ==" -ForegroundColor Cyan

function Stop-Tracked {
    param([Parameter(Mandatory)][string]$Name, [Parameter(Mandatory)][string]$Label)

    $processId = Get-SavedProcessId -Name $Name
    if (-not $processId) {
        Write-Host "  $Label -- no PID on record, nothing to do."
        return
    }
    $proc = Get-Process -Id $processId -ErrorAction SilentlyContinue
    if (-not $proc) {
        Write-Host "  $Label -- recorded PID $processId is not running (already stopped)."
    } else {
        Stop-ProcessTree -ProcessId $processId
        Write-Host "  $Label -- stopped (PID $processId)."
    }
    Remove-SavedProcessId -Name $Name
}

Stop-Tracked -Name "frontend" -Label "Frontend"
Stop-Tracked -Name "backend"  -Label "Backend"
Stop-Tracked -Name "ollama"   -Label "Ollama"

Write-Host "`nDone." -ForegroundColor Green
