"""
Simple Flask application for the FinTech forecasting application.
"""

import os
import sys
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc, and_

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fintech_forecasting.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'

# Initialize extensions
CORS(app)
db = SQLAlchemy(app)

# Track trained models
trained_models = {}

# Database Models
class FinancialInstrument(db.Model):
    """Represents a financial instrument (stock, crypto, forex)."""
    __tablename__ = 'financial_instruments'
    
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(20), nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False)
    exchange = db.Column(db.String(20), nullable=False)
    instrument_type = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<FinancialInstrument {self.symbol}>'


class PriceData(db.Model):
    """Historical price data for financial instruments."""
    __tablename__ = 'price_data'
    
    id = db.Column(db.Integer, primary_key=True)
    instrument_id = db.Column(db.Integer, db.ForeignKey('financial_instruments.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    
    # OHLCV data
    open_price = db.Column(db.Float, nullable=False)
    high_price = db.Column(db.Float, nullable=False)
    low_price = db.Column(db.Float, nullable=False)
    close_price = db.Column(db.Float, nullable=False)
    adj_close_price = db.Column(db.Float, nullable=False)
    volume = db.Column(db.BigInteger, nullable=False)
    
    # Technical indicators
    daily_return = db.Column(db.Float)
    volatility_5d = db.Column(db.Float)
    ma_5 = db.Column(db.Float)
    ma_10 = db.Column(db.Float)
    volume_zscore_5d = db.Column(db.Float)
    
    # News sentiment
    news_count = db.Column(db.Integer, default=0)
    sent_compound_mean = db.Column(db.Float, default=0.0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<PriceData {self.instrument_id} {self.date}>'


class Forecast(db.Model):
    """Forecast predictions for financial instruments."""
    __tablename__ = 'forecasts'
    
    id = db.Column(db.Integer, primary_key=True)
    instrument_id = db.Column(db.Integer, db.ForeignKey('financial_instruments.id'), nullable=False)
    model_name = db.Column(db.String(50), nullable=False)
    forecast_date = db.Column(db.Date, nullable=False)
    target_date = db.Column(db.Date, nullable=False)
    
    # Forecast values
    predicted_close = db.Column(db.Float)
    confidence_lower = db.Column(db.Float)
    confidence_upper = db.Column(db.Float)
    confidence_level = db.Column(db.Float, default=0.95)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Forecast {self.instrument_id} {self.model_name} {self.target_date}>'


# API Routes
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })


@app.route('/api/instruments', methods=['GET'])
def get_instruments():
    """Get all financial instruments."""
    instruments = FinancialInstrument.query.all()
    return jsonify([{
        'id': inst.id,
        'symbol': inst.symbol,
        'name': inst.name,
        'exchange': inst.exchange,
        'instrument_type': inst.instrument_type,
        'created_at': inst.created_at.isoformat()
    } for inst in instruments])


@app.route('/api/instruments/<int:instrument_id>/price-data', methods=['GET'])
def get_price_data(instrument_id):
    """Get price data for a specific instrument."""
    instrument = FinancialInstrument.query.get_or_404(instrument_id)
    
    # Get query parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    limit = request.args.get('limit', type=int)
    
    query = PriceData.query.filter_by(instrument_id=instrument_id)
    
    if start_date:
        query = query.filter(PriceData.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
    if end_date:
        query = query.filter(PriceData.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
    
    query = query.order_by(desc(PriceData.date))
    
    if limit:
        query = query.limit(limit)
    
    price_data = query.all()
    
    return jsonify([{
        'date': price_point.date.strftime('%Y-%m-%d'),
        'open_price': price_point.open_price,
        'high_price': price_point.high_price,
        'low_price': price_point.low_price,
        'close_price': price_point.close_price,
        'adj_close_price': price_point.adj_close_price,
        'volume': price_point.volume,
        'daily_return': price_point.daily_return,
        'volatility_5d': price_point.volatility_5d,
        'ma_5': price_point.ma_5,
        'ma_10': price_point.ma_10,
        'volume_zscore_5d': price_point.volume_zscore_5d,
        'news_count': price_point.news_count,
        'sent_compound_mean': price_point.sent_compound_mean
    } for price_point in price_data])


@app.route('/api/instruments/<int:instrument_id>/price-data', methods=['POST'])
def update_price_data(instrument_id):
    """Update price data for a specific instrument."""
    instrument = FinancialInstrument.query.get_or_404(instrument_id)
    
    try:
        # Create sample data for demonstration
        import random
        from datetime import datetime, timedelta
        
        # Clear existing data
        PriceData.query.filter_by(instrument_id=instrument_id).delete()
        
        # Generate sample data for the last 30 days
        base_price = 150.0 if instrument.symbol == 'AAPL' else 300.0 if instrument.symbol == 'MSFT' else 50000.0
        current_date = datetime.now().date()
        
        for i in range(30):
            date = current_date - timedelta(days=i)
            price_change = random.uniform(-0.05, 0.05)  # ±5% daily change
            base_price *= (1 + price_change)
            
            open_price = base_price * random.uniform(0.98, 1.02)
            high_price = max(open_price, base_price) * random.uniform(1.0, 1.03)
            low_price = min(open_price, base_price) * random.uniform(0.97, 1.0)
            close_price = base_price
            volume = random.randint(1000000, 10000000)
            
            price_data = PriceData(
                instrument_id=instrument_id,
                date=date,
                open_price=round(open_price, 2),
                high_price=round(high_price, 2),
                low_price=round(low_price, 2),
                close_price=round(close_price, 2),
                adj_close_price=round(close_price, 2),
                volume=volume,
                daily_return=round(price_change, 4),
                volatility_5d=round(random.uniform(0.01, 0.05), 4),
                ma_5=round(base_price * random.uniform(0.95, 1.05), 2),
                ma_10=round(base_price * random.uniform(0.90, 1.10), 2),
                volume_zscore_5d=round(random.uniform(-2, 2), 2),
                news_count=random.randint(0, 5),
                sent_compound_mean=round(random.uniform(-0.5, 0.5), 3)
            )
            db.session.add(price_data)
        
        db.session.commit()
        
        return jsonify({
            'message': f'Updated price data for {instrument.symbol}',
            'records_updated': 30
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/models', methods=['GET'])
def get_available_models():
    """Get available forecasting models."""
    return jsonify({
        'models': ['moving_average', 'arima', 'lstm', 'gru', 'linear_regression'],
        'registered_models': [
            {
                'model_id': model_id,
                'model_name': model_info['model_name'],
                'is_fitted': model_info['is_fitted'],
                'instrument_id': model_info['instrument_id']
            }
            for model_id, model_info in trained_models.items()
        ],
        'ensembles': []
    })


@app.route('/api/models', methods=['POST'])
def create_model():
    """Create a new forecasting model."""
    data = request.get_json()
    
    model_name = data.get('model_name')
    model_params = data.get('model_params', {})
    model_id = f"{model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    if not model_name:
        return jsonify({'error': 'model_name is required'}), 400
    
    return jsonify({
        'model_id': model_id,
        'model_name': model_name,
        'model_params': model_params
    }), 201


@app.route('/api/models/<model_id>/train', methods=['POST'])
def train_model(model_id):
    """Train a forecasting model."""
    data = request.get_json()
    
    instrument_id = data.get('instrument_id')
    target_column = data.get('target_column', 'close_price')
    
    if not instrument_id:
        return jsonify({'error': 'instrument_id is required'}), 400
    
    try:
        # Get price data
        price_data = PriceData.query.filter_by(instrument_id=instrument_id).order_by(PriceData.date).all()
        
        if len(price_data) < 30:
            return jsonify({'error': 'Insufficient data for training'}), 400
        
        # Simulate training
        import time
        time.sleep(2)  # Simulate training time
        
        # Track the trained model
        trained_models[model_id] = {
            'model_name': model_id.split('_')[0],
            'is_fitted': True,
            'instrument_id': instrument_id,
            'trained_at': datetime.now().isoformat()
        }
        
        return jsonify({
            'model_id': model_id,
            'model_name': model_id.split('_')[0],
            'is_fitted': True,
            'feature_columns': ['close_price', 'volume', 'daily_return']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/models/<model_id>/predict', methods=['POST'])
def predict(model_id):
    """Generate predictions using a trained model."""
    data = request.get_json()
    
    horizon = data.get('horizon', 24)
    confidence_level = data.get('confidence_level', 0.95)
    
    try:
        # Get latest price data
        latest_price = PriceData.query.order_by(desc(PriceData.date)).first()
        if not latest_price:
            return jsonify({'error': 'No price data available'}), 400
        
        # Generate simple predictions (random walk with trend)
        import random
        base_price = latest_price.close_price
        predictions = []
        
        for i in range(horizon):
            # Simple random walk with slight upward bias
            change = random.uniform(-0.02, 0.03)  # -2% to +3% change
            base_price *= (1 + change)
            predictions.append(round(base_price, 2))
        
        # Generate confidence intervals
        std_dev = base_price * 0.05  # 5% standard deviation
        z_score = 1.96 if confidence_level == 0.95 else 2.576
        
        confidence_intervals = {
            'lower': [max(0, p - z_score * std_dev) for p in predictions],
            'upper': [p + z_score * std_dev for p in predictions]
        }
        
        return jsonify({
            'model_id': model_id,
            'model_name': model_id.split('_')[0],
            'horizon': horizon,
            'confidence_level': confidence_level,
            'predictions': predictions,
            'confidence_intervals': confidence_intervals
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/models/<model_id>/evaluate', methods=['POST'])
def evaluate_model(model_id):
    """Evaluate model performance."""
    data = request.get_json()
    
    instrument_id = data.get('instrument_id')
    test_period_days = data.get('test_period_days', 7)
    
    if not instrument_id:
        return jsonify({'error': 'instrument_id is required'}), 400
    
    try:
        # Simulate evaluation metrics
        import random
        
        metrics = {
            'rmse': round(random.uniform(0.5, 2.0), 4),
            'mae': round(random.uniform(0.3, 1.5), 4),
            'mape': round(random.uniform(1.0, 5.0), 2),
            'mse': round(random.uniform(0.25, 4.0), 4),
            'directional_accuracy': round(random.uniform(55, 75), 1),
            'sharpe_ratio': round(random.uniform(0.5, 2.0), 2)
        }
        
        return jsonify({
            'model_id': model_id,
            'model_name': model_id.split('_')[0],
            'metrics': metrics,
            'evaluation_date': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Serve static files (for frontend)
@app.route('/')
def serve_frontend():
    """Serve the frontend application."""
    return send_from_directory('frontend', 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    """Serve static files."""
    return send_from_directory('frontend', path)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Add sample instruments if they don't exist
        if FinancialInstrument.query.count() == 0:
            instruments = [
                FinancialInstrument(
                    symbol='AAPL',
                    name='Apple Inc.',
                    exchange='NASDAQ',
                    instrument_type='STOCK'
                ),
                FinancialInstrument(
                    symbol='MSFT',
                    name='Microsoft Corporation',
                    exchange='NASDAQ',
                    instrument_type='STOCK'
                ),
                FinancialInstrument(
                    symbol='BTC-USD',
                    name='Bitcoin',
                    exchange='CRYPTO',
                    instrument_type='CRYPTO'
                ),
                FinancialInstrument(
                    symbol='ETH-USD',
                    name='Ethereum',
                    exchange='CRYPTO',
                    instrument_type='CRYPTO'
                ),
                FinancialInstrument(
                    symbol='EURUSD=X',
                    name='EUR/USD',
                    exchange='FOREX',
                    instrument_type='FOREX'
                )
            ]
            
            for instrument in instruments:
                db.session.add(instrument)
            
            db.session.commit()
            print("✅ Sample instruments added successfully!")
    
    print("🚀 Starting FinTech Forecasting Application...")
    print("📊 Dashboard: http://localhost:8000")
    print("🔌 API: http://localhost:8000/api")
    app.run(debug=True, host='127.0.0.1', port=8000)
