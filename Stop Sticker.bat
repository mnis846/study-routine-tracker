@echo off
title Stop CGPSC Study Sticker
cd /d "%~dp0"
echo Stopping old study sticker...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\stop_sticker.ps1"
echo.
pause