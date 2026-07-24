@echo off
REM Export Streamlit SQLite progress to a JSON file for the Android app
cd /d "%~dp0"
echo.
echo  Exporting your Study Routine Tracker data for Android...
echo.
if exist "venv\Scripts\python.exe" (
  "venv\Scripts\python.exe" scripts\export_to_android.py
) else (
  python scripts\export_to_android.py
)
echo.
echo  Look for the file in the "exports" folder.
echo  Copy it to your phone, then: Study Tracker → More → Restore backup
echo.
pause
