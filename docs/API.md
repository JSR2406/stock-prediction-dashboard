# API Documentation

Complete API reference for StockAI Dashboard.

## Base URL

- **Development**: `http://localhost:8000/api/v1`
- **Production**: `https://api.stockai.com/api/v1`

## Authentication

Currently, the API is open. Future versions will support:
- API Key authentication
- JWT tokens

## Response Format

All responses follow this format:

```json
{
  "success": true,
  "data": { ... },
  "message": "Optional message",
  "meta": {
    "pagination": { ... }
  }
}
```

Error responses:
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": { ... }
  }
}
```

---

## Endpoints

### Stocks

#### Get Stock Quote
```http
GET /stocks/{symbol}
```

| Parameter | Type | Description |
|-----------|------|-------------|
| symbol | string | Stock symbol (e.g., RELIANCE, TCS) |

**Response:**
```json
{
  "success": true,
  "data": {
    "symbol": "RELIANCE",
    "name": "Reliance Industries Ltd",
    "price": 2456.30,
    "change": 25.40,
    "change_percent": 1.05,
    "open": 2430.00,
    "high": 2480.00,
    "low": 2420.00,
    "volume": 5000000,
    "market_cap": 1660000000000,
    "last_updated": "2026-01-17T10:30:00Z"
  }
}
```

#### Get Historical Data
```http
GET /stocks/{symbol}/historical?period=1M
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| symbol | string | - | Stock symbol |
| period | string | 1M | Period: 1D, 5D, 1M, 3M, 6M, 1Y, 5Y |

---

### Predictions

#### Get Prediction
```http
POST /predictions
```

**Request Body:**
```json
{
  "symbol": "RELIANCE",
  "horizon": "7d"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| symbol | string | Yes | Stock symbol |
| horizon | string | No | 1d, 3d, 7d, 14d (default: 7d) |

**Response:**
```json
{
  "success": true,
  "data": {
    "symbol": "RELIANCE",
    "current_price": 2456.30,
    "predicted_prices": [
      { "date": "2026-01-18", "price": 2470.50, "confidence": 0.85 },
      { "date": "2026-01-19", "price": 2485.20, "confidence": 0.80 }
    ],
    "overall_trend": "bullish",
    "confidence_score": 0.82,
    "model_version": "ensemble-v1.0"
  }
}
```

---

### Technical Analysis

#### Get Technical Indicators
```http
GET /analysis/{symbol}/technical
```

**Response:**
```json
{
  "success": true,
  "data": {
    "symbol": "RELIANCE",
    "indicators": {
      "rsi": { "value": 58.5, "signal": "neutral" },
      "macd": { "value": 12.34, "signal": "bullish", "histogram": 2.1 },
      "sma_20": 2420.50,
      "sma_50": 2380.00,
      "bollinger": {
        "upper": 2520.00,
        "middle": 2450.00,
        "lower": 2380.00
      }
    }
  }
}
```

#### Get Trading Signals
```http
GET /analysis/{symbol}/signals
```

**Response:**
```json
{
  "success": true,
  "data": {
    "symbol": "RELIANCE",
    "overall_signal": "buy",
    "strength": 0.75,
    "signals": {
      "rsi": "hold",
      "macd": "buy",
      "sma": "buy",
      "bollinger": "buy"
    }
  }
}
```

---

### Crypto

#### Get Crypto List
```http
GET /crypto
```

#### Get Crypto Details
```http
GET /crypto/{coin_id}
```

---

### Commodities

#### Get Commodities List
```http
GET /commodities
```

#### Get Commodity Details
```http
GET /commodities/{commodity_id}
```

---

### History & Accuracy

#### Get Prediction History
```http
GET /history/{symbol}/predictions?days=30
```

#### Get Prediction Accuracy
```http
GET /history/{symbol}/accuracy?days=30
```

#### Get Top Performers
```http
GET /history/top-performers?limit=10
```

---

### WebSocket

#### Real-time Prices
```
ws://localhost:8000/ws/stocks
```

**Subscribe:**
```json
{
  "action": "subscribe",
  "symbols": ["RELIANCE", "TCS"]
}
```

**Price Update (received):**
```json
{
  "type": "price_update",
  "symbol": "RELIANCE",
  "price": 2456.50,
  "change": 0.08,
  "timestamp": "2026-01-17T10:30:15Z"
}
```

---

## Rate Limits

| Endpoint Type | Limit |
|---------------|-------|
| Standard | 100/minute |
| Predictions | 20/minute |
| WebSocket | 50 messages/minute |

---

## Error Codes

| Code | Description |
|------|-------------|
| VALIDATION_ERROR | Invalid request parameters |
| NOT_FOUND | Resource not found |
| RATE_LIMIT_EXCEEDED | Too many requests |
| INTERNAL_ERROR | Server error |
| EXTERNAL_SERVICE_ERROR | Third-party API failure |

---

## SDKs

Coming soon:
- Python SDK
- JavaScript/TypeScript SDK
- React hooks library
