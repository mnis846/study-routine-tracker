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
echo   WHAT EACH APP IS:
echo   [1] Tracker      = Website (Streamlit) + Vader sticker
echo   [2] Desktop companion   = Desktop watcher ONLY (no website)
echo.
echo   Sticker and Desktop companion do NOT share one process.
echo.
echo   --- START ---
echo   1. Start Tracker (website + Vader sticker)
echo   2. Start Desktop companion watcher only
echo.
echo   --- STATUS / STOP ---
echo   3. Show what is running now
echo   4. Stop EVERYTHING (website + sticker + death star)
echo   5. Stop Desktop companion only
echo   6. Stop Tracker only (website + Vader sticker)
echo.
echo   0. Exit
echo.
set /p choice="Choose 0-6: "

if "%choice%"=="1" goto start_tracker
if "%choice%"=="2" goto start_deathstar
if "%choice%"=="3" goto status
if "%choice%"=="4" goto stop_all
if "%choice%"=="5" goto stop_deathstar
if "%choice%"=="6" goto stop_tracker
if "%choice%"=="0" exit /b 0
goto menu

:start_tracker
call "%~dp0start_tracker.bat"
goto pause_return

:start_deathstar
call "%~dp0start_deathstar.bat"
goto pause_return

:status
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\scripts\status_tracker.ps1"
goto pause_return

:stop_all
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\scripts\stop_all_tracker.ps1"
goto pause_return

:stop_deathstar
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\scripts\stop_all_tracker.ps1" -DeathStarOnly
goto pause_return

:stop_tracker
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\scripts\stop_all_tracker.ps1" -TrackerOnly
goto pause_return

:pause_return
echo.
pause
goto menu