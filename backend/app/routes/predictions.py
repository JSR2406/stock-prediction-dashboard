"""
Predictions Routes - Real data-based ML prediction endpoints.
Uses technical analysis and historical data for stock, crypto, and commodity predictions.
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Request, HTTPException, Body, Query
from pydantic import BaseModel

from app.services.real_data_predictor import real_data_predictor
from app.utils.rate_limiter import limiter
from app.utils.logging import logger
from app.utils.cache import cache_manager

router = APIRouter(prefix="/predictions", tags=["Predictions"])


class BatchPredictionRequest(BaseModel):
    symbols: List[str]


# ============== Stock Predictions ==============

@router.get("/{symbol}")
@limiter.limit("30/minute")
async def get_prediction(
    request: Request, 
    symbol: str,
    exchange: str = Query(default="NSE", description="Exchange: NSE or BSE")
):
    """
    Get next-day prediction for a stock using real market data.
    
    - **symbol**: Stock symbol (e.g., RELIANCE, TCS, INFY)
    - **exchange**: NSE or BSE (default: NSE)
    
    Returns predicted price based on technical analysis of real historical data.
    """
    symbol = symbol.upper()
    cache_key = f"prediction:daily:{symbol}:{exchange}"
    cached_data = await cache_manager.get(cache_key)
    
    if cached_data:
        return cached_data
    
    logger.info("get_prediction", symbol=symbol, exchange=exchange)
    
    try:
        result = await real_data_predictor.predict_next_day(symbol, exchange)
        
        if result is None:
            raise HTTPException(
                status_code=404, 
                detail=f"Could not fetch data for {symbol}. Please check the symbol."
            )
        
        response = {"success": True, "data": result}
        await cache_manager.set(cache_key, response, ttl=900)  # 15 min cache
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("prediction_error", symbol=symbol, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{symbol}/weekly")
@limiter.limit("20/minute")
async def get_weekly_prediction(
    request: Request, 
    symbol: str,
    exchange: str = Query(default="NSE", description="Exchange: NSE or BSE")
):
    """
    Get 7-day forecast for a stock using real market data.
    
    - **symbol**: Stock symbol
    - **exchange**: NSE or BSE
    
    Returns daily predictions for the next 7 trading days.
    """
    symbol = symbol.upper()
    cache_key = f"prediction:weekly:{symbol}:{exchange}"
    cached_data = await cache_manager.get(cache_key)
    
    if cached_data:
        return cached_data
    
    logger.info("get_weekly_prediction", symbol=symbol, exchange=exchange)
    
    try:
        result = await real_data_predictor.predict_weekly(symbol, exchange)
        
        if result is None:
            raise HTTPException(
                status_code=404, 
                detail=f"Could not fetch data for {symbol}"
            )
        
        response = {"success": True, "data": result}
        await cache_manager.set(cache_key, response, ttl=1800)  # 30 min cache
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("weekly_prediction_error", symbol=symbol, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch")
@limiter.limit("10/minute")
async def get_batch_predictions(
    request: Request,
    body: BatchPredictionRequest,
    exchange: str = Query(default="NSE", description="Exchange: NSE or BSE")
):
    """
    Get predictions for multiple stocks using real market data.
    
    - **symbols**: List of stock symbols (max 10)
    - **exchange**: NSE or BSE
    """
    logger.info("batch_prediction", symbols=body.symbols, exchange=exchange)
    
    results = []
    for symbol in body.symbols[:10]:  # Limit to 10
        try:
            result = await real_data_predictor.predict_next_day(symbol.upper(), exchange)
            if result:
                results.append(result)
            else:
                results.append({
                    "symbol": symbol.upper(),
                    "status": "error",
                    "message": f"No data available for {symbol}"
                })
        except Exception as e:
            results.append({
                "symbol": symbol.upper(),
                "status": "error",
                "message": str(e)
            })
    
    return {
        "success": True,
        "data": {
            "predictions": results,
            "requested": len(body.symbols),
            "processed": len(results),
            "exchange": exchange,
            "generated_at": datetime.utcnow().isoformat() + "Z"
        }
    }


# ============== Commodity Predictions ==============

@router.get("/commodity/{commodity}")
@limiter.limit("30/minute")
async def get_commodity_prediction(request: Request, commodity: str):
    """
    Get next-day prediction for a commodity.
    
    - **commodity**: gold, silver, crude_oil, platinum, copper
    
    Returns prediction in both USD and INR.
    """
    cache_key = f"prediction:commodity:{commodity.lower()}"
    cached_data = await cache_manager.get(cache_key)
    
    if cached_data:
        return cached_data
    
    logger.info("get_commodity_prediction", commodity=commodity)
    
    try:
        result = await real_data_predictor.predict_commodity(commodity)
        
        if result is None:
            raise HTTPException(
                status_code=404, 
                detail=f"Commodity '{commodity}' not found. Valid options: gold, silver, crude_oil, platinum, copper"
            )
        
        response = {"success": True, "data": result}
        await cache_manager.set(cache_key, response, ttl=1800)  # 30 min cache
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("commodity_prediction_error", commodity=commodity, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/commodities/all")
@limiter.limit("15/minute")
async def get_all_commodity_predictions(request: Request):
    """
    Get predictions for all supported commodities (Gold, Silver, Crude Oil).
    """
    cache_key = "prediction:commodities:all"
    cached_data = await cache_manager.get(cache_key)
    
    if cached_data:
        return cached_data
    
    logger.info("get_all_commodity_predictions")
    
    commodities = ["gold", "silver", "crude_oil"]
    results = []
    
    for commodity in commodities:
        try:
            result = await real_data_predictor.predict_commodity(commodity)
            if result:
                results.append(result)
        except Exception as e:
            logger.error("commodity_prediction_error", commodity=commodity, error=str(e))
    
    response = {
        "success": True,
        "data": {
            "predictions": results,
            "count": len(results),
            "generated_at": datetime.utcnow().isoformat() + "Z"
        }
    }
    
    await cache_manager.set(cache_key, response, ttl=1800)
    return response


# ============== Crypto Predictions ==============

@router.get("/crypto/{crypto_id}")
@limiter.limit("30/minute")
async def get_crypto_prediction(request: Request, crypto_id: str):
    """
    Get next-day prediction for a cryptocurrency.
    
    - **crypto_id**: bitcoin, ethereum, solana, cardano, ripple, dogecoin, etc.
    
    Returns prediction in both USD and INR.
    """
    cache_key = f"prediction:crypto:{crypto_id.lower()}"
    cached_data = await cache_manager.get(cache_key)
    
    if cached_data:
        return cached_data
    
    logger.info("get_crypto_prediction", crypto_id=crypto_id)
    
    try:
        result = await real_data_predictor.predict_crypto(crypto_id)
        
        if result is None:
            raise HTTPException(
                status_code=404, 
                detail=f"Cryptocurrency '{crypto_id}' not found or no data available"
            )
        
        response = {"success": True, "data": result}
        await cache_manager.set(cache_key, response, ttl=900)  # 15 min cache
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("crypto_prediction_error", crypto_id=crypto_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/crypto/top/predictions")
@limiter.limit("10/minute")
async def get_top_crypto_predictions(request: Request):
    """
    Get predictions for top 10 cryptocurrencies by market cap.
    """
    cache_key = "prediction:crypto:top10"
    cached_data = await cache_manager.get(cache_key)
    
    if cached_data:
        return cached_data
    
    logger.info("get_top_crypto_predictions")
    
    top_cryptos = [
        "bitcoin", "ethereum", "binancecoin", "ripple", "cardano",
        "solana", "polkadot", "dogecoin", "avalanche-2", "chainlink"
    ]
    
    results = []
    for crypto_id in top_cryptos:
        try:
            result = await real_data_predictor.predict_crypto(crypto_id)
            if result:
                results.append(result)
        except Exception as e:
            logger.error("crypto_prediction_error", crypto_id=crypto_id, error=str(e))
    
    response = {
        "success": True,
        "data": {
            "predictions": results,
            "count": len(results),
            "generated_at": datetime.utcnow().isoformat() + "Z"
        }
    }
    
    await cache_manager.set(cache_key, response, ttl=900)
    return response


# ============== Model Status ==============

@router.get("/models/status")
@limiter.limit("60/minute")
async def get_models_status(request: Request):
    """Get status of the prediction system."""
    return {
        "success": True,
        "data": {
            "prediction_engine": "real-data-technical-analysis",
            "version": "1.0.0",
            "data_source": "yahoo_finance",
            "capabilities": {
                "stocks": {
                    "exchanges": ["NSE", "BSE"],
                    "prediction_horizon": ["1-day", "7-day"],
                    "features": ["technical_indicators", "price_forecast", "trend_analysis"]
                },
                "crypto": {
                    "supported": ["bitcoin", "ethereum", "solana", "cardano", "ripple", "dogecoin", "avalanche", "polkadot", "chainlink", "binancecoin"],
                    "currencies": ["USD", "INR"],
                    "update_frequency": "real-time"
                },
                "commodities": {
                    "supported": ["gold", "silver", "crude_oil", "platinum", "copper"],
                    "currencies": ["USD", "INR"],
                    "units": ["per gram", "per barrel"]
                }
            },
            "technical_indicators": [
                "RSI (Relative Strength Index)",
                "MACD (Moving Average Convergence Divergence)",
                "Bollinger Bands",
                "SMA (Simple Moving Average)",
                "EMA (Exponential Moving Average)",
                "ATR (Average True Range)",
                "Momentum Indicators"
            ],
            "disclaimer": "Predictions are based on technical analysis of historical data. This is NOT financial advice.",
            "last_checked": datetime.utcnow().isoformat() + "Z"
        }
    }


@router.get("/{symbol}/accuracy")
@limiter.limit("30/minute")
async def get_prediction_accuracy(request: Request, symbol: str):
    """Get prediction methodology information for a symbol."""
    symbol = symbol.upper()
    
    return {
        "success": True,
        "data": {
            "symbol": symbol,
            "methodology": "Technical Analysis",
            "indicators_used": [
                {"name": "RSI", "weight": 0.20, "description": "Relative Strength Index for overbought/oversold signals"},
                {"name": "MACD", "weight": 0.15, "description": "Moving Average Convergence Divergence for trend"},
                {"name": "Bollinger Bands", "weight": 0.15, "description": "Price volatility and reversal signals"},
                {"name": "Moving Averages", "weight": 0.15, "description": "SMA/EMA crossovers for trend direction"},
                {"name": "Momentum", "weight": 0.20, "description": "Price momentum over 5-10 days"},
                {"name": "Volume", "weight": 0.15, "description": "Volume confirmation of price moves"}
            ],
            "confidence_factors": [
                "Low volatility increases confidence",
                "Aligned indicators increase confidence",
                "Strong MACD signals increase confidence",
                "RSI extremes (< 30 or > 70) increase confidence"
            ],
            "limitations": [
                "Predictions are based on historical patterns",
                "Cannot predict black swan events",
                "Market sentiment not fully captured",
                "Longer horizons have lower accuracy"
            ],
            "note": "For best results, use with other analysis methods"
        }
    }
