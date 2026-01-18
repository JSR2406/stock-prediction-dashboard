"""
Ensemble Model for Stock Price Prediction
Combines LSTM, GRU, Random Forest, and XGBoost for improved accuracy.
"""

import os
import json
import pickle
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

# ML imports with fallback
import sys
custom_tf_path = r"C:\Users\Janmejay Singh\tf"
if os.path.exists(custom_tf_path) and custom_tf_path not in sys.path:
    sys.path.append(custom_tf_path)

try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential, load_model
    from tensorflow.keras.layers import LSTM, GRU, Dense, Dropout, BatchNormalization
    from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
    from tensorflow.keras.optimizers import Adam
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    print("TensorFlow not available - using mock predictions")

try:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.preprocessing import MinMaxScaler
    from sklearn.model_selection import TimeSeriesSplit
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False


@dataclass
class PredictionResult:
    """Result of an ensemble prediction."""
    symbol: str
    current_price: float
    predicted_price: float
    change_percent: float
    confidence: float
    prediction_date: str
    model_contributions: Dict[str, float]
    upper_bound: float
    lower_bound: float
    quality: str  # "high", "medium", "low"


@dataclass
class ModelMetrics:
    """Training metrics for a model."""
    model_type: str
    rmse: float
    mae: float
    mape: float
    r_squared: float
    training_samples: int
    training_date: str


