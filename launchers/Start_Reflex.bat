@echo off
title Study Tracker (Reflex)
cd /d "%~dp0.."
if exist "venv\Scripts\activate.bat" call "venv\Scripts\activate.bat"
reflex run
if errorlevel 1 pause
