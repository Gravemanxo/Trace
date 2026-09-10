@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Erstelle lokale Python-Umgebung ...
  where py >nul 2>nul
  if %errorlevel%==0 (
    py -3 -m venv .venv
  ) else (
    python -m venv .venv
  )
  if errorlevel 1 (
    echo.
    echo Python 3 wurde nicht gefunden. Bitte Python von python.org installieren
    echo und dabei "Add Python to PATH" aktivieren.
    pause
    exit /b 1
  )
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
)

start "Trace" http://127.0.0.1:8000
echo Trace laeuft unter http://127.0.0.1:8000
echo Dieses Fenster bitte offen lassen. Zum Beenden Strg+C druecken.
".venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000
pause
