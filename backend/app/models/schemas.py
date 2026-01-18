"""
Pydantic Models/Schemas for API Request/Response Validation
Defines all data structures used across the application.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator, model_validator


# ============== Enums ==============

class MarketType(str, Enum):
    """Supported market types."""
    NSE = "NSE"
    BSE = "BSE"
    CRYPTO = "CRYPTO"
    COMMODITY = "COMMODITY"


class TrendDirection(str, Enum):
    """Price trend direction."""
    UP = "up"
    DOWN = "down"
    NEUTRAL = "neutral"


class TimeFrame(str, Enum):
    """Supported time frames for data."""
    HOUR_1 = "1h"
    HOUR_4 = "4h"
    DAY_1 = "1d"
    WEEK_1 = "1w"
    MONTH_1 = "1mo"
    YEAR_1 = "1y"


class PredictionHorizon(str, Enum):
    """Prediction time horizons."""
    DAY_1 = "1d"
    WEEK_1 = "1w"
    MONTH_1 = "1mo"


# ============== Base Models ==============

class BaseResponse(BaseModel):
    """Base response model with common fields."""
    success: bool = Field(default=True, description="Request success status")
    message: Optional[str] = Field(default=None, description="Optional response message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class PaginationMeta(BaseModel):
    """Pagination metadata."""
    page: int = Field(ge=1, description="Current page number")
    per_page: int = Field(ge=1, le=100, description="Items per page")
    total_items: int = Field(ge=0, description="Total number of items")
    total_pages: int = Field(ge=0, description="Total number of pages")


# ============== Stock Models ==============

class StockQuote(BaseModel):
    """Real-time stock quote data."""
    symbol: str = Field(..., min_length=1, max_length=20, description="Stock symbol")
    name: str = Field(..., description="Company name")
    exchange: MarketType = Field(..., description="Stock exchange")
    current_price: float = Field(..., ge=0, description="Current stock price")
    previous_close: float = Field(..., ge=0, description="Previous closing price")
    open_price: float = Field(..., ge=0, description="Opening price")
    high: float = Field(..., ge=0, description="Day high")
    low: float = Field(..., ge=0, description="Day low")
    volume: int = Field(..., ge=0, description="Trading volume")
    change: float = Field(..., description="Price change")
    change_percent: float = Field(..., description="Price change percentage")
    trend: TrendDirection = Field(..., description="Price trend direction")
    market_cap: Optional[float] = Field(default=None, ge=0, description="Market capitalization")
    pe_ratio: Optional[float] = Field(default=None, description="P/E ratio")
    week_52_high: Optional[float] = Field(default=None, ge=0, description="52-week high")
    week_52_low: Optional[float] = Field(default=None, ge=0, description="52-week low")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update time")
    
    @field_validator("symbol")
    @classmethod
    def uppercase_symbol(cls, v: str) -> str:
        """Convert symbol to uppercase."""
        return v.upper().strip()
    
    @model_validator(mode="after")
    def validate_price_range(self) -> "StockQuote":
        """Validate that low <= current_price <= high for the day."""
        if self.low > self.high:
            raise ValueError("Low price cannot be greater than high price")
        return self


class StockHistoricalData(BaseModel):
    """Historical stock data point."""
    date: datetime = Field(..., description="Data point date")
    open: float = Field(..., ge=0, description="Opening price")
    high: float = Field(..., ge=0, description="High price")
    low: float = Field(..., ge=0, description="Low price")
    close: float = Field(..., ge=0, description="Closing price")
    volume: int = Field(..., ge=0, description="Trading volume")
    adjusted_close: Optional[float] = Field(default=None, ge=0, description="Adjusted closing price")


class StockResponse(BaseResponse):
    """Complete stock data response."""
    data: StockQuote = Field(..., description="Stock quote data")
    historical: Optional[List[StockHistoricalData]] = Field(
        default=None, 
        description="Historical price data"
    )


class StockListResponse(BaseResponse):
    """List of stocks response with pagination."""
    data: List[StockQuote] = Field(..., description="List of stock quotes")
    pagination: Optional[PaginationMeta] = Field(default=None, description="Pagination metadata")


# ============== Prediction Models ==============

class PredictionDataPoint(BaseModel):
    """Single prediction data point."""
    date: datetime = Field(..., description="Predicted date")
    predicted_price: float = Field(..., ge=0, description="Predicted price")
    lower_bound: float = Field(..., ge=0, description="Lower confidence bound")
    upper_bound: float = Field(..., ge=0, description="Upper confidence bound")
    confidence: float = Field(..., ge=0, le=100, description="Confidence percentage")


class PredictionMetrics(BaseModel):
    """Model prediction metrics."""
    mse: float = Field(..., ge=0, description="Mean Squared Error")
    rmse: float = Field(..., ge=0, description="Root Mean Squared Error")
    mae: float = Field(..., ge=0, description="Mean Absolute Error")
    mape: float = Field(..., ge=0, description="Mean Absolute Percentage Error")
    r2_score: float = Field(..., ge=-1, le=1, description="R-squared score")
    accuracy: float = Field(..., ge=0, le=100, description="Direction accuracy percentage")


class PredictionRequest(BaseModel):
    """Prediction request parameters."""
    symbol: str = Field(..., min_length=1, max_length=20, description="Stock/asset symbol")
    market: MarketType = Field(default=MarketType.NSE, description="Market type")
    horizon: PredictionHorizon = Field(default=PredictionHorizon.WEEK_1, description="Prediction horizon")
    include_confidence: bool = Field(default=True, description="Include confidence intervals")
    
    @field_validator("symbol")
    @classmethod
    def uppercase_symbol(cls, v: str) -> str:
        """Convert symbol to uppercase."""
        return v.upper().strip()


class PredictionResponse(BaseResponse):
    """Prediction response with forecasted data."""
    symbol: str = Field(..., description="Asset symbol")
    market: MarketType = Field(..., description="Market type")
    current_price: float = Field(..., ge=0, description="Current price")
    predictions: List[PredictionDataPoint] = Field(..., description="List of predictions")
    trend: TrendDirection = Field(..., description="Predicted trend")
    metrics: Optional[PredictionMetrics] = Field(default=None, description="Model metrics")
    model_version: str = Field(default="1.0.0", description="ML model version")


# ============== Crypto Models ==============

class CryptoData(BaseModel):
    """Cryptocurrency data."""
    id: str = Field(..., description="Crypto ID (e.g., bitcoin)")
    symbol: str = Field(..., min_length=1, max_length=10, description="Crypto symbol")
    name: str = Field(..., description="Cryptocurrency name")
    current_price: float = Field(..., ge=0, description="Current price in USD")
    price_inr: Optional[float] = Field(default=None, ge=0, description="Current price in INR")
    market_cap: float = Field(..., ge=0, description="Market capitalization")
    market_cap_rank: int = Field(..., ge=1, description="Market cap ranking")
    total_volume: float = Field(..., ge=0, description="24h trading volume")
    high_24h: float = Field(..., ge=0, description="24h high")
    low_24h: float = Field(..., ge=0, description="24h low")
    price_change_24h: float = Field(..., description="24h price change")
    price_change_percentage_24h: float = Field(..., description="24h price change %")
    price_change_percentage_7d: Optional[float] = Field(default=None, description="7d price change %")
    price_change_percentage_30d: Optional[float] = Field(default=None, description="30d price change %")
    circulating_supply: Optional[float] = Field(default=None, ge=0, description="Circulating supply")
    total_supply: Optional[float] = Field(default=None, ge=0, description="Total supply")
    max_supply: Optional[float] = Field(default=None, ge=0, description="Maximum supply")
    ath: Optional[float] = Field(default=None, ge=0, description="All-time high")
    ath_date: Optional[datetime] = Field(default=None, description="All-time high date")
    image: Optional[str] = Field(default=None, description="Crypto logo URL")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update time")
    trend: TrendDirection = Field(default=TrendDirection.NEUTRAL, description="Price trend")
    
    @field_validator("symbol")
    @classmethod
    def uppercase_symbol(cls, v: str) -> str:
        """Convert symbol to uppercase."""
        return v.upper().strip()


class CryptoListResponse(BaseResponse):
    """List of cryptocurrencies response."""
    data: List[CryptoData] = Field(..., description="List of crypto data")
    total_market_cap: Optional[float] = Field(default=None, description="Total crypto market cap")


# ============== Commodity Models ==============

class CommodityData(BaseModel):
    """Commodity/metals data."""
    symbol: str = Field(..., description="Commodity symbol (e.g., XAU for Gold)")
    name: str = Field(..., description="Commodity name")
    price_usd: float = Field(..., ge=0, description="Price in USD per unit")
    price_inr: Optional[float] = Field(default=None, ge=0, description="Price in INR per unit")
    unit: str = Field(default="oz", description="Price unit (oz, kg, etc.)")
    change_24h: float = Field(..., description="24h price change")
    change_percentage_24h: float = Field(..., description="24h change percentage")
    high_24h: Optional[float] = Field(default=None, ge=0, description="24h high")
    low_24h: Optional[float] = Field(default=None, ge=0, description="24h low")
    trend: TrendDirection = Field(default=TrendDirection.NEUTRAL, description="Price trend")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update time")


class CommodityResponse(BaseResponse):
    """Single commodity response."""
    data: CommodityData = Field(..., description="Commodity data")


class CommodityListResponse(BaseResponse):
    """List of commodities response."""
    data: List[CommodityData] = Field(..., description="List of commodity data")
    base_currency: str = Field(default="USD", description="Base currency for prices")


# ============== Market Overview Models ==============

class MarketIndex(BaseModel):
    """Market index data."""
    symbol: str = Field(..., description="Index symbol")
    name: str = Field(..., description="Index name")
    value: float = Field(..., ge=0, description="Current index value")
    change: float = Field(..., description="Change from previous close")
    change_percent: float = Field(..., description="Change percentage")
    trend: TrendDirection = Field(..., description="Trend direction")
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class TopMover(BaseModel):
    """Top gainer/loser stock."""
    symbol: str = Field(..., description="Stock symbol")
    name: str = Field(..., description="Company name")
    price: float = Field(..., ge=0, description="Current price")
    change_percent: float = Field(..., description="Change percentage")
    volume: int = Field(..., ge=0, description="Trading volume")


class MarketSentiment(BaseModel):
    """Market sentiment indicators."""
    overall: str = Field(..., description="Overall sentiment: bullish, bearish, neutral")
    fear_greed_index: Optional[int] = Field(default=None, ge=0, le=100, description="Fear & Greed index")
    advancing: int = Field(..., ge=0, description="Number of advancing stocks")
    declining: int = Field(..., ge=0, description="Number of declining stocks")
    unchanged: int = Field(..., ge=0, description="Number of unchanged stocks")


class MarketOverview(BaseResponse):
    """Complete market overview."""
    indices: List[MarketIndex] = Field(..., description="Major market indices")
    top_gainers: List[TopMover] = Field(..., description="Top gaining stocks")
    top_losers: List[TopMover] = Field(..., description="Top losing stocks")
    most_active: List[TopMover] = Field(..., description="Most actively traded")
    sentiment: MarketSentiment = Field(..., description="Market sentiment")
    market_status: str = Field(..., description="Market status: open, closed, pre-market, after-hours")
    last_updated: datetime = Field(default_factory=datetime.utcnow)


# ============== Error Models ==============

class ErrorDetail(BaseModel):
    """Detailed error information."""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    field: Optional[str] = Field(default=None, description="Field causing error")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")


class ErrorResponse(BaseModel):
    """Standard error response."""
    success: bool = Field(default=False)
    error: ErrorDetail = Field(..., description="Error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = Field(default=None, description="Request tracking ID")


# ============== Health Check Models ==============

class ServiceHealth(BaseModel):
    """Individual service health status."""
    name: str = Field(..., description="Service name")
    status: str = Field(..., description="Status: healthy, degraded, unhealthy")
    latency_ms: Optional[float] = Field(default=None, description="Response latency in ms")
    message: Optional[str] = Field(default=None, description="Status message")


class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Overall status: healthy, degraded, unhealthy")
    version: str = Field(..., description="API version")
    environment: str = Field(..., description="Environment: development, production")
    services: List[ServiceHealth] = Field(..., description="Individual service statuses")
    uptime_seconds: float = Field(..., ge=0, description="Server uptime in seconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
