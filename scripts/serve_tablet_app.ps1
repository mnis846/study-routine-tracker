# Serve tablet-app/ so a phone or tablet on the same Wi-Fi can open and install it.
# Data always saves in the tablet browser / installed PWA (not on this PC).

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path $PSScriptRoot -Parent
$AppDir = Join-Path $ProjectRoot "tablet-app"
$Port = 8765

if (-not (Test-Path (Join-Path $AppDir "index.html"))) {
    Write-Error "tablet-app/index.html not found at $AppDir"
}

function Get-LanIPv4 {
    try {
        $addrs = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
            Where-Object {
                $_.IPAddress -notlike "127.*" -and
                $_.IPAddress -notlike "169.254.*" -and
                $_.PrefixOrigin -ne "WellKnown"
            }
        if ($addrs) { return ($addrs | Select-Object -First 1).IPAddress }
    } catch {}
    try {
        $line = ipconfig | Select-String -Pattern "IPv4" | Select-Object -First 1
        if ($line -match "(\d+\.\d+\.\d+\.\d+)") { return $Matches[1] }
    } catch {}
    return "YOUR-PC-IP"
}

$ip = Get-LanIPv4
Write-Host ""
Write-Host "Study Tracker — tablet app server"
Write-Host "================================"
Write-Host "Folder: $AppDir"
Write-Host ""
Write-Host "On this PC:     http://localhost:$Port/"
Write-Host "On the tablet:  http://${ip}:$Port/"
Write-Host ""
Write-Host "Tablet steps:"
Write-Host "  1. Join the same Wi-Fi as this PC"
Write-Host "  2. Open the tablet URL in Chrome"
Write-Host "  3. Menu (three dots) -> Install app / Add to Home screen"
Write-Host "  4. After install, the app works offline; study data stays on the tablet"
Write-Host ""
Write-Host "Press Ctrl+C to stop the server."
Write-Host ""

Set-Location $AppDir

$python = $null
foreach ($rel in @("venv\Scripts\python.exe", ".venv\Scripts\python.exe")) {
    $candidate = Join-Path $ProjectRoot $rel
    if (Test-Path $candidate) { $python = $candidate; break }
}
if (-not $python) {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) { $python = $cmd.Source }
}

if ($python) {
    & $python -m http.server $Port --bind 0.0.0.0
} else {
    Write-Host "Python not found — using PowerShell listener (Ctrl+C to stop)."
    $listener = [System.Net.HttpListener]::new()
    $listener.Prefixes.Add("http://+:$Port/")
    try {
        $listener.Start()
    } catch {
        $listener = [System.Net.HttpListener]::new()
        $listener.Prefixes.Add("http://localhost:$Port/")
        $listener.Start()
        Write-Host "Bound: bound to localhost only. Allow firewall / run as admin for LAN."
    }
    $mime = @{
        ".html" = "text/html; charset=utf-8"
        ".js"   = "application/javascript; charset=utf-8"
        ".css"  = "text/css; charset=utf-8"
        ".json" = "application/json"
        ".webmanifest" = "application/manifest+json"
        ".svg"  = "image/svg+xml"
        ".png"  = "image/png"
        ".ico"  = "image/x-icon"
    }
    while ($listener.IsListening) {
        $ctx = $listener.GetContext()
        $path = $ctx.Request.Url.LocalPath.TrimStart("/")
        if ([string]::IsNullOrWhiteSpace($path)) { $path = "index.html" }
        $file = Join-Path $AppDir ($path -replace "/", [IO.Path]::DirectorySeparatorChar)
        if (-not (Test-Path $file) -or (Get-Item $file).PSIsContainer) {
            $ctx.Response.StatusCode = 404
            $buf = [Text.Encoding]::UTF8.GetBytes("Not found")
            $ctx.Response.OutputStream.Write($buf, 0, $buf.Length)
            $ctx.Response.Close()
            continue
        }
        $bytes = [IO.File]::ReadAllBytes($file)
        $ext = [IO.Path]::GetExtension($file).ToLowerInvariant()
        $ctx.Response.ContentType = $(if ($mime.ContainsKey($ext)) { $mime[$ext] } else { "application/octet-stream" })
        $ctx.Response.ContentLength64 = $bytes.Length
        $ctx.Response.OutputStream.Write($bytes, 0, $bytes.Length)
        $ctx.Response.Close()
    }
}
