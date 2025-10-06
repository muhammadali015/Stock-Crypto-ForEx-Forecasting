"""
MongoDB database schema and connection management
"""

import pymongo
from pymongo import MongoClient
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
import os
from dotenv import load_dotenv

load_dotenv()


class DatabaseManager:
    """MongoDB database manager for financial forecasting application"""
    
    def __init__(self, connection_string: str = None):
        if connection_string is None:
            connection_string = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
        
        self.client = MongoClient(connection_string)
        self.db = self.client['fintech_forecasting']
        
        # Define collections
        self.historical_data = self.db['historical_data']
        self.forecasts = self.db['forecasts']
        self.model_metadata = self.db['model_metadata']
        self.performance_metrics = self.db['performance_metrics']
        
        # Create indexes for better performance
        self._create_indexes()
    
    def _create_indexes(self):
        """Create database indexes for optimal performance"""
        # Historical data indexes
        self.historical_data.create_index([("instrument", 1), ("date", 1)], unique=True)
        self.historical_data.create_index([("instrument", 1)])
        self.historical_data.create_index([("date", 1)])
        
        # Forecasts indexes
        self.forecasts.create_index([("instrument", 1), ("forecast_date", 1), ("model_name", 1)])
        self.forecasts.create_index([("instrument", 1)])
        self.forecasts.create_index([("created_at", 1)])
        
        # Model metadata indexes
        self.model_metadata.create_index([("model_name", 1), ("instrument", 1)])
        
        # Performance metrics indexes
        self.performance_metrics.create_index([("instrument", 1), ("model_name", 1), ("evaluation_date", 1)])
    
    def insert_historical_data(self, instrument: str, data: List[Dict]) -> bool:
        """Insert historical price data"""
        try:
            documents = []
            for record in data:
                document = {
                    'instrument': instrument,
                    'date': record['Date'],
                    'open': record.get('Open'),
                    'high': record.get('High'),
                    'low': record.get('Low'),
                    'close': record.get('Close'),
                    'adj_close': record.get('Adj Close'),
                    'volume': record.get('Volume'),
                    'daily_return': record.get('daily_return'),
                    'volatility_5d': record.get('volatility_5d'),
                    'ma_5': record.get('ma_5'),
                    'ma_10': record.get('ma_10'),
                    'volume_zscore_5d': record.get('volume_zscore_5d'),
                    'news_count': record.get('news_count'),
                    'sent_compound_mean': record.get('sent_compound_mean'),
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                }
                documents.append(document)
            
            # Use upsert to handle duplicates
            for doc in documents:
                self.historical_data.update_one(
                    {'instrument': doc['instrument'], 'date': doc['date']},
                    {'$set': doc},
                    upsert=True
                )
            
            return True
        except Exception as e:
            print(f"Error inserting historical data: {e}")
            return False
    
    def get_historical_data(self, instrument: str, start_date: Optional[datetime] = None, 
                           end_date: Optional[datetime] = None, limit: Optional[int] = None) -> List[Dict]:
        """Retrieve historical data for an instrument"""
        try:
            query = {'instrument': instrument}
            
            if start_date or end_date:
                date_query = {}
                if start_date:
                    date_query['$gte'] = start_date
                if end_date:
                    date_query['$lte'] = end_date
                query['date'] = date_query
            
            cursor = self.historical_data.find(query).sort('date', 1)
            
            if limit:
                cursor = cursor.limit(limit)
            
            return list(cursor)
        except Exception as e:
            print(f"Error retrieving historical data: {e}")
            return []
    
    def insert_forecast(self, instrument: str, model_name: str, forecast_data: Dict) -> bool:
        """Insert forecast results"""
        try:
            document = {
                'instrument': instrument,
                'model_name': model_name,
                'model_category': forecast_data.get('category', 'unknown'),
                'forecast_hours': forecast_data.get('forecast_hours', 0),
                'forecast_values': forecast_data.get('forecast', []),
                'forecast_dates': forecast_data.get('forecast_dates', []),
                'confidence_intervals': forecast_data.get('confidence_intervals', []),
                'model_parameters': forecast_data.get('model_parameters', {}),
                'created_at': datetime.now(),
                'forecast_date': datetime.now()
            }
            
            # Remove None values
            document = {k: v for k, v in document.items() if v is not None}
            
            self.forecasts.insert_one(document)
            return True
        except Exception as e:
            print(f"Error inserting forecast: {e}")
            return False
    
    def get_latest_forecast(self, instrument: str, model_name: Optional[str] = None) -> Optional[Dict]:
        """Get the latest forecast for an instrument"""
        try:
            query = {'instrument': instrument}
            if model_name:
                query['model_name'] = model_name
            
            return self.forecasts.find_one(query, sort=[('created_at', -1)])
        except Exception as e:
            print(f"Error retrieving latest forecast: {e}")
            return None
    
    def get_forecasts_by_date_range(self, instrument: str, start_date: datetime, 
                                   end_date: datetime) -> List[Dict]:
        """Get forecasts within a date range"""
        try:
            query = {
                'instrument': instrument,
                'created_at': {
                    '$gte': start_date,
                    '$lte': end_date
                }
            }
            
            return list(self.forecasts.find(query).sort('created_at', 1))
        except Exception as e:
            print(f"Error retrieving forecasts by date range: {e}")
            return []
    
    def insert_model_metadata(self, model_name: str, instrument: str, metadata: Dict) -> bool:
        """Insert model metadata"""
        try:
            document = {
                'model_name': model_name,
                'instrument': instrument,
                'model_type': metadata.get('model_type', 'unknown'),
                'parameters': metadata.get('parameters', {}),
                'training_data_size': metadata.get('training_data_size', 0),
                'sequence_length': metadata.get('sequence_length', 0),
                'created_at': datetime.now(),
                'last_updated': datetime.now()
            }
            
            # Update existing or insert new
            self.model_metadata.update_one(
                {'model_name': model_name, 'instrument': instrument},
                {'$set': document},
                upsert=True
            )
            
            return True
        except Exception as e:
            print(f"Error inserting model metadata: {e}")
            return False
    
    def insert_performance_metrics(self, instrument: str, model_name: str, metrics: Dict) -> bool:
        """Insert model performance metrics"""
        try:
            document = {
                'instrument': instrument,
                'model_name': model_name,
                'rmse': metrics.get('rmse'),
                'mae': metrics.get('mae'),
                'mape': metrics.get('mape'),
                'evaluation_date': datetime.now(),
                'data_points_evaluated': metrics.get('data_points_evaluated', 0),
                'created_at': datetime.now()
            }
            
            self.performance_metrics.insert_one(document)
            return True
        except Exception as e:
            print(f"Error inserting performance metrics: {e}")
            return False
    
    def get_model_performance_history(self, instrument: str, model_name: str, 
                                     limit: Optional[int] = None) -> List[Dict]:
        """Get performance history for a model"""
        try:
            query = {'instrument': instrument, 'model_name': model_name}
            cursor = self.performance_metrics.find(query).sort('evaluation_date', -1)
            
            if limit:
                cursor = cursor.limit(limit)
            
            return list(cursor)
        except Exception as e:
            print(f"Error retrieving model performance history: {e}")
            return []
    
    def get_available_instruments(self) -> List[str]:
        """Get list of all available instruments"""
        try:
            return self.historical_data.distinct('instrument')
        except Exception as e:
            print(f"Error retrieving available instruments: {e}")
            return []
    
    def get_available_models(self, instrument: Optional[str] = None) -> List[str]:
        """Get list of available models"""
        try:
            query = {}
            if instrument:
                query['instrument'] = instrument
            
            return self.forecasts.distinct('model_name', query)
        except Exception as e:
            print(f"Error retrieving available models: {e}")
            return []
    
    def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old forecast data"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            # Remove old forecasts
            result = self.forecasts.delete_many({
                'created_at': {'$lt': cutoff_date}
            })
            
            print(f"Cleaned up {result.deleted_count} old forecast records")
            return True
        except Exception as e:
            print(f"Error cleaning up old data: {e}")
            return False
    
    def get_database_stats(self) -> Dict:
        """Get database statistics"""
        try:
            stats = {
                'historical_data_count': self.historical_data.count_documents({}),
                'forecasts_count': self.forecasts.count_documents({}),
                'model_metadata_count': self.model_metadata.count_documents({}),
                'performance_metrics_count': self.performance_metrics.count_documents({}),
                'instruments_count': len(self.get_available_instruments()),
                'models_count': len(self.get_available_models())
            }
            return stats
        except Exception as e:
            print(f"Error getting database stats: {e}")
            return {}
    
    def close_connection(self):
        """Close database connection"""
        self.client.close()
