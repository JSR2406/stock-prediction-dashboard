import { useState, useEffect, useCallback, useRef } from 'react'
import { stocksApi, predictionsApi } from '../services/api'

/**
 * Hook to fetch and cache stock data
 */
export function useStockData(symbol: string) {
    const [data, setData] = useState<any>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    const fetchData = useCallback(async () => {
        if (!symbol) return

        setLoading(true)
        setError(null)

        try {
            const response = await stocksApi.getQuote(symbol)
            setData(response.data)
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to fetch stock data')
            // Return demo data on error
            setData({
                symbol,
                price: 2500 + Math.random() * 500,
                change: (Math.random() - 0.5) * 50,
                change_percent: (Math.random() - 0.5) * 3,
                high: 2600,
                low: 2400,
                open: 2450,
                volume: 1000000
            })
        } finally {
            setLoading(false)
        }
    }, [symbol])

    useEffect(() => {
        fetchData()
    }, [fetchData])

    return { data, loading, error, refetch: fetchData }
}

/**
 * Hook to fetch predictions with caching
 */
export function usePrediction(symbol: string) {
    const [prediction, setPrediction] = useState<any>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        if (!symbol) return

        const fetchPrediction = async () => {
            setLoading(true)
            setError(null)

            try {
                const response = await predictionsApi.get(symbol)
                setPrediction(response.data)
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to fetch prediction')
                // Return demo prediction
                const currentPrice = 2500
                const predictedChange = (Math.random() - 0.4) * 5
                setPrediction({
                    symbol,
                    current_price: currentPrice,
                    predicted_price: currentPrice * (1 + predictedChange / 100),
                    change_percent: predictedChange,
                    confidence: 70 + Math.random() * 20,
                    horizon: '7d',
                    model: 'ensemble'
                })
            } finally {
                setLoading(false)
            }
        }

        fetchPrediction()
    }, [symbol])

    return { prediction, loading, error }
}

/**
 * Hook for real-time market status
 */
export function useMarketStatus() {
    const [status, setStatus] = useState<{
        isOpen: boolean
        status: string
        message: string
        nextOpen?: string
    }>({
        isOpen: false,
        status: 'closed',
        message: 'Market closed'
    })

    useEffect(() => {
        const checkMarketStatus = () => {
            const now = new Date()
            const hours = now.getHours()
            const minutes = now.getMinutes()
            const day = now.getDay()

            // Weekend check
            if (day === 0 || day === 6) {
                setStatus({
                    isOpen: false,
                    status: 'closed',
                    message: 'Market closed for weekend',
                    nextOpen: getNextMonday()
                })
                return
            }

            // Time check (9:15 AM - 3:30 PM IST)
            const currentTime = hours * 60 + minutes
            const openTime = 9 * 60 + 15
            const closeTime = 15 * 60 + 30

            if (currentTime >= openTime && currentTime <= closeTime) {
                setStatus({
                    isOpen: true,
                    status: 'open',
                    message: 'Market is open'
                })
            } else if (currentTime < openTime && currentTime >= 9 * 60) {
                setStatus({
                    isOpen: false,
                    status: 'pre_market',
                    message: 'Pre-market session'
                })
            } else if (currentTime > closeTime && currentTime <= 16 * 60) {
                setStatus({
                    isOpen: false,
                    status: 'post_market',
                    message: 'Post-market session'
                })
            } else {
                setStatus({
                    isOpen: false,
                    status: 'closed',
                    message: 'Market closed',
                    nextOpen: getTomorrowAt915()
                })
            }
        }

        checkMarketStatus()
        const interval = setInterval(checkMarketStatus, 60000) // Check every minute

        return () => clearInterval(interval)
    }, [])

    return status
}

function getNextMonday(): string {
    const now = new Date()
    const daysUntilMonday = (8 - now.getDay()) % 7 || 7
    now.setDate(now.getDate() + daysUntilMonday)
    now.setHours(9, 15, 0, 0)
    return now.toISOString()
}

