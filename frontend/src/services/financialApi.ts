/**
 * Financial API Service
 * 
 * Client for accessing Financial Datasets endpoints from the backend.
 * Provides fundamentals, prices, news, filings, and ratios.
 */

import api from './api'

// Types
export interface IncomeStatement {
    ticker: string
    period: string
    calendar_date: string
    report_period: string
    revenue: number
    cost_of_good_sold: number
    gross_profit: number
    operating_expenses: number
    operating_income: number
    interest_expense: number
    income_before_tax: number
    income_tax_expense: number
    net_income: number
    eps_basic: number
    eps_diluted: number
    weighted_average_shares_outstanding_basic: number
    weighted_average_shares_outstanding_diluted: number
    [key: string]: any
}

export interface BalanceSheet {
    ticker: string
    period: string
    calendar_date: string
    report_period: string
    total_assets: number
    total_current_assets: number
    cash_and_equivalents: number
    inventory: number
    total_liabilities: number
    total_current_liabilities: number
    total_debt: number
    stockholders_equity: number
    [key: string]: any
}

export interface CashFlowStatement {
    ticker: string
    period: string
    calendar_date: string
    report_period: string
    net_cash_flow_from_operations: number
    net_cash_flow_from_investing: number
    net_cash_flow_from_financing: number
    net_change_in_cash: number
    free_cash_flow: number
    [key: string]: any
}

export interface PriceSnapshot {
    ticker: string
    price: number
    open: number
    high: number
    low: number
    close: number
    volume: number
    change: number
    change_percent: number
    timestamp: string
}

export interface SECFiling {
    ticker: string
    accession_number: string
    form_type: string
    filing_date: string
    report_date: string
    acceptance_datetime: string
    act: string
    file_number: string
    film_number: string
    items: string
    size: number
    is_xbrl: boolean
    is_inline_xbrl: boolean
    primary_document: string
    primary_doc_description: string
    filing_url: string
}

export interface FinancialRatios {
    ticker: string
    calculated_at: string
    current_price: number
    ratios: {
        pe_ratio?: number
        pb_ratio?: number
        debt_to_equity?: number
        current_ratio?: number
        quick_ratio?: number
        roe?: number
        roa?: number
        profit_margin?: number
        operating_margin?: number
        [key: string]: number | undefined
    }
}

// Service definition
export const financialApi = {
    // Fundamentals
    getIncomeStatements: (ticker: string, period = 'annual', limit = 4) =>
        api.get(`/financial/${ticker}/income-statement?period=${period}&limit=${limit}`),

    getBalanceSheets: (ticker: string, period = 'annual', limit = 4) =>
        api.get(`/financial/${ticker}/balance-sheet?period=${period}&limit=${limit}`),

    getCashFlows: (ticker: string, period = 'annual', limit = 4) =>
        api.get(`/financial/${ticker}/cash-flow?period=${period}&limit=${limit}`),

    getFundamentals: (ticker: string, period = 'annual', limit = 4) =>
        api.get(`/financial/${ticker}/fundamentals?period=${period}&limit=${limit}`),

    // Prices
    getSnapshot: (ticker: string) =>
        api.get(`/financial/${ticker}/price`),

    getHistory: (ticker: string, startDate: string, endDate: string, interval = 'day') =>
        api.get(`/financial/${ticker}/history?start_date=${startDate}&end_date=${endDate}&interval=${interval}`),

    // Crypto
    getCryptoTickers: () =>
        api.get('/financial/crypto/tickers'),

    getCryptoPrice: (ticker: string) =>
        api.get(`/financial/crypto/${ticker}/price`),

    getCryptoHistory: (ticker: string, startDate: string, endDate: string, interval = 'day') =>
        api.get(`/financial/crypto/${ticker}/history?start_date=${startDate}&end_date=${endDate}&interval=${interval}`),

    // Other
    getNews: (ticker: string) =>
        api.get(`/financial/${ticker}/news`),

    getFilings: (ticker: string, type?: string, limit = 10) => {
        let url = `/financial/${ticker}/filings?limit=${limit}`;
        if (type) url += `&filing_type=${type}`;
        return api.get(url);
    },

    getRatios: (ticker: string) =>
        api.get(`/financial/${ticker}/ratios`)
}

export default financialApi
