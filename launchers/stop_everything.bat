@echo off
title Stop All Tracker Apps
cd /d "%~dp0\.."
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\scripts\stop_all_tracker.ps1"
echo.
pause