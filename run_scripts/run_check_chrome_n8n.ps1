# Chrome Debug Port Check for n8n - string output for better n8n compatibility
try {
    # variable to hold the TCP client Transmission control protocol
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    # variable to hold the connection check from tcp client
    $connect = $tcpClient.BeginConnect("127.0.0.1", 9222, $null, $null)
    # variable to hold boolean of connection status
    $wait = $connect.AsyncWaitHandle.WaitOne(3000, $false)
    
    # after boolean check if else output string values for n8n
    if ($wait -and $tcpClient.Connected) {
        $tcpClient.Close()
        # Chrome is ready - return string value
        '{"chrome_ready":"true"}'
        exit 0
    }
    else {
        $tcpClient.Close()
        # Chrome not ready - return string value
        '{"chrome_ready":"false"}'
        exit 0
    }
}
catch {
    # Error - return string value
    '{"chrome_ready":"false"}'
    exit 0
}