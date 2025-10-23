import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Mock MongoDB
@pytest.fixture
def mock_mongo():
    with patch('backend.app.mongo') as mock:
        yield mock

# Mock forecasting service
@pytest.fixture
def mock_forecasting_service():
    with patch('backend.app.forecasting_service') as mock:
        yield mock

@pytest.fixture
def client():
    from backend.app import app
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

class TestHealthEndpoint:
    def test_health_check(self, client):
        response = client.get('/api/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
        assert data['version'] == '1.0.0'
        assert data['database'] == 'mongodb'

class TestInstrumentsEndpoints:
    def test_get_instruments(self, client, mock_mongo):
        # Mock MongoDB response
        mock_instruments = [
            {
                'id': '507f1f77bcf86cd799439011',
                'symbol': 'AAPL',
                'name': 'Apple Inc.',
                'exchange': 'NASDAQ',
                'instrument_type': 'STOCK'
            }
        ]
        mock_mongo.db.instruments.find.return_value = mock_instruments
        
        response = client.get('/api/instruments')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data) == 1
        assert data[0]['symbol'] == 'AAPL'

    def test_create_instrument(self, client, mock_mongo):
        # Mock MongoDB insert
        mock_mongo.db.instruments.find_one.return_value = None
        mock_mongo.db.instruments.insert_one.return_value.inserted_id = '507f1f77bcf86cd799439011'
        
        instrument_data = {
            'symbol': 'TSLA',
            'name': 'Tesla Inc.',
            'exchange': 'NASDAQ',
            'instrument_type': 'STOCK'
        }
        
        response = client.post('/api/instruments', 
                             data=json.dumps(instrument_data),
                             content_type='application/json')
        assert response.status_code == 201
        
        data = json.loads(response.data)
        assert data['symbol'] == 'TSLA'
        assert data['id'] == '507f1f77bcf86cd799439011'

    def test_create_instrument_duplicate(self, client, mock_mongo):
        # Mock existing instrument
        mock_mongo.db.instruments.find_one.return_value = {'symbol': 'AAPL'}
        
        instrument_data = {
            'symbol': 'AAPL',
            'name': 'Apple Inc.',
            'exchange': 'NASDAQ',
            'instrument_type': 'STOCK'
        }
        
        response = client.post('/api/instruments',
                             data=json.dumps(instrument_data),
                             content_type='application/json')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'already exists' in data['error']

    def test_create_instrument_missing_fields(self, client):
        instrument_data = {
            'symbol': 'TSLA',
            'name': 'Tesla Inc.'
            # Missing exchange and instrument_type
        }
        
        response = client.post('/api/instruments',
                             data=json.dumps(instrument_data),
                             content_type='application/json')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'Missing required field' in data['error']

class TestPriceDataEndpoints:
    def test_get_price_data(self, client, mock_mongo):
        # Mock MongoDB response
        mock_price_data = [
            {
                '_id': '507f1f77bcf86cd799439011',
                'instrument_id': '507f1f77bcf86cd799439012',
                'date': '2023-01-01',
                'open_price': 100.0,
                'high_price': 105.0,
                'low_price': 95.0,
                'close_price': 102.0,
                'volume': 1000
            }
        ]
        mock_mongo.db.instruments.find_one.return_value = {'symbol': 'AAPL'}
        mock_mongo.db.price_data.find.return_value.sort.return_value.limit.return_value = mock_price_data
        
        response = client.get('/api/instruments/507f1f77bcf86cd799439012/price-data')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data) == 1
        assert data[0]['close_price'] == 102.0

    def test_get_price_data_instrument_not_found(self, client, mock_mongo):
        mock_mongo.db.instruments.find_one.return_value = None
        
        response = client.get('/api/instruments/507f1f77bcf86cd799439012/price-data')
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert 'Instrument not found' in data['error']

    @patch('backend.app.fetch_price_history')
    def test_refresh_price_data(self, mock_fetch, client, mock_mongo):
        # Mock instrument
        mock_mongo.db.instruments.find_one.return_value = {
            'symbol': 'AAPL',
            'exchange': 'NASDAQ'
        }
        
        # Mock price history
        mock_price_history = [
            {
                'date': '2023-01-01',
                'open': 100.0,
                'high': 105.0,
                'low': 95.0,
                'close': 102.0,
                'volume': 1000
            }
        ]
        mock_fetch.return_value = mock_price_history
        
        # Mock compute_minimal_indicators
        with patch('backend.app.compute_minimal_indicators') as mock_compute:
            mock_df = pd.DataFrame(mock_price_history)
            mock_compute.return_value = mock_df
            
            response = client.post('/api/instruments/507f1f77bcf86cd799439012/price-data')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert 'refreshed successfully' in data['message']

class TestModelsEndpoints:
    def test_get_models(self, client, mock_mongo):
        mock_models = [
            {
                'model_name': 'lstm',
                'status': 'trained',
                'created_at': datetime.utcnow()
            }
        ]
        mock_mongo.db.models.find.return_value = mock_models
        
        response = client.get('/api/models')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data) == 1
        assert data[0]['model_name'] == 'lstm'

    def test_create_model(self, client, mock_mongo):
        mock_mongo.db.models.insert_one.return_value.inserted_id = '507f1f77bcf86cd799439011'
        
        model_data = {
            'model_name': 'lstm',
            'model_params': {'epochs': 100}
        }
        
        response = client.post('/api/models',
                             data=json.dumps(model_data),
                             content_type='application/json')
        assert response.status_code == 201
        
        data = json.loads(response.data)
        assert data['model_id'] == '507f1f77bcf86cd799439011'

    def test_create_model_missing_name(self, client):
        model_data = {
            'model_params': {'epochs': 100}
        }
        
        response = client.post('/api/models',
                             data=json.dumps(model_data),
                             content_type='application/json')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'Missing required field: model_name' in data['error']

