# FinTech Forecasting Application

A comprehensive forecasting application for financial instruments (stocks, cryptocurrencies, and forex) that combines traditional and neural network models with a modern web interface.

## 🚀 Features

- **Multiple Forecasting Models**: ARIMA, Moving Averages, VAR, Linear Regression, LSTM, GRU, and Transformer models
- **Model Ensembles**: Combine multiple models for improved accuracy
- **Real-time Data**: Integration with Yahoo Finance for live price data and news sentiment
- **Interactive Dashboard**: React-based frontend with candlestick charts
- **Performance Metrics**: RMSE, MAE, MAPE, directional accuracy, and Sharpe ratio
- **Database Integration**: SQLite database for storing historical data and predictions
- **RESTful API**: Flask-based backend with comprehensive endpoints
- **Unit Tests**: Comprehensive test coverage for all components

## 📁 Project Structure

```
fintech-forecasting/
├── backend/                 # Flask backend API
│   ├── models.py           # Database models
│   ├── database.py         # Database configuration
│   └── app.py              # Flask application
├── frontend/               # React frontend
│   └── index.html          # Single-page application
├── ml_models/              # Machine learning models
│   ├── base.py             # Base classes and utilities
│   ├── traditional.py      # Traditional models (ARIMA, MA, VAR)
│   ├── neural.py           # Neural network models (LSTM, GRU, Transformer)
│   └── service.py          # Forecasting service and factory
├── src/fintech_dataset/    # Data curation (existing)
│   ├── prices.py          # Price data fetching
│   ├── news.py             # News sentiment analysis
│   ├── features.py         # Feature engineering
│   ├── align.py            # Data alignment
│   └── cli.py              # Command-line interface
├── tests/                  # Unit tests
│   └── test_forecasting.py # Comprehensive test suite
├── docs/                   # Documentation
├── outputs/                # Data outputs
└── requirements.txt        # Python dependencies
```

## 🛠️ Installation & Setup

### Prerequisites

- Python 3.8+
- Node.js 16+ (for frontend development)
- Git

### 1. Clone the Repository

```bash
git clone <repository-url>
cd fintech-forecasting
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Initialize Database

```bash
python backend/database.py
```

### 5. Run the Application

```bash
# Start the Flask backend
python backend/app.py

# The application will be available at:
# Backend API: http://localhost:5000
# Frontend: http://localhost:5000 (served by Flask)
```

## 🎯 Usage Guide

### 1. Access the Dashboard

Open your browser and navigate to `http://localhost:5000` to access the forecasting dashboard.

### 2. Select Financial Instrument

- Choose from available instruments (AAPL, MSFT, BTC-USD, etc.)
- Click "Refresh Data" to fetch the latest price and news data

### 3. Train Forecasting Models

- Select a model type (ARIMA, LSTM, GRU, etc.)
- Click "Train" to train the model on historical data
- Click "Evaluate" to assess model performance

### 4. Generate Forecasts

- Set forecast horizon (1 hour to 1 week)
- Choose confidence level (90%, 95%, 99%)
- Click "Generate Forecast" to create predictions

### 5. View Results

- Interactive candlestick charts show historical and predicted prices
- Performance metrics display model accuracy
- Confidence intervals show prediction uncertainty

## 🔧 API Documentation

### Instruments

- `GET /api/instruments` - List all instruments
- `POST /api/instruments` - Create new instrument
- `GET /api/instruments/{id}` - Get specific instrument
- `POST /api/instruments/{id}/price-data` - Update price data

### Models

- `GET /api/models` - List available models
- `POST /api/models` - Create new model
- `POST /api/models/{id}/train` - Train model
- `POST /api/models/{id}/predict` - Generate predictions
- `POST /api/models/{id}/evaluate` - Evaluate model performance

### Forecasts

- `GET /api/instruments/{id}/forecasts` - Get forecast history
- `GET /api/instruments/{id}/performance` - Get performance metrics

## 🤖 Machine Learning Models

### Traditional Models

1. **ARIMA (AutoRegressive Integrated Moving Average)**
   - Suitable for univariate time series
   - Automatically finds optimal parameters
   - Good for trend and seasonal patterns

2. **Moving Averages**
   - Simple Moving Average (SMA)
   - Exponential Moving Average (EMA)
   - Fast and interpretable

3. **VAR (Vector Autoregression)**
   - Multivariate time series model
   - Captures relationships between variables
   - Good for correlated financial instruments

4. **Linear Regression**
   - Uses technical indicators as features
   - Interpretable and fast
   - Good baseline model

### Neural Network Models

1. **LSTM (Long Short-Term Memory)**
   - Captures long-term dependencies
   - Good for sequential data
   - Handles vanishing gradient problem

2. **GRU (Gated Recurrent Unit)**
   - Simpler than LSTM
   - Faster training
   - Good performance on financial data

3. **Transformer**
   - Attention mechanism
   - Parallel processing
   - State-of-the-art performance

### Model Ensembles

- Combines multiple models for improved accuracy
- Weighted averaging of predictions
- Reduces overfitting and improves robustness

## 📊 Performance Metrics

### Accuracy Metrics

- **RMSE (Root Mean Square Error)**: Measures prediction accuracy
- **MAE (Mean Absolute Error)**: Average absolute prediction error
- **MAPE (Mean Absolute Percentage Error)**: Percentage-based error metric

### Financial Metrics

- **Directional Accuracy**: Percentage of correct direction predictions
- **Sharpe Ratio**: Risk-adjusted return measure
- **Maximum Drawdown**: Largest peak-to-trough decline

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=ml_models --cov=backend

# Run specific test file
pytest tests/test_forecasting.py -v
```

### Test Coverage

- Unit tests for all ML models
- Integration tests for complete workflows
- API endpoint testing
- Data preprocessing validation
- Performance metrics verification

## 🔒 Security Considerations

- Input validation on all API endpoints
- SQL injection prevention through SQLAlchemy ORM
- CORS configuration for frontend-backend communication
- Error handling and logging
- Rate limiting (recommended for production)

## 🚀 Deployment

### Development

```bash
python backend/app.py
```

### Production

```bash
# Using Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 backend.app:app

# Using Docker (create Dockerfile)
docker build -t fintech-forecasting .
docker run -p 5000:5000 fintech-forecasting
```

### Environment Variables

Create a `.env` file:

```env
DATABASE_URL=sqlite:///fintech_forecasting.db
SECRET_KEY=your-secret-key-here
FLASK_ENV=production
```

## 📈 Performance Optimization

### Database

- Indexes on frequently queried columns
- Connection pooling for high concurrency
- Query optimization and caching

### ML Models

- Model serialization for faster loading
- Batch prediction for multiple instruments
- GPU acceleration for neural networks

### Frontend

- CDN for static assets
- Code splitting and lazy loading
- Caching strategies

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Yahoo Finance for financial data
- VADER for sentiment analysis
- Plotly for interactive charts
- Flask and React communities
- TensorFlow/Keras for neural networks
- Statsmodels for traditional models

## 📞 Support

For questions, issues, or contributions:

- Create an issue on GitHub
- Contact the development team
- Check the documentation wiki

---

**Note**: This application is for educational and research purposes. Always consult with financial professionals before making investment decisions based on model predictions.
