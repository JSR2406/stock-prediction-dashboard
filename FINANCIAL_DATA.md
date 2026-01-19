# Financial Datasets Integration

This project now integrates with the [Financial Datasets API](https://financialdatasets.ai) to provide comprehensive US market data and institutional-grade financial analysis.

## Features

- **Fundamental Data**: Income statements, balance sheets, and cash flow statements.
- **Financial Ratios**: calculated metrics like P/E, P/S, ROE, ROA, and more.
- **SEC Filings**: Direct access to 10-K and 10-Q filings.
- **Institutional Holders**: Data on major shareholders.
- **Insider Trades**: Tracking of insider buy/sell activity.

## MCP Server

The integration is powered by a Model Context Protocol (MCP) server located in `financial-mcp/`. This server exposes standardized tools that the AI agent and backend services can use.

### Tools Available
- `get_income_statements`
- `get_balance_sheets`
- `get_cash_flow_statements`
- `get_financial_ratios`
- `get_price_history`
- `get_company_news`

## Smart Data Strategy

A `SmartDataFetcher` service (`backend/app/services/smart_data_fetcher.py`) intelligently routes data requests:

1. **Indian Stocks** (`.NS`, `.BO`): Routed to **Yahoo Finance**.
2. **US Stocks**: Routed to **Financial Datasets API** (Primary) with fallback to Yahoo Finance.
3. **Crypto**: Routed to **Financial Datasets API** (Primary).

This hybrid approach ensures the best data quality and coverage for each asset class while maintaining system robustness.

## Configuration

Ensure your `.env` file contains:
```env
FINANCIAL_DATASETS_API_KEY=your_api_key_here
```
