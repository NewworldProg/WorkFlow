$projectRoot = Split-Path $PSScriptRoot -Parent
# Chrome Chat Status Check - Identical to working version
# Checks if Chrome is running with debug port 9223 for chat

try {
    Set-Location $projectRoot
    
    # Set UTF-8 encoding
    $OutputEncoding = [System.Text.Encoding]::UTF8
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    
    # variable to hold the TCP client Transmission control protocol
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    # variable to hold the connection check from tcp client - PORT 9223 for chat
    $connect = $tcpClient.BeginConnect("127.0.0.1", 9223, $null, $null)
    # variable to hold boolean of connection status
    $wait = $connect.AsyncWaitHandle.WaitOne(3000, $false)
    
    # after boolean check if else output string values for n8n
    if ($wait -and $tcpClient.Connected) {
        $tcpClient.Close()
        # Chrome chat is ready - return string value (IMPORTANT: string not boolean!)
        '{"chrome_ready":"true"}'
        exit 0
    }
    else {
        $tcpClient.Close()
        # Chrome chat not ready - return string value
        '{"chrome_ready":"false"}'
        exit 0
    }
}
catch {
    # Error - return string value
    '{"chrome_ready":"false"}'
    exit 0
}