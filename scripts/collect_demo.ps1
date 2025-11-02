Param(
    [int]$Count = 30,
    [string]$Url = 'http://localhost/users',
    [string]$OutDir = "./artifacts"
)

if (-not (Test-Path $OutDir)) { New-Item -ItemType Directory -Path $OutDir | Out-Null }
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$respFile = Join-Path $OutDir ("responses_$timestamp.json")
$logsDir = Join-Path $OutDir ("logs_$timestamp")
New-Item -ItemType Directory -Path $logsDir | Out-Null

Write-Host "Sending $Count POST requests to $Url and saving responses to $respFile"

$responses = @()
for ($i = 1; $i -le $Count; $i++) {
    $body = @{ nombre = "User-$i"; email = "user$i@example.com" } | ConvertTo-Json
    try {
        $r = Invoke-RestMethod -Method Post -Uri $Url -ContentType 'application/json' -Body $body -TimeoutSec 10
        $responses += $r
        Write-Host "[$i] =>" ($r | ConvertTo-Json -Depth 2)
    } catch {
        Write-Host "[$i] ERROR: $_"
        $responses += @{ error = $_.Exception.Message; index = $i }
    }
}

# Save responses
$responses | ConvertTo-Json -Depth 4 | Out-File -FilePath $respFile -Encoding utf8
Write-Host "Saved responses to $respFile"

# Collect docker logs for known containers (best-effort)
$containers = @('user-service-1','user-service-2','user-service-3','nginx_taller6','ecomarket-rabbit')
foreach ($c in $containers) {
    $out = Join-Path $logsDir ("$c.log")
    # Use Start-Process to capture stdout/stderr reliably and avoid PowerShell NativeCommandError
    $stdoutTmp = Join-Path $logsDir ("${c}_stdout.tmp")
    $stderrTmp = Join-Path $logsDir ("${c}_stderr.tmp")
    if (Test-Path $stdoutTmp) { Remove-Item $stdoutTmp -ErrorAction SilentlyContinue }
    if (Test-Path $stderrTmp) { Remove-Item $stderrTmp -ErrorAction SilentlyContinue }

    $args = @('logs', $c, '--tail', '500')
    $proc = Start-Process -FilePath 'docker' -ArgumentList $args -NoNewWindow -RedirectStandardOutput $stdoutTmp -RedirectStandardError $stderrTmp -Wait -PassThru

    $stdout = ''
    $stderr = ''
    if (Test-Path $stdoutTmp) { $stdout = Get-Content -Raw -Path $stdoutTmp -ErrorAction SilentlyContinue }
    if (Test-Path $stderrTmp) { $stderr = Get-Content -Raw -Path $stderrTmp -ErrorAction SilentlyContinue }

    if ($proc.ExitCode -ne 0) {
        $errText = if ($stderr) { $stderr } elseif ($stdout) { $stdout } else { 'Unknown error' }
        Write-Host "Could not collect logs for ${c}: $errText"
        # Save whatever we captured for debugging
        ($stdout + "`n" + $stderr) | Out-File -FilePath $out -Encoding utf8
    } else {
        ($stdout + "`n" + $stderr) | Out-File -FilePath $out -Encoding utf8
        Write-Host "Saved logs for $c -> $out"
    }

    # Cleanup temp files
    if (Test-Path $stdoutTmp) { Remove-Item $stdoutTmp -ErrorAction SilentlyContinue }
    if (Test-Path $stderrTmp) { Remove-Item $stderrTmp -ErrorAction SilentlyContinue }
}

Write-Host "Artifacts collected in: $logsDir and $respFile"
Write-Host "To make a short video: 1) run this script, 2) open the responses file and the logs, 3) use your screen recorder (OBS/Windows Game Bar) to capture the terminal and log viewer for ~60s."
