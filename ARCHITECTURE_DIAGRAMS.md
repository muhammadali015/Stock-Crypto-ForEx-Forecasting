# Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACE LAYER                              │
│                                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                │
│  │   React App     │  │  Mobile View    │  │   Desktop View  │                │
│  │   (Port 3000)   │  │   (Responsive)  │  │   (Full Features)│                │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                │
│           │                       │                       │                    │
│           └───────────────────────┼───────────────────────┘                    │
│                                   │                                            │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    FRONTEND COMPONENTS                                  │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐    │   │
│  │  │Instrument    │ │Model        │ │Forecast     │ │Performance  │    │   │
│  │  │Selector      │ │Selector     │ │Controls     │ │Metrics      │    │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘    │   │
│  │                                                                       │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │   │
│  │  │              Interactive Candlestick Chart                     │  │   │
│  │  │  • OHLC Data Visualization                                      │  │   │
│  │  │  • Forecast Overlays                                            │  │   │
│  │  │  • Time Range Selection (1D, 1W, 1M, 3M, 1Y)                  │  │   │
│  │  │  • Confidence Intervals                                        │  │   │
│  │  └─────────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTP/REST API
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            APPLICATION LAYER                                   │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                        Flask Backend API                               │   │
│  │                           (Port 8000)                                 │   │
│  │                                                                       │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐    │   │
│  │  │Instruments  │ │Price Data   │ │Models       │ │Forecasts    │    │   │
│  │  │Endpoints     │ │Endpoints    │ │Endpoints    │ │Endpoints    │    │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘    │   │
│  │                                                                       │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │   │
│  │  │                    Forecasting Service                         │  │   │
│  │  │  • Model Training Orchestration                                │  │   │
│  │  │  • Prediction Generation                                        │  │   │
│  │  │  • Performance Evaluation                                      │  │   │
│  │  └─────────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Database Operations
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              DATA LAYER                                        │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                          MongoDB Database                               │   │
│  │                                                                       │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐    │   │
│  │  │Instruments  │ │Price Data   │ │Models       │ │Forecasts    │    │   │
│  │  │Collection   │ │Collection   │ │Collection   │ │Collection   │    │   │
│  │  │• Symbol     │ │• OHLC Data  │ │• Parameters │ │• Predictions│    │   │
│  │  │• Exchange   │ │• Volume     │ │• Status     │ │• Confidence │    │   │
│  │  │• Type       │ │• Timestamps │ │• Metrics    │ │• Timestamps │    │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘    │   │
│  │                                                                       │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │   │
│  │  │                    News Data Collection                         │  │   │
│  │  │  • Sentiment Analysis                                          │  │   │
│  │  │  • Market News                                                 │  │   │
│  │  │  • Social Media Data                                           │  │   │
│  │  └─────────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ External Data Sources
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           EXTERNAL SERVICES LAYER                              │
│                                                                                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                │
│  │Yahoo Finance│ │Alpha Vantage│ │News APIs    │ │Social Media │                │
│  │• Stock Data │ │• Forex Data │ │• Market News│ │• Sentiment  │                │
│  │• Crypto Data│ │• Indicators │ │• Analysis   │ │• Trends     │                │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘                │
└─────────────────────────────────────────────────────────────────────────────────┘
```

# Machine Learning Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           ML MODEL PIPELINE                                     │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                        DATA PREPROCESSING                              │   │
│  │                                                                       │   │
│  │  Raw Data → Cleaning → Normalization → Feature Engineering → Splitting │   │
│  │     │           │           │              │              │          │   │
│  │     ▼           ▼           ▼              ▼              ▼          │   │
│  │  OHLC Data   Missing    MinMaxScaler   Technical      Train/Val     │   │
│  │  Volume      Values     StandardScaler  Indicators     Test Split    │   │
│  │  News        Outliers   RobustScaler    Lag Features   Time Series   │   │
│  │  Sentiment   Duplicates                Price Ratios   Cross-Validation│   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                    │                                            │
│                                    ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                        MODEL TRAINING                                  │   │
│  │                                                                       │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐    │   │
│  │  │Traditional  │ │Neural       │ │Ensemble     │ │Hyperparameter│    │   │
│  │  │Models       │ │Models       │ │Methods      │ │Optimization  │    │   │
│  │  │• ARIMA      │ │• LSTM       │ │• Voting     │ │• Grid Search │    │   │
│  │  │• Moving Avg │ │• GRU        │ │• Bagging    │ │• Random Search│   │   │
│  │  │• VAR        │ │• Transformer│ │• Boosting   │ │• Bayesian    │    │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘    │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                    │                                            │
│                                    ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                        MODEL EVALUATION                                 │   │
│  │                                                                       │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐    │   │
│  │  │Accuracy     │ │Performance  │ │Confidence   │ │Backtesting  │    │   │
│  │  │Metrics      │ │Metrics      │ │Intervals    │ │Analysis     │    │   │
│  │  │• RMSE       │ │• MAE        │ │• Statistical│ │• Walk Forward│   │   │
│  │  │• MAPE       │ │• Directional│ │• Monte Carlo│ │• Out-of-Sample│  │   │
│  │  │• R²         │ │• Accuracy   │ │• Bootstrap  │ │• Risk Metrics│    │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘    │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                    │                                            │
│                                    ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                        PREDICTION GENERATION                            │   │
│  │                                                                       │   │
│  │  Trained Models → Forecast Generation → Confidence Estimation → API   │   │
│  │       │                │                    │              │         │   │
│  │       ▼                ▼                    ▼              ▼         │   │
│  │  Model Weights    Point Forecasts    Uncertainty      REST Endpoint │   │
│  │  Parameters       Confidence        Quantification    JSON Response │   │
│  │  Metadata         Intervals         Risk Assessment   Real-time     │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

# Performance Comparison Chart

```
Model Performance Comparison (Lower is Better for RMSE/MAE/MAPE, Higher is Better for Directional Accuracy)

