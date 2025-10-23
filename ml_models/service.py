"""
Model factory and ensemble management for the forecasting application.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Type
from datetime import datetime, timedelta

from .base import BaseForecaster, ModelEnsemble
from .traditional import (
    ARIMAForecaster, 
    MovingAverageForecaster, 
    VARForecaster, 
    LinearRegressionForecaster
)
from .neural import LSTMForecaster, GRUForecaster, TransformerForecaster


class ModelFactory:
    """Factory class for creating forecasting models."""
    
    MODEL_REGISTRY = {
        'arima': ARIMAForecaster,
        'moving_average': MovingAverageForecaster,
        'var': VARForecaster,
        'linear_regression': LinearRegressionForecaster,
        'lstm': LSTMForecaster,
        'gru': GRUForecaster,
        'transformer': TransformerForecaster,
    }
    
    @classmethod
    def create_model(cls, model_name: str, **kwargs) -> BaseForecaster:
        """Create a forecasting model by name."""
        if model_name not in cls.MODEL_REGISTRY:
            raise ValueError(f"Unknown model: {model_name}. Available models: {list(cls.MODEL_REGISTRY.keys())}")
        
        model_class = cls.MODEL_REGISTRY[model_name]
        return model_class(**kwargs)
    
    @classmethod
    def get_available_models(cls) -> List[str]:
        """Get list of available model names."""
        return list(cls.MODEL_REGISTRY.keys())
    
    @classmethod
    def register_model(cls, name: str, model_class: Type[BaseForecaster]):
        """Register a new model class."""
        cls.MODEL_REGISTRY[name] = model_class


class ForecastingService:
    """Main service for managing forecasting operations."""
    
    def __init__(self):
        self.models: Dict[str, BaseForecaster] = {}
        self.ensembles: Dict[str, ModelEnsemble] = {}
        self.model_factory = ModelFactory()
        
    def create_model(self, model_name: str, model_id: str = None, **kwargs) -> str:
        """Create and register a forecasting model."""
        if model_id is None:
            model_id = f"{model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        model = self.model_factory.create_model(model_name, **kwargs)
        self.models[model_id] = model
        
        return model_id
    
    def create_ensemble(self, model_ids: List[str], ensemble_id: str = None, 
                       weights: Optional[List[float]] = None) -> str:
        """Create an ensemble of models."""
        if ensemble_id is None:
            ensemble_id = f"ensemble_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        models = [self.models[mid] for mid in model_ids if mid in self.models]
        if len(models) == 0:
            raise ValueError("No valid models found for ensemble")
        
        ensemble = ModelEnsemble(models, weights)
        self.ensembles[ensemble_id] = ensemble
        
        return ensemble_id
    
    def train_model(self, model_id: str, data: pd.DataFrame, target_column: str = 'close_price') -> Dict[str, Any]:
        """Train a specific model."""
        if model_id not in self.models:
            raise ValueError(f"Model {model_id} not found")
        
        model = self.models[model_id]
        model.fit(data, target_column)
        
        return {
            'model_id': model_id,
            'model_name': model.name,
            'is_fitted': model.is_fitted,
            'feature_columns': getattr(model, 'feature_columns', [])
        }
    
    def train_ensemble(self, ensemble_id: str, data: pd.DataFrame, target_column: str = 'close_price') -> Dict[str, Any]:
        """Train an ensemble of models."""
        if ensemble_id not in self.ensembles:
            raise ValueError(f"Ensemble {ensemble_id} not found")
        
        ensemble = self.ensembles[ensemble_id]
        ensemble.fit(data, target_column)
        
        return {
            'ensemble_id': ensemble_id,
            'is_fitted': ensemble.is_fitted,
            'model_count': len(ensemble.models)
        }
    
    def predict(self, model_id: str, horizon: int, confidence_level: float = 0.95) -> Dict[str, Any]:
        """Generate predictions using a specific model."""
        if model_id not in self.models:
            raise ValueError(f"Model {model_id} not found")
        
        model = self.models[model_id]
        if not model.is_fitted:
            raise ValueError(f"Model {model_id} is not fitted")
        
        predictions = model.predict(horizon, confidence_level)
        
        return {
            'model_id': model_id,
            'model_name': model.name,
            'horizon': horizon,
            'confidence_level': confidence_level,
            'predictions': predictions['predictions'].tolist(),
            'confidence_intervals': predictions.get('confidence_intervals'),
            'model_info': predictions.get('model_info', {})
        }
    
    def predict_ensemble(self, ensemble_id: str, horizon: int, confidence_level: float = 0.95) -> Dict[str, Any]:
        """Generate predictions using an ensemble."""
        if ensemble_id not in self.ensembles:
            raise ValueError(f"Ensemble {ensemble_id} not found")
        
        ensemble = self.ensembles[ensemble_id]
        if not ensemble.is_fitted:
            raise ValueError(f"Ensemble {ensemble_id} is not fitted")
        
        predictions = ensemble.predict(horizon, confidence_level)
        
        return {
            'ensemble_id': ensemble_id,
            'horizon': horizon,
            'confidence_level': confidence_level,
            'predictions': predictions['predictions'].tolist(),
            'confidence_intervals': predictions.get('confidence_intervals'),
            'individual_predictions': predictions.get('model_predictions', {})
        }
    
    def evaluate_model(self, model_id: str, test_data: pd.DataFrame, target_column: str = 'close_price') -> Dict[str, Any]:
        """Evaluate a model's performance."""
        if model_id not in self.models:
            raise ValueError(f"Model {model_id} not found")
        
        model = self.models[model_id]
        if not model.is_fitted:
            raise ValueError(f"Model {model_id} is not fitted")
        
        metrics = model.evaluate(test_data, target_column)
        
        return {
            'model_id': model_id,
            'model_name': model.name,
            'metrics': metrics,
            'evaluation_date': datetime.now().isoformat()
        }
    
    def evaluate_ensemble(self, ensemble_id: str, test_data: pd.DataFrame, target_column: str = 'close_price') -> Dict[str, Any]:
        """Evaluate an ensemble's performance."""
        if ensemble_id not in self.ensembles:
            raise ValueError(f"Ensemble {ensemble_id} not found")
        
        ensemble = self.ensembles[ensemble_id]
        if not ensemble.is_fitted:
            raise ValueError(f"Ensemble {ensemble_id} is not fitted")
        
        metrics = ensemble.evaluate(test_data, target_column)
        
        return {
            'ensemble_id': ensemble_id,
            'metrics': metrics,
            'evaluation_date': datetime.now().isoformat()
        }
    
    def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """Get information about a specific model."""
        if model_id not in self.models:
            raise ValueError(f"Model {model_id} not found")
        
        model = self.models[model_id]
        
        return {
            'model_id': model_id,
            'model_name': model.name,
            'is_fitted': model.is_fitted,
            'feature_columns': getattr(model, 'feature_columns', []),
            'model_type': type(model).__name__
        }
    
    def list_models(self) -> List[Dict[str, Any]]:
        """List all available models."""
        return [self.get_model_info(model_id) for model_id in self.models.keys()]
    
    def list_ensembles(self) -> List[Dict[str, Any]]:
        """List all available ensembles."""
        return [
            {
                'ensemble_id': ensemble_id,
                'is_fitted': ensemble.is_fitted,
                'model_count': len(ensemble.models),
                'model_names': [model.name for model in ensemble.models]
            }
            for ensemble_id, ensemble in self.ensembles.items()
        ]
    
    def delete_model(self, model_id: str) -> bool:
        """Delete a model."""
        if model_id in self.models:
            del self.models[model_id]
            return True
        return False
    
    def delete_ensemble(self, ensemble_id: str) -> bool:
        """Delete an ensemble."""
        if ensemble_id in self.ensembles:
            del self.ensembles[ensemble_id]
            return True
        return False


