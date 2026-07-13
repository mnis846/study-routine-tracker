# Pin Study Tracker + Study Coach to Windows Startup (runs on login).
$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path $PSScriptRoot -Parent
$Launcher = Join-Path $ProjectRoot "Start Tracker.bat"

if (-not (Test-Path $Launcher)) {
    Write-Error "Launcher not found: $Launcher"
}

$Startup = [Environment]::GetFolderPath("Startup")
$ShortcutPath = Join-Path $Startup "Study Routine Tracker.lnk"

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $Launcher
$Shortcut.WorkingDirectory = $ProjectRoot
$Shortcut.Description = "Study Routine Tracker + Study Coach"
$Shortcut.Save()

Write-Host "Startup shortcut installed:"
Write-Host "  $ShortcutPath"
Write-Host ""
Write-Host "On every login: Streamlit app + always-on-top study sticker (top-right)."
Write-Host "To remove: delete that shortcut from your Startup folder."