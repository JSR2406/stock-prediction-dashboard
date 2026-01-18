"""
Analysis Routes
API endpoints for technical analysis and market status.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime, date
import yfinance as yf
import pandas as pd

from ..utils.technical_indicators import TechnicalIndicators, analyze_stock, SignalResult
from ..utils.market_utils import MarketUtils, NSE_HOLIDAYS_2026
from ..utils.cache import cache_manager


router = APIRouter(prefix="/analysis", tags=["Technical Analysis"])


# Response Models
class IndicatorDescription(BaseModel):
    """Description of a technical indicator."""
    name: str
    value: Any
    interpretation: str
    signal: Optional[str] = None


class TechnicalAnalysisResponse(BaseModel):
    """Full technical analysis response."""
    symbol: str
    timestamp: datetime
    current_price: float
    indicators: Dict[str, Any]
    signals: Dict[str, Any]
    overall_signal: str
    confidence: float
    
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class SignalResponse(BaseModel):
    """Trading signals response."""
    symbol: str
    overall: str
    confidence: float
    signals: Dict[str, Dict[str, Any]]
    recommendation: str


class SupportResistanceResponse(BaseModel):
    """Support and resistance levels."""
    symbol: str
    current_price: float
    support_levels: list
    resistance_levels: list
    pivot_points: Dict[str, float]


class MarketStatusResponse(BaseModel):
    """Market status response."""
    status: str
    is_trading: bool
    message: str
    next_open: Optional[str]
    next_close: Optional[str]
    holidays: list


# Helper functions
def fetch_stock_data(symbol: str, period: str = "6mo") -> pd.DataFrame:
    """Fetch stock data from Yahoo Finance."""
    ticker = yf.Ticker(f"{symbol}.NS")
    df = ticker.history(period=period)
    
    if df.empty:
        # Try BSE
        ticker = yf.Ticker(f"{symbol}.BO")
        df = ticker.history(period=period)
    
    if df.empty:
        raise HTTPException(status_code=404, detail=f"No data found for symbol: {symbol}")
    
    return df


def interpret_rsi(value: float) -> str:
    """Interpret RSI value."""
    if value > 70:
        return "Overbought - Consider selling or waiting for pullback"
    elif value < 30:
        return "Oversold - Consider buying opportunity"
    elif value > 60:
        return "Bullish momentum"
    elif value < 40:
        return "Bearish momentum"
    else:
        return "Neutral momentum"


def interpret_macd(histogram: float) -> str:
    """Interpret MACD histogram."""
    if histogram > 0:
        return "Bullish - MACD above signal line"
    elif histogram < 0:
        return "Bearish - MACD below signal line"
    else:
        return "Neutral - At crossover point"


# Routes
@router.get("/{symbol}/technical", response_model=TechnicalAnalysisResponse)
async def get_technical_analysis(
    symbol: str,
    period: str = Query("6mo", description="Data period: 1mo, 3mo, 6mo, 1y")
):
    """
    Get comprehensive technical analysis for a symbol.
    
    Returns all major technical indicators including:
    - RSI, MACD, Stochastic (Momentum)
    - SMA, EMA, ADX (Trend)
    - Bollinger Bands, ATR (Volatility)
    - OBV, VWAP (Volume)
    
    **Parameters:**
    - **symbol**: NSE stock symbol (e.g., RELIANCE, TCS)
    - **period**: Historical data period
    
    **Example:**
    ```
    GET /api/v1/analysis/RELIANCE/technical
    ```
    """
    # Check cache
    cache_key = f"technical_{symbol}_{period}"
    cached = await cache_manager.get(cache_key)
    if cached:
        return cached
    
    try:
        df = fetch_stock_data(symbol, period)
        
        close = df['Close']
        high = df['High']
        low = df['Low']
        volume = df['Volume']
        
        # Calculate all indicators
        ti = TechnicalIndicators
        
        # Momentum
        rsi = ti.calculate_rsi(close)
        macd = ti.calculate_macd(close)
        stoch = ti.calculate_stochastic(high, low, close)
        
        # Trend
        smas = ti.calculate_sma(close, [20, 50, 200])
        emas = ti.calculate_ema(close, [12, 26])
        adx = ti.calculate_adx(high, low, close)
        
        # Volatility
        bb = ti.calculate_bollinger_bands(close)
        atr = ti.calculate_atr(high, low, close)
        
        # Volume
        obv = ti.calculate_obv(close, volume)
        vwap = ti.calculate_vwap(high, low, close, volume)
        
        # Trend identification
        trend = ti.identify_trend(close)
        
        # Generate signals
        signals = ti.generate_signals(close, high, low, volume)
        overall = ti.get_overall_signal(signals)
        
        current_price = float(close.iloc[-1])
        
        response = TechnicalAnalysisResponse(
            symbol=symbol,
            timestamp=datetime.now(),
            current_price=current_price,
            indicators={
                "momentum": {
                    "rsi": {
                        "value": round(float(rsi.iloc[-1]), 2),
                        "interpretation": interpret_rsi(float(rsi.iloc[-1]))
                    },
                    "macd": {
                        "macd_line": round(float(macd['macd_line'].iloc[-1]), 2),
                        "signal_line": round(float(macd['signal_line'].iloc[-1]), 2),
                        "histogram": round(float(macd['histogram'].iloc[-1]), 2),
                        "interpretation": interpret_macd(float(macd['histogram'].iloc[-1]))
                    },
                    "stochastic": {
                        "k": round(float(stoch['k'].iloc[-1]), 2),
                        "d": round(float(stoch['d'].iloc[-1]), 2)
                    }
                },
                "trend": {
                    "sma_20": round(float(smas['sma_20'].iloc[-1]), 2),
                    "sma_50": round(float(smas['sma_50'].iloc[-1]), 2) if not pd.isna(smas['sma_50'].iloc[-1]) else None,
                    "sma_200": round(float(smas['sma_200'].iloc[-1]), 2) if not pd.isna(smas['sma_200'].iloc[-1]) else None,
                    "ema_12": round(float(emas['ema_12'].iloc[-1]), 2),
                    "ema_26": round(float(emas['ema_26'].iloc[-1]), 2),
                    "adx": round(float(adx['adx'].iloc[-1]), 2),
                    "trend_direction": trend
                },
                "volatility": {
                    "bollinger_upper": round(float(bb['upper'].iloc[-1]), 2),
                    "bollinger_middle": round(float(bb['middle'].iloc[-1]), 2),
                    "bollinger_lower": round(float(bb['lower'].iloc[-1]), 2),
                    "bollinger_bandwidth": round(float(bb['bandwidth'].iloc[-1]), 2),
                    "atr": round(float(atr.iloc[-1]), 2)
                },
                "volume": {
                    "obv": round(float(obv.iloc[-1]), 0),
                    "vwap": round(float(vwap.iloc[-1]), 2)
                }
            },
            signals={k: {"signal": v.signal, "strength": v.strength, "reason": v.reason} 
                     for k, v in signals.items()},
            overall_signal=overall.signal,
            confidence=overall.strength
        )
        
        # Cache for 5 minutes
        await cache_manager.set(cache_key, response.model_dump(), ttl=300)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/{symbol}/signals", response_model=SignalResponse)
async def get_trading_signals(symbol: str):
    """
    Get buy/sell/hold signals for a symbol.
    
    Analyzes multiple technical indicators and provides:
    - Individual signal for each indicator
    - Weighted overall signal
    - Confidence score
    - Trade recommendation
    
    **Parameters:**
    - **symbol**: NSE stock symbol
    
    **Example:**
    ```
    GET /api/v1/analysis/TCS/signals
    ```
    """
    cache_key = f"signals_{symbol}"
    cached = await cache_manager.get(cache_key)
    if cached:
        return cached
    
    try:
        df = fetch_stock_data(symbol, "3mo")
        
        close = df['Close']
        high = df['High']
        low = df['Low']
        volume = df['Volume']
        
        signals = TechnicalIndicators.generate_signals(close, high, low, volume)
        overall = TechnicalIndicators.get_overall_signal(signals)
        
        # Generate recommendation
        if overall.signal == "buy" and overall.strength > 70:
            recommendation = "Strong Buy - Multiple indicators showing bullish signals"
        elif overall.signal == "buy":
            recommendation = "Buy - Moderate bullish signals, consider entry"
        elif overall.signal == "sell" and overall.strength > 70:
            recommendation = "Strong Sell - Multiple indicators showing bearish signals"
        elif overall.signal == "sell":
            recommendation = "Sell - Moderate bearish signals, consider exit"
        else:
            recommendation = "Hold - Mixed signals, wait for clearer direction"
        
        response = SignalResponse(
            symbol=symbol,
            overall=overall.signal,
            confidence=overall.strength,
            signals={k: {"signal": v.signal, "strength": v.strength, "reason": v.reason} 
                     for k, v in signals.items()},
            recommendation=recommendation
        )
        
        await cache_manager.set(cache_key, response.model_dump(), ttl=300)
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Signal generation failed: {str(e)}")


@router.get("/{symbol}/support-resistance", response_model=SupportResistanceResponse)
async def get_support_resistance(symbol: str):
    """
    Get key support and resistance levels for a symbol.
    
    Identifies:
    - Support levels (local minima)
    - Resistance levels (local maxima)
    - Pivot points (daily)
    
    **Parameters:**
    - **symbol**: NSE stock symbol
    
    **Example:**
    ```
    GET /api/v1/analysis/INFY/support-resistance
    ```
    """
    cache_key = f"sr_{symbol}"
    cached = await cache_manager.get(cache_key)
    if cached:
        return cached
    
    try:
        df = fetch_stock_data(symbol, "3mo")
        
        close = df['Close']
        high = df['High']
        low = df['Low']
        
        # Find support/resistance
        sr = TechnicalIndicators.find_support_resistance(close, window=5, num_levels=5)
        
        # Calculate pivot points from last trading day
        pivot = TechnicalIndicators.calculate_pivot_points(
            float(high.iloc[-1]),
            float(low.iloc[-1]),
            float(close.iloc[-1])
        )
        
        response = SupportResistanceResponse(
            symbol=symbol,
            current_price=float(close.iloc[-1]),
            support_levels=sr['support'],
            resistance_levels=sr['resistance'],
            pivot_points=pivot
        )
        
        await cache_manager.set(cache_key, response.model_dump(), ttl=300)
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Support/Resistance calculation failed: {str(e)}")


@router.get("/market-status", response_model=MarketStatusResponse)
async def get_market_status():
    """
    Get current NSE market status.
    
    Returns:
    - Current status (pre_market, open, closed, post_market)
    - Next trading session times
    - Upcoming holidays
    
    **Example:**
    ```
    GET /api/v1/analysis/market-status
    ```
    """
    status = MarketUtils.get_market_status()
    
    # Get upcoming holidays
    today = date.today()
    upcoming_holidays = [
        {"date": h.isoformat(), "name": name}
        for h, name in [(d, n["name"]) for n in MarketUtils.indian_market_holidays_2026() 
                        for d in [n["date"]] if d >= today][:5]
    ]
    
    # Simplified holiday list
    holidays_list = []
    for holiday in MarketUtils.indian_market_holidays_2026():
        if holiday["date"] >= today:
            holidays_list.append({
                "date": holiday["date"].isoformat(),
                "name": holiday["name"]
            })
            if len(holidays_list) >= 5:
                break
    
    return MarketStatusResponse(
        status=status.status,
        is_trading=status.is_trading,
        message=status.message,
        next_open=status.next_open.isoformat() if status.next_open else None,
        next_close=status.next_close.isoformat() if status.next_close else None,
        holidays=holidays_list
    )


@router.get("/{symbol}/returns")
async def get_returns(symbol: str):
    """
    Get returns for various time periods.
    
    Calculates:
    - Daily, weekly, monthly, quarterly, yearly returns
    - Sharpe ratio
    - Maximum drawdown
    - Volatility
    """
    try:
        df = fetch_stock_data(symbol, "1y")
        close = df['Close']
        
        # Calculate metrics
        returns = MarketUtils.calculate_returns(close, [1, 7, 30, 90, 365])
        
        daily_returns = close.pct_change().dropna()
        sharpe = MarketUtils.calculate_sharpe_ratio(daily_returns)
        max_dd = MarketUtils.calculate_max_drawdown(close)
        volatility = MarketUtils.calculate_volatility(close)
        
        return {
            "symbol": symbol,
            "current_price": round(float(close.iloc[-1]), 2),
            "returns": returns,
            "sharpe_ratio": sharpe,
            "max_drawdown": max_dd["max_drawdown"],
            "volatility": volatility,
            "metrics_period": "1 year"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Returns calculation failed: {str(e)}")
