$ErrorActionPreference = "Stop"

$frontendRoot = $PSScriptRoot
$pidFile = Join-Path $frontendRoot ".frontend.pid"

if (-not (Test-Path $pidFile)) {
    Write-Output "No frontend pid file found."
    exit 0
}

$processId = Get-Content $pidFile | Select-Object -First 1
if ($processId) {
    Stop-Process -Id ([int]$processId) -Force -ErrorAction SilentlyContinue
}

Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
Write-Output "Frontend stopped."
