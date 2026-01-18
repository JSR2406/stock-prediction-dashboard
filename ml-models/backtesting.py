"""
Backtesting Module for Stock Predictions
Test prediction accuracy against historical data.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import json


@dataclass
class BacktestResult:
    """Results from a backtest run."""
    symbol: str
    start_date: str
    end_date: str
    total_predictions: int
    correct_direction: int
    direction_accuracy: float
    mean_absolute_error: float
    mean_percentage_error: float
    profit_loss: float
    profit_loss_percent: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    best_prediction: Dict
    worst_prediction: Dict


class Backtester:
    """
    Backtest stock predictions against historical data.
    
    Usage:
        backtester = Backtester()
        results = backtester.backtest_predictions("RELIANCE", predictions, actual_prices)
    """
    
    def __init__(self):
        self.results_history: List[BacktestResult] = []
    
    def backtest_predictions(
        self,
        symbol: str,
        predictions: pd.DataFrame,
        actual_prices: pd.Series,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> BacktestResult:
        """
        Backtest predictions against actual prices.
        
        Args:
            symbol: Stock symbol
            predictions: DataFrame with 'date' and 'predicted_price' columns
            actual_prices: Series of actual closing prices with date index
            start_date: Start date for backtest (optional)
            end_date: End date for backtest (optional)
            
        Returns:
            BacktestResult with comprehensive metrics
        """
        # Align predictions with actual prices
        if isinstance(predictions, pd.DataFrame):
            pred_df = predictions.copy()
        else:
            pred_df = pd.DataFrame(predictions)
        
        if start_date:
            pred_df = pred_df[pred_df['date'] >= start_date]
        if end_date:
            pred_df = pred_df[pred_df['date'] <= end_date]
        
        # Calculate metrics
        correct_direction = 0
        errors = []
        percentage_errors = []
        best_pred = {'error': float('inf'), 'date': None}
        worst_pred = {'error': 0, 'date': None}
        
        for _, row in pred_df.iterrows():
            date = row.get('date')
            predicted = row.get('predicted_price')
            
            if date in actual_prices.index:
                actual = actual_prices[date]
                error = abs(predicted - actual)
                pct_error = (error / actual) * 100
                
                errors.append(error)
                percentage_errors.append(pct_error)
                
                # Direction accuracy
                if len(actual_prices) > 1:
                    prev_idx = actual_prices.index.get_loc(date) - 1
                    if prev_idx >= 0:
                        prev_price = actual_prices.iloc[prev_idx]
                        actual_direction = actual > prev_price
                        pred_direction = predicted > prev_price
                        if actual_direction == pred_direction:
                            correct_direction += 1
                
                # Track best/worst
                if error < best_pred['error']:
                    best_pred = {'error': round(error, 2), 'date': str(date), 
                                'predicted': round(predicted, 2), 'actual': round(actual, 2)}
                if error > worst_pred['error']:
                    worst_pred = {'error': round(error, 2), 'date': str(date),
                                 'predicted': round(predicted, 2), 'actual': round(actual, 2)}
        
        total_predictions = len(errors)
        
        if total_predictions == 0:
            return BacktestResult(
                symbol=symbol,
                start_date=start_date or "",
                end_date=end_date or "",
                total_predictions=0,
                correct_direction=0,
                direction_accuracy=0,
                mean_absolute_error=0,
                mean_percentage_error=0,
                profit_loss=0,
                profit_loss_percent=0,
                max_drawdown=0,
                sharpe_ratio=0,
                win_rate=0,
                best_prediction={},
                worst_prediction={}
            )
        
        mae = np.mean(errors)
        mpe = np.mean(percentage_errors)
        direction_accuracy = (correct_direction / max(1, total_predictions - 1)) * 100
        
        # Calculate profit/loss simulation
        pnl = self.calculate_profit_loss(pred_df, actual_prices)
        max_dd = self._calculate_max_drawdown(actual_prices)
        sharpe = self._calculate_sharpe_ratio(actual_prices)
        win_rate = (correct_direction / max(1, total_predictions)) * 100
        
        result = BacktestResult(
            symbol=symbol,
            start_date=start_date or str(pred_df['date'].min()),
            end_date=end_date or str(pred_df['date'].max()),
            total_predictions=total_predictions,
            correct_direction=correct_direction,
            direction_accuracy=round(direction_accuracy, 2),
            mean_absolute_error=round(mae, 2),
            mean_percentage_error=round(mpe, 2),
            profit_loss=round(pnl['profit_loss'], 2),
            profit_loss_percent=round(pnl['profit_loss_percent'], 2),
            max_drawdown=round(max_dd, 2),
            sharpe_ratio=round(sharpe, 2),
            win_rate=round(win_rate, 2),
            best_prediction=best_pred,
            worst_prediction=worst_pred
        )
        
        self.results_history.append(result)
        return result
    
    def calculate_profit_loss(
        self,
        predictions: pd.DataFrame,
        actual_prices: pd.Series,
        initial_capital: float = 100000,
        position_size: float = 0.1
    ) -> Dict:
        """
        Calculate profit/loss if trading based on predictions.
        
        Args:
            predictions: DataFrame with predictions
            actual_prices: Actual price series
            initial_capital: Starting capital (default ₹100,000)
            position_size: Fraction of capital per trade (default 10%)
            
        Returns:
            Dict with profit/loss metrics
        """
        capital = initial_capital
        trades = []
        
        for i, row in predictions.iterrows():
            date = row.get('date')
            predicted = row.get('predicted_price')
            
            if date in actual_prices.index:
                actual = actual_prices[date]
                prev_idx = actual_prices.index.get_loc(date) - 1
                
                if prev_idx >= 0:
                    prev_price = actual_prices.iloc[prev_idx]
                    trade_capital = capital * position_size
                    
                    # Simple strategy: buy if predicted up, sell if predicted down
                    if predicted > prev_price:
                        # Buy signal
                        shares = trade_capital / prev_price
                        profit = shares * (actual - prev_price)
                    else:
                        # Sell signal (short)
                        shares = trade_capital / prev_price
                        profit = shares * (prev_price - actual)
                    
                    capital += profit
                    trades.append({
                        'date': str(date),
                        'signal': 'buy' if predicted > prev_price else 'sell',
                        'profit': round(profit, 2)
                    })
        
        total_pnl = capital - initial_capital
        pnl_percent = (total_pnl / initial_capital) * 100
        winning_trades = sum(1 for t in trades if t['profit'] > 0)
        
        return {
            'initial_capital': initial_capital,
            'final_capital': round(capital, 2),
            'profit_loss': round(total_pnl, 2),
            'profit_loss_percent': round(pnl_percent, 2),
            'total_trades': len(trades),
            'winning_trades': winning_trades,
            'win_rate': round((winning_trades / max(1, len(trades))) * 100, 2),
            'trades': trades[:20]  # Return first 20 trades
        }
    
    def _calculate_max_drawdown(self, prices: pd.Series) -> float:
        """Calculate maximum drawdown percentage."""
        running_max = prices.expanding().max()
        drawdown = (prices - running_max) / running_max * 100
        return abs(drawdown.min())
    
    def _calculate_sharpe_ratio(
        self, 
        prices: pd.Series, 
        risk_free_rate: float = 0.065
    ) -> float:
        """Calculate Sharpe ratio."""
        returns = prices.pct_change().dropna()
        if len(returns) < 2:
            return 0
        
        mean_return = returns.mean() * 252
        std_return = returns.std() * np.sqrt(252)
        
        if std_return == 0:
            return 0
        
        return (mean_return - risk_free_rate) / std_return
    
    def generate_backtest_report(self, result: BacktestResult) -> Dict:
        """
        Generate a comprehensive backtest report.
        
        Args:
            result: BacktestResult to report on
            
        Returns:
            Dict with formatted report data
        """
        report = {
            'summary': {
                'symbol': result.symbol,
                'period': f"{result.start_date} to {result.end_date}",
                'total_predictions': result.total_predictions
            },
            'accuracy_metrics': {
                'direction_accuracy': f"{result.direction_accuracy}%",
                'mean_absolute_error': f"₹{result.mean_absolute_error}",
                'mean_percentage_error': f"{result.mean_percentage_error}%",
                'win_rate': f"{result.win_rate}%"
            },
            'risk_metrics': {
                'max_drawdown': f"{result.max_drawdown}%",
                'sharpe_ratio': result.sharpe_ratio
            },
            'trading_simulation': {
                'profit_loss': f"₹{result.profit_loss:,.2f}",
                'profit_loss_percent': f"{result.profit_loss_percent}%"
            },
            'notable_predictions': {
                'best': result.best_prediction,
                'worst': result.worst_prediction
            },
            'recommendation': self._generate_recommendation(result),
            'generated_at': datetime.now().isoformat()
        }
        
        return report
    
    def _generate_recommendation(self, result: BacktestResult) -> str:
        """Generate recommendation based on backtest results."""
        if result.direction_accuracy >= 60 and result.profit_loss > 0:
            return "GOOD: Model shows promising accuracy. Consider for live testing."
        elif result.direction_accuracy >= 55:
            return "MODERATE: Model shows some predictive power. Needs improvement."
        else:
            return "POOR: Model needs significant improvement before deployment."
    
    def compare_models(
        self, 
        results: List[BacktestResult]
    ) -> pd.DataFrame:
        """
        Compare multiple backtest results.
        
        Args:
            results: List of BacktestResult objects
            
        Returns:
            DataFrame comparing all models
        """
        comparison = []
        for r in results:
            comparison.append({
                'Symbol': r.symbol,
                'Period': f"{r.start_date[:10]} - {r.end_date[:10]}",
                'Predictions': r.total_predictions,
                'Direction %': r.direction_accuracy,
                'MAE': r.mean_absolute_error,
                'MAPE %': r.mean_percentage_error,
                'P&L %': r.profit_loss_percent,
                'Sharpe': r.sharpe_ratio,
                'Win Rate %': r.win_rate
            })
        
        return pd.DataFrame(comparison)
    
    def plot_backtest_results(
        self, 
        predictions: pd.DataFrame,
        actual_prices: pd.Series
    ) -> Dict:
        """
        Generate data for plotting backtest results.
        
        Returns chart data that can be used by frontend.
        """
        chart_data = []
        
        for _, row in predictions.iterrows():
            date = row.get('date')
            predicted = row.get('predicted_price')
            
            if date in actual_prices.index:
                actual = actual_prices[date]
                chart_data.append({
                    'date': str(date),
                    'actual': round(actual, 2),
                    'predicted': round(predicted, 2),
                    'error': round(abs(predicted - actual), 2)
                })
        
        return {
            'chart_data': chart_data,
            'metrics': {
                'correlation': predictions['predicted_price'].corr(
                    actual_prices.reindex(predictions['date'])
                ) if len(predictions) > 1 else 0
            }
        }


# Demo function for testing
def run_demo_backtest():
    """Run a demo backtest with synthetic data."""
    # Generate synthetic data
    dates = pd.date_range(start='2026-01-01', periods=30, freq='B')
    base_price = 2500
    
    actual = pd.Series(
        [base_price + np.random.randn() * 50 + i * 2 for i in range(30)],
        index=dates
    )
    
    predictions = pd.DataFrame({
        'date': dates.tolist(),
        'predicted_price': [p + np.random.randn() * 30 for p in actual.values]
    })
    
    backtester = Backtester()
    result = backtester.backtest_predictions("RELIANCE", predictions, actual)
    report = backtester.generate_backtest_report(result)
    
    return report


if __name__ == "__main__":
    report = run_demo_backtest()
    print(json.dumps(report, indent=2, default=str))