RMSE Comparison:
┌─────────────────────────────────────────────────────────────────────────────┐
│ Moving Average ████████████████████████████████████████████████████████████ │ 2.45
│ ARIMA          ████████████████████████████████████████████████████████████ │ 2.12
│ VAR            ████████████████████████████████████████████████████████████ │ 2.34
│ LSTM           ████████████████████████████████████████████████████████████ │ 1.89
│ GRU            ████████████████████████████████████████████████████████████ │ 1.92
│ Transformer    ████████████████████████████████████████████████████████████ │ 1.85 ⭐
└─────────────────────────────────────────────────────────────────────────────┘

Directional Accuracy Comparison:
┌─────────────────────────────────────────────────────────────────────────────┐
│ Moving Average ████████████████████████████████████████████████████████████ │ 58.2%
│ ARIMA          ████████████████████████████████████████████████████████████ │ 62.1%
│ VAR            ████████████████████████████████████████████████████████████ │ 59.8%
│ LSTM           ████████████████████████████████████████████████████████████ │ 68.4%
│ GRU            ████████████████████████████████████████████████████████████ │ 67.9%
│ Transformer    ████████████████████████████████████████████████████████████ │ 69.1% ⭐
└─────────────────────────────────────────────────────────────────────────────┘

Training Time Comparison (seconds):
┌─────────────────────────────────────────────────────────────────────────────┐
│ Moving Average ██                                                           │ 0.5s ⭐
│ ARIMA          █████                                                       │ 2.3s
│ VAR            ████████                                                     │ 5.7s
│ LSTM           ████████████████████████████████████████████████████████████ │ 45.2s
│ GRU            ████████████████████████████████████████████████████████████ │ 38.7s
│ Transformer    ████████████████████████████████████████████████████████████ │ 67.8s
└─────────────────────────────────────────────────────────────────────────────┘

Legend: ⭐ = Best Performance
```

# Technology Stack

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              TECHNOLOGY STACK                                  │
│                                                                                 │
│  Frontend Technologies:                                                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│  │React 18      │ │Tailwind CSS │ │Framer Motion│ │Axios        │            │
│  │• Hooks       │ │• Utility    │ │• Animations │ │• HTTP Client│            │
│  │• Components  │ │• Responsive │ │• Transitions│ │• Interceptors│            │
│  │• State Mgmt  │ │• Dark Theme │ │• Gestures   │ │• Error Handle│            │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘            │
│                                                                                 │
│  Backend Technologies:                                                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│  │Flask 2.3    │ │MongoDB 6.0  │ │PyMongo 4.5  │ │CORS         │            │
│  │• REST API    │ │• NoSQL      │ │• ODM        │ │• Cross-Origin│            │
│  │• Blueprints  │ │• Collections│ │• Aggregation│ │• Security   │            │
│  │• Middleware  │ │• Indexing   │ │• Transactions│ │• Headers    │            │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘            │
│                                                                                 │
│  Machine Learning:                                                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│  │TensorFlow   │ │scikit-learn │ │pandas       │ │numpy        │            │
│  │• Keras API  │ │• Traditional│ │• Data Manip │ │• Numerical  │            │
│  │• LSTM/GRU   │ │• ARIMA/VAR  │ │• Time Series│ │• Computing  │            │
│  │• Transformers│ │• Metrics    │ │• Analysis   │ │• Arrays     │            │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘            │
│                                                                                 │
│  Development Tools:                                                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│  │Docker       │ │pytest       │ │Jest         │ │ESLint       │            │
│  │• Containers │ │• Unit Tests  │ │• React Tests│ │• Code Quality│            │
│  │• Compose    │ │• Coverage    │ │• Mocking    │ │• Formatting │            │
│  │• Multi-stage│ │• Fixtures    │ │• Snapshots  │ │• Rules      │            │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘            │
└─────────────────────────────────────────────────────────────────────────────────┘
```
