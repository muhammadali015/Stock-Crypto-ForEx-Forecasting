# 🚀 Quick Start Guide

## Run the Application Locally

### 🪟 Windows Users
Double-click this file or run in PowerShell:
```bash
START_APPLICATION.bat
```

### 🐧 Linux/Mac Users
Run this command in terminal:
```bash
chmod +x start.sh
./start.sh
```

### 🐍 Python Users (Cross-Platform)
Run this command:
```bash
python start.py
```

---

## What Each Script Does

All scripts perform the same steps:

1. **Check Dependencies**
   - Verify Python 3.8+ is installed
   - Verify Node.js 16+ is installed
   - Check if all required packages are installed

2. **Install Dependencies** (if needed)
   - Install Python packages from `requirements.txt`
   - Install Node.js packages for frontend

3. **Initialize Database** (if needed)
   - Create SQLite database
   - Seed with sample data

4. **Start Servers**
   - Start Flask backend on http://localhost:8000
   - Start React frontend on http://localhost:3000
   - Open browser automatically

---

## Manual Start (Alternative)

If the scripts don't work, you can start the servers manually:

### Terminal 1 - Backend
```bash
python backend/app_sqlite.py
```

### Terminal 2 - Frontend
```bash
cd frontend
npm start
```

---

## Access the Application

Once running, access:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/api
- **API Docs**: http://localhost:8000/api/docs (if available)

---

## Troubleshooting

### Port Already in Use
If port 8000 or 3000 is already in use:
1. Stop other applications using these ports
2. Or modify the port numbers in the configuration files

### Dependencies Missing
If dependencies are missing:
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies
cd frontend
npm install
```

### Database Issues
To reset the database:
```bash
# Delete existing database
rm -rf instance/fintech_forecasting.db

# Or on Windows:
del instance\fintech_forecasting.db

# Reinitialize
python init_db.py
```

---

## Features Available

✅ **Interactive Charts** - Professional candlestick charts  
✅ **Technical Indicators** - RSI, MACD, Bollinger Bands, Stochastic  
✅ **ML Models** - ARIMA, LSTM, GRU, Transformer  
✅ **Forecasting** - Generate predictions with confidence intervals  
✅ **Performance Metrics** - RMSE, MAE, MAPE, Directional Accuracy  

---

## Stop the Application

Press **Ctrl+C** in the terminal to stop all servers.

---

**Need Help?** Check the main README.md for more details.
