"""
Train All Models Script
Trains LSTM, GRU, Random Forest, and XGBoost models for top NSE stocks.
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import List, Dict
import argparse

import yfinance as yf
import pandas as pd

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ensemble_model import EnsemblePredictor, ModelMetrics


# Top 50 NSE Stocks by Market Cap
TOP_NSE_STOCKS = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
    "HINDUNILVR", "SBIN", "BHARTIARTL", "ITC", "KOTAKBANK",
    "LT", "HCLTECH", "AXISBANK", "ASIANPAINT", "MARUTI",
    "SUNPHARMA", "TITAN", "BAJFINANCE", "DMART", "ULTRACEMCO",
    "WIPRO", "NESTLEIND", "M&M", "TATAMOTORS", "POWERGRID",
    "NTPC", "BAJAJFINSV", "TECHM", "ONGC", "TATASTEEL",
    "JSWSTEEL", "ADANIENT", "ADANIPORTS", "COALINDIA", "HINDALCO",
    "DRREDDY", "CIPLA", "DIVISLAB", "EICHERMOT", "BRITANNIA",
    "GRASIM", "APOLLOHOSP", "HEROMOTOCO", "SBILIFE", "HDFCLIFE",
    "INDUSINDBK", "TATACONSUM", "BPCL", "UPL", "SHREECEM"
]


def fetch_stock_data(symbol: str, period: str = "2y") -> pd.DataFrame:
    """
    Fetch historical stock data from Yahoo Finance.
    
    Args:
        symbol: NSE stock symbol
        period: Data period (default 2 years for training)
        
    Returns:
        DataFrame with OHLCV data
    """
    try:
        ticker = yf.Ticker(f"{symbol}.NS")
        df = ticker.history(period=period)
        
        if df.empty:
            # Try BSE
            ticker = yf.Ticker(f"{symbol}.BO")
            df = ticker.history(period=period)
        
        if not df.empty:
            print(f"  ✓ Fetched {len(df)} days of data for {symbol}")
            return df
        else:
            print(f"  ✗ No data found for {symbol}")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"  ✗ Error fetching {symbol}: {e}")
        return pd.DataFrame()


def train_models_for_symbol(
    predictor: EnsemblePredictor,
    symbol: str,
    data: pd.DataFrame,
    epochs: int = 50
) -> Dict[str, ModelMetrics]:
    """
    Train all model types for a single symbol.
    
    Args:
        predictor: EnsemblePredictor instance
        symbol: Stock symbol
        data: Historical data
        epochs: Training epochs for deep learning models
        
    Returns:
        Dict of model type to metrics
    """
    metrics = {}
    
    # Train LSTM
    print(f"  Training LSTM for {symbol}...")
    start = time.time()
    try:
        lstm_metrics = predictor.train_lstm_model(symbol, data, epochs=epochs)
        metrics['lstm'] = lstm_metrics
        print(f"    LSTM: RMSE={lstm_metrics.rmse}, R²={lstm_metrics.r_squared} ({time.time()-start:.1f}s)")
    except Exception as e:
        print(f"    LSTM failed: {e}")
    
    # Train GRU
    print(f"  Training GRU for {symbol}...")
    start = time.time()
    try:
        gru_metrics = predictor.train_gru_model(symbol, data, epochs=epochs)
        metrics['gru'] = gru_metrics
        print(f"    GRU: RMSE={gru_metrics.rmse}, R²={gru_metrics.r_squared} ({time.time()-start:.1f}s)")
    except Exception as e:
        print(f"    GRU failed: {e}")
    
    # Train Random Forest
    print(f"  Training Random Forest for {symbol}...")
    start = time.time()
    try:
        rf_metrics = predictor.train_random_forest(symbol, data)
        metrics['random_forest'] = rf_metrics
        print(f"    RF: RMSE={rf_metrics.rmse}, R²={rf_metrics.r_squared} ({time.time()-start:.1f}s)")
    except Exception as e:
        print(f"    RF failed: {e}")
    
    # Train XGBoost
    print(f"  Training XGBoost for {symbol}...")
    start = time.time()
    try:
        xgb_metrics = predictor.train_xgboost(symbol, data)
        metrics['xgboost'] = xgb_metrics
        print(f"    XGB: RMSE={xgb_metrics.rmse}, R²={xgb_metrics.r_squared} ({time.time()-start:.1f}s)")
    except Exception as e:
        print(f"    XGB failed: {e}")
    
    return metrics


def generate_training_report(
    all_metrics: Dict[str, Dict[str, ModelMetrics]],
    output_path: str = "training_report.json"
) -> Dict:
    """
    Generate a comprehensive training summary report.
    
    Args:
        all_metrics: Dict of symbol -> model_type -> metrics
        output_path: Path to save JSON report
        
    Returns:
        Summary report dict
    """
    report = {
        'generated_at': datetime.now().isoformat(),
        'total_symbols': len(all_metrics),
        'models_trained': sum(len(m) for m in all_metrics.values()),
        'summary': {},
        'details': {}
    }
    
    # Calculate averages by model type
    model_stats = {}
    for symbol, metrics in all_metrics.items():
        for model_type, m in metrics.items():
            if model_type not in model_stats:
                model_stats[model_type] = {'rmse': [], 'mae': [], 'mape': [], 'r_squared': []}
            model_stats[model_type]['rmse'].append(m.rmse)
            model_stats[model_type]['mae'].append(m.mae)
            model_stats[model_type]['mape'].append(m.mape)
            model_stats[model_type]['r_squared'].append(m.r_squared)
    
    for model_type, stats in model_stats.items():
        report['summary'][model_type] = {
            'count': len(stats['rmse']),
            'avg_rmse': round(sum(stats['rmse']) / len(stats['rmse']), 4) if stats['rmse'] else 0,
            'avg_mae': round(sum(stats['mae']) / len(stats['mae']), 4) if stats['mae'] else 0,
            'avg_mape': round(sum(stats['mape']) / len(stats['mape']), 2) if stats['mape'] else 0,
            'avg_r_squared': round(sum(stats['r_squared']) / len(stats['r_squared']), 4) if stats['r_squared'] else 0
        }
    
    # Detailed results by symbol
    for symbol, metrics in all_metrics.items():
        report['details'][symbol] = {
            model_type: {
                'rmse': m.rmse,
                'mae': m.mae,
                'mape': m.mape,
                'r_squared': m.r_squared,
                'training_samples': m.training_samples,
                'training_date': m.training_date
            }
            for model_type, m in metrics.items()
        }
    
    # Find best performing models
    best_models = {}
    for symbol, metrics in all_metrics.items():
        best_r2 = -1
        best_model = None
        for model_type, m in metrics.items():
            if m.r_squared > best_r2:
                best_r2 = m.r_squared
                best_model = model_type
        if best_model:
            best_models[symbol] = {'best_model': best_model, 'r_squared': best_r2}
    
    report['best_models'] = best_models
    
    # Save report
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n📊 Training report saved to: {output_path}")
    
    return report


def main():
    """Main training script."""
    parser = argparse.ArgumentParser(description='Train models for NSE stocks')
    parser.add_argument('--stocks', nargs='+', help='Specific stocks to train (default: top 50)')
    parser.add_argument('--limit', type=int, default=50, help='Number of stocks to train')
    parser.add_argument('--epochs', type=int, default=50, help='Training epochs')
    parser.add_argument('--output-dir', type=str, default='saved_models', help='Output directory')
    parser.add_argument('--quick', action='store_true', help='Quick mode (fewer epochs)')
    
    args = parser.parse_args()
    
    # Setup
    stocks = args.stocks if args.stocks else TOP_NSE_STOCKS[:args.limit]
    epochs = 20 if args.quick else args.epochs
    
    print(f"""
