param(
    [switch]$OpenManagementUI
)

# Helper to launch consumers in new PowerShell windows (FAST_RETRY=1) and run automated Fase3 test.
Write-Host "Starting demo_quick: launching consumers..."

$root = (Get-Location).Path

function Start-ConsumerWindow($script) {
    $ps = "powershell -NoExit -Command `$env:FAST_RETRY='1'; Set-Location -Path '$root'; .\.venv311\Scripts\python.exe $script"
    Start-Process -FilePath powershell -ArgumentList "-NoExit","-Command","`$env:FAST_RETRY='1'; Set-Location -Path '$root'; .\.venv311\Scripts\python.exe $script"
}

# Start consumers
Start-ConsumerWindow '.\email_consumer_simple.py'
Start-ConsumerWindow '.\loyalty_consumer_simple.py'
Start-ConsumerWindow '.\analytics_consumer.py'

Write-Host "Waiting 2s for consumers to be ready..."
Start-Sleep -Seconds 2

Write-Host "Running automated Fase3 validations..."
$env:PYTHONPATH = '.'
.\.venv311\Scripts\python.exe .\tests\fase3_runner.py

if ($OpenManagementUI) {
    Start-Process "http://localhost:15672"
}

Write-Host "Demo finished. Close consumer windows manually when done."
