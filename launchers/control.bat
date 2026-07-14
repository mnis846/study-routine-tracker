@echo off
title Study Tracker Control
cd /d "%~dp0\.."

:menu
cls
echo.
echo  ========================================
echo   Study Tracker Control
echo  ========================================
echo.
echo   1. Start Tracker (website + desktop coach)
echo   2. Show what is running
echo   3. Stop everything
echo   4. Stop desktop coach only
echo   5. Stop website only
echo.
echo   0. Exit
echo.
set /p choice="Choose 0-5: "

if "%choice%"=="1" goto start_tracker
if "%choice%"=="2" goto status
if "%choice%"=="3" goto stop_all
if "%choice%"=="4" goto stop_sticker
if "%choice%"=="5" goto stop_tracker
if "%choice%"=="0" exit /b 0
goto menu

:start_tracker
call "%~dp0Start_Tracker.bat"
goto pause_return

:status
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\scripts\status_tracker.ps1"
goto pause_return

:stop_all
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\scripts\stop_all_tracker.ps1"
goto pause_return

:stop_sticker
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\scripts\stop_all_tracker.ps1" -StickerOnly
goto pause_return

:stop_tracker
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\scripts\stop_all_tracker.ps1" -TrackerOnly
goto pause_return

:pause_return
echo.
pause
goto menu
