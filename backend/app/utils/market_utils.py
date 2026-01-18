"""
Market Utilities Module
Comprehensive utilities for Indian stock market analysis.
Includes market hours, holidays, and performance calculations.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple, Union
from zoneinfo import ZoneInfo
from dataclasses import dataclass


# NSE Market Holidays 2026 (Official List)
NSE_HOLIDAYS_2026 = [
    date(2026, 1, 26),   # Republic Day
    date(2026, 3, 10),   # Maha Shivaratri
    date(2026, 3, 17),   # Holi
    date(2026, 4, 2),    # Ram Navami
    date(2026, 4, 3),    # Good Friday
    date(2026, 4, 14),   # Dr. Ambedkar Jayanti
    date(2026, 4, 21),   # Mahavir Jayanti
    date(2026, 5, 1),    # May Day / Maharashtra Day
    date(2026, 5, 25),   # Buddha Purnima
    date(2026, 6, 26),   # Bakri Id (tentative)
    date(2026, 7, 26),   # Muharram (tentative)
    date(2026, 8, 15),   # Independence Day
    date(2026, 10, 2),   # Mahatma Gandhi Jayanti
    date(2026, 10, 20),  # Dussehra
    date(2026, 11, 9),   # Diwali (Lakshmi Puja)
    date(2026, 11, 10),  # Diwali Balipratipada
    date(2026, 11, 30),  # Guru Nanak Jayanti
    date(2026, 12, 25),  # Christmas
]

# Top 50 NSE Stocks by Market Cap
TOP_NSE_STOCKS = [
    {"symbol": "RELIANCE", "name": "Reliance Industries Ltd.", "sector": "Oil & Gas"},
    {"symbol": "TCS", "name": "Tata Consultancy Services Ltd.", "sector": "IT"},
    {"symbol": "HDFCBANK", "name": "HDFC Bank Ltd.", "sector": "Banking"},
    {"symbol": "INFY", "name": "Infosys Ltd.", "sector": "IT"},
    {"symbol": "ICICIBANK", "name": "ICICI Bank Ltd.", "sector": "Banking"},
    {"symbol": "HINDUNILVR", "name": "Hindustan Unilever Ltd.", "sector": "FMCG"},
    {"symbol": "SBIN", "name": "State Bank of India", "sector": "Banking"},
    {"symbol": "BHARTIARTL", "name": "Bharti Airtel Ltd.", "sector": "Telecom"},
    {"symbol": "ITC", "name": "ITC Ltd.", "sector": "FMCG"},
    {"symbol": "KOTAKBANK", "name": "Kotak Mahindra Bank Ltd.", "sector": "Banking"},
    {"symbol": "LT", "name": "Larsen & Toubro Ltd.", "sector": "Construction"},
    {"symbol": "HCLTECH", "name": "HCL Technologies Ltd.", "sector": "IT"},
    {"symbol": "AXISBANK", "name": "Axis Bank Ltd.", "sector": "Banking"},
    {"symbol": "ASIANPAINT", "name": "Asian Paints Ltd.", "sector": "Consumer Durables"},
    {"symbol": "MARUTI", "name": "Maruti Suzuki India Ltd.", "sector": "Automobile"},
    {"symbol": "SUNPHARMA", "name": "Sun Pharmaceutical Industries Ltd.", "sector": "Pharma"},
    {"symbol": "TITAN", "name": "Titan Company Ltd.", "sector": "Consumer Durables"},
    {"symbol": "BAJFINANCE", "name": "Bajaj Finance Ltd.", "sector": "Finance"},
    {"symbol": "DMART", "name": "Avenue Supermarts Ltd.", "sector": "Retail"},
    {"symbol": "ULTRACEMCO", "name": "UltraTech Cement Ltd.", "sector": "Cement"},
    {"symbol": "WIPRO", "name": "Wipro Ltd.", "sector": "IT"},
    {"symbol": "NESTLEIND", "name": "Nestle India Ltd.", "sector": "FMCG"},
    {"symbol": "M&M", "name": "Mahindra & Mahindra Ltd.", "sector": "Automobile"},
    {"symbol": "TATAMOTORS", "name": "Tata Motors Ltd.", "sector": "Automobile"},
    {"symbol": "POWERGRID", "name": "Power Grid Corporation of India Ltd.", "sector": "Power"},
    {"symbol": "NTPC", "name": "NTPC Ltd.", "sector": "Power"},
    {"symbol": "BAJAJFINSV", "name": "Bajaj Finserv Ltd.", "sector": "Finance"},
    {"symbol": "TECHM", "name": "Tech Mahindra Ltd.", "sector": "IT"},
    {"symbol": "ONGC", "name": "Oil & Natural Gas Corporation Ltd.", "sector": "Oil & Gas"},
    {"symbol": "TATASTEEL", "name": "Tata Steel Ltd.", "sector": "Metals"},
    {"symbol": "JSWSTEEL", "name": "JSW Steel Ltd.", "sector": "Metals"},
    {"symbol": "ADANIENT", "name": "Adani Enterprises Ltd.", "sector": "Conglomerate"},
    {"symbol": "ADANIPORTS", "name": "Adani Ports and SEZ Ltd.", "sector": "Infrastructure"},
    {"symbol": "COALINDIA", "name": "Coal India Ltd.", "sector": "Mining"},
    {"symbol": "HINDALCO", "name": "Hindalco Industries Ltd.", "sector": "Metals"},
    {"symbol": "DRREDDY", "name": "Dr. Reddy's Laboratories Ltd.", "sector": "Pharma"},
    {"symbol": "CIPLA", "name": "Cipla Ltd.", "sector": "Pharma"},
    {"symbol": "DIVISLAB", "name": "Divi's Laboratories Ltd.", "sector": "Pharma"},
    {"symbol": "EICHERMOT", "name": "Eicher Motors Ltd.", "sector": "Automobile"},
    {"symbol": "BRITANNIA", "name": "Britannia Industries Ltd.", "sector": "FMCG"},
    {"symbol": "GRASIM", "name": "Grasim Industries Ltd.", "sector": "Cement"},
    {"symbol": "APOLLOHOSP", "name": "Apollo Hospitals Enterprise Ltd.", "sector": "Healthcare"},
    {"symbol": "HEROMOTOCO", "name": "Hero MotoCorp Ltd.", "sector": "Automobile"},
    {"symbol": "SBILIFE", "name": "SBI Life Insurance Company Ltd.", "sector": "Insurance"},
    {"symbol": "HDFCLIFE", "name": "HDFC Life Insurance Company Ltd.", "sector": "Insurance"},
    {"symbol": "INDUSINDBK", "name": "IndusInd Bank Ltd.", "sector": "Banking"},
    {"symbol": "TATACONSUM", "name": "Tata Consumer Products Ltd.", "sector": "FMCG"},
    {"symbol": "BPCL", "name": "Bharat Petroleum Corporation Ltd.", "sector": "Oil & Gas"},
    {"symbol": "UPL", "name": "UPL Ltd.", "sector": "Chemicals"},
    {"symbol": "SHREECEM", "name": "Shree Cement Ltd.", "sector": "Cement"},
]


@dataclass
class MarketStatus:
    """Market status information."""
    status: str  # "pre_market", "open", "closed", "post_market"
    is_trading: bool
    message: str
    next_open: Optional[datetime]
    next_close: Optional[datetime]


class MarketUtils:
    """Utilities for Indian stock market analysis."""
    
    IST = ZoneInfo("Asia/Kolkata")
    
    # NSE Trading Hours
    MARKET_OPEN = (9, 15)   # 9:15 AM IST
    MARKET_CLOSE = (15, 30)  # 3:30 PM IST
    PRE_MARKET_START = (9, 0)   # 9:00 AM
    POST_MARKET_END = (16, 0)   # 4:00 PM

    @classmethod
    def is_market_open(cls, timezone: str = "Asia/Kolkata") -> bool:
        """
        Check if the NSE market is currently open for trading.
        
        NSE Trading Hours: 9:15 AM - 3:30 PM IST (Monday-Friday)
        
        Args:
            timezone: Timezone for checking (default: Asia/Kolkata)
            
        Returns:
            bool: True if market is open, False otherwise
            
        Example:
            >>> MarketUtils.is_market_open()
            True  # During trading hours on weekdays
        """
        now = datetime.now(cls.IST)
        
        # Check if it's a weekend
        if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False
        
        # Check if it's a holiday
        if now.date() in NSE_HOLIDAYS_2026:
            return False
        
        # Check time
        market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
        market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
        
        return market_open <= now <= market_close

    @classmethod
    def get_market_status(cls) -> MarketStatus:
        """
        Get detailed market status including pre/post market sessions.
        
        Returns:
            MarketStatus: Detailed status with next trading session info
            
        Example:
            >>> status = MarketUtils.get_market_status()
            >>> print(status.status, status.message)
            "open" "Market is currently trading"
        """
        now = datetime.now(cls.IST)
        today = now.date()
        
        # Define time boundaries
        pre_market_start = now.replace(hour=9, minute=0, second=0, microsecond=0)
        market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
        market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
        post_market_end = now.replace(hour=16, minute=0, second=0, microsecond=0)
        
        # Check weekend
        if now.weekday() >= 5:
            next_trading = cls.get_next_trading_day()
            return MarketStatus(
                status="closed",
                is_trading=False,
                message="Market closed for weekend",
                next_open=datetime.combine(next_trading, datetime.min.time().replace(hour=9, minute=15), tzinfo=cls.IST),
                next_close=None
            )
        
        # Check holiday
        if today in NSE_HOLIDAYS_2026:
            next_trading = cls.get_next_trading_day()
            return MarketStatus(
                status="closed",
                is_trading=False,
                message="Market closed for holiday",
                next_open=datetime.combine(next_trading, datetime.min.time().replace(hour=9, minute=15), tzinfo=cls.IST),
                next_close=None
            )
        
        # Pre-market session
        if pre_market_start <= now < market_open:
            return MarketStatus(
                status="pre_market",
                is_trading=False,
                message="Pre-market session - Trading opens shortly",
                next_open=market_open,
                next_close=market_close
            )
        
        # Market open
        if market_open <= now <= market_close:
            return MarketStatus(
                status="open",
                is_trading=True,
                message="Market is currently trading",
                next_open=None,
                next_close=market_close
            )
        
        # Post-market session
        if market_close < now <= post_market_end:
            next_trading = cls.get_next_trading_day()
            return MarketStatus(
                status="post_market",
                is_trading=False,
                message="Post-market session - Trading closed for today",
                next_open=datetime.combine(next_trading, datetime.min.time().replace(hour=9, minute=15), tzinfo=cls.IST),
                next_close=None
            )
        
        # Closed
        next_trading = cls.get_next_trading_day() if now.hour >= 16 else today
        return MarketStatus(
            status="closed",
            is_trading=False,
            message="Market closed",
            next_open=datetime.combine(next_trading, datetime.min.time().replace(hour=9, minute=15), tzinfo=cls.IST),
            next_close=None
        )

    @classmethod
    def get_next_trading_day(cls, from_date: Optional[date] = None, exclude_holidays: bool = True) -> date:
        """
        Get the next trading day, skipping weekends and holidays.
        
        Args:
            from_date: Start date (default: today)
            exclude_holidays: Whether to skip NSE holidays
            
        Returns:
            date: Next trading day
            
        Example:
            >>> MarketUtils.get_next_trading_day()
            datetime.date(2026, 1, 19)  # Next Monday if today is Friday
        """
        if from_date is None:
            from_date = datetime.now(cls.IST).date()
        
        next_day = from_date + timedelta(days=1)
        
        while True:
            # Skip weekends
            if next_day.weekday() >= 5:
                next_day += timedelta(days=1)
                continue
            
            # Skip holidays
            if exclude_holidays and next_day in NSE_HOLIDAYS_2026:
                next_day += timedelta(days=1)
                continue
            
            return next_day

    @staticmethod
    def indian_market_holidays_2026() -> List[Dict[str, Union[str, date]]]:
        """
        Get list of NSE holidays for 2026.
        
        Returns:
            List of holidays with date and name
        """
        holidays = [
            {"date": date(2026, 1, 26), "name": "Republic Day"},
            {"date": date(2026, 3, 10), "name": "Maha Shivaratri"},
            {"date": date(2026, 3, 17), "name": "Holi"},
            {"date": date(2026, 4, 2), "name": "Ram Navami"},
            {"date": date(2026, 4, 3), "name": "Good Friday"},
            {"date": date(2026, 4, 14), "name": "Dr. Ambedkar Jayanti"},
            {"date": date(2026, 4, 21), "name": "Mahavir Jayanti"},
            {"date": date(2026, 5, 1), "name": "May Day"},
            {"date": date(2026, 5, 25), "name": "Buddha Purnima"},
            {"date": date(2026, 6, 26), "name": "Bakri Id"},
            {"date": date(2026, 7, 26), "name": "Muharram"},
            {"date": date(2026, 8, 15), "name": "Independence Day"},
            {"date": date(2026, 10, 2), "name": "Mahatma Gandhi Jayanti"},
            {"date": date(2026, 10, 20), "name": "Dussehra"},
            {"date": date(2026, 11, 9), "name": "Diwali - Lakshmi Puja"},
            {"date": date(2026, 11, 10), "name": "Diwali - Balipratipada"},
            {"date": date(2026, 11, 30), "name": "Guru Nanak Jayanti"},
            {"date": date(2026, 12, 25), "name": "Christmas"},
        ]
        return holidays

    # ==================== PERFORMANCE CALCULATIONS ====================

    @staticmethod
    def calculate_returns(
        prices: Union[pd.Series, np.ndarray],
        periods: List[int] = [1, 7, 30, 90]
    ) -> Dict[str, float]:
        """
        Calculate returns for multiple periods.
        
        Args:
            prices: Price series (most recent last)
            periods: List of periods in days [1=daily, 7=weekly, 30=monthly, 90=quarterly]
            
        Returns:
            Dict with period names and return percentages
            
        Example:
            >>> returns = MarketUtils.calculate_returns(df['close'], [1, 7, 30])
            {'1d': 0.52, '7d': 2.15, '30d': -1.23}
        """
        prices = pd.Series(prices)
        current_price = prices.iloc[-1]
        
        result = {}
        period_names = {1: '1d', 7: '7d', 30: '30d', 90: '90d', 365: '1y'}
        
        for period in periods:
            if len(prices) > period:
                past_price = prices.iloc[-period - 1]
                ret = ((current_price - past_price) / past_price) * 100
                name = period_names.get(period, f'{period}d')
                result[name] = round(ret, 2)
            else:
                name = period_names.get(period, f'{period}d')
                result[name] = None
        
        return result

    @staticmethod
    def calculate_sharpe_ratio(
        returns: Union[pd.Series, np.ndarray],
        risk_free_rate: float = 0.065,
        periods_per_year: int = 252
    ) -> float:
        """
        Calculate the Sharpe Ratio for risk-adjusted returns.
        
        Sharpe Ratio = (Mean Return - Risk Free Rate) / Std Dev of Returns
        
        Args:
            returns: Daily returns series
            risk_free_rate: Annual risk-free rate (default 6.5% for India)
            periods_per_year: Trading days in a year (default 252)
            
        Returns:
            float: Annualized Sharpe Ratio
            
        Example:
            >>> daily_returns = df['close'].pct_change().dropna()
            >>> sharpe = MarketUtils.calculate_sharpe_ratio(daily_returns)
            1.45  # Good risk-adjusted returns
        """
        returns = pd.Series(returns).dropna()
        
        if len(returns) < 2:
            return 0.0
        
        # Annualize returns and std dev
        mean_return = returns.mean() * periods_per_year
        std_return = returns.std() * np.sqrt(periods_per_year)
        
        if std_return == 0:
            return 0.0
        
        sharpe = (mean_return - risk_free_rate) / std_return
        return round(sharpe, 2)

    @staticmethod
    def calculate_max_drawdown(prices: Union[pd.Series, np.ndarray]) -> Dict[str, Union[float, int]]:
        """
        Calculate Maximum Drawdown (MDD) - the largest peak-to-trough decline.
        
        Args:
            prices: Price series
            
        Returns:
            Dict with max_drawdown percentage, peak date, trough date
            
        Example:
            >>> mdd = MarketUtils.calculate_max_drawdown(df['close'])
            {'max_drawdown': -15.3, 'peak_idx': 45, 'trough_idx': 78}
        """
        prices = pd.Series(prices)
        
        # Calculate running maximum
        running_max = prices.expanding().max()
        
        # Calculate drawdown
        drawdown = (prices - running_max) / running_max * 100
        
        # Find max drawdown
        max_dd = drawdown.min()
        trough_idx = drawdown.idxmin() if isinstance(drawdown.idxmin(), int) else drawdown.values.argmin()
        
        # Find the peak before the trough
        peak_idx = prices.iloc[:trough_idx + 1].idxmax() if isinstance(prices.iloc[:trough_idx + 1].idxmax(), int) else prices.iloc[:trough_idx + 1].values.argmax()
        
        return {
            'max_drawdown': round(max_dd, 2),
            'peak_idx': int(peak_idx),
            'trough_idx': int(trough_idx)
        }

    @staticmethod
    def beta_calculation(
        stock_returns: Union[pd.Series, np.ndarray],
        market_returns: Union[pd.Series, np.ndarray]
    ) -> float:
        """
        Calculate stock beta against market returns.
        
        Beta measures the volatility of a stock relative to the market.
        Beta > 1: More volatile than market
        Beta < 1: Less volatile than market
        Beta = 1: Moves with market
        
        Args:
            stock_returns: Daily returns of the stock
            market_returns: Daily returns of the market index (Nifty 50)
            
        Returns:
            float: Beta coefficient
            
        Example:
            >>> stock_ret = stock_df['close'].pct_change().dropna()
            >>> nifty_ret = nifty_df['close'].pct_change().dropna()
            >>> beta = MarketUtils.beta_calculation(stock_ret, nifty_ret)
            1.25  # Stock is 25% more volatile than Nifty
        """
        stock_returns = pd.Series(stock_returns).dropna()
        market_returns = pd.Series(market_returns).dropna()
        
        # Align the series
        min_len = min(len(stock_returns), len(market_returns))
        stock_returns = stock_returns.iloc[-min_len:]
        market_returns = market_returns.iloc[-min_len:]
        
        if len(stock_returns) < 10:
            return 1.0
        
        # Calculate covariance and variance
        covariance = stock_returns.cov(market_returns)
        market_variance = market_returns.var()
        
        if market_variance == 0:
            return 1.0
        
        beta = covariance / market_variance
        return round(beta, 2)

    @staticmethod
    def calculate_volatility(
        prices: Union[pd.Series, np.ndarray],
        period: int = 20,
        annualize: bool = True
    ) -> float:
        """
        Calculate historical volatility.
        
        Args:
            prices: Price series
            period: Rolling period for volatility calculation
            annualize: Whether to annualize the result
            
        Returns:
            float: Volatility as a percentage
        """
        returns = pd.Series(prices).pct_change().dropna()
        
        if len(returns) < period:
            period = len(returns)
        
        volatility = returns.iloc[-period:].std()
        
        if annualize:
            volatility *= np.sqrt(252)
        
        return round(volatility * 100, 2)

    @staticmethod
    def get_top_stocks(limit: int = 50) -> List[Dict]:
        """Get list of top NSE stocks by market cap."""
        return TOP_NSE_STOCKS[:limit]

    @staticmethod
    def search_stocks(query: str, limit: int = 10) -> List[Dict]:
        """
        Search stocks by symbol or name.
        
        Args:
            query: Search query
            limit: Maximum results to return
            
        Returns:
            List of matching stocks
        """
        query = query.upper()
        results = []
        
        for stock in TOP_NSE_STOCKS:
            if query in stock['symbol'].upper() or query in stock['name'].upper():
                results.append(stock)
                if len(results) >= limit:
                    break
        
        return results


# Convenience functions
def is_market_open() -> bool:
    """Check if NSE market is currently open."""
    return MarketUtils.is_market_open()


def get_market_status() -> MarketStatus:
    """Get current market status."""
    return MarketUtils.get_market_status()


def get_next_trading_day() -> date:
    """Get the next NSE trading day."""
    return MarketUtils.get_next_trading_day()
