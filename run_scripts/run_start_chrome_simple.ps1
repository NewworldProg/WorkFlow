# Chrome Debug Starter - Portable version using $PSScriptRoot
$projectRoot = $PSScriptRoot
Write-Host "Starting Chrome from: $projectRoot"

# Try common Chrome installation paths
$chromePaths = @(
    "C:\Program Files\Google\Chrome\Application\chrome.exe",
    "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe"
)

$chrome = $chromePaths | Where-Object { Test-Path $_ } | Select-Object -First 1

if ($chrome) {
    $profilePath = Join-Path $projectRoot "chrome_profile"
    Start-Process $chrome "--remote-debugging-port=9222 --user-data-dir=`"$profilePath`""
    Write-Host "Chrome started with profile: $profilePath"
}
else {
    Write-Host "ERROR: Chrome not found in standard locations!"
    Write-Host "Please install Chrome or update the script with your Chrome path."
    exit 1
}
