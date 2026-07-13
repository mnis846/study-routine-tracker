@echo off
title Study Routine Tracker
cd /d "%~dp0\.."

echo Stopping any old sticker / website first...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\scripts\stop_all_tracker.ps1" -TrackerOnly >nul 2>&1

echo Starting study website (Streamlit)...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\scripts\start_tracker.ps1"

for /f "delims=" %%P in ('powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\scripts\resolve_python.ps1" -Gui') do set "PY=%%P"
if not defined PY (
    echo Python not found. Install Python 3.10+ and run: pip install -r requirements.txt
    pause
    exit /b 1
)

echo Starting study sticker (Desktop companion / Jupiter / Saturn)...
start "" /min "%PY%" "%~dp0..\desktop_companion.py" --sticker-only
echo.
echo Website + planet sticker are starting.
echo Standalone Desktop companion watcher — use Tracker Control.bat option 2.
exit /b 0