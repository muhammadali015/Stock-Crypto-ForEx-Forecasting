"""
Neural network forecasting models for financial time series
Includes LSTM, GRU, and Transformer models
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
import tensorflow as tf
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import LSTM, GRU, Dense, Dropout, Input, MultiHeadAttention, LayerNormalization
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping
import warnings
warnings.filterwarnings('ignore')


class NeuralForecaster:
    """Neural network forecasting models"""
    
    def __init__(self, sequence_length: int = 60):
        self.sequence_length = sequence_length
        self.scalers = {}
        self.models = {}
        
    def prepare_sequences(self, data: np.ndarray, scaler: MinMaxScaler = None) -> Tuple[np.ndarray, np.ndarray, MinMaxScaler]:
        """Prepare sequences for neural network training"""
        if scaler is None:
            scaler = MinMaxScaler()
            scaled_data = scaler.fit_transform(data.reshape(-1, 1))
        else:
            scaled_data = scaler.transform(data.reshape(-1, 1))
        
        X, y = [], []
        for i in range(self.sequence_length, len(scaled_data)):
            X.append(scaled_data[i-self.sequence_length:i, 0])
            y.append(scaled_data[i, 0])
        
        return np.array(X), np.array(y), scaler
    
    def lstm_model(self, input_shape: Tuple[int, int]) -> Model:
        """Create LSTM model architecture"""
        model = Sequential([
            LSTM(50, return_sequences=True, input_shape=input_shape),
            Dropout(0.2),
            LSTM(50, return_sequences=False),
            Dropout(0.2),
            Dense(25),
            Dense(1)
        ])
        
        model.compile(optimizer=Adam(learning_rate=0.001), loss='mse')
        return model
    
    def gru_model(self, input_shape: Tuple[int, int]) -> Model:
        """Create GRU model architecture"""
        model = Sequential([
            GRU(50, return_sequences=True, input_shape=input_shape),
            Dropout(0.2),
            GRU(50, return_sequences=False),
            Dropout(0.2),
            Dense(25),
            Dense(1)
        ])
        
        model.compile(optimizer=Adam(learning_rate=0.001), loss='mse')
        return model
    
    def transformer_model(self, input_shape: Tuple[int, int]) -> Model:
        """Create Transformer model architecture"""
        inputs = Input(shape=input_shape)
        
        # Multi-head attention
        attention = MultiHeadAttention(num_heads=8, key_dim=64)(inputs, inputs)
        attention = Dropout(0.1)(attention)
        
        # Add & Norm
        attention = LayerNormalization(epsilon=1e-6)(attention + inputs)
        
        # Feed forward
        ffn = Dense(128, activation='relu')(attention)
        ffn = Dropout(0.1)(ffn)
        ffn = Dense(64)(ffn)
        
        # Add & Norm
        ffn = LayerNormalization(epsilon=1e-6)(ffn + attention)
        
        # Global average pooling and output
        pooled = tf.keras.layers.GlobalAveragePooling1D()(ffn)
        outputs = Dense(1)(pooled)
        
        model = Model(inputs, outputs)
        model.compile(optimizer=Adam(learning_rate=0.001), loss='mse')
        
        return model
    
    def train_model(self, model: Model, X_train: np.ndarray, y_train: np.ndarray, 
                   X_val: np.ndarray, y_val: np.ndarray, epochs: int = 100) -> Model:
        """Train neural network model"""
        early_stopping = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
        
        history = model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=32,
            callbacks=[early_stopping],
            verbose=0
        )
        
        return model
    
    def lstm_forecast(self, data: np.ndarray, forecast_hours: int, train_split: float = 0.8) -> Dict:
        """LSTM forecasting model"""
        try:
            X, y, scaler = self.prepare_sequences(data)
            
            # Split data
            split_idx = int(len(X) * train_split)
            X_train, X_val = X[:split_idx], X[split_idx:]
            y_train, y_val = y[:split_idx], y[split_idx:]
            
            # Reshape for LSTM
            X_train = X_train.reshape((X_train.shape[0], X_train.shape[1], 1))
            X_val = X_val.reshape((X_val.shape[0], X_val.shape[1], 1))
            
            # Create and train model
            model = self.lstm_model((X_train.shape[1], X_train.shape[2]))
            trained_model = self.train_model(model, X_train, y_train, X_val, y_val)
            
            # Generate forecast
            forecast = []
            current_sequence = X[-1].reshape(1, self.sequence_length, 1)
            
            for _ in range(forecast_hours):
                next_pred = trained_model.predict(current_sequence, verbose=0)
                forecast.append(next_pred[0, 0])
                
                # Update sequence
                current_sequence = np.append(current_sequence[:, 1:, :], next_pred.reshape(1, 1, 1), axis=1)
            
            # Inverse transform
            forecast = scaler.inverse_transform(np.array(forecast).reshape(-1, 1)).flatten()
            
            return {
                'forecast': forecast,
                'model': trained_model,
                'scaler': scaler
            }
        except Exception as e:
            print(f"LSTM forecasting error: {e}")
            return {'forecast': np.full(forecast_hours, data[-1]), 'error': str(e)}
    
    def gru_forecast(self, data: np.ndarray, forecast_hours: int, train_split: float = 0.8) -> Dict:
        """GRU forecasting model"""
        try:
            X, y, scaler = self.prepare_sequences(data)
            
            # Split data
            split_idx = int(len(X) * train_split)
            X_train, X_val = X[:split_idx], X[split_idx:]
            y_train, y_val = y[:split_idx], y[split_idx:]
            
            # Reshape for GRU
            X_train = X_train.reshape((X_train.shape[0], X_train.shape[1], 1))
            X_val = X_val.reshape((X_val.shape[0], X_val.shape[1], 1))
            
            # Create and train model
            model = self.gru_model((X_train.shape[1], X_train.shape[2]))
            trained_model = self.train_model(model, X_train, y_train, X_val, y_val)
            
            # Generate forecast
            forecast = []
            current_sequence = X[-1].reshape(1, self.sequence_length, 1)
            
            for _ in range(forecast_hours):
                next_pred = trained_model.predict(current_sequence, verbose=0)
                forecast.append(next_pred[0, 0])
                
                # Update sequence
                current_sequence = np.append(current_sequence[:, 1:, :], next_pred.reshape(1, 1, 1), axis=1)
            
            # Inverse transform
            forecast = scaler.inverse_transform(np.array(forecast).reshape(-1, 1)).flatten()
            
            return {
                'forecast': forecast,
                'model': trained_model,
                'scaler': scaler
            }
        except Exception as e:
            print(f"GRU forecasting error: {e}")
            return {'forecast': np.full(forecast_hours, data[-1]), 'error': str(e)}
    
    def transformer_forecast(self, data: np.ndarray, forecast_hours: int, train_split: float = 0.8) -> Dict:
        """Transformer forecasting model"""
        try:
            X, y, scaler = self.prepare_sequences(data)
            
            # Split data
            split_idx = int(len(X) * train_split)
            X_train, X_val = X[:split_idx], X[split_idx:]
            y_train, y_val = y[:split_idx], y[split_idx:]
            
            # Reshape for Transformer
            X_train = X_train.reshape((X_train.shape[0], X_train.shape[1], 1))
            X_val = X_val.reshape((X_val.shape[0], X_val.shape[1], 1))
            
            # Create and train model
            model = self.transformer_model((X_train.shape[1], X_train.shape[2]))
            trained_model = self.train_model(model, X_train, y_train, X_val, y_val, epochs=50)
            
            # Generate forecast
            forecast = []
            current_sequence = X[-1].reshape(1, self.sequence_length, 1)
            
            for _ in range(forecast_hours):
                next_pred = trained_model.predict(current_sequence, verbose=0)
                forecast.append(next_pred[0, 0])
                
                # Update sequence
                current_sequence = np.append(current_sequence[:, 1:, :], next_pred.reshape(1, 1, 1), axis=1)
            
            # Inverse transform
            forecast = scaler.inverse_transform(np.array(forecast).reshape(-1, 1)).flatten()
            
            return {
                'forecast': forecast,
                'model': trained_model,
                'scaler': scaler
            }
        except Exception as e:
            print(f"Transformer forecasting error: {e}")
            return {'forecast': np.full(forecast_hours, data[-1]), 'error': str(e)}
    
    def calculate_metrics(self, actual: np.ndarray, predicted: np.ndarray) -> Dict[str, float]:
        """Calculate performance metrics"""
        try:
            # Remove any NaN values
            mask = ~(np.isnan(actual) | np.isnan(predicted))
            actual_clean = actual[mask]
            predicted_clean = predicted[mask]
            
            if len(actual_clean) == 0:
                return {'rmse': np.nan, 'mae': np.nan, 'mape': np.nan}
            
            rmse = np.sqrt(mean_squared_error(actual_clean, predicted_clean))
            mae = mean_absolute_error(actual_clean, predicted_clean)
            
            # MAPE calculation with handling for zero values
            mape = np.mean(np.abs((actual_clean - predicted_clean) / (actual_clean + 1e-8))) * 100
            
            return {
                'rmse': rmse,
                'mae': mae,
                'mape': mape
            }
        except Exception as e:
            print(f"Metrics calculation error: {e}")
            return {'rmse': np.nan, 'mae': np.nan, 'mape': np.nan}
    
    def forecast_all(self, data: np.ndarray, forecast_hours: int) -> Dict:
        """Run all neural network forecasting models"""
        results = {}
        
        # LSTM
        lstm_result = self.lstm_forecast(data, forecast_hours)
        results['lstm'] = lstm_result
        
        # GRU
        gru_result = self.gru_forecast(data, forecast_hours)
        results['gru'] = gru_result
        
        # Transformer
        transformer_result = self.transformer_forecast(data, forecast_hours)
        results['transformer'] = transformer_result
        
        return results
