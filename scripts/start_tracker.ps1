# One-click launcher - double-click "Start Tracker.bat" or run this script.
$ErrorActionPreference = "Continue"
$ProjectRoot = Split-Path $PSScriptRoot -Parent
Set-Location $ProjectRoot

$Port = 8501
$Url = "http://localhost:$Port"
$LogFile = Join-Path $ProjectRoot "tracker-launch.log"

function Write-Log([string]$Message) {
    $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $Message"
    Add-Content -Path $LogFile -Value $line
    Write-Host $Message
}

function Test-PortOpen([int]$TargetPort) {
    try {
        $conn = Get-NetTCPConnection -LocalPort $TargetPort -State Listen -ErrorAction SilentlyContinue
        return [bool]$conn
    } catch {
        return $false
    }
}

function Resolve-Python {
    $py = Get-Command python -ErrorAction SilentlyContinue
    if ($py) { return $py.Source }
    $launcher = Get-Command py -ErrorAction SilentlyContinue
    if ($launcher) { return "$($launcher.Source) -3" }
    $local = Join-Path $env:LOCALAPPDATA "Programs\Python\Python313\python.exe"
    if (Test-Path $local) { return $local }
    $local314 = Join-Path $env:LOCALAPPDATA "Microsoft\WindowsApps\python.exe"
    if (Test-Path $local314) { return $local314 }
    return $null
}

Write-Log "Launch requested from $ProjectRoot"

if (Test-PortOpen $Port) {
    Write-Log "Server already on port $Port - opening browser"
    Start-Process $Url
    exit 0
}

$pythonCmd = Resolve-Python
if (-not $pythonCmd) {
    Write-Log "ERROR: Python not found in PATH"
    Write-Host ""
    Write-Host "Python not found. Install Python 3.10+ then run:"
    Write-Host "  pip install -r requirements.txt"
    exit 1
}

Write-Log "Using Python: $pythonCmd"
Write-Log "Starting Streamlit..."

if ($pythonCmd -like "* -3") {
    $parts = $pythonCmd -split " ", 2
    $exe = $parts[0]
    $argPrefix = @($parts[1])
} else {
    $exe = $pythonCmd
    $argPrefix = @()
}

$streamlitArgs = $argPrefix + @(
    "-m", "streamlit", "run", "app.py",
    "--server.headless", "true",
    "--server.port", "$Port"
)

Start-Process -FilePath $exe `
    -ArgumentList $streamlitArgs `
    -WorkingDirectory $ProjectRoot `
    -WindowStyle Minimized | Out-Null

$deadline = (Get-Date).AddSeconds(45)
while ((Get-Date) -lt $deadline) {
    if (Test-PortOpen $Port) {
        Start-Sleep -Seconds 1
        Start-Process $Url
        Write-Log "Ready at $Url"
        exit 0
    }
    Start-Sleep -Milliseconds 500
}

Write-Log "ERROR: Server did not start within 45 seconds"
Write-Host ""
Write-Host "Server did not start. Try manually:"
Write-Host "  cd $ProjectRoot"
Write-Host "  python -m streamlit run app.py"
Write-Host ""
Write-Host "Log: $LogFile"
exit 1