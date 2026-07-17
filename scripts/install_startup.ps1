# Install or remove Windows login autostart for Study Routine Tracker.
# Usage:
#   powershell -File scripts\install_startup.ps1           # enable
#   powershell -File scripts\install_startup.ps1 -Remove   # disable
#   powershell -File scripts\install_startup.ps1 -Status   # check
param(
    [switch]$Remove,
    [switch]$Status
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path $PSScriptRoot -Parent
$Launcher = Join-Path $ProjectRoot "Start Tracker.bat"
$Startup = [Environment]::GetFolderPath("Startup")
$ShortcutPath = Join-Path $Startup "Study Routine Tracker.lnk"
$VenvPython = Join-Path $ProjectRoot "venv\Scripts\python.exe"

function Test-Installed {
    return Test-Path $ShortcutPath
}

if ($Status) {
    if (Test-Installed) {
        Write-Host "Autostart: ON"
        Write-Host "  $ShortcutPath"
    } else {
        Write-Host "Autostart: OFF"
    }
    exit 0
}

if ($Remove) {
    if (Test-Installed) {
        Remove-Item -LiteralPath $ShortcutPath -Force
        Write-Host "Autostart removed."
        Write-Host "The tracker will no longer start when Windows logs in."
    } else {
        Write-Host "Autostart was not installed (nothing to remove)."
    }
    exit 0
}

if (-not (Test-Path $Launcher)) {
    Write-Error "Launcher not found: $Launcher"
}

if (-not (Test-Path $VenvPython)) {
    Write-Host "WARNING: Project venv not found at:"
    Write-Host "  $VenvPython"
    Write-Host "Run install steps first (python -m venv venv, pip install -r requirements.txt)"
    Write-Host "or Start Tracker.bat may fail at login."
    Write-Host ""
}

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $Launcher
$Shortcut.WorkingDirectory = $ProjectRoot
$Shortcut.WindowStyle = 7  # Minimized
$Shortcut.Description = "Study Routine Tracker (starts on Windows login)"
$Shortcut.Save()

Write-Host "Autostart enabled."
Write-Host "  Shortcut: $ShortcutPath"
Write-Host ""
Write-Host "On every Windows login the tracker will start in the background"
Write-Host "and open http://localhost:8501 when ready."
Write-Host ""
Write-Host "To turn it off later:"
Write-Host "  - Tracker Control.bat  →  Remove autostart"
Write-Host "  - Or:  powershell -File scripts\install_startup.ps1 -Remove"
Write-Host "  - Or delete the Startup shortcut above."
