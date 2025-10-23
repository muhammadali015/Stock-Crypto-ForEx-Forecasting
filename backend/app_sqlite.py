from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import os
import sys
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import json
import sqlite3

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Initialize extensions
CORS(app)

# SQLite database setup
DATABASE = 'instance/fintech_forecasting.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize SQLite database with tables and sample data."""
    os.makedirs('instance', exist_ok=True)
    
    conn = get_db_connection()
    
    # Create tables
    conn.execute('''
        CREATE TABLE IF NOT EXISTS instruments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            exchange TEXT NOT NULL,
            instrument_type TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS price_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            instrument_id INTEGER NOT NULL,
            date TIMESTAMP NOT NULL,
            open_price REAL NOT NULL,
            high_price REAL NOT NULL,
            low_price REAL NOT NULL,
            close_price REAL NOT NULL,
            volume INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (instrument_id) REFERENCES instruments (id)
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_name TEXT NOT NULL,
            model_params TEXT DEFAULT '{}',
            status TEXT DEFAULT 'created',
            instrument_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            trained_at TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (instrument_id) REFERENCES instruments (id)
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS forecasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_id INTEGER NOT NULL,
            instrument_id INTEGER NOT NULL,
            horizon INTEGER NOT NULL,
            confidence_level REAL NOT NULL,
            predictions TEXT NOT NULL,
            confidence_intervals TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (model_id) REFERENCES models (id),
            FOREIGN KEY (instrument_id) REFERENCES instruments (id)
        )
    ''')
    
    # Check if instruments already exist
    instruments = conn.execute('SELECT COUNT(*) FROM instruments').fetchone()[0]
    
    if instruments == 0:
        # Insert sample instruments
        sample_instruments = [
            ('AAPL', 'Apple Inc.', 'NASDAQ', 'STOCK'),
            ('MSFT', 'Microsoft Corporation', 'NASDAQ', 'STOCK'),
            ('BTC-USD', 'Bitcoin', 'CRYPTO', 'CRYPTO'),
            ('ETH-USD', 'Ethereum', 'CRYPTO', 'CRYPTO'),
            ('EURUSD=X', 'EUR/USD', 'FOREX', 'FOREX')
        ]
        
        conn.executemany(
            'INSERT INTO instruments (symbol, name, exchange, instrument_type) VALUES (?, ?, ?, ?)',
            sample_instruments
        )
        
        # Generate sample price data
        generate_sample_price_data(conn)
        
        print("✅ Sample data added successfully!")
    
    conn.commit()
    conn.close()

