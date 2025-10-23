# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Prerequisites
- Node.js 16+ installed
- Python 3.8+ installed
- MongoDB 4.4+ installed and running

### Option 1: Using Startup Scripts (Recommended)

#### Windows
```bash
# Run the Windows startup script
start.bat
```

#### Linux/Mac
```bash
# Make script executable
chmod +x start.sh

# Run the startup script
./start.sh
```

### Option 2: Manual Setup

#### 1. Start MongoDB
```bash
# Windows
net start MongoDB

# Linux/Mac
sudo systemctl start mongod
# or
mongod
```

#### 2. Start Backend
```bash
# Install dependencies
pip install -r requirements.txt

# Start backend server
cd backend
python app.py
```

#### 3. Start Frontend
```bash
# Install dependencies
cd frontend
npm install

# Start frontend server
npm start
```

### Option 3: Docker (All-in-One)

```bash
# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

## 🌐 Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/api
- **Health Check**: http://localhost:8000/api/health

## 📊 Using the Application

### 1. Select an Instrument
- Choose from available stocks, crypto, or forex instruments
- Click "Refresh Data" to fetch latest price data

### 2. Train a Model
- Select a forecasting model (LSTM, ARIMA, Moving Average, etc.)
- Click "Train" to train the model on historical data
- Wait for training to complete

### 3. Generate Forecasts
- Set forecast horizon (1 hour to 1 week)
- Choose confidence level (90%, 95%, 99%)
- Click "Generate Forecast" to create predictions

### 4. View Results
- Interactive candlestick chart with forecast overlays
- Performance metrics (RMSE, MAE, MAPE, Directional Accuracy)
- Time range selector for different views

## 🔧 Troubleshooting

### Common Issues

**MongoDB Connection Error**
```bash
# Check if MongoDB is running
sudo systemctl status mongod

# Start MongoDB if not running
sudo systemctl start mongod
```

**Port Already in Use**
```bash
# Kill processes using ports 3000 or 8000
# Windows
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:3000 | xargs kill -9
```

**Python Dependencies Error**
```bash
# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

**Node.js Dependencies Error**
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

## 📈 Sample Data

The application comes with sample instruments:
- **AAPL** - Apple Inc. (Stock)
- **MSFT** - Microsoft Corporation (Stock)
- **BTC-USD** - Bitcoin (Cryptocurrency)
- **ETH-USD** - Ethereum (Cryptocurrency)
- **EURUSD=X** - EUR/USD (Forex)

## 🧪 Testing

### Run Tests
```bash
# Frontend tests
cd frontend
npm test

# Backend tests
cd backend
pytest tests/test_backend.py -v
```

### Test Coverage
```bash
# Frontend coverage
cd frontend
npm run test -- --coverage

# Backend coverage
cd backend
pytest tests/test_backend.py --cov=backend
```

## 🚀 Production Deployment

### Using Docker
```bash
# Build production images
docker-compose -f docker-compose.prod.yml up --build
```

### Manual Deployment
```bash
# Build frontend
cd frontend
npm run build

# Serve with nginx
sudo cp -r build/* /var/www/html/

# Start backend with gunicorn
cd backend
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

## 📚 Documentation

- **Full Documentation**: [README.md](README.md)
- **Architecture**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **API Reference**: [docs/API.md](docs/API.md)

## 🆘 Support

If you encounter any issues:
1. Check the troubleshooting section above
2. Review the logs for error messages
3. Ensure all prerequisites are installed
4. Try the Docker setup for a clean environment

## 🎯 Next Steps

- Explore different forecasting models
- Try various financial instruments
- Experiment with different forecast horizons
- Analyze model performance metrics
- Customize the application for your needs