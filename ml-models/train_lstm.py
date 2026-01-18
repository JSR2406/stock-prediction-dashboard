"""
LSTM Model Training Module
Builds, trains, and saves LSTM models for stock prediction.
"""

import os
import json
from datetime import datetime
from typing import Tuple, Optional, Dict, Any
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from tensorflow.keras.optimizers import Adam

from data_preprocessing import StockDataPreprocessor, preprocess_for_training
from model_evaluation import calculate_accuracy_metrics, plot_predictions, directional_accuracy


# Model versioning
MODEL_VERSION = "1.0.0"
MODEL_BASE_PATH = "saved_models"


def build_lstm_model(
    input_shape: Tuple[int, int],
    lstm_units: list = [50, 50, 50],
    dropout_rate: float = 0.2,
    learning_rate: float = 0.001
) -> Sequential:
    """
    Build LSTM model architecture.
    
    Args:
        input_shape: (lookback, num_features)
        lstm_units: List of units for each LSTM layer
        dropout_rate: Dropout rate between layers
        learning_rate: Adam optimizer learning rate
        
    Returns:
        Compiled Keras Sequential model
    """
    model = Sequential()
    
    # First LSTM layer
    model.add(LSTM(
        units=lstm_units[0],
        return_sequences=True,
        input_shape=input_shape
    ))
    model.add(BatchNormalization())
    model.add(Dropout(dropout_rate))
    
    # Second LSTM layer
    model.add(LSTM(
        units=lstm_units[1],
        return_sequences=True
    ))
    model.add(BatchNormalization())
    model.add(Dropout(dropout_rate))
    
    # Third LSTM layer
    model.add(LSTM(
        units=lstm_units[2],
        return_sequences=False
    ))
    model.add(BatchNormalization())
    model.add(Dropout(dropout_rate))
    
    # Dense layers
    model.add(Dense(25, activation='relu'))
    model.add(Dense(1))
    
    # Compile
    optimizer = Adam(learning_rate=learning_rate)
    model.compile(optimizer=optimizer, loss='mse', metrics=['mae'])
    
    print(model.summary())
    return model


def train_model(
    symbol: str,
    period: str = "5y",
    epochs: int = 100,
    batch_size: int = 32,
    patience: int = 10,
    lookback: int = 60
) -> Optional[Dict[str, Any]]:
    """
    Train LSTM model for a stock.
    
    Args:
        symbol: Stock symbol (NSE)
        period: Data period for training
        epochs: Maximum training epochs
        batch_size: Batch size
        patience: Early stopping patience
        lookback: Sequence length
        
    Returns:
        Training results dictionary
    """
    print(f"\n{'='*60}")
    print(f"Training LSTM Model for {symbol}")
    print(f"Period: {period} | Lookback: {lookback} | Epochs: {epochs}")
    print(f"{'='*60}\n")
    
    # Preprocess data
    data = preprocess_for_training(symbol, period, lookback)
    if data is None:
        return None
    
    X_train, y_train = data['X_train'], data['y_train']
    X_val, y_val = data['X_val'], data['y_val']
    X_test, y_test = data['X_test'], data['y_test']
    preprocessor = data['preprocessor']
    
    print(f"\nData splits:")
    print(f"  Train: {X_train.shape[0]} samples")
    print(f"  Val: {X_val.shape[0]} samples")
    print(f"  Test: {X_test.shape[0]} samples")
    
    # Build model
    input_shape = (X_train.shape[1], X_train.shape[2])
    model = build_lstm_model(input_shape)
    
    # Callbacks
    os.makedirs(MODEL_BASE_PATH, exist_ok=True)
    model_path = os.path.join(MODEL_BASE_PATH, f"{symbol}_best_model.h5")
    
    callbacks = [
        EarlyStopping(
            monitor='val_loss',
            patience=patience,
            restore_best_weights=True,
            verbose=1
        ),
        ModelCheckpoint(
            model_path,
            monitor='val_loss',
            save_best_only=True,
            verbose=1
        ),
        ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=5,
            min_lr=1e-6,
            verbose=1
        )
    ]
    
    # Train
    print("\nStarting training...")
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=epochs,
        batch_size=batch_size,
        callbacks=callbacks,
        verbose=1
    )
    
    # Evaluate on test set
    print("\nEvaluating on test set...")
    predictions = model.predict(X_test, verbose=0)
    
    # Inverse transform
    y_test_orig = preprocessor.inverse_transform(y_test)
    predictions_orig = preprocessor.inverse_transform(predictions)
    
    # Calculate metrics
    metrics = calculate_accuracy_metrics(y_test_orig.flatten(), predictions_orig.flatten())
    dir_acc = directional_accuracy(y_test_orig.flatten(), predictions_orig.flatten())
    
    print(f"\nTest Results:")
    print(f"  RMSE: ₹{metrics['rmse']:.2f}")
    print(f"  MAE: ₹{metrics['mae']:.2f}")
    print(f"  MAPE: {metrics['mape']:.2f}%")
    print(f"  R²: {metrics['r2']:.4f}")
    print(f"  Direction Accuracy: {dir_acc:.2f}%")
    
    # Save training history plot
    plot_training_history(history, symbol)
    
    # Save prediction plot
    plot_predictions(y_test_orig.flatten(), predictions_orig.flatten(), symbol)
    
    # Save model metadata
    metadata = {
        "symbol": symbol,
        "version": MODEL_VERSION,
        "trained_at": datetime.now().isoformat(),
        "period": period,
        "lookback": lookback,
        "epochs_trained": len(history.history['loss']),
        "metrics": metrics,
        "directional_accuracy": dir_acc,
        "input_shape": list(input_shape),
        "train_samples": len(X_train),
        "val_samples": len(X_val),
        "test_samples": len(X_test)
    }
    
    metadata_path = os.path.join(MODEL_BASE_PATH, f"{symbol}_metadata.json")
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\nModel saved to: {model_path}")
    print(f"Metadata saved to: {metadata_path}")
    
    return {
        "model": model,
        "history": history.history,
        "metrics": metrics,
        "directional_accuracy": dir_acc,
        "metadata": metadata
    }


