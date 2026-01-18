"""
Technical Indicators Module
Comprehensive technical analysis utilities for stock market analysis.
All calculations are vectorized using pandas/numpy for efficiency.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass


@dataclass
class SignalResult:
    """Result of a technical signal analysis."""
    signal: str  # "buy", "sell", "hold"
    strength: float  # 0-100
    reason: str


class TechnicalIndicators:
    """
    Static methods for calculating technical indicators.
    All methods are designed to work with pandas Series or numpy arrays.
    """

    # ==================== MOMENTUM INDICATORS ====================

    @staticmethod
    def calculate_rsi(prices: Union[pd.Series, np.ndarray], period: int = 14) -> pd.Series:
        """
        Calculate Relative Strength Index (RSI).
        
        RSI measures momentum by comparing the magnitude of recent gains to recent losses.
        Values above 70 indicate overbought, below 30 indicate oversold.
        
        Args:
            prices: Series of closing prices
            period: RSI period (default 14)
            
        Returns:
            pd.Series: RSI values (0-100)
            
        Example:
            >>> rsi = TechnicalIndicators.calculate_rsi(df['close'], period=14)
        """
        if len(prices) < period + 1:
            return pd.Series([np.nan] * len(prices), index=getattr(prices, 'index', None))
        
        prices = pd.Series(prices)
        delta = prices.diff()
        
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.fillna(50)

    @staticmethod
    def calculate_macd(
        prices: Union[pd.Series, np.ndarray],
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> Dict[str, pd.Series]:
        """
        Calculate Moving Average Convergence Divergence (MACD).
        
        MACD shows the relationship between two moving averages and is used to
        identify trend direction and momentum.
        
        Args:
            prices: Series of closing prices
            fast_period: Fast EMA period (default 12)
            slow_period: Slow EMA period (default 26)
            signal_period: Signal line period (default 9)
            
        Returns:
            Dict with 'macd_line', 'signal_line', 'histogram'
            
        Example:
            >>> macd = TechnicalIndicators.calculate_macd(df['close'])
            >>> histogram = macd['histogram']
        """
        prices = pd.Series(prices)
        
        ema_fast = prices.ewm(span=fast_period, adjust=False).mean()
        ema_slow = prices.ewm(span=slow_period, adjust=False).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return {
            'macd_line': macd_line,
            'signal_line': signal_line,
            'histogram': histogram
        }

    @staticmethod
    def calculate_stochastic(
        high: Union[pd.Series, np.ndarray],
        low: Union[pd.Series, np.ndarray],
        close: Union[pd.Series, np.ndarray],
        period: int = 14,
        smooth_k: int = 3,
        smooth_d: int = 3
    ) -> Dict[str, pd.Series]:
        """
        Calculate Stochastic Oscillator (%K and %D).
        
        Stochastic compares closing price to its price range over a period.
        Values above 80 indicate overbought, below 20 indicate oversold.
        
        Args:
            high: High prices
            low: Low prices
            close: Closing prices
            period: Lookback period (default 14)
            smooth_k: Smoothing for %K (default 3)
            smooth_d: Smoothing for %D (default 3)
            
        Returns:
            Dict with 'k' and 'd' lines
        """
        high = pd.Series(high)
        low = pd.Series(low)
        close = pd.Series(close)
        
        lowest_low = low.rolling(window=period).min()
        highest_high = high.rolling(window=period).max()
        
        k = 100 * (close - lowest_low) / (highest_high - lowest_low).replace(0, np.nan)
        k = k.rolling(window=smooth_k).mean()
        d = k.rolling(window=smooth_d).mean()
        
        return {'k': k.fillna(50), 'd': d.fillna(50)}

    # ==================== TREND INDICATORS ====================

    @staticmethod
    def calculate_sma(
        prices: Union[pd.Series, np.ndarray],
        windows: List[int] = [20, 50, 200]
    ) -> Dict[str, pd.Series]:
        """
        Calculate Simple Moving Averages (SMA) for multiple windows.
        
        SMA is the unweighted mean of the previous n data points.
        
        Args:
            prices: Series of closing prices
            windows: List of window sizes (default [20, 50, 200])
            
        Returns:
            Dict mapping window name to SMA series
            
        Example:
            >>> smas = TechnicalIndicators.calculate_sma(df['close'], [20, 50])
            >>> sma_20 = smas['sma_20']
        """
        prices = pd.Series(prices)
        return {f'sma_{w}': prices.rolling(window=w).mean() for w in windows}

    @staticmethod
    def calculate_ema(
        prices: Union[pd.Series, np.ndarray],
        windows: List[int] = [12, 26]
    ) -> Dict[str, pd.Series]:
        """
        Calculate Exponential Moving Averages (EMA) for multiple windows.
        
        EMA gives more weight to recent prices than SMA.
        
        Args:
            prices: Series of closing prices
            windows: List of window sizes (default [12, 26])
            
        Returns:
            Dict mapping window name to EMA series
        """
        prices = pd.Series(prices)
        return {f'ema_{w}': prices.ewm(span=w, adjust=False).mean() for w in windows}

    @staticmethod
    def calculate_adx(
        high: Union[pd.Series, np.ndarray],
        low: Union[pd.Series, np.ndarray],
        close: Union[pd.Series, np.ndarray],
        period: int = 14
    ) -> Dict[str, pd.Series]:
        """
        Calculate Average Directional Index (ADX).
        
        ADX measures trend strength regardless of direction.
        Values above 25 indicate a strong trend.
        
        Args:
            high: High prices
            low: Low prices
            close: Closing prices
            period: ADX period (default 14)
            
        Returns:
            Dict with 'adx', 'di_plus', 'di_minus'
        """
        high = pd.Series(high)
        low = pd.Series(low)
        close = pd.Series(close)
        
        # True Range
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        # Directional Movement
        up_move = high - high.shift(1)
        down_move = low.shift(1) - low
        
        plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0)
        minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0)
        
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
        
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, np.nan)
        adx = dx.rolling(window=period).mean()
        
        return {
            'adx': adx.fillna(0),
            'di_plus': plus_di.fillna(0),
            'di_minus': minus_di.fillna(0)
        }

    # ==================== VOLATILITY INDICATORS ====================

    @staticmethod
    def calculate_bollinger_bands(
        prices: Union[pd.Series, np.ndarray],
        period: int = 20,
        std_dev: float = 2.0
    ) -> Dict[str, pd.Series]:
        """
        Calculate Bollinger Bands.
        
        Bollinger Bands consist of a middle band (SMA) and upper/lower bands
        at a specified number of standard deviations away.
        
        Args:
            prices: Series of closing prices
            period: SMA period (default 20)
            std_dev: Standard deviation multiplier (default 2)
            
        Returns:
            Dict with 'upper', 'middle', 'lower', 'bandwidth', 'percent_b'
        """
        prices = pd.Series(prices)
        
        middle = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        
        bandwidth = (upper - lower) / middle * 100
        percent_b = (prices - lower) / (upper - lower) * 100
        
        return {
            'upper': upper,
            'middle': middle,
            'lower': lower,
            'bandwidth': bandwidth.fillna(0),
            'percent_b': percent_b.fillna(50)
        }

    @staticmethod
    def calculate_atr(
        high: Union[pd.Series, np.ndarray],
        low: Union[pd.Series, np.ndarray],
        close: Union[pd.Series, np.ndarray],
        period: int = 14
    ) -> pd.Series:
        """
        Calculate Average True Range (ATR).
        
        ATR measures volatility by decomposing the entire range of an asset.
        Higher ATR indicates higher volatility.
        
        Args:
            high: High prices
            low: Low prices
            close: Closing prices
            period: ATR period (default 14)
            
        Returns:
            pd.Series: ATR values
        """
        high = pd.Series(high)
        low = pd.Series(low)
        close = pd.Series(close)
        
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        return atr

    # ==================== VOLUME INDICATORS ====================

    @staticmethod
    def calculate_obv(
        prices: Union[pd.Series, np.ndarray],
        volume: Union[pd.Series, np.ndarray]
    ) -> pd.Series:
        """
        Calculate On-Balance Volume (OBV).
        
        OBV uses volume flow to predict changes in stock price.
        Rising OBV suggests buying pressure, falling OBV suggests selling pressure.
        
        Args:
            prices: Closing prices
            volume: Trading volume
            
        Returns:
            pd.Series: OBV values
        """
        prices = pd.Series(prices)
        volume = pd.Series(volume)
        
        direction = np.sign(prices.diff())
        direction.iloc[0] = 0
        
        obv = (direction * volume).cumsum()
        return obv

    @staticmethod
    def calculate_vwap(
        high: Union[pd.Series, np.ndarray],
        low: Union[pd.Series, np.ndarray],
        close: Union[pd.Series, np.ndarray],
        volume: Union[pd.Series, np.ndarray]
    ) -> pd.Series:
        """
        Calculate Volume Weighted Average Price (VWAP).
        
        VWAP gives the average price weighted by volume.
        Prices above VWAP suggest bullish sentiment, below suggest bearish.
        
        Args:
            high: High prices
            low: Low prices
            close: Closing prices
            volume: Trading volume
            
        Returns:
            pd.Series: VWAP values
        """
        typical_price = (pd.Series(high) + pd.Series(low) + pd.Series(close)) / 3
        volume = pd.Series(volume)
        
        vwap = (typical_price * volume).cumsum() / volume.cumsum()
        return vwap

    # ==================== SUPPORT/RESISTANCE ====================

    @staticmethod
    def find_support_resistance(
        prices: Union[pd.Series, np.ndarray],
        window: int = 10,
        num_levels: int = 3
    ) -> Dict[str, List[float]]:
        """
        Find key support and resistance levels using local minima/maxima.
        
        Args:
            prices: Price series
            window: Window for finding local extrema
            num_levels: Number of levels to return
            
        Returns:
            Dict with 'support' and 'resistance' level lists
        """
        prices = pd.Series(prices)
        
        # Find local minima (support)
        local_min = prices.iloc[
            (prices.shift(window) > prices) & 
            (prices.shift(-window) > prices)
        ].dropna()
        
        # Find local maxima (resistance)
        local_max = prices.iloc[
            (prices.shift(window) < prices) & 
            (prices.shift(-window) < prices)
        ].dropna()
        
        # Get unique levels, sorted
        support_levels = sorted(local_min.unique())[:num_levels] if len(local_min) > 0 else []
        resistance_levels = sorted(local_max.unique(), reverse=True)[:num_levels] if len(local_max) > 0 else []
        
        return {
            'support': [round(s, 2) for s in support_levels],
            'resistance': [round(r, 2) for r in resistance_levels]
        }

    @staticmethod
    def calculate_pivot_points(
        high: float,
        low: float,
        close: float
    ) -> Dict[str, float]:
        """
        Calculate standard pivot points for a trading session.
        
        Pivot points are used to predict support and resistance levels.
        
        Args:
            high: Previous session high
            low: Previous session low
            close: Previous session close
            
        Returns:
            Dict with pivot, support (s1-s3), and resistance (r1-r3) levels
        """
        pivot = (high + low + close) / 3
        
        r1 = (2 * pivot) - low
        r2 = pivot + (high - low)
        r3 = high + 2 * (pivot - low)
        
        s1 = (2 * pivot) - high
        s2 = pivot - (high - low)
        s3 = low - 2 * (high - pivot)
        
        return {
            'pivot': round(pivot, 2),
            'r1': round(r1, 2),
            'r2': round(r2, 2),
            'r3': round(r3, 2),
            's1': round(s1, 2),
            's2': round(s2, 2),
            's3': round(s3, 2)
        }

    # ==================== PATTERN RECOGNITION ====================

    @staticmethod
    def detect_golden_cross(
        sma_50: Union[pd.Series, np.ndarray],
        sma_200: Union[pd.Series, np.ndarray]
    ) -> pd.Series:
        """
        Detect Golden Cross (bullish signal).
        
        A golden cross occurs when the 50-day SMA crosses above the 200-day SMA.
        
        Args:
            sma_50: 50-day SMA series
            sma_200: 200-day SMA series
            
        Returns:
            pd.Series: Boolean series where True indicates a golden cross
        """
        sma_50 = pd.Series(sma_50)
        sma_200 = pd.Series(sma_200)
        
        # Golden cross: 50 crosses above 200
        golden_cross = (sma_50 > sma_200) & (sma_50.shift(1) <= sma_200.shift(1))
        return golden_cross.fillna(False)

    @staticmethod
    def detect_death_cross(
        sma_50: Union[pd.Series, np.ndarray],
        sma_200: Union[pd.Series, np.ndarray]
    ) -> pd.Series:
        """
        Detect Death Cross (bearish signal).
        
        A death cross occurs when the 50-day SMA crosses below the 200-day SMA.
        
        Args:
            sma_50: 50-day SMA series
            sma_200: 200-day SMA series
            
        Returns:
            pd.Series: Boolean series where True indicates a death cross
        """
        sma_50 = pd.Series(sma_50)
        sma_200 = pd.Series(sma_200)
        
        # Death cross: 50 crosses below 200
        death_cross = (sma_50 < sma_200) & (sma_50.shift(1) >= sma_200.shift(1))
        return death_cross.fillna(False)

    @staticmethod
    def identify_trend(
        prices: Union[pd.Series, np.ndarray],
        period: int = 20
    ) -> str:
        """
        Identify the current trend direction.
        
        Uses moving average slope and price position to determine trend.
        
        Args:
            prices: Price series
            period: Period for trend detection
            
        Returns:
            str: "uptrend", "downtrend", or "sideways"
        """
        prices = pd.Series(prices)
        
        if len(prices) < period + 5:
            return "sideways"
        
        sma = prices.rolling(window=period).mean()
        sma_slope = sma.diff(5).iloc[-1]
        
        current_price = prices.iloc[-1]
        sma_current = sma.iloc[-1]
        
        # Calculate percentage differences
        slope_threshold = sma_current * 0.001  # 0.1% threshold
        
        if sma_slope > slope_threshold and current_price > sma_current:
            return "uptrend"
        elif sma_slope < -slope_threshold and current_price < sma_current:
            return "downtrend"
        else:
            return "sideways"

    # ==================== SIGNAL GENERATION ====================

    @staticmethod
    def generate_signals(
        close: pd.Series,
        high: Optional[pd.Series] = None,
        low: Optional[pd.Series] = None,
        volume: Optional[pd.Series] = None
    ) -> Dict[str, SignalResult]:
        """
        Generate comprehensive trading signals based on multiple indicators.
        
        Args:
            close: Closing prices
            high: High prices (optional)
            low: Low prices (optional)
            volume: Volume (optional)
            
        Returns:
            Dict of indicator names to SignalResult objects
        """
        signals = {}
        
        # RSI Signal
        rsi = TechnicalIndicators.calculate_rsi(close)
        current_rsi = rsi.iloc[-1]
        
        if current_rsi > 70:
            signals['rsi'] = SignalResult("sell", 80, "RSI indicates overbought condition")
        elif current_rsi < 30:
            signals['rsi'] = SignalResult("buy", 80, "RSI indicates oversold condition")
        else:
            signals['rsi'] = SignalResult("hold", 50, "RSI in neutral zone")
        
        # MACD Signal
        macd = TechnicalIndicators.calculate_macd(close)
        macd_hist = macd['histogram'].iloc[-1]
        macd_hist_prev = macd['histogram'].iloc[-2] if len(macd['histogram']) > 1 else 0
        
        if macd_hist > 0 and macd_hist > macd_hist_prev:
            signals['macd'] = SignalResult("buy", 70, "MACD histogram rising above zero")
        elif macd_hist < 0 and macd_hist < macd_hist_prev:
            signals['macd'] = SignalResult("sell", 70, "MACD histogram falling below zero")
        else:
            signals['macd'] = SignalResult("hold", 50, "MACD histogram neutral")
        
        # Trend Signal
        trend = TechnicalIndicators.identify_trend(close)
        if trend == "uptrend":
            signals['trend'] = SignalResult("buy", 60, "Price in uptrend")
        elif trend == "downtrend":
            signals['trend'] = SignalResult("sell", 60, "Price in downtrend")
        else:
            signals['trend'] = SignalResult("hold", 50, "Price moving sideways")
        
        # Bollinger Bands Signal
        bb = TechnicalIndicators.calculate_bollinger_bands(close)
        current_price = close.iloc[-1]
        
        if current_price > bb['upper'].iloc[-1]:
            signals['bollinger'] = SignalResult("sell", 65, "Price above upper Bollinger Band")
        elif current_price < bb['lower'].iloc[-1]:
            signals['bollinger'] = SignalResult("buy", 65, "Price below lower Bollinger Band")
        else:
            signals['bollinger'] = SignalResult("hold", 50, "Price within Bollinger Bands")
        
        # SMA Cross Signal
        smas = TechnicalIndicators.calculate_sma(close, [50, 200])
        if len(close) >= 200:
            golden = TechnicalIndicators.detect_golden_cross(smas['sma_50'], smas['sma_200'])
            death = TechnicalIndicators.detect_death_cross(smas['sma_50'], smas['sma_200'])
            
            if golden.iloc[-1]:
                signals['sma_cross'] = SignalResult("buy", 90, "Golden cross detected")
            elif death.iloc[-1]:
                signals['sma_cross'] = SignalResult("sell", 90, "Death cross detected")
            elif smas['sma_50'].iloc[-1] > smas['sma_200'].iloc[-1]:
                signals['sma_cross'] = SignalResult("buy", 55, "50 SMA above 200 SMA")
            else:
                signals['sma_cross'] = SignalResult("sell", 55, "50 SMA below 200 SMA")
        
        return signals

    @staticmethod
    def get_overall_signal(signals: Dict[str, SignalResult]) -> SignalResult:
        """
        Calculate overall signal from multiple indicators.
        
        Args:
            signals: Dict of indicator signals
            
        Returns:
            SignalResult: Aggregated signal with weighted average
        """
        if not signals:
            return SignalResult("hold", 50, "Insufficient data for analysis")
        
        buy_score = 0
        sell_score = 0
        hold_score = 0
        
        for signal in signals.values():
            if signal.signal == "buy":
                buy_score += signal.strength
            elif signal.signal == "sell":
                sell_score += signal.strength
            else:
                hold_score += signal.strength
        
        total = buy_score + sell_score + hold_score
        
        if buy_score > sell_score and buy_score > hold_score:
            return SignalResult(
                "buy",
                round(buy_score / total * 100, 1),
                f"Bullish signals from {sum(1 for s in signals.values() if s.signal == 'buy')} indicators"
            )
        elif sell_score > buy_score and sell_score > hold_score:
            return SignalResult(
                "sell",
                round(sell_score / total * 100, 1),
                f"Bearish signals from {sum(1 for s in signals.values() if s.signal == 'sell')} indicators"
            )
        else:
            return SignalResult(
                "hold",
                round(hold_score / total * 100, 1),
                "Mixed signals - consider waiting"
            )


# Convenience function for quick analysis
def analyze_stock(
    close: pd.Series,
    high: Optional[pd.Series] = None,
    low: Optional[pd.Series] = None,
    volume: Optional[pd.Series] = None
) -> Dict:
    """
    Perform comprehensive technical analysis on a stock.
    
    Args:
        close: Closing prices
        high: High prices (optional)
        low: Low prices (optional)
        volume: Volume (optional)
        
    Returns:
        Dict with all calculated indicators and signals
    """
    ti = TechnicalIndicators
    
    result = {
        'rsi': ti.calculate_rsi(close).iloc[-1],
        'macd': {k: v.iloc[-1] for k, v in ti.calculate_macd(close).items()},
        'sma': {k: v.iloc[-1] for k, v in ti.calculate_sma(close).items()},
        'ema': {k: v.iloc[-1] for k, v in ti.calculate_ema(close).items()},
        'bollinger': {k: v.iloc[-1] for k, v in ti.calculate_bollinger_bands(close).items()},
        'trend': ti.identify_trend(close),
    }
    
    if high is not None and low is not None:
        result['stochastic'] = {k: v.iloc[-1] for k, v in ti.calculate_stochastic(high, low, close).items()}
        result['atr'] = ti.calculate_atr(high, low, close).iloc[-1]
        
        if len(close) > 0:
            result['pivot_points'] = ti.calculate_pivot_points(
                high.iloc[-1], low.iloc[-1], close.iloc[-1]
            )
    
    if volume is not None:
        result['obv'] = ti.calculate_obv(close, volume).iloc[-1]
        if high is not None and low is not None:
            result['vwap'] = ti.calculate_vwap(high, low, close, volume).iloc[-1]
    
    # Generate signals
    signals = ti.generate_signals(close, high, low, volume)
    result['signals'] = {k: {'signal': v.signal, 'strength': v.strength, 'reason': v.reason} 
                         for k, v in signals.items()}
    result['overall_signal'] = ti.get_overall_signal(signals)
    
    return result
