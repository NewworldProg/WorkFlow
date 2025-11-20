param(
    [string]$CustomPath = "",
    [switch]$DryRun = $false,
    [switch]$WorkflowsOnly = $false,
    [switch]$Force = $false,
    [switch]$SkipN8nInstall = $false
)

# Set UTF-8 encoding
$PSDefaultParameterValues['*:Encoding'] = 'utf8'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [Console]::OutputEncoding

Write-Host "N8N WORKFLOW INSTALLER & COMPLETE SETUP" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Get current working directory
if ($CustomPath) {
    $newBasePath = $CustomPath.TrimEnd('\')
    Write-Host "Using custom path: $newBasePath" -ForegroundColor Yellow
}
else {
    $newBasePath = (Get-Location).Path.TrimEnd('\')
    Write-Host "Auto-detected path: $newBasePath" -ForegroundColor Green
}

$venvName = "upwork_notif_env"
$venvPath = Join-Path $newBasePath $venvName

# CHECK PREREQUISITES
Write-Host "`nChecking prerequisites..." -ForegroundColor Cyan

# Check Node.js
$nodeVersion = $null
try {
    $nodeVersion = & node --version 2>$null
    Write-Host "  Node.js: $nodeVersion" -ForegroundColor Green
}
catch {
    Write-Host "  Node.js not found!" -ForegroundColor Red
    $needsNode = $true
}

# Check npm
$npmVersion = $null
try {
    $npmVersion = & npm --version 2>$null
    Write-Host "  npm: v$npmVersion" -ForegroundColor Green
}
catch {
    Write-Host "  npm not found!" -ForegroundColor Red
    $needsNpm = $true
}

# Check Python
$pythonVersion = $null
try {
    $pythonVersion = & python --version 2>$null
    Write-Host "  Python: $pythonVersion" -ForegroundColor Green
}
catch {
    Write-Host "  Python not found!" -ForegroundColor Red
    $needsPython = $true
}

# Install Node.js if missing
if (($needsNode -or $needsNpm) -and -not $SkipN8nInstall) {
    Write-Host "`nNode.js installation required..." -ForegroundColor Yellow
    Write-Host "Please install Node.js manually:" -ForegroundColor White
    Write-Host "1. Go to: https://nodejs.org/en/download/" -ForegroundColor Gray
    Write-Host "2. Download and install Node.js LTS" -ForegroundColor Gray
    Write-Host "3. Restart PowerShell and run this script again" -ForegroundColor Gray
    Write-Host "`nOr run with -SkipN8nInstall to skip N8N installation" -ForegroundColor Cyan
    exit 1
}

# DETERMINE MODE
if ($WorkflowsOnly) {
    Write-Host "`nWORKFLOWS ONLY MODE" -ForegroundColor Yellow
    Write-Host "Will only install N8N workflows, skip environment setup" -ForegroundColor Gray
}
else {
    Write-Host "`nCOMPLETE SETUP MODE (DEFAULT)" -ForegroundColor Magenta
    Write-Host "Will set up: N8N + virtual environment + packages + workflows" -ForegroundColor Yellow
    Write-Host "Use -WorkflowsOnly to skip environment setup" -ForegroundColor Gray
}

# STEP 1: INSTALL N8N GLOBALLY
if (-not $SkipN8nInstall -and -not $WorkflowsOnly) {
    Write-Host "`nSTEP 1: Installing N8N..." -ForegroundColor Magenta
    
    # Check if N8N is already installed
    $n8nInstalled = $false
    try {
        $n8nVersion = & n8n --version 2>$null
        Write-Host "  N8N already installed: v$n8nVersion" -ForegroundColor Green
        $n8nInstalled = $true
    }
    catch {
        Write-Host "  N8N not found, installing..." -ForegroundColor Yellow
    }
    
    if (-not $n8nInstalled -or $Force) {
        if ($Force -and $n8nInstalled) {
            Write-Host "  Force reinstalling N8N..." -ForegroundColor Yellow
        }
        
        if ($DryRun) {
            Write-Host "  [DRY RUN] Would run: npm install n8n -g" -ForegroundColor Cyan
        }
        else {
            Write-Host "  Installing N8N globally via npm..." -ForegroundColor Cyan
            Write-Host "  (This may take a few minutes)" -ForegroundColor Gray
            
            # Install N8N globally
            $npmOutput = & npm install n8n -g 2>&1
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  N8N installed successfully!" -ForegroundColor Green
                
                # Verify installation
                try {
                    $n8nVersion = & n8n --version 2>$null
                    Write-Host "  Verified N8N version: v$n8nVersion" -ForegroundColor Green
                }
                catch {
                    Write-Host "  N8N installed but verification failed" -ForegroundColor Yellow
                }
            }
            else {
                Write-Host "  N8N installation failed!" -ForegroundColor Red
                Write-Host "  Error: $npmOutput" -ForegroundColor Red
                Write-Host "  Try running as Administrator or use -SkipN8nInstall" -ForegroundColor Yellow
            }
        }
    }
}

# STEP 1.5: INSTALL NODE.JS DEPENDENCIES
if (-not $SkipN8nInstall -and -not $WorkflowsOnly) {
    Write-Host "`n📦 STEP 1.5: Installing Node.js Dependencies..." -ForegroundColor Magenta
    
    # Check if package.json exists
    if (Test-Path "package.json") {
        Write-Host "  📄 Found package.json, installing dependencies..." -ForegroundColor Cyan
        
        if ($DryRun) {
            Write-Host "  [DRY RUN] Would run: npm install" -ForegroundColor Cyan
        } else {
            # Install dependencies from package.json
            $npmInstallOutput = & npm install 2>&1
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  ✅ npm install completed successfully!" -ForegroundColor Green
            } else {
                Write-Host "  ❌ npm install failed!" -ForegroundColor Red
                Write-Host "  Output: $npmInstallOutput" -ForegroundColor Red
            }
        }
    } else {
        Write-Host "  📦 No package.json found, installing required packages manually..." -ForegroundColor Yellow
        
        $nodePackages = @("puppeteer-core", "puppeteer", "selenium-webdriver", "cheerio", "fs-extra")
        
        foreach ($package in $nodePackages) {
            Write-Host "    Installing $package..." -ForegroundColor Yellow -NoNewline
            
            if ($DryRun) {
                Write-Host " [DRY RUN]" -ForegroundColor Cyan
            } else {
                $npmOutput = & npm install $package 2>&1
                
                if ($LASTEXITCODE -eq 0) {
                    Write-Host " ✅" -ForegroundColor Green
                } else {
                    Write-Host " ❌" -ForegroundColor Red
                }
            }
        }
        
        if (-not $DryRun) {
            # Create package.json for future use
            $packageJsonContent = @{
                "name" = "upwork-notif-scrapers"
                "version" = "1.0.0"
                "description" = "Node.js scrapers for Upwork Notification System"
                "main" = "js_scrapers/browser_connect_puppeteer.js"
                "scripts" = @{
                    "test" = "node js_scrapers/browser_connect_puppeteer.js"
                    "scrape" = "node js_scrapers/browser_connect_puppeteer.js"
                }
                "dependencies" = @{
                    "puppeteer-core" = "^21.0.0"
                    "puppeteer" = "^21.0.0"
                    "selenium-webdriver" = "^4.15.0"
                    "cheerio" = "^1.0.0-rc.12"
                    "fs-extra" = "^11.1.1"
                }
                "keywords" = @("upwork", "scraping", "automation", "n8n")
                "author" = "Upwork Notification System"
                "license" = "MIT"
            } | ConvertTo-Json -Depth 3
            
            Set-Content -Path "package.json" -Value $packageJsonContent -Encoding UTF8
            Write-Host "  ✅ Created package.json for future installations" -ForegroundColor Green
        }
    }
}

