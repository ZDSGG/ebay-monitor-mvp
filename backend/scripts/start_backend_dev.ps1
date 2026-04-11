param(
    [int]$Port = 8000,
    [int]$TimeoutSec = 20
)

$ErrorActionPreference = "Stop"

$backendRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $backendRoot ".venv\Scripts\python.exe"
$stdoutLog = Join-Path $backendRoot "uvicorn_out.log"
$stderrLog = Join-Path $backendRoot "uvicorn_err.log"
$pidFile = Join-Path $backendRoot ".backend.pid"
$healthUrl = "http://127.0.0.1:$Port/api/health"

$existingProcessIds = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique
foreach ($existingProcessId in $existingProcessIds) {
    Stop-Process -Id $existingProcessId -Force -ErrorAction SilentlyContinue
}

if (-not (Test-Path $pythonPath)) {
    throw "Backend virtual environment not found: $pythonPath"
}

Remove-Item $stdoutLog, $stderrLog -Force -ErrorAction SilentlyContinue

$command = @"
Set-Location '$backendRoot'
\$env:PYTHONPATH='.'
& '$pythonPath' -m uvicorn app.main:app --host 127.0.0.1 --port $Port *>> '$stdoutLog' 2>> '$stderrLog'
"@

$process = Start-Process -FilePath "powershell.exe" `
    -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $command `
    -PassThru `
    -WindowStyle Hidden

Set-Content -Path $pidFile -Value $process.Id

$deadline = (Get-Date).AddSeconds($TimeoutSec)
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Seconds 1

    if ($process.HasExited) {
        $stdout = if (Test-Path $stdoutLog) { Get-Content $stdoutLog -Raw } else { "" }
        $stderr = if (Test-Path $stderrLog) { Get-Content $stderrLog -Raw } else { "" }
        throw "Backend exited early.`nSTDOUT:`n$stdout`nSTDERR:`n$stderr"
    }

    try {
        $response = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 2
        if ($response.StatusCode -eq 200) {
            $listenerProcessId = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue |
                Select-Object -ExpandProperty OwningProcess -Unique |
                Select-Object -First 1
            if ($listenerProcessId) {
                Set-Content -Path $pidFile -Value $listenerProcessId
            }
            Write-Output "Backend started successfully on $healthUrl (PID $($process.Id))."
            exit 0
        }
    } catch {
    }
}

Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue

$stdout = if (Test-Path $stdoutLog) { Get-Content $stdoutLog -Raw } else { "" }
$stderr = if (Test-Path $stderrLog) { Get-Content $stderrLog -Raw } else { "" }
throw "Backend start timed out after $TimeoutSec seconds.`nSTDOUT:`n$stdout`nSTDERR:`n$stderr"
