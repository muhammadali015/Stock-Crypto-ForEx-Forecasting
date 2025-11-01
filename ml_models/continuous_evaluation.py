"""
Continuous evaluation system for monitoring model performance over time.
Tracks metrics (MAE, RMSE, MAPE) as new ground-truth data becomes available.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from .base import PerformanceMetrics


class ContinuousEvaluator:
    """Continuously evaluates model predictions against actual values."""
    
    def __init__(self, model_id: int, instrument_id: int):
        self.model_id = model_id
        self.instrument_id = instrument_id
        self.evaluation_history = []
        self.error_tracking = []
        
    def evaluate_prediction(self, forecast_id: int, predictions: List[float],
                          actual_values: List[float], evaluation_date: datetime) -> Dict[str, Any]:
        """Evaluate predictions against actual values."""
        if len(predictions) != len(actual_values):
            raise ValueError("Predictions and actual values must have the same length")
        
        # Calculate metrics
        metrics = PerformanceMetrics.calculate_metrics(
            np.array(actual_values),
            np.array(predictions)
        )
        
        # Calculate individual errors for visualization
        errors = []
        error_percentages = []
        
        for i in range(len(predictions)):
            error = abs(predictions[i] - actual_values[i])
            error_pct = (error / actual_values[i]) * 100 if actual_values[i] != 0 else 0
            
            errors.append({
                'forecast_id': forecast_id,
                'prediction_index': i,
                'predicted_value': predictions[i],
                'actual_value': actual_values[i],
                'error_value': error,
                'error_percentage': error_pct,
                'evaluation_date': evaluation_date.isoformat()
            })
            
            error_percentages.append(error_pct)
        
        # Store evaluation
        evaluation_record = {
            'model_id': self.model_id,
            'instrument_id': self.instrument_id,
            'evaluation_date': evaluation_date.isoformat(),
            'forecast_id': forecast_id,
            'metrics': metrics,
            'predictions': predictions,
            'actual_values': actual_values,
            'errors': errors
        }
        
        self.evaluation_history.append(evaluation_record)
        self.error_tracking.extend(errors)
        
        return evaluation_record
    
    def get_error_statistics(self, window_size: Optional[int] = None) -> Dict[str, float]:
        """Get error statistics over a time window."""
        if window_size:
            recent_errors = self.error_tracking[-window_size:]
        else:
            recent_errors = self.error_tracking
        
        if len(recent_errors) == 0:
            return {
                'mean_error': 0.0,
                'std_error': 0.0,
                'mean_error_pct': 0.0,
                'max_error': 0.0,
                'min_error': 0.0
            }
        
        error_values = [e['error_value'] for e in recent_errors]
        error_pcts = [e['error_percentage'] for e in recent_errors]
        
        return {
            'mean_error': np.mean(error_values),
            'std_error': np.std(error_values),
            'mean_error_pct': np.mean(error_pcts),
            'max_error': np.max(error_values),
            'min_error': np.min(error_values),
            'median_error': np.median(error_values),
            'q95_error': np.percentile(error_values, 95)
        }
    
    def get_metrics_history(self) -> pd.DataFrame:
        """Get metrics history as a DataFrame."""
        if len(self.evaluation_history) == 0:
            return pd.DataFrame()
        
        records = []
        for eval_record in self.evaluation_history:
            record = {
                'date': eval_record['evaluation_date'],
                'rmse': eval_record['metrics']['rmse'],
                'mae': eval_record['metrics']['mae'],
                'mape': eval_record['metrics']['mape'],
                'directional_accuracy': eval_record['metrics'].get('directional_accuracy', 0)
            }
            records.append(record)
        
        return pd.DataFrame(records)
    
    def check_degradation(self, threshold_mape: float = 5.0) -> Dict[str, Any]:
        """Check if model performance has degraded."""
        if len(self.evaluation_history) < 5:
            return {'degraded': False, 'reason': 'insufficient_data'}
        
        # Compare recent metrics to historical average
        recent_metrics = self.evaluation_history[-5:]
        historical_metrics = self.evaluation_history[:-5] if len(self.evaluation_history) > 5 else recent_metrics
        
        recent_mape = np.mean([m['metrics']['mape'] for m in recent_metrics])
        historical_mape = np.mean([m['metrics']['mape'] for m in historical_metrics])
        
        degradation_ratio = recent_mape / (historical_mape + 1e-6)
        
        return {
            'degraded': recent_mape > threshold_mape or degradation_ratio > 1.5,
            'recent_mape': recent_mape,
            'historical_mape': historical_mape,
            'degradation_ratio': degradation_ratio,
            'threshold_exceeded': recent_mape > threshold_mape
        }
    
    def get_error_overlay_data(self, forecast_id: int) -> List[Dict[str, Any]]:
        """Get error data formatted for chart overlay visualization."""
        errors_for_forecast = [
            e for e in self.error_tracking 
            if e['forecast_id'] == forecast_id
        ]
        
        return sorted(errors_for_forecast, key=lambda x: x['prediction_index'])


class MonitoringDashboard:
    """Aggregates evaluation metrics across multiple models for dashboard visualization."""
    
    def __init__(self):
        self.evaluators = {}  # {model_id: ContinuousEvaluator}
        
    def register_model(self, model_id: int, instrument_id: int) -> ContinuousEvaluator:
        """Register a model for monitoring."""
        evaluator = ContinuousEvaluator(model_id, instrument_id)
        self.evaluators[model_id] = evaluator
        return evaluator
    
    def get_all_metrics(self) -> Dict[int, Dict[str, Any]]:
        """Get metrics for all registered models."""
        all_metrics = {}
        
        for model_id, evaluator in self.evaluators.items():
            metrics_df = evaluator.get_metrics_history()
            error_stats = evaluator.get_error_statistics()
            degradation = evaluator.check_degradation()
            
            all_metrics[model_id] = {
                'metrics_history': metrics_df.to_dict('records') if not metrics_df.empty else [],
                'error_statistics': error_stats,
                'degradation_status': degradation,
                'total_evaluations': len(evaluator.evaluation_history)
            }
        
        return all_metrics
    
    def get_comparison_metrics(self) -> pd.DataFrame:
        """Get comparison metrics across all models."""
        comparison_data = []
        
        for model_id, evaluator in self.evaluators.items():
            if len(evaluator.evaluation_history) > 0:
                latest = evaluator.evaluation_history[-1]
                comparison_data.append({
                    'model_id': model_id,
                    'rmse': latest['metrics']['rmse'],
                    'mae': latest['metrics']['mae'],
                    'mape': latest['metrics']['mape'],
                    'directional_accuracy': latest['metrics'].get('directional_accuracy', 0),
                    'last_evaluation': latest['evaluation_date']
                })
        
        return pd.DataFrame(comparison_data)
    
    def detect_anomalies(self, threshold_sigma: float = 3.0) -> List[Dict[str, Any]]:
        """Detect anomalous performance across all models."""
        anomalies = []
        
        for model_id, evaluator in self.evaluators.items():
            error_stats = evaluator.get_error_statistics()
            
            # Check if error exceeds threshold
            if error_stats['mean_error'] > threshold_sigma * error_stats['std_error']:
                anomalies.append({
                    'model_id': model_id,
                    'type': 'high_error',
                    'severity': 'warning',
                    'mean_error': error_stats['mean_error'],
                    'threshold': threshold_sigma * error_stats['std_error']
                })
            
            # Check degradation
            degradation = evaluator.check_degradation()
            if degradation['degraded']:
                anomalies.append({
                    'model_id': model_id,
                    'type': 'performance_degradation',
                    'severity': 'critical',
                    'degradation_ratio': degradation['degradation_ratio']
                })
        
        return anomalies
