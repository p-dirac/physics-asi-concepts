

. "$PSScriptRoot\common.ps1"

if (Test-HttpUp -Url "http://localhost:11434") {
    Write-Host "  Ollama already running -- leaving it alone."
} else{
    Write-Host "  Ollama not running"
}