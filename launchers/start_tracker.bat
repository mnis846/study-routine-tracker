@echo off
title Study Routine Tracker
cd /d "%~dp0.."

echo Starting Study Routine Tracker...
powershell -NoProfile -ExecutionPolicy Bypass -File "%cd%\scripts\start_tracker.ps1"
set ERR=%ERRORLEVEL%

if %ERR% NEQ 0 (
    echo.
    echo Launch failed ^(exit code %ERR%^).
    echo Check tracker-launch.log in this folder.
    echo.
    echo Or run manually:
    echo   venv\Scripts\activate
    echo   streamlit run app.py
    echo.
    pause
    exit /b %ERR%
)

exit /b 0