def plot_training_history(history, symbol: str) -> None:
    """Plot and save training history."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Loss plot
    axes[0].plot(history.history['loss'], label='Train Loss', color='#2196F3')
    axes[0].plot(history.history['val_loss'], label='Val Loss', color='#F44336')
    axes[0].set_title(f'{symbol} - Training Loss', fontsize=12, fontweight='bold')
    axes[0].set_xlabel('Epoch')
    axes[0].set_ylabel('Loss (MSE)')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # MAE plot
    axes[1].plot(history.history['mae'], label='Train MAE', color='#4CAF50')
    axes[1].plot(history.history['val_mae'], label='Val MAE', color='#FF9800')
    axes[1].set_title(f'{symbol} - Mean Absolute Error', fontsize=12, fontweight='bold')
    axes[1].set_xlabel('Epoch')
    axes[1].set_ylabel('MAE')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plot_path = os.path.join(MODEL_BASE_PATH, f"{symbol}_training_history.png")
    plt.savefig(plot_path, dpi=150)
    plt.close()
    print(f"Training history plot saved to: {plot_path}")


def load_trained_model(symbol: str) -> Optional[tf.keras.Model]:
    """Load a trained model."""
    model_path = os.path.join(MODEL_BASE_PATH, f"{symbol}_best_model.h5")
    if os.path.exists(model_path):
        return load_model(model_path)
    return None


def get_model_metadata(symbol: str) -> Optional[Dict]:
    """Load model metadata."""
    metadata_path = os.path.join(MODEL_BASE_PATH, f"{symbol}_metadata.json")
    if os.path.exists(metadata_path):
        with open(metadata_path, 'r') as f:
            return json.load(f)
    return None


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Train LSTM model for stock prediction")
    parser.add_argument("--symbol", type=str, default="RELIANCE", help="Stock symbol")
    parser.add_argument("--period", type=str, default="5y", help="Data period")
    parser.add_argument("--epochs", type=int, default=100, help="Max epochs")
    parser.add_argument("--batch_size", type=int, default=32, help="Batch size")
    
    args = parser.parse_args()
    
    result = train_model(
        symbol=args.symbol,
        period=args.period,
        epochs=args.epochs,
        batch_size=args.batch_size
    )
    
    if result:
        print("\n✅ Training completed successfully!")
    else:
        print("\n❌ Training failed!")