class TestTrainingEndpoints:
    @patch('backend.app.trained_models')
    def test_train_model(self, mock_trained_models, client, mock_mongo, mock_forecasting_service):
        # Mock model and instrument
        mock_mongo.db.models.find_one.return_value = {
            'model_name': 'lstm',
            'model_params': {}
        }
        mock_mongo.db.instruments.find_one.return_value = {
            'symbol': 'AAPL',
            'exchange': 'NASDAQ'
        }
        
        # Mock price data
        mock_price_data = [
            {
                'instrument_id': '507f1f77bcf86cd799439012',
                'date': '2023-01-01',
                'close_price': 100.0
            }
        ] * 150  # More than 100 records
        mock_mongo.db.price_data.find.return_value.sort.return_value = mock_price_data
        
        # Mock forecasting service
        mock_trained_model = MagicMock()
        mock_forecasting_service.train_model.return_value = mock_trained_model
        
        training_data = {
            'instrument_id': '507f1f77bcf86cd799439012'
        }
        
        response = client.post('/api/models/507f1f77bcf86cd799439011/train',
                             data=json.dumps(training_data),
                             content_type='application/json')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'trained successfully' in data['message']

    def test_train_model_not_found(self, client, mock_mongo):
        mock_mongo.db.models.find_one.return_value = None
        
        training_data = {
            'instrument_id': '507f1f77bcf86cd799439012'
        }
        
        response = client.post('/api/models/507f1f77bcf86cd799439011/train',
                             data=json.dumps(training_data),
                             content_type='application/json')
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert 'Model not found' in data['error']

class TestForecastingEndpoints:
    @patch('backend.app.trained_models')
    def test_generate_forecast(self, mock_trained_models, client, mock_mongo, mock_forecasting_service):
        # Mock model
        mock_mongo.db.models.find_one.return_value = {
            'model_name': 'lstm',
            'status': 'trained'
        }
        
        # Mock trained model
        mock_trained_model = MagicMock()
        mock_trained_models.__contains__.return_value = True
        mock_trained_models.__getitem__.return_value = mock_trained_model
        
        # Mock price data
        mock_price_data = [
            {
                'instrument_id': '507f1f77bcf86cd799439012',
                'date': '2023-01-01',
                'close_price': 100.0
            }
        ] * 100
        mock_mongo.db.price_data.find.return_value.sort.return_value.limit.return_value = mock_price_data
        
        # Mock forecasting service
        mock_forecast = {
            'predictions': np.array([110, 112, 115]),
            'confidence_intervals': {
                'lower': np.array([108, 110, 113]),
                'upper': np.array([112, 114, 117])
            }
        }
        mock_forecasting_service.generate_forecast.return_value = mock_forecast
        
        # Mock MongoDB insert
        mock_mongo.db.forecasts.insert_one.return_value.inserted_id = '507f1f77bcf86cd799439013'
        
        forecast_data = {
            'horizon': 24,
            'confidence_level': 0.95,
            'instrument_id': '507f1f77bcf86cd799439012'
        }
        
        response = client.post('/api/models/507f1f77bcf86cd799439011/predict',
                             data=json.dumps(forecast_data),
                             content_type='application/json')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'predictions' in data
        assert 'confidence_intervals' in data
        assert len(data['predictions']) == 3

class TestNewsEndpoints:
    def test_get_news_data(self, client, mock_mongo):
        mock_news_data = [
            {
                '_id': '507f1f77bcf86cd799439011',
                'instrument_id': '507f1f77bcf86cd799439012',
                'title': 'Apple Stock Rises',
                'content': 'Apple stock price increased...',
                'url': 'https://example.com/news1',
                'published_at': '2023-01-01',
                'sentiment_score': 0.8
            }
        ]
        mock_mongo.db.news_data.find.return_value.sort.return_value.limit.return_value = mock_news_data
        
        response = client.get('/api/instruments/507f1f77bcf86cd799439012/news')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert len(data) == 1
        assert data[0]['title'] == 'Apple Stock Rises'

    @patch('backend.app.fetch_news_items')
    def test_refresh_news_data(self, mock_fetch, client, mock_mongo):
        # Mock instrument
        mock_mongo.db.instruments.find_one.return_value = {
            'symbol': 'AAPL'
        }
        
        # Mock news items
        mock_news_items = [
            {
                'title': 'Apple Stock Rises',
                'content': 'Apple stock price increased...',
                'url': 'https://example.com/news1',
                'published_at': '2023-01-01',
                'sentiment_score': 0.8
            }
        ]
        mock_fetch.return_value = mock_news_items
        
        response = client.post('/api/instruments/507f1f77bcf86cd799439012/news')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'refreshed successfully' in data['message']

if __name__ == '__main__':
    pytest.main([__file__])
