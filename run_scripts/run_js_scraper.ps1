$projectRoot = Split-Path $PSScriptRoot -Parent
# Direct Node.js Scraper for n8n - runs js_scrapers/browser_connect_puppeteer.js
Set-Location $projectRoot
# log that script is starting
Write-Host "Starting Node.js scraper directly..."

try {
    # Run Node.js scraper with timeout
    $process = Start-Process -FilePath "C:\Program Files\nodejs\node.exe" -ArgumentList "js_scrapers\browser_connect_puppeteer.js" -PassThru -NoNewWindow -Wait
    # log the output
    if ($process.ExitCode -eq 0) {
        Write-Host "Node.js scraper completed successfully"
        exit 0
    }
    else {
        Write-Host "Node.js scraper failed with exit code: $($process.ExitCode)"
        exit 1
    }
}
catch {
    Write-Host "Error running Node.js scraper: $($_.Exception.Message)"
    exit 1
}