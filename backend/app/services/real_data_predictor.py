import os
import sys
import json
import asyncio
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
import pandas as pd
import yfinance as yf

# Add project root and ml-models to path for integration
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'ml-models'))

# Custom TensorFlow path
custom_tf_path = r"C:\Users\Janmejay Singh\tf"
if os.path.exists(custom_tf_path) and custom_tf_path not in sys.path:
    sys.path.append(custom_tf_path)

from app.config import settings
from app.utils.logging import logger
from app.utils.market_utils import get_next_trading_day

# Try to import EnsemblePredictor
try:
    from ensemble_model import EnsemblePredictor
    ENSEMBLE_AVAILABLE = True
except ImportError:
    ENSEMBLE_AVAILABLE = False
    logger.warning("ensemble_model_not_found", message="Falling back to pure technical analysis")


class RealDataPredictor:
    """
    Stock prediction service using real market data and ML models.
    Combines technical analysis with ensemble ML predictions.
    """
    
    def __init__(self, model_base_path: Optional[str] = None):
        # Resolve path relative to project root if it exists
        if model_base_path:
            self.model_base_path = model_base_path
        else:
             # Look for models in the project root's ml-models folder
            potential_path = os.path.join(project_root, 'ml-models', 'saved_models')
            if os.path.exists(potential_path):
                self.model_base_path = potential_path
            else:
                self.model_base_path = "saved_models"
                
        self._loaded_models: Dict[str, Any] = {}
        self._metadata: Dict[str, Dict] = {}
        self._data_cache: Dict[str, Tuple[pd.DataFrame, datetime]] = {}
        self._cache_ttl = 300  # 5 minutes
        self._tf_available = False
        
        # Initialize Ensemble Predictor if available
        self.ensemble = None
        if ENSEMBLE_AVAILABLE:
            try:
                self.ensemble = EnsemblePredictor(models_dir=self.model_base_path)
                logger.info("ensemble_predictor_initialized", path=self.model_base_path)
            except Exception as e:
                logger.error("ensemble_init_error", error=str(e))
        
        # Check TensorFlow availability for technical info
        try:
            import tensorflow
            self._tf_available = True
            logger.info("tensorflow_available", version=tensorflow.__version__)
        except ImportError:
            logger.warning("tensorflow_not_installed", message="Deep learning models will be skipped")
    
    def _get_yf_symbol(self, symbol: str, exchange: str = "NSE") -> str:
        """Convert symbol to Yahoo Finance format."""
        symbol = symbol.upper().strip()
        if symbol.endswith('.NS') or symbol.endswith('.BO'):
            return symbol
        if exchange.upper() == "NSE":
            return f"{symbol}.NS"
        elif exchange.upper() == "BSE":
            return f"{symbol}.BO"
        return symbol
    
    async def _fetch_historical_data(
        self, 
        symbol: str, 
        period: str = "6mo",
        exchange: str = "NSE"
    ) -> pd.DataFrame:
        """Fetch historical data with caching."""
        cache_key = f"{symbol}_{exchange}_{period}"
        
        # Check cache
        if cache_key in self._data_cache:
            df, cached_at = self._data_cache[cache_key]
            if (datetime.now() - cached_at).seconds < self._cache_ttl:
                return df
        
        # Fetch from Yahoo Finance
        yf_symbol = self._get_yf_symbol(symbol, exchange)
        
        try:
            loop = asyncio.get_event_loop()
            ticker = await loop.run_in_executor(None, lambda: yf.Ticker(yf_symbol))
            df = await loop.run_in_executor(None, lambda: ticker.history(period=period))
            
            if not df.empty:
                self._data_cache[cache_key] = (df, datetime.now())
                return df
        except Exception as e:
            logger.error("fetch_historical_error", symbol=symbol, error=str(e))
        
        return pd.DataFrame()
    
    def _calculate_technical_indicators(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate technical indicators for prediction."""
        if df.empty or len(df) < 20:
            return {}
        
        close = df['Close']
        high = df['High']
        low = df['Low']
        volume = df['Volume']
        
        indicators = {}
        
        # Moving Averages
        indicators['sma_5'] = float(close.rolling(window=5).mean().iloc[-1])
        indicators['sma_10'] = float(close.rolling(window=10).mean().iloc[-1])
        indicators['sma_20'] = float(close.rolling(window=20).mean().iloc[-1])
        indicators['sma_50'] = float(close.rolling(window=50).mean().iloc[-1]) if len(close) >= 50 else indicators['sma_20']
        
        # EMA
        indicators['ema_20'] = float(close.ewm(span=20, adjust=False).mean().iloc[-1])
        
        # RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        indicators['rsi'] = float(100 - (100 / (1 + rs)).iloc[-1]) if not pd.isna(rs.iloc[-1]) else 50.0
        
        # MACD
        ema_12 = close.ewm(span=12, adjust=False).mean()
        ema_26 = close.ewm(span=26, adjust=False).mean()
        indicators['macd'] = float((ema_12 - ema_26).iloc[-1])
        indicators['macd_signal'] = float((ema_12 - ema_26).ewm(span=9, adjust=False).mean().iloc[-1])
        
        # Bollinger Bands
        sma_20 = close.rolling(window=20).mean()
        std_20 = close.rolling(window=20).std()
        indicators['bb_upper'] = float((sma_20 + (std_20 * 2)).iloc[-1])
        indicators['bb_lower'] = float((sma_20 - (std_20 * 2)).iloc[-1])
        
        # Volatility & Momentum
        indicators['volatility'] = float((close.pct_change().rolling(20).std() * np.sqrt(252) * 100).iloc[-1])
        indicators['momentum_5'] = float((close / close.shift(5) - 1).iloc[-1] * 100)
        
        # Volume features
        avg_volume = volume.rolling(20).mean().iloc[-1]
        indicators['volume_ratio'] = float(volume.iloc[-1] / avg_volume) if avg_volume > 0 else 1.0
        
        # ATR
        high_low = high - low
        high_cp = (high - close.shift(1)).abs()
        low_cp = (low - close.shift(1)).abs()
        tr = pd.concat([high_low, high_cp, low_cp], axis=1).max(axis=1)
        indicators['atr'] = float(tr.rolling(window=14).mean().iloc[-1])
        
        return indicators

    def _generate_prediction(
        self, 
        current_price: float, 
        indicators: Dict[str, float],
        days_ahead: int = 1
    ) -> Tuple[float, str, float]:
        """
        Generate price prediction using technical indicators.
        Returns: (predicted_price, quality, confidence_score)
        """
        if not indicators:
            change = np.random.normal(0.1, 1.5) * days_ahead
            return current_price * (1 + change / 100), "low", 50.0
        
        signals = []
        weights = []
        
        # SMA Crossover
        if indicators.get('sma_5') and indicators.get('sma_20'):
            signals.append(1 if indicators['sma_5'] > indicators['sma_20'] else -1)
            weights.append(0.2)
        
        # RSI
        rsi = indicators.get('rsi', 50)
        if rsi < 35: signals.append(1.0); weights.append(0.2)
        elif rsi > 65: signals.append(-1.0); weights.append(0.2)
        else: signals.append(0.2 if rsi > 50 else -0.2); weights.append(0.1)
        
        # MACD
        macd = indicators.get('macd', 0)
        signal = indicators.get('macd_signal', 0)
        if macd > signal: signals.append(0.5); weights.append(0.15)
        else: signals.append(-0.5); weights.append(0.15)
        
        # BB
        up, lo = indicators.get('bb_upper', 0), indicators.get('bb_lower', 0)
        if up != lo:
            pos = (current_price - lo) / (up - lo)
            if pos < 0.2: signals.append(1.0); weights.append(0.15)
            elif pos > 0.8: signals.append(-1.0); weights.append(0.15)
        
        # Momentum
        mom = indicators.get('momentum_5', 0)
        signals.append(np.clip(mom / 10, -1, 1)); weights.append(0.15)
        
        # Calculate ensemble signal
        total_weight = sum(weights)
        weighted_signal = sum(s * w for s, w in zip(signals, weights)) / total_weight if total_weight > 0 else 0
        
        volatility = indicators.get('volatility', 20) / 100
        daily_vol = volatility / np.sqrt(252)
        
        # Predicted change
        predicted_change = weighted_signal * daily_vol * 100 * days_ahead
        predicted_change += np.random.normal(0, daily_vol * 20)
        
        predicted_price = current_price * (1 + predicted_change / 100)
        
        score = 50 + (abs(weighted_signal) * 30)
        if indicators.get('volume_ratio', 1) > 1.2: score += 5
        score = min(95, max(30, score - (days_ahead - 1) * 4))
        
        quality = "high" if score >= 75 else "medium" if score >= 55 else "low"
        
        return predicted_price, quality, score

    async def predict_next_day(
        self, 
        symbol: str,
        exchange: str = "NSE"
    ) -> Optional[Dict[str, Any]]:
        """Predict next trading day's price using Hybrid ML/Technical approach."""
        symbol = symbol.upper()
        logger.info("predict_next_day", symbol=symbol, exchange=exchange)
        
        df = await self._fetch_historical_data(symbol, period="6mo", exchange=exchange)
        if df.empty:
            return await self._fallback_prediction(symbol)
        
        current_price = float(df['Close'].iloc[-1])
        indicators = self._calculate_technical_indicators(df)
        
        # Attempt ML Ensemble Prediction
        ml_result = None
        is_demo = True
        
        if self.ensemble:
            try:
                loop = asyncio.get_event_loop()
                ml_result = await loop.run_in_executor(None, lambda: self.ensemble.ensemble_predict(symbol, df))
                is_demo = ml_result.model_contributions.get("demo") is not None
            except Exception as e:
                logger.error("ml_prediction_failed", symbol=symbol, error=str(e))
        
        if ml_result and not is_demo:
            predicted_price = ml_result.predicted_price
            confidence_score = ml_result.confidence
            quality = ml_result.quality
            change_pct = ml_result.change_percent
            model_contributions = ml_result.model_contributions
            upper_bound = ml_result.upper_bound
            lower_bound = ml_result.lower_bound
        else:
            predicted_price, quality, confidence_score = self._generate_prediction(current_price, indicators)
            change_pct = ((predicted_price - current_price) / current_price) * 100
            model_contributions = {"technical_analysis": 100.0}
            atr = indicators.get('atr', current_price * 0.02)
            upper_bound = predicted_price + atr * 1.5
            lower_bound = predicted_price - atr * 1.5
            is_demo = True

        return {
            "symbol": symbol,
            "name": f"{symbol} Industries Ltd",
            "current_price": round(current_price, 2),
            "predicted_price": round(predicted_price, 2),
            "change": round(predicted_price - current_price, 2),
            "change_percent": round(change_pct, 2),
            "trend": "up" if change_pct >= 0 else "down",
            "confidence": round(confidence_score, 1),
            "quality": quality,
            "is_demo": is_demo,
            "model_contributions": model_contributions,
            "signals": {
                "rsi": "buy" if indicators.get('rsi', 50) < 35 else "sell" if indicators.get('rsi', 50) > 65 else "hold",
                "macd": "buy" if indicators.get('macd', 0) > indicators.get('macd_signal', 0) else "sell",
                "sma": "buy" if indicators.get('sma_5', 0) > indicators.get('sma_20', 0) else "sell",
                "bb": "buy" if current_price < indicators.get('bb_lower', 0) else "sell" if current_price > indicators.get('bb_upper', 0) else "hold"
            },
            "forecast": await self._generate_forecast_list(current_price, predicted_price, upper_bound, lower_bound),
            "prediction_date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
            "last_updated": datetime.utcnow().isoformat() + "Z"
        }

    async def _generate_forecast_list(self, current: float, target: float, upper: float, lower: float) -> List[Dict]:
        forecast = []
        for i in range(1, 8):
            weight = i / 7
            day_price = current * (1 - weight) + target * weight
            day_price += np.random.normal(0, (upper - lower) / 20)
            spread = (upper - lower) * (0.5 + weight * 0.5)
            forecast.append({
                "date": (datetime.now() + timedelta(days=i)).strftime("%d %b"),
                "predicted": round(day_price, 2),
                "upper": round(day_price + spread / 2, 2),
                "lower": round(day_price - spread / 2, 2)
            })
        return forecast

    async def predict_weekly(self, symbol: str, exchange: str = "NSE") -> Optional[Dict[str, Any]]:
        return await self.predict_next_day(symbol, exchange)

    async def predict_crypto(self, crypto_id: str) -> Optional[Dict[str, Any]]:
        symbol = f"{crypto_id.upper()}-USD"
        df = await self._fetch_historical_data(symbol, period="6mo", exchange="CRYPTO")
        if df.empty: return None
        current_price = float(df['Close'].iloc[-1])
        indicators = self._calculate_technical_indicators(df)
        try:
            loop = asyncio.get_event_loop()
            usdinr = await loop.run_in_executor(None, lambda: yf.Ticker("USDINR=X").history(period="1d"))
            exchange_rate = float(usdinr['Close'].iloc[-1]) if not usdinr.empty else 83.5
        except:
            exchange_rate = 83.5
        predicted_price, quality, score = self._generate_prediction(current_price, indicators)
        change_pct = ((predicted_price - current_price) / current_price) * 100
        atr = indicators.get('atr', current_price * 0.05)
        return {
            "symbol": crypto_id.upper(),
            "name": crypto_id.title(),
            "current_price": round(current_price * exchange_rate, 2),
            "predicted_price": round(predicted_price * exchange_rate, 2),
            "change_percent": round(change_pct, 2),
            "confidence": round(score, 1),
            "quality": quality,
            "is_demo": True,
            "signals": {
                "rsi": "buy" if indicators.get('rsi', 50) < 35 else "sell" if indicators.get('rsi', 50) > 65 else "hold",
                "macd": "buy" if indicators.get('macd', 0) > indicators.get('macd_signal', 0) else "sell",
                "sma": "buy" if indicators.get('sma_5', 0) > indicators.get('sma_20', 0) else "sell",
                "bb": "buy" if current_price < indicators.get('bb_lower', 0) else "sell" if current_price > indicators.get('bb_upper', 0) else "hold"
            },
            "forecast": await self._generate_forecast_list(current_price * exchange_rate, predicted_price * exchange_rate, (predicted_price+atr) * exchange_rate, (predicted_price-atr) * exchange_rate),
            "last_updated": datetime.utcnow().isoformat() + "Z"
        }

    async def predict_commodity(self, commodity: str) -> Optional[Dict[str, Any]]:
        mapping = {"gold": "GC=F", "silver": "SI=F", "crude_oil": "CL=F", "platinum": "PL=F", "copper": "HG=F"}
        symbol = mapping.get(commodity.lower())
        if not symbol: return None
        df = await self._fetch_historical_data(symbol, period="6mo", exchange="COMMODITY")
        if df.empty: return None
        current_price = float(df['Close'].iloc[-1])
        indicators = self._calculate_technical_indicators(df)
        predicted_price, quality, score = self._generate_prediction(current_price, indicators)
        return {
            "symbol": commodity.upper(),
            "current_price": round(current_price, 2),
            "predicted_price": round(predicted_price, 2),
            "change_percent": round(((predicted_price - current_price) / current_price) * 100, 2),
            "confidence": score,
            "quality": quality,
            "is_demo": True,
            "last_updated": datetime.utcnow().isoformat() + "Z"
        }

    async def _fallback_prediction(self, symbol: str) -> Dict[str, Any]:
        res = await self._fallback_weekly_prediction(symbol)
        res["quality"] = "low"
        res["confidence"] = 40.0
        res["is_demo"] = True
        return res

    async def _fallback_weekly_prediction(self, symbol: str) -> Dict[str, Any]:
        np.random.seed(hash(symbol + "weekly") % 2**32)
        base_price = 1500 + np.random.random() * 1000
        predictions = []
        price = base_price
        for day in range(1, 8):
            change = np.random.normal(0.1, 1.0)
            price = price * (1 + change / 100)
            predictions.append({
                "date": (datetime.now() + timedelta(days=day)).strftime("%d %b"),
                "predicted": round(price, 2),
                "upper": round(price * 1.02, 2),
                "lower": round(price * 0.98, 2)
            })
        final_price = predictions[-1]["predicted"]
        return {
            "symbol": symbol.upper(),
            "name": f"{symbol} (Simulated)",
            "current_price": round(base_price, 2),
            "predicted_price": round(final_price, 2),
            "change_percent": round(((final_price - base_price) / base_price) * 100, 2),
            "forecast": predictions,
            "is_demo": True,
            "last_updated": datetime.utcnow().isoformat() + "Z"
        }

# Singleton instance
real_data_predictor = RealDataPredictor()
