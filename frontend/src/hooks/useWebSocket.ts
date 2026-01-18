/**
 * WebSocket Hook for Real-time Stock Price Updates
 * This is now a wrapper around the Global WebSocketContext.
 */

import { useWebSocket as useGlobalWebSocket } from '../contexts/WebSocketContext'

export type { PriceUpdate, WebSocketMessage } from '../contexts/WebSocketContext'

export function useWebSocket() {
    return useGlobalWebSocket()
}

export default useWebSocket
