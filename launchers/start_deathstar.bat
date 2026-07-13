@echo off
title Start Desktop companion Watcher
cd /d "%~dp0\.."

echo Stopping any old Desktop companion first...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\scripts\stop_all_tracker.ps1" -DeathStarOnly >nul 2>&1

for /f "delims=" %%P in ('powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\scripts\resolve_python.ps1" -Gui') do set "PY=%%P"
if not defined PY (
    echo Python not found. Install Python 3.10+ and run: pip install -r requirements.txt
    pause
    exit /b 1
)

start "" /min "%PY%" "%~dp0..\deathstar_watcher.py"
echo.
echo Desktop companion started (top-right). Does NOT start the study website.
echo Open website from tray - Open tracker - if you need Streamlit.
echo Quit: X button, Esc, middle-click, tray Quit, or Tracker Control option 5.
exit /b 0