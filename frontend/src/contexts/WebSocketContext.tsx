import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react'

// Types
export interface PriceUpdate {
    type: 'price_update'
    symbol: string
    price: number
    change: number
    change_percent: number
    high: number
    low: number
    volume: number
    timestamp: string
}

export interface WebSocketMessage {
    type: string
    [key: string]: any
}

type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'reconnecting' | 'error'

interface WebSocketContextType {
    status: ConnectionStatus
    isConnected: boolean
    prices: Record<string, PriceUpdate>
    subscribe: (symbols: string[]) => void
    unsubscribe: (symbols: string[]) => void
    lastMessage: WebSocketMessage | null
    error: string | null
    reconnect: () => void
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined)

const DEFAULT_WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/stocks'

export const WebSocketProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [status, setStatus] = useState<ConnectionStatus>('disconnected')
    const [prices, setPrices] = useState<Record<string, PriceUpdate>>({})
    const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
    const [error, setError] = useState<string | null>(null)

    const wsRef = useRef<WebSocket | null>(null)
    const reconnectCountRef = useRef(0)
    const reconnectAttempts = 5
    const reconnectInterval = 3000
    const heartbeatInterval = 30000

    const subscriptionsRef = useRef<Set<string>>(new Set())
    const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
    const heartbeatTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

    const clientIdRef = useRef(`client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`)

    const clearTimeouts = useCallback(() => {
        if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current)
        if (heartbeatTimeoutRef.current) clearTimeout(heartbeatTimeoutRef.current)
    }, [])

    const sendHeartbeat = useCallback(() => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: 'ping' }))
            heartbeatTimeoutRef.current = setTimeout(sendHeartbeat, heartbeatInterval)
        }
    }, [heartbeatInterval])

    const connect = useCallback(() => {
        if (wsRef.current) wsRef.current.close()
        clearTimeouts()
        setStatus('connecting')
        setError(null)

        try {
            const wsUrl = `${DEFAULT_WS_URL}/${clientIdRef.current}`
            wsRef.current = new WebSocket(wsUrl)

            wsRef.current.onopen = () => {
                console.log('Global WebSocket connected')
                setStatus('connected')
                reconnectCountRef.current = 0

                // Resubscribe to everything
                if (subscriptionsRef.current.size > 0) {
                    wsRef.current?.send(JSON.stringify({
                        type: 'subscribe',
                        symbols: Array.from(subscriptionsRef.current)
                    }))
                }
                sendHeartbeat()
            }

            wsRef.current.onmessage = (event) => {
                try {
                    const message: WebSocketMessage = JSON.parse(event.data)
                    setLastMessage(message)
                    if (message.type === 'price_update') {
                        setPrices(prev => ({ ...prev, [message.symbol]: message as PriceUpdate }))
                    }
                } catch (err) {
                    console.error('Failed to parse WS message', err)
                }
            }

            wsRef.current.onclose = (event) => {
                clearTimeouts()
                if (!event.wasClean && reconnectCountRef.current < reconnectAttempts) {
                    setStatus('reconnecting')
                    reconnectCountRef.current++
                    reconnectTimeoutRef.current = setTimeout(connect, reconnectInterval * reconnectCountRef.current)
                } else {
                    setStatus('disconnected')
                }
            }

            wsRef.current.onerror = () => {
                setError('WebSocket connection error')
                setStatus('error')
            }
        } catch (err) {
            console.error('WS connection failed', err)
            setStatus('error')
        }
    }, [clearTimeouts, sendHeartbeat])

    useEffect(() => {
        connect()
        return () => {
            clearTimeouts()
            if (wsRef.current) wsRef.current.close()
        }
    }, [connect, clearTimeouts])

    const subscribe = useCallback((symbols: string[]) => {
        const newSymbols = symbols.map(s => s.toUpperCase())
        newSymbols.forEach(s => subscriptionsRef.current.add(s))

        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: 'subscribe', symbols: newSymbols }))
        }
    }, [])

    const unsubscribe = useCallback((symbols: string[]) => {
        const removeSymbols = symbols.map(s => s.toUpperCase())
        removeSymbols.forEach(s => subscriptionsRef.current.delete(s))

        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: 'unsubscribe', symbols: removeSymbols }))
        }
    }, [])

    const value = {
        status,
        isConnected: status === 'connected',
        prices,
        subscribe,
        unsubscribe,
        lastMessage,
        error,
        reconnect: connect
    }

    return <WebSocketContext.Provider value={value}>{children}</WebSocketContext.Provider>
}

export const useWebSocket = () => {
    const context = useContext(WebSocketContext)
    if (context === undefined) {
        throw new Error('useWebSocket must be used within a WebSocketProvider')
    }
    return context
}
