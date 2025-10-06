"""
Unit tests for the financial forecasting application
"""

import unittest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml_models.traditional_models import TraditionalForecaster
from ml_models.neural_models import NeuralForecaster
from ml_models.ensemble_models import EnsembleForecaster
from ml_models.ml_orchestrator import MLOrchestrator


class TestTraditionalModels(unittest.TestCase):
    """Test cases for traditional forecasting models"""
    
    def setUp(self):
        """Set up test data"""
        self.forecaster = TraditionalForecaster()
        
        # Create sample data
        dates = pd.date_range(start='2023-01-01', periods=100, freq='H')
        np.random.seed(42)
        prices = 100 + np.cumsum(np.random.randn(100) * 0.1)
        
        self.test_df = pd.DataFrame({
            'Date': dates,
            'Open': prices + np.random.randn(100) * 0.5,
            'High': prices + np.abs(np.random.randn(100) * 0.5),
            'Low': prices - np.abs(np.random.randn(100) * 0.5),
            'Close': prices,
            'Volume': np.random.randint(1000, 10000, 100)
        })
    
    def test_prepare_data(self):
        """Test data preparation"""
        data, dates = self.forecaster.prepare_data(self.test_df)
        
        self.assertIsInstance(data, np.ndarray)
        self.assertIsInstance(dates, pd.DatetimeIndex)
        self.assertEqual(len(data), len(dates))
        self.assertEqual(len(data), 100)
    
    def test_arima_forecast(self):
        """Test ARIMA forecasting"""
        data, _ = self.forecaster.prepare_data(self.test_df)
        result = self.forecaster.arima_forecast(data, forecast_hours=5)
        
        self.assertIn('forecast', result)
        self.assertEqual(len(result['forecast']), 5)
        self.assertIsInstance(result['forecast'], np.ndarray)
    
    def test_moving_average_forecast(self):
        """Test Moving Average forecasting"""
        data, _ = self.forecaster.prepare_data(self.test_df)
        result = self.forecaster.moving_average_forecast(data, forecast_hours=5)
        
        self.assertIn('forecast', result)
        self.assertEqual(len(result['forecast']), 5)
        self.assertIsInstance(result['forecast'], np.ndarray)
    
    def test_exponential_smoothing_forecast(self):
        """Test Exponential Smoothing forecasting"""
        data, _ = self.forecaster.prepare_data(self.test_df)
        result = self.forecaster.exponential_smoothing_forecast(data, forecast_hours=5)
        
        self.assertIn('forecast', result)
        self.assertEqual(len(result['forecast']), 5)
        self.assertIsInstance(result['forecast'], np.ndarray)
    
    def test_calculate_metrics(self):
        """Test metrics calculation"""
        actual = np.array([1, 2, 3, 4, 5])
        predicted = np.array([1.1, 2.1, 2.9, 4.1, 4.9])
        
        metrics = self.forecaster.calculate_metrics(actual, predicted)
        
        self.assertIn('rmse', metrics)
        self.assertIn('mae', metrics)
        self.assertIn('mape', metrics)
        self.assertIsInstance(metrics['rmse'], float)
        self.assertIsInstance(metrics['mae'], float)
        self.assertIsInstance(metrics['mape'], float)


class TestNeuralModels(unittest.TestCase):
    """Test cases for neural network forecasting models"""
    
    def setUp(self):
        """Set up test data"""
        self.forecaster = NeuralForecaster(sequence_length=10)
        
        # Create sample data
        np.random.seed(42)
        self.test_data = 100 + np.cumsum(np.random.randn(100) * 0.1)
    
    def test_prepare_sequences(self):
        """Test sequence preparation"""
        X, y, scaler = self.forecaster.prepare_sequences(self.test_data)
        
        self.assertIsInstance(X, np.ndarray)
        self.assertIsInstance(y, np.ndarray)
        self.assertEqual(X.shape[0], y.shape[0])
        self.assertEqual(X.shape[1], self.forecaster.sequence_length)
    
    def test_lstm_model_creation(self):
        """Test LSTM model creation"""
        model = self.forecaster.lstm_model((10, 1))
        
        self.assertIsNotNone(model)
        self.assertEqual(len(model.layers), 5)  # LSTM, Dropout, LSTM, Dropout, Dense
    
    def test_gru_model_creation(self):
        """Test GRU model creation"""
        model = self.forecaster.gru_model((10, 1))
        
        self.assertIsNotNone(model)
        self.assertEqual(len(model.layers), 5)  # GRU, Dropout, GRU, Dropout, Dense
    
    def test_transformer_model_creation(self):
        """Test Transformer model creation"""
        model = self.forecaster.transformer_model((10, 1))
        
        self.assertIsNotNone(model)
        self.assertGreater(len(model.layers), 5)  # Multiple layers in transformer
    
    def test_calculate_metrics(self):
        """Test metrics calculation"""
        actual = np.array([1, 2, 3, 4, 5])
        predicted = np.array([1.1, 2.1, 2.9, 4.1, 4.9])
        
        metrics = self.forecaster.calculate_metrics(actual, predicted)
        
        self.assertIn('rmse', metrics)
        self.assertIn('mae', metrics)
        self.assertIn('mape', metrics)


