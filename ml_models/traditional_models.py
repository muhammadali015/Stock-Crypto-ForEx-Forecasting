"""
Traditional forecasting models for financial time series
Includes ARIMA, Moving Averages, and VAR models
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from sklearn.metrics import mean_squared_error, mean_absolute_error
import statsmodels.api as sm
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.vector_ar.var_model import VAR
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import warnings
warnings.filterwarnings('ignore')


class TraditionalForecaster:
    """Traditional time series forecasting models"""
    
    def __init__(self):
        self.models = {}
        self.metrics = {}
    
    def prepare_data(self, df: pd.DataFrame, target_col: str = 'Close') -> Tuple[np.ndarray, pd.DatetimeIndex]:
        """Prepare data for forecasting"""
        df = df.sort_values('Date')
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.set_index('Date')
        
        # Remove any NaN values
        df = df.dropna()
        
        return df[target_col].values, df.index
    
    def arima_forecast(self, data: np.ndarray, forecast_hours: int, order: Tuple[int, int, int] = (1, 1, 1)) -> Dict:
        """ARIMA forecasting model"""
        try:
            model = ARIMA(data, order=order)
            fitted_model = model.fit()
            
            # Generate forecast
            forecast = fitted_model.forecast(steps=forecast_hours)
            confidence_intervals = fitted_model.get_forecast(steps=forecast_hours).conf_int()
            
            return {
                'forecast': forecast,
                'confidence_intervals': confidence_intervals,
                'model': fitted_model,
                'aic': fitted_model.aic,
                'bic': fitted_model.bic
            }
        except Exception as e:
            print(f"ARIMA forecasting error: {e}")
            return {'forecast': np.full(forecast_hours, data[-1]), 'error': str(e)}
    
    def moving_average_forecast(self, data: np.ndarray, forecast_hours: int, window: int = 5) -> Dict:
        """Simple Moving Average forecasting"""
        try:
            # Use the last 'window' values to predict next values
            last_values = data[-window:]
            forecast = np.full(forecast_hours, np.mean(last_values))
            
            # Add some trend based on recent changes
            recent_trend = np.mean(np.diff(last_values))
            forecast = forecast + np.arange(1, forecast_hours + 1) * recent_trend
            
            return {
                'forecast': forecast,
                'window': window,
                'trend': recent_trend
            }
        except Exception as e:
            print(f"Moving Average forecasting error: {e}")
            return {'forecast': np.full(forecast_hours, data[-1]), 'error': str(e)}
    
    def exponential_smoothing_forecast(self, data: np.ndarray, forecast_hours: int) -> Dict:
        """Exponential Smoothing forecasting"""
        try:
            model = ExponentialSmoothing(data, trend='add', seasonal=None)
            fitted_model = model.fit()
            
            forecast = fitted_model.forecast(steps=forecast_hours)
            
            return {
                'forecast': forecast,
                'model': fitted_model,
                'sse': fitted_model.sse
            }
        except Exception as e:
            print(f"Exponential Smoothing forecasting error: {e}")
            return {'forecast': np.full(forecast_hours, data[-1]), 'error': str(e)}
    
    def var_forecast(self, df: pd.DataFrame, forecast_hours: int, 
                    target_cols: List[str] = ['Close', 'Volume']) -> Dict:
        """Vector Autoregression (VAR) forecasting"""
        try:
            # Prepare multivariate data
            var_data = df[target_cols].dropna()
            
            if len(var_data) < 10:  # Need sufficient data for VAR
                return {'forecast': np.full(forecast_hours, var_data[target_cols[0]].iloc[-1]), 
                       'error': 'Insufficient data for VAR'}
            
            model = VAR(var_data)
            fitted_model = model.fit(maxlags=5)
            
            # Generate forecast
            forecast = fitted_model.forecast(var_data.values[-fitted_model.k_ar:], steps=forecast_hours)
            
            return {
                'forecast': forecast[:, 0],  # Return Close price forecast
                'model': fitted_model,
                'lag_order': fitted_model.k_ar
            }
        except Exception as e:
            print(f"VAR forecasting error: {e}")
            return {'forecast': np.full(forecast_hours, df[target_cols[0]].iloc[-1]), 'error': str(e)}
    
    def calculate_metrics(self, actual: np.ndarray, predicted: np.ndarray) -> Dict[str, float]:
        """Calculate performance metrics"""
        try:
            # Remove any NaN values
            mask = ~(np.isnan(actual) | np.isnan(predicted))
            actual_clean = actual[mask]
            predicted_clean = predicted[mask]
            
            if len(actual_clean) == 0:
                return {'rmse': np.nan, 'mae': np.nan, 'mape': np.nan}
            
            rmse = np.sqrt(mean_squared_error(actual_clean, predicted_clean))
            mae = mean_absolute_error(actual_clean, predicted_clean)
            
            # MAPE calculation with handling for zero values
            mape = np.mean(np.abs((actual_clean - predicted_clean) / (actual_clean + 1e-8))) * 100
            
            return {
                'rmse': rmse,
                'mae': mae,
                'mape': mape
            }
        except Exception as e:
            print(f"Metrics calculation error: {e}")
            return {'rmse': np.nan, 'mae': np.nan, 'mape': np.nan}
    
    def forecast_all(self, df: pd.DataFrame, forecast_hours: int, target_col: str = 'Close') -> Dict:
        """Run all traditional forecasting models"""
        data, dates = self.prepare_data(df, target_col)
        
        results = {}
        
        # ARIMA
        arima_result = self.arima_forecast(data, forecast_hours)
        results['arima'] = arima_result
        
        # Moving Average
        ma_result = self.moving_average_forecast(data, forecast_hours)
        results['moving_average'] = ma_result
        
        # Exponential Smoothing
        es_result = self.exponential_smoothing_forecast(data, forecast_hours)
        results['exponential_smoothing'] = es_result
        
        # VAR (if we have multiple columns)
        if len(df.columns) > 1:
            var_result = self.var_forecast(df, forecast_hours)
            results['var'] = var_result
        
        return results
