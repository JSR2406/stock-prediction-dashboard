/**
 * API Service - Axios instance with interceptors for API calls
 */

import axios, { AxiosError, AxiosInstance, AxiosResponse } from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

// Create axios instance
const api: AxiosInstance = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json',
    },
})

// Request interceptor
api.interceptors.request.use(
    (config) => {
        // Add request ID for tracking
        config.headers['X-Request-ID'] = crypto.randomUUID()
        return config
    },
    (error) => Promise.reject(error)
)

// Response interceptor
api.interceptors.response.use(
    (response: AxiosResponse) => response,
    (error: AxiosError) => {
        console.error('API Error:', error.response?.data || error.message)
        return Promise.reject(error)
    }
)

// API Types
export interface StockData {
    symbol: string
    name: string
    current_price: number
    previous_close: number
    change: number
    change_percent: number
    trend: 'up' | 'down'
    volume: number
    high: number
    low: number
    market_status?: string
}

export interface IndexData {
    name: string
    value: number
    change: number
    change_percent: number
    trend: 'up' | 'down'
}

export interface CryptoData {
    id: string
    symbol: string
    name: string
    current_price: number
    price_change_percentage_24h: number
    market_cap: number
    image?: string
    trend: 'up' | 'down'
}

export interface CommodityData {
    symbol: string
    name: string
    price_per_gram?: number
    price_per_10g?: number
    price_per_kg?: number
    unit: string
    currency: string
}

export interface PredictionData {
    symbol: string
    current_price: number
    predicted_price: number
    change: number
    change_percent: number
    trend: 'up' | 'down'
    confidence: 'high' | 'medium' | 'low'
    prediction_date: string
    disclaimer: string
}

// API Methods
export const stocksApi = {
    getIndices: () => api.get('/stocks/indices'),
    getNifty: () => api.get('/stocks/nifty'),
    getSensex: () => api.get('/stocks/sensex'),
    getTopMovers: (limit = 10) => api.get(`/stocks/top-movers?limit=${limit}`),
    getQuote: (symbol: string) => api.get(`/stocks/quote/${symbol}`),
    getHistorical: (symbol: string, period = '1y') =>
        api.get(`/stocks/historical/${symbol}?period=${period}`),
    getMarketOverview: () => api.get('/stocks/market-overview'),
    search: (query: string) => api.get(`/stocks/search?q=${query}`),
}

export const cryptoApi = {
    getTop: (limit = 10) => api.get(`/crypto/top?limit=${limit}`),
    getList: () => api.get('/crypto/list'),
    getDetail: (id: string) => api.get(`/crypto/${id}`),
}

export const commoditiesApi = {
    getGold: () => api.get('/commodities/gold'),
    getSilver: () => api.get('/commodities/silver'),
    getAll: () => api.get('/commodities/all'),
}

export const predictionsApi = {
    get: (symbol: string) => api.get(`/predictions/${symbol}`),
    getWeekly: (symbol: string) => api.get(`/predictions/${symbol}/weekly`),
    getBatch: (symbols: string[]) => api.post('/predictions/batch', { symbols }),
    getAccuracy: (symbol: string) => api.get(`/predictions/${symbol}/accuracy`),
    getModelsStatus: () => api.get('/predictions/models/status'),
}

export const healthApi = {
    check: () => api.get('/health'),
}

export default api