class EnsemblePredictor:
    """
    Ensemble predictor combining multiple ML models.
    
    Model Weights:
    - LSTM: 40%
    - GRU: 30%
    - XGBoost: 20%
    - Random Forest: 10%
    
    Usage:
        predictor = EnsemblePredictor()
        result = predictor.ensemble_predict("RELIANCE", data)
    """
    
    WEIGHTS = {
        'lstm': 0.40,
        'gru': 0.30,
        'xgboost': 0.20,
        'random_forest': 0.10
    }
    
    def __init__(self, models_dir: str = "saved_models"):
        self.models_dir = models_dir
        os.makedirs(models_dir, exist_ok=True)
        
        self.models: Dict[str, Dict[str, Any]] = {}
        self.scalers: Dict[str, MinMaxScaler] = {}
        
    def _get_model_path(self, symbol: str, model_type: str) -> str:
        """Get path for model file."""
        return os.path.join(self.models_dir, f"{symbol}_{model_type}")
    
    def _prepare_data(
        self, 
        data: pd.DataFrame, 
        sequence_length: int = 60,
        target_col: str = 'Close'
    ) -> Tuple[np.ndarray, np.ndarray, MinMaxScaler]:
        """
        Prepare data for training.
        
        Args:
            data: DataFrame with OHLCV data
            sequence_length: Number of timesteps for sequences
            target_col: Target column name
            
        Returns:
            X, y arrays and fitted scaler
        """
        # Select features
        features = ['Open', 'High', 'Low', 'Close', 'Volume']
        df = data[features].copy()
        
        # Handle missing values
        df = df.ffill().bfill()
        
        # Scale data
        scaler = MinMaxScaler()
        scaled_data = scaler.fit_transform(df)
        
        # Create sequences
        X, y = [], []
        target_idx = features.index(target_col)
        
        for i in range(sequence_length, len(scaled_data)):
            X.append(scaled_data[i-sequence_length:i])
            y.append(scaled_data[i, target_idx])
        
        return np.array(X), np.array(y), scaler
    
    def _prepare_ml_data(
        self, 
        data: pd.DataFrame, 
        lookback: int = 20
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare data for traditional ML models (RF, XGBoost).
        Creates lag features.
        """
        df = data.copy()
        
        # Create lag features
        for i in range(1, lookback + 1):
            df[f'close_lag_{i}'] = df['Close'].shift(i)
            df[f'volume_lag_{i}'] = df['Volume'].shift(i)
        
        # Moving averages
        df['sma_5'] = df['Close'].rolling(5).mean()
        df['sma_10'] = df['Close'].rolling(10).mean()
        df['sma_20'] = df['Close'].rolling(20).mean()
        
        # Returns
        df['returns_1d'] = df['Close'].pct_change()
        df['returns_5d'] = df['Close'].pct_change(5)
        
        # Volatility
        df['volatility'] = df['returns_1d'].rolling(10).std()
        
        # Drop NaN rows
        df = df.dropna()
        
        # Target: next day close
        y = df['Close'].shift(-1).dropna().values
        X = df.iloc[:-1].drop(columns=['Open', 'High', 'Low', 'Close', 'Volume']).values
        
        return X, y
    
    def train_lstm_model(
        self, 
        symbol: str, 
        data: pd.DataFrame,
        sequence_length: int = 60,
        epochs: int = 100,
        batch_size: int = 32
    ) -> ModelMetrics:
        """
        Train LSTM model for a symbol.
        
        Args:
            symbol: Stock symbol
            data: Historical OHLCV data
            sequence_length: Sequence length for LSTM
            epochs: Training epochs
            batch_size: Batch size
            
        Returns:
            ModelMetrics with training results
        """
        if not TF_AVAILABLE:
            return ModelMetrics("lstm", 0, 0, 0, 0, 0, datetime.now().isoformat())
        
        X, y, scaler = self._prepare_data(data, sequence_length)
        
        # Train/test split (80/20)
        split = int(len(X) * 0.8)
        X_train, X_test = X[:split], X[split:]
        y_train, y_test = y[:split], y[split:]
        
        # Build model
        model = Sequential([
            LSTM(128, return_sequences=True, input_shape=(X.shape[1], X.shape[2])),
            Dropout(0.3),
            BatchNormalization(),
            LSTM(64, return_sequences=True),
            Dropout(0.3),
            BatchNormalization(),
            LSTM(32, return_sequences=False),
            Dropout(0.2),
            Dense(16, activation='relu'),
            Dense(1)
        ])
        
        model.compile(optimizer=Adam(learning_rate=0.001), loss='huber')
        
        callbacks = [
            EarlyStopping(patience=15, restore_best_weights=True, monitor='val_loss'),
            ReduceLROnPlateau(factor=0.5, patience=5, min_lr=1e-6)
        ]
        
        # Train
        history = model.fit(
            X_train, y_train,
            validation_data=(X_test, y_test),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=0
        )
        
        # Evaluate
        predictions = model.predict(X_test, verbose=0).flatten()
        
        rmse = np.sqrt(np.mean((predictions - y_test) ** 2))
        mae = np.mean(np.abs(predictions - y_test))
        mape = np.mean(np.abs((y_test - predictions) / y_test)) * 100
        ss_res = np.sum((y_test - predictions) ** 2)
        ss_tot = np.sum((y_test - np.mean(y_test)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        # Save model
        model_path = self._get_model_path(symbol, "lstm")
        model.save(f"{model_path}.keras")
        
        # Save scaler
        with open(f"{model_path}_scaler.pkl", 'wb') as f:
            pickle.dump(scaler, f)
        
        self.models.setdefault(symbol, {})['lstm'] = model
        self.scalers[f"{symbol}_lstm"] = scaler
        
        return ModelMetrics(
            model_type="lstm",
            rmse=round(rmse, 4),
            mae=round(mae, 4),
            mape=round(mape, 2),
            r_squared=round(r_squared, 4),
            training_samples=len(X_train),
            training_date=datetime.now().isoformat()
        )
    
    def train_gru_model(
        self, 
        symbol: str, 
        data: pd.DataFrame,
        sequence_length: int = 60,
        epochs: int = 100,
        batch_size: int = 32
    ) -> ModelMetrics:
        """Train GRU model - faster alternative to LSTM."""
        if not TF_AVAILABLE:
            return ModelMetrics("gru", 0, 0, 0, 0, 0, datetime.now().isoformat())
        
        X, y, scaler = self._prepare_data(data, sequence_length)
        
        split = int(len(X) * 0.8)
        X_train, X_test = X[:split], X[split:]
        y_train, y_test = y[:split], y[split:]
        
        # Build GRU model
        model = Sequential([
            GRU(100, return_sequences=True, input_shape=(X.shape[1], X.shape[2])),
            Dropout(0.3),
            GRU(50, return_sequences=False),
            Dropout(0.2),
            Dense(25, activation='relu'),
            Dense(1)
        ])
        
        model.compile(optimizer=Adam(learning_rate=0.001), loss='huber')
        
        callbacks = [
            EarlyStopping(patience=15, restore_best_weights=True),
            ReduceLROnPlateau(factor=0.5, patience=5, min_lr=1e-6)
        ]
        
        model.fit(
            X_train, y_train,
            validation_data=(X_test, y_test),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=0
        )
        
        predictions = model.predict(X_test, verbose=0).flatten()
        
        rmse = np.sqrt(np.mean((predictions - y_test) ** 2))
        mae = np.mean(np.abs(predictions - y_test))
        mape = np.mean(np.abs((y_test - predictions) / y_test)) * 100
        ss_res = np.sum((y_test - predictions) ** 2)
        ss_tot = np.sum((y_test - np.mean(y_test)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        model_path = self._get_model_path(symbol, "gru")
        model.save(f"{model_path}.keras")
        
        with open(f"{model_path}_scaler.pkl", 'wb') as f:
            pickle.dump(scaler, f)
        
        self.models.setdefault(symbol, {})['gru'] = model
        self.scalers[f"{symbol}_gru"] = scaler
        
        return ModelMetrics(
            model_type="gru",
            rmse=round(rmse, 4),
            mae=round(mae, 4),
            mape=round(mape, 2),
            r_squared=round(r_squared, 4),
            training_samples=len(X_train),
            training_date=datetime.now().isoformat()
        )
    
    def train_random_forest(
        self, 
        symbol: str, 
        data: pd.DataFrame,
        n_estimators: int = 100
    ) -> ModelMetrics:
        """Train Random Forest model for comparison."""
        if not SKLEARN_AVAILABLE:
            return ModelMetrics("random_forest", 0, 0, 0, 0, 0, datetime.now().isoformat())
        
        X, y = self._prepare_ml_data(data)
        
        split = int(len(X) * 0.8)
        X_train, X_test = X[:split], X[split:]
        y_train, y_test = y[:split], y[split:]
        
        model = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
        
        model.fit(X_train, y_train)
        predictions = model.predict(X_test)
        
        rmse = np.sqrt(np.mean((predictions - y_test) ** 2))
        mae = np.mean(np.abs(predictions - y_test))
        mape = np.mean(np.abs((y_test - predictions) / y_test)) * 100
        r_squared = model.score(X_test, y_test)
        
        model_path = self._get_model_path(symbol, "rf")
        with open(f"{model_path}.pkl", 'wb') as f:
            pickle.dump(model, f)
        
        self.models.setdefault(symbol, {})['random_forest'] = model
        
        return ModelMetrics(
            model_type="random_forest",
            rmse=round(rmse, 4),
            mae=round(mae, 4),
            mape=round(mape, 2),
            r_squared=round(r_squared, 4),
            training_samples=len(X_train),
            training_date=datetime.now().isoformat()
        )
    
    def train_xgboost(
        self, 
        symbol: str, 
        data: pd.DataFrame
    ) -> ModelMetrics:
        """Train XGBoost model for non-linear patterns."""
        if not XGBOOST_AVAILABLE:
            return ModelMetrics("xgboost", 0, 0, 0, 0, 0, datetime.now().isoformat())
        
        X, y = self._prepare_ml_data(data)
        
        split = int(len(X) * 0.8)
        X_train, X_test = X[:split], X[split:]
        y_train, y_test = y[:split], y[split:]
        
        model = xgb.XGBRegressor(
            n_estimators=200,
            max_depth=8,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            verbosity=0
        )
        
        model.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            verbose=False
        )
        
        predictions = model.predict(X_test)
        
        rmse = np.sqrt(np.mean((predictions - y_test) ** 2))
        mae = np.mean(np.abs(predictions - y_test))
        mape = np.mean(np.abs((y_test - predictions) / y_test)) * 100
        r_squared = model.score(X_test, y_test)
        
        model_path = self._get_model_path(symbol, "xgb")
        model.save_model(f"{model_path}.json")
        
        self.models.setdefault(symbol, {})['xgboost'] = model
        
        return ModelMetrics(
            model_type="xgboost",
            rmse=round(rmse, 4),
            mae=round(mae, 4),
            mape=round(mape, 2),
            r_squared=round(r_squared, 4),
            training_samples=len(X_train),
            training_date=datetime.now().isoformat()
        )
    
    def ensemble_predict(
        self, 
        symbol: str, 
        data: pd.DataFrame,
        sequence_length: int = 60
    ) -> PredictionResult:
        """
        Generate ensemble prediction using all available models.
        
        Args:
            symbol: Stock symbol
            data: Recent OHLCV data
            sequence_length: Sequence length for RNN models
            
        Returns:
            PredictionResult with weighted ensemble prediction
        """
        predictions = {}
        current_price = float(data['Close'].iloc[-1])
        
        # Get predictions from each model
        if symbol in self.models:
            models = self.models[symbol]
            
            # LSTM prediction
            if 'lstm' in models and TF_AVAILABLE:
                try:
                    scaler = self.scalers.get(f"{symbol}_lstm")
                    if scaler:
                        X, _, _ = self._prepare_data(data.tail(sequence_length + 1), sequence_length)
                        if len(X) > 0:
                            pred = models['lstm'].predict(X[-1:], verbose=0)[0][0]
                            predictions['lstm'] = float(pred)
                except Exception as e:
                    print(f"LSTM prediction error: {e}")
            
            # GRU prediction
            if 'gru' in models and TF_AVAILABLE:
                try:
                    scaler = self.scalers.get(f"{symbol}_gru")
                    if scaler:
                        X, _, _ = self._prepare_data(data.tail(sequence_length + 1), sequence_length)
                        if len(X) > 0:
                            pred = models['gru'].predict(X[-1:], verbose=0)[0][0]
                            predictions['gru'] = float(pred)
                except Exception as e:
                    print(f"GRU prediction error: {e}")
            
            # Random Forest prediction
            if 'random_forest' in models:
                try:
                    X, _ = self._prepare_ml_data(data.tail(30))
                    if len(X) > 0:
                        pred = models['random_forest'].predict(X[-1:])[0]
                        predictions['random_forest'] = float(pred)
                except Exception as e:
                    print(f"RF prediction error: {e}")
            
            # XGBoost prediction
            if 'xgboost' in models:
                try:
                    X, _ = self._prepare_ml_data(data.tail(30))
                    if len(X) > 0:
                        pred = models['xgboost'].predict(X[-1:])[0]
                        predictions['xgboost'] = float(pred)
                except Exception as e:
                    print(f"XGBoost prediction error: {e}")
        
        # If no trained models, return demo prediction
        if not predictions:
            change = np.random.uniform(-2, 3)
            predicted_price = current_price * (1 + change / 100)
            return PredictionResult(
                symbol=symbol,
                current_price=round(current_price, 2),
                predicted_price=round(predicted_price, 2),
                change_percent=round(change, 2),
                confidence=65.0,
                prediction_date=datetime.now().isoformat(),
                model_contributions={"demo": 100.0},
                upper_bound=round(predicted_price * 1.02, 2),
                lower_bound=round(predicted_price * 0.98, 2),
                quality="medium"
            )
        
        # Calculate weighted ensemble prediction
        weighted_sum = 0
        total_weight = 0
        contributions = {}
        
        for model_name, pred in predictions.items():
            weight = self.WEIGHTS.get(model_name, 0.1)
            weighted_sum += pred * weight
            total_weight += weight
            contributions[model_name] = round(weight * 100 / total_weight, 1)
        
        if total_weight > 0:
            ensemble_pred = weighted_sum / total_weight
        else:
            ensemble_pred = current_price
        
        # Calculate confidence based on model agreement
        if len(predictions) > 1:
            pred_values = list(predictions.values())
            std_dev = np.std(pred_values)
            mean_pred = np.mean(pred_values)
            cv = std_dev / mean_pred if mean_pred != 0 else 0
            # Lower CV = higher confidence
            confidence = max(50, min(95, 100 - (cv * 200)))
        else:
            confidence = 60.0
        
        change_percent = ((ensemble_pred - current_price) / current_price) * 100
        
        # Determine quality
        if confidence >= 80 and len(predictions) >= 3:
            quality = "high"
        elif confidence >= 65 and len(predictions) >= 2:
            quality = "medium"
        else:
            quality = "low"
        
        # Calculate bounds (95% confidence interval approximation)
        volatility = data['Close'].pct_change().std() * 100
        margin = max(1.5, volatility * 2)
        upper_bound = ensemble_pred * (1 + margin / 100)
        lower_bound = ensemble_pred * (1 - margin / 100)
        
        return PredictionResult(
            symbol=symbol,
            current_price=round(current_price, 2),
            predicted_price=round(ensemble_pred, 2),
            change_percent=round(change_percent, 2),
            confidence=round(confidence, 1),
            prediction_date=datetime.now().isoformat(),
            model_contributions=contributions,
            upper_bound=round(upper_bound, 2),
            lower_bound=round(lower_bound, 2),
            quality=quality
        )
    
    def get_feature_importance(self, symbol: str) -> Dict[str, List[Tuple[str, float]]]:
        """
        Get feature importance from tree-based models.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dict with feature importance for each model
        """
        importance = {}
        
        if symbol in self.models:
            if 'random_forest' in self.models[symbol]:
                rf = self.models[symbol]['random_forest']
                fi = rf.feature_importances_
                importance['random_forest'] = sorted(
                    enumerate(fi), key=lambda x: x[1], reverse=True
                )[:10]
            
            if 'xgboost' in self.models[symbol]:
                xgb_model = self.models[symbol]['xgboost']
                fi = xgb_model.feature_importances_
                importance['xgboost'] = sorted(
                    enumerate(fi), key=lambda x: x[1], reverse=True
                )[:10]
        
        return importance
    
    def calculate_confidence_score(
        self, 
        predictions: Dict[str, float], 
        volatility: float
    ) -> float:
        """
        Calculate confidence score based on model agreement and volatility.
        
        Args:
            predictions: Dict of model predictions
            volatility: Recent price volatility
            
        Returns:
            Confidence score (0-100)
        """
        if not predictions:
            return 50.0
        
        pred_values = list(predictions.values())
        
        # Model agreement factor
        if len(pred_values) > 1:
            std_dev = np.std(pred_values)
            mean_val = np.mean(pred_values)
            agreement = 1 - (std_dev / mean_val) if mean_val != 0 else 0
        else:
            agreement = 0.5
        
        # Volatility factor (lower volatility = higher confidence)
        vol_factor = max(0, 1 - (volatility / 5))  # Normalize around 5%
        
        # Number of models factor
        model_factor = min(1, len(predictions) / 4)
        
        # Weighted combination
        confidence = (
            agreement * 0.5 +
            vol_factor * 0.3 +
            model_factor * 0.2
        ) * 100
        
        return min(95, max(40, confidence))


# Convenience function
def create_ensemble_predictor(models_dir: str = "saved_models") -> EnsemblePredictor:
    """Create and return an EnsemblePredictor instance."""
    return EnsemblePredictor(models_dir)
