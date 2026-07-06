# Import phone database sync file into the PC tracker.
# Usage: .\scripts\import_db.ps1 -SyncFile "D:\Downloads\cgpsc_mains_tracker_sync_20260702.db"

param(
    [Parameter(Mandatory = $true)]
    [string]$SyncFile
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

if (-not (Test-Path $SyncFile)) {
    Write-Error "Sync file not found: $SyncFile"
}

python -c @"
from sync import import_database
result = import_database(r'$SyncFile')
print('Imported to:', result['imported_to'])
if result.get('backup_path'):
    print('PC backup saved:', result['backup_path'])
"@

Write-Host ""
Write-Host "Done. Restart Streamlit if it is running, then refresh the browser."