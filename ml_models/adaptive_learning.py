"""
Adaptive learning mechanisms for continuous model updates.
Supports incremental updates, fine-tuning, and scheduled retraining.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import os
import pickle
from abc import ABC, abstractmethod

from .base import BaseForecaster, PerformanceMetrics


class AdaptiveLearner:
    """Manages adaptive learning strategies for forecasting models."""
    
    def __init__(self, model: BaseForecaster, learning_strategy: str = 'incremental'):
        self.model = model
        self.learning_strategy = learning_strategy  # 'incremental', 'fine_tune', 'retrain'
        self.model_versions = []
        self.performance_history = []
        
    def update_with_new_data(self, new_data: pd.DataFrame, target_column: str = 'close_price',
                            batch_size: int = 32, epochs: int = 10) -> Dict[str, Any]:
        """Update model with new incoming data."""
        if self.learning_strategy == 'incremental':
            return self._incremental_update(new_data, target_column, batch_size, epochs)
        elif self.learning_strategy == 'fine_tune':
            return self._fine_tune(new_data, target_column, batch_size, epochs)
        elif self.learning_strategy == 'retrain':
            return self._retrain(new_data, target_column)
        else:
            raise ValueError(f"Unknown learning strategy: {self.learning_strategy}")
    
    def _incremental_update(self, new_data: pd.DataFrame, target_column: str,
                           batch_size: int, epochs: int) -> Dict[str, Any]:
        """Incremental learning: update model with small batches of new data."""
        if not hasattr(self.model, 'model') or self.model.model is None:
            raise ValueError("Model must be fitted before incremental update")
        
        # Prepare new data
        df, feature_columns = self._prepare_features(new_data, target_column)
        
        if len(df) == 0:
            return {'status': 'no_data', 'updated': False}
        
        # Get scalers from the model
        feature_scaler = getattr(self.model, 'feature_scaler', None)
        scaler = getattr(self.model, 'scaler', None)
        
        if feature_scaler is None or scaler is None:
            return {'status': 'no_scaler', 'updated': False}
        
        # Scale new data
        feature_data = df[feature_columns].values
        target_data = df[target_column].values.reshape(-1, 1)
        
        feature_data_scaled = feature_scaler.transform(feature_data)
        target_data_scaled = scaler.transform(target_data)
        
        # Create sequences for neural models
        if hasattr(self.model, 'sequence_length'):
            sequence_length = self.model.sequence_length
            X_new, y_new = self._create_sequences(
                pd.DataFrame(feature_data_scaled, columns=feature_columns),
                feature_columns,
                target_column,
                sequence_length
            )
            y_new = y_new.reshape(-1, 1)
        else:
            # For non-sequence models
            X_new = feature_data_scaled
            y_new = target_data_scaled
        
        # Fine-tune the model with new data
        try:
            history = self.model.model.fit(
                X_new, y_new,
                epochs=epochs,
                batch_size=batch_size,
                verbose=0,
                validation_split=0.2 if len(X_new) > 10 else 0.0
            )
            
            return {
                'status': 'success',
                'updated': True,
                'samples_processed': len(X_new),
                'epochs': epochs,
                'loss': history.history.get('loss', [])[-1] if hasattr(history, 'history') else None
            }
        except Exception as e:
            return {
                'status': 'error',
                'updated': False,
                'error': str(e)
            }
    
    def _fine_tune(self, new_data: pd.DataFrame, target_column: str,
                  batch_size: int, epochs: int) -> Dict[str, Any]:
        """Fine-tuning: train with lower learning rate on new data."""
        # Reduce learning rate for fine-tuning
        if hasattr(self.model.model, 'optimizer'):
            original_lr = float(self.model.model.optimizer.learning_rate.numpy())
            self.model.model.optimizer.learning_rate.assign(original_lr * 0.1)
        
        result = self._incremental_update(new_data, target_column, batch_size, epochs)
        
        # Restore original learning rate
        if hasattr(self.model.model, 'optimizer'):
            self.model.model.optimizer.learning_rate.assign(original_lr)
        
        return result
    
    def _retrain(self, new_data: pd.DataFrame, target_column: str) -> Dict[str, Any]:
        """Full retraining: retrain model from scratch with all available data."""
        # This would require keeping all historical data
        # For now, retrain with new data only
        try:
            self.model.fit(new_data, target_column)
            return {
                'status': 'success',
                'updated': True,
                'samples_processed': len(new_data)
            }
        except Exception as e:
            return {
                'status': 'error',
                'updated': False,
                'error': str(e)
            }
    
    def _prepare_features(self, data: pd.DataFrame, target_column: str) -> Tuple[pd.DataFrame, List[str]]:
        """Prepare features similar to DataPreprocessor."""
        from .base import DataPreprocessor
        return DataPreprocessor.prepare_features(data, target_column)
    
    def _create_sequences(self, data: pd.DataFrame, feature_columns: List[str],
                         target_column: str, sequence_length: int) -> Tuple[np.ndarray, np.ndarray]:
        """Create sequences for neural models."""
        from .base import DataPreprocessor
        return DataPreprocessor.create_sequences(data, feature_columns, target_column, sequence_length)
    
    def save_version(self, version_number: int, model_path: str, 
                    training_metrics: Dict[str, float]) -> Dict[str, Any]:
        """Save a version of the model."""
        version_info = {
            'version_number': version_number,
            'model_path': model_path,
            'created_at': datetime.now().isoformat(),
            'training_metrics': training_metrics
        }
        self.model_versions.append(version_info)
        return version_info
    
    def get_performance_history(self) -> List[Dict[str, Any]]:
        """Get performance history over time."""
        return self.performance_history
    
    def add_performance_record(self, metrics: Dict[str, float], evaluation_date: datetime):
        """Record performance metrics."""
        self.performance_history.append({
            'date': evaluation_date.isoformat(),
            'metrics': metrics
        })


class RollingWindowRetrainer:
    """Retrains models using a rolling window of data."""
    
    def __init__(self, window_size: int = 100, retrain_frequency: int = 24):
        self.window_size = window_size  # Number of data points to keep
        self.retrain_frequency = retrain_frequency  # Retrain every N hours
        self.last_retrain_time = None
        
    def should_retrain(self) -> bool:
        """Check if model should be retrained based on frequency."""
        if self.last_retrain_time is None:
            return True
        
        time_since_last = (datetime.now() - self.last_retrain_time).total_seconds() / 3600
        return time_since_last >= self.retrain_frequency
    
    def get_training_window(self, data: pd.DataFrame) -> pd.DataFrame:
        """Get the rolling window of data for training."""
        return data.tail(self.window_size).copy()
    
    def retrain(self, model: BaseForecaster, data: pd.DataFrame, 
               target_column: str = 'close_price') -> Dict[str, Any]:
        """Retrain model with rolling window."""
        window_data = self.get_training_window(data)
        model.fit(window_data, target_column)
        self.last_retrain_time = datetime.now()
        
        return {
            'status': 'success',
            'window_size': len(window_data),
            'retrained_at': self.last_retrain_time.isoformat()
        }


class EnsembleAdaptiveWeights:
    """Dynamically adjusts ensemble weights based on recent performance."""
    
    def __init__(self, models: List[BaseForecaster], initial_weights: Optional[List[float]] = None):
        self.models = models
        self.weights = initial_weights or [1.0 / len(models)] * len(models)
        self.performance_window = []
        self.window_size = 20  # Track last 20 evaluations
        
    def update_weights(self, recent_errors: List[List[float]]) -> List[float]:
        """Update weights based on recent prediction errors."""
        if len(recent_errors) == 0 or len(recent_errors[0]) != len(self.models):
            return self.weights
        
        # Calculate inverse RMSE for each model (lower error = higher weight)
        model_errors = []
        for model_idx in range(len(self.models)):
            errors = [errors_list[model_idx] for errors_list in recent_errors]
            rmse = np.sqrt(np.mean([e**2 for e in errors]))
            model_errors.append(rmse)
        
        # Convert errors to weights (inverse, normalized)
        inverse_errors = [1.0 / (e + 1e-6) for e in model_errors]
        total = sum(inverse_errors)
        self.weights = [w / total for w in inverse_errors]
        
        return self.weights
    
    def add_performance(self, errors: List[float]):
        """Add new performance data."""
        self.performance_window.append(errors)
        if len(self.performance_window) > self.window_size:
            self.performance_window.pop(0)
        
        # Update weights
        if len(self.performance_window) >= 5:  # Need at least 5 evaluations
            self.update_weights(self.performance_window)
    
    def get_weights(self) -> List[float]:
        """Get current ensemble weights."""
        return self.weights.copy()
