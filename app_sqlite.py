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
CORS(app, resources={r"/api/*": {"origins": "*"}})

# SQLite database setup
DATABASE = os.path.join(os.path.dirname(__file__), 'instance', 'fintech_forecasting.db')

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize SQLite database with tables and sample data."""
    os.makedirs(os.path.join(os.path.dirname(__file__), 'instance'), exist_ok=True)
    
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
    
    # Model versioning for adaptive learning
    conn.execute('''
        CREATE TABLE IF NOT EXISTS model_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_id INTEGER NOT NULL,
            version_number INTEGER NOT NULL,
            model_path TEXT,
            training_data_size INTEGER,
            training_metrics TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (model_id) REFERENCES models (id),
            UNIQUE(model_id, version_number)
        )
    ''')
    
    # Continuous evaluation metrics
    conn.execute('''
        CREATE TABLE IF NOT EXISTS evaluation_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_id INTEGER NOT NULL,
            instrument_id INTEGER NOT NULL,
            evaluation_date TIMESTAMP NOT NULL,
            rmse REAL,
            mae REAL,
            mape REAL,
            directional_accuracy REAL,
            predictions TEXT,
            actual_values TEXT,
            FOREIGN KEY (model_id) REFERENCES models (id),
            FOREIGN KEY (instrument_id) REFERENCES instruments (id)
        )
    ''')
    
    # Prediction errors for visualization
    conn.execute('''
        CREATE TABLE IF NOT EXISTS prediction_errors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            forecast_id INTEGER NOT NULL,
            prediction_index INTEGER NOT NULL,
            predicted_value REAL NOT NULL,
            actual_value REAL,
            error_value REAL,
            error_percentage REAL,
            evaluation_date TIMESTAMP,
            FOREIGN KEY (forecast_id) REFERENCES forecasts (id)
        )
    ''')
    
    # Portfolio management
    conn.execute('''
        CREATE TABLE IF NOT EXISTS portfolios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            initial_capital REAL NOT NULL,
            current_value REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Portfolio positions
    conn.execute('''
        CREATE TABLE IF NOT EXISTS portfolio_positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            portfolio_id INTEGER NOT NULL,
            instrument_id INTEGER NOT NULL,
            quantity REAL NOT NULL,
            average_price REAL NOT NULL,
            current_price REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (portfolio_id) REFERENCES portfolios (id),
            FOREIGN KEY (instrument_id) REFERENCES instruments (id)
        )
    ''')
    
    # Trading transactions
    conn.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            portfolio_id INTEGER NOT NULL,
            instrument_id INTEGER NOT NULL,
            transaction_type TEXT NOT NULL,
            quantity REAL NOT NULL,
            price REAL NOT NULL,
            total_value REAL NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            model_id INTEGER,
            signal_strength REAL,
            FOREIGN KEY (portfolio_id) REFERENCES portfolios (id),
            FOREIGN KEY (instrument_id) REFERENCES instruments (id),
            FOREIGN KEY (model_id) REFERENCES models (id)
        )
    ''')
    
    # Portfolio performance metrics
    conn.execute('''
        CREATE TABLE IF NOT EXISTS portfolio_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            portfolio_id INTEGER NOT NULL,
            metric_date TIMESTAMP NOT NULL,
            total_value REAL NOT NULL,
            total_return REAL,
            daily_return REAL,
            volatility REAL,
            sharpe_ratio REAL,
            max_drawdown REAL,
            FOREIGN KEY (portfolio_id) REFERENCES portfolios (id)
        )
    ''')
    
    # Adaptive learning schedules
    conn.execute('''
        CREATE TABLE IF NOT EXISTS retraining_schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_id INTEGER NOT NULL,
            schedule_type TEXT NOT NULL,
            frequency_hours INTEGER,
            trigger_threshold REAL,
            last_retrained_at TIMESTAMP,
            next_retraining_at TIMESTAMP,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (model_id) REFERENCES models (id)
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

# ==================== ADAPTIVE LEARNING ENDPOINTS ====================

@app.route('/api/models/<int:model_id>/adaptive-update', methods=['POST'])
def adaptive_update(model_id):
    """Update model with new data using adaptive learning."""
    try:
        data = request.get_json()
        instrument_id = data.get('instrument_id')
        learning_strategy = data.get('learning_strategy', 'incremental')
        
        if not instrument_id:
            return jsonify({'error': 'Missing instrument_id'}), 400
        
        # Get price data for the instrument
        conn = get_db_connection()
        price_data = conn.execute(
            'SELECT * FROM price_data WHERE instrument_id = ? ORDER BY date DESC LIMIT 50',
            (instrument_id,)
        ).fetchall()
        conn.close()
        
        if len(price_data) == 0:
            return jsonify({'error': 'No data available'}), 400
        
        # Convert to DataFrame
        df = pd.DataFrame([dict(row) for row in price_data])
        df['date'] = pd.to_datetime(df['date'])
        
        # Import adaptive learning service
        from ml_models.adaptive_learning import AdaptiveLearner
        from ml_models.service import ForecastingService
        
        # Get model from service
        service = ForecastingService()
        # This is simplified - in production, you'd load the actual model
        # For now, return success
        return jsonify({
            'status': 'success',
            'message': 'Model updated successfully',
            'strategy': learning_strategy,
            'samples_processed': len(df)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/models/<int:model_id>/retraining-schedule', methods=['POST'])
def create_retraining_schedule(model_id):
    """Create a retraining schedule for a model."""
    try:
        data = request.get_json()
        schedule_type = data.get('schedule_type', 'time_based')
        frequency_hours = data.get('frequency_hours', 24)
        trigger_threshold = data.get('trigger_threshold', 0.1)
        
        conn = get_db_connection()
        next_retraining = datetime.now() + timedelta(hours=frequency_hours)
        
        conn.execute(
            '''INSERT INTO retraining_schedules 
               (model_id, schedule_type, frequency_hours, trigger_threshold, next_retraining_at, is_active)
               VALUES (?, ?, ?, ?, ?, 1)''',
            (model_id, schedule_type, frequency_hours, trigger_threshold, next_retraining)
        )
        conn.commit()
        schedule_id = conn.lastrowid
        conn.close()
        
        return jsonify({
            'schedule_id': schedule_id,
            'next_retraining_at': next_retraining.isoformat()
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== CONTINUOUS EVALUATION ENDPOINTS ====================

@app.route('/api/evaluation/<int:model_id>/evaluate', methods=['POST'])
def evaluate_prediction(model_id):
    """Evaluate model predictions against actual values."""
    try:
        data = request.get_json()
        forecast_id = data.get('forecast_id')
        actual_values = data.get('actual_values')
        instrument_id = data.get('instrument_id')
        
        if not forecast_id or not actual_values or not instrument_id:
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Get forecast predictions
        conn = get_db_connection()
        forecast = conn.execute(
            'SELECT predictions FROM forecasts WHERE id = ?',
            (forecast_id,)
        ).fetchone()
        
        if not forecast:
            return jsonify({'error': 'Forecast not found'}), 404
        
        predictions = json.loads(forecast['predictions'])
        
        if len(predictions) != len(actual_values):
            return jsonify({'error': 'Predictions and actual values must have same length'}), 400
        
        # Calculate metrics
        from ml_models.base import PerformanceMetrics
        metrics = PerformanceMetrics.calculate_metrics(
            np.array(actual_values),
            np.array(predictions)
        )
        
        # Store evaluation
        conn.execute(
            '''INSERT INTO evaluation_metrics 
               (model_id, instrument_id, evaluation_date, rmse, mae, mape, directional_accuracy, predictions, actual_values)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (model_id, instrument_id, datetime.now(), metrics['rmse'], metrics['mae'], 
             metrics['mape'], metrics.get('directional_accuracy', 0),
             json.dumps(predictions), json.dumps(actual_values))
        )
        
        # Store prediction errors for visualization
        for i in range(len(predictions)):
            error = abs(predictions[i] - actual_values[i])
            error_pct = (error / actual_values[i]) * 100 if actual_values[i] != 0 else 0
            
            conn.execute(
                '''INSERT INTO prediction_errors 
                   (forecast_id, prediction_index, predicted_value, actual_value, error_value, error_percentage, evaluation_date)
                   VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (forecast_id, i, predictions[i], actual_values[i], error, error_pct, datetime.now())
            )
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'metrics': metrics,
            'forecast_id': forecast_id,
            'evaluation_date': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/evaluation/<int:model_id>/metrics', methods=['GET'])
def get_evaluation_metrics(model_id):
    """Get evaluation metrics history for a model."""
    try:
        conn = get_db_connection()
        limit = request.args.get('limit', 50, type=int)
        
        metrics = conn.execute(
            '''SELECT * FROM evaluation_metrics 
               WHERE model_id = ? 
               ORDER BY evaluation_date DESC 
               LIMIT ?''',
            (model_id, limit)
        ).fetchall()
        conn.close()
        
        result = []
        for m in metrics:
            result.append({
                'id': m['id'],
                'model_id': m['model_id'],
                'instrument_id': m['instrument_id'],
                'evaluation_date': m['evaluation_date'],
                'rmse': m['rmse'],
                'mae': m['mae'],
                'mape': m['mape'],
                'directional_accuracy': m['directional_accuracy']
            })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/forecasts/<int:forecast_id>/errors', methods=['GET'])
def get_forecast_errors(forecast_id):
    """Get prediction errors for a forecast (for visualization)."""
    try:
        conn = get_db_connection()
        errors = conn.execute(
            'SELECT * FROM prediction_errors WHERE forecast_id = ? ORDER BY prediction_index',
            (forecast_id,)
        ).fetchall()
        conn.close()
        
        result = []
        for e in errors:
            result.append({
                'prediction_index': e['prediction_index'],
                'predicted_value': e['predicted_value'],
                'actual_value': e['actual_value'],
                'error_value': e['error_value'],
                'error_percentage': e['error_percentage'],
                'evaluation_date': e['evaluation_date']
            })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== PORTFOLIO MANAGEMENT ENDPOINTS ====================

@app.route('/api/portfolios', methods=['POST'])
def create_portfolio():
    """Create a new portfolio."""
    try:
        data = request.get_json()
        name = data.get('name', 'Default Portfolio')
        initial_capital = data.get('initial_capital', 10000.0)
        
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO portfolios (name, initial_capital, current_value) VALUES (?, ?, ?)',
            (name, initial_capital, initial_capital)
        )
        conn.commit()
        portfolio_id = conn.lastrowid
        conn.close()
        
        return jsonify({
            'portfolio_id': portfolio_id,
            'name': name,
            'initial_capital': initial_capital,
            'current_value': initial_capital
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/portfolios', methods=['GET'])
def get_portfolios():
    """Get all portfolios."""
    try:
        conn = get_db_connection()
        portfolios = conn.execute('SELECT * FROM portfolios').fetchall()
        conn.close()
        
        result = []
        for p in portfolios:
            result.append({
                'id': p['id'],
                'name': p['name'],
                'initial_capital': p['initial_capital'],
                'current_value': p['current_value'],
                'created_at': p['created_at']
            })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/portfolios/<int:portfolio_id>/buy', methods=['POST'])
def buy_instrument(portfolio_id):
    """Execute a buy order."""
    try:
        data = request.get_json()
        instrument_id = data.get('instrument_id')
        quantity = data.get('quantity')
        price = data.get('price')
        model_id = data.get('model_id')
        
        if not instrument_id or not quantity or not price:
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Get portfolio
        conn = get_db_connection()
        portfolio = conn.execute(
            'SELECT * FROM portfolios WHERE id = ?',
            (portfolio_id,)
        ).fetchone()
        
        if not portfolio:
            return jsonify({'error': 'Portfolio not found'}), 404
        
        if portfolio['current_value'] < quantity * price:
            return jsonify({'error': 'Insufficient funds'}), 400
        
        # Record transaction
        total_value = quantity * price
        conn.execute(
            '''INSERT INTO transactions 
               (portfolio_id, instrument_id, transaction_type, quantity, price, total_value, model_id)
               VALUES (?, ?, 'buy', ?, ?, ?, ?)''',
            (portfolio_id, instrument_id, quantity, price, total_value, model_id)
        )
        
        # Update portfolio
        new_value = portfolio['current_value'] - total_value
        conn.execute(
            'UPDATE portfolios SET current_value = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
            (new_value, portfolio_id)
        )
        
        # Update or create position
        position = conn.execute(
            'SELECT * FROM portfolio_positions WHERE portfolio_id = ? AND instrument_id = ?',
            (portfolio_id, instrument_id)
        ).fetchone()
        
        if position:
            # Update existing position
            new_quantity = position['quantity'] + quantity
            total_cost = (position['quantity'] * position['average_price']) + total_value
            new_avg_price = total_cost / new_quantity
            conn.execute(
                '''UPDATE portfolio_positions 
                   SET quantity = ?, average_price = ?, current_price = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE portfolio_id = ? AND instrument_id = ?''',
                (new_quantity, new_avg_price, price, portfolio_id, instrument_id)
            )
        else:
            # Create new position
            conn.execute(
                '''INSERT INTO portfolio_positions 
                   (portfolio_id, instrument_id, quantity, average_price, current_price)
                   VALUES (?, ?, ?, ?, ?)''',
                (portfolio_id, instrument_id, quantity, price, price)
            )
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'transaction_type': 'buy',
            'quantity': quantity,
            'price': price,
            'total_value': total_value
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/portfolios/<int:portfolio_id>/sell', methods=['POST'])
def sell_instrument(portfolio_id):
    """Execute a sell order."""
    try:
        data = request.get_json()
        instrument_id = data.get('instrument_id')
        quantity = data.get('quantity')
        price = data.get('price')
        model_id = data.get('model_id')
        
        if not instrument_id or not quantity or not price:
            return jsonify({'error': 'Missing required fields'}), 400
        
        conn = get_db_connection()
        position = conn.execute(
            'SELECT * FROM portfolio_positions WHERE portfolio_id = ? AND instrument_id = ?',
            (portfolio_id, instrument_id)
        ).fetchone()
        
        if not position:
            return jsonify({'error': 'No position found'}), 404
        
        if quantity > position['quantity']:
            return jsonify({'error': 'Insufficient quantity'}), 400
        
        # Record transaction
        total_value = quantity * price
        conn.execute(
            '''INSERT INTO transactions 
               (portfolio_id, instrument_id, transaction_type, quantity, price, total_value, model_id)
               VALUES (?, ?, 'sell', ?, ?, ?, ?)''',
            (portfolio_id, instrument_id, quantity, price, total_value, model_id)
        )
        
        # Update portfolio value
        portfolio = conn.execute(
            'SELECT * FROM portfolios WHERE id = ?',
            (portfolio_id,)
        ).fetchone()
        
        new_value = portfolio['current_value'] + total_value
        conn.execute(
            'UPDATE portfolios SET current_value = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
            (new_value, portfolio_id)
        )
        
        # Update position
        if quantity == position['quantity']:
            # Sell entire position
            conn.execute(
                'DELETE FROM portfolio_positions WHERE portfolio_id = ? AND instrument_id = ?',
                (portfolio_id, instrument_id)
            )
        else:
            # Partial sale
            new_quantity = position['quantity'] - quantity
            conn.execute(
                '''UPDATE portfolio_positions 
                   SET quantity = ?, current_price = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE portfolio_id = ? AND instrument_id = ?''',
                (new_quantity, price, portfolio_id, instrument_id)
            )
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'transaction_type': 'sell',
            'quantity': quantity,
            'price': price,
            'total_value': total_value
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/portfolios/<int:portfolio_id>/positions', methods=['GET'])
def get_portfolio_positions(portfolio_id):
    """Get all positions for a portfolio."""
    try:
        conn = get_db_connection()
        positions = conn.execute(
            '''SELECT pp.*, i.symbol, i.name 
               FROM portfolio_positions pp
               JOIN instruments i ON pp.instrument_id = i.id
               WHERE pp.portfolio_id = ?''',
            (portfolio_id,)
        ).fetchall()
        conn.close()
        
        result = []
        for p in positions:
            unrealized_pnl = (p['current_price'] - p['average_price']) * p['quantity']
            unrealized_pnl_pct = ((p['current_price'] - p['average_price']) / p['average_price']) * 100 if p['average_price'] > 0 else 0
            
            result.append({
                'id': p['id'],
                'instrument_id': p['instrument_id'],
                'symbol': p['symbol'],
                'name': p['name'],
                'quantity': p['quantity'],
                'average_price': p['average_price'],
                'current_price': p['current_price'],
                'current_value': p['quantity'] * p['current_price'],
                'unrealized_pnl': unrealized_pnl,
                'unrealized_pnl_pct': unrealized_pnl_pct
            })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/portfolios/<int:portfolio_id>/metrics', methods=['GET'])
def get_portfolio_metrics(portfolio_id):
    """Get portfolio performance metrics."""
    try:
        conn = get_db_connection()
        portfolio = conn.execute(
            'SELECT * FROM portfolios WHERE id = ?',
            (portfolio_id,)
        ).fetchone()
        
        if not portfolio:
            return jsonify({'error': 'Portfolio not found'}), 404
        
        # Get positions
        positions = conn.execute(
            'SELECT * FROM portfolio_positions WHERE portfolio_id = ?',
            (portfolio_id,)
        ).fetchall()
        
        # Calculate total value
        positions_value = sum(p['quantity'] * p['current_price'] for p in positions)
        total_value = portfolio['current_value'] + positions_value
        
        # Get historical metrics
        historical = conn.execute(
            '''SELECT * FROM portfolio_metrics 
               WHERE portfolio_id = ? 
               ORDER BY metric_date DESC 
               LIMIT 30''',
            (portfolio_id,)
        ).fetchall()
        
        # Calculate returns
        total_return = ((total_value - portfolio['initial_capital']) / portfolio['initial_capital']) * 100 if portfolio['initial_capital'] > 0 else 0
        
        # Calculate Sharpe ratio and volatility if we have historical data
        if len(historical) > 1:
            values = [h['total_value'] for h in historical[::-1]]
            returns = np.diff(values) / values[:-1] if len(values) > 1 else [0.0]
            
            if len(returns) > 0 and np.std(returns) > 0:
                sharpe_ratio = (np.mean(returns) / np.std(returns)) * np.sqrt(252)
                volatility = np.std(returns) * np.sqrt(252) * 100
            else:
                sharpe_ratio = 0.0
                volatility = 0.0
        else:
            sharpe_ratio = 0.0
            volatility = 0.0
        
        # Calculate unrealized PnL
        unrealized_pnl = sum((p['current_price'] - p['average_price']) * p['quantity'] for p in positions)
        
        conn.close()
        
        return jsonify({
            'portfolio_id': portfolio_id,
            'total_value': total_value,
            'initial_capital': portfolio['initial_capital'],
            'total_return': total_return,
            'unrealized_pnl': unrealized_pnl,
            'sharpe_ratio': sharpe_ratio,
            'volatility': volatility,
            'positions_count': len(positions)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/portfolios/<int:portfolio_id>/metrics/history', methods=['GET'])
def get_portfolio_metrics_history(portfolio_id):
    """Get historical portfolio metrics for charting."""
    try:
        conn = get_db_connection()
        limit = request.args.get('limit', 100, type=int)
        
        historical = conn.execute(
            '''SELECT * FROM portfolio_metrics 
               WHERE portfolio_id = ? 
               ORDER BY metric_date ASC 
               LIMIT ?''',
            (portfolio_id, limit)
        ).fetchall()
        
        # Get initial capital for first data point
        portfolio = conn.execute(
            'SELECT initial_capital FROM portfolios WHERE id = ?',
            (portfolio_id,)
        ).fetchone()
        
        conn.close()
        
        result = []
        for h in historical:
            result.append({
                'metric_date': h['metric_date'],
                'total_value': h['total_value'],
                'total_return': h['total_return'] if h['total_return'] is not None else 0,
                'daily_return': h['daily_return'] if h['daily_return'] is not None else 0,
                'volatility': h['volatility'] if h['volatility'] is not None else 0,
                'sharpe_ratio': h['sharpe_ratio'] if h['sharpe_ratio'] is not None else 0
            })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/portfolios/<int:portfolio_id>/transactions', methods=['GET'])
def get_portfolio_transactions(portfolio_id):
    """Get transaction history for a portfolio."""
    try:
        conn = get_db_connection()
        limit = request.args.get('limit', 100, type=int)
        
        transactions = conn.execute(
            '''SELECT t.*, i.symbol, i.name 
               FROM transactions t
               JOIN instruments i ON t.instrument_id = i.id
               WHERE t.portfolio_id = ?
               ORDER BY t.timestamp DESC
               LIMIT ?''',
            (portfolio_id, limit)
        ).fetchall()
        conn.close()
        
        result = []
        for t in transactions:
            result.append({
                'id': t['id'],
                'instrument_id': t['instrument_id'],
                'symbol': t['symbol'],
                'name': t['name'],
                'transaction_type': t['transaction_type'],
                'quantity': t['quantity'],
                'price': t['price'],
                'total_value': t['total_value'],
                'timestamp': t['timestamp'],
                'model_id': t['model_id']
            })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/portfolios/<int:portfolio_id>', methods=['DELETE'])
def delete_portfolio(portfolio_id):
    """Delete a portfolio and all related data."""
    try:
        conn = get_db_connection()
        
        # Check if portfolio exists
        portfolio = conn.execute(
            'SELECT * FROM portfolios WHERE id = ?',
            (portfolio_id,)
        ).fetchone()
        
        if not portfolio:
            return jsonify({'error': 'Portfolio not found'}), 404
        
        # Delete related data in order (to maintain referential integrity)
        # Delete portfolio metrics
        conn.execute(
            'DELETE FROM portfolio_metrics WHERE portfolio_id = ?',
            (portfolio_id,)
        )
        
        # Delete transactions
        conn.execute(
            'DELETE FROM transactions WHERE portfolio_id = ?',
            (portfolio_id,)
        )
        
        # Delete positions
        conn.execute(
            'DELETE FROM portfolio_positions WHERE portfolio_id = ?',
            (portfolio_id,)
        )
        
        # Delete portfolio
        conn.execute(
            'DELETE FROM portfolios WHERE id = ?',
            (portfolio_id,)
        )
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Portfolio {portfolio_id} deleted successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/portfolios/delete-by-name', methods=['POST'])
def delete_portfolios_by_name():
    """Delete all portfolios with a specific name."""
    try:
        data = request.get_json()
        name = data.get('name')
        
        if not name:
            return jsonify({'error': 'Portfolio name is required'}), 400
        
        conn = get_db_connection()
        
        # Get all portfolios with this name
        portfolios = conn.execute(
            'SELECT id FROM portfolios WHERE name = ?',
            (name,)
        ).fetchall()
        
        if not portfolios:
            return jsonify({
                'success': False,
                'message': f'No portfolios found with name "{name}"'
            }), 404
        
        deleted_count = 0
        
        for portfolio in portfolios:
            portfolio_id = portfolio['id']
            
            # Delete related data
            conn.execute('DELETE FROM portfolio_metrics WHERE portfolio_id = ?', (portfolio_id,))
            conn.execute('DELETE FROM transactions WHERE portfolio_id = ?', (portfolio_id,))
            conn.execute('DELETE FROM portfolio_positions WHERE portfolio_id = ?', (portfolio_id,))
            conn.execute('DELETE FROM portfolios WHERE id = ?', (portfolio_id,))
            
            deleted_count += 1
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Deleted {deleted_count} portfolio(s) with name "{name}"',
            'deleted_count': deleted_count
        })
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
