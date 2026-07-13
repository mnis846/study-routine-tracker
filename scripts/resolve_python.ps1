# Resolve one Python executable for tracker launchers (prefer real install over Store stub).
$preferGui = $args -contains "-Gui"
$suffix = if ($preferGui) { "pythonw.exe" } else { "python.exe" }

$candidates = @(
    (Join-Path $env:LOCALAPPDATA "Python\pythoncore-3.14-64\$suffix"),
    (Join-Path $env:LOCALAPPDATA "Programs\Python\Python313\$suffix"),
    (Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\$suffix")
)

foreach ($path in $candidates) {
    if (Test-Path $path) {
        Write-Output $path
        exit 0
    }
}

$cmdName = if ($preferGui) { "pythonw" } else { "python" }
$cmd = Get-Command $cmdName -ErrorAction SilentlyContinue
if ($cmd -and $cmd.Source -notlike "*WindowsApps*") {
    Write-Output $cmd.Source
    exit 0
}

if ($preferGui) {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd -and $cmd.Source -notlike "*WindowsApps*") {
        Write-Output $cmd.Source
        exit 0
    }
}

$launcher = Get-Command py -ErrorAction SilentlyContinue
if ($launcher) {
    Write-Output "$($launcher.Source) -3"
    exit 0
}

if ($cmd) {
    Write-Output $cmd.Source
    exit 0
}

exit 1