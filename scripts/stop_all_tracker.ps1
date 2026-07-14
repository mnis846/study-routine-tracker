# Stop tracker desktop apps and/or the Streamlit website.
param(
    [switch]$StickerOnly,
    [switch]$TrackerOnly
)

$ErrorActionPreference = "SilentlyContinue"
. (Join-Path $PSScriptRoot "tracker_processes.ps1")

$keys = @()
if ($StickerOnly) { $keys += "sticker" }
elseif ($TrackerOnly) { $keys += "sticker", "streamlit" }
# default: stop everything

$patterns = Get-TrackerPatterns -Keys $(if ($keys.Count) { $keys } else { $null })
$running = Get-TrackerProcesses | Where-Object {
    $cmd = $_.CommandLine
    $patterns | Where-Object { $cmd -like $_ }
}

if (-not $running) {
    Write-Host "No matching tracker processes running."
    exit 0
}

Write-Host "Stopping:"
$killed = 0
foreach ($item in $running) {
    Write-Host "  - $($item.Name) (PID $($item.ProcessId))"
    Stop-Process -Id $item.ProcessId -Force
    $killed++
}

Write-Host ""
Write-Host "Stopped $killed process(es)."
