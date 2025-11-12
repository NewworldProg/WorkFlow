# PowerShell Script: Standalone Phase Detector
# Detects conversation phase using BERT and updates database
# No response generation - only phase detection

param(
    [string]$SessionId = "latest",
    [string]$Output = "json"
)

# Get current directory and Python executable
$currentDir = Get-Location
$pythonExe = "python"
$scriptPath = "E:\Repoi\UpworkNotif\ai\standalone_phase_detector.py"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "STANDALONE PHASE DETECTOR" -ForegroundColor Cyan  
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Session ID: $SessionId" -ForegroundColor Yellow
Write-Host "Output Format: $Output" -ForegroundColor Yellow
Write-Host "Script Path: $scriptPath" -ForegroundColor Yellow
Write-Host ""

# Build command with full path
$command = "$pythonExe `"$scriptPath`" --session `"$SessionId`" --output `"$Output`""

Write-Host "Command: $command" -ForegroundColor Green
Write-Host ""

# Execute phase detection
try {
    Write-Host "[PHASE DETECT] Starting BERT analysis..." -ForegroundColor Blue
    
    # Run the standalone phase detector
    $result = Invoke-Expression $command
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[SUCCESS] Phase detection completed!" -ForegroundColor Green
        Write-Host ""
        Write-Host $result
    }
    else {
        Write-Host "[ERROR] Phase detection failed!" -ForegroundColor Red
        Write-Host $result
        exit 1
    }
    
}
catch {
    Write-Host "[EXCEPTION] Error running phase detector: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "PHASE DETECTION COMPLETE" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan