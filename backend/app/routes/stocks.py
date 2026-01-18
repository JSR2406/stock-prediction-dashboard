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
        data = await data_fetcher.fetch_stock_data(symbol, period="5d", exchange=exchange.value)
        result = {
            "success": True,
            "data": {
                "symbol": data["symbol"],
                "name": data["name"],
                "exchange": data["exchange"],
                "current_price": data["current_price"],
                "previous_close": data["previous_close"],
                "open_price": data["open_price"],
                "high": data["high"],
                "low": data["low"],
                "volume": data["volume"],
                "change": data["change"],
                "change_percent": data["change_percent"],
                "trend": data["trend"],
                "market_cap": data.get("market_cap"),
                "pe_ratio": data.get("pe_ratio"),
                "week_52_high": data.get("week_52_high"),
                "week_52_low": data.get("week_52_low"),
                "market_status": get_market_status()
            },
            "last_updated": data["last_updated"]
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
        data = await data_fetcher.fetch_stock_data(symbol, period=period, exchange=exchange.value)
        result = {
            "success": True,
            "symbol": data["symbol"],
            "name": data["name"],
            "exchange": data["exchange"],
            "period": period,
            "historical": data.get("historical", []),
            "last_updated": data["last_updated"]
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
