#!/bin/bash

# FinTech Forecasting Application Startup Script

echo "🚀 Starting FinTech Forecasting Application..."

# Check if MongoDB is running
echo "📊 Checking MongoDB status..."
if ! pgrep -x "mongod" > /dev/null; then
    echo "⚠️  MongoDB is not running. Starting MongoDB..."
    sudo systemctl start mongod
    sleep 5
else
    echo "✅ MongoDB is running"
fi

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip install -r requirements.txt

# Start backend server
echo "🔧 Starting backend server..."
cd backend
python app.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 10

# Check if backend is running
if curl -s http://localhost:8000/api/health > /dev/null; then
    echo "✅ Backend server started successfully"
else
    echo "❌ Backend server failed to start"
    exit 1
fi

# Start frontend server
echo "⚛️  Starting frontend server..."
cd ../frontend
npm install
npm start &
FRONTEND_PID=$!

echo "🎉 Application started successfully!"
echo "📊 Frontend: http://localhost:3000"
echo "🔌 Backend API: http://localhost:8000/api"
echo "📚 MongoDB: mongodb://localhost:27017/fintech_forecasting"

# Function to cleanup on exit
cleanup() {
    echo "🛑 Shutting down application..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

# Trap Ctrl+C
trap cleanup SIGINT

# Wait for processes
wait
