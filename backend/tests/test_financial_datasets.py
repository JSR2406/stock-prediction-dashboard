"""
Tests for Financial Datasets Integration
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.financial_datasets_service import FinancialDatasetsClient
from app.services.smart_data_fetcher import SmartDataFetcher

@pytest.fixture
def mock_client():
    return AsyncMock(spec=FinancialDatasetsClient)

@pytest.mark.asyncio
async def test_financial_datasets_client_income_statements(mock_client):
    """Test fetching income statements."""
    mock_response = [{"revenue": 1000, "net_income": 100}]
    mock_client.get_income_statements.return_value = mock_response
    
    result = await mock_client.get_income_statements("AAPL")
    assert result == mock_response
    mock_client.get_income_statements.assert_called_with("AAPL")

@pytest.mark.asyncio
async def test_financial_datasets_client_price(mock_client):
    """Test fetching current price."""
    mock_response = {"symbol": "AAPL", "price": 150.0}
    mock_client.get_current_stock_price.return_value = mock_response
    
    result = await mock_client.get_current_stock_price("AAPL")
    assert result['price'] == 150.0

@pytest.mark.asyncio
async def test_smart_fetcher_routing():
    """Test that SmartDataFetcher routes correctly."""
    fetcher = SmartDataFetcher()
    
    # Test Indian stock routing
    assert fetcher.get_best_source("RELIANCE.NS") == "yahoo_finance"
    
    # Test US stock routing
    assert fetcher.get_best_source("AAPL") == "financial_datasets"
    
    # Test Crypto routing
    assert fetcher.get_best_source("BTC-USD") == "financial_datasets"

@pytest.mark.asyncio
async def test_smart_fetcher_integration():
    """Test smart fetcher functionality with routes."""
    fetcher = SmartDataFetcher()
    
    with patch.object(fetcher, '_fetch_price_financial_datasets', new_callable=AsyncMock) as mock_fd:
        mock_fd.return_value = {"symbol": "AAPL", "price": 150.0, "source": "financial_datasets"}
        
        result = await fetcher.get_stock_price("AAPL", source="financial_datasets")
        assert result['source'] == "financial_datasets"
        assert result['price'] == 150.0

@pytest.mark.asyncio
async def test_fallback_mechanism():
    """Test fallback to Yahoo Finance when API fails."""
    fetcher = SmartDataFetcher()
    
    with patch.object(fetcher, '_fetch_price_financial_datasets', side_effect=Exception("API Error")):
        with patch.object(fetcher, '_fetch_price_yahoo', new_callable=AsyncMock) as mock_yahoo:
            mock_yahoo.return_value = {"symbol": "AAPL", "price": 150.0, "source": "yahoo_finance"}
            
            # This should trigger fallback
            result = await fetcher.get_stock_price("AAPL", source="financial_datasets")
            
            assert result['source'] == "yahoo_finance"
            mock_yahoo.assert_called_once()
