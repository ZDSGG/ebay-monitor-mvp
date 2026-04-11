param(
    [int]$Port = 5173,
    [int]$TimeoutSec = 30
)

$ErrorActionPreference = "Stop"

$frontendRoot = $PSScriptRoot
$stdoutLog = Join-Path $frontendRoot "vite_out.log"
$stderrLog = Join-Path $frontendRoot "vite_err.log"
$pidFile = Join-Path $frontendRoot ".frontend.pid"
$appUrl = "http://127.0.0.1:$Port"

$existingProcessIds = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique
foreach ($existingProcessId in $existingProcessIds) {
    Stop-Process -Id $existingProcessId -Force -ErrorAction SilentlyContinue
}

Remove-Item $stdoutLog, $stderrLog -Force -ErrorAction SilentlyContinue

$command = @"
Set-Location '$frontendRoot'
npm run dev -- --host 127.0.0.1 --port $Port *>> '$stdoutLog' 2>> '$stderrLog'
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
        throw "Frontend exited early.`nSTDOUT:`n$stdout`nSTDERR:`n$stderr"
    }

    try {
        $response = Invoke-WebRequest -Uri $appUrl -UseBasicParsing -TimeoutSec 2
        if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
            $listenerProcessId = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue |
                Select-Object -ExpandProperty OwningProcess -Unique |
                Select-Object -First 1
            if ($listenerProcessId) {
                Set-Content -Path $pidFile -Value $listenerProcessId
            }
            Write-Output "Frontend started successfully on $appUrl (PID $($process.Id))."
            exit 0
        }
    } catch {
    }
}

Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue

$stdout = if (Test-Path $stdoutLog) { Get-Content $stdoutLog -Raw } else { "" }
$stderr = if (Test-Path $stderrLog) { Get-Content $stderrLog -Raw } else { "" }
throw "Frontend start timed out after $TimeoutSec seconds.`nSTDOUT:`n$stdout`nSTDERR:`n$stderr"
