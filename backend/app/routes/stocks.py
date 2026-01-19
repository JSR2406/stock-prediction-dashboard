"""
Stock Routes - Enhanced API endpoints with caching and data fetcher integration.
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query, Request, HTTPException

from app.models.schemas import (
    StockResponse, StockListResponse, StockQuote, StockHistoricalData,
    MarketType, TrendDirection, TimeFrame, MarketOverview, MarketIndex,
    TopMover, MarketSentiment
)
from app.services.data_fetcher import data_fetcher
from app.services.smart_data_fetcher import smart_data_fetcher
from app.utils.rate_limiter import limiter
from app.utils.logging import logger
from app.utils.cache import cache_manager, cached
from app.utils.market_utils import get_market_status

router = APIRouter(prefix="/stocks", tags=["Stocks"])


@router.get("/nifty")
@limiter.limit("120/minute")
async def get_nifty(request: Request):
    """Get NIFTY 50 index data with live updates."""
    cache_key = "indices:nifty"
    cached_data = await cache_manager.get(cache_key)
    
    if cached_data:
        return cached_data
    
    try:
        data = await data_fetcher.fetch_nifty_sensex()
        result = {
            "success": True,
            **data["nifty50"],
            "market_status": data["market_status"],
            "last_updated": data["last_updated"]
        }
        await cache_manager.set(cache_key, result, ttl=60)
        return result
    except Exception as e:
        logger.error("nifty_fetch_error", error=str(e))
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/sensex")
@limiter.limit("120/minute")
async def get_sensex(request: Request):
    """Get SENSEX index data with live updates."""
    cache_key = "indices:sensex"
    cached_data = await cache_manager.get(cache_key)
    
    if cached_data:
        return cached_data
    
    try:
        data = await data_fetcher.fetch_nifty_sensex()
        result = {
            "success": True,
            **data["sensex"],
            "market_status": data["market_status"],
            "last_updated": data["last_updated"]
        }
        await cache_manager.set(cache_key, result, ttl=60)
        return result
    except Exception as e:
        logger.error("sensex_fetch_error", error=str(e))
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/indices")
@limiter.limit("120/minute")
async def get_all_indices(request: Request):
    """Get all major indices (NIFTY 50 & SENSEX)."""
    cache_key = "indices:all"
    cached_data = await cache_manager.get(cache_key)
    
    if cached_data:
        return cached_data
    
    try:
        data = await data_fetcher.fetch_nifty_sensex()
        result = {"success": True, **data}
        await cache_manager.set(cache_key, result, ttl=60)
        return result
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/top-movers")
@limiter.limit("30/minute")
async def get_top_movers(
    request: Request,
    limit: int = Query(default=10, ge=1, le=20)
):
    """Get top gainers and losers from NSE."""
    cache_key = f"movers:top:{limit}"
    cached_data = await cache_manager.get(cache_key)
    
    if cached_data:
        return cached_data
    
    try:
        data = await data_fetcher.fetch_top_gainers_losers(limit=limit)
        result = {"success": True, **data}
        await cache_manager.set(cache_key, result, ttl=300)
        return result
    except Exception as e:
        logger.error("movers_fetch_error", error=str(e))
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/quote/{symbol}")
@limiter.limit("60/minute")
async def get_stock_quote(
    request: Request,
    symbol: str,
    exchange: MarketType = Query(default=MarketType.NSE)
):
    """Get real-time stock quote."""
    symbol = symbol.upper()
    cache_key = f"stock:quote:{symbol}:{exchange.value}"
    cached_data = await cache_manager.get(cache_key)
    
    if cached_data:
        return cached_data
    
    try:
        # Determine strict suffix for Indian stocks if NSE/BSE
        search_symbol = symbol
        if exchange == MarketType.NSE and not symbol.endswith(".NS"):
            search_symbol = f"{symbol}.NS"
        elif exchange == MarketType.BSE and not symbol.endswith(".BO"):
            search_symbol = f"{symbol}.BO"

        # Use SmartDataFetcher
        data = await smart_data_fetcher.get_stock_price(search_symbol)
        
        # Map response to schema
        result = {
            "success": True,
            "data": {
                "symbol": symbol, # Keep original requested symbol
                "name": data.get("name", symbol),
                "exchange": exchange.value,
                "current_price": data.get("price", 0.0),
                "previous_close": 0.0, # Not always available in simple price call
                "open_price": data.get("open", 0.0),
                "high": data.get("high", 0.0),
                "low": data.get("low", 0.0),
                "volume": data.get("volume", 0),
                "change": data.get("change", 0.0),
                "change_percent": data.get("change_percent", 0.0),
                "trend": "up" if data.get("change", 0) >= 0 else "down",
                "market_cap": None, 
                "pe_ratio": None,
                "week_52_high": None,
                "week_52_low": None,
                "market_status": get_market_status(),
                "source": data.get("source", "unknown")
            },
            "last_updated": datetime.now().isoformat()
        }
        await cache_manager.set(cache_key, result, ttl=300)
        return result
    except Exception as e:
        logger.error("stock_quote_error", symbol=symbol, error=str(e))
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/historical/{symbol}")
@limiter.limit("30/minute")
async def get_stock_historical(
    request: Request,
    symbol: str,
    period: str = Query(default="1y", regex="^(1d|5d|1mo|3mo|6mo|1y|2y|5y|max)$"),
    exchange: MarketType = Query(default=MarketType.NSE)
):
    """Get historical stock data."""
    symbol = symbol.upper()
    cache_key = f"stock:hist:{symbol}:{exchange.value}:{period}"
    cached_data = await cache_manager.get(cache_key)
    
    if cached_data:
        return cached_data
    
    try:
        # Determine suffix
        search_symbol = symbol
        if exchange == MarketType.NSE and not symbol.endswith(".NS"):
            search_symbol = f"{symbol}.NS"
        elif exchange == MarketType.BSE and not symbol.endswith(".BO"):
            search_symbol = f"{symbol}.BO"
            
        # Calc dates for history
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        # Parse period to days
        period_days = 365 # Default
        interval = "1d"
        
        period_map = {
            "1d": 1, "5d": 5, "1mo": 30, "3mo": 90, "6mo": 180, 
            "1y": 365, "2y": 730, "5y": 1825, "max": 365*10
        }
        
        if period in period_map:
            period_days = period_map[period]
            # Adjust interval for short periods
            if period == "1d": interval = "15m"
            elif period == "5d": interval = "1h"
            
        start_date = (datetime.now() - timedelta(days=period_days)).strftime('%Y-%m-%d')
        
        data = await smart_data_fetcher.get_historical_prices(
            search_symbol, 
            start_date=start_date, 
            end_date=end_date,
            interval=interval
        )
        
        result = {
            "success": True,
            "symbol": symbol,
            "name": symbol, # Placeholder
            "exchange": exchange.value,
            "period": period,
            "historical": data,
            "last_updated": datetime.now().isoformat()
        }
        
        # Longer cache for historical data
        ttl = 3600 if period in ["1y", "2y", "5y", "max"] else 900
        await cache_manager.set(cache_key, result, ttl=ttl)
        return result
    except Exception as e:
        logger.error("historical_error", symbol=symbol, error=str(e))
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/search")
@limiter.limit("60/minute") 
async def search_stocks(
    request: Request,
    q: str = Query(..., min_length=1, description="Search query"),
    exchange: Optional[MarketType] = Query(default=None),
    limit: int = Query(default=10, ge=1, le=50)
):
    """Search for stocks by name or symbol."""
    logger.info("search_stocks", query=q, exchange=exchange)
    
    # For demo, return matching stocks from top list
    matching = []
    for symbol in data_fetcher.NSE_TOP_STOCKS:
        if q.upper() in symbol:
            try:
                data = await data_fetcher.fetch_stock_data(symbol, period="1d")
                matching.append({
                    "symbol": data["symbol"],
                    "name": data["name"],
                    "current_price": data["current_price"],
                    "change_percent": data["change_percent"],
                    "trend": data["trend"]
                })
                if len(matching) >= limit:
                    break
            except:
                continue
    
    return {"success": True, "data": matching, "total": len(matching)}


@router.get("/market-overview")
@limiter.limit("60/minute")
async def get_market_overview(request: Request):
    """Get complete market overview."""
    cache_key = "market:overview"
    cached_data = await cache_manager.get(cache_key)
    
    if cached_data:
        return cached_data
    
    try:
        indices = await data_fetcher.fetch_nifty_sensex()
        movers = await data_fetcher.fetch_top_gainers_losers(limit=5)
        
        result = {
            "success": True,
            "indices": [indices["nifty50"], indices["sensex"]],
            "top_gainers": movers["top_gainers"],
            "top_losers": movers["top_losers"],
            "market_status": indices["market_status"],
            "last_updated": datetime.utcnow().isoformat() + "Z"
        }
        
        await cache_manager.set(cache_key, result, ttl=120)
        return result
    except Exception as e:
        logger.error("market_overview_error", error=str(e))
        raise HTTPException(status_code=502, detail=str(e))
