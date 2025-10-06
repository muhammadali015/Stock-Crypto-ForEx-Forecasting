"""
Flask backend API for the financial forecasting application
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import sys
from typing import Dict, List, Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import DatabaseManager
from ml_models.ml_orchestrator import MLOrchestrator
from prices import fetch_price_history, compute_minimal_indicators
from news import fetch_news_items, score_sentiment, aggregate_daily_sentiment
from features import build_feature_frame
from align import align_and_save

app = Flask(__name__)
CORS(app)

# Initialize components
db_manager = DatabaseManager()
ml_orchestrator = MLOrchestrator()

# Configuration
app.config['JSON_SORT_KEYS'] = False


@app.route('/')
def index():
    """Serve the main application page"""
    return render_template('index.html')


@app.route('/api/instruments', methods=['GET'])
def get_instruments():
    """Get list of available instruments"""
    try:
        instruments = db_manager.get_available_instruments()
        return jsonify({
            'success': True,
            'instruments': instruments,
            'count': len(instruments)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/instruments/<instrument>', methods=['POST'])
def add_instrument_data(instrument: str):
    """Add historical data for a new instrument"""
    try:
        data = request.get_json()
        days = data.get('days', 30)
        
        # Fetch price data
        price_df = fetch_price_history(instrument, period_days=days)
        price_df = compute_minimal_indicators(price_df)
        
        # Fetch news data
        news_items = fetch_news_items(instrument)
        news_scored = score_sentiment(news_items)
        news_daily = pd.DataFrame(aggregate_daily_sentiment(news_scored))
        
        # Build feature frame
        features_df = build_feature_frame(price_df, news_daily if not news_daily.empty else pd.DataFrame())
        
        # Convert to list of dictionaries for database insertion
        data_list = features_df.to_dict('records')
        
        # Insert into database
        success = db_manager.insert_historical_data(instrument, data_list)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Successfully added {len(data_list)} records for {instrument}',
                'records_added': len(data_list)
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to insert data into database'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/instruments/<instrument>/data', methods=['GET'])
def get_instrument_data(instrument: str):
    """Get historical data for an instrument"""
    try:
        # Get query parameters
        limit = request.args.get('limit', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Parse dates if provided
        start_dt = None
        end_dt = None
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        # Get data from database
        data = db_manager.get_historical_data(instrument, start_dt, end_dt, limit)
        
        # Convert ObjectId to string for JSON serialization
        for record in data:
            record['_id'] = str(record['_id'])
        
        return jsonify({
            'success': True,
            'data': data,
            'count': len(data)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/instruments/<instrument>/forecast', methods=['POST'])
def generate_forecast(instrument: str):
    """Generate forecast for an instrument"""
    try:
        data = request.get_json()
        forecast_hours = data.get('forecast_hours', 24)
        
        # Validate forecast_hours
        if not isinstance(forecast_hours, int) or forecast_hours <= 0 or forecast_hours > 168:  # Max 1 week
            return jsonify({
                'success': False,
                'error': 'forecast_hours must be an integer between 1 and 168'
            }), 400
        
        # Get historical data
        historical_data = db_manager.get_historical_data(instrument, limit=1000)
        
        if not historical_data:
            return jsonify({
                'success': False,
                'error': f'No historical data found for {instrument}'
            }), 404
        
        # Convert to DataFrame
        df = pd.DataFrame(historical_data)
        df = df.drop(columns=['_id', 'created_at', 'updated_at'])
        
        # Generate forecast
        results = ml_orchestrator.run_all_models(df, forecast_hours)
        
        # Get best model
        best_model = ml_orchestrator.get_best_model(results)
        
        # Save forecasts to database
        for category, models in results['forecasts'].items():
            for model_name, model_result in models.items():
                if 'forecast' in model_result and 'error' not in model_result:
                    forecast_data = {
                        'category': category,
                        'forecast_hours': forecast_hours,
                        'forecast': model_result['forecast'].tolist(),
                        'forecast_dates': results['metadata']['forecast_dates'],
                        'model_parameters': model_result.get('model_parameters', {})
                    }
                    
                    if 'confidence_intervals' in model_result:
                        forecast_data['confidence_intervals'] = model_result['confidence_intervals'].tolist()
                    
                    db_manager.insert_forecast(instrument, f"{category}_{model_name}", forecast_data)
        
        # Save performance metrics
        for category, models in results['performance_metrics'].items():
            for model_name, metrics in models.items():
                metrics['data_points_evaluated'] = len(historical_data)
                db_manager.insert_performance_metrics(instrument, f"{category}_{model_name}", metrics)
        
        return jsonify({
            'success': True,
            'forecast_results': results,
            'best_model': best_model
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/instruments/<instrument>/forecasts', methods=['GET'])
def get_forecasts(instrument: str):
    """Get latest forecasts for an instrument"""
    try:
        model_name = request.args.get('model_name')
        
        forecast = db_manager.get_latest_forecast(instrument, model_name)
        
        if forecast:
            forecast['_id'] = str(forecast['_id'])
            return jsonify({
                'success': True,
                'forecast': forecast
            })
        else:
            return jsonify({
                'success': False,
                'error': f'No forecasts found for {instrument}'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/instruments/<instrument>/models', methods=['GET'])
def get_available_models(instrument: str):
    """Get available models for an instrument"""
    try:
        models = db_manager.get_available_models(instrument)
        return jsonify({
            'success': True,
            'models': models,
            'count': len(models)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/instruments/<instrument>/performance/<model_name>', methods=['GET'])
def get_model_performance(instrument: str, model_name: str):
    """Get performance history for a model"""
    try:
        limit = request.args.get('limit', type=int)
        
        performance_history = db_manager.get_model_performance_history(instrument, model_name, limit)
        
        # Convert ObjectId to string
        for record in performance_history:
            record['_id'] = str(record['_id'])
        
        return jsonify({
            'success': True,
            'performance_history': performance_history,
            'count': len(performance_history)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/stats', methods=['GET'])
def get_database_stats():
    """Get database statistics"""
    try:
        stats = db_manager.get_database_stats()
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        stats = db_manager.get_database_stats()
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database_connected': True
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500


if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    # Run the application
    app.run(debug=True, host='0.0.0.0', port=5000)
