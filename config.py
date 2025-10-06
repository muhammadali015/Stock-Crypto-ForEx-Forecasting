# Configuration file for FinTech Forecasting Application

# MongoDB Configuration
MONGODB_URI = "mongodb://localhost:27017/fintech_forecasting"

# Flask Configuration
FLASK_ENV = "development"
FLASK_DEBUG = True

# Logging Configuration
LOG_LEVEL = "INFO"

# Model Configuration
SEQUENCE_LENGTH = 60
MAX_FORECAST_HOURS = 168
TRAIN_SPLIT = 0.8

# API Configuration
API_HOST = "0.0.0.0"
API_PORT = 5000

# Data Sources
YAHOO_FINANCE_ENABLED = True
NEWS_SENTIMENT_ENABLED = True
MAX_NEWS_ITEMS = 50

# Performance Settings
CACHE_FORECASTS = True
CACHE_TTL_HOURS = 1
MAX_CONCURRENT_FORECASTS = 5
