"""
Neural network forecasting models: LSTM, GRU, Transformer.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
import tensorflow as tf
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import LSTM, GRU, Dense, Dropout, Input, MultiHeadAttention, LayerNormalization
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from sklearn.preprocessing import MinMaxScaler
import warnings
warnings.filterwarnings('ignore')

from .base import BaseForecaster, PerformanceMetrics, DataPreprocessor


class LSTMForecaster(BaseForecaster):
    """LSTM (Long Short-Term Memory) neural network forecasting model."""
    
    def __init__(self, sequence_length: int = 60, hidden_units: int = 50, 
                 dropout_rate: float = 0.2, learning_rate: float = 0.001):
        super().__init__("LSTM")
        self.sequence_length = sequence_length
        self.hidden_units = hidden_units
        self.dropout_rate = dropout_rate
        self.learning_rate = learning_rate
        self.model = None
        self.scaler = MinMaxScaler()
        self.feature_scaler = MinMaxScaler()
        self.feature_columns = []
        
    def _build_model(self, n_features: int) -> Sequential:
        """Build LSTM model architecture."""
        model = Sequential([
            LSTM(self.hidden_units, return_sequences=True, input_shape=(self.sequence_length, n_features)),
            Dropout(self.dropout_rate),
            LSTM(self.hidden_units, return_sequences=False),
            Dropout(self.dropout_rate),
            Dense(25),
            Dense(1)
        ])
        
        model.compile(
            optimizer=Adam(learning_rate=self.learning_rate),
            loss='mse',
            metrics=['mae']
        )
        
        return model
    
    def fit(self, data: pd.DataFrame, target_column: str = 'close_price') -> 'LSTMForecaster':
        """Fit LSTM model to the data."""
        if target_column not in data.columns:
            raise ValueError(f"Target column '{target_column}' not found in data")
        
        # Prepare features
        df, feature_columns = DataPreprocessor.prepare_features(data, target_column)
        self.feature_columns = feature_columns
        
        if len(feature_columns) == 0:
            raise ValueError("No features available for training")
        
        # Scale features and target
        feature_data = df[feature_columns].values
        target_data = df[target_column].values.reshape(-1, 1)
        
        feature_data_scaled = self.feature_scaler.fit_transform(feature_data)
        target_data_scaled = self.scaler.fit_transform(target_data)
        
        # Create sequences
        X, y = DataPreprocessor.create_sequences(
            pd.DataFrame(feature_data_scaled, columns=feature_columns),
            feature_columns,
            target_column,
            self.sequence_length
        )
        
        # Reshape y to match X
        y = y.reshape(-1, 1)
        
        if len(X) == 0:
            raise ValueError("Not enough data to create sequences")
        
        # Build and train model
        self.model = self._build_model(len(feature_columns))
        
        # Callbacks
        callbacks = [
            EarlyStopping(patience=10, restore_best_weights=True),
            ReduceLROnPlateau(factor=0.5, patience=5)
        ]
        
        # Train model
        history = self.model.fit(
            X, y,
            epochs=100,
            batch_size=32,
            validation_split=0.2,
            callbacks=callbacks,
            verbose=0
        )
        
        self.is_fitted = True
        return self
    
    def predict(self, horizon: int, confidence_level: float = 0.95) -> Dict[str, Any]:
        """Generate LSTM predictions."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before making predictions")
        
        # Use the last sequence_length points for prediction
        last_sequence = self.feature_scaler.transform(
            self.last_features[-self.sequence_length:]
        ).reshape(1, self.sequence_length, len(self.feature_columns))
        
        predictions = []
        
        # Generate predictions step by step
        current_sequence = last_sequence.copy()
        
        for _ in range(horizon):
            pred = self.model.predict(current_sequence, verbose=0)
            predictions.append(pred[0, 0])
            
            # Update sequence for next prediction (simplified approach)
            # In practice, you might want to update with actual future features
            new_features = current_sequence[0, -1, :].copy()
            new_features[0] = pred[0, 0]  # Update close price
            
            current_sequence = np.roll(current_sequence, -1, axis=1)
            current_sequence[0, -1, :] = new_features
        
        # Inverse transform predictions
        predictions = self.scaler.inverse_transform(np.array(predictions).reshape(-1, 1)).flatten()
        
        # Simple confidence intervals based on training error
        training_error = np.std(self.training_errors) if hasattr(self, 'training_errors') else 0.1
        z_score = 1.96 if confidence_level == 0.95 else 2.576
        
        return {
            'predictions': predictions,
            'confidence_intervals': {
                'lower': predictions - z_score * training_error,
                'upper': predictions + z_score * training_error
            }
        }
    
    def evaluate(self, test_data: pd.DataFrame, target_column: str = 'close_price') -> Dict[str, float]:
        """Evaluate LSTM model performance."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before evaluation")
        
        # Prepare test data
        df, _ = DataPreprocessor.prepare_features(test_data, target_column)
        
        if len(df) < self.sequence_length:
            return {'rmse': np.nan, 'mae': np.nan, 'mape': np.nan}
        
        # Scale test data
        feature_data = df[self.feature_columns].values
        target_data = df[target_column].values.reshape(-1, 1)
        
        feature_data_scaled = self.feature_scaler.transform(feature_data)
        target_data_scaled = self.scaler.transform(target_data)
        
        # Create test sequences
        X_test, y_test = DataPreprocessor.create_sequences(
            pd.DataFrame(feature_data_scaled, columns=self.feature_columns),
            self.feature_columns,
            target_column,
            self.sequence_length
        )
        
        if len(X_test) == 0:
            return {'rmse': np.nan, 'mae': np.nan, 'mape': np.nan}
        
        # Make predictions
        y_pred_scaled = self.model.predict(X_test, verbose=0)
        y_pred = self.scaler.inverse_transform(y_pred_scaled).flatten()
        
        return PerformanceMetrics.calculate_metrics(y_test, y_pred)


class GRUForecaster(BaseForecaster):
    """GRU (Gated Recurrent Unit) neural network forecasting model."""
    
    def __init__(self, sequence_length: int = 60, hidden_units: int = 50, 
                 dropout_rate: float = 0.2, learning_rate: float = 0.001):
        super().__init__("GRU")
        self.sequence_length = sequence_length
        self.hidden_units = hidden_units
        self.dropout_rate = dropout_rate
        self.learning_rate = learning_rate
        self.model = None
        self.scaler = MinMaxScaler()
        self.feature_scaler = MinMaxScaler()
        self.feature_columns = []
        
    def _build_model(self, n_features: int) -> Sequential:
        """Build GRU model architecture."""
        model = Sequential([
            GRU(self.hidden_units, return_sequences=True, input_shape=(self.sequence_length, n_features)),
            Dropout(self.dropout_rate),
            GRU(self.hidden_units, return_sequences=False),
            Dropout(self.dropout_rate),
            Dense(25),
            Dense(1)
        ])
        
        model.compile(
            optimizer=Adam(learning_rate=self.learning_rate),
            loss='mse',
            metrics=['mae']
        )
        
        return model
    
    def fit(self, data: pd.DataFrame, target_column: str = 'close_price') -> 'GRUForecaster':
        """Fit GRU model to the data."""
        if target_column not in data.columns:
            raise ValueError(f"Target column '{target_column}' not found in data")
        
        # Prepare features
        df, feature_columns = DataPreprocessor.prepare_features(data, target_column)
        self.feature_columns = feature_columns
        
        if len(feature_columns) == 0:
            raise ValueError("No features available for training")
        
        # Scale features and target
        feature_data = df[feature_columns].values
        target_data = df[target_column].values.reshape(-1, 1)
        
        feature_data_scaled = self.feature_scaler.fit_transform(feature_data)
        target_data_scaled = self.scaler.fit_transform(target_data)
        
        # Create sequences
        X, y = DataPreprocessor.create_sequences(
            pd.DataFrame(feature_data_scaled, columns=feature_columns),
            feature_columns,
            target_column,
            self.sequence_length
        )
        
        y = y.reshape(-1, 1)
        
        if len(X) == 0:
            raise ValueError("Not enough data to create sequences")
        
        # Build and train model
        self.model = self._build_model(len(feature_columns))
        
        # Callbacks
        callbacks = [
            EarlyStopping(patience=10, restore_best_weights=True),
            ReduceLROnPlateau(factor=0.5, patience=5)
        ]
        
        # Train model
        history = self.model.fit(
            X, y,
            epochs=100,
            batch_size=32,
            validation_split=0.2,
            callbacks=callbacks,
            verbose=0
        )
        
        self.is_fitted = True
        return self
    
    def predict(self, horizon: int, confidence_level: float = 0.95) -> Dict[str, Any]:
        """Generate GRU predictions."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before making predictions")
        
        # Similar to LSTM prediction logic
        last_sequence = self.feature_scaler.transform(
            self.last_features[-self.sequence_length:]
        ).reshape(1, self.sequence_length, len(self.feature_columns))
        
        predictions = []
        current_sequence = last_sequence.copy()
        
        for _ in range(horizon):
            pred = self.model.predict(current_sequence, verbose=0)
            predictions.append(pred[0, 0])
            
            # Update sequence
            new_features = current_sequence[0, -1, :].copy()
            new_features[0] = pred[0, 0]
            
            current_sequence = np.roll(current_sequence, -1, axis=1)
            current_sequence[0, -1, :] = new_features
        
        # Inverse transform predictions
        predictions = self.scaler.inverse_transform(np.array(predictions).reshape(-1, 1)).flatten()
        
        # Confidence intervals
        training_error = np.std(self.training_errors) if hasattr(self, 'training_errors') else 0.1
        z_score = 1.96 if confidence_level == 0.95 else 2.576
        
        return {
            'predictions': predictions,
            'confidence_intervals': {
                'lower': predictions - z_score * training_error,
                'upper': predictions + z_score * training_error
            }
        }
    
    def evaluate(self, test_data: pd.DataFrame, target_column: str = 'close_price') -> Dict[str, float]:
        """Evaluate GRU model performance."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before evaluation")
        
        # Similar to LSTM evaluation logic
        df, _ = DataPreprocessor.prepare_features(test_data, target_column)
        
        if len(df) < self.sequence_length:
            return {'rmse': np.nan, 'mae': np.nan, 'mape': np.nan}
        
        feature_data = df[self.feature_columns].values
        target_data = df[target_column].values.reshape(-1, 1)
        
        feature_data_scaled = self.feature_scaler.transform(feature_data)
        target_data_scaled = self.scaler.transform(target_data)
        
        X_test, y_test = DataPreprocessor.create_sequences(
            pd.DataFrame(feature_data_scaled, columns=self.feature_columns),
            self.feature_columns,
            target_column,
            self.sequence_length
        )
        
        if len(X_test) == 0:
            return {'rmse': np.nan, 'mae': np.nan, 'mape': np.nan}
        
        y_pred_scaled = self.model.predict(X_test, verbose=0)
        y_pred = self.scaler.inverse_transform(y_pred_scaled).flatten()
        
        return PerformanceMetrics.calculate_metrics(y_test, y_pred)


class TransformerForecaster(BaseForecaster):
    """Transformer-based forecasting model."""
    
    def __init__(self, sequence_length: int = 60, d_model: int = 64, num_heads: int = 4,
                 num_layers: int = 2, dropout_rate: float = 0.1, learning_rate: float = 0.001):
        super().__init__("Transformer")
        self.sequence_length = sequence_length
        self.d_model = d_model
        self.num_heads = num_heads
        self.num_layers = num_layers
        self.dropout_rate = dropout_rate
        self.learning_rate = learning_rate
        self.model = None
        self.scaler = MinMaxScaler()
        self.feature_scaler = MinMaxScaler()
        self.feature_columns = []
        
    def _build_model(self, n_features: int) -> Model:
        """Build Transformer model architecture."""
        inputs = Input(shape=(self.sequence_length, n_features))
        
        # Linear projection to d_model
        x = Dense(self.d_model)(inputs)
        
        # Positional encoding (simplified)
        positions = tf.range(start=0, limit=self.sequence_length, dtype=tf.float32)
        positions = tf.expand_dims(positions, 1)
        div_term = tf.exp(tf.range(0, self.d_model, 2, dtype=tf.float32) * 
                         -(tf.math.log(10000.0) / self.d_model))
        
        pos_encoding = tf.zeros((self.sequence_length, self.d_model))
        pos_encoding = tf.tensor_scatter_nd_update(
            pos_encoding,
            tf.expand_dims(tf.range(self.sequence_length), 1),
            tf.sin(positions * div_term)
        )
        
        x = x + pos_encoding
        
        # Transformer layers
        for _ in range(self.num_layers):
            # Multi-head attention
            attn_output = MultiHeadAttention(
                num_heads=self.num_heads,
                key_dim=self.d_model // self.num_heads
            )(x, x)
            attn_output = Dropout(self.dropout_rate)(attn_output)
            x = LayerNormalization(epsilon=1e-6)(x + attn_output)
            
            # Feed forward
            ffn = Dense(self.d_model * 4, activation='relu')(x)
            ffn = Dropout(self.dropout_rate)(ffn)
            ffn = Dense(self.d_model)(ffn)
            x = LayerNormalization(epsilon=1e-6)(x + ffn)
        
        # Global average pooling and output
        x = tf.reduce_mean(x, axis=1)
        x = Dropout(self.dropout_rate)(x)
        outputs = Dense(1)(x)
        
        model = Model(inputs, outputs)
        model.compile(
            optimizer=Adam(learning_rate=self.learning_rate),
            loss='mse',
            metrics=['mae']
        )
        
        return model
    
    def fit(self, data: pd.DataFrame, target_column: str = 'close_price') -> 'TransformerForecaster':
        """Fit Transformer model to the data."""
        if target_column not in data.columns:
            raise ValueError(f"Target column '{target_column}' not found in data")
        
        # Prepare features
        df, feature_columns = DataPreprocessor.prepare_features(data, target_column)
        self.feature_columns = feature_columns
        
        if len(feature_columns) == 0:
            raise ValueError("No features available for training")
        
        # Scale features and target
        feature_data = df[feature_columns].values
        target_data = df[target_column].values.reshape(-1, 1)
        
        feature_data_scaled = self.feature_scaler.fit_transform(feature_data)
        target_data_scaled = self.scaler.fit_transform(target_data)
        
        # Create sequences
        X, y = DataPreprocessor.create_sequences(
            pd.DataFrame(feature_data_scaled, columns=feature_columns),
            feature_columns,
            target_column,
            self.sequence_length
        )
        
        y = y.reshape(-1, 1)
        
        if len(X) == 0:
            raise ValueError("Not enough data to create sequences")
        
        # Build and train model
        self.model = self._build_model(len(feature_columns))
        
        # Callbacks
        callbacks = [
            EarlyStopping(patience=15, restore_best_weights=True),
            ReduceLROnPlateau(factor=0.5, patience=5)
        ]
        
        # Train model
        history = self.model.fit(
            X, y,
            epochs=100,
            batch_size=32,
            validation_split=0.2,
            callbacks=callbacks,
            verbose=0
        )
        
        self.is_fitted = True
        return self
    
    def predict(self, horizon: int, confidence_level: float = 0.95) -> Dict[str, Any]:
        """Generate Transformer predictions."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before making predictions")
        
        # Similar prediction logic to LSTM/GRU
        last_sequence = self.feature_scaler.transform(
            self.last_features[-self.sequence_length:]
        ).reshape(1, self.sequence_length, len(self.feature_columns))
        
        predictions = []
        current_sequence = last_sequence.copy()
        
        for _ in range(horizon):
            pred = self.model.predict(current_sequence, verbose=0)
            predictions.append(pred[0, 0])
            
            # Update sequence
            new_features = current_sequence[0, -1, :].copy()
            new_features[0] = pred[0, 0]
            
            current_sequence = np.roll(current_sequence, -1, axis=1)
            current_sequence[0, -1, :] = new_features
        
        # Inverse transform predictions
        predictions = self.scaler.inverse_transform(np.array(predictions).reshape(-1, 1)).flatten()
        
        # Confidence intervals
        training_error = np.std(self.training_errors) if hasattr(self, 'training_errors') else 0.1
        z_score = 1.96 if confidence_level == 0.95 else 2.576
        
        return {
            'predictions': predictions,
            'confidence_intervals': {
                'lower': predictions - z_score * training_error,
                'upper': predictions + z_score * training_error
            }
        }
    
    def evaluate(self, test_data: pd.DataFrame, target_column: str = 'close_price') -> Dict[str, float]:
        """Evaluate Transformer model performance."""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before evaluation")
        
        # Similar evaluation logic
        df, _ = DataPreprocessor.prepare_features(test_data, target_column)
        
        if len(df) < self.sequence_length:
            return {'rmse': np.nan, 'mae': np.nan, 'mape': np.nan}
        
        feature_data = df[self.feature_columns].values
        target_data = df[target_column].values.reshape(-1, 1)
        
        feature_data_scaled = self.feature_scaler.transform(feature_data)
        target_data_scaled = self.scaler.transform(target_data)
        
        X_test, y_test = DataPreprocessor.create_sequences(
            pd.DataFrame(feature_data_scaled, columns=self.feature_columns),
            self.feature_columns,
            target_column,
            self.sequence_length
        )
        
        if len(X_test) == 0:
            return {'rmse': np.nan, 'mae': np.nan, 'mape': np.nan}
        
        y_pred_scaled = self.model.predict(X_test, verbose=0)
        y_pred = self.scaler.inverse_transform(y_pred_scaled).flatten()
        
        return PerformanceMetrics.calculate_metrics(y_test, y_pred)
