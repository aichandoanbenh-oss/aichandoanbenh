@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Run setup.bat first.
  pause
  exit /b 1
)
echo Open http://127.0.0.1:8000 - press Ctrl+C to stop.
".venv\Scripts\python.exe" -m uvicorn web.app:app --host 127.0.0.1 --port 8000
if errorlevel 1 pause
