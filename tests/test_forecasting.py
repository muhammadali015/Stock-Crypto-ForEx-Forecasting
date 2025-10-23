"""
Unit tests for the FinTech forecasting application.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml_models.base import BaseForecaster, PerformanceMetrics, DataPreprocessor, ModelEnsemble
from ml_models.traditional import ARIMAForecaster, MovingAverageForecaster, LinearRegressionForecaster
from ml_models.neural import LSTMForecaster, GRUForecaster
from ml_models.service import ForecastingService, ModelFactory
from backend.models import FinancialInstrument, PriceData, Forecast, ModelPerformance


class TestPerformanceMetrics:
    """Test performance metrics calculations."""
    
    def test_calculate_metrics_basic(self):
        """Test basic metrics calculation."""
        y_true = np.array([100, 102, 101, 103, 105])
        y_pred = np.array([99, 101, 100, 102, 104])
        
        metrics = PerformanceMetrics.calculate_metrics(y_true, y_pred)
        
        assert 'rmse' in metrics
        assert 'mae' in metrics
        assert 'mape' in metrics
        assert 'mse' in metrics
        assert 'directional_accuracy' in metrics
        assert 'sharpe_ratio' in metrics
        
        # RMSE should be positive
        assert metrics['rmse'] > 0
        # MAE should be positive
        assert metrics['mae'] > 0
        # MAPE should be positive percentage
        assert metrics['mape'] > 0
    
    def test_calculate_metrics_with_nan(self):
        """Test metrics calculation with NaN values."""
        y_true = np.array([100, np.nan, 101, 103, 105])
        y_pred = np.array([99, 101, np.nan, 102, 104])
        
        metrics = PerformanceMetrics.calculate_metrics(y_true, y_pred)
        
        # Should handle NaN values gracefully
        assert not np.isnan(metrics['rmse'])
        assert not np.isnan(metrics['mae'])
    
    def test_calculate_metrics_empty_arrays(self):
        """Test metrics calculation with empty arrays."""
        y_true = np.array([])
        y_pred = np.array([])
        
        metrics = PerformanceMetrics.calculate_metrics(y_true, y_pred)
        
        # Should return NaN for all metrics
        assert np.isnan(metrics['rmse'])
        assert np.isnan(metrics['mae'])
        assert np.isnan(metrics['mape'])


class TestDataPreprocessor:
    """Test data preprocessing functionality."""
    
    def test_prepare_features_basic(self):
        """Test basic feature preparation."""
        # Create sample data
        dates = pd.date_range('2023-01-01', periods=10, freq='D')
        data = pd.DataFrame({
            'date': dates,
            'close_price': np.random.randn(10).cumsum() + 100,
            'volume': np.random.randint(1000, 10000, 10),
            'daily_return': np.random.randn(10) * 0.02,
            'volatility_5d': np.random.randn(10) * 0.01,
            'ma_5': np.random.randn(10) + 100,
            'ma_10': np.random.randn(10) + 100,
            'volume_zscore_5d': np.random.randn(10),
            'news_count': np.random.randint(0, 5, 10),
            'sent_compound_mean': np.random.randn(10) * 0.5
        })
        
        df, feature_columns = DataPreprocessor.prepare_features(data, 'close_price')
        
        assert len(feature_columns) > 0
        assert 'close_price_lag_1' in feature_columns
        assert len(df) > 0
        assert len(df.columns) > len(data.columns)  # Should have more columns due to lagged features
    
    def test_create_sequences(self):
        """Test sequence creation for neural networks."""
        data = pd.DataFrame({
            'feature1': np.random.randn(100),
            'feature2': np.random.randn(100),
            'close_price': np.random.randn(100).cumsum() + 100
        })
        
        feature_columns = ['feature1', 'feature2']
        sequence_length = 10
        
        X, y = DataPreprocessor.create_sequences(data, feature_columns, 'close_price', sequence_length)
        
        assert len(X) == len(y)
        assert X.shape[1] == sequence_length  # Sequence length
        assert X.shape[2] == len(feature_columns)  # Number of features
        assert len(X) == len(data) - sequence_length  # Should lose sequence_length samples


class TestMovingAverageForecaster:
    """Test Moving Average forecasting model."""
    
    def test_simple_moving_average_fit_predict(self):
        """Test simple moving average model."""
        # Create sample data
        data = pd.DataFrame({
            'close_price': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109]
        })
        
        model = MovingAverageForecaster(window=5, method='simple')
        model.fit(data, 'close_price')
        
        assert model.is_fitted
        assert model.last_values is not None
        assert len(model.last_values) == 5
        
        # Test prediction
        predictions = model.predict(3, 0.95)
        
        assert 'predictions' in predictions
        assert len(predictions['predictions']) == 3
        assert 'confidence_intervals' in predictions
    
    def test_exponential_moving_average_fit_predict(self):
        """Test exponential moving average model."""
        data = pd.DataFrame({
            'close_price': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109]
        })
        
        model = MovingAverageForecaster(window=5, method='exponential')
        model.fit(data, 'close_price')
        
        assert model.is_fitted
        assert model.last_values is not None
        
        predictions = model.predict(3, 0.95)
        
        assert 'predictions' in predictions
        assert len(predictions['predictions']) == 3
    
    def test_evaluate_performance(self):
        """Test model evaluation."""
        # Create training data
        train_data = pd.DataFrame({
            'close_price': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109]
        })
        
        # Create test data
        test_data = pd.DataFrame({
            'close_price': [110, 111, 112, 113, 114]
        })
        
        model = MovingAverageForecaster(window=5, method='simple')
        model.fit(train_data, 'close_price')
        
        metrics = model.evaluate(test_data, 'close_price')
        
        assert 'rmse' in metrics
        assert 'mae' in metrics
        assert 'mape' in metrics
        assert metrics['rmse'] > 0


class TestLinearRegressionForecaster:
    """Test Linear Regression forecasting model."""
    
    def test_fit_predict(self):
        """Test linear regression model fitting and prediction."""
        # Create sample data with features
        np.random.seed(42)
        n_samples = 50
        
        data = pd.DataFrame({
            'close_price': np.random.randn(n_samples).cumsum() + 100,
            'volume': np.random.randint(1000, 10000, n_samples),
            'daily_return': np.random.randn(n_samples) * 0.02,
            'volatility_5d': np.random.randn(n_samples) * 0.01
        })
        
        model = LinearRegressionForecaster()
        model.fit(data, 'close_price')
        
        assert model.is_fitted
        assert len(model.feature_columns) > 0
        
        predictions = model.predict(5, 0.95)
        
        assert 'predictions' in predictions
        assert len(predictions['predictions']) == 5
    
    def test_evaluate_performance(self):
        """Test linear regression evaluation."""
        np.random.seed(42)
        n_samples = 30
        
        data = pd.DataFrame({
            'close_price': np.random.randn(n_samples).cumsum() + 100,
            'volume': np.random.randint(1000, 10000, n_samples),
            'daily_return': np.random.randn(n_samples) * 0.02
        })
        
        model = LinearRegressionForecaster()
        model.fit(data, 'close_price')
        
        # Use last 10 samples as test data
        test_data = data.tail(10)
        
        metrics = model.evaluate(test_data, 'close_price')
        
        assert 'rmse' in metrics
        assert 'mae' in metrics
        assert 'mape' in metrics


class TestModelFactory:
    """Test model factory functionality."""
    
    def test_create_model(self):
        """Test model creation by name."""
        # Test creating different model types
        models_to_test = ['moving_average', 'linear_regression']
        
        for model_name in models_to_test:
            model = ModelFactory.create_model(model_name)
            assert isinstance(model, BaseForecaster)
            assert model.name == model_name
    
    def test_get_available_models(self):
        """Test getting available model names."""
        models = ModelFactory.get_available_models()
        
        assert isinstance(models, list)
        assert len(models) > 0
        assert 'moving_average' in models
        assert 'linear_regression' in models
    
    def test_invalid_model_name(self):
        """Test creating model with invalid name."""
        with pytest.raises(ValueError):
            ModelFactory.create_model('invalid_model')


class TestForecastingService:
    """Test forecasting service functionality."""
    
    def test_create_model(self):
        """Test model creation in service."""
        service = ForecastingService()
        
        model_id = service.create_model('moving_average', window=10)
        
        assert model_id in service.models
        assert service.models[model_id].name == 'moving_average'
    
    def test_train_model(self):
        """Test model training in service."""
        service = ForecastingService()
        
        # Create model
        model_id = service.create_model('moving_average', window=5)
        
        # Create training data
        data = pd.DataFrame({
            'close_price': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109]
        })
        
        # Train model
        result = service.train_model(model_id, data, 'close_price')
        
        assert result['is_fitted']
        assert result['model_id'] == model_id
    
    def test_predict(self):
        """Test prediction in service."""
        service = ForecastingService()
        
        # Create and train model
        model_id = service.create_model('moving_average', window=5)
        data = pd.DataFrame({
            'close_price': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109]
        })
        service.train_model(model_id, data, 'close_price')
        
        # Generate predictions
        predictions = service.predict(model_id, 3, 0.95)
        
        assert 'predictions' in predictions
        assert len(predictions['predictions']) == 3
        assert predictions['model_id'] == model_id
    
    def test_evaluate_model(self):
        """Test model evaluation in service."""
        service = ForecastingService()
        
        # Create and train model
        model_id = service.create_model('moving_average', window=5)
        train_data = pd.DataFrame({
            'close_price': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109]
        })
        service.train_model(model_id, train_data, 'close_price')
        
        # Create test data
        test_data = pd.DataFrame({
            'close_price': [110, 111, 112, 113, 114]
        })
        
        # Evaluate model
        evaluation = service.evaluate_model(model_id, test_data, 'close_price')
        
        assert 'metrics' in evaluation
        assert 'rmse' in evaluation['metrics']
        assert 'mae' in evaluation['metrics']


class TestModelEnsemble:
    """Test model ensemble functionality."""
    
    def test_create_ensemble(self):
        """Test creating an ensemble."""
        # Create individual models
        model1 = MovingAverageForecaster(window=5, method='simple')
        model2 = MovingAverageForecaster(window=10, method='simple')
        
        ensemble = ModelEnsemble([model1, model2], weights=[0.6, 0.4])
        
        assert len(ensemble.models) == 2
        assert len(ensemble.weights) == 2
        assert ensemble.weights[0] == 0.6
        assert ensemble.weights[1] == 0.4
    
    def test_ensemble_fit_predict(self):
        """Test ensemble fitting and prediction."""
        # Create models
        model1 = MovingAverageForecaster(window=5, method='simple')
        model2 = MovingAverageForecaster(window=10, method='simple')
        
        ensemble = ModelEnsemble([model1, model2])
        
        # Create training data
        data = pd.DataFrame({
            'close_price': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114]
        })
        
        # Fit ensemble
        ensemble.fit(data, 'close_price')
        
        assert ensemble.is_fitted
        
        # Generate predictions
        predictions = ensemble.predict(3, 0.95)
        
        assert 'predictions' in predictions
        assert len(predictions['predictions']) == 3
        assert 'model_predictions' in predictions


# Integration tests
class TestIntegration:
    """Integration tests for the complete system."""
    
    def test_end_to_end_forecasting_workflow(self):
        """Test complete forecasting workflow."""
        service = ForecastingService()
        
        # Create sample data
        np.random.seed(42)
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        data = pd.DataFrame({
            'date': dates,
            'close_price': np.random.randn(100).cumsum() + 100,
            'volume': np.random.randint(1000, 10000, 100),
            'daily_return': np.random.randn(100) * 0.02,
            'volatility_5d': np.random.randn(100) * 0.01,
            'ma_5': np.random.randn(100) + 100,
            'ma_10': np.random.randn(100) + 100,
            'volume_zscore_5d': np.random.randn(100),
            'news_count': np.random.randint(0, 5, 100),
            'sent_compound_mean': np.random.randn(100) * 0.5
        })
        
        # Create and train multiple models
        model_ids = []
        for model_name in ['moving_average', 'linear_regression']:
            model_id = service.create_model(model_name)
            service.train_model(model_id, data, 'close_price')
            model_ids.append(model_id)
        
        # Create ensemble
        ensemble_id = service.create_ensemble(model_ids)
        service.train_ensemble(ensemble_id, data, 'close_price')
        
        # Generate predictions
        individual_predictions = []
        for model_id in model_ids:
            pred = service.predict(model_id, 5, 0.95)
            individual_predictions.append(pred)
        
        ensemble_predictions = service.predict_ensemble(ensemble_id, 5, 0.95)
        
        # Verify predictions
        assert len(individual_predictions) == 2
        assert len(ensemble_predictions['predictions']) == 5
        assert 'individual_predictions' in ensemble_predictions
        
        # Evaluate models
        test_data = data.tail(20)
        evaluations = []
        for model_id in model_ids:
            eval_result = service.evaluate_model(model_id, test_data, 'close_price')
            evaluations.append(eval_result)
        
        ensemble_evaluation = service.evaluate_ensemble(ensemble_id, test_data, 'close_price')
        
        # Verify evaluations
        assert len(evaluations) == 2
        assert 'metrics' in ensemble_evaluation


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
