"""
Model Evaluation Module
Provides metrics calculation and visualization for model performance.
"""

import os
from typing import Dict, List, Tuple, Optional
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score


def calculate_accuracy_metrics(
    y_true: np.ndarray, 
    y_pred: np.ndarray
) -> Dict[str, float]:
    """
    Calculate comprehensive accuracy metrics.
    
    Args:
        y_true: Actual values
        y_pred: Predicted values
        
    Returns:
        Dictionary with RMSE, MAE, MAPE, R²
    """
    y_true = np.array(y_true).flatten()
    y_pred = np.array(y_pred).flatten()
    
    # RMSE
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    
    # MAE
    mae = mean_absolute_error(y_true, y_pred)
    
    # MAPE (Mean Absolute Percentage Error)
    mask = y_true != 0
    mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100
    
    # R² Score
    r2 = r2_score(y_true, y_pred)
    
    return {
        "rmse": round(float(rmse), 4),
        "mae": round(float(mae), 4),
        "mape": round(float(mape), 4),
        "r2": round(float(r2), 4)
    }


def directional_accuracy(
    y_true: np.ndarray, 
    y_pred: np.ndarray
) -> float:
    """
    Calculate directional accuracy (up/down prediction accuracy).
    
    Args:
        y_true: Actual values
        y_pred: Predicted values
        
    Returns:
        Percentage of correct direction predictions
    """
    y_true = np.array(y_true).flatten()
    y_pred = np.array(y_pred).flatten()
    
    if len(y_true) < 2:
        return 0.0
    
    # Calculate actual and predicted directions
    true_direction = np.sign(np.diff(y_true))
    pred_direction = np.sign(np.diff(y_pred))
    
    # Count correct directions
    correct = np.sum(true_direction == pred_direction)
    total = len(true_direction)
    
    return round((correct / total) * 100, 2)


