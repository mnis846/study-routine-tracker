@echo off
REM Enable Study Routine Tracker on Windows login
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\install_startup.ps1"
echo.
pause
