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
    # Prefer project venv so README install steps work with double-click launch.
    foreach ($rel in @("venv\Scripts\python.exe", ".venv\Scripts\python.exe")) {
        $candidate = Join-Path $ProjectRoot $rel
        if (Test-Path $candidate) { return $candidate }
    }

    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd -and $cmd.Source -notlike "*WindowsApps*") { return $cmd.Source }

    $launcher = Get-Command py -ErrorAction SilentlyContinue
    if ($launcher) { return "$($launcher.Source) -3" }

    foreach ($path in @(
        (Join-Path $env:LOCALAPPDATA "Python\pythoncore-3.14-64\python.exe"),
        (Join-Path $env:LOCALAPPDATA "Programs\Python\Python313\python.exe"),
        (Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\python.exe")
    )) {
        if (Test-Path $path) { return $path }
    }

    if ($cmd) { return $cmd.Source }
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
    Write-Log "ERROR: Python not found"
    Write-Host ""
    Write-Host "Install Python 3.10+, then run:"
    Write-Host "  python -m venv venv"
    Write-Host "  venv\Scripts\activate"
    Write-Host "  pip install -r requirements.txt"
    Write-Host "  streamlit run app.py"
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

# Fail fast if streamlit is missing in the chosen Python.
$check = & $exe @($argPrefix + @("-c", "import streamlit")) 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Log "ERROR: streamlit not installed for $pythonCmd"
    Write-Host ""
    Write-Host "Install dependencies first:"
    Write-Host "  python -m venv venv"
    Write-Host "  venv\Scripts\activate"
    Write-Host "  pip install -r requirements.txt"
    exit 1
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
Write-Host "  venv\Scripts\activate"
Write-Host "  streamlit run app.py"
Write-Host ""
Write-Host "Log: $LogFile"
exit 1
