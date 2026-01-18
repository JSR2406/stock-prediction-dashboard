# 📊 Real-Time Data Integration Requirements

## Overview

This document outlines the requirements and setup for obtaining **real, live market data** that updates 24/7 for the Stock Prediction Dashboard. The system supports:

- **Indian Stocks** (NSE/BSE)
- **Cryptocurrencies** (Bitcoin, Ethereum, etc.)
- **Commodities** (Gold, Silver, Crude Oil)

---

## 🔑 Required API Keys & Services

### 1. Stock Market Data (NSE/BSE)

#### Primary: Yahoo Finance (yfinance)
- **Status**: ✅ **FREE - No API key required**
- **Coverage**: NSE, BSE, global stocks
- **Update Frequency**: 15-minute delay for free tier
- **Rate Limits**: ~2000 requests/hour
- **Usage**: Already integrated in `data_fetcher.py`

#### Premium Alternative: Alpha Vantage
- **Website**: [alphavantage.co](https://www.alphavantage.co/support/#api-key)
- **Free Tier**: 25 requests/day
- **Premium**: Starting $49.99/month for real-time data
- **Setup**: Add `ALPHA_VANTAGE_KEY=your_key` to `.env`

#### Premium Alternative: NSE Official API
- **Website**: [nseindia.com](https://www.nseindia.com/)
- **Note**: NSE has restricted their official API, best accessed via web scraping or data vendors
- **Alternative**: Upstox, Zerodha, Angel Broking APIs (broker accounts required)

---

### 2. Cryptocurrency Data

#### Primary: CoinGecko API
- **Website**: [coingecko.com](https://www.coingecko.com/en/api)
- **Free Tier**: ✅ **FREE - 10-30 calls/minute**
- **Pro Tier**: $129/month for higher limits
- **Update Frequency**: Real-time (seconds delay)
- **Coverage**: 10,000+ cryptocurrencies
- **Setup** (optional for higher limits):
  ```env
  COINGECKO_API_KEY=your_demo_api_key
  ```

#### Alternative: CoinMarketCap
- **Website**: [coinmarketcap.com/api](https://coinmarketcap.com/api/)
- **Free Tier**: 10,000 calls/month
- **Pro Tier**: Starting $79/month
- **Setup**: Add `COINMARKETCAP_KEY=your_key` to `.env`

---

### 3. Commodities (Gold, Silver, Crude Oil)

#### Primary: Metals-API
- **Website**: [metals-api.com](https://metals-api.com/)
- **Free Tier**: 100 requests/month
- **Basic Plan**: $14.99/month (1000 requests)
- **Pro Plan**: $79.99/month (unlimited)
- **Setup**:
  ```env
  METALS_API_KEY=your_metals_api_key
  ```

#### Alternative: GoldAPI
- **Website**: [goldapi.io](https://www.goldapi.io/)
- **Free Tier**: 300 requests/month
- **Premium**: Starting $9.99/month

#### Fallback: Yahoo Finance
- **Status**: ✅ **FREE - Already implemented**
- **Symbols**: `GC=F` (Gold), `SI=F` (Silver), `CL=F` (Crude Oil)
- **Note**: Provides USD prices, converted to INR using USDINR rate

---

## 📋 Environment Configuration

Create/update your `.env` file in the `backend` directory:

```env
# =================================================
# Stock Prediction Dashboard - Production Config
# =================================================

# Application Settings
APP_NAME=Stock Prediction Dashboard API
APP_VERSION=1.0.0
DEBUG=false
ENVIRONMENT=production

# Server Settings
HOST=0.0.0.0
PORT=8000

# CORS Origins
CORS_ORIGINS=["https://yourdomain.com", "http://localhost:3000"]

# =================================================
# API KEYS - Get these for real-time data
# =================================================

# Metals-API (Gold, Silver, Commodities)
# Get free key at: https://metals-api.com/
METALS_API_KEY=your_metals_api_key_here

# Alpha Vantage (Stock data - optional)
# Get free key at: https://www.alphavantage.co/support/#api-key
ALPHA_VANTAGE_KEY=your_alpha_vantage_key_here

# CoinGecko (Crypto - optional, for higher rate limits)
# Get demo key at: https://www.coingecko.com/en/api
COINGECKO_API_KEY=

# =================================================
# Redis (Required for production caching)
# =================================================

# Local Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# OR Cloud Redis (e.g., Redis Cloud, AWS ElastiCache)
# REDIS_HOST=your-redis-host.cloud.redislabs.com
# REDIS_PORT=12345
# REDIS_PASSWORD=your_password
# REDIS_SSL=true

# Cache TTL in seconds (5 minutes default)
CACHE_TTL=300

# =================================================
# Machine Learning Models
# =================================================

MODEL_BASE_PATH=ml-models/saved_models

# =================================================
# Rate Limiting
# =================================================

RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# =================================================
# Market Settings
# =================================================

DEFAULT_MARKET=NSE
MARKET_TIMEZONE=Asia/Kolkata
```

---

## 🔄 Data Update Frequencies

| Data Type | Source | Update Frequency | API Limit |
|-----------|--------|-----------------|-----------|
| Indian Stocks | Yahoo Finance | 15-min delay (free) | ~2000/hour |
| NIFTY/SENSEX | Yahoo Finance | 15-min delay | ~2000/hour |
| Crypto | CoinGecko | Real-time | 10-30/min (free) |
| Gold/Silver | Metals-API | Real-time | 100/month (free) |
| Gold/Silver | Yahoo Finance | 15-min delay | ~2000/hour |

---

## 🏗️ Architecture for 24/7 Live Updates

### Option 1: Polling (Current Implementation)
```
Frontend → API (every 1 min) → Cache → External APIs
```
- **Pros**: Simple, works with free APIs
- **Cons**: Not truly real-time

### Option 2: WebSocket (Real-time)
```
Frontend ←WebSocket→ Backend ←Poll→ External APIs
```
- Backend polls APIs every 30 seconds
- Broadcasts updates via WebSocket to all clients
- **Already implemented** in `websocket_manager.py`

### Option 3: Premium Real-time Feeds
```
Frontend ←WebSocket→ Backend ←WebSocket→ Premium API
```
- Requires paid broker API (Zerodha Kite, Upstox, Angel)
- True tick-by-tick data
- **Cost**: ₹2000-5000/month for broker subscription

---

## 📝 Setup Steps

### Step 1: Get Free API Keys

1. **Metals-API** (for Gold/Silver):
   - Go to [metals-api.com](https://metals-api.com/)
   - Sign up for free account
   - Copy API key to `.env`

2. **Alpha Vantage** (optional, for stocks):
   - Go to [alphavantage.co/support/#api-key](https://www.alphavantage.co/support/#api-key)
   - Get free API key
   - Add to `.env`

3. **CoinGecko** (optional, for higher crypto limits):
   - Go to [coingecko.com/en/api](https://www.coingecko.com/en/api)
   - Create demo account
   - Add key to `.env`

### Step 2: Install Redis (for caching)

**Windows:**
```powershell
# Using WSL or Docker
docker run -d --name redis -p 6379:6379 redis:alpine
```

**Linux/Mac:**
```bash
# Ubuntu/Debian
sudo apt install redis-server
sudo systemctl start redis

# Mac
brew install redis
brew services start redis
```

### Step 3: Configure Environment
```bash
cd backend
cp .env.example .env
# Edit .env with your API keys
```

### Step 4: Start the Application
```bash
# Backend
cd backend
.\venv\Scripts\activate
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm run dev
```

---

## 🚀 Premium Upgrade Path

For truly **real-time, tick-by-tick data**, consider:

### Indian Markets (NSE/BSE)

| Provider | Type | Cost | Features |
|----------|------|------|----------|
| **Zerodha Kite** | Broker API | ₹2000/month | Real-time, WebSocket |
| **Upstox Pro** | Broker API | ₹500/month | Real-time, historical |
| **Angel Broking** | Broker API | Free (with account) | Real-time streaming |
| **TrueData** | Data Vendor | ₹2000/month | Tick data, historical |

### Crypto

| Provider | Type | Cost | Features |
|----------|------|------|----------|
| **CoinGecko Pro** | API | $129/month | 1000 req/min |
| **CoinMarketCap Pro** | API | $79/month | Real-time |
| **Binance API** | Exchange | Free | Real-time WebSocket |

### Commodities

| Provider | Type | Cost | Features |
|----------|------|------|----------|
| **Metals-API Pro** | API | $79.99/month | Unlimited requests |
| **MCX API** | Exchange | Contact sales | Official prices |

---

## ⚠️ Important Notes

1. **Rate Limiting**: The application implements caching to avoid hitting API rate limits
2. **Market Hours**: Indian stock market hours: 9:15 AM - 3:30 PM IST (Mon-Fri)
3. **Crypto**: Trades 24/7, data always available
4. **Commodities**: Global market hours vary by commodity
5. **Data Accuracy**: Free APIs may have 15-20 minute delays
6. **Predictions**: ML models require training with historical data for accuracy

---

## 📊 Current Implementation Status

| Feature | Status | Notes |
|---------|--------|-------|
| Stock Quotes (Yahoo) | ✅ Working | 15-min delay |
| NIFTY/SENSEX | ✅ Working | Real indices |
| Crypto (CoinGecko) | ✅ Working | Real-time |
| Commodities | ✅ Working | Via Yahoo fallback |
| WebSocket Updates | ✅ Working | 30-sec refresh |
| ML Predictions | ⚠️ Demo Mode | Needs TensorFlow training |
| Redis Caching | ⚠️ Optional | In-memory fallback |

---

*Last Updated: January 18, 2026*
