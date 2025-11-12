$projectRoot = Split-Path $PSScriptRoot -Parent
# PowerShell script to parse HTML from database for n8n workflow
# Activates venv and runs Python script

# Set working directory
Set-Location $projectRoot

# Activate virtual environment
& ".\venv\Scripts\Activate.ps1"

# Run Python script to parse HTML
python scripts\parse_html_only.py

# Check exit code and output result
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ HTML successfully parsed"
}
else {
    Write-Host "❌ Error parsing HTML"
    exit 1
}