@echo off
title Stop Vader Sticker + Website
cd /d "%~dp0\.."
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\scripts\stop_all_tracker.ps1" -TrackerOnly
echo.
pause