def plot_predictions(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    symbol: str,
    save_path: str = "saved_models",
    show: bool = False
) -> str:
    """
    Plot actual vs predicted values.
    
    Args:
        y_true: Actual values
        y_pred: Predicted values
        symbol: Stock symbol for title
        save_path: Directory to save plot
        show: Whether to display plot
        
    Returns:
        Path to saved plot
    """
    os.makedirs(save_path, exist_ok=True)
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. Time series comparison
    ax1 = axes[0, 0]
    ax1.plot(y_true, label='Actual', color='#2196F3', linewidth=1.5)
    ax1.plot(y_pred, label='Predicted', color='#F44336', linewidth=1.5, alpha=0.8)
    ax1.set_title(f'{symbol} - Actual vs Predicted Prices', fontsize=12, fontweight='bold')
    ax1.set_xlabel('Time Steps')
    ax1.set_ylabel('Price (₹)')
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)
    
    # 2. Scatter plot
    ax2 = axes[0, 1]
    ax2.scatter(y_true, y_pred, alpha=0.5, color='#4CAF50')
    
    # Perfect prediction line
    min_val = min(y_true.min(), y_pred.min())
    max_val = max(y_true.max(), y_pred.max())
    ax2.plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2, label='Perfect Prediction')
    
    ax2.set_title(f'{symbol} - Prediction Scatter Plot', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Actual Price (₹)')
    ax2.set_ylabel('Predicted Price (₹)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. Error distribution
    ax3 = axes[1, 0]
    errors = y_pred - y_true
    ax3.hist(errors, bins=50, color='#9C27B0', edgecolor='white', alpha=0.7)
    ax3.axvline(x=0, color='red', linestyle='--', linewidth=2)
    ax3.axvline(x=np.mean(errors), color='green', linestyle='-', linewidth=2, label=f'Mean: {np.mean(errors):.2f}')
    ax3.set_title(f'{symbol} - Prediction Error Distribution', fontsize=12, fontweight='bold')
    ax3.set_xlabel('Error (₹)')
    ax3.set_ylabel('Frequency')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. Cumulative error
    ax4 = axes[1, 1]
    cumulative_error = np.cumsum(np.abs(errors)) / (np.arange(len(errors)) + 1)
    ax4.plot(cumulative_error, color='#FF9800', linewidth=2)
    ax4.set_title(f'{symbol} - Cumulative Mean Absolute Error', fontsize=12, fontweight='bold')
    ax4.set_xlabel('Time Steps')
    ax4.set_ylabel('Cumulative MAE (₹)')
    ax4.grid(True, alpha=0.3)
    
    # Add metrics text
    metrics = calculate_accuracy_metrics(y_true, y_pred)
    dir_acc = directional_accuracy(y_true, y_pred)
    
    metrics_text = (
        f"RMSE: ₹{metrics['rmse']:.2f}\n"
        f"MAE: ₹{metrics['mae']:.2f}\n"
        f"MAPE: {metrics['mape']:.2f}%\n"
        f"R²: {metrics['r2']:.4f}\n"
        f"Dir. Acc: {dir_acc:.1f}%"
    )
    
    fig.text(0.02, 0.02, metrics_text, fontsize=10, family='monospace',
             verticalalignment='bottom', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    
    plot_path = os.path.join(save_path, f"{symbol}_predictions.png")
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    
    if show:
        plt.show()
    else:
        plt.close()
    
    print(f"Prediction plot saved to: {plot_path}")
    return plot_path


def evaluate_model_performance(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    symbol: str,
    verbose: bool = True
) -> Dict:
    """
    Comprehensive model evaluation.
    
    Args:
        y_true: Actual values
        y_pred: Predicted values
        symbol: Stock symbol
        verbose: Print results
        
    Returns:
        Complete evaluation results
    """
    metrics = calculate_accuracy_metrics(y_true, y_pred)
    dir_acc = directional_accuracy(y_true, y_pred)
    
    # Additional statistics
    errors = y_pred - y_true
    pct_errors = (y_pred - y_true) / y_true * 100
    
    results = {
        **metrics,
        "directional_accuracy": dir_acc,
        "mean_error": round(float(np.mean(errors)), 4),
        "std_error": round(float(np.std(errors)), 4),
        "max_error": round(float(np.max(np.abs(errors))), 4),
        "mean_pct_error": round(float(np.mean(pct_errors)), 4),
        "predictions_count": len(y_pred)
    }
    
    if verbose:
        print(f"\n{'='*50}")
        print(f"Model Evaluation: {symbol}")
        print(f"{'='*50}")
        print(f"RMSE:               ₹{metrics['rmse']:.2f}")
        print(f"MAE:                ₹{metrics['mae']:.2f}")
        print(f"MAPE:               {metrics['mape']:.2f}%")
        print(f"R² Score:           {metrics['r2']:.4f}")
        print(f"Direction Accuracy: {dir_acc:.1f}%")
        print(f"Mean Error:         ₹{results['mean_error']:.2f}")
        print(f"Max Error:          ₹{results['max_error']:.2f}")
        print(f"{'='*50}")
    
    return results


def calculate_confidence_score(
    predictions: np.ndarray,
    volatility: float,
    model_accuracy: float
) -> str:
    """
    Calculate confidence level for predictions.
    
    Args:
        predictions: Predicted values
        volatility: Historical volatility score
        model_accuracy: Model's historical accuracy
        
    Returns:
        Confidence level: high, medium, or low
    """
    # Base score from model accuracy
    base_score = model_accuracy
    
    # Adjust for volatility (high volatility = lower confidence)
    volatility_penalty = min(volatility / 50, 0.3)  # Max 30% penalty
    
    # Calculate prediction consistency
    pred_std = np.std(np.diff(predictions)) if len(predictions) > 1 else 0
    consistency_factor = 1 - min(pred_std / np.mean(predictions), 0.2)
    
    # Final score
    final_score = base_score * (1 - volatility_penalty) * consistency_factor
    
    if final_score >= 75:
        return "high"
    elif final_score >= 50:
        return "medium"
    else:
        return "low"


if __name__ == "__main__":
    # Test with dummy data
    np.random.seed(42)
    y_true = np.cumsum(np.random.randn(100)) + 1000
    y_pred = y_true + np.random.randn(100) * 10
    
    results = evaluate_model_performance(y_true, y_pred, "TEST")
    plot_predictions(y_true, y_pred, "TEST", show=True)
