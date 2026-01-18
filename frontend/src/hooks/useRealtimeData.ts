import { useState, useEffect, useCallback, useRef } from 'react'

interface UseRealtimeDataOptions<T> {
    fetchFn: () => Promise<T>
    intervalMs?: number
    enabled?: boolean
}

interface UseRealtimeDataResult<T> {
    data: T | null
    loading: boolean
    error: Error | null
    lastUpdated: Date | null
    isConnected: boolean
    isPaused: boolean
    pause: () => void
    resume: () => void
    refresh: () => Promise<void>
}

export function useRealtimeData<T>({
    fetchFn,
    intervalMs = 120000, // 2 minutes default
    enabled = true,
}: UseRealtimeDataOptions<T>): UseRealtimeDataResult<T> {
    const [data, setData] = useState<T | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<Error | null>(null)
    const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
    const [isConnected, setIsConnected] = useState(true)
    const [isPaused, setIsPaused] = useState(false)

    const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
    const mountedRef = useRef(true)

    const fetchData = useCallback(async () => {
        if (!mountedRef.current || isPaused) return

        try {
            setLoading(true)
            const result = await fetchFn()

            if (mountedRef.current) {
                setData(result)
                setError(null)
                setLastUpdated(new Date())
                setIsConnected(true)
            }
        } catch (err) {
            if (mountedRef.current) {
                setError(err instanceof Error ? err : new Error('Unknown error'))
                setIsConnected(false)
            }
        } finally {
            if (mountedRef.current) {
                setLoading(false)
            }
        }
    }, [fetchFn, isPaused])

    const refresh = useCallback(async () => {
        await fetchData()
    }, [fetchData])

    const pause = useCallback(() => {
        setIsPaused(true)
        if (intervalRef.current) {
            clearInterval(intervalRef.current)
            intervalRef.current = null
        }
    }, [])

    const resume = useCallback(() => {
        setIsPaused(false)
    }, [])

    // Initial fetch and interval setup
    useEffect(() => {
        if (!enabled || isPaused) return

        // Initial fetch
        fetchData()

        // Set up interval
        intervalRef.current = setInterval(fetchData, intervalMs)

        return () => {
            if (intervalRef.current) {
                clearInterval(intervalRef.current)
            }
        }
    }, [fetchData, intervalMs, enabled, isPaused])

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            mountedRef.current = false
        }
    }, [])

    return {
        data,
        loading,
        error,
        lastUpdated,
        isConnected,
        isPaused,
        pause,
        resume,
        refresh,
    }
}

// Hook for multiple data sources
interface UseMultipleRealtimeDataOptions {
    sources: {
        key: string
        fetchFn: () => Promise<any>
    }[]
    intervalMs?: number
    enabled?: boolean
}

export function useMultipleRealtimeData({
    sources,
    intervalMs = 120000,
    enabled = true,
}: UseMultipleRealtimeDataOptions) {
    const [data, setData] = useState<Record<string, any>>({})
    const [loading, setLoading] = useState(true)
    const [errors, setErrors] = useState<Record<string, Error>>({})
    const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

    const fetchAllData = useCallback(async () => {
        setLoading(true)
        const results: Record<string, any> = {}
        const newErrors: Record<string, Error> = {}

        await Promise.allSettled(
            sources.map(async ({ key, fetchFn }) => {
                try {
                    results[key] = await fetchFn()
                } catch (err) {
                    newErrors[key] = err instanceof Error ? err : new Error('Unknown error')
                }
            })
        )

        setData(results)
        setErrors(newErrors)
        setLastUpdated(new Date())
        setLoading(false)
    }, [sources])

    useEffect(() => {
        if (!enabled) return

        fetchAllData()
        const interval = setInterval(fetchAllData, intervalMs)

        return () => clearInterval(interval)
    }, [fetchAllData, intervalMs, enabled])

    return {
        data,
        loading,
        errors,
        lastUpdated,
        refresh: fetchAllData,
    }
}

export default useRealtimeData
