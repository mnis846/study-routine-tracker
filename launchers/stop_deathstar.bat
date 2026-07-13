@echo off
title Stop Desktop companion Watcher
cd /d "%~dp0\.."
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\scripts\stop_all_tracker.ps1" -DeathStarOnly
echo.
pause