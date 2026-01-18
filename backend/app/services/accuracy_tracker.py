"""
Accuracy Tracker Service
Tracks and updates prediction accuracy over time.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

import yfinance as yf
from sqlalchemy.orm import Session

from ..database import get_db_context, crud
from ..database.models import PredictionHistory, DailyAccuracy

logger = logging.getLogger(__name__)


@dataclass
class AccuracyReport:
    """Daily accuracy report."""
    date: str
    total_predictions: int
    correct_directions: int
    direction_accuracy: float
    avg_error_percent: float
    by_model: Dict[str, Dict]


class AccuracyTracker:
    """
    Tracks prediction accuracy by comparing predictions to actual prices.
    
    Usage:
        tracker = AccuracyTracker()
        await tracker.update_daily_accuracy()
        report = tracker.generate_accuracy_report("weekly")
    """
    
    def __init__(self):
        self.last_update: Optional[datetime] = None
    
    async def update_daily_accuracy(self) -> Dict:
        """
        Update prediction accuracy for yesterday's predictions.
        Compares predicted prices with actual closing prices.
        
        Returns:
            Dict with update statistics
        """
        with get_db_context() as db:
            # Find predictions where target date has passed
            predictions = crud.get_predictions_needing_update(db)
            
            if not predictions:
                logger.info("No predictions to update")
                return {"updated": 0, "errors": 0}
            
            updated = 0
            errors = 0
            
            # Group by symbol for efficient fetching
            symbols = set(p.symbol for p in predictions)
            
            for symbol in symbols:
                try:
                    # Fetch actual prices
                    ticker = yf.Ticker(f"{symbol}.NS")
                    history = ticker.history(period="5d")
                    
                    if history.empty:
                        continue
                    
                    symbol_predictions = [p for p in predictions if p.symbol == symbol]
                    
                    for pred in symbol_predictions:
                        target_date = pred.target_date.date() if hasattr(pred.target_date, 'date') else pred.target_date
                        
                        # Find closing price for target date
                        for idx, row in history.iterrows():
                            if idx.date() == target_date:
                                actual_price = row['Close']
                                crud.update_prediction_accuracy(db, pred.id, actual_price)
                                updated += 1
                                break
                                
                except Exception as e:
                    logger.error(f"Error updating accuracy for {symbol}: {e}")
                    errors += 1
            
            self.last_update = datetime.now()
            
            logger.info(f"Accuracy update complete: {updated} updated, {errors} errors")
            
            return {
                "updated": updated,
                "errors": errors,
                "timestamp": self.last_update.isoformat()
            }
    
    def generate_accuracy_report(
        self, 
        period: str = "weekly",
        symbol: Optional[str] = None
    ) -> AccuracyReport:
        """
        Generate accuracy report for specified period.
        
        Args:
            period: "daily", "weekly", or "monthly"
            symbol: Optional specific symbol
            
        Returns:
            AccuracyReport with aggregated metrics
        """
        days = {"daily": 1, "weekly": 7, "monthly": 30}.get(period, 7)
        
        with get_db_context() as db:
            if symbol:
                metrics = crud.calculate_model_accuracy(db, symbol, days=days)
            else:
                # Aggregate across all symbols
                performers = crud.get_best_performing_stocks(db, limit=100)
                
                if not performers:
                    return AccuracyReport(
                        date=datetime.now().isoformat(),
                        total_predictions=0,
                        correct_directions=0,
                        direction_accuracy=0,
                        avg_error_percent=0,
                        by_model={}
                    )
                
                total_pred = sum(p['total_predictions'] for p in performers)
                weighted_accuracy = sum(
                    p['direction_accuracy'] * p['total_predictions'] 
                    for p in performers
                ) / total_pred if total_pred > 0 else 0
                
                avg_error = sum(p['average_error_percent'] for p in performers) / len(performers)
                
                return AccuracyReport(
                    date=datetime.now().isoformat(),
                    total_predictions=total_pred,
                    correct_directions=int(total_pred * weighted_accuracy / 100),
                    direction_accuracy=round(weighted_accuracy, 2),
                    avg_error_percent=round(avg_error, 2),
                    by_model={}
                )
    
    def identify_best_prediction_window(
        self, 
        symbol: str
    ) -> Dict:
        """
        Identify which prediction horizon (1d, 3d, 7d) is most accurate.
        
        Args:
            symbol: Stock symbol to analyze
            
        Returns:
            Dict with accuracy by time horizon
        """
        # For now, return demo data
        # In production, would analyze actual prediction history
        return {
            "symbol": symbol,
            "best_horizon": "3d",
            "accuracy_by_horizon": {
                "1d": 72.5,
                "3d": 75.8,
                "7d": 68.2
            },
            "recommendation": "3-day predictions show highest accuracy"
        }
    
    async def alert_low_accuracy(
        self, 
        threshold: float = 60.0
    ) -> List[Dict]:
        """
        Identify stocks with accuracy below threshold.
        
        Args:
            threshold: Minimum acceptable accuracy percentage
            
        Returns:
            List of stocks with low accuracy
        """
        alerts = []
        
        with get_db_context() as db:
            performers = crud.get_best_performing_stocks(db, limit=100)
            
            for stock in performers:
                if stock['direction_accuracy'] < threshold:
                    alerts.append({
                        "symbol": stock['symbol'],
                        "current_accuracy": stock['direction_accuracy'],
                        "threshold": threshold,
                        "action_required": "Review model performance",
                        "severity": "high" if stock['direction_accuracy'] < 50 else "medium"
                    })
        
        if alerts:
            logger.warning(f"Low accuracy alert: {len(alerts)} stocks below {threshold}%")
        
        return alerts
    
    async def run_scheduled_update(self, interval_hours: int = 24):
        """
        Run accuracy updates on a schedule.
        
        Args:
            interval_hours: Hours between updates
        """
        while True:
            try:
                await self.update_daily_accuracy()
                
                # Check for low accuracy
                alerts = await self.alert_low_accuracy()
                if alerts:
                    # In production, would send notifications
                    logger.warning(f"Low accuracy stocks: {[a['symbol'] for a in alerts]}")
                    
            except Exception as e:
                logger.error(f"Scheduled accuracy update failed: {e}")
            
            await asyncio.sleep(interval_hours * 3600)


# Global tracker instance
accuracy_tracker = AccuracyTracker()


async def start_accuracy_tracking():
    """Start background accuracy tracking."""
    await accuracy_tracker.run_scheduled_update()
