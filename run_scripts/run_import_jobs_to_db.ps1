$projectRoot = Split-Path $PSScriptRoot -Parent
# PowerShell script to import jobs to database for n8n workflow
# Activates venv and runs Python script

# Set working directory
Set-Location $projectRoot

# Activate virtual environment
& ".\venv\Scripts\Activate.ps1"

# Run Python script to import jobs
python scripts\import_jobs_to_db.py

# Check exit code and output result
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Jobs successfully imported to database"
}
else {
    Write-Host "❌ Error importing jobs to database"
    exit 1
}