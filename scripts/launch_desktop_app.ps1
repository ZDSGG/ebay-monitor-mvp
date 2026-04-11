$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$frontendUrl = "http://127.0.0.1:5173/items"

& (Join-Path $root "scripts\start_all_dev.ps1")

Start-Sleep -Seconds 3
Start-Process $frontendUrl

Write-Output "eBay monitor desktop launcher completed."