╔══════════════════════════════════════════════════════════╗
║         Stock Prediction Model Training Pipeline         ║
╠══════════════════════════════════════════════════════════╣
║  Stocks to train: {len(stocks):3d}                                   ║
║  Models per stock: 4 (LSTM, GRU, RF, XGBoost)            ║
║  Total models: {len(stocks) * 4:4d}                                    ║
║  Epochs: {epochs:3d}                                             ║
║  Output: {args.output_dir:<47}║
╚══════════════════════════════════════════════════════════╝
    """)
    
    start_time = time.time()
    
    # Initialize predictor
    predictor = EnsemblePredictor(models_dir=args.output_dir)
    
    all_metrics = {}
    failed_stocks = []
    
    for i, symbol in enumerate(stocks, 1):
        print(f"\n[{i}/{len(stocks)}] Processing {symbol}...")
        
        # Fetch data
        data = fetch_stock_data(symbol)
        
        if data.empty or len(data) < 100:
            print(f"  ⚠ Insufficient data for {symbol}, skipping...")
            failed_stocks.append(symbol)
            continue
        
        # Train models
        metrics = train_models_for_symbol(predictor, symbol, data, epochs=epochs)
        
        if metrics:
            all_metrics[symbol] = metrics
            print(f"  ✓ {symbol} complete - {len(metrics)} models trained")
        else:
            failed_stocks.append(symbol)
    
    # Generate report
    elapsed = time.time() - start_time
    
    print(f"\n{'='*60}")
    print(f"Training Complete!")
    print(f"{'='*60}")
    print(f"✓ Successfully trained: {len(all_metrics)} stocks")
    print(f"✗ Failed: {len(failed_stocks)} stocks")
    print(f"⏱ Total time: {elapsed/60:.1f} minutes")
    
    if all_metrics:
        report = generate_training_report(
            all_metrics, 
            os.path.join(args.output_dir, 'training_report.json')
        )
        
        # Print summary
        print(f"\n📈 Model Performance Summary:")
        for model, stats in report['summary'].items():
            print(f"  {model.upper():15} - Avg R²: {stats['avg_r_squared']:.4f}, Avg MAPE: {stats['avg_mape']:.2f}%")
    
    if failed_stocks:
        print(f"\n⚠ Failed stocks: {', '.join(failed_stocks)}")
    
    return all_metrics


if __name__ == "__main__":
    main()
