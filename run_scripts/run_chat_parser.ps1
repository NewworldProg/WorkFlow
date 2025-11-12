$projectRoot = Split-Path $PSScriptRoot -Parent
# Chat Parser for n8n
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Set-Location $projectRoot
Write-Host "Starting Chat Parser..."

try {
    # Activate venv if it exists
    if (Test-Path "venv\Scripts\Activate.ps1") {
        & "venv\Scripts\Activate.ps1"
    }
    
    # Run chat parser
    $process = Start-Process -FilePath "python" -ArgumentList "scripts\chat_parser.py --latest" -PassThru -NoNewWindow -Wait
    
    if ($process.ExitCode -eq 0) {
        Write-Host "Chat parser completed successfully"
        exit 0
    }
    else {
        Write-Host "Chat parser failed with exit code: $($process.ExitCode)"
        exit 1
    }
}
catch {
    Write-Host "Error running chat parser: $($_.Exception.Message)"
    exit 1
}