from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_pymongo import PyMongo
from datetime import datetime, timedelta
import os
import sys
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import json

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.fintech_dataset.prices import fetch_price_history, compute_minimal_indicators
from src.fintech_dataset.news import fetch_news_items, score_sentiment, aggregate_daily_sentiment
from src.fintech_dataset.features import build_feature_frame
from ml_models.service import ForecastingService, ForecastScheduler
from ml_models.base import PerformanceMetrics

# Create Flask app
app = Flask(__name__)
app.config['MONGO_URI'] = os.getenv('MONGO_URI', 'mongodb://localhost:27017/fintech_forecasting')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Initialize extensions
CORS(app)
mongo = PyMongo(app)

# Initialize forecasting service
forecasting_service = ForecastingService()
scheduler = ForecastScheduler(forecasting_service)

# Track trained models
trained_models = {}

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'database': 'mongodb'
    })

# Financial Instruments Endpoints
@app.route('/api/instruments', methods=['GET'])
def get_instruments():
    """Get all financial instruments."""
    try:
        instruments = list(mongo.db.instruments.find({}, {'_id': 0}))
        return jsonify(instruments)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/instruments', methods=['POST'])
def create_instrument():
    """Create a new financial instrument."""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['symbol', 'name', 'exchange', 'instrument_type']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Check if instrument already exists
        existing = mongo.db.instruments.find_one({'symbol': data['symbol']})
        if existing:
            return jsonify({'error': 'Instrument with this symbol already exists'}), 400
        
        # Create new instrument
        instrument = {
            'symbol': data['symbol'],
            'name': data['name'],
            'exchange': data['exchange'],
            'instrument_type': data['instrument_type'],
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        result = mongo.db.instruments.insert_one(instrument)
        instrument['id'] = str(result.inserted_id)
        
        return jsonify(instrument), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/instruments/<instrument_id>', methods=['GET'])
def get_instrument(instrument_id):
    """Get a specific financial instrument."""
    try:
        from bson import ObjectId
        instrument = mongo.db.instruments.find_one({'_id': ObjectId(instrument_id)}, {'_id': 0})
        if not instrument:
            return jsonify({'error': 'Instrument not found'}), 404
        
        instrument['id'] = instrument_id
        return jsonify(instrument)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Price Data Endpoints
@app.route('/api/instruments/<instrument_id>/price-data', methods=['GET'])
def get_price_data(instrument_id):
    """Get price data for a specific instrument."""
    try:
        from bson import ObjectId
        limit = request.args.get('limit', 100, type=int)
        
        # Get instrument
        instrument = mongo.db.instruments.find_one({'_id': ObjectId(instrument_id)})
        if not instrument:
            return jsonify({'error': 'Instrument not found'}), 404
        
        # Get price data
        price_data = list(mongo.db.price_data.find(
            {'instrument_id': instrument_id}
        ).sort('date', -1).limit(limit))
        
        # Convert ObjectId to string
        for data in price_data:
            data['id'] = str(data['_id'])
            del data['_id']
        
        return jsonify(price_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/instruments/<instrument_id>/price-data', methods=['POST'])
def refresh_price_data(instrument_id):
    """Refresh price data for a specific instrument."""
    try:
        from bson import ObjectId
        
        # Get instrument
        instrument = mongo.db.instruments.find_one({'_id': ObjectId(instrument_id)})
        if not instrument:
            return jsonify({'error': 'Instrument not found'}), 404
        
        # Fetch new price data
        symbol = instrument['symbol']
        exchange = instrument['exchange']
        
        # Fetch price history
        price_history = fetch_price_history(symbol, exchange)
        
        if not price_history or len(price_history) == 0:
            return jsonify({'error': 'No price data available'}), 400
        
        # Convert to DataFrame and compute indicators
        df = pd.DataFrame(price_history)
        df = compute_minimal_indicators(df)
        
        # Store in database
        price_records = []
        for _, row in df.iterrows():
            price_record = {
                'instrument_id': instrument_id,
                'date': row['date'],
                'open_price': float(row['open']),
                'high_price': float(row['high']),
                'low_price': float(row['low']),
                'close_price': float(row['close']),
                'volume': int(row.get('volume', 0)),
                'created_at': datetime.utcnow()
            }
            price_records.append(price_record)
        
        # Insert or update price data
        for record in price_records:
            mongo.db.price_data.update_one(
                {
                    'instrument_id': record['instrument_id'],
                    'date': record['date']
                },
                {'$set': record},
                upsert=True
            )
        
        return jsonify({'message': 'Price data refreshed successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Models Endpoints
@app.route('/api/models', methods=['GET'])
def get_models():
    """Get all trained models."""
    try:
        models = list(mongo.db.models.find({}, {'_id': 0}))
        return jsonify(models)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/models', methods=['POST'])
def create_model():
    """Create a new forecasting model."""
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'model_name' not in data:
            return jsonify({'error': 'Missing required field: model_name'}), 400
        
        # Create new model
        model = {
            'model_name': data['model_name'],
            'model_params': data.get('model_params', {}),
            'status': 'created',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        result = mongo.db.models.insert_one(model)
        model_id = str(result.inserted_id)
        
        return jsonify({'model_id': model_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/models/<model_id>/train', methods=['POST'])
def train_model(model_id):
    """Train a forecasting model."""
    try:
        from bson import ObjectId
        data = request.get_json()
        
        # Get model
        model = mongo.db.models.find_one({'_id': ObjectId(model_id)})
        if not model:
            return jsonify({'error': 'Model not found'}), 404
        
        # Get instrument
        instrument_id = data.get('instrument_id')
        if not instrument_id:
            return jsonify({'error': 'Missing instrument_id'}), 400
        
        instrument = mongo.db.instruments.find_one({'_id': ObjectId(instrument_id)})
        if not instrument:
            return jsonify({'error': 'Instrument not found'}), 404
        
        # Update model status
        mongo.db.models.update_one(
            {'_id': ObjectId(model_id)},
            {
                '$set': {
                    'status': 'training',
                    'instrument_id': instrument_id,
                    'updated_at': datetime.utcnow()
                }
            }
        )
        
        # Train model using forecasting service
        model_name = model['model_name']
        model_params = model.get('model_params', {})
        
        # Get price data for training
        price_data = list(mongo.db.price_data.find(
            {'instrument_id': instrument_id}
        ).sort('date', 1))
        
        if len(price_data) < 100:
            return jsonify({'error': 'Insufficient data for training'}), 400
        
        # Convert to DataFrame
        df = pd.DataFrame(price_data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
        
        # Train model
        trained_model = forecasting_service.train_model(
            model_name, df, model_params
        )
        
        # Store trained model
        trained_models[model_id] = trained_model
        
        # Update model status
        mongo.db.models.update_one(
            {'_id': ObjectId(model_id)},
            {
                '$set': {
                    'status': 'trained',
                    'trained_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                }
            }
        )
        
        return jsonify({'message': 'Model trained successfully'})
    except Exception as e:
        # Update model status to failed
        mongo.db.models.update_one(
            {'_id': ObjectId(model_id)},
            {
                '$set': {
                    'status': 'failed',
                    'error': str(e),
                    'updated_at': datetime.utcnow()
                }
            }
        )
        return jsonify({'error': str(e)}), 500

@app.route('/api/models/<model_id>/evaluate', methods=['POST'])
def evaluate_model(model_id):
    """Evaluate a trained model."""
    try:
        from bson import ObjectId
        data = request.get_json()
        
        # Get model
        model = mongo.db.models.find_one({'_id': ObjectId(model_id)})
        if not model:
            return jsonify({'error': 'Model not found'}), 404
        
        if model['status'] != 'trained':
            return jsonify({'error': 'Model not trained'}), 400
        
        # Get instrument
        instrument_id = data.get('instrument_id')
        if not instrument_id:
            return jsonify({'error': 'Missing instrument_id'}), 400
        
        # Get trained model
        if model_id not in trained_models:
            return jsonify({'error': 'Trained model not found in memory'}), 400
        
        trained_model = trained_models[model_id]
        
        # Get test data
        test_period_days = data.get('test_period_days', 7)
        cutoff_date = datetime.utcnow() - timedelta(days=test_period_days)
        
        test_data = list(mongo.db.price_data.find({
            'instrument_id': instrument_id,
            'date': {'$gte': cutoff_date}
        }).sort('date', 1))
        
        if len(test_data) < 10:
            return jsonify({'error': 'Insufficient test data'}), 400
        
        # Convert to DataFrame
        df = pd.DataFrame(test_data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
        
        # Evaluate model
        metrics = forecasting_service.evaluate_model(trained_model, df)
        
        # Store evaluation results
        evaluation = {
            'model_id': model_id,
            'instrument_id': instrument_id,
            'test_period_days': test_period_days,
            'metrics': metrics.to_dict(),
            'evaluated_at': datetime.utcnow()
        }
        
        mongo.db.evaluations.insert_one(evaluation)
        
        return jsonify({'metrics': metrics.to_dict()})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/models/<model_id>/predict', methods=['POST'])
def generate_forecast(model_id):
    """Generate forecast using a trained model."""
    try:
        from bson import ObjectId
        data = request.get_json()
        
        # Get model
        model = mongo.db.models.find_one({'_id': ObjectId(model_id)})
        if not model:
            return jsonify({'error': 'Model not found'}), 404
        
        if model['status'] != 'trained':
            return jsonify({'error': 'Model not trained'}), 400
        
        # Get parameters
        horizon = data.get('horizon', 24)
        confidence_level = data.get('confidence_level', 0.95)
        instrument_id = data.get('instrument_id')
        
        if not instrument_id:
            return jsonify({'error': 'Missing instrument_id'}), 400
        
        # Get trained model
        if model_id not in trained_models:
            return jsonify({'error': 'Trained model not found in memory'}), 400
        
        trained_model = trained_models[model_id]
        
        # Get recent data for forecasting
        recent_data = list(mongo.db.price_data.find(
            {'instrument_id': instrument_id}
        ).sort('date', -1).limit(100))
        
        if len(recent_data) < 50:
            return jsonify({'error': 'Insufficient data for forecasting'}), 400
        
        # Convert to DataFrame
        df = pd.DataFrame(recent_data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date').sort_index()
        
        # Generate forecast
        forecast = forecasting_service.generate_forecast(
            trained_model, df, horizon, confidence_level
        )
        
        # Store forecast
        forecast_record = {
            'model_id': model_id,
            'instrument_id': instrument_id,
            'horizon': horizon,
            'confidence_level': confidence_level,
            'predictions': forecast['predictions'].tolist(),
            'confidence_intervals': {
                'lower': forecast['confidence_intervals']['lower'].tolist(),
                'upper': forecast['confidence_intervals']['upper'].tolist()
            },
            'created_at': datetime.utcnow()
        }
        
        result = mongo.db.forecasts.insert_one(forecast_record)
        forecast_record['forecast_id'] = str(result.inserted_id)
        
        return jsonify(forecast_record)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Forecasts Endpoints
@app.route('/api/instruments/<instrument_id>/forecasts', methods=['GET'])
def get_forecasts(instrument_id):
    """Get forecasts for a specific instrument."""
    try:
        from bson import ObjectId
        limit = request.args.get('limit', 100, type=int)
        
        forecasts = list(mongo.db.forecasts.find(
            {'instrument_id': instrument_id}
        ).sort('created_at', -1).limit(limit))
        
        # Convert ObjectId to string
        for forecast in forecasts:
            forecast['id'] = str(forecast['_id'])
            del forecast['_id']
        
        return jsonify(forecasts)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# News Data Endpoints
@app.route('/api/instruments/<instrument_id>/news', methods=['GET'])
def get_news_data(instrument_id):
    """Get news data for a specific instrument."""
    try:
        from bson import ObjectId
        limit = request.args.get('limit', 100, type=int)
        
        news_data = list(mongo.db.news_data.find(
            {'instrument_id': instrument_id}
        ).sort('published_at', -1).limit(limit))
        
        # Convert ObjectId to string
        for news in news_data:
            news['id'] = str(news['_id'])
            del news['_id']
        
        return jsonify(news_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/instruments/<instrument_id>/news', methods=['POST'])
def refresh_news_data(instrument_id):
    """Refresh news data for a specific instrument."""
    try:
        from bson import ObjectId
        
        # Get instrument
        instrument = mongo.db.instruments.find_one({'_id': ObjectId(instrument_id)})
        if not instrument:
            return jsonify({'error': 'Instrument not found'}), 404
        
        # Fetch news data
        symbol = instrument['symbol']
        news_items = fetch_news_items(symbol)
        
        if not news_items:
            return jsonify({'error': 'No news data available'}), 400
        
        # Process and store news data
        for item in news_items:
            news_record = {
                'instrument_id': instrument_id,
                'title': item['title'],
                'content': item['content'],
                'url': item['url'],
                'published_at': item['published_at'],
                'sentiment_score': item.get('sentiment_score', 0),
                'created_at': datetime.utcnow()
            }
            
            mongo.db.news_data.update_one(
                {
                    'instrument_id': instrument_id,
                    'url': item['url']
                },
                {'$set': news_record},
                upsert=True
            )
        
        return jsonify({'message': 'News data refreshed successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Initialize sample data
def init_sample_data():
    """Initialize sample financial instruments."""
    try:
        # Check if instruments already exist
        if mongo.db.instruments.count_documents({}) > 0:
            print("Sample data already exists!")
            return
        
        # Sample instruments
        instruments = [
            {
                'symbol': 'AAPL',
                'name': 'Apple Inc.',
                'exchange': 'NASDAQ',
                'instrument_type': 'STOCK',
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            },
            {
                'symbol': 'MSFT',
                'name': 'Microsoft Corporation',
                'exchange': 'NASDAQ',
                'instrument_type': 'STOCK',
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            },
            {
                'symbol': 'BTC-USD',
                'name': 'Bitcoin',
                'exchange': 'CRYPTO',
                'instrument_type': 'CRYPTO',
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            },
            {
                'symbol': 'ETH-USD',
                'name': 'Ethereum',
                'exchange': 'CRYPTO',
                'instrument_type': 'CRYPTO',
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            },
            {
                'symbol': 'EURUSD=X',
                'name': 'EUR/USD',
                'exchange': 'FOREX',
                'instrument_type': 'FOREX',
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
        ]
        
        mongo.db.instruments.insert_many(instruments)
        print("✅ Sample instruments added successfully!")
    except Exception as e:
        print(f"Error initializing sample data: {e}")

if __name__ == '__main__':
    # Initialize sample data
    init_sample_data()
    
    print("🚀 Starting FinTech Forecasting Application...")
    print("📊 Dashboard: http://localhost:3000")
    print("🔌 API: http://localhost:8000/api")
    app.run(debug=True, host='0.0.0.0', port=8000)
