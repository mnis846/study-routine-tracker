# Creates a Desktop shortcut for one-click launch.
$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path $PSScriptRoot -Parent
$Launcher = Join-Path $ProjectRoot "Start Tracker.bat"
$Icon = Join-Path $env:SystemRoot "System32\imageres.dll"

if (-not (Test-Path $Launcher)) {
    Write-Error "Launcher not found: $Launcher"
}

$WshShell = New-Object -ComObject WScript.Shell
$Desktop = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $Desktop "CGPSC Mains Tracker.lnk"

$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $Launcher
$Shortcut.WorkingDirectory = $ProjectRoot
$Shortcut.Description = "Launch CGPSC Mains Tracker"
$Shortcut.IconLocation = "$Icon,109"
$Shortcut.Save()

Write-Host "Desktop shortcut created:"
Write-Host "  $ShortcutPath"
Write-Host "Right-click it and choose Pin to taskbar for fastest access."