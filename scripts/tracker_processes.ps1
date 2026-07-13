# Shared definitions for tracker desktop apps and the Streamlit website.
$script:TrackerProcessDefs = @(
    @{
        Key     = "streamlit"
        Name    = "Study website (Streamlit)"
        Pattern = "*streamlit*app.py*"
        Exe     = "python.exe"
    },
    @{
        Key     = "sticker"
        Name    = "Study sticker"
        Pattern = "*desktop_companion*"
        Exe     = "pythonw.exe"
    },
    @{
        Key     = "deathstar"
        Name    = "Desktop companion watcher"
        Pattern = "*deathstar_watcher*"
        Exe     = "pythonw.exe"
    }
)

function Get-TrackerProcesses {
    $found = @()
    foreach ($proc in Get-CimInstance Win32_Process) {
        $cmd = $proc.CommandLine
        if (-not $cmd) { continue }
        foreach ($def in $script:TrackerProcessDefs) {
            if ($cmd -like $def.Pattern) {
                $found += [PSCustomObject]@{
                    Key       = $def.Key
                    Name      = $def.Name
                    ProcessId = $proc.ProcessId
                    CommandLine = $cmd
                }
                break
            }
        }
    }
    return $found
}

function Get-TrackerPatterns {
    param([string[]]$Keys)
    $defs = if ($Keys) {
        $script:TrackerProcessDefs | Where-Object { $_.Key -in $Keys }
    } else {
        $script:TrackerProcessDefs
    }
    return @($defs | ForEach-Object { $_.Pattern })
}