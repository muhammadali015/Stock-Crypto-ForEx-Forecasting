@echo off
echo Starting FinTech Forecasting Application...
echo.

echo Starting Backend (SQLite)...
start "Backend" cmd /k "cd /d %~dp0 && python backend/app_sqlite.py"

echo Waiting for backend to start...
timeout /t 5 /nobreak > nul

echo Starting Frontend...
start "Frontend" cmd /k "cd /d %~dp0\frontend && npm start"

echo.
echo Application is starting...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Press any key to exit...
pause > nul