# STEP 2: PYTHON VIRTUAL ENVIRONMENT SETUP
if (-not $WorkflowsOnly) {
    Write-Host "`n📁 STEP 2: Python Virtual Environment..." -ForegroundColor Magenta
    
    if (Test-Path $venvPath) {
        if ($Force) {
            Write-Host "  Removing existing environment..." -ForegroundColor Yellow
            if (-not $DryRun) {
                Remove-Item $venvPath -Recurse -Force
            }
        }
        else {
            Write-Host "  Virtual environment exists (use -Force to recreate)" -ForegroundColor Green
        }
    }
    
    if (-not (Test-Path $venvPath)) {
        Write-Host "  Creating virtual environment..." -ForegroundColor Cyan
        if ($DryRun) {
            Write-Host "  [DRY RUN] Would create: $venvPath" -ForegroundColor Cyan
        }
        else {
            python -m venv $venvPath
            
            if (Test-Path $venvPath) {
                Write-Host "  Virtual environment created!" -ForegroundColor Green
            }
            else {
                Write-Host "  Failed to create virtual environment!" -ForegroundColor Red
                if ($needsPython) {
                    Write-Host "  Install Python first: https://python.org/downloads/" -ForegroundColor Yellow
                }
                exit 1
            }
        }
    }
    
    # Install Python packages
    if ((Test-Path $venvPath) -and -not $DryRun) {
        Write-Host "  Installing Python packages..." -ForegroundColor Cyan
        
        # Set execution policy if needed
        $currentPolicy = Get-ExecutionPolicy -Scope CurrentUser
        if ($currentPolicy -eq "Restricted") {
            Write-Host "  Setting execution policy..." -ForegroundColor Yellow
            Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
        }
        
        $packages = @("beautifulsoup4", "requests", "selenium", "transformers", "torch", "openai", "python-dotenv")
        
        foreach ($package in $packages) {
            Write-Host "    Installing $package..." -ForegroundColor Yellow -NoNewline
            
            & "$venvPath\Scripts\python.exe" -m pip install $package --quiet 2>&1 | Out-Null
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host " OK" -ForegroundColor Green
            }
            else {
                Write-Host " FAILED" -ForegroundColor Red
            }
        }
        
        # Generate requirements.txt
        & "$venvPath\Scripts\python.exe" -m pip freeze > requirements.txt
        Write-Host "  Python environment ready!" -ForegroundColor Green
    }
    
    # Create convenience scripts
    Write-Host "  Creating convenience scripts..." -ForegroundColor Cyan
    
    if (-not $DryRun) {
        # Create activate script
        @"
Write-Host "Activating Upwork Notification System..." -ForegroundColor Cyan
& "$venvPath\Scripts\Activate.ps1"
Write-Host "Environment activated! Project: $newBasePath" -ForegroundColor Green
"@ | Out-File -FilePath "activate_env.ps1" -Encoding UTF8
        
        # Create run with venv script  
        @"
param(
    [Parameter(Mandatory=`$true)][string]`$ScriptPath,
    [Parameter(ValueFromRemainingArguments=`$true)][string[]]`$Arguments
)
Write-Host "Running: `$ScriptPath" -ForegroundColor Cyan
& "$venvPath\Scripts\Activate.ps1"
Set-Location "$newBasePath"
if (`$Arguments) { & `$ScriptPath @Arguments } else { & `$ScriptPath }
"@ | Out-File -FilePath "run_with_venv.ps1" -Encoding UTF8
        
        # Create N8N launcher script
        @"
Write-Host "Starting N8N..." -ForegroundColor Cyan
Write-Host "N8N will be available at: http://localhost:5678" -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop N8N" -ForegroundColor Gray
Write-Host ""

# Set N8N data directory to current project
`$env:N8N_USER_FOLDER = "$newBasePath\.n8n"

# Start N8N
n8n start
"@ | Out-File -FilePath "start_n8n.ps1" -Encoding UTF8
        
        # Create .env template
        if (-not (Test-Path ".env.template")) {
            @"
# Upwork Notification System Environment Variables
OPENAI_API_KEY=your_openai_api_key_here
CHROME_EXECUTABLE_PATH=auto_detect
N8N_WEBHOOK_URL=http://localhost:5678/webhook/your_webhook_id
DEBUG=false

# N8N Configuration
N8N_USER_FOLDER=$newBasePath\.n8n
N8N_HOST=localhost
N8N_PORT=5678
"@ | Out-File -FilePath ".env.template" -Encoding UTF8
        }
        
        Write-Host "  Created helper scripts!" -ForegroundColor Green
    }
}

# STEP 3: WORKFLOW INSTALLATION AND SETUP
Write-Host "`nSTEP 3: N8N Workflows..." -ForegroundColor Magenta

# Create N8N directory structure
$n8nDataDir = Join-Path $newBasePath ".n8n"
$workflowsDir = Join-Path $n8nDataDir "workflows"

if (-not (Test-Path $n8nDataDir)) {
    if ($DryRun) {
        Write-Host "  [DRY RUN] Would create N8N data directory: $n8nDataDir" -ForegroundColor Cyan
    }
    else {
        New-Item -Path $n8nDataDir -ItemType Directory -Force | Out-Null
        Write-Host "  Created N8N data directory" -ForegroundColor Green
    }
}

if (-not (Test-Path $workflowsDir)) {
    if ($DryRun) {
        Write-Host "  [DRY RUN] Would create workflows directory: $workflowsDir" -ForegroundColor Cyan
    }
    else {
        New-Item -Path $workflowsDir -ItemType Directory -Force | Out-Null
        Write-Host "  Created workflows directory" -ForegroundColor Green
    }
}

# Fix hardcoded paths in workflow files
Write-Host "  Processing workflow files..." -ForegroundColor Cyan

$workflowFiles = @(
    "n8n_ai_cover_letter_workflow.json",
    "n8n_chat_ai_workflow.json",
    "n8n_database_cleanup_workflow.json",
    "n8n_workflow_conditional.json"
)

foreach ($workflowFile in $workflowFiles) {
    if (Test-Path $workflowFile) {
        Write-Host "  Processing $workflowFile..." -ForegroundColor Yellow
        
        if ($DryRun) {
            Write-Host "    [DRY RUN] Would fix paths in: $workflowFile" -ForegroundColor Cyan
        }
        else {
            # Read workflow file
            $content = Get-Content $workflowFile -Raw -Encoding UTF8
            
            # Replace hardcoded paths
            $modified = $false
            $oldPaths = @(
                "e:\\Repoi\\UpworkNotif",
                "e:/Repoi/UpworkNotif", 
                "E:\\Repoi\\UpworkNotif",
                "E:/Repoi/UpworkNotif"
            )
            
            foreach ($oldPath in $oldPaths) {
                if ($content.Contains($oldPath)) {
                    $newPath = if ($oldPath.Contains('/')) { $newBasePath.Replace('\', '/') } else { $newBasePath.Replace('\', '\\') }
                    $content = $content.Replace($oldPath, $newPath)
                    $modified = $true
                    Write-Host "    Replaced: $oldPath" -ForegroundColor Gray
                }
            }
            
            # Save fixed workflow
            $outputFile = Join-Path $workflowsDir $workflowFile
            Set-Content -Path $outputFile -Value $content -Encoding UTF8
            
            if ($modified) {
                Write-Host "    Fixed paths in $workflowFile" -ForegroundColor Green
            }
            else {
                Write-Host "    Copied $workflowFile (no changes needed)" -ForegroundColor Green
            }
        }
    }
    else {
        Write-Host "  Workflow file not found: $workflowFile" -ForegroundColor Yellow
    }
}

# Generate workflow import instructions
if (-not $DryRun) {
    @"
# N8N WORKFLOW IMPORT INSTRUCTIONS

To import these workflows into N8N:

1. Start N8N:
   .\start_n8n.ps1

2. Open N8N in browser:
   http://localhost:5678

3. Import workflows:
   - Click "+" to create new workflow
   - Click the "..." menu in top right
   - Select "Import from file"
   - Choose from the following files:

AVAILABLE WORKFLOWS:
• AI Cover Letter Generator: .\.n8n\workflows\n8n_ai_cover_letter_workflow.json
• Chat AI System: .\.n8n\workflows\n8n_chat_ai_workflow.json  
• Database Cleanup: .\.n8n\workflows\n8n_database_cleanup_workflow.json
• Conditional Workflow: .\.n8n\workflows\n8n_workflow_conditional.json

4. Configure webhooks:
   - Each workflow will have unique webhook URLs
   - Update your .env file with the webhook URLs
   - Test workflows using the webhook test feature

HELPFUL COMMANDS:
• Activate environment: .\activate_env.ps1
• Run scripts in environment: .\run_with_venv.ps1 script_name.py
• Start N8N: .\start_n8n.ps1

Project Location: $newBasePath
"@ | Out-File -FilePath "WORKFLOW_IMPORT_GUIDE.md" -Encoding UTF8
    Write-Host "  Created workflow import guide" -ForegroundColor Green
}

# FINAL SUMMARY
Write-Host "`nINSTALLATION COMPLETE!" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green

if (-not $SkipN8nInstall -and -not $WorkflowsOnly) {
    Write-Host "N8N installed globally" -ForegroundColor Green
}

if (-not $WorkflowsOnly) {
    Write-Host "Python virtual environment created: $venvName" -ForegroundColor Green
    Write-Host "Python packages installed" -ForegroundColor Green
    Write-Host "Convenience scripts created" -ForegroundColor Green
}

Write-Host "Workflows processed and copied to .n8n directory" -ForegroundColor Green
Write-Host "Project configured at: $newBasePath" -ForegroundColor Green

Write-Host "`nNEXT STEPS:" -ForegroundColor Cyan
Write-Host "1. Copy .env.template to .env and configure your API keys" -ForegroundColor White
Write-Host "2. Run: .\start_n8n.ps1 to start N8N" -ForegroundColor White
Write-Host "3. Open: http://localhost:5678 in your browser" -ForegroundColor White
Write-Host "4. Import workflows using WORKFLOW_IMPORT_GUIDE.md" -ForegroundColor White

if (-not $WorkflowsOnly) {
    Write-Host "5. Activate Python environment: .\activate_env.ps1" -ForegroundColor White
    Write-Host "6. Run Python scripts: .\run_with_venv.ps1 script_name.py" -ForegroundColor White
}

Write-Host "`nHELPFUL FILES:" -ForegroundColor Yellow
Write-Host "• WORKFLOW_IMPORT_GUIDE.md - Complete workflow setup guide" -ForegroundColor Gray
Write-Host "• .env.template - Environment variables template" -ForegroundColor Gray
if (-not $WorkflowsOnly) {
    Write-Host "• activate_env.ps1 - Activate Python environment" -ForegroundColor Gray
    Write-Host "• run_with_venv.ps1 - Run scripts in environment" -ForegroundColor Gray
    Write-Host "• start_n8n.ps1 - Launch N8N with proper configuration" -ForegroundColor Gray
}

Write-Host "`nEnjoy your Upwork Notification System!" -ForegroundColor Magenta