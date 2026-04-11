$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot

& (Join-Path $root "scripts\start_postgres_dev.ps1")
& (Join-Path $root "backend\scripts\start_backend_dev.ps1")
& (Join-Path $root "frontend\start_frontend_dev.ps1")

Write-Output "All services started."
