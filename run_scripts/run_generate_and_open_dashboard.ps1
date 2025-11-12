$projectRoot = Split-Path $PSScriptRoot -Parent
# PowerShell script to generate HTML dashboard and open it
# For use with n8n Execute Command node

try {
    # log that script is starting
    Write-Host "💼 Generating and opening job opportunities dashboard..."
    
    # Change to project directory
    Set-Location $projectRoot
    
    # Generate timestamp for unique filename
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $outputFile = "data\dashboard_$timestamp.html"
    
    # Check if database exists
    if (-not (Test-Path "upwork_data.db")) {
        Write-Host "⚠️ Database not found, creating with sample data..."
        # Try to load existing parsed data first
        python -c "
from data.database_manager import UpworkDatabase
db = UpworkDatabase()
files, jobs = db.load_existing_parsed_data()
print(f'Loaded {files} files with {jobs} jobs from existing data')
"
    }
    
    # Run enhanced dashboard generator with UTF-8 encoding
    $env:PYTHONIOENCODING = "utf-8"
    # inside variable define path to output file that generates static dashboard
    $result = python dashboard_generate\generate_dashboard_enhanced.py --output $outputFile
    
    # log output based on result
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Dashboard generated successfully"
        Write-Host $result
        
        # Also create a latest.html copy
        Copy-Item $outputFile "data\dashboard_latest.html" -Force
        
        # Get full path for browser
        $fullPath = Resolve-Path "data\dashboard_latest.html"
        Write-Host "🌐 Dashboard URL: file:///$($fullPath.Path.Replace('\', '/'))"
        
        # log that we are opening the dashboard
        Write-Host "🚀 Opening job opportunities dashboard in smaller window..."
        
        # Try to open with specific window size (works with Chrome/Edge)
        $dashboardPath = Resolve-Path "data\dashboard_latest.html"
        $url = "file:///$($dashboardPath.Path.Replace('\', '/'))"
        
        # Try different approaches for smaller window
        try {
            # Method 1: Use Chrome with window size parameters
            $chromeArgs = "--new-window --window-size=1200,800 --window-position=100,100 `"$url`""
            Start-Process "chrome.exe" -ArgumentList $chromeArgs -ErrorAction SilentlyContinue
            Write-Host "✅ Opened in Chrome with custom size"
        }
        catch {
            try {
                # Method 2: Use Edge with window parameters  
                $edgeArgs = "--new-window --window-size=1200,800 `"$url`""
                Start-Process "msedge.exe" -ArgumentList $edgeArgs -ErrorAction SilentlyContinue
                Write-Host "✅ Opened in Edge with custom size"
            }
            catch {
                # Method 3: Fallback to default browser
                Start-Process "data\dashboard_latest.html"
                Write-Host "✅ Opened in default browser"
            }
        }
        
        # Wait a moment for browser to start
        Start-Sleep -Seconds 2
        
        # Output JSON for n8n
        $output = @{
            "success"        = $true
            "dashboard_file" = $outputFile
            "dashboard_url"  = "file:///$($fullPath.Path.Replace('\', '/'))"
            "timestamp"      = $timestamp
            "browser_opened" = $true
        }
        
        Write-Host ($output | ConvertTo-Json -Compress)
        exit 0
    }
    else {
        Write-Host "❌ Dashboard generation failed with exit code: $LASTEXITCODE"
        Write-Host $result
        
        # Output error JSON for n8n
        $output = @{
            "success"        = $false
            "error"          = "Dashboard generation failed"
            "exit_code"      = $LASTEXITCODE
            "browser_opened" = $false
        }
        
        Write-Host ($output | ConvertTo-Json -Compress)
        exit 1
    }
}
catch {
    Write-Host "💥 Script error: $($_.Exception.Message)"
    
    # Output error JSON for n8n
    $output = @{
        "success"        = $false
        "error"          = $_.Exception.Message
        "browser_opened" = $false
    }
    
    Write-Host ($output | ConvertTo-Json -Compress)
    exit 1
}