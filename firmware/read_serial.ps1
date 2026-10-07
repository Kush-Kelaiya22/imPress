$port = $args[0]
$s = New-Object System.IO.Ports.SerialPort($port, 115200)
$s.ReadTimeout = 1000
$s.Open()
$s.DtrEnable = $true
$s.RtsEnable = $true
Start-Sleep -Seconds 7
$buf = ''
while ($s.BytesToRead -gt 0) {
    try { $buf += $s.ReadExisting() } catch { break }
}
"$buf"
$s.Close()