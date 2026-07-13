@echo off
title Study Routine Tracker
cd /d "%~dp0"

echo Stopping any old sticker first...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\stop_sticker.ps1" >nul 2>&1
echo Starting Study Routine Tracker + Study Coach...
start "" /min pythonw "%~dp0desktop_companion.py" 2>nul
if errorlevel 1 start "" /min python "%~dp0desktop_companion.py"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start_tracker.ps1"
set ERR=%ERRORLEVEL%

if %ERR% NEQ 0 (
    echo.
    echo Launch failed ^(exit code %ERR%^).
    echo Check tracker-launch.log in this folder.
    echo.
    pause
    exit /b %ERR%
)

exit /b 0