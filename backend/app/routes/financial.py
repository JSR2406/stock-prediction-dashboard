"""
Financial Routes
API endpoints for Financial Datasets integration - fundamentals, prices, news, and SEC filings.
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel

from app.services.financial_datasets_service import financial_datasets_client, FinancialDatasetsClient
from app.utils.cache import cache_manager
from app.utils.logging import logger


router = APIRouter(prefix="/financial", tags=["Financial Data"])


# ==================== Response Models ====================

class FundamentalsResponse(BaseModel):
    """Response model for fundamental data."""
    success: bool
    data: dict
    source: str = "financial_datasets"


class PriceResponse(BaseModel):
    """Response model for price data."""
    success: bool
    data: dict
    source: str = "financial_datasets"


class NewsResponse(BaseModel):
    """Response model for news data."""
    success: bool
    data: list
    source: str = "financial_datasets"


class RatiosResponse(BaseModel):
    """Response model for financial ratios."""
    success: bool
    data: dict
    source: str = "financial_datasets"


# ==================== Dependency ====================

def get_client() -> FinancialDatasetsClient:
    """Dependency to get Financial Datasets client."""
    return financial_datasets_client


# ==================== Fundamental Data Endpoints ====================

@router.get("/{symbol}/income-statement")
async def get_income_statement(
    symbol: str,
    period: str = Query("annual", description="Period: annual, quarterly, or ttm"),
    limit: int = Query(4, description="Number of statements to return", ge=1, le=20),
    client: FinancialDatasetsClient = Depends(get_client)
):
    """
    Get income statements for a company.
    
    **Parameters:**
    - **symbol**: Stock ticker symbol (e.g., AAPL, GOOGL, MSFT)
    - **period**: Period type - annual, quarterly, or ttm
    - **limit**: Number of statements to return (1-20)
    
    **Example:**
    ```
    GET /api/v1/financial/AAPL/income-statement?period=annual&limit=4
    ```
    """
    cache_key = f"financial:income:{symbol}:{period}:{limit}"
    cached = await cache_manager.get(cache_key)
    if cached:
        return cached
    
    try:
        logger.info("get_income_statement", symbol=symbol, period=period)
        data = await client.get_income_statements(symbol.upper(), period, limit)
        
        if not data:
            raise HTTPException(status_code=404, detail=f"No income statements found for {symbol}")
        
        response = {
            "success": True,
            "data": {
                "ticker": symbol.upper(),
                "period": period,
                "income_statements": data,
                "count": len(data)
            },
            "source": "financial_datasets"
        }
        
        await cache_manager.set(cache_key, response, ttl=86400)  # 24 hours
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("income_statement_error", symbol=symbol, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{symbol}/balance-sheet")
async def get_balance_sheet(
    symbol: str,
    period: str = Query("annual", description="Period: annual, quarterly, or ttm"),
    limit: int = Query(4, description="Number of statements to return", ge=1, le=20),
    client: FinancialDatasetsClient = Depends(get_client)
):
    """
    Get balance sheets for a company.
    
    **Parameters:**
    - **symbol**: Stock ticker symbol
    - **period**: Period type - annual, quarterly, or ttm
    - **limit**: Number of statements to return
    """
    cache_key = f"financial:balance:{symbol}:{period}:{limit}"
    cached = await cache_manager.get(cache_key)
    if cached:
        return cached
    
    try:
        logger.info("get_balance_sheet", symbol=symbol, period=period)
        data = await client.get_balance_sheets(symbol.upper(), period, limit)
        
        if not data:
            raise HTTPException(status_code=404, detail=f"No balance sheets found for {symbol}")
        
        response = {
            "success": True,
            "data": {
                "ticker": symbol.upper(),
                "period": period,
                "balance_sheets": data,
                "count": len(data)
            },
            "source": "financial_datasets"
        }
        
        await cache_manager.set(cache_key, response, ttl=86400)  # 24 hours
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("balance_sheet_error", symbol=symbol, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{symbol}/cash-flow")
async def get_cash_flow(
    symbol: str,
    period: str = Query("annual", description="Period: annual, quarterly, or ttm"),
    limit: int = Query(4, description="Number of statements to return", ge=1, le=20),
    client: FinancialDatasetsClient = Depends(get_client)
):
    """
    Get cash flow statements for a company.
    
    **Parameters:**
    - **symbol**: Stock ticker symbol
    - **period**: Period type - annual, quarterly, or ttm
    - **limit**: Number of statements to return
    """
    cache_key = f"financial:cashflow:{symbol}:{period}:{limit}"
    cached = await cache_manager.get(cache_key)
    if cached:
        return cached
    
    try:
        logger.info("get_cash_flow", symbol=symbol, period=period)
        data = await client.get_cash_flow_statements(symbol.upper(), period, limit)
        
        if not data:
            raise HTTPException(status_code=404, detail=f"No cash flow statements found for {symbol}")
        
        response = {
            "success": True,
            "data": {
                "ticker": symbol.upper(),
                "period": period,
                "cash_flow_statements": data,
                "count": len(data)
            },
            "source": "financial_datasets"
        }
        
        await cache_manager.set(cache_key, response, ttl=86400)  # 24 hours
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("cash_flow_error", symbol=symbol, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{symbol}/fundamentals")
async def get_fundamentals(
    symbol: str,
    period: str = Query("annual", description="Period: annual, quarterly, or ttm"),
    limit: int = Query(4, description="Number of statements to return", ge=1, le=20),
    client: FinancialDatasetsClient = Depends(get_client)
):
    """
    Get all fundamental data for a company (income statement, balance sheet, cash flow).
    
    **Parameters:**
    - **symbol**: Stock ticker symbol (e.g., AAPL, GOOGL, MSFT)
    - **period**: Period type - annual, quarterly, or ttm
    - **limit**: Number of statements per type to return
    
    **Example:**
    ```
    GET /api/v1/financial/AAPL/fundamentals?period=annual&limit=4
    ```
    """
    cache_key = f"financial:fundamentals:{symbol}:{period}:{limit}"
    cached = await cache_manager.get(cache_key)
    if cached:
        return cached
    
    try:
        logger.info("get_fundamentals", symbol=symbol, period=period)
        data = await client.get_fundamentals(symbol.upper(), period, limit)
        
        response = {
            "success": True,
            "data": data,
            "source": "financial_datasets"
        }
        
        await cache_manager.set(cache_key, response, ttl=86400)  # 24 hours
        return response
        
    except Exception as e:
        logger.error("fundamentals_error", symbol=symbol, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Price Endpoints ====================

@router.get("/{symbol}/price")
async def get_current_price(
    symbol: str,
    client: FinancialDatasetsClient = Depends(get_client)
):
    """
    Get current stock price.
    
    **Parameters:**
    - **symbol**: Stock ticker symbol
    
    **Example:**
    ```
    GET /api/v1/financial/AAPL/price
    ```
    """
    cache_key = f"financial:price:{symbol}"
    cached = await cache_manager.get(cache_key)
    if cached:
        return cached
    
    try:
        logger.info("get_current_price", symbol=symbol)
        data = await client.get_current_stock_price(symbol.upper())
        
        if not data:
            raise HTTPException(status_code=404, detail=f"No price data found for {symbol}")
        
        response = {
            "success": True,
            "data": {
                "ticker": symbol.upper(),
                "snapshot": data,
                "fetched_at": datetime.utcnow().isoformat() + "Z"
            },
            "source": "financial_datasets"
        }
        
        await cache_manager.set(cache_key, response, ttl=60)  # 1 minute
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("price_error", symbol=symbol, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{symbol}/history")
async def get_price_history(
    symbol: str,
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    interval: str = Query("day", description="Interval: minute, hour, day, week, month"),
    client: FinancialDatasetsClient = Depends(get_client)
):
    """
    Get historical stock prices.
    
    **Parameters:**
    - **symbol**: Stock ticker symbol
    - **start_date**: Start date (YYYY-MM-DD format)
    - **end_date**: End date (YYYY-MM-DD format)
    - **interval**: Data interval - minute, hour, day, week, month
    
    **Example:**
    ```
    GET /api/v1/financial/AAPL/history?start_date=2024-01-01&end_date=2024-12-31&interval=day
    ```
    """
    cache_key = f"financial:history:{symbol}:{start_date}:{end_date}:{interval}"
    cached = await cache_manager.get(cache_key)
    if cached:
        return cached
    
    try:
        logger.info("get_price_history", symbol=symbol, start_date=start_date, end_date=end_date)
        data = await client.get_historical_stock_prices(
            symbol.upper(), start_date, end_date, interval
        )
        
        if not data:
            raise HTTPException(status_code=404, detail=f"No historical data found for {symbol}")
        
        response = {
            "success": True,
            "data": {
                "ticker": symbol.upper(),
                "start_date": start_date,
                "end_date": end_date,
                "interval": interval,
                "prices": data,
                "count": len(data)
            },
            "source": "financial_datasets"
        }
        
        await cache_manager.set(cache_key, response, ttl=3600)  # 1 hour
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("history_error", symbol=symbol, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ==================== News Endpoint ====================

@router.get("/{symbol}/news")
async def get_news(
    symbol: str,
    client: FinancialDatasetsClient = Depends(get_client)
):
    """
    Get company news articles.
    
    **Parameters:**
    - **symbol**: Stock ticker symbol
    
    **Example:**
    ```
    GET /api/v1/financial/AAPL/news
    ```
    """
    cache_key = f"financial:news:{symbol}"
    cached = await cache_manager.get(cache_key)
    if cached:
        return cached
    
    try:
        logger.info("get_news", symbol=symbol)
        data = await client.get_company_news(symbol.upper())
        
        response = {
            "success": True,
            "data": {
                "ticker": symbol.upper(),
                "news": data,
                "count": len(data)
            },
            "source": "financial_datasets"
        }
        
        await cache_manager.set(cache_key, response, ttl=900)  # 15 minutes
        return response
        
    except Exception as e:
        logger.error("news_error", symbol=symbol, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ==================== SEC Filings Endpoint ====================

@router.get("/{symbol}/filings")
async def get_filings(
    symbol: str,
    filing_type: Optional[str] = Query(None, description="Filing type: 10-K, 10-Q, 8-K, etc."),
    limit: int = Query(10, description="Number of filings to return", ge=1, le=50),
    client: FinancialDatasetsClient = Depends(get_client)
):
    """
    Get SEC filings for a company.
    
    **Parameters:**
    - **symbol**: Stock ticker symbol
    - **filing_type**: Type of filing (10-K, 10-Q, 8-K, etc.)
    - **limit**: Number of filings to return
    
    **Example:**
    ```
    GET /api/v1/financial/AAPL/filings?type=10-K&limit=5
    ```
    """
    cache_key = f"financial:filings:{symbol}:{filing_type}:{limit}"
    cached = await cache_manager.get(cache_key)
    if cached:
        return cached
    
    try:
        logger.info("get_filings", symbol=symbol, filing_type=filing_type)
        data = await client.get_sec_filings(symbol.upper(), limit, filing_type)
        
        response = {
            "success": True,
            "data": {
                "ticker": symbol.upper(),
                "filings": data,
                "count": len(data)
            },
            "source": "financial_datasets"
        }
        
        await cache_manager.set(cache_key, response, ttl=21600)  # 6 hours
        return response
        
    except Exception as e:
        logger.error("filings_error", symbol=symbol, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Financial Ratios ====================

@router.get("/{symbol}/ratios")
async def get_ratios(
    symbol: str,
    client: FinancialDatasetsClient = Depends(get_client)
):
    """
    Get calculated financial ratios for a company.
    
    Calculates key ratios from fundamental data:
    - P/E Ratio, P/B Ratio
    - ROE, ROA
    - Debt/Equity, Current Ratio
    - Profit Margin, Operating Margin
    
    **Parameters:**
    - **symbol**: Stock ticker symbol
    
    **Example:**
    ```
    GET /api/v1/financial/AAPL/ratios
    ```
    """
    cache_key = f"financial:ratios:{symbol}"
    cached = await cache_manager.get(cache_key)
    if cached:
        return cached
    
    try:
        logger.info("get_ratios", symbol=symbol)
        data = await client.calculate_financial_ratios(symbol.upper())
        
        response = {
            "success": True,
            "data": data,
            "source": "financial_datasets"
        }
        
        await cache_manager.set(cache_key, response, ttl=3600)  # 1 hour
        return response
        
    except Exception as e:
        logger.error("ratios_error", symbol=symbol, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Crypto Endpoints ====================

@router.get("/crypto/tickers")
async def get_crypto_tickers(
    client: FinancialDatasetsClient = Depends(get_client)
):
    """
    Get list of available cryptocurrency tickers.
    
    **Example:**
    ```
    GET /api/v1/financial/crypto/tickers
    ```
    """
    cache_key = "financial:crypto:tickers"
    cached = await cache_manager.get(cache_key)
    if cached:
        return cached
    
    try:
        logger.info("get_crypto_tickers")
        data = await client.get_available_crypto_tickers()
        
        response = {
            "success": True,
            "data": {
                "tickers": data,
                "count": len(data)
            },
            "source": "financial_datasets"
        }
        
        await cache_manager.set(cache_key, response, ttl=86400)  # 24 hours
        return response
        
    except Exception as e:
        logger.error("crypto_tickers_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/crypto/{symbol}/price")
async def get_crypto_price(
    symbol: str,
    client: FinancialDatasetsClient = Depends(get_client)
):
    """
    Get current cryptocurrency price.
    
    **Parameters:**
    - **symbol**: Crypto ticker symbol (e.g., BTC-USD, ETH-USD)
    
    **Example:**
    ```
    GET /api/v1/financial/crypto/BTC-USD/price
    ```
    """
    cache_key = f"financial:crypto:price:{symbol}"
    cached = await cache_manager.get(cache_key)
    if cached:
        return cached
    
    try:
        logger.info("get_crypto_price", symbol=symbol)
        data = await client.get_current_crypto_price(symbol.upper())
        
        if not data:
            raise HTTPException(status_code=404, detail=f"No price data found for {symbol}")
        
        response = {
            "success": True,
            "data": {
                "ticker": symbol.upper(),
                "snapshot": data,
                "fetched_at": datetime.utcnow().isoformat() + "Z"
            },
            "source": "financial_datasets"
        }
        
        await cache_manager.set(cache_key, response, ttl=30)  # 30 seconds
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("crypto_price_error", symbol=symbol, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/crypto/{symbol}/history")
async def get_crypto_history(
    symbol: str,
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    interval: str = Query("day", description="Interval: minute, hour, day, week, month"),
    client: FinancialDatasetsClient = Depends(get_client)
):
    """
    Get historical cryptocurrency prices.
    
    **Parameters:**
    - **symbol**: Crypto ticker symbol (e.g., BTC-USD)
    - **start_date**: Start date (YYYY-MM-DD format)
    - **end_date**: End date (YYYY-MM-DD format)
    - **interval**: Data interval
    
    **Example:**
    ```
    GET /api/v1/financial/crypto/BTC-USD/history?start_date=2024-01-01&end_date=2024-12-31
    ```
    """
    cache_key = f"financial:crypto:history:{symbol}:{start_date}:{end_date}:{interval}"
    cached = await cache_manager.get(cache_key)
    if cached:
        return cached
    
    try:
        logger.info("get_crypto_history", symbol=symbol, start_date=start_date, end_date=end_date)
        data = await client.get_crypto_prices(
            symbol.upper(), start_date, end_date, interval
        )
        
        if not data:
            raise HTTPException(status_code=404, detail=f"No historical data found for {symbol}")
        
        response = {
            "success": True,
            "data": {
                "ticker": symbol.upper(),
                "start_date": start_date,
                "end_date": end_date,
                "interval": interval,
                "prices": data,
                "count": len(data)
            },
            "source": "financial_datasets"
        }
        
        await cache_manager.set(cache_key, response, ttl=3600)  # 1 hour
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("crypto_history_error", symbol=symbol, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
