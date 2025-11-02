Param(
    [int]$Tail = 500,
    [string]$OutDir = "./artifacts"
)

if (-not (Test-Path $OutDir)) { New-Item -ItemType Directory -Path $OutDir | Out-Null }
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logsDir = Join-Path $OutDir ("logs_$timestamp")
New-Item -ItemType Directory -Path $logsDir | Out-Null

$containers = @('user-service-1','user-service-2','user-service-3')
$patterns = @('Usuario creado localmente','Evento UsuarioCreado publicado')

$summary = @{}

Write-Host "Collecting docker logs (tail $Tail) for: $($containers -join ', ')"

foreach ($c in $containers) {
    $logFile = Join-Path $logsDir ("$c.log")
    Write-Host "Saving logs for $c -> $logFile"
    # Use Start-Process to avoid NativeCommandError and capture stdout/stderr reliably
    $stdoutTmp = Join-Path $logsDir ("${c}_stdout.tmp")
    $stderrTmp = Join-Path $logsDir ("${c}_stderr.tmp")
    if (Test-Path $stdoutTmp) { Remove-Item $stdoutTmp -ErrorAction SilentlyContinue }
    if (Test-Path $stderrTmp) { Remove-Item $stderrTmp -ErrorAction SilentlyContinue }
    $args = @('logs', $c, '--tail', $Tail)
    $proc = Start-Process -FilePath 'docker' -ArgumentList $args -NoNewWindow -RedirectStandardOutput $stdoutTmp -RedirectStandardError $stderrTmp -Wait -PassThru
    $stdout = ''
    $stderr = ''
    if (Test-Path $stdoutTmp) { $stdout = Get-Content -Raw -Path $stdoutTmp -ErrorAction SilentlyContinue }
    if (Test-Path $stderrTmp) { $stderr = Get-Content -Raw -Path $stderrTmp -ErrorAction SilentlyContinue }
    ($stdout + "`n" + $stderr) | Out-File -FilePath $logFile -Encoding utf8
    if (Test-Path $stdoutTmp) { Remove-Item $stdoutTmp -ErrorAction SilentlyContinue }
    if (Test-Path $stderrTmp) { Remove-Item $stderrTmp -ErrorAction SilentlyContinue }

    # Filter relevant lines
    $filtered = Join-Path $logsDir ("$c.filtered.log")
    Select-String -Path $logFile -Pattern $patterns -SimpleMatch | ForEach-Object { $_.Line } | Out-File -FilePath $filtered -Encoding utf8

    # Count occurrences by pattern
    $counts = @{}
    foreach ($p in $patterns) {
        $cnt = 0
        try {
            $cnt = (Select-String -Path $logFile -Pattern $p -SimpleMatch).Count
        } catch { $cnt = 0 }
        $counts[$p] = $cnt
    }

    $summary[$c] = $counts
}

$summaryFile = Join-Path $logsDir ("summary_$timestamp.json")
$summary | ConvertTo-Json -Depth 4 | Out-File -FilePath $summaryFile -Encoding utf8

Write-Host "Logs and filtered files saved in: $logsDir"
Write-Host "Summary written to: $summaryFile"
Write-Host "Summary (printed):"
$summary | ConvertTo-Json -Depth 4 | Write-Host

Write-Host "You can inspect filtered logs and attach $logsDir to your deliverables. Example: Get-Content $summaryFile -Raw | ConvertFrom-Json"
