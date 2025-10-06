"""
Ensemble forecasting model that combines traditional and neural approaches
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error
from .traditional_models import TraditionalForecaster
from .neural_models import NeuralForecaster
import warnings
warnings.filterwarnings('ignore')


class EnsembleForecaster:
    """Ensemble forecasting model combining multiple approaches"""
    
    def __init__(self, sequence_length: int = 60):
        self.traditional_forecaster = TraditionalForecaster()
        self.neural_forecaster = NeuralForecaster(sequence_length)
        self.ensemble_weights = {}
        
    def prepare_ensemble_features(self, df: pd.DataFrame, forecast_hours: int) -> Dict:
        """Prepare features from all models for ensemble"""
        data, dates = self.traditional_forecaster.prepare_data(df)
        
        # Get forecasts from all models
        traditional_results = self.traditional_forecaster.forecast_all(df, forecast_hours)
        neural_results = self.neural_forecaster.forecast_all(data, forecast_hours)
        
        # Combine all forecasts
        all_forecasts = {}
        all_forecasts.update(traditional_results)
        all_forecasts.update(neural_results)
        
        return all_forecasts
    
    def weighted_average_ensemble(self, forecasts: Dict, weights: Dict = None) -> np.ndarray:
        """Create weighted average ensemble"""
        if weights is None:
            # Equal weights for all models
            weights = {key: 1.0 for key in forecasts.keys()}
            total_weight = sum(weights.values())
            weights = {key: weight/total_weight for key, weight in weights.items()}
        
        # Calculate weighted average
        ensemble_forecast = np.zeros(len(list(forecasts.values())[0]['forecast']))
        
        for model_name, result in forecasts.items():
            if 'forecast' in result and 'error' not in result:
                weight = weights.get(model_name, 0)
                ensemble_forecast += weight * result['forecast']
        
        return ensemble_forecast
    
    def stacking_ensemble(self, df: pd.DataFrame, forecast_hours: int) -> Dict:
        """Create stacking ensemble using meta-learner"""
        try:
            # Prepare training data for meta-learner
            data, dates = self.traditional_forecaster.prepare_data(df)
            
            # Use first 80% for training meta-learner
            train_size = int(len(data) * 0.8)
            train_data = data[:train_size]
            test_data = data[train_size:]
            
            # Generate predictions for training set
            train_df = df.iloc[:train_size]
            train_forecasts = self.prepare_ensemble_features(train_df, len(test_data))
            
            # Prepare features for meta-learner
            X_meta = []
            for model_name, result in train_forecasts.items():
                if 'forecast' in result and 'error' not in result:
                    X_meta.append(result['forecast'])
            
            if len(X_meta) == 0:
                return {'forecast': np.full(forecast_hours, data[-1]), 'error': 'No valid forecasts'}
            
            X_meta = np.array(X_meta).T
            y_meta = test_data
            
            # Train meta-learner
            meta_learner = RandomForestRegressor(n_estimators=100, random_state=42)
            meta_learner.fit(X_meta, y_meta)
            
            # Generate final forecast
            final_forecasts = self.prepare_ensemble_features(df, forecast_hours)
            
            X_final = []
            for model_name, result in final_forecasts.items():
                if 'forecast' in result and 'error' not in result:
                    X_final.append(result['forecast'])
            
            X_final = np.array(X_final).T
            ensemble_forecast = meta_learner.predict(X_final)
            
            return {
                'forecast': ensemble_forecast,
                'meta_learner': meta_learner,
                'feature_importance': dict(zip(list(final_forecasts.keys()), meta_learner.feature_importances_))
            }
            
        except Exception as e:
            print(f"Stacking ensemble error: {e}")
            return {'forecast': np.full(forecast_hours, df['Close'].iloc[-1]), 'error': str(e)}
    
    def adaptive_ensemble(self, df: pd.DataFrame, forecast_hours: int) -> Dict:
        """Create adaptive ensemble that adjusts weights based on recent performance"""
        try:
            data, dates = self.traditional_forecaster.prepare_data(df)
            
            # Use last 20% of data for performance evaluation
            eval_size = int(len(data) * 0.2)
            if eval_size < 10:
                eval_size = min(10, len(data) - 1)
            
            eval_data = data[-eval_size:]
            train_data = data[:-eval_size]
            
            # Generate forecasts for evaluation period
            eval_df = df.iloc[-eval_size:]
            eval_forecasts = self.prepare_ensemble_features(eval_df, eval_size)
            
            # Calculate performance metrics for each model
            model_performance = {}
            for model_name, result in eval_forecasts.items():
                if 'forecast' in result and 'error' not in result:
                    metrics = self.traditional_forecaster.calculate_metrics(eval_data, result['forecast'])
                    # Use inverse RMSE as weight (lower RMSE = higher weight)
                    model_performance[model_name] = 1.0 / (metrics['rmse'] + 1e-8)
            
            # Normalize weights
            total_performance = sum(model_performance.values())
            if total_performance > 0:
                adaptive_weights = {key: perf/total_performance for key, perf in model_performance.items()}
            else:
                adaptive_weights = {key: 1.0/len(model_performance) for key in model_performance.keys()}
            
            # Generate final forecast with adaptive weights
            final_forecasts = self.prepare_ensemble_features(df, forecast_hours)
            ensemble_forecast = self.weighted_average_ensemble(final_forecasts, adaptive_weights)
            
            return {
                'forecast': ensemble_forecast,
                'adaptive_weights': adaptive_weights,
                'model_performance': model_performance
            }
            
        except Exception as e:
            print(f"Adaptive ensemble error: {e}")
            return {'forecast': np.full(forecast_hours, df['Close'].iloc[-1]), 'error': str(e)}
    
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
    
    def forecast_all_ensembles(self, df: pd.DataFrame, forecast_hours: int) -> Dict:
        """Run all ensemble forecasting methods"""
        results = {}
        
        # Weighted Average Ensemble
        forecasts = self.prepare_ensemble_features(df, forecast_hours)
        weighted_forecast = self.weighted_average_ensemble(forecasts)
        results['weighted_average'] = {'forecast': weighted_forecast}
        
        # Stacking Ensemble
        stacking_result = self.stacking_ensemble(df, forecast_hours)
        results['stacking'] = stacking_result
        
        # Adaptive Ensemble
        adaptive_result = self.adaptive_ensemble(df, forecast_hours)
        results['adaptive'] = adaptive_result
        
        return results
