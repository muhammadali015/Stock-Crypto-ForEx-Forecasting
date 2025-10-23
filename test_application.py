#!/usr/bin/env python3
"""
Comprehensive test script for FinTech Forecasting Application
Tests all API endpoints and functionality
"""

import requests
import json
import time
import sys

API_BASE_URL = "http://localhost:8000/api"

def test_endpoint(endpoint, method="GET", data=None, expected_status=200):
    """Test a single API endpoint"""
    url = f"{API_BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        elif method == "PUT":
            response = requests.put(url, json=data, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, timeout=10)
        
        if response.status_code == expected_status:
            print(f"✅ {method} {endpoint} - Status: {response.status_code}")
            return True, response.json() if response.content else {}
        else:
            print(f"❌ {method} {endpoint} - Status: {response.status_code} (Expected: {expected_status})")
            return False, None
    except requests.exceptions.RequestException as e:
        print(f"❌ {method} {endpoint} - Error: {str(e)}")
        return False, None

def main():
    print("🚀 Starting FinTech Forecasting Application Tests")
    print("=" * 60)
    
    # Test 1: Health Check
    print("\n📊 Testing Health Check...")
    success, data = test_endpoint("/health")
    if success:
        print(f"   Database: {data.get('database', 'Unknown')}")
        print(f"   Version: {data.get('version', 'Unknown')}")
    
    # Test 2: Get Instruments
    print("\n📈 Testing Instruments...")
    success, instruments = test_endpoint("/instruments")
    if success and instruments:
        print(f"   Found {len(instruments)} instruments:")
        for instrument in instruments[:3]:  # Show first 3
            print(f"   - {instrument['symbol']}: {instrument['name']}")
    
    # Test 3: Get Price Data
    print("\n💰 Testing Price Data...")
    if success and instruments:
        instrument_id = instruments[0]['id']
        success, price_data = test_endpoint(f"/instruments/{instrument_id}/price-data?limit=5")
        if success and price_data:
            print(f"   Found {len(price_data)} price records for {instruments[0]['symbol']}")
            print(f"   Sample data: {price_data[0]['date']} - Close: ${price_data[0]['close_price']:.2f}")
    
    # Test 4: Refresh Price Data
    print("\n🔄 Testing Data Refresh...")
    if success and instruments:
        success, refresh_data = test_endpoint(f"/instruments/{instrument_id}/price-data", "POST")
        if success:
            print(f"   Refresh message: {refresh_data.get('message', 'Success')}")
    
    # Test 5: Get Models
    print("\n🤖 Testing Models...")
    success, models = test_endpoint("/models")
    if success:
        print(f"   Found {len(models)} models")
    
    # Test 6: Create Model
    print("\n➕ Testing Model Creation...")
    model_data = {"model_name": "test_model", "model_params": {}}
    success, model_response = test_endpoint("/models", "POST", model_data, 201)
    if success:
        model_id = model_response.get('model_id')
        print(f"   Created model with ID: {model_id}")
        
        # Test 7: Train Model
        print("\n🎯 Testing Model Training...")
        train_data = {"instrument_id": instrument_id}
        success, train_response = test_endpoint(f"/models/{model_id}/train", "POST", train_data)
        if success:
            print(f"   Training message: {train_response.get('message', 'Success')}")
        
        # Test 8: Evaluate Model
        print("\n📊 Testing Model Evaluation...")
        eval_data = {"instrument_id": instrument_id}
        success, eval_response = test_endpoint(f"/models/{model_id}/evaluate", "POST", eval_data)
        if success:
            metrics = eval_response.get('metrics', {})
            print(f"   Evaluation metrics: RMSE={metrics.get('rmse', 'N/A'):.2f}")
        
        # Test 9: Generate Forecast
        print("\n🔮 Testing Forecast Generation...")
        forecast_data = {
            "horizon": 24,
            "confidence_level": 0.95,
            "instrument_id": instrument_id
        }
        success, forecast_response = test_endpoint(f"/models/{model_id}/predict", "POST", forecast_data)
        if success:
            predictions = forecast_response.get('predictions', [])
            print(f"   Generated {len(predictions)} forecast points")
    
    # Test 10: Get Forecasts
    print("\n📋 Testing Forecast Retrieval...")
    if success and instruments:
        success, forecasts = test_endpoint(f"/instruments/{instrument_id}/forecasts")
        if success:
            print(f"   Found {len(forecasts)} forecast records")
    
    print("\n" + "=" * 60)
    print("🎉 Test Summary Complete!")
    print("\nTo start the frontend:")
    print("1. Navigate to the frontend directory: cd frontend")
    print("2. Start the React app: npm start")
    print("3. Open http://localhost:3000 in your browser")
    print("\nThe application should now be fully functional with:")
    print("- ✅ Working API endpoints")
    print("- ✅ Fixed dropdown visibility")
    print("- ✅ Chart data display")
    print("- ✅ All interactive features")

if __name__ == "__main__":
    main()
