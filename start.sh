#!/bin/bash

echo "========================================"
echo " FinTech Forecasting Application"
echo " Complete Startup Script (Linux/Mac)"
echo "========================================"
echo

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR] Python is not installed${NC}"
    echo "Please install Python 3.8+ and try again"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}[ERROR] Node.js is not installed${NC}"
    echo "Please install Node.js 16+ and try again"
    exit 1
fi

echo -e "${GREEN}[INFO] Python and Node.js are installed${NC}"
echo

# Check if virtual environment exists (optional)
if [ -d "venv" ]; then
    echo "[INFO] Activating virtual environment..."
    source venv/bin/activate
else
    echo "[INFO] No virtual environment found, using system Python"
fi

echo
echo "========================================"
echo " STEP 1: Installing Dependencies"
echo "========================================"
echo

# Install Python dependencies
if [ ! -d "backend/__pycache__" ]; then
    echo "[1/4] Installing Python dependencies..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo -e "${RED}[ERROR] Failed to install Python dependencies${NC}"
        exit 1
    fi
    echo -e "${GREEN}[OK] Python dependencies installed${NC}"
else
    echo -e "${GREEN}[OK] Python dependencies already installed${NC}"
fi

# Install Node.js dependencies
if [ ! -d "frontend/node_modules" ]; then
    echo "[2/4] Installing Node.js dependencies..."
    cd frontend
    npm install
    if [ $? -ne 0 ]; then
        echo -e "${RED}[ERROR] Failed to install Node.js dependencies${NC}"
        exit 1
    fi
    cd ..
    echo -e "${GREEN}[OK] Node.js dependencies installed${NC}"
else
    echo -e "${GREEN}[OK] Node.js dependencies already installed${NC}"
fi

echo
echo "========================================"
echo " STEP 2: Initializing Database"
echo "========================================"
echo

# Initialize database
if [ ! -f "instance/fintech_forecasting.db" ]; then
    echo "[3/4] Initializing SQLite database..."
    python3 init_db.py
    if [ $? -ne 0 ]; then
        echo -e "${RED}[ERROR] Failed to initialize database${NC}"
        exit 1
    fi
    echo -e "${GREEN}[OK] Database initialized${NC}"
else
    echo -e "${GREEN}[OK] Database already exists${NC}"
fi

echo
echo "========================================"
echo " STEP 3: Starting Servers"
echo "========================================"
echo

echo "[4/4] Starting Backend and Frontend servers..."
echo
echo "========================================"
echo " SERVER STATUS"
echo "========================================"
echo -e "${GREEN}Backend:  http://localhost:8000${NC}"
echo -e "${GREEN}Frontend: http://localhost:3000${NC}"
echo -e "${GREEN}API:      http://localhost:8000/api${NC}"
echo -e "${GREEN}Database: instance/fintech_forecasting.db${NC}"
echo "========================================"
echo
echo "[INFO] Press Ctrl+C to stop all servers"
echo

# Function to cleanup on exit
cleanup() {
    echo
    echo -e "${YELLOW}[INFO] Stopping servers...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}[INFO] Application stopped${NC}"
    exit 0
}

# Trap Ctrl+C
trap cleanup INT

# Start Backend
echo "[INFO] Starting Backend server..."
python3 backend/app_sqlite.py > backend.log 2>&1 &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start Frontend
echo "[INFO] Starting Frontend server..."
cd frontend
npm start > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

echo
echo "========================================"
echo " APPLICATION STARTED SUCCESSFULLY!"
echo "========================================"
echo
echo "[INFO] Both servers are running in the background"
echo "[INFO] Check backend.log and frontend.log for server logs"
echo
echo "Opening browser..."
sleep 2

# Open browser
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:3000 &
elif command -v open &> /dev/null; then
    open http://localhost:3000 &
fi

echo
echo "Press Ctrl+C to stop the application"
echo

# Wait for user interrupt
wait