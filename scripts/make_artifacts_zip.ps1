Param(
    [string]$ArtifactsDir = "./artifacts",
    [string]$OutDir = "./artifacts"
)

if (-not (Test-Path $ArtifactsDir)) {
    Write-Error "Artifacts directory '$ArtifactsDir' does not exist. Run the collection scripts first."
    exit 1
}

if (-not (Test-Path $OutDir)) { New-Item -ItemType Directory -Path $OutDir | Out-Null }

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$zipName = "evidence_$timestamp.zip"
$zipPath = Join-Path $OutDir $zipName

Write-Host "Creating ZIP: $zipPath from $ArtifactsDir"
try {
    Compress-Archive -Path (Join-Path $ArtifactsDir "*") -DestinationPath $zipPath -Force
    Write-Host "Created: $zipPath"
} catch {
    Write-Error "Failed to create ZIP: $_"
    exit 2
}

# Print the created file path for automation
Write-Output $zipPath
