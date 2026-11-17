$proj = "C:\Users\b6829162\Documents\Default Project\transistor-simulator"
$up = $false
try {
    $r = Invoke-WebRequest -Uri 'http://127.0.0.1:5000/' -TimeoutSec 2 -UseBasicParsing
    $up = ($r.StatusCode -eq 200)
} catch { $up = $false }
if (-not $up) {
    Start-Process -FilePath "$proj\.venv\Scripts\pythonw.exe" `
        -ArgumentList "-m","flask","--app","app","run","--host","127.0.0.1","--port","5000" `
        -WorkingDirectory $proj -WindowStyle Hidden
}
