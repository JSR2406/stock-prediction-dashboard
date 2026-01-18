"""
Data Fetcher Service - Comprehensive data fetching with retry logic.
Fetches stock, crypto, and commodity data from multiple APIs.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
import httpx
import yfinance as yf
import pandas as pd
from functools import wraps

from app.config import settings
from app.utils.logging import logger
from app.utils.exceptions import (
    YahooFinanceException, CoinGeckoException, MetalsAPIException, ExternalServiceException
)


def async_retry(max_retries: int = 3, initial_delay: float = 1.0, backoff_factor: float = 2.0):
    """Decorator for async retry with exponential backoff."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(
                            "retry_attempt",
                            function=func.__name__,
                            attempt=attempt + 1,
                            max_retries=max_retries,
                            delay=delay,
                            error=str(e)
                        )
                        await asyncio.sleep(delay)
                        delay *= backoff_factor
                    else:
                        logger.error("retry_failed", function=func.__name__, error=str(e))
            
            raise last_exception
        return wrapper
    return decorator


class DataFetcher:
    """
    Comprehensive data fetcher for stocks, crypto, and commodities.
    Implements retry logic and proper error handling.
    """
    
    # NSE Top Stocks for gainers/losers calculation
    NSE_TOP_STOCKS = [
        "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "HINDUNILVR",
        "SBIN", "BHARTIARTL", "KOTAKBANK", "ITC", "LT", "AXISBANK",
        "ASIANPAINT", "MARUTI", "TITAN", "SUNPHARMA", "BAJFINANCE",
        "WIPRO", "HCLTECH", "ULTRACEMCO", "ONGC", "NTPC", "POWERGRID",
        "TATAMOTORS", "M&M", "ADANIENT", "COALINDIA", "JSWSTEEL", "TATASTEEL"
    ]
    
    # CoinGecko top crypto IDs
    TOP_CRYPTO_IDS = [
        "bitcoin", "ethereum", "tether", "binancecoin", "ripple",
        "cardano", "solana", "polkadot", "dogecoin", "avalanche-2"
    ]
    
    def __init__(self):
        self.timeout = httpx.Timeout(30.0, connect=10.0)
        self._http_client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=self.timeout)
        return self._http_client
    
    async def close(self):
        """Close HTTP client."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
    
    def _get_yf_symbol(self, symbol: str, exchange: str = "NSE") -> str:
        """Convert symbol to Yahoo Finance format."""
        symbol = symbol.upper().strip()
        if exchange.upper() == "NSE":
            return f"{symbol}.NS"
        elif exchange.upper() == "BSE":
            return f"{symbol}.BO"
        return symbol
    
    @async_retry(max_retries=3)
    async def fetch_stock_data(
        self, 
        symbol: str, 
        period: str = "1y",
        exchange: str = "NSE"
    ) -> Dict[str, Any]:
        """
        Fetch stock data from Yahoo Finance.
        
        Args:
            symbol: Stock symbol (e.g., RELIANCE, TCS)
            period: Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max)
            exchange: Stock exchange (NSE or BSE)
            
        Returns:
            Dictionary with stock quote and historical data
        """
        yf_symbol = self._get_yf_symbol(symbol, exchange)
        logger.info("fetch_stock_data", symbol=yf_symbol, period=period)
        
        try:
            # Run yfinance in thread pool (it's not async)
            loop = asyncio.get_event_loop()
            ticker = await loop.run_in_executor(None, lambda: yf.Ticker(yf_symbol))
            info = await loop.run_in_executor(None, lambda: ticker.info)
            hist = await loop.run_in_executor(None, lambda: ticker.history(period=period))
            
            if hist.empty:
                raise YahooFinanceException(f"No data found for {symbol}")
            
            # Get latest quote
            current_price = info.get("currentPrice") or info.get("regularMarketPrice", 0)
            prev_close = info.get("previousClose", info.get("regularMarketPreviousClose", 0))
            
            change = current_price - prev_close if prev_close else 0
            change_pct = (change / prev_close * 100) if prev_close else 0
            
            return {
                "symbol": symbol.upper(),
                "name": info.get("longName", info.get("shortName", symbol)),
                "exchange": exchange.upper(),
                "current_price": round(current_price, 2),
                "previous_close": round(prev_close, 2),
                "open_price": round(info.get("open", info.get("regularMarketOpen", 0)), 2),
                "high": round(info.get("dayHigh", info.get("regularMarketDayHigh", 0)), 2),
                "low": round(info.get("dayLow", info.get("regularMarketDayLow", 0)), 2),
                "volume": int(info.get("volume", info.get("regularMarketVolume", 0))),
                "change": round(change, 2),
                "change_percent": round(change_pct, 2),
                "trend": "up" if change >= 0 else "down",
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "week_52_high": info.get("fiftyTwoWeekHigh"),
                "week_52_low": info.get("fiftyTwoWeekLow"),
                "historical": self._process_historical(hist),
                "last_updated": datetime.utcnow().isoformat() + "Z"
            }
            
        except Exception as e:
            logger.error("fetch_stock_error", symbol=symbol, error=str(e))
            raise YahooFinanceException(f"Failed to fetch {symbol}: {str(e)}")
    
    def _process_historical(self, df: pd.DataFrame) -> List[Dict]:
        """Process historical DataFrame to list of dicts."""
        if df.empty:
            return []
        
        records = []
        for date, row in df.iterrows():
            records.append({
                "date": date.isoformat(),
                "open": round(row["Open"], 2),
                "high": round(row["High"], 2),
                "low": round(row["Low"], 2),
                "close": round(row["Close"], 2),
                "volume": int(row["Volume"])
            })
        return records
    
    @async_retry(max_retries=3)
    async def fetch_nifty_sensex(self) -> Dict[str, Any]:
        """Fetch Nifty 50 and Sensex indices data."""
        logger.info("fetch_nifty_sensex")
        
        try:
            loop = asyncio.get_event_loop()
            
            # Fetch both indices concurrently
            nifty_ticker = await loop.run_in_executor(None, lambda: yf.Ticker("^NSEI"))
            sensex_ticker = await loop.run_in_executor(None, lambda: yf.Ticker("^BSESN"))
            
            nifty_info = await loop.run_in_executor(None, lambda: nifty_ticker.info)
            sensex_info = await loop.run_in_executor(None, lambda: sensex_ticker.info)
            
            def process_index(info: Dict, name: str) -> Dict:
                price = info.get("regularMarketPrice", 0)
                prev_close = info.get("regularMarketPreviousClose", 0)
                change = price - prev_close
                change_pct = (change / prev_close * 100) if prev_close else 0
                
                return {
                    "name": name,
                    "value": round(price, 2),
                    "change": round(change, 2),
                    "change_percent": round(change_pct, 2),
                    "trend": "up" if change >= 0 else "down",
                    "high": round(info.get("regularMarketDayHigh", 0), 2),
                    "low": round(info.get("regularMarketDayLow", 0), 2),
                    "open": round(info.get("regularMarketOpen", 0), 2)
                }
            
            return {
                "nifty50": process_index(nifty_info, "NIFTY 50"),
                "sensex": process_index(sensex_info, "SENSEX"),
                "market_status": self._get_market_status(),
                "last_updated": datetime.utcnow().isoformat() + "Z"
            }
            
        except Exception as e:
            logger.error("fetch_indices_error", error=str(e))
            raise YahooFinanceException(f"Failed to fetch indices: {str(e)}")
    
    @async_retry(max_retries=2)
    async def fetch_top_gainers_losers(self, limit: int = 10) -> Dict[str, List[Dict]]:
        """Fetch top gainers and losers from NSE."""
        logger.info("fetch_top_gainers_losers", limit=limit)
        
        try:
            loop = asyncio.get_event_loop()
            stocks_data = []
            
            # Fetch data for top stocks
            for symbol in self.NSE_TOP_STOCKS[:30]:
                try:
                    yf_symbol = self._get_yf_symbol(symbol)
                    ticker = await loop.run_in_executor(None, lambda s=yf_symbol: yf.Ticker(s))
                    info = await loop.run_in_executor(None, lambda t=ticker: t.info)
                    
                    price = info.get("currentPrice", info.get("regularMarketPrice", 0))
                    prev_close = info.get("previousClose", info.get("regularMarketPreviousClose", 0))
                    
                    if price and prev_close:
                        change_pct = ((price - prev_close) / prev_close) * 100
                        stocks_data.append({
                            "symbol": symbol,
                            "name": info.get("shortName", symbol),
                            "price": round(price, 2),
                            "change_percent": round(change_pct, 2),
                            "volume": int(info.get("volume", 0))
                        })
                except Exception:
                    continue
            
            # Sort for gainers and losers
            sorted_stocks = sorted(stocks_data, key=lambda x: x["change_percent"], reverse=True)
            
            return {
                "top_gainers": sorted_stocks[:limit],
                "top_losers": sorted_stocks[-limit:][::-1],
                "last_updated": datetime.utcnow().isoformat() + "Z"
            }
            
        except Exception as e:
            logger.error("fetch_movers_error", error=str(e))
            raise YahooFinanceException(f"Failed to fetch movers: {str(e)}")
    
    @async_retry(max_retries=3)
    async def fetch_gold_silver(self) -> Dict[str, Any]:
        """Fetch gold and silver prices (in INR)."""
        logger.info("fetch_gold_silver")
        
        try:
            client = await self._get_client()
            
            # Using Metals-API or fallback to Yahoo Finance
            if settings.metals_api_key:
                url = "https://metals-api.com/api/latest"
                params = {
                    "access_key": settings.metals_api_key,
                    "base": "INR",
                    "symbols": "XAU,XAG"
                }
                response = await client.get(url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        rates = data.get("rates", {})
                        # Convert from INR per oz to per gram
                        gold_per_gram = (1 / rates.get("XAU", 1)) / 31.1035
                        silver_per_gram = (1 / rates.get("XAG", 1)) / 31.1035
                        
                        return {
                            "gold": {
                                "symbol": "XAU",
                                "name": "Gold",
                                "price_per_gram": round(gold_per_gram, 2),
                                "price_per_10g": round(gold_per_gram * 10, 2),
                                "unit": "gram",
                                "currency": "INR"
                            },
                            "silver": {
                                "symbol": "XAG",
                                "name": "Silver",
                                "price_per_gram": round(silver_per_gram, 2),
                                "price_per_kg": round(silver_per_gram * 1000, 2),
                                "unit": "gram",
                                "currency": "INR"
                            },
                            "last_updated": datetime.utcnow().isoformat() + "Z"
                        }
            
            # Fallback to Yahoo Finance
            loop = asyncio.get_event_loop()
            gold = await loop.run_in_executor(None, lambda: yf.Ticker("GC=F").info)
            silver = await loop.run_in_executor(None, lambda: yf.Ticker("SI=F").info)
            usd_inr = await loop.run_in_executor(None, lambda: yf.Ticker("USDINR=X").info)
            
            exchange_rate = usd_inr.get("regularMarketPrice", 83.5)
            
            gold_usd = gold.get("regularMarketPrice", 2000)
            silver_usd = silver.get("regularMarketPrice", 24)
            
            # Convert to INR per gram
            gold_inr_gram = (gold_usd * exchange_rate) / 31.1035
            silver_inr_gram = (silver_usd * exchange_rate) / 31.1035
            
            return {
                "gold": {
                    "symbol": "XAU",
                    "name": "Gold",
                    "price_per_gram": round(gold_inr_gram, 2),
                    "price_per_10g": round(gold_inr_gram * 10, 2),
                    "unit": "gram",
                    "currency": "INR"
                },
                "silver": {
                    "symbol": "XAG",
                    "name": "Silver",
                    "price_per_gram": round(silver_inr_gram, 2),
                    "price_per_kg": round(silver_inr_gram * 1000, 2),
                    "unit": "gram",
                    "currency": "INR"
                },
                "exchange_rate": round(exchange_rate, 2),
                "last_updated": datetime.utcnow().isoformat() + "Z"
            }
            
        except Exception as e:
            logger.error("fetch_metals_error", error=str(e))
            raise MetalsAPIException(f"Failed to fetch metals: {str(e)}")
    
    @async_retry(max_retries=3)
    async def fetch_crypto_data(self, symbols: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Fetch cryptocurrency data from CoinGecko.
        
        Args:
            symbols: List of crypto IDs (default: top 10)
            
        Returns:
            List of crypto data dictionaries
        """
        crypto_ids = symbols or self.TOP_CRYPTO_IDS
        logger.info("fetch_crypto_data", symbols=crypto_ids)
        
        try:
            client = await self._get_client()
            
            url = "https://api.coingecko.com/api/v3/coins/markets"
            params = {
                "vs_currency": "inr",
                "ids": ",".join(crypto_ids),
                "order": "market_cap_desc",
                "sparkline": False,
                "price_change_percentage": "24h,7d,30d"
            }
            
            headers = {}
            if settings.coingecko_api_key:
                headers["x-cg-demo-api-key"] = settings.coingecko_api_key
            
            response = await client.get(url, params=params, headers=headers)
            
            if response.status_code == 429:
                raise CoinGeckoException("Rate limit exceeded")
            
            if response.status_code != 200:
                raise CoinGeckoException(f"API error: {response.status_code}")
            
            data = response.json()
            
            return [
                {
                    "id": coin["id"],
                    "symbol": coin["symbol"].upper(),
                    "name": coin["name"],
                    "current_price": coin["current_price"],
                    "market_cap": coin["market_cap"],
                    "market_cap_rank": coin["market_cap_rank"],
                    "total_volume": coin["total_volume"],
                    "high_24h": coin["high_24h"],
                    "low_24h": coin["low_24h"],
                    "price_change_24h": coin["price_change_24h"],
                    "price_change_percentage_24h": round(coin.get("price_change_percentage_24h", 0), 2),
                    "price_change_percentage_7d": round(coin.get("price_change_percentage_7d_in_currency", 0) or 0, 2),
                    "price_change_percentage_30d": round(coin.get("price_change_percentage_30d_in_currency", 0) or 0, 2),
                    "circulating_supply": coin.get("circulating_supply"),
                    "total_supply": coin.get("total_supply"),
                    "max_supply": coin.get("max_supply"),
                    "ath": coin.get("ath"),
                    "image": coin.get("image"),
                    "trend": "up" if coin.get("price_change_percentage_24h", 0) >= 0 else "down",
                    "last_updated": coin.get("last_updated")
                }
                for coin in data
            ]
            
        except httpx.TimeoutException:
            raise CoinGeckoException("Request timeout")
        except Exception as e:
            logger.error("fetch_crypto_error", error=str(e))
            raise CoinGeckoException(f"Failed to fetch crypto: {str(e)}")
    
    def _get_market_status(self) -> str:
        """Get current Indian market status based on IST time."""
        from zoneinfo import ZoneInfo
        
        ist = ZoneInfo("Asia/Kolkata")
        now = datetime.now(ist)
        
        # Weekend check
        if now.weekday() >= 5:
            return "closed"
        
        # Market hours: 9:15 AM - 3:30 PM IST
        market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
        market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
        pre_market_start = now.replace(hour=9, minute=0, second=0, microsecond=0)
        post_market_end = now.replace(hour=16, minute=0, second=0, microsecond=0)
        
        if now < pre_market_start:
            return "closed"
        elif now < market_open:
            return "pre-market"
        elif now <= market_close:
            return "open"
        elif now <= post_market_end:
            return "post-market"
        else:
            return "closed"


# Singleton instance
data_fetcher = DataFetcher()
