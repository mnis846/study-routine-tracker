# Show which tracker apps are currently running.
$ErrorActionPreference = "SilentlyContinue"
. (Join-Path $PSScriptRoot "tracker_processes.ps1")

Write-Host ""
Write-Host "=== Study Tracker - what is running ===" -ForegroundColor Cyan
Write-Host ""

$running = Get-TrackerProcesses
if (-not $running) {
    Write-Host "Nothing from this project is running." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Apps you can start (each is separate):"
    foreach ($def in $script:TrackerProcessDefs) {
        Write-Host "  - $($def.Name)"
    }
    Write-Host ""
    Write-Host "Desktop companion and Vader sticker run without the website unless you"
    Write-Host "used Start Tracker (option 1) or clicked Open tracker in the tray."
    Write-Host ""
    exit 0
}

$running | Group-Object Key | ForEach-Object {
    $item = $_.Group[0]
    Write-Host "RUNNING: $($item.Name)" -ForegroundColor Green
    foreach ($p in $_.Group) {
        Write-Host "          PID $($p.ProcessId)"
    }
}

$allKeys = $script:TrackerProcessDefs | ForEach-Object { $_.Key }
$runningKeys = $running | ForEach-Object { $_.Key } | Select-Object -Unique
$stopped = $allKeys | Where-Object { $_ -notin $runningKeys }
if ($stopped) {
    Write-Host ""
    Write-Host "Not running:" -ForegroundColor DarkGray
    foreach ($key in $stopped) {
        $name = ($script:TrackerProcessDefs | Where-Object Key -eq $key).Name
        Write-Host "  - $name" -ForegroundColor DarkGray
    }
}

Write-Host ""
Write-Host "Tip: use Tracker Control.bat (or launchers\control.bat) to stop specific apps." -ForegroundColor DarkGray
Write-Host ""