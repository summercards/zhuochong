param(
    [Parameter(Mandatory = $true)]
    [string]$Json,
    [int]$TimeoutMs = 600000
)

$client = [System.Net.Sockets.TcpClient]::new()
$client.Connect("127.0.0.1", 9876)
$stream = $client.GetStream()
$stream.ReadTimeout = $TimeoutMs
$stream.WriteTimeout = $TimeoutMs

$bytes = [System.Text.Encoding]::UTF8.GetBytes($Json)
$stream.Write($bytes, 0, $bytes.Length)
$stream.Flush()

$buffer = New-Object byte[] 65536
$memory = [System.IO.MemoryStream]::new()

try {
    while ($true) {
        $read = $stream.Read($buffer, 0, $buffer.Length)
        if ($read -le 0) {
            break
        }
        $memory.Write($buffer, 0, $read)
        $text = [System.Text.Encoding]::UTF8.GetString($memory.ToArray())
        try {
            $parsed = $text | ConvertFrom-Json
            $parsed | ConvertTo-Json -Depth 100
            break
        }
        catch {
            Start-Sleep -Milliseconds 40
        }
    }
}
finally {
    $memory.Dispose()
    $stream.Dispose()
    $client.Dispose()
}
