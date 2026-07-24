@echo off
REM Disable Study Routine Tracker on Windows login
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\install_startup.ps1" -Remove
echo.
pause
