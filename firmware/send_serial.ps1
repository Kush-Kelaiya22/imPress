$port = $args[0]
$text = $args[1]
$s = New-Object System.IO.Ports.SerialPort($port, 115200)
$s.WriteTimeout = 1000
$s.ReadTimeout = 1000
$s.Open()
$s.DtrEnable = $true
$s.RtsEnable = $true
$s.Write($text + "`r`n")
Start-Sleep -Seconds 6
$buf = ''
while ($s.BytesToRead -gt 0) {
    try { $buf += $s.ReadExisting() } catch { break }
}
"$buf"
$s.Close()