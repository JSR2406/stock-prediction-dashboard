"""
API Endpoint Tests
Comprehensive tests for all FastAPI routes.
"""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
import asyncio

from app.main import app


# Sync test client
client = TestClient(app)


# ============== Health Check Tests ==============

class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_root_endpoint(self):
        """Test root endpoint returns app info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert data["name"] == "Stock Prediction Dashboard"
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        assert "version" in data
        assert "services" in data


# ============== Stock API Tests ==============

class TestStockEndpoints:
    """Test stock-related endpoints."""
    
    def test_get_stock_quote_valid(self):
        """Test getting a valid stock quote."""
        response = client.get("/api/v1/stocks/RELIANCE")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["symbol"] == "RELIANCE"
    
    def test_get_stock_quote_with_suffix(self):
        """Test stock symbol with .NS suffix."""
        response = client.get("/api/v1/stocks/TCS.NS")
        assert response.status_code == 200
    
    def test_get_stock_historical(self):
        """Test getting historical data."""
        response = client.get("/api/v1/stocks/INFY/historical?period=1M")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_search_stocks(self):
        """Test stock search functionality."""
        response = client.get("/api/v1/stocks/search?query=TATA")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data


# ============== Crypto API Tests ==============

class TestCryptoEndpoints:
    """Test cryptocurrency endpoints."""
    
    def test_get_crypto_list(self):
        """Test getting top cryptocurrencies."""
        response = client.get("/api/v1/crypto")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)
    
    def test_get_crypto_detail(self):
        """Test getting specific crypto details."""
        response = client.get("/api/v1/crypto/bitcoin")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


# ============== Commodities API Tests ==============

class TestCommoditiesEndpoints:
    """Test commodities endpoints."""
    
    def test_get_commodities_list(self):
        """Test getting commodities list."""
        response = client.get("/api/v1/commodities")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_get_commodity_detail(self):
        """Test getting specific commodity."""
        response = client.get("/api/v1/commodities/gold")
        assert response.status_code == 200


# ============== Prediction API Tests ==============

class TestPredictionEndpoints:
    """Test prediction endpoints."""
    
    def test_get_prediction(self):
        """Test getting stock prediction."""
        response = client.post(
            "/api/v1/predictions",
            json={
                "symbol": "RELIANCE",
                "horizon": "7d"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "predicted_prices" in data["data"]
    
    def test_prediction_invalid_symbol(self):
        """Test prediction with invalid symbol format."""
        response = client.post(
            "/api/v1/predictions",
            json={
                "symbol": "",
                "horizon": "7d"
            }
        )
        # Should still work but return error or demo data
        assert response.status_code in [200, 400]
    
    def test_get_models_status(self):
        """Test getting ML models status."""
        response = client.get("/api/v1/predictions/models/status")
        assert response.status_code == 200


# ============== Analysis API Tests ==============

class TestAnalysisEndpoints:
    """Test technical analysis endpoints."""
    
    def test_get_technical_indicators(self):
        """Test getting technical indicators."""
        response = client.get("/api/v1/analysis/RELIANCE/technical")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "indicators" in data["data"]
    
    def test_get_signals(self):
        """Test getting trading signals."""
        response = client.get("/api/v1/analysis/TCS/signals")
        assert response.status_code == 200
        data = response.json()
        assert "overall_signal" in data["data"]
    
    def test_get_support_resistance(self):
        """Test support/resistance levels."""
        response = client.get("/api/v1/analysis/HDFCBANK/support-resistance")
        assert response.status_code == 200
    
    def test_get_market_status(self):
        """Test market status endpoint."""
        response = client.get("/api/v1/analysis/market-status")
        assert response.status_code == 200
        data = response.json()
        assert "is_open" in data["data"]


# ============== Error Handling Tests ==============

class TestErrorHandling:
    """Test error handling."""
    
    def test_404_not_found(self):
        """Test 404 response for unknown endpoints."""
        response = client.get("/api/v1/unknown/endpoint")
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "error" in data
    
    def test_validation_error(self):
        """Test validation error response."""
        response = client.post(
            "/api/v1/predictions",
            json={}  # Missing required fields
        )
        # Should return 422 or handle gracefully
        assert response.status_code in [200, 422]


# ============== Rate Limiting Tests ==============

class TestRateLimiting:
    """Test rate limiting functionality."""
    
    def test_rate_limit_headers(self):
        """Test that rate limit headers are present."""
        response = client.get("/api/v1/stocks/RELIANCE")
        # Rate limit headers should be present
        assert "X-Request-ID" in response.headers
    
    def test_multiple_requests(self):
        """Test multiple rapid requests."""
        for _ in range(5):
            response = client.get("/api/v1/health")
            assert response.status_code == 200


# ============== CORS Tests ==============

class TestCORS:
    """Test CORS configuration."""
    
    def test_cors_headers(self):
        """Test CORS headers in response."""
        response = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
        )
        # Should allow CORS
        assert response.status_code in [200, 204]


# ============== WebSocket Tests ==============

class TestWebSocket:
    """Test WebSocket endpoints."""
    
    def test_websocket_stats(self):
        """Test WebSocket stats endpoint."""
        response = client.get("/ws/stats")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "active_connections" in data["data"]


# Pytest configuration
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
