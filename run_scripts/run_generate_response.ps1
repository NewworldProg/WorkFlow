# Response Generator - CLEAN VERSION  
# Generates responses based on pre-detected phase
# Usage: .\run_generate_response.ps1 [-Mode template|ai|both] [-Phase detected_phase]

param(
    [ValidateSet('template', 'ai', 'both')]
    [string]$Mode = 'template',
    
    [string]$Phase = 'auto'
)

$projectRoot = Split-Path $PSScriptRoot -Parent
Set-Location $projectRoot

Write-Host "=== Response Generator ===" -ForegroundColor Cyan
Write-Host "Generating responses for detected phase..." -ForegroundColor Yellow

# Show mode info
switch ($Mode) {
    'template' { 
        Write-Host "Mode: TEMPLATE (Pre-written responses)" -ForegroundColor Green 
    }
    'ai' { 
        Write-Host "Mode: AI (GPT-2 Generated)" -ForegroundColor Yellow 
    }
    'both' { 
        Write-Host "Mode: BOTH (Template + AI)" -ForegroundColor Magenta 
    }
}

if ($Phase -ne 'auto') {
    Write-Host "Phase: $Phase (manually specified)" -ForegroundColor Cyan
}
else {
    Write-Host "Phase: Auto-detect from conversation" -ForegroundColor Cyan
}
Write-Host ""

# Activate virtual environment
$venvActivate = ".\venv\Scripts\Activate.ps1"
if (Test-Path $venvActivate) {
    & $venvActivate
    Write-Host "[OK] Virtual environment activated" -ForegroundColor Green
}
else {
    Write-Host "[WARN] No venv found - using system Python" -ForegroundColor Yellow
}

# Run response generator
Write-Host ""
Write-Host "Generating responses..." -ForegroundColor Cyan

if ($Phase -ne 'auto') {
    # Use specified phase
    python ai\smart_chat_response.py --session-id latest --mode $Mode --phase $Phase
}
else {
    # Auto-detect phase
    python ai\smart_chat_response.py --session-id latest --mode $Mode
}

Write-Host ""
Write-Host "=== Response Generation Complete ===" -ForegroundColor Green
Write-Host "Responses generated successfully" -ForegroundColor Cyan