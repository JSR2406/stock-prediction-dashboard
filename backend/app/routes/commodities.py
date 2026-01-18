"""
Commodities Routes - Enhanced API endpoints for commodities/metals data.
"""

from datetime import datetime
from fastapi import APIRouter, Query, Request, HTTPException

from app.services.data_fetcher import data_fetcher
from app.utils.rate_limiter import limiter
from app.utils.logging import logger
from app.utils.cache import cache_manager

router = APIRouter(prefix="/commodities", tags=["Commodities"])


@router.get("/gold")
@limiter.limit("60/minute")
async def get_gold_price(request: Request):
    """Get current gold price in INR."""
    cache_key = "commodities:gold"
    cached_data = await cache_manager.get(cache_key)
    
    if cached_data:
        return cached_data
    
    try:
        data = await data_fetcher.fetch_gold_silver()
        result = {
            "success": True,
            "data": data["gold"],
            "exchange_rate": data.get("exchange_rate"),
            "last_updated": data["last_updated"]
        }
        await cache_manager.set(cache_key, result, ttl=900)
        return result
    except Exception as e:
        logger.error("gold_fetch_error", error=str(e))
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/silver")
@limiter.limit("60/minute")
async def get_silver_price(request: Request):
    """Get current silver price in INR."""
    cache_key = "commodities:silver"
    cached_data = await cache_manager.get(cache_key)
    
    if cached_data:
        return cached_data
    
    try:
        data = await data_fetcher.fetch_gold_silver()
        result = {
            "success": True,
            "data": data["silver"],
            "exchange_rate": data.get("exchange_rate"),
            "last_updated": data["last_updated"]
        }
        await cache_manager.set(cache_key, result, ttl=900)
        return result
    except Exception as e:
        logger.error("silver_fetch_error", error=str(e))
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/all")
@limiter.limit("60/minute")
async def get_all_commodities(request: Request):
    """Get all commodities prices."""
    cache_key = "commodities:all"
    cached_data = await cache_manager.get(cache_key)
    
    if cached_data:
        return cached_data
    
    try:
        data = await data_fetcher.fetch_gold_silver()
        result = {
            "success": True,
            "data": [data["gold"], data["silver"]],
            "exchange_rate_usd_inr": data.get("exchange_rate"),
            "base_currency": "INR",
            "last_updated": data["last_updated"]
        }
        await cache_manager.set(cache_key, result, ttl=900)
        return result
    except Exception as e:
        logger.error("commodities_all_error", error=str(e))
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/list")
@limiter.limit("60/minute")
async def get_commodities_list(request: Request):
    """Get list of all tracked commodities."""
    return await get_all_commodities(request)
