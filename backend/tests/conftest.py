"""
Pytest configuration and fixtures.
"""

import pytest
import asyncio
from typing import Generator
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    """Create test client."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def sample_stock_symbols():
    """Sample stock symbols for testing."""
    return ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"]


@pytest.fixture
def sample_prediction_request():
    """Sample prediction request payload."""
    return {
        "symbol": "RELIANCE",
        "horizon": "7d"
    }


@pytest.fixture
def mock_stock_data():
    """Mock stock data for testing."""
    return {
        "symbol": "RELIANCE",
        "name": "Reliance Industries Ltd",
        "price": 2456.30,
        "change": 25.40,
        "change_percent": 1.05,
        "open": 2430.00,
        "high": 2480.00,
        "low": 2420.00,
        "volume": 5000000,
        "market_cap": 1660000000000
    }