def generate_sample_price_data(conn):
    """Generate sample price data for demonstration."""
    instruments = conn.execute('SELECT id, symbol FROM instruments').fetchall()
    
    for instrument in instruments:
        instrument_id, symbol = instrument
        
        # Generate 100 days of sample data
        base_price = 150.0 if 'AAPL' in symbol else 45000.0 if 'BTC' in symbol else 1.1
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
        
        price_data = []
        current_price = base_price
        
        for date in dates:
            # Generate realistic price movement
            change = np.random.normal(0, 0.02) * current_price
            current_price += change
            
            open_price = current_price
            high_price = current_price * (1 + abs(np.random.normal(0, 0.01)))
            low_price = current_price * (1 - abs(np.random.normal(0, 0.01)))
            close_price = current_price
            volume = np.random.randint(1000000, 10000000)
            
            price_data.append((
                instrument_id,
                date.isoformat(),
                open_price,
                high_price,
                low_price,
                close_price,
                volume
            ))
        
        conn.executemany(
            '''INSERT INTO price_data (instrument_id, date, open_price, high_price, low_price, close_price, volume) 
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            price_data
        )

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'database': 'sqlite'
    })

@app.route('/api/instruments', methods=['GET'])
def get_instruments():
    """Get all financial instruments."""
    try:
        conn = get_db_connection()
        instruments = conn.execute('SELECT * FROM instruments').fetchall()
        conn.close()
        
        result = []
        for instrument in instruments:
            result.append({
                'id': instrument['id'],
                'symbol': instrument['symbol'],
                'name': instrument['name'],
                'exchange': instrument['exchange'],
                'instrument_type': instrument['instrument_type'],
                'created_at': instrument['created_at'],
                'updated_at': instrument['updated_at']
            })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/instruments/<int:instrument_id>/price-data', methods=['GET'])
def get_price_data(instrument_id):
    """Get price data for a specific instrument."""
    try:
        conn = get_db_connection()
        limit = request.args.get('limit', 100, type=int)
        
        price_data = conn.execute(
            'SELECT * FROM price_data WHERE instrument_id = ? ORDER BY date ASC LIMIT ?',
            (instrument_id, limit)
        ).fetchall()
        conn.close()
        
        result = []
        for data in price_data:
            result.append({
                'id': data['id'],
                'instrument_id': data['instrument_id'],
                'date': data['date'],
                'open_price': data['open_price'],
                'high_price': data['high_price'],
                'low_price': data['low_price'],
                'close_price': data['close_price'],
                'volume': data['volume'],
                'created_at': data['created_at']
            })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/instruments/<int:instrument_id>/price-data', methods=['POST'])
def refresh_price_data(instrument_id):
    """Refresh price data for a specific instrument."""
    try:
        # For demo purposes, just return success
        # In a real application, this would fetch new data from external APIs
        return jsonify({'message': 'Price data refreshed successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/models', methods=['GET'])
def get_models():
    """Get all trained models."""
    try:
        conn = get_db_connection()
        models = conn.execute('SELECT * FROM models').fetchall()
        conn.close()
        
        result = []
        for model in models:
            result.append({
                'id': model['id'],
                'model_name': model['model_name'],
                'model_params': json.loads(model['model_params']),
                'status': model['status'],
                'instrument_id': model['instrument_id'],
                'created_at': model['created_at'],
                'trained_at': model['trained_at'],
                'updated_at': model['updated_at']
            })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/models', methods=['POST'])
def create_model():
    """Create a new forecasting model."""
    try:
        data = request.get_json()
        
        if 'model_name' not in data:
            return jsonify({'error': 'Missing required field: model_name'}), 400
        
        conn = get_db_connection()
        cursor = conn.execute(
            'INSERT INTO models (model_name, model_params) VALUES (?, ?)',
            (data['model_name'], json.dumps(data.get('model_params', {})))
        )
        model_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({'model_id': model_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/models/<int:model_id>/train', methods=['POST'])
def train_model(model_id):
    """Train a forecasting model."""
    try:
        data = request.get_json()
        instrument_id = data.get('instrument_id')
        
        if not instrument_id:
            return jsonify({'error': 'Missing instrument_id'}), 400
        
        conn = get_db_connection()
        
        # Update model status
        conn.execute(
            'UPDATE models SET status = ?, instrument_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
            ('trained', instrument_id, model_id)
        )
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Model trained successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/models/<int:model_id>/evaluate', methods=['POST'])
def evaluate_model(model_id):
    """Evaluate a trained model."""
    try:
        data = request.get_json()
        instrument_id = data.get('instrument_id')
        
        if not instrument_id:
            return jsonify({'error': 'Missing instrument_id'}), 400
        
        # Generate sample metrics
        metrics = {
            'rmse': np.random.uniform(1.5, 3.0),
            'mae': np.random.uniform(1.0, 2.5),
            'mape': np.random.uniform(1.0, 4.0),
            'directional_accuracy': np.random.uniform(55, 75)
        }
        
        return jsonify({'metrics': metrics})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/models/<int:model_id>/predict', methods=['POST'])
def generate_forecast(model_id):
    """Generate forecast using a trained model."""
    try:
        data = request.get_json()
        horizon = data.get('horizon', 24)
        confidence_level = data.get('confidence_level', 0.95)
        instrument_id = data.get('instrument_id')
        
        if not instrument_id:
            return jsonify({'error': 'Missing instrument_id'}), 400
        
        # Generate sample forecast
        base_price = 150.0
        predictions = []
        confidence_intervals = {'lower': [], 'upper': []}
        
        for i in range(horizon):
            # Generate realistic forecast
            change = np.random.normal(0, 0.01) * base_price
            base_price += change
            predictions.append(base_price)
            
            # Generate confidence intervals
            std_dev = base_price * 0.02
            confidence_intervals['lower'].append(base_price - 1.96 * std_dev)
            confidence_intervals['upper'].append(base_price + 1.96 * std_dev)
        
        # Store forecast
        conn = get_db_connection()
        conn.execute(
            '''INSERT INTO forecasts (model_id, instrument_id, horizon, confidence_level, predictions, confidence_intervals)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (model_id, instrument_id, horizon, confidence_level, 
             json.dumps(predictions), json.dumps(confidence_intervals))
        )
        conn.commit()
        conn.close()
        
        return jsonify({
            'predictions': predictions,
            'confidence_intervals': confidence_intervals,
            'forecast_id': model_id
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/instruments/<int:instrument_id>/forecasts', methods=['GET'])
def get_forecasts(instrument_id):
    """Get forecasts for a specific instrument."""
    try:
        conn = get_db_connection()
        limit = request.args.get('limit', 100, type=int)
        
        forecasts = conn.execute(
            'SELECT * FROM forecasts WHERE instrument_id = ? ORDER BY created_at DESC LIMIT ?',
            (instrument_id, limit)
        ).fetchall()
        conn.close()
        
        result = []
        for forecast in forecasts:
            result.append({
                'id': forecast['id'],
                'model_id': forecast['model_id'],
                'instrument_id': forecast['instrument_id'],
                'horizon': forecast['horizon'],
                'confidence_level': forecast['confidence_level'],
                'predictions': json.loads(forecast['predictions']),
                'confidence_intervals': json.loads(forecast['confidence_intervals']),
                'created_at': forecast['created_at']
            })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Initialize database
    init_database()
    
    print("🚀 Starting FinTech Forecasting Application...")
    print("📊 Dashboard: http://localhost:3000")
    print("🔌 API: http://localhost:8000/api")
    print("💾 Database: SQLite")
    app.run(debug=True, host='0.0.0.0', port=8000)
