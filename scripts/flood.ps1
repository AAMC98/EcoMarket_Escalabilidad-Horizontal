Param(
    [int]$Count = 30,
    [string]$Url = 'http://localhost/users'
)

Write-Host "Sending $Count POST requests to $Url"

for ($i = 1; $i -le $Count; $i++) {
    $body = @{ nombre = "User-$i"; email = "user$i@example.com" } | ConvertTo-Json
    try {
        $r = Invoke-RestMethod -Method Post -Uri $Url -ContentType 'application/json' -Body $body -TimeoutSec 10
        Write-Host "[$i] =>" ($r | ConvertTo-Json -Depth 2)
    } catch {
        Write-Host "[$i] ERROR: $_"
    }
}