class TestEnsembleModels(unittest.TestCase):
    """Test cases for ensemble forecasting models"""
    
    def setUp(self):
        """Set up test data"""
        self.forecaster = EnsembleForecaster(sequence_length=10)
        
        # Create sample data
        dates = pd.date_range(start='2023-01-01', periods=100, freq='H')
        np.random.seed(42)
        prices = 100 + np.cumsum(np.random.randn(100) * 0.1)
        
        self.test_df = pd.DataFrame({
            'Date': dates,
            'Close': prices,
            'Volume': np.random.randint(1000, 10000, 100)
        })
    
    def test_weighted_average_ensemble(self):
        """Test weighted average ensemble"""
        forecasts = {
            'model1': {'forecast': np.array([1, 2, 3])},
            'model2': {'forecast': np.array([2, 3, 4])},
            'model3': {'forecast': np.array([3, 4, 5])}
        }
        
        weights = {'model1': 0.5, 'model2': 0.3, 'model3': 0.2}
        
        result = self.forecaster.weighted_average_ensemble(forecasts, weights)
        
        self.assertIsInstance(result, np.ndarray)
        self.assertEqual(len(result), 3)
        # Check that result is weighted average
        expected = 0.5 * np.array([1, 2, 3]) + 0.3 * np.array([2, 3, 4]) + 0.2 * np.array([3, 4, 5])
        np.testing.assert_array_almost_equal(result, expected)
    
    def test_calculate_metrics(self):
        """Test metrics calculation"""
        actual = np.array([1, 2, 3, 4, 5])
        predicted = np.array([1.1, 2.1, 2.9, 4.1, 4.9])
        
        metrics = self.forecaster.calculate_metrics(actual, predicted)
        
        self.assertIn('rmse', metrics)
        self.assertIn('mae', metrics)
        self.assertIn('mape', metrics)


class TestMLOrchestrator(unittest.TestCase):
    """Test cases for ML orchestrator"""
    
    def setUp(self):
        """Set up test data"""
        self.orchestrator = MLOrchestrator(sequence_length=10)
        
        # Create sample data
        dates = pd.date_range(start='2023-01-01', periods=100, freq='H')
        np.random.seed(42)
        prices = 100 + np.cumsum(np.random.randn(100) * 0.1)
        
        self.test_df = pd.DataFrame({
            'Date': dates,
            'Open': prices + np.random.randn(100) * 0.5,
            'High': prices + np.abs(np.random.randn(100) * 0.5),
            'Low': prices - np.abs(np.random.randn(100) * 0.5),
            'Close': prices,
            'Volume': np.random.randint(1000, 10000, 100)
        })
    
    def test_prepare_data(self):
        """Test data preparation"""
        result = self.orchestrator.prepare_data(self.test_df)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertIn('Date', result.columns)
        self.assertIn('Close', result.columns)
        self.assertEqual(len(result), 100)
    
    def test_generate_forecast_dates(self):
        """Test forecast date generation"""
        last_date = datetime(2023, 1, 1, 12, 0, 0)
        forecast_hours = 5
        
        dates = self.orchestrator.generate_forecast_dates(last_date, forecast_hours)
        
        self.assertEqual(len(dates), forecast_hours)
        self.assertIsInstance(dates[0], datetime)
    
    def test_make_json_serializable(self):
        """Test JSON serialization"""
        test_data = {
            'array': np.array([1, 2, 3]),
            'float': np.float64(3.14),
            'int': np.int64(42),
            'date': datetime.now(),
            'nested': {
                'array': np.array([4, 5, 6])
            }
        }
        
        result = self.orchestrator._make_json_serializable(test_data)
        
        self.assertIsInstance(result['array'], list)
        self.assertIsInstance(result['float'], float)
        self.assertIsInstance(result['int'], int)
        self.assertIsInstance(result['date'], str)
        self.assertIsInstance(result['nested']['array'], list)


class TestIntegration(unittest.TestCase):
    """Integration tests"""
    
    def setUp(self):
        """Set up test data"""
        self.orchestrator = MLOrchestrator(sequence_length=10)
        
        # Create sample data
        dates = pd.date_range(start='2023-01-01', periods=200, freq='H')
        np.random.seed(42)
        prices = 100 + np.cumsum(np.random.randn(200) * 0.1)
        
        self.test_df = pd.DataFrame({
            'Date': dates,
            'Open': prices + np.random.randn(200) * 0.5,
            'High': prices + np.abs(np.random.randn(200) * 0.5),
            'Low': prices - np.abs(np.random.randn(200) * 0.5),
            'Close': prices,
            'Volume': np.random.randint(1000, 10000, 200)
        })
    
    def test_end_to_end_forecast(self):
        """Test end-to-end forecasting pipeline"""
        forecast_hours = 5
        
        results = self.orchestrator.run_all_models(self.test_df, forecast_hours)
        
        # Check metadata
        self.assertIn('metadata', results)
        self.assertIn('forecasts', results)
        self.assertIn('performance_metrics', results)
        
        # Check forecast structure
        self.assertIn('traditional', results['forecasts'])
        self.assertIn('neural', results['forecasts'])
        self.assertIn('ensemble', results['forecasts'])
        
        # Check that we have forecasts
        traditional_forecasts = results['forecasts']['traditional']
        self.assertGreater(len(traditional_forecasts), 0)
    
    def test_best_model_selection(self):
        """Test best model selection"""
        results = self.orchestrator.run_all_models(self.test_df, 5)
        best_model = self.orchestrator.get_best_model(results)
        
        self.assertIsNotNone(best_model)
        self.assertIn('model', best_model)
        self.assertIn('category', best_model)
        self.assertIn('model_name', best_model)


if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestTraditionalModels))
    test_suite.addTest(unittest.makeSuite(TestNeuralModels))
    test_suite.addTest(unittest.makeSuite(TestEnsembleModels))
    test_suite.addTest(unittest.makeSuite(TestMLOrchestrator))
    test_suite.addTest(unittest.makeSuite(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\nTests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
