Param(
    [string]$Destination = 'D:\EcoMarketPubSub'
)

try {
    $src = (Get-Location).ProviderPath
} catch {
    $src = Get-Location
}

Write-Host "Source: $src"
Write-Host "Destination: $Destination"

Write-Host "\nSTEP 1: Ensure no terminals or editors are open inside the source folder. If you get 'in use' errors, close VS Code/PowerShell windows and re-run this script."

# Create destination if missing and mirror copy using robocopy (robust for open files)
if (-not (Test-Path $Destination)) {
    New-Item -ItemType Directory -Path $Destination -Force | Out-Null
}

$robocopyArgs = @(
    "`"$src`"",
    "`"$Destination`"",
    '/MIR', '/R:3', '/W:5'
)

Write-Host "Running robocopy to copy repository (this can take a moment)..."
robocopy @robocopyArgs | Write-Host

Write-Host "\nSTEP 2: Change directory to destination and run docker compose in verbose mode; output will be saved to compose_verbose.log"
Set-Location $Destination

$logFile = Join-Path $Destination 'compose_verbose.log'
Write-Host "Running: docker compose --verbose -f docker-compose.taller6.yml up --build -d"
Write-Host "Logs will be written to: $logFile"

# Run compose verbose and capture output using Start-Process
$dockerArgs = 'compose --verbose -f docker-compose.taller6.yml up --build -d'
$outStd = Join-Path $Destination 'compose_stdout.log'
$outErr = Join-Path $Destination 'compose_stderr.log'

if (Test-Path $outStd) { Remove-Item $outStd -Force }
if (Test-Path $outErr) { Remove-Item $outErr -Force }

$proc = Start-Process -FilePath "docker" -ArgumentList $dockerArgs -NoNewWindow -RedirectStandardOutput $outStd -RedirectStandardError $outErr -Wait -PassThru
$exitCode = $proc.ExitCode

Write-Host "docker compose exited with code: $exitCode"

# Combine stdout and stderr into the single compose_verbose.log for easier inspection
Get-Content $outStd, $outErr | Out-File -FilePath $logFile -Encoding utf8

Write-Host "-- Last 200 lines of compose_verbose.log --"
Get-Content $logFile -Tail 200 | Write-Host

Write-Host "\nSaving docker info and docker ps -a to files for diagnostics..."
docker info *> docker_info.txt 2>&1
docker ps -a *> docker_ps_a.txt 2>&1
Write-Host "Saved docker_info.txt and docker_ps_a.txt"

if ($exitCode -ne 0) {
    Write-Host "Compose failed. Please attach the file compose_verbose.log (and docker_info.txt, docker_ps_a.txt) so I can analyze."
    exit $exitCode
}

Write-Host "Compose reported success (exit code 0). You can now run: .\scripts\collect_demo.ps1 -Count 30 -Url http://localhost/users to collect responses/logs for the demo."
