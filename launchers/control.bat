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
echo   1. Start Tracker
echo   2. Show what is running
echo   3. Stop everything
echo   4. Stop desktop coach only
echo   5. Stop website only
echo   6. Install autostart (run on Windows login)
echo   7. Remove autostart
echo   8. Autostart status
echo.
echo   0. Exit
echo.
set /p choice="Choose 0-8: "

if "%choice%"=="1" goto start_tracker
if "%choice%"=="2" goto status
if "%choice%"=="3" goto stop_all
if "%choice%"=="4" goto stop_sticker
if "%choice%"=="5" goto stop_tracker
if "%choice%"=="6" goto install_startup
if "%choice%"=="7" goto remove_startup
if "%choice%"=="8" goto status_startup
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

:install_startup
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\scripts\install_startup.ps1"
goto pause_return

:remove_startup
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\scripts\install_startup.ps1" -Remove
goto pause_return

:status_startup
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\scripts\install_startup.ps1" -Status
goto pause_return

:pause_return
echo.
pause
goto menu
