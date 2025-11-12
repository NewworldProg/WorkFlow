$projectRoot = Split-Path $PSScriptRoot -Parent
# PowerShell script to get latest job without cover letter for n8n workflow
# Activates venv and runs Python script

# Set working directory
Set-Location $projectRoot

# Activate virtual environment
& ".\venv\Scripts\Activate.ps1"

# Run Python script to get latest job
python scripts\get_latest_job_without_cover_letter.py

# Check exit code and output result
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Latest job retrieved successfully"
}
else {
    Write-Host "❌ Error getting latest job"
    exit 1
}