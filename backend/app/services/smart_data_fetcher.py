"""
Smart Data Fetcher
Intelligent data source selection and routing for financial data.
Routes requests to Financial Datasets (US/Crypto) or Yahoo Finance (Indian/Global) based on asset type.
"""

import logging
from typing import Any, Dict, List, Optional
import yfinance as yf
from datetime import datetime
import asyncio

from app.services.financial_datasets_service import financial_datasets_client
from app.utils.logging import logger

class SmartDataFetcher:
    """
    Intelligently routes data requests to the best available source.
    
    Strategies:
    - US Stocks -> Financial Datasets API (Primary)
    - Indian Stocks (.NS/.BO) -> Yahoo Finance
    - Crypto -> Financial Datasets API
    - Fallbacks -> Yahoo Finance
    """
    
    def __init__(self):
        self.primary_client = financial_datasets_client
        self.secondary_source = "yahoo_finance"

    def _is_indian_stock(self, symbol: str) -> bool:
        """Check if symbol belongs to Indian markets."""
        return symbol.endswith(('.NS', '.BO'))

    def _is_crypto(self, symbol: str) -> bool:
        """Check if symbol is a cryptocurrency pair (approximate)."""
        return '-' in symbol and ('USD' in symbol or 'USDT' in symbol)

    def get_best_source(self, symbol: str) -> str:
        """Determine the best data source for a given symbol."""
        if self._is_indian_stock(symbol):
            return "yahoo_finance"
        
        if self._is_crypto(symbol):
            return "financial_datasets"
        
        # Default to Financial Datasets for US stocks (no suffix usually)
        return "financial_datasets"

    async def get_stock_price(self, symbol: str, source: str = "auto") -> Dict[str, Any]:
        """
        Get current stock price from the best source.
        """
        if source == "auto":
            source = self.get_best_source(symbol)
        
        logger.info("smart_fetch_price", symbol=symbol, source=source)
        
        try:
            if source == "financial_datasets":
                return await self._fetch_price_financial_datasets(symbol)
            else:
                return await self._fetch_price_yahoo(symbol)
        except Exception as e:
            logger.error("smart_fetch_error", symbol=symbol, source=source, error=str(e))
            # Fallback
            if source == "financial_datasets":
                logger.info("attempting_fallback", symbol=symbol, fallback="yahoo_finance")
                return await self._fetch_price_yahoo(symbol)
            raise e

    async def get_historical_prices(
        self, 
        symbol: str, 
        start_date: str, 
        end_date: str, 
        interval: str = "1d",
        source: str = "auto"
    ) -> List[Dict[str, Any]]:
        """
        Get historical prices from the best source.
        """
        if source == "auto":
            source = self.get_best_source(symbol)
            
        logger.info("smart_fetch_history", symbol=symbol, source=source)
        
        try:
            if source == "financial_datasets":
                # Map interval 1d/1wk/1mo to standard
                fd_interval = "day"
                if interval in ["1wk", "1week"]: fd_interval = "week"
                if interval in ["1mo", "1month"]: fd_interval = "month"
                
                return await self.primary_client.get_historical_stock_prices(
                    symbol, start_date, end_date, interval=fd_interval
                )
            else:
                return await self._fetch_history_yahoo(symbol, start_date, end_date, interval)
        except Exception as e:
            logger.error("smart_fetch_history_error", symbol=symbol, source=source, error=str(e))
            if source == "financial_datasets":
                 return await self._fetch_history_yahoo(symbol, start_date, end_date, interval)
            raise e

    # ==================== Source Implementations ====================

    async def _fetch_price_financial_datasets(self, symbol: str) -> Dict[str, Any]:
        """Fetch price from Financial Datasets."""
        data = await self.primary_client.get_current_stock_price(symbol)
        if not data:
            raise ValueError(f"No price data found for {symbol}")
        
        return {
            "symbol": symbol,
            "price": data.get("price"),
            "open": data.get("open"),
            "high": data.get("high"),
            "low": data.get("low"),
            "volume": data.get("volume"),
            "change": data.get("change"),
            "change_percent": data.get("change_percent"),
            "source": "financial_datasets"
        }

    async def _fetch_price_yahoo(self, symbol: str) -> Dict[str, Any]:
        """Fetch price from Yahoo Finance."""
        def _get_yf_data():
            ticker = yf.Ticker(symbol)
            # FAST info gives real-time-ish data
            info = ticker.fast_info
            # Regular info for details
            details = ticker.info
            
            # Close price logic
            price = info.last_price
            prev_close = info.previous_close
            change = price - prev_close
            change_p = (change / prev_close) * 100 if prev_close else 0
            
            return {
                "symbol": symbol,
                "price": price,
                "open": info.open,
                "high": info.day_high,
                "low": info.day_low,
                "volume": info.last_volume,
                "change": change,
                "change_percent": change_p,
                "name": details.get("longName", symbol),
                "source": "yahoo_finance"
            }
            
        return await asyncio.to_thread(_get_yf_data)

    async def _fetch_history_yahoo(self, symbol: str, start: str, end: str, interval: str) -> List[Dict[str, Any]]:
        """Fetch history from Yahoo Finance."""
        def _get_yf_hist():
            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=start, end=end, interval=interval)
            
            results = []
            for date, row in hist.iterrows():
                results.append({
                    "date": date.strftime('%Y-%m-%d'),
                    "open": row['Open'],
                    "high": row['High'],
                    "low": row['Low'],
                    "close": row['Close'],
                    "volume": row['Volume']
                })
            return results
            
        return await asyncio.to_thread(_get_yf_hist)
        
    async def get_company_news(self, symbol: str, source: str = "auto") -> List[Dict[str, Any]]:
        """Get company news."""
        if source == "auto":
             source = "financial_datasets" if not self._is_indian_stock(symbol) else "yahoo_finance"
             
        if source == "financial_datasets":
             return await self.primary_client.get_company_news(symbol)
        
        # Yahoo News Fallback
        def _get_news():
            ticker = yf.Ticker(symbol)
            return ticker.news
        
        return await asyncio.to_thread(_get_news)

# Singleton
smart_data_fetcher = SmartDataFetcher()
