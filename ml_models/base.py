"""
Base classes and utilities for forecasting models.
"""

import numpy as np
import pandas as pd
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Optional, Any
from sklearn.metrics import mean_squared_error, mean_absolute_error
import warnings
warnings.filterwarnings('ignore')


class BaseForecaster(ABC):
    """Abstract base class for all forecasting models."""
    
    def __init__(self, name: str):
        self.name = name
        self.is_fitted = False
        self.feature_columns = []
        
    @abstractmethod
    def fit(self, data: pd.DataFrame, target_column: str = 'close_price') -> 'BaseForecaster':
        """Fit the model to historical data."""
        pass
    
    @abstractmethod
    def predict(self, horizon: int, confidence_level: float = 0.95) -> Dict[str, Any]:
        """Generate predictions for the specified horizon."""
        pass
    
    @abstractmethod
    def evaluate(self, test_data: pd.DataFrame, target_column: str = 'close_price') -> Dict[str, float]:
        """Evaluate model performance on test data."""
        pass
    
    def get_feature_importance(self) -> Optional[Dict[str, float]]:
        """Get feature importance if available."""
        return None


class PerformanceMetrics:
    """Calculate various performance metrics for forecasting models."""
    
    @staticmethod
    def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """Calculate comprehensive performance metrics."""
        # Remove any NaN values
        mask = ~(np.isnan(y_true) | np.isnan(y_pred))
        y_true = y_true[mask]
        y_pred = y_pred[mask]
        
        if len(y_true) == 0:
            return {
                'rmse': np.nan,
                'mae': np.nan,
                'mape': np.nan,
                'mse': np.nan,
                'directional_accuracy': np.nan,
                'sharpe_ratio': np.nan
            }
        
        # Basic metrics
        mse = mean_squared_error(y_true, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_true, y_pred)
        
        # MAPE (Mean Absolute Percentage Error)
        mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
        
        # Directional accuracy
        true_direction = np.diff(y_true) > 0
        pred_direction = np.diff(y_pred) > 0
        directional_accuracy = np.mean(true_direction == pred_direction) * 100
        
        # Sharpe ratio (risk-adjusted return)
        returns_true = np.diff(y_true) / y_true[:-1]
        returns_pred = np.diff(y_pred) / y_pred[:-1]
        
        if np.std(returns_pred) > 0:
            sharpe_ratio = np.mean(returns_pred) / np.std(returns_pred) * np.sqrt(252)  # Annualized
        else:
            sharpe_ratio = 0.0
        
        return {
            'rmse': rmse,
            'mae': mae,
            'mape': mape,
            'mse': mse,
            'directional_accuracy': directional_accuracy,
            'sharpe_ratio': sharpe_ratio
        }


class DataPreprocessor:
    """Preprocess financial data for machine learning models."""
    
    @staticmethod
    def prepare_features(data: pd.DataFrame, target_column: str = 'close_price') -> Tuple[pd.DataFrame, List[str]]:
        """Prepare features for ML models."""
        df = data.copy()
        
        # Ensure date column is datetime
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
        
        # Create lagged features
        feature_columns = []
        
        # Price-based features
        if target_column in df.columns:
            for lag in [1, 2, 3, 5]:
                df[f'{target_column}_lag_{lag}'] = df[target_column].shift(lag)
                feature_columns.append(f'{target_column}_lag_{lag}')
        
        # Technical indicators
        if 'daily_return' in df.columns:
            df['daily_return_lag_1'] = df['daily_return'].shift(1)
            feature_columns.append('daily_return_lag_1')
        
        if 'volatility_5d' in df.columns:
            df['volatility_5d_lag_1'] = df['volatility_5d'].shift(1)
            feature_columns.append('volatility_5d_lag_1')
        
        if 'ma_5' in df.columns and 'ma_10' in df.columns:
            df['ma_ratio'] = df['ma_5'] / df['ma_10']
            df['ma_ratio_lag_1'] = df['ma_ratio'].shift(1)
            feature_columns.append('ma_ratio_lag_1')
        
        if 'volume_zscore_5d' in df.columns:
            df['volume_zscore_5d_lag_1'] = df['volume_zscore_5d'].shift(1)
            feature_columns.append('volume_zscore_5d_lag_1')
        
        # News sentiment features
        if 'news_count' in df.columns:
            df['news_count_lag_1'] = df['news_count'].shift(1)
            feature_columns.append('news_count_lag_1')
        
        if 'sent_compound_mean' in df.columns:
            df['sent_compound_mean_lag_1'] = df['sent_compound_mean'].shift(1)
            feature_columns.append('sent_compound_mean_lag_1')
        
        # Remove rows with NaN values
        df = df.dropna()
        
        return df, feature_columns
    
    @staticmethod
    def create_sequences(data: pd.DataFrame, feature_columns: List[str], 
                        target_column: str, sequence_length: int = 60) -> Tuple[np.ndarray, np.ndarray]:
        """Create sequences for LSTM/GRU models."""
        X, y = [], []
        
        for i in range(sequence_length, len(data)):
            X.append(data[feature_columns].iloc[i-sequence_length:i].values)
            y.append(data[target_column].iloc[i])
        
        return np.array(X), np.array(y)


class ModelEnsemble:
    """Ensemble of multiple forecasting models."""
    
    def __init__(self, models: List[BaseForecaster], weights: Optional[List[float]] = None):
        self.models = models
        self.weights = weights or [1.0 / len(models)] * len(models)
        self.is_fitted = False
        
    def fit(self, data: pd.DataFrame, target_column: str = 'close_price') -> 'ModelEnsemble':
        """Fit all models in the ensemble."""
        for model in self.models:
            model.fit(data, target_column)
        self.is_fitted = True
        return self
    
    def predict(self, horizon: int, confidence_level: float = 0.95) -> Dict[str, Any]:
        """Generate ensemble predictions."""
        if not self.is_fitted:
            raise ValueError("Ensemble must be fitted before making predictions")
        
        predictions = []
        confidences = []
        
        for model in self.models:
            pred = model.predict(horizon, confidence_level)
            predictions.append(pred['predictions'])
            confidences.append(pred.get('confidence_intervals', []))
        
        # Weighted average of predictions
        ensemble_pred = np.average(predictions, axis=0, weights=self.weights)
        
        # Average confidence intervals
        if confidences and all(len(ci) > 0 for ci in confidences):
            ensemble_conf = np.average(confidences, axis=0, weights=self.weights)
        else:
            ensemble_conf = None
        
        return {
            'predictions': ensemble_pred,
            'confidence_intervals': ensemble_conf,
            'model_predictions': dict(zip([m.name for m in self.models], predictions))
        }
    
    def evaluate(self, test_data: pd.DataFrame, target_column: str = 'close_price') -> Dict[str, float]:
        """Evaluate ensemble performance."""
        predictions = []
        
        for model in self.models:
            pred = model.predict(len(test_data), confidence_level=0.95)
            predictions.append(pred['predictions'])
        
        # Weighted average
        ensemble_pred = np.average(predictions, axis=0, weights=self.weights)
        
        return PerformanceMetrics.calculate_metrics(
            test_data[target_column].values, 
            ensemble_pred
        )
