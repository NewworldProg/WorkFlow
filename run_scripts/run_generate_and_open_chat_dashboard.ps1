$projectRoot = Split-Path $PSScriptRoot -Parent
# Chat Dashboard Generator and Browser Opener for n8n
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Set-Location $projectRoot
Write-Host "Starting Chat Dashboard Generator and Browser Opener..."

try {
    # Activate venv if it exists
    if (Test-Path "venv\Scripts\Activate.ps1") {
        & "venv\Scripts\Activate.ps1"
    }
    
    # Run dashboard generator
    Write-Host "Generating chat dashboard..."
    $process = Start-Process -FilePath "python" -ArgumentList "dashboard_generate\chat_dashboard_generator.py" -PassThru -NoNewWindow -Wait
    
    if ($process.ExitCode -ne 0) {
        Write-Host "Chat dashboard generation failed with exit code: $($process.ExitCode)"
        exit 1
    }
    
    Write-Host "Chat dashboard generated successfully"
    
    # Check if dashboard file exists
    $dashboardPath = "$projectRoot\dashboard_generate\chat_dashboard.html"
    if (-not (Test-Path $dashboardPath)) {
        Write-Host "Dashboard file not found at: $dashboardPath"
        exit 1
    }
    
    # Convert to URL
    $url = "file:///$($dashboardPath.Replace('\', '/'))"
    Write-Host "Opening dashboard: $url"
    
    # Chrome executable paths to try
    $chromePaths = @(
        "${env:ProgramFiles}\Google\Chrome\Application\chrome.exe",
        "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
        "${env:LOCALAPPDATA}\Google\Chrome\Application\chrome.exe"
    )
    
    $chromePath = $null
    foreach ($path in $chromePaths) {
        if (Test-Path $path) {
            $chromePath = $path
            break
        }
    }
    
    if ($chromePath) {
        try {
            # Open in Chrome with specific window position (different from cover letter dashboard)
            # Chat dashboard will open at position 1250,100 (right side of screen)
            $chromeArgs = "--new-window --window-size=1200,900 --window-position=1250,100 `"$url`""
            Start-Process $chromePath -ArgumentList $chromeArgs -ErrorAction SilentlyContinue
            Write-Host "[OK] Chat dashboard opened in Chrome (right side)"
        }
        catch {
            Write-Host "Failed to open Chrome with custom args, trying default method..."
            Start-Process $url
        }
    }
    else {
        # Fallback to default browser
        Write-Host "Chrome not found, opening in default browser..."
        Start-Process $url
    }
    
    Write-Host "Chat dashboard workflow completed successfully"
    exit 0
}
catch {
    Write-Host "Error in chat dashboard workflow: $($_.Exception.Message)"
    exit 1
}