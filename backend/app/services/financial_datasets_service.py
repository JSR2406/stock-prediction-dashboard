"""
Financial Datasets Service
A comprehensive service for fetching financial data from the Financial Datasets API.
Provides access to stock prices, fundamentals, crypto, and SEC filings.
"""

import asyncio
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from functools import wraps

import httpx

from app.utils.logging import logger


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


class FinancialDatasetsClient:
    """
    Client for interacting with the Financial Datasets API.
    
    Provides access to:
    - Income statements, balance sheets, cash flow statements
    - Stock prices (current and historical)
    - Cryptocurrency prices
    - Company news
    - SEC filings
    
    Example:
        client = FinancialDatasetsClient()
        price = await client.get_current_stock_price("AAPL")
    """
    
    API_BASE_URL = "https://api.financialdatasets.ai"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Financial Datasets client.
        
        Args:
            api_key: API key for Financial Datasets. If not provided,
                     reads from FINANCIAL_DATASETS_API_KEY environment variable.
        """
        self.api_key = api_key or os.getenv("FINANCIAL_DATASETS_API_KEY")
        self.timeout = httpx.Timeout(30.0, connect=10.0)
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client
    
    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-KEY"] = self.api_key
        return headers
    
    @async_retry(max_retries=3)
    async def _make_request(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Make a request to the Financial Datasets API.
        
        Args:
            url: Full URL to request
            
        Returns:
            JSON response as dictionary, or None if request fails
        """
        client = await self._get_client()
        
        logger.info("financial_datasets_request", url=url)
        
        try:
            response = await client.get(url, headers=self._get_headers())
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(
                "financial_datasets_http_error",
                url=url,
                status_code=e.response.status_code,
                error=str(e)
            )
            if e.response.status_code == 429:
                raise Exception("Rate limit exceeded. Please try again later.")
            raise
        except httpx.TimeoutException as e:
            logger.error("financial_datasets_timeout", url=url, error=str(e))
            raise Exception("Request timed out. Please try again.")
        except Exception as e:
            logger.error("financial_datasets_error", url=url, error=str(e))
            raise
    
    # ==================== Fundamental Data ====================
    
    async def get_income_statements(
        self,
        ticker: str,
        period: str = "annual",
        limit: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Get income statements for a company.
        
        Args:
            ticker: Stock ticker symbol (e.g., AAPL, GOOGL)
            period: Period type - 'annual', 'quarterly', or 'ttm'
            limit: Number of statements to return
            
        Returns:
            List of income statement dictionaries
        """
        url = f"{self.API_BASE_URL}/financials/income-statements/?ticker={ticker}&period={period}&limit={limit}"
        data = await self._make_request(url)
        
        if not data:
            return []
        
        return data.get("income_statements", [])
    
    async def get_balance_sheets(
        self,
        ticker: str,
        period: str = "annual",
        limit: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Get balance sheets for a company.
        
        Args:
            ticker: Stock ticker symbol (e.g., AAPL, GOOGL)
            period: Period type - 'annual', 'quarterly', or 'ttm'
            limit: Number of statements to return
            
        Returns:
            List of balance sheet dictionaries
        """
        url = f"{self.API_BASE_URL}/financials/balance-sheets/?ticker={ticker}&period={period}&limit={limit}"
        data = await self._make_request(url)
        
        if not data:
            return []
        
        return data.get("balance_sheets", [])
    
    async def get_cash_flow_statements(
        self,
        ticker: str,
        period: str = "annual",
        limit: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Get cash flow statements for a company.
        
        Args:
            ticker: Stock ticker symbol (e.g., AAPL, GOOGL)
            period: Period type - 'annual', 'quarterly', or 'ttm'
            limit: Number of statements to return
            
        Returns:
            List of cash flow statement dictionaries
        """
        url = f"{self.API_BASE_URL}/financials/cash-flow-statements/?ticker={ticker}&period={period}&limit={limit}"
        data = await self._make_request(url)
        
        if not data:
            return []
        
        return data.get("cash_flow_statements", [])
    
    async def get_fundamentals(
        self,
        ticker: str,
        period: str = "annual",
        limit: int = 4
    ) -> Dict[str, Any]:
        """
        Get all fundamental data for a company (income, balance sheet, cash flow).
        
        Args:
            ticker: Stock ticker symbol
            period: Period type - 'annual', 'quarterly', or 'ttm'
            limit: Number of statements to return
            
        Returns:
            Dictionary with income_statements, balance_sheets, and cash_flow_statements
        """
        # Fetch all three in parallel
        income_task = self.get_income_statements(ticker, period, limit)
        balance_task = self.get_balance_sheets(ticker, period, limit)
        cashflow_task = self.get_cash_flow_statements(ticker, period, limit)
        
        income, balance, cashflow = await asyncio.gather(
            income_task, balance_task, cashflow_task,
            return_exceptions=True
        )
        
        return {
            "ticker": ticker,
            "period": period,
            "income_statements": income if not isinstance(income, Exception) else [],
            "balance_sheets": balance if not isinstance(balance, Exception) else [],
            "cash_flow_statements": cashflow if not isinstance(cashflow, Exception) else [],
            "fetched_at": datetime.utcnow().isoformat() + "Z"
        }
    
    # ==================== Price Data ====================
    
    async def get_current_stock_price(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Get the current/latest stock price.
        
        Args:
            ticker: Stock ticker symbol (e.g., AAPL)
            
        Returns:
            Price snapshot dictionary with open, high, low, close, volume
        """
        url = f"{self.API_BASE_URL}/prices/snapshot/?ticker={ticker}"
        data = await self._make_request(url)
        
        if not data:
            return None
        
        return data.get("snapshot")
    
    async def get_historical_stock_prices(
        self,
        ticker: str,
        start_date: str,
        end_date: str,
        interval: str = "day",
        interval_multiplier: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Get historical stock prices.
        
        Args:
            ticker: Stock ticker symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            interval: Interval type - 'minute', 'hour', 'day', 'week', 'month'
            interval_multiplier: Multiplier for interval
            
        Returns:
            List of price bar dictionaries
        """
        url = (
            f"{self.API_BASE_URL}/prices/?ticker={ticker}"
            f"&interval={interval}&interval_multiplier={interval_multiplier}"
            f"&start_date={start_date}&end_date={end_date}"
        )
        data = await self._make_request(url)
        
        if not data:
            return []
        
        return data.get("prices", [])
    
    # ==================== Company News ====================
    
    async def get_company_news(self, ticker: str) -> List[Dict[str, Any]]:
        """
        Get news articles for a company.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            List of news article dictionaries
        """
        url = f"{self.API_BASE_URL}/news/?ticker={ticker}"
        data = await self._make_request(url)
        
        if not data:
            return []
        
        return data.get("news", [])
    
    # ==================== Crypto ====================
    
    async def get_available_crypto_tickers(self) -> List[str]:
        """
        Get list of available cryptocurrency tickers.
        
        Returns:
            List of crypto ticker symbols (e.g., BTC-USD, ETH-USD)
        """
        url = f"{self.API_BASE_URL}/crypto/prices/tickers"
        data = await self._make_request(url)
        
        if not data:
            return []
        
        return data.get("tickers", [])
    
    async def get_current_crypto_price(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Get current cryptocurrency price.
        
        Args:
            ticker: Crypto ticker symbol (e.g., BTC-USD)
            
        Returns:
            Price snapshot dictionary
        """
        url = f"{self.API_BASE_URL}/crypto/prices/snapshot/?ticker={ticker}"
        data = await self._make_request(url)
        
        if not data:
            return None
        
        return data.get("snapshot")
    
    async def get_crypto_prices(
        self,
        ticker: str,
        start_date: str,
        end_date: str,
        interval: str = "day",
        interval_multiplier: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Get historical cryptocurrency prices.
        
        Args:
            ticker: Crypto ticker symbol (e.g., BTC-USD)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            interval: Interval type - 'minute', 'hour', 'day', 'week', 'month'
            interval_multiplier: Multiplier for interval
            
        Returns:
            List of price bar dictionaries
        """
        url = (
            f"{self.API_BASE_URL}/crypto/prices/?ticker={ticker}"
            f"&interval={interval}&interval_multiplier={interval_multiplier}"
            f"&start_date={start_date}&end_date={end_date}"
        )
        data = await self._make_request(url)
        
        if not data:
            return []
        
        return data.get("prices", [])
    
    # ==================== SEC Filings ====================
    
    async def get_sec_filings(
        self,
        ticker: str,
        limit: int = 10,
        filing_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get SEC filings for a company.
        
        Args:
            ticker: Stock ticker symbol
            limit: Number of filings to return
            filing_type: Type of filing (e.g., '10-K', '10-Q', '8-K')
            
        Returns:
            List of SEC filing dictionaries
        """
        url = f"{self.API_BASE_URL}/filings/?ticker={ticker}&limit={limit}"
        if filing_type:
            url += f"&filing_type={filing_type}"
        
        data = await self._make_request(url)
        
        if not data:
            return []
        
        return data.get("filings", [])
    
    # ==================== Financial Ratios (Calculated) ====================
    
    async def calculate_financial_ratios(self, ticker: str) -> Dict[str, Any]:
        """
        Calculate key financial ratios from fundamental data.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dictionary with calculated ratios
        """
        try:
            # Fetch latest fundamental data
            income = await self.get_income_statements(ticker, "annual", 1)
            balance = await self.get_balance_sheets(ticker, "annual", 1)
            price = await self.get_current_stock_price(ticker)
            
            ratios = {
                "ticker": ticker,
                "calculated_at": datetime.utcnow().isoformat() + "Z",
                "ratios": {}
            }
            
            if income and len(income) > 0:
                latest_income = income[0]
                revenue = latest_income.get("total_revenue") or latest_income.get("revenue", 0)
                net_income = latest_income.get("net_income", 0)
                operating_income = latest_income.get("operating_income", 0)
                
                if revenue and revenue > 0:
                    ratios["ratios"]["profit_margin"] = round((net_income / revenue) * 100, 2)
                    ratios["ratios"]["operating_margin"] = round((operating_income / revenue) * 100, 2)
            
            if balance and len(balance) > 0:
                latest_balance = balance[0]
                total_assets = latest_balance.get("total_assets", 0)
                total_liabilities = latest_balance.get("total_liabilities", 0)
                stockholders_equity = latest_balance.get("stockholders_equity", 0)
                current_assets = latest_balance.get("total_current_assets", 0)
                current_liabilities = latest_balance.get("total_current_liabilities", 0)
                total_debt = latest_balance.get("total_debt", 0)
                
                if stockholders_equity and stockholders_equity > 0:
                    ratios["ratios"]["debt_to_equity"] = round(total_debt / stockholders_equity, 2)
                    if income and len(income) > 0:
                        net_income = income[0].get("net_income", 0)
                        ratios["ratios"]["roe"] = round((net_income / stockholders_equity) * 100, 2)
                
                if total_assets and total_assets > 0:
                    if income and len(income) > 0:
                        net_income = income[0].get("net_income", 0)
                        ratios["ratios"]["roa"] = round((net_income / total_assets) * 100, 2)
                
                if current_liabilities and current_liabilities > 0:
                    ratios["ratios"]["current_ratio"] = round(current_assets / current_liabilities, 2)
            
            if price:
                current_price = price.get("price") or price.get("close", 0)
                ratios["current_price"] = current_price
                
                if income and len(income) > 0:
                    eps = income[0].get("eps_diluted") or income[0].get("eps_basic", 0)
                    if eps and eps > 0:
                        ratios["ratios"]["pe_ratio"] = round(current_price / eps, 2)
                
                if balance and len(balance) > 0:
                    book_value = balance[0].get("stockholders_equity", 0)
                    shares = income[0].get("weighted_average_shares_diluted", 0) if income else 0
                    if shares and shares > 0:
                        book_per_share = book_value / shares
                        if book_per_share > 0:
                            ratios["ratios"]["pb_ratio"] = round(current_price / book_per_share, 2)
            
            return ratios
            
        except Exception as e:
            logger.error("ratio_calculation_error", ticker=ticker, error=str(e))
            return {
                "ticker": ticker,
                "error": str(e),
                "ratios": {}
            }


# Singleton instance
financial_datasets_client = FinancialDatasetsClient()
