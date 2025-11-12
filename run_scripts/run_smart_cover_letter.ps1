$projectRoot = Split-Path $PSScriptRoot -Parent
# Smart Cover Letter Generator
# ===========================
# Intelligent generator that only works when needed
# Perfect for scheduled runs every 5 minutes

# in environment add utf-8 encoding so emojis wont break the script
$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# log that script is starting give it neon color
Write-Host "🧠 Smart Cover Letter Generator..." -ForegroundColor Cyan

try {
    # Ensure we're in the correct directory
    Set-Location $projectRoot
    
    # Activate virtual environment if it exists
    if (Test-Path ".\.venv\Scripts\Activate.ps1") {
        Write-Host "🔄 Activating virtual environment..." -ForegroundColor Yellow
        & ".\.venv\Scripts\Activate.ps1"
    }
    
    # Run the smart cover letter generator from current directory
    $result = python scripts\smart_cover_letter_generator.py
    
    # LASTEXITCODE check and output based on result
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Smart generation completed!" -ForegroundColor Green
        Write-Host $result
    }
    else {
        Write-Host "⚠️ No work needed or generation failed" -ForegroundColor Yellow
        Write-Host $result
    }
}
# catch error handling
catch {
    Write-Host "❌ Error running smart generator: $_" -ForegroundColor Red
    exit 1
}

exit 0