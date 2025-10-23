@echo off
REM FinTech Forecasting Application Startup Script for Windows

echo 🚀 Starting FinTech Forecasting Application...

REM Check if MongoDB is running
echo 📊 Checking MongoDB status...
tasklist /FI "IMAGENAME eq mongod.exe" 2>NUL | find /I /N "mongod.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo ✅ MongoDB is running
) else (
    echo ⚠️  MongoDB is not running. Please start MongoDB manually.
    echo    You can start it with: net start MongoDB
    pause
)

REM Install Python dependencies
echo 🐍 Installing Python dependencies...
pip install -r requirements.txt

REM Start backend server
echo 🔧 Starting backend server...
cd backend
start "Backend Server" cmd /k "python app.py"

REM Wait for backend to start
timeout /t 10 /nobreak > nul

REM Check if backend is running
powershell -Command "try { Invoke-WebRequest -Uri 'http://localhost:8000/api/health' -UseBasicParsing | Out-Null; Write-Host '✅ Backend server started successfully' } catch { Write-Host '❌ Backend server failed to start' }"

REM Start frontend server
echo ⚛️  Starting frontend server...
cd ../frontend
call npm install
start "Frontend Server" cmd /k "npm start"

echo 🎉 Application started successfully!
echo 📊 Frontend: http://localhost:3000
echo 🔌 Backend API: http://localhost:8000/api
echo 📚 MongoDB: mongodb://localhost:27017/fintech_forecasting

pause
