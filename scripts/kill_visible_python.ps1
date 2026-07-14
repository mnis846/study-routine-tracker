# Kill desktop tracker python processes (broad match).
$ErrorActionPreference = "SilentlyContinue"
$patterns = @("*desktop_companion*", "*streamlit*app.py*", "*study_routine*")

Write-Host ""
Write-Host "All python / pythonw processes:"
Get-CimInstance Win32_Process |
    Where-Object { $_.Name -in @("python.exe", "pythonw.exe") } |
    ForEach-Object {
        $cmd = $_.CommandLine
        if (-not $cmd) { $cmd = "(no command line)" }
        Write-Host "  PID $($_.ProcessId): $cmd"
    }

Write-Host ""
Write-Host "Stopping tracker-related processes..."
$killed = 0
Get-CimInstance Win32_Process |
    Where-Object {
        $_.Name -in @("python.exe", "pythonw.exe") -and $_.CommandLine -and
        ($patterns | Where-Object { $_.CommandLine -like $_ })
    } |
    ForEach-Object {
        Write-Host "  Killing PID $($_.ProcessId)"
        Stop-Process -Id $_.ProcessId -Force
        $killed++
    }

if ($killed -eq 0) {
    Write-Host ""
    Write-Host "No command-line match. Killing ALL pythonw.exe (desktop widgets use this)..."
    Get-Process pythonw -ErrorAction SilentlyContinue | ForEach-Object {
        Write-Host "  Killing pythonw PID $($_.Id)"
        Stop-Process -Id $_.Id -Force
        $killed++
    }
}

Write-Host ""
Write-Host "Stopped $killed process(es)."
Write-Host ""
