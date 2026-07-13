@echo off
title Tracker Status
cd /d "%~dp0\.."
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\scripts\status_tracker.ps1"
pause