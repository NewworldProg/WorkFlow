$projectRoot = Split-Path $PSScriptRoot -Parent
# PowerShell script to save HTML to database from n8n workflow
# Activates venv and runs Python script

# Set working directory
Set-Location $projectRoot

# Activate virtual environment
& ".\venv\Scripts\Activate.ps1"

# Run Python script to save HTML to database
python scripts\save_html_to_db.py

# Check exit code and output result
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ HTML successfully saved to database"
}
else {
    Write-Host "❌ Error saving HTML to database"
    exit 1
}