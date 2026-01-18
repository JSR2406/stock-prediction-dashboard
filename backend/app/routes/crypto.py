"""
Crypto Routes - Enhanced API endpoints for cryptocurrency data.
"""

from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Query, Request, HTTPException

from app.services.data_fetcher import data_fetcher
from app.utils.rate_limiter import limiter
from app.utils.logging import logger
from app.utils.cache import cache_manager

router = APIRouter(prefix="/crypto", tags=["Cryptocurrency"])


@router.get("/top")
@limiter.limit("60/minute")
async def get_top_crypto(
    request: Request,
    limit: int = Query(default=10, ge=1, le=50)
):
    """Get top cryptocurrencies by market cap."""
    cache_key = f"crypto:top:{limit}"
    cached_data = await cache_manager.get(cache_key)
    
    if cached_data:
        return cached_data
    
    try:
        data = await data_fetcher.fetch_crypto_data()
        result = {
            "success": True,
            "data": data[:limit],
            "total_count": len(data),
            "currency": "INR",
            "last_updated": datetime.utcnow().isoformat() + "Z"
        }
        await cache_manager.set(cache_key, result, ttl=120)
        return result
    except Exception as e:
        logger.error("crypto_top_error", error=str(e))
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/list")
@limiter.limit("60/minute")
async def get_crypto_list(
    request: Request,
    ids: Optional[str] = Query(default=None, description="Comma-separated crypto IDs")
):
    """Get list of cryptocurrencies."""
    crypto_ids = ids.split(",") if ids else None
    
    cache_key = f"crypto:list:{ids or 'default'}"
    cached_data = await cache_manager.get(cache_key)
    
    if cached_data:
        return cached_data
    
    try:
        data = await data_fetcher.fetch_crypto_data(symbols=crypto_ids)
        result = {
            "success": True,
            "data": data,
            "currency": "INR",
            "last_updated": datetime.utcnow().isoformat() + "Z"
        }
        await cache_manager.set(cache_key, result, ttl=120)
        return result
    except Exception as e:
        logger.error("crypto_list_error", error=str(e))
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/{crypto_id}")
@limiter.limit("60/minute")
async def get_crypto_detail(request: Request, crypto_id: str):
    """Get detailed cryptocurrency data."""
    cache_key = f"crypto:detail:{crypto_id}"
    cached_data = await cache_manager.get(cache_key)
    
    if cached_data:
        return cached_data
    
    try:
        data = await data_fetcher.fetch_crypto_data(symbols=[crypto_id.lower()])
        
        if not data:
            raise HTTPException(status_code=404, detail=f"Crypto '{crypto_id}' not found")
        
        result = {
            "success": True,
            "data": data[0],
            "currency": "INR",
            "last_updated": datetime.utcnow().isoformat() + "Z"
        }
        await cache_manager.set(cache_key, result, ttl=120)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("crypto_detail_error", crypto_id=crypto_id, error=str(e))
        raise HTTPException(status_code=502, detail=str(e))
