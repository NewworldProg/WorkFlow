param(
    [string]$CustomPath = "",
    [switch]$DryRun = $false
)

Write-Host "N8N WORKFLOW INSTALLER" -ForegroundColor Cyan
Write-Host "=====================" -ForegroundColor Cyan

# Get current working directory
if ($CustomPath) {
    $newBasePath = $CustomPath.TrimEnd('\')
    Write-Host "Using custom path: $newBasePath" -ForegroundColor Yellow
}
else {
    $newBasePath = (Get-Location).Path.TrimEnd('\')
    Write-Host "Auto-detected path: $newBasePath" -ForegroundColor Green
}

# List of n8n workflow files
$workflowFiles = @(
    "n8n_workflow_conditional.json",
    "n8n_chat_ai_workflow.json", 
    "n8n_ai_cover_letter_workflow.json",
    "n8n_database_cleanup_workflow.json"
)

Write-Host "`nChecking workflow files:" -ForegroundColor Cyan
$foundFiles = @()
foreach ($file in $workflowFiles) {
    if (Test-Path $file) {
        $foundFiles += $file
        Write-Host "  Found: $file" -ForegroundColor Green
    }
    else {
        Write-Host "  Missing: $file" -ForegroundColor Red
    }
}

if ($foundFiles.Count -eq 0) {
    Write-Host "`nNo workflow files found!" -ForegroundColor Red
    exit 1
}

# Check if paths are already correct
$firstFile = $foundFiles[0]
$content = Get-Content $firstFile -Raw -Encoding UTF8

$currentPath = ""
if ($content -match '"workingDirectory"[^"]*"([^"]+)"') {
    $currentPath = $matches[1]
}

if ($currentPath -eq $newBasePath) {
    Write-Host "`nPaths already correct!" -ForegroundColor Green
    Write-Host "Current: $currentPath" -ForegroundColor Gray
    Write-Host "Target:  $newBasePath" -ForegroundColor Gray
    Write-Host "No changes needed!" -ForegroundColor Green
    return
}

$oldPath = if ($currentPath) { $currentPath } else { "E:\\Repoi\\UpworkNotif" }

Write-Host "`nPath conversion:" -ForegroundColor Yellow
Write-Host "  FROM: $oldPath" -ForegroundColor Red
Write-Host "  TO:   $newBasePath" -ForegroundColor Green

# Create n8n directory
$n8nDir = Join-Path $newBasePath "n8n"

if ($DryRun) {
    Write-Host "`nDRY RUN - Simulating:" -ForegroundColor Cyan
    Write-Host "  Would create: $n8nDir" -ForegroundColor Yellow
}
else {
    Write-Host "`nCreating n8n directory..." -ForegroundColor Cyan
    if (-not (Test-Path $n8nDir)) {
        New-Item -ItemType Directory -Path $n8nDir -Force | Out-Null
        Write-Host "  Created: $n8nDir" -ForegroundColor Green
    }
    else {
        Write-Host "  Exists: $n8nDir" -ForegroundColor Blue
    }
}

Write-Host "`nProcessing files:" -ForegroundColor Cyan

foreach ($file in $foundFiles) {
    $destinationPath = Join-Path $n8nDir $file
    
    Write-Host "`n  Processing: $file" -ForegroundColor Yellow
    
    # Read and update content
    $originalContent = Get-Content $file -Raw -Encoding UTF8
    
    # Replace paths
    $oldPathJson = $oldPath -replace '\\', '\\\\'
    $newPathJson = $newBasePath -replace '\\', '\\\\'
    
    # Count matches
    $matchCount = 0
    $lines = $originalContent -split "`n"
    foreach ($line in $lines) {
        if ($line -match [regex]::Escape($oldPathJson)) {
            $matchCount++
        }
    }
    
    if ($matchCount -eq 0) {
        Write-Host "    No paths to update" -ForegroundColor Gray
    }
    else {
        Write-Host "    Found $matchCount path references" -ForegroundColor Cyan
    }
    
    if ($DryRun) {
        Write-Host "    [DRY RUN] Would copy to: $destinationPath" -ForegroundColor Cyan
        if ($matchCount -gt 0) {
            Write-Host "    [DRY RUN] Would update $matchCount references" -ForegroundColor Cyan
        }
    }
    else {
        # Update content
        $updatedContent = $originalContent -replace [regex]::Escape($oldPathJson), $newPathJson
        
        # Save to n8n directory
        Set-Content -Path $destinationPath -Value $updatedContent -Encoding UTF8
        Write-Host "    Saved: $destinationPath" -ForegroundColor Green
        
        if ($matchCount -gt 0) {
            Write-Host "    Updated $matchCount path references" -ForegroundColor Green
        }
    }
}

# Summary
Write-Host "`nSUMMARY:" -ForegroundColor Cyan
Write-Host "========" -ForegroundColor Cyan

if ($DryRun) {
    Write-Host "DRY RUN completed - no files modified" -ForegroundColor Yellow
    Write-Host "`nTo apply changes: .\install_n8n.ps1" -ForegroundColor White
}
else {
    Write-Host "Installation completed!" -ForegroundColor Green
    Write-Host "`nOutput: $n8nDir" -ForegroundColor White
    Write-Host "Files:  $($foundFiles.Count)" -ForegroundColor White
    
    Write-Host "`nNext steps:" -ForegroundColor Cyan
    Write-Host "1. Go to n8n folder" -ForegroundColor White
    Write-Host "2. Import workflows into n8n" -ForegroundColor White
    Write-Host "3. Test workflows" -ForegroundColor White
}

Write-Host "`nConfiguration:" -ForegroundColor Cyan
Write-Host "Project:    $newBasePath" -ForegroundColor White
Write-Host "Scripts:    $newBasePath\run_scripts" -ForegroundColor White
Write-Host "Workflows:  $newBasePath\n8n" -ForegroundColor Yellow

Write-Host "`nReady to use!" -ForegroundColor Green