"""
Traditional forecasting models: ARIMA, Moving Averages, VAR.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.vector_ar.var_model import VAR
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.seasonal import seasonal_decompose
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
import warnings
warnings.filterwarnings('ignore')

from .base import BaseForecaster, PerformanceMetrics, DataPreprocessor


class ARIMAForecaster(BaseForecaster):
    """ARIMA (AutoRegressive Integrated Moving Average) forecasting model."""
    
    def __init__(self, order: tuple = (1, 1, 1), seasonal_order: tuple = (0, 0, 0, 0)):
        super().__init__("ARIMA")
        self.order = order
        self.seasonal_order = seasonal_order
        self.model = None
        self.fitted_model = None
        
    def _check_stationarity(self, series: pd.Series) -> bool:
        """Check if the series is stationary using Augmented Dickey-Fuller test."""
        result = adfuller(series.dropna())
        return result[1] <= 0.05  # p-value <= 0.05 means stationary
    
    def _find_optimal_order(self, data: pd.Series, max_p: int = 3, max_d: int = 2, max_q: int = 3) -> tuple:
        """Find optimal ARIMA order using AIC."""
        best_aic = np.inf
        best_order = (1, 1, 1)
        
        for p in range(max_p + 1):
            for d in range(max_d + 1):
                for q in range(max_q + 1):
                    try:
                        model = ARIMA(data, order=(p, d, q))
                        fitted_model = model.fit()
                        if fitted_model.aic < best_aic:
                            best_aic = fitted_model.aic
                            best_order = (p, d, q)
                    except:
                        continue
        
        return best_order
    
    def fit(self, data: pd.DataFrame, target_column: str = 'close_price') -> 'ARIMAForecaster':
        """Fit ARIMA model to the data."""
        if target_column not in data.columns:
            raise ValueError(f"Target column '{target_column}' not found in data")
        
        # Prepare the time series
        series = data[target_column].dropna()
        
        # Auto-find optimal order if not specified
        if self.order == (1, 1, 1):
            self.order = self._find_optimal_order(series)
        
        # Fit the model
        self.model = ARIMA(series, order=self.order, seasonal_order=self.seasonal_order)
        self.fitted_model = self.model.fit()
        
        self.is_fitted = True
        return self
    
    def predict(self, horizon: int, confidence_level: float = 0.95) -> Dict[str, Any]:
        """Generate ARIMA predictions."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before making predictions")
        
        # Generate predictions
        forecast = self.fitted_model.forecast(steps=horizon)
        conf_int = self.fitted_model.get_forecast(steps=horizon).conf_int(alpha=1-confidence_level)
        
        return {
            'predictions': forecast.values,
            'confidence_intervals': {
                'lower': conf_int.iloc[:, 0].values,
                'upper': conf_int.iloc[:, 1].values
            },
            'model_info': {
                'order': self.order,
                'aic': self.fitted_model.aic,
                'bic': self.fitted_model.bic
            }
        }
    
    def evaluate(self, test_data: pd.DataFrame, target_column: str = 'close_price') -> Dict[str, float]:
        """Evaluate ARIMA model performance."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before evaluation")
        
        predictions = self.predict(len(test_data), confidence_level=0.95)['predictions']
        return PerformanceMetrics.calculate_metrics(
            test_data[target_column].values,
            predictions
        )


class MovingAverageForecaster(BaseForecaster):
    """Simple and Exponential Moving Average forecasting models."""
    
    def __init__(self, window: int = 20, method: str = 'simple'):
        super().__init__(f"MA_{method}_{window}")
        self.window = window
        self.method = method  # 'simple' or 'exponential'
        self.last_values = None
        
    def fit(self, data: pd.DataFrame, target_column: str = 'close_price') -> 'MovingAverageForecaster':
        """Fit moving average model."""
        if target_column not in data.columns:
            raise ValueError(f"Target column '{target_column}' not found in data")
        
        series = data[target_column].dropna()
        
        if self.method == 'simple':
            self.last_values = series.tail(self.window).values
        elif self.method == 'exponential':
            # Calculate exponential moving average
            alpha = 2.0 / (self.window + 1)
            ema_values = []
            ema_values.append(series.iloc[0])
            
            for i in range(1, len(series)):
                ema_values.append(alpha * series.iloc[i] + (1 - alpha) * ema_values[-1])
            
            self.last_values = np.array(ema_values[-self.window:])
        
        self.is_fitted = True
        return self
    
    def predict(self, horizon: int, confidence_level: float = 0.95) -> Dict[str, Any]:
        """Generate moving average predictions."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before making predictions")
        
        if self.method == 'simple':
            # Simple moving average: predict the average of last window values
            predictions = np.full(horizon, np.mean(self.last_values))
        else:
            # Exponential moving average: use the last EMA value
            predictions = np.full(horizon, self.last_values[-1])
        
        # Simple confidence intervals based on historical volatility
        std_dev = np.std(self.last_values)
        z_score = 1.96 if confidence_level == 0.95 else 2.576  # 95% or 99%
        
        return {
            'predictions': predictions,
            'confidence_intervals': {
                'lower': predictions - z_score * std_dev,
                'upper': predictions + z_score * std_dev
            }
        }
    
    def evaluate(self, test_data: pd.DataFrame, target_column: str = 'close_price') -> Dict[str, float]:
        """Evaluate moving average model performance."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before evaluation")
        
        predictions = self.predict(len(test_data), confidence_level=0.95)['predictions']
        return PerformanceMetrics.calculate_metrics(
            test_data[target_column].values,
            predictions
        )


class VARForecaster(BaseForecaster):
    """Vector Autoregression (VAR) model for multivariate time series."""
    
    def __init__(self, maxlags: int = 15):
        super().__init__("VAR")
        self.maxlags = maxlags
        self.model = None
        self.fitted_model = None
        self.feature_columns = []
        
    def fit(self, data: pd.DataFrame, target_column: str = 'close_price') -> 'VARForecaster':
        """Fit VAR model to multivariate data."""
        # Prepare multivariate time series
        feature_cols = ['close_price', 'volume', 'daily_return']
        available_cols = [col for col in feature_cols if col in data.columns]
        
        if len(available_cols) < 2:
            raise ValueError("VAR requires at least 2 variables")
        
        # Prepare data
        var_data = data[available_cols].dropna()
        
        # Check stationarity and difference if needed
        for col in available_cols:
            if not self._check_stationarity(var_data[col]):
                var_data[col] = var_data[col].diff().dropna()
        
        # Fit VAR model
        self.model = VAR(var_data)
        self.fitted_model = self.model.fit(maxlags=self.maxlags, ic='aic')
        
        self.feature_columns = available_cols
        self.is_fitted = True
        return self
    
    def _check_stationarity(self, series: pd.Series) -> bool:
        """Check stationarity using ADF test."""
        from statsmodels.tsa.stattools import adfuller
        result = adfuller(series.dropna())
        return result[1] <= 0.05
    
    def predict(self, horizon: int, confidence_level: float = 0.95) -> Dict[str, Any]:
        """Generate VAR predictions."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before making predictions")
        
        # Generate forecasts
        forecast = self.fitted_model.forecast(self.fitted_model.y, steps=horizon)
        
        # Get confidence intervals
        conf_int = self.fitted_model.forecast_interval(self.fitted_model.y, steps=horizon, alpha=1-confidence_level)
        
        # Extract close price predictions (assuming it's the first column)
        close_idx = 0 if 'close_price' in self.feature_columns else 0
        predictions = forecast[:, close_idx]
        
        return {
            'predictions': predictions,
            'confidence_intervals': {
                'lower': conf_int[0][:, close_idx],
                'upper': conf_int[1][:, close_idx]
            },
            'all_predictions': forecast,
            'model_info': {
                'selected_lags': self.fitted_model.k_ar,
                'aic': self.fitted_model.aic
            }
        }
    
    def evaluate(self, test_data: pd.DataFrame, target_column: str = 'close_price') -> Dict[str, float]:
        """Evaluate VAR model performance."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before evaluation")
        
        predictions = self.predict(len(test_data), confidence_level=0.95)['predictions']
        return PerformanceMetrics.calculate_metrics(
            test_data[target_column].values,
            predictions
        )


class LinearRegressionForecaster(BaseForecaster):
    """Linear regression-based forecasting model."""
    
    def __init__(self):
        super().__init__("LinearRegression")
        self.model = None
        self.feature_columns = []
        
    def fit(self, data: pd.DataFrame, target_column: str = 'close_price') -> 'LinearRegressionForecaster':
        """Fit linear regression model."""
        # Prepare features
        df, feature_columns = DataPreprocessor.prepare_features(data, target_column)
        self.feature_columns = feature_columns
        
        if len(feature_columns) == 0:
            raise ValueError("No features available for training")
        
        # Prepare training data
        X = df[feature_columns].values
        y = df[target_column].values
        
        # Fit model
        self.model = LinearRegression()
        self.model.fit(X, y)
        
        self.is_fitted = True
        return self
    
    def predict(self, horizon: int, confidence_level: float = 0.95) -> Dict[str, Any]:
        """Generate linear regression predictions."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before making predictions")
        
        # For simplicity, use the last available features for all predictions
        # In practice, you might want to generate features for future periods
        last_features = self.model.feature_importances_ if hasattr(self.model, 'feature_importances_') else None
        
        # Simple prediction: use the last fitted value
        predictions = np.full(horizon, self.model.intercept_)
        
        return {
            'predictions': predictions,
            'confidence_intervals': None,
            'feature_importance': dict(zip(self.feature_columns, self.model.coef_)) if hasattr(self.model, 'coef_') else None
        }
    
    def evaluate(self, test_data: pd.DataFrame, target_column: str = 'close_price') -> Dict[str, float]:
        """Evaluate linear regression model performance."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before evaluation")
        
        # Prepare test features
        df, _ = DataPreprocessor.prepare_features(test_data, target_column)
        
        if len(df) == 0:
            return {'rmse': np.nan, 'mae': np.nan, 'mape': np.nan}
        
        X_test = df[self.feature_columns].values
        y_pred = self.model.predict(X_test)
        
        return PerformanceMetrics.calculate_metrics(
            df[target_column].values,
            y_pred
        )
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance from linear regression coefficients."""
        if not self.is_fitted:
            return {}
        
        return dict(zip(self.feature_columns, self.model.coef_))
