$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$pidFile = Join-Path $root ".postgres.pid"

$processId = $null
if (Test-Path $pidFile) {
    $processId = Get-Content $pidFile | Select-Object -First 1
}

if ($processId) {
    Stop-Process -Id ([int]$processId) -Force -ErrorAction SilentlyContinue
}

$listenerProcessIds = Get-NetTCPConnection -LocalPort 5432 -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique
foreach ($listenerProcessId in $listenerProcessIds) {
    Stop-Process -Id $listenerProcessId -Force -ErrorAction SilentlyContinue
}

Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
Write-Output "PostgreSQL stopped."
