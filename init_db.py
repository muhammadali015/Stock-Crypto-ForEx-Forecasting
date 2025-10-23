"""
Simple database initialization script.
"""

import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Create Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fintech_forecasting.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'dev-secret-key'

# Initialize database
db = SQLAlchemy()
db.init_app(app)

# Import models
from backend.models import FinancialInstrument, PriceData, Forecast, ModelPerformance, NewsData

def init_database():
    """Initialize the database with tables and sample data."""
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✅ Database tables created successfully!")
        
        # Check if instruments already exist
        if FinancialInstrument.query.count() > 0:
            print("✅ Sample data already exists!")
            return
        
        # Create sample instruments
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

if __name__ == '__main__':
    init_database()
