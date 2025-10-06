"""
Main ML orchestrator that coordinates all forecasting models
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
import os

from .traditional_models import TraditionalForecaster
from .neural_models import NeuralForecaster
from .ensemble_models import EnsembleForecaster


class MLOrchestrator:
    """Main orchestrator for all forecasting models"""
    
    def __init__(self, sequence_length: int = 60):
        self.traditional_forecaster = TraditionalForecaster()
        self.neural_forecaster = NeuralForecaster(sequence_length)
        self.ensemble_forecaster = EnsembleForecaster(sequence_length)
        self.results_cache = {}
        
    def prepare_data(self, df: pd.DataFrame, target_col: str = 'Close') -> pd.DataFrame:
        """Prepare and clean data for forecasting"""
        # Ensure Date column is datetime
        df = df.copy()
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values('Date')
        
        # Remove any rows with missing target values
        df = df.dropna(subset=[target_col])
        
        # Ensure we have enough data
        if len(df) < 30:
            raise ValueError(f"Insufficient data: need at least 30 observations, got {len(df)}")
        
        return df
    
    def generate_forecast_dates(self, last_date: datetime, forecast_hours: int) -> List[datetime]:
        """Generate future dates for forecast"""
        forecast_dates = []
        current_date = last_date
        
        for i in range(forecast_hours):
            # Add hours (assuming hourly data)
            current_date += timedelta(hours=1)
            forecast_dates.append(current_date)
        
        return forecast_dates
    
    def run_all_models(self, df: pd.DataFrame, forecast_hours: int, 
                      target_col: str = 'Close') -> Dict:
        """Run all forecasting models and return results"""
        
        # Prepare data
        clean_df = self.prepare_data(df, target_col)
        data, dates = self.traditional_forecaster.prepare_data(clean_df, target_col)
        
        # Generate forecast dates
        last_date = dates[-1]
        forecast_dates = self.generate_forecast_dates(last_date, forecast_hours)
        
        results = {
            'metadata': {
                'forecast_hours': forecast_hours,
                'last_date': last_date.isoformat(),
                'forecast_dates': [d.isoformat() for d in forecast_dates],
                'data_points': len(data),
                'target_column': target_col
            },
            'forecasts': {},
            'performance_metrics': {}
        }
        
        # Traditional Models
        print("Running traditional models...")
        traditional_results = self.traditional_forecaster.forecast_all(clean_df, forecast_hours, target_col)
        results['forecasts']['traditional'] = traditional_results
        
        # Neural Models
        print("Running neural models...")
        neural_results = self.neural_forecaster.forecast_all(data, forecast_hours)
        results['forecasts']['neural'] = neural_results
        
        # Ensemble Models
        print("Running ensemble models...")
        ensemble_results = self.ensemble_forecaster.forecast_all_ensembles(clean_df, forecast_hours)
        results['forecasts']['ensemble'] = ensemble_results
        
        # Calculate performance metrics for each model
        print("Calculating performance metrics...")
        self._calculate_all_metrics(results, data, forecast_hours)
        
        return results
    
    def _calculate_all_metrics(self, results: Dict, actual_data: np.ndarray, forecast_hours: int):
        """Calculate performance metrics for all models"""
        
        # Use last portion of actual data for validation
        validation_size = min(forecast_hours, len(actual_data) // 4)
        if validation_size < 5:
            validation_size = min(5, len(actual_data) - 1)
        
        validation_data = actual_data[-validation_size:]
        
        # Calculate metrics for each model category
        for category, models in results['forecasts'].items():
            results['performance_metrics'][category] = {}
            
            for model_name, model_result in models.items():
                if 'forecast' in model_result and 'error' not in model_result:
                    # Use first 'validation_size' points of forecast for comparison
                    forecast_subset = model_result['forecast'][:validation_size]
                    
                    if category == 'traditional':
                        metrics = self.traditional_forecaster.calculate_metrics(validation_data, forecast_subset)
                    elif category == 'neural':
                        metrics = self.neural_forecaster.calculate_metrics(validation_data, forecast_subset)
                    else:  # ensemble
                        metrics = self.ensemble_forecaster.calculate_metrics(validation_data, forecast_subset)
                    
                    results['performance_metrics'][category][model_name] = metrics
    
    def get_best_model(self, results: Dict) -> Dict:
        """Determine the best performing model based on RMSE"""
        best_model = None
        best_rmse = float('inf')
        best_category = None
        best_model_name = None
        
        for category, models in results['performance_metrics'].items():
            for model_name, metrics in models.items():
                if metrics['rmse'] < best_rmse and not np.isnan(metrics['rmse']):
                    best_rmse = metrics['rmse']
                    best_model = results['forecasts'][category][model_name]
                    best_category = category
                    best_model_name = model_name
        
        return {
            'model': best_model,
            'category': best_category,
            'model_name': best_model_name,
            'rmse': best_rmse,
            'metrics': results['performance_metrics'][best_category][best_model_name] if best_category else {}
        }
    
    def save_results(self, results: Dict, filepath: str):
        """Save forecasting results to JSON file"""
        # Convert numpy arrays to lists for JSON serialization
        serializable_results = self._make_json_serializable(results)
        
        with open(filepath, 'w') as f:
            json.dump(serializable_results, f, indent=2)
    
    def _make_json_serializable(self, obj):
        """Convert numpy arrays and other non-serializable objects to JSON-compatible formats"""
        if isinstance(obj, dict):
            return {key: self._make_json_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_serializable(item) for item in obj]
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.integer, np.floating)):
            return obj.item()
        elif hasattr(obj, 'isoformat'):  # datetime objects
            return obj.isoformat()
        else:
            return obj
    
    def load_results(self, filepath: str) -> Dict:
        """Load forecasting results from JSON file"""
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def forecast_single_instrument(self, df: pd.DataFrame, forecast_hours: int, 
                                 instrument_name: str, save_path: Optional[str] = None) -> Dict:
        """Complete forecasting pipeline for a single instrument"""
        
        print(f"Starting forecast for {instrument_name} - {forecast_hours} hours ahead")
        
        # Run all models
        results = self.run_all_models(df, forecast_hours)
        
        # Add instrument metadata
        results['metadata']['instrument'] = instrument_name
        results['metadata']['timestamp'] = datetime.now().isoformat()
        
        # Get best model
        best_model_info = self.get_best_model(results)
        results['best_model'] = best_model_info
        
        # Save results if path provided
        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            self.save_results(results, save_path)
            print(f"Results saved to {save_path}")
        
        print(f"Forecast completed. Best model: {best_model_info['category']}/{best_model_info['model_name']} (RMSE: {best_model_info['rmse']:.4f})")
        
        return results
