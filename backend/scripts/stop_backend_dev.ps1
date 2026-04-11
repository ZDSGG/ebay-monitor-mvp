$ErrorActionPreference = "Stop"

$backendRoot = Split-Path -Parent $PSScriptRoot
$pidFile = Join-Path $backendRoot ".backend.pid"

if (-not (Test-Path $pidFile)) {
    Write-Output "No backend pid file found."
    exit 0
}

$processId = Get-Content $pidFile | Select-Object -First 1
if ($processId) {
    Stop-Process -Id ([int]$processId) -Force -ErrorAction SilentlyContinue
}

Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
Write-Output "Backend stopped."