class ForecastScheduler:
    """Schedule and manage periodic forecasting tasks."""
    
    def __init__(self, forecasting_service: ForecastingService):
        self.forecasting_service = forecasting_service
        self.scheduled_tasks = {}
    
    def schedule_forecast(self, model_id: str, instrument_symbol: str, 
                         horizon: int, frequency: str = 'daily') -> str:
        """Schedule periodic forecasts for an instrument."""
        task_id = f"{model_id}_{instrument_symbol}_{frequency}"
        
        self.scheduled_tasks[task_id] = {
            'model_id': model_id,
            'instrument_symbol': instrument_symbol,
            'horizon': horizon,
            'frequency': frequency,
            'last_run': None,
            'next_run': self._calculate_next_run(frequency)
        }
        
        return task_id
    
    def _calculate_next_run(self, frequency: str) -> datetime:
        """Calculate the next run time based on frequency."""
        now = datetime.now()
        
        if frequency == 'hourly':
            return now + timedelta(hours=1)
        elif frequency == 'daily':
            return now + timedelta(days=1)
        elif frequency == 'weekly':
            return now + timedelta(weeks=1)
        else:
            return now + timedelta(days=1)  # Default to daily
    
    def run_scheduled_forecasts(self) -> List[Dict[str, Any]]:
        """Run all due scheduled forecasts."""
        results = []
        now = datetime.now()
        
        for task_id, task in self.scheduled_tasks.items():
            if task['next_run'] <= now:
                try:
                    # Generate forecast
                    forecast = self.forecasting_service.predict(
                        task['model_id'], 
                        task['horizon']
                    )
                    
                    # Update task
                    task['last_run'] = now
                    task['next_run'] = self._calculate_next_run(task['frequency'])
                    
                    results.append({
                        'task_id': task_id,
                        'status': 'success',
                        'forecast': forecast,
                        'instrument_symbol': task['instrument_symbol']
                    })
                    
                except Exception as e:
                    results.append({
                        'task_id': task_id,
                        'status': 'error',
                        'error': str(e),
                        'instrument_symbol': task['instrument_symbol']
                    })
        
        return results
    
    def get_scheduled_tasks(self) -> Dict[str, Any]:
        """Get all scheduled tasks."""
        return self.scheduled_tasks.copy()
