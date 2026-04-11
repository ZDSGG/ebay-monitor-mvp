$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot

& (Join-Path $root "frontend\stop_frontend_dev.ps1")
& (Join-Path $root "backend\scripts\stop_backend_dev.ps1")
& (Join-Path $root "scripts\stop_postgres_dev.ps1")

Write-Output "All services stopped."
