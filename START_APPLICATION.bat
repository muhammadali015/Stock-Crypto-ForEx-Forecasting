@echo off
echo ========================================
echo  FinTech Forecasting Application
echo  Complete Startup Script
echo ========================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

:: Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed or not in PATH
    echo Please install Node.js 16+ and try again
    pause
    exit /b 1
)

echo [INFO] Python and Node.js are installed
echo.

:: Check if virtual environment exists (optional)
if exist venv (
    echo [INFO] Activating virtual environment...
    call venv\Scripts\activate
) else (
    echo [INFO] No virtual environment found, using system Python
)

echo.
echo ========================================
echo  STEP 1: Installing Dependencies
echo ========================================
echo.

:: Install Python dependencies
if not exist "backend\__pycache__" (
    echo [1/4] Installing Python dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install Python dependencies
        pause
        exit /b 1
    )
    echo [OK] Python dependencies installed
) else (
    echo [OK] Python dependencies already installed
)

:: Install Node.js dependencies
if not exist "frontend\node_modules" (
    echo [2/4] Installing Node.js dependencies...
    cd frontend
    call npm install
    if errorlevel 1 (
        echo [ERROR] Failed to install Node.js dependencies
        pause
        exit /b 1
    )
    cd ..
    echo [OK] Node.js dependencies installed
) else (
    echo [OK] Node.js dependencies already installed
)

echo.
echo ========================================
echo  STEP 2: Initializing Database
echo ========================================
echo.

if not exist "instance\fintech_forecasting.db" (
    echo [3/4] Initializing SQLite database...
    python init_db.py
    if errorlevel 1 (
        echo [ERROR] Failed to initialize database
        pause
        exit /b 1
    )
    echo [OK] Database initialized
) else (
    echo [OK] Database already exists
)

echo.
echo ========================================
echo  STEP 3: Starting Servers
echo ========================================
echo.

echo [4/4] Starting Backend and Frontend servers...
echo.
echo ========================================
echo  SERVER STATUS
echo ========================================
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo API:      http://localhost:8000/api
echo Database: instance\fintech_forecasting.db
echo ========================================
echo.
echo [INFO] Press Ctrl+C to stop all servers
echo.

:: Start Backend in a new window
start "FinTech Backend" cmd /k "python backend/app_sqlite.py"

:: Wait for backend to start
timeout /t 3 /nobreak >nul

:: Start Frontend in a new window
start "FinTech Frontend" cmd /k "cd frontend && npm start"

echo.
echo ========================================
echo  APPLICATION STARTED SUCCESSFULLY!
echo ========================================
echo.
echo [INFO] Both servers are running in separate windows
echo [INFO] Keep this window open to monitor the application
echo.
echo Opening browser...
start http://localhost:3000
echo.
echo Press any key to stop the application...
pause >nul

:: Kill background processes (optional)
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1

echo.
echo [INFO] Application stopped
pause
