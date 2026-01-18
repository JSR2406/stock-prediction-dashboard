"""
Stock Data Preprocessing Module
Handles feature engineering, normalization, and sequence creation for LSTM models.
"""

import os
import pickle
from datetime import datetime
from typing import Tuple, List, Optional, Dict, Any
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler


class StockDataPreprocessor:
    """
    Preprocessor for stock data with technical indicators and sequence creation.
    Designed for LSTM time-series prediction.
    """
    
    def __init__(self, lookback: int = 60, scaler_path: Optional[str] = None):
        """
        Initialize preprocessor.
        
        Args:
            lookback: Number of past days to use for prediction
            scaler_path: Path to save/load scaler objects
        """
        self.lookback = lookback
        self.scaler_path = scaler_path or "ml-models/saved_models/scalers"
        self.feature_scaler = MinMaxScaler(feature_range=(0, 1))
        self.target_scaler = MinMaxScaler(feature_range=(0, 1))
        self.feature_columns: List[str] = []
        
        # Create scaler directory
        os.makedirs(self.scaler_path, exist_ok=True)
    
    def add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add technical indicators to the dataframe.
        
        Args:
            df: DataFrame with OHLCV columns
            
        Returns:
            DataFrame with additional technical indicator columns
        """
        df = df.copy()
        
        # Ensure we have required columns
        required = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in df.columns for col in required):
            # Try lowercase
            df.columns = [col.capitalize() for col in df.columns]
        
        close = df['Close']
        high = df['High']
        low = df['Low']
        volume = df['Volume']
        
        # Simple Moving Averages
        df['SMA_20'] = close.rolling(window=20).mean()
        df['SMA_50'] = close.rolling(window=50).mean()
        
        # Exponential Moving Averages
        df['EMA_12'] = close.ewm(span=12, adjust=False).mean()
        df['EMA_26'] = close.ewm(span=26, adjust=False).mean()
        
        # MACD
        df['MACD'] = df['EMA_12'] - df['EMA_26']
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
        
        # RSI (Relative Strength Index)
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        bb_period = 20
        bb_std = 2
        df['BB_Middle'] = close.rolling(window=bb_period).mean()
        bb_std_val = close.rolling(window=bb_period).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * bb_std_val)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * bb_std_val)
        df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle']
        
        # Average True Range (ATR)
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df['ATR'] = tr.rolling(window=14).mean()
        
        # On-Balance Volume (OBV)
        obv = [0]
        for i in range(1, len(close)):
            if close.iloc[i] > close.iloc[i-1]:
                obv.append(obv[-1] + volume.iloc[i])
            elif close.iloc[i] < close.iloc[i-1]:
                obv.append(obv[-1] - volume.iloc[i])
            else:
                obv.append(obv[-1])
        df['OBV'] = obv
        
        # Price Rate of Change
        df['ROC'] = close.pct_change(periods=10) * 100
        
        # Volume Moving Average
        df['Volume_MA'] = volume.rolling(window=20).mean()
        df['Volume_Ratio'] = volume / df['Volume_MA']
        
        # Price position relative to range
        df['Price_Position'] = (close - low.rolling(20).min()) / (high.rolling(20).max() - low.rolling(20).min())
        
        # Drop NaN values
        df = df.dropna()
        
        return df
    
    def normalize_data(
        self, 
        df: pd.DataFrame, 
        fit: bool = True,
        symbol: Optional[str] = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Normalize features and target using MinMaxScaler.
        
        Args:
            df: DataFrame with features
            fit: Whether to fit scalers (True for training)
            symbol: Stock symbol for saving scalers
            
        Returns:
            Tuple of (normalized features, normalized target)
        """
        # Define feature columns (exclude target)
        self.feature_columns = [
            'Open', 'High', 'Low', 'Close', 'Volume',
            'SMA_20', 'SMA_50', 'EMA_12', 'EMA_26',
            'MACD', 'MACD_Signal', 'MACD_Hist', 'RSI',
            'BB_Middle', 'BB_Upper', 'BB_Lower', 'BB_Width',
            'ATR', 'OBV', 'ROC', 'Volume_MA', 'Volume_Ratio', 'Price_Position'
        ]
        
        # Filter to available columns
        available_features = [col for col in self.feature_columns if col in df.columns]
        features = df[available_features].values
        target = df[['Close']].values
        
        if fit:
            self.feature_scaler.fit(features)
            self.target_scaler.fit(target)
            
            if symbol:
                self.save_scalers(symbol)
        
        normalized_features = self.feature_scaler.transform(features)
        normalized_target = self.target_scaler.transform(target)
        
        return normalized_features, normalized_target
    
    def create_sequences(
        self, 
        features: np.ndarray, 
        target: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create sequences for LSTM input.
        
        Args:
            features: Normalized feature array
            target: Normalized target array
            
        Returns:
            Tuple of (X sequences, y targets)
        """
        X, y = [], []
        
        for i in range(self.lookback, len(features)):
            X.append(features[i-self.lookback:i])
            y.append(target[i, 0])
        
        return np.array(X), np.array(y)
    
    def prepare_train_test_split(
        self, 
        X: np.ndarray, 
        y: np.ndarray, 
        train_split: float = 0.8,
        val_split: float = 0.1
    ) -> Dict[str, np.ndarray]:
        """
        Split data maintaining temporal order (no shuffle).
        
        Args:
            X: Feature sequences
            y: Target values
            train_split: Proportion for training
            val_split: Proportion for validation
            
        Returns:
            Dictionary with train/val/test splits
        """
        total_samples = len(X)
        train_size = int(total_samples * train_split)
        val_size = int(total_samples * val_split)
        
        return {
            'X_train': X[:train_size],
            'y_train': y[:train_size],
            'X_val': X[train_size:train_size+val_size],
            'y_val': y[train_size:train_size+val_size],
            'X_test': X[train_size+val_size:],
            'y_test': y[train_size+val_size:]
        }
    
    def inverse_transform(self, predictions: np.ndarray) -> np.ndarray:
        """
        Convert normalized predictions back to original scale.
        
        Args:
            predictions: Normalized prediction values
            
        Returns:
            Predictions in original price scale
        """
        if predictions.ndim == 1:
            predictions = predictions.reshape(-1, 1)
        return self.target_scaler.inverse_transform(predictions)
    
    def save_scalers(self, symbol: str) -> None:
        """Save scalers for later use."""
        scaler_file = os.path.join(self.scaler_path, f"{symbol}_scalers.pkl")
        with open(scaler_file, 'wb') as f:
            pickle.dump({
                'feature_scaler': self.feature_scaler,
                'target_scaler': self.target_scaler,
                'feature_columns': self.feature_columns,
                'lookback': self.lookback
            }, f)
        print(f"Scalers saved to {scaler_file}")
    
    def load_scalers(self, symbol: str) -> bool:
        """Load saved scalers."""
        scaler_file = os.path.join(self.scaler_path, f"{symbol}_scalers.pkl")
        if os.path.exists(scaler_file):
            with open(scaler_file, 'rb') as f:
                data = pickle.load(f)
                self.feature_scaler = data['feature_scaler']
                self.target_scaler = data['target_scaler']
                self.feature_columns = data['feature_columns']
                self.lookback = data['lookback']
            return True
        return False
    
    def prepare_prediction_data(
        self, 
        df: pd.DataFrame, 
        symbol: str
    ) -> Optional[np.ndarray]:
        """
        Prepare data for making predictions.
        
        Args:
            df: Recent stock data (at least lookback days)
            symbol: Stock symbol to load scalers
            
        Returns:
            Prepared sequence for prediction
        """
        if not self.load_scalers(symbol):
            print(f"No scalers found for {symbol}")
            return None
        
        # Add indicators
        df = self.add_technical_indicators(df)
        
        if len(df) < self.lookback:
            print(f"Insufficient data: need {self.lookback}, got {len(df)}")
            return None
        
        # Normalize without fitting
        features, _ = self.normalize_data(df, fit=False)
        
        # Get last lookback sequence
        sequence = features[-self.lookback:]
        return sequence.reshape(1, self.lookback, -1)


def preprocess_for_training(
    symbol: str,
    period: str = "5y",
    lookback: int = 60
) -> Optional[Dict[str, Any]]:
    """
    Complete preprocessing pipeline for training.
    
    Args:
        symbol: Stock symbol
        period: Data period
        lookback: Sequence length
        
    Returns:
        Dictionary with preprocessed data splits
    """
    import yfinance as yf
    
    print(f"Fetching data for {symbol}...")
    ticker = yf.Ticker(f"{symbol}.NS")
    df = ticker.history(period=period)
    
    if df.empty:
        print(f"No data found for {symbol}")
        return None
    
    print(f"Data shape: {df.shape}")
    
    preprocessor = StockDataPreprocessor(lookback=lookback)
    
    # Add technical indicators
    print("Adding technical indicators...")
    df = preprocessor.add_technical_indicators(df)
    print(f"After indicators: {df.shape}")
    
    # Normalize
    print("Normalizing data...")
    features, target = preprocessor.normalize_data(df, fit=True, symbol=symbol)
    
    # Create sequences
    print("Creating sequences...")
    X, y = preprocessor.create_sequences(features, target)
    print(f"Sequences: X={X.shape}, y={y.shape}")
    
    # Split data
    splits = preprocessor.prepare_train_test_split(X, y)
    splits['preprocessor'] = preprocessor
    splits['dates'] = df.index[lookback:].tolist()
    
    return splits


if __name__ == "__main__":
    # Test preprocessing
    result = preprocess_for_training("RELIANCE", period="2y")
    if result:
        print(f"\nTrain: {result['X_train'].shape}")
        print(f"Val: {result['X_val'].shape}")
        print(f"Test: {result['X_test'].shape}")
