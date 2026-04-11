param(
    [int]$Port = 5432,
    [int]$TimeoutSec = 20
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$postgresExe = Join-Path $root "postgresql-binaries\pgsql\bin\postgres.exe"
$dataDir = Join-Path $root "postgres-data"
$stdoutLog = Join-Path $root "postgres_stdout.log"
$stderrLog = Join-Path $root "postgres_stderr.log"
$pidFile = Join-Path $root ".postgres.pid"

if (-not (Test-Path $postgresExe)) {
    throw "postgres.exe not found: $postgresExe"
}

$existingProcessIds = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique
foreach ($existingProcessId in $existingProcessIds) {
    Stop-Process -Id $existingProcessId -Force -ErrorAction SilentlyContinue
}

Remove-Item $stdoutLog, $stderrLog -Force -ErrorAction SilentlyContinue
Remove-Item (Join-Path $dataDir "postmaster.pid") -Force -ErrorAction SilentlyContinue

$sec = ConvertTo-SecureString 'PgUser#2026' -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential('.\pguser', $sec)
$command = "& '$postgresExe' -D '$dataDir' -p $Port -c 'listen_addresses=localhost' 1>> '$stdoutLog' 2>> '$stderrLog'"

$process = Start-Process -FilePath "powershell.exe" `
    -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $command `
    -Credential $cred `
    -PassThru `
    -WindowStyle Hidden

$deadline = (Get-Date).AddSeconds($TimeoutSec)
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Seconds 1

    $listenerProcessId = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique |
        Select-Object -First 1
    if ($listenerProcessId) {
        Set-Content -Path $pidFile -Value $listenerProcessId
        Write-Output "PostgreSQL started on 127.0.0.1:$Port (PID $listenerProcessId)."
        exit 0
    }
}

$stdout = if (Test-Path $stdoutLog) { Get-Content $stdoutLog -Raw } else { "" }
$stderr = if (Test-Path $stderrLog) { Get-Content $stderrLog -Raw } else { "" }
throw "PostgreSQL start timed out after $TimeoutSec seconds.`nSTDOUT:`n$stdout`nSTDERR:`n$stderr"
