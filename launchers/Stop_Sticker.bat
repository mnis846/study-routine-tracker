@echo off
cd /d "%~dp0.."
powershell -NoProfile -ExecutionPolicy Bypass -File "%cd%\scripts\stop_sticker.ps1"
