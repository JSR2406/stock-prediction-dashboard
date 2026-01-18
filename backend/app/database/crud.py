"""
CRUD operations for database models.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_

from .models import Stock, PredictionHistory, ModelMetrics, DailyAccuracy, UserWatchlist


# ============== Stock CRUD ==============

def get_stock(db: Session, symbol: str) -> Optional[Stock]:
    """Get stock by symbol."""
    return db.query(Stock).filter(Stock.symbol == symbol.upper()).first()


def get_stocks(db: Session, skip: int = 0, limit: int = 100) -> List[Stock]:
    """Get all stocks with pagination."""
    return db.query(Stock).filter(Stock.is_active == True).offset(skip).limit(limit).all()


def create_stock(db: Session, symbol: str, name: str, **kwargs) -> Stock:
    """Create a new stock."""
    stock = Stock(symbol=symbol.upper(), name=name, **kwargs)
    db.add(stock)
    db.commit()
    db.refresh(stock)
    return stock


def update_stock(db: Session, symbol: str, **kwargs) -> Optional[Stock]:
    """Update stock attributes."""
    stock = get_stock(db, symbol)
    if stock:
        for key, value in kwargs.items():
            if hasattr(stock, key):
                setattr(stock, key, value)
        stock.last_updated = datetime.utcnow()
        db.commit()
        db.refresh(stock)
    return stock


# ============== Prediction CRUD ==============

def save_prediction(
    db: Session,
    symbol: str,
    predicted_price: float,
    target_date: datetime,
    model_type: str = "ensemble",
    confidence: float = 0.0,
    **kwargs
) -> PredictionHistory:
    """Save a new prediction."""
    prediction = PredictionHistory(
        symbol=symbol.upper(),
        prediction_date=datetime.utcnow(),
        target_date=target_date,
        predicted_price=predicted_price,
        model_type=model_type,
        confidence_score=confidence,
        **kwargs
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    return prediction


def get_prediction_history(
    db: Session,
    symbol: str,
    days: int = 30
) -> List[PredictionHistory]:
    """Get prediction history for a symbol."""
    start_date = datetime.utcnow() - timedelta(days=days)
    return (
        db.query(PredictionHistory)
        .filter(
            PredictionHistory.symbol == symbol.upper(),
            PredictionHistory.prediction_date >= start_date
        )
        .order_by(desc(PredictionHistory.prediction_date))
        .all()
    )


def update_prediction_accuracy(
    db: Session,
    prediction_id: int,
    actual_price: float
) -> Optional[PredictionHistory]:
    """Update prediction with actual price and calculate accuracy."""
    prediction = db.query(PredictionHistory).get(prediction_id)
    if prediction:
        prediction.actual_price = actual_price
        prediction.error_amount = abs(prediction.predicted_price - actual_price)
        prediction.error_percent = (prediction.error_amount / actual_price) * 100
        
        # Direction accuracy (would need previous close to calculate properly)
        # For now, simplified version
        prediction.direction_correct = (
            (prediction.predicted_price > actual_price * 0.99) and 
            (prediction.predicted_price < actual_price * 1.01)
        )
        
        db.commit()
        db.refresh(prediction)
    return prediction


def get_predictions_needing_update(db: Session) -> List[PredictionHistory]:
    """Get predictions where target date has passed but actual price is missing."""
    return (
        db.query(PredictionHistory)
        .filter(
            PredictionHistory.target_date < datetime.utcnow(),
            PredictionHistory.actual_price.is_(None)
        )
        .all()
    )


def calculate_model_accuracy(
    db: Session,
    symbol: str,
    model_type: Optional[str] = None,
    days: int = 30
) -> Dict[str, Any]:
    """Calculate prediction accuracy for a symbol."""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    query = db.query(PredictionHistory).filter(
        PredictionHistory.symbol == symbol.upper(),
        PredictionHistory.prediction_date >= start_date,
        PredictionHistory.actual_price.isnot(None)
    )
    
    if model_type:
        query = query.filter(PredictionHistory.model_type == model_type)
    
    predictions = query.all()
    
    if not predictions:
        return {"total": 0, "accuracy": 0}
    
    total = len(predictions)
    correct = sum(1 for p in predictions if p.direction_correct)
    avg_error = sum(p.error_percent for p in predictions) / total
    
    return {
        "symbol": symbol.upper(),
        "total_predictions": total,
        "direction_accuracy": round((correct / total) * 100, 2),
        "average_error_percent": round(avg_error, 2),
        "period_days": days
    }


# ============== Model Metrics CRUD ==============

def save_model_metrics(
    db: Session,
    symbol: str,
    model_type: str,
    rmse: float,
    mae: float,
    mape: float,
    r_squared: float,
    **kwargs
) -> ModelMetrics:
    """Save model training metrics."""
    # Deactivate previous active model
    db.query(ModelMetrics).filter(
        ModelMetrics.symbol == symbol.upper(),
        ModelMetrics.model_type == model_type,
        ModelMetrics.is_active == True
    ).update({"is_active": False})
    
    metrics = ModelMetrics(
        symbol=symbol.upper(),
        model_type=model_type,
        rmse=rmse,
        mae=mae,
        mape=mape,
        r_squared=r_squared,
        is_active=True,
        **kwargs
    )
    db.add(metrics)
    db.commit()
    db.refresh(metrics)
    return metrics


def get_model_metrics(
    db: Session,
    symbol: str,
    model_type: Optional[str] = None
) -> List[ModelMetrics]:
    """Get model metrics for a symbol."""
    query = db.query(ModelMetrics).filter(ModelMetrics.symbol == symbol.upper())
    if model_type:
        query = query.filter(ModelMetrics.model_type == model_type)
    return query.order_by(desc(ModelMetrics.training_date)).all()


def get_active_models(db: Session) -> List[ModelMetrics]:
    """Get all currently active models."""
    return (
        db.query(ModelMetrics)
        .filter(ModelMetrics.is_active == True)
        .all()
    )


# ============== Best Performers ==============

def get_best_performing_stocks(
    db: Session,
    limit: int = 10,
    min_predictions: int = 5
) -> List[Dict[str, Any]]:
    """Get stocks with highest prediction accuracy."""
    # Subquery for accuracy calculation
    results = (
        db.query(
            PredictionHistory.symbol,
            func.count(PredictionHistory.id).label('total'),
            func.avg(PredictionHistory.error_percent).label('avg_error'),
            func.sum(func.cast(PredictionHistory.direction_correct, db.Integer)).label('correct')
        )
        .filter(PredictionHistory.actual_price.isnot(None))
        .group_by(PredictionHistory.symbol)
        .having(func.count(PredictionHistory.id) >= min_predictions)
        .all()
    )
    
    performers = []
    for symbol, total, avg_error, correct in results:
        accuracy = (correct / total) * 100 if total > 0 else 0
        performers.append({
            "symbol": symbol,
            "total_predictions": total,
            "direction_accuracy": round(accuracy, 2),
            "average_error_percent": round(avg_error, 2) if avg_error else 0
        })
    
    # Sort by accuracy
    performers.sort(key=lambda x: x['direction_accuracy'], reverse=True)
    return performers[:limit]


# ============== Watchlist CRUD ==============

def add_to_watchlist(
    db: Session,
    user_id: str,
    symbol: str,
    **kwargs
) -> UserWatchlist:
    """Add stock to user's watchlist."""
    existing = db.query(UserWatchlist).filter(
        UserWatchlist.user_id == user_id,
        UserWatchlist.symbol == symbol.upper()
    ).first()
    
    if existing:
        return existing
    
    item = UserWatchlist(
        user_id=user_id,
        symbol=symbol.upper(),
        **kwargs
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def remove_from_watchlist(db: Session, user_id: str, symbol: str) -> bool:
    """Remove stock from user's watchlist."""
    result = db.query(UserWatchlist).filter(
        UserWatchlist.user_id == user_id,
        UserWatchlist.symbol == symbol.upper()
    ).delete()
    db.commit()
    return result > 0


def get_user_watchlist(db: Session, user_id: str) -> List[UserWatchlist]:
    """Get user's watchlist."""
    return (
        db.query(UserWatchlist)
        .filter(UserWatchlist.user_id == user_id)
        .order_by(desc(UserWatchlist.added_at))
        .all()
    )
