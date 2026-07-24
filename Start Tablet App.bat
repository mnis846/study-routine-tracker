@echo off
REM Serve the offline tablet PWA on the local network (for first install / use).
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\serve_tablet_app.ps1"
pause
