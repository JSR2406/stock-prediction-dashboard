"""
Database Models - SQLAlchemy ORM models for data persistence.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, 
    Text, ForeignKey, Index, JSON,
    create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Stock(Base):
    """Stock master data."""
    __tablename__ = 'stocks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    exchange = Column(String(10), default='NSE')  # NSE, BSE
    sector = Column(String(100))
    industry = Column(String(100))
    market_cap = Column(Float)
    is_active = Column(Boolean, default=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    predictions = relationship("PredictionHistory", back_populates="stock")
    metrics = relationship("ModelMetrics", back_populates="stock")
    
    def __repr__(self):
        return f"<Stock(symbol='{self.symbol}', name='{self.name}')>"


class PredictionHistory(Base):
    """Historical predictions for accuracy tracking."""
    __tablename__ = 'prediction_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    symbol = Column(String(20), nullable=False, index=True)
    
    # Prediction details
    prediction_date = Column(DateTime, nullable=False, index=True)
    target_date = Column(DateTime, nullable=False)
    predicted_price = Column(Float, nullable=False)
    actual_price = Column(Float)  # Filled in after target date
    prediction_type = Column(String(20), default='next_day')  # next_day, weekly
    
    # Model info
    model_version = Column(String(50))
    model_type = Column(String(50))  # lstm, ensemble, etc.
    confidence_score = Column(Float)
    
    # Accuracy metrics (calculated after actual price is known)
    error_amount = Column(Float)
    error_percent = Column(Float)
    direction_correct = Column(Boolean)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    stock = relationship("Stock", back_populates="predictions")
    
    __table_args__ = (
        Index('ix_prediction_symbol_date', 'symbol', 'prediction_date'),
    )
    
    def __repr__(self):
        return f"<PredictionHistory(symbol='{self.symbol}', date='{self.prediction_date}')>"


class UserWatchlist(Base):
    """User watchlist items."""
    __tablename__ = 'user_watchlist'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), nullable=False, index=True)  # Anonymous user ID
    symbol = Column(String(20), nullable=False)
    
    # Alert settings
    alert_enabled = Column(Boolean, default=False)
    target_price = Column(Float)
    alert_type = Column(String(20))  # above, below, percent_change
    
    notes = Column(Text)
    added_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_watchlist_user_symbol', 'user_id', 'symbol', unique=True),
    )


class NewsArticle(Base):
    """Aggregated news articles."""
    __tablename__ = 'news_articles'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    content = Column(Text)
    summary = Column(Text)
    source = Column(String(100))
    url = Column(String(1000))
    
    # Related stocks
    symbols = Column(JSON)  # List of related stock symbols
    
    # Sentiment analysis
    sentiment_score = Column(Float)  # -1 to 1
    sentiment_label = Column(String(20))  # positive, negative, neutral
    
    published_at = Column(DateTime)
    fetched_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_news_published', 'published_at'),
    )


class ModelMetrics(Base):
    """ML model training and performance metrics."""
    __tablename__ = 'model_metrics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'))
    symbol = Column(String(20), nullable=False, index=True)
    
    # Model info
    model_type = Column(String(50), nullable=False)  # lstm, gru, xgboost, ensemble
    model_version = Column(String(50))
    model_path = Column(String(500))
    
    # Training metrics
    rmse = Column(Float)
    mae = Column(Float)
    mape = Column(Float)
    r_squared = Column(Float)
    
    # Training details
    training_samples = Column(Integer)
    epochs = Column(Integer)
    training_duration_seconds = Column(Float)
    
    # Validation metrics
    val_rmse = Column(Float)
    val_mae = Column(Float)
    
    # Dates
    training_date = Column(DateTime, default=datetime.utcnow)
    data_start_date = Column(DateTime)
    data_end_date = Column(DateTime)
    
    # Status
    is_active = Column(Boolean, default=True)  # Currently deployed model
    
    # Relationships
    stock = relationship("Stock", back_populates="metrics")
    
    __table_args__ = (
        Index('ix_metrics_symbol_type', 'symbol', 'model_type'),
    )


class DailyAccuracy(Base):
    """Daily prediction accuracy tracking."""
    __tablename__ = 'daily_accuracy'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False, index=True)
    
    # Aggregate metrics
    total_predictions = Column(Integer, default=0)
    correct_directions = Column(Integer, default=0)
    direction_accuracy = Column(Float)
    
    avg_error_percent = Column(Float)
    median_error_percent = Column(Float)
    
    # By model type (JSON for flexibility)
    metrics_by_model = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_accuracy_date', 'date', unique=True),
    )


class APIUsage(Base):
    """Track API usage for rate limiting and analytics."""
    __tablename__ = 'api_usage'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    client_ip = Column(String(50), index=True)
    endpoint = Column(String(200))
    method = Column(String(10))
    
    # Response metrics
    status_code = Column(Integer)
    response_time_ms = Column(Float)
    
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('ix_usage_ip_time', 'client_ip', 'timestamp'),
    )
