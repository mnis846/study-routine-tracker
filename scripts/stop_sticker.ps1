# Stop all running study sticker / desktop companion processes.
$ErrorActionPreference = "SilentlyContinue"
$killed = 0

Get-CimInstance Win32_Process |
    Where-Object {
        $_.CommandLine -and $_.CommandLine -like "*desktop_companion*"
    } |
    ForEach-Object {
        Stop-Process -Id $_.ProcessId -Force
        $killed++
        Write-Host "Stopped PID $($_.ProcessId)"
    }

if ($killed -eq 0) {
    Write-Host "No study sticker running."
} else {
    Write-Host "Stopped $killed sticker process(es)."
}
Write-Host ""
Write-Host "Tip: also right-click the tray icon -> Quit sticker"