function getTomorrowAt915(): string {
    const now = new Date()
    now.setDate(now.getDate() + 1)
    now.setHours(9, 15, 0, 0)
    return now.toISOString()
}

/**
 * Hook for localStorage persistence
 */
export function useLocalStorage<T>(key: string, defaultValue: T): [T, (value: T | ((prev: T) => T)) => void] {
    const [value, setValue] = useState<T>(() => {
        try {
            const saved = localStorage.getItem(key)
            return saved ? JSON.parse(saved) : defaultValue
        } catch {
            return defaultValue
        }
    })

    useEffect(() => {
        try {
            localStorage.setItem(key, JSON.stringify(value))
        } catch (e) {
            console.error('Failed to save to localStorage:', e)
        }
    }, [key, value])

    return [value, setValue]
}

/**
 * Hook for WebSocket connection
 */
export function useWebSocket(url: string) {
    const [isConnected, setIsConnected] = useState(false)
    const [lastMessage, setLastMessage] = useState<any>(null)
    const [error, setError] = useState<string | null>(null)
    const wsRef = useRef<WebSocket | null>(null)
    const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout>>()
    const reconnectAttemptsRef = useRef(0)
    const MAX_RECONNECT_ATTEMPTS = 5

    const connect = useCallback(() => {
        if (wsRef.current?.readyState === WebSocket.OPEN) return

        try {
            wsRef.current = new WebSocket(url)

            wsRef.current.onopen = () => {
                setIsConnected(true)
                setError(null)
                reconnectAttemptsRef.current = 0
                console.log('WebSocket connected')
            }

            wsRef.current.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data)
                    setLastMessage(data)
                } catch {
                    setLastMessage(event.data)
                }
            }

            wsRef.current.onerror = () => {
                setError('WebSocket connection error')
            }

            wsRef.current.onclose = () => {
                setIsConnected(false)

                // Attempt to reconnect with exponential backoff
                if (reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
                    const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000)
                    reconnectAttemptsRef.current++

                    reconnectTimeoutRef.current = setTimeout(() => {
                        console.log(`Reconnecting... attempt ${reconnectAttemptsRef.current}`)
                        connect()
                    }, delay)
                }
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to connect')
        }
    }, [url])

    const disconnect = useCallback(() => {
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current)
        }
        if (wsRef.current) {
            wsRef.current.close()
            wsRef.current = null
        }
        setIsConnected(false)
    }, [])

    const send = useCallback((data: any) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(typeof data === 'string' ? data : JSON.stringify(data))
        }
    }, [])

    useEffect(() => {
        connect()
        return () => disconnect()
    }, [connect, disconnect])

    return { isConnected, lastMessage, error, send, connect, disconnect }
}

/**
 * Hook for real-time price updates (polling fallback)
 */
export function useRealtimePrices(symbols: string[], intervalMs: number = 30000) {
    const [prices, setPrices] = useState<Record<string, {
        price: number
        change: number
        changePercent: number
        lastUpdated: Date
    }>>({})
    const [loading, setLoading] = useState(false)

    const fetchPrices = useCallback(async () => {
        if (symbols.length === 0) return

        setLoading(true)

        try {
            // In production, this would batch fetch from API
            const newPrices: Record<string, any> = {}

            for (const symbol of symbols) {
                // Demo data - in production would fetch from API
                const basePrice = 2000 + Math.random() * 2000
                const change = (Math.random() - 0.5) * 50

                newPrices[symbol] = {
                    price: basePrice,
                    change,
                    changePercent: (change / basePrice) * 100,
                    lastUpdated: new Date()
                }
            }

            setPrices(newPrices)
        } catch (error) {
            console.error('Failed to fetch prices:', error)
        } finally {
            setLoading(false)
        }
    }, [symbols])

    useEffect(() => {
        fetchPrices()
        const interval = setInterval(fetchPrices, intervalMs)
        return () => clearInterval(interval)
    }, [fetchPrices, intervalMs])

    return { prices, loading, refetch: fetchPrices }
}
