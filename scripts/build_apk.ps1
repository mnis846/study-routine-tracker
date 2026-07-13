# Build Study Routine Tracker Android APK with Flet (Windows/macOS/Linux).
# Prerequisites: Python 3.10+, JDK 17, Android SDK, Flutter (installed by Flet).

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$JavaHome = Join-Path $env:USERPROFILE "java\17.0.13+11"
if (Test-Path $JavaHome) {
    $env:JAVA_HOME = $JavaHome
    $env:PATH = "$JavaHome\bin;$env:PATH"
}

Write-Host "Installing build dependencies..."
python -m pip install --upgrade pip
python -m pip install "flet[all]>=0.27.0" "pandas>=2.0.0,<3"

$AndroidHome = Join-Path $env:USERPROFILE "Android\sdk"
$env:ANDROID_HOME = $AndroidHome
$env:ANDROID_SDK_ROOT = $AndroidHome

$sdkManager = Join-Path $AndroidHome "cmdline-tools\12.0\bin\sdkmanager.bat"
if (Test-Path $sdkManager) {
    Write-Host "Accepting Android SDK licenses and installing build packages..."
    $yes = ("y`n" * 40)
    $yes | & $sdkManager --licenses | Out-Null
    & $sdkManager "platform-tools" "platforms;android-36" "build-tools;36.0.0" | Out-Null
}

$PythonScripts = python -c "import os, sys; print(os.path.join(sys.prefix, 'Scripts'))"
$FletExe = Join-Path $PythonScripts "flet.exe"
if (-not (Test-Path $FletExe)) {
    Write-Error "flet.exe not found at $FletExe. Re-run pip install step."
}

Write-Host "Packaging Python app and generating Flutter project..."
& $FletExe build apk . `
    --module-name main `
    --bundle-id com.study.routinetracker `
    --product "Study Routine Tracker" `
    --org com.study.routinetracker `
    --split-per-abi `
    --yes `
    --verbose

$FlutterDir = Join-Path $Root "build\flutter"
$SitePackages = Join-Path $Root "build\site-packages"

if (-not (Test-Path $FlutterDir)) {
    Write-Error "Flutter project not found at $FlutterDir. Flet packaging step failed."
}

# Windows: Flutter plugin symlinks need Developer Mode or junction repair.
if ($IsWindows -or $env:OS -like "*Windows*") {
    $FlutterBin = Join-Path $env:USERPROFILE "flutter\3.41.7\bin"
    if (-not (Test-Path $FlutterBin)) {
        $FlutterBin = (Get-Command flutter -ErrorAction SilentlyContinue).Source
        if ($FlutterBin) {
            $FlutterBin = Split-Path -Parent $FlutterBin
        }
    }
    if ($FlutterBin -and (Test-Path (Join-Path $FlutterBin "flutter.bat"))) {
        $env:PATH = "$FlutterBin;$env:PATH"
    }

    Write-Host "Repairing Flutter plugin links (Windows junction workaround)..."
    Push-Location $FlutterDir
    try {
        dart pub add --dev win_plugin_link_repair 2>$null
        dart run win_plugin_link_repair
    } finally {
        Pop-Location
    }
}

$env:SERIOUS_PYTHON_SITE_PACKAGES = $SitePackages

Write-Host "Building Android APK (Gradle)..."
Push-Location $FlutterDir
try {
    flutter build apk --split-per-abi --build-name 1.0.0
} finally {
    Pop-Location
}

$ApkDirs = @(
    (Join-Path $FlutterDir "build\app\outputs\flutter-apk"),
    (Join-Path $Root "build\apk")
)

Write-Host ""
Write-Host "APK output:"
$found = $false
foreach ($dir in $ApkDirs) {
    if (Test-Path $dir) {
        Get-ChildItem -Path $dir -Recurse -Filter "*.apk" -ErrorAction SilentlyContinue |
            ForEach-Object {
                $found = $true
                $_.FullName
            }
    }
}
if (-not $found) {
    Write-Host "No APK files found. Check build logs above."
}