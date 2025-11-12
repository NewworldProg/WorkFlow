$projectRoot = Split-Path $PSScriptRoot -Parent
# Chat JavaScript Scraper for n8n
Set-Location $projectRoot
Write-Host "Starting Chat JavaScript Scraper..."

try {
    # Run JavaScript chat scraper
    $process = Start-Process -FilePath "node" -ArgumentList "js_scrapers\browser_connect_chat.js" -PassThru -NoNewWindow -Wait
    
    if ($process.ExitCode -eq 0) {
        Write-Host "Chat scraper completed successfully"
        exit 0
    }
    else {
        Write-Host "Chat scraper failed with exit code: $($process.ExitCode)"
        exit 1
    }
}
catch {
    Write-Host "Error running chat scraper: $($_.Exception.Message)"
    exit 1
}