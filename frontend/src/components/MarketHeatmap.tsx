import { useState, useMemo, useEffect, useCallback } from 'react'
import {
    Box,
    VStack,
    HStack,
    Text,
    useColorMode,
    SimpleGrid,
    Tooltip,
    Badge,
    Select,
    Icon,
    Skeleton,
    Alert,
    AlertIcon,
    Button,
    useToast,
} from '@chakra-ui/react'
import { FiTrendingUp, FiTrendingDown, FiRefreshCw } from 'react-icons/fi'
import { stocksApi } from '../services/api'
import { useWebSocket } from '../hooks'

// Types
interface StockCell {
    symbol: string
    name: string
    price: number
    change: number
    changePercent: number
    marketCap: number
    sector: string
}

interface SectorData {
    name: string
    change: number
    stocks: StockCell[]
}

// Sector mapping for categorizing stocks
const SECTOR_MAP: Record<string, string> = {
    'TCS': 'IT', 'INFY': 'IT', 'HCLTECH': 'IT', 'WIPRO': 'IT', 'TECHM': 'IT', 'LTI': 'IT',
    'HDFCBANK': 'Banking', 'ICICIBANK': 'Banking', 'SBIN': 'Banking', 'KOTAKBANK': 'Banking',
    'AXISBANK': 'Banking', 'INDUSINDBK': 'Banking', 'BANDHANBNK': 'Banking',
    'RELIANCE': 'Oil & Gas', 'ONGC': 'Oil & Gas', 'BPCL': 'Oil & Gas', 'IOC': 'Oil & Gas',
    'TATAMOTORS': 'Auto', 'MARUTI': 'Auto', 'M&M': 'Auto', 'BAJAJ-AUTO': 'Auto', 'HEROMOTOCO': 'Auto',
    'SUNPHARMA': 'Pharma', 'DRREDDY': 'Pharma', 'CIPLA': 'Pharma', 'DIVISLAB': 'Pharma',
    'HINDUNILVR': 'FMCG', 'ITC': 'FMCG', 'NESTLEIND': 'FMCG', 'BRITANNIA': 'FMCG', 'DABUR': 'FMCG',
    'TATASTEEL': 'Metals', 'JSWSTEEL': 'Metals', 'HINDALCO': 'Metals', 'COALINDIA': 'Metals',
    'TITAN': 'Consumer', 'ASIANPAINT': 'Consumer', 'BAJFINANCE': 'Finance', 'BAJAJFINSV': 'Finance',
    'LT': 'Infrastructure', 'ULTRACEMCO': 'Infrastructure', 'GRASIM': 'Infrastructure',
    'BHARTIARTL': 'Telecom', 'POWERGRID': 'Utilities', 'NTPC': 'Utilities',
}

// Default market cap estimates (in crores) for display sizing
const DEFAULT_MCAP: Record<string, number> = {
    'RELIANCE': 1660000, 'TCS': 1420000, 'HDFCBANK': 1260000, 'ICICIBANK': 715000,
    'INFY': 650000, 'HINDUNILVR': 577000, 'ITC': 569500, 'SBIN': 560000,
    'BHARTIARTL': 480000, 'KOTAKBANK': 355000, 'LT': 350000, 'AXISBANK': 328000,
}

// Demo/fallback data (used when API is unavailable)
const DEMO_SECTOR_STOCKS: SectorData[] = [
    {
        name: 'IT',
        change: 1.24,
        stocks: [
            { symbol: 'TCS', name: 'TCS Ltd', price: 3892.45, change: 45.30, changePercent: 1.18, marketCap: 1420000, sector: 'IT' },
            { symbol: 'INFY', name: 'Infosys', price: 1567.80, change: 23.45, changePercent: 1.52, marketCap: 650000, sector: 'IT' },
            { symbol: 'HCLTECH', name: 'HCL Tech', price: 1456.30, change: 18.90, changePercent: 1.31, marketCap: 395000, sector: 'IT' },
            { symbol: 'WIPRO', name: 'Wipro', price: 485.20, change: -3.40, changePercent: -0.70, marketCap: 265000, sector: 'IT' },
            { symbol: 'TECHM', name: 'Tech Mahindra', price: 1234.50, change: 15.60, changePercent: 1.28, marketCap: 120000, sector: 'IT' },
        ]
    },
    {
        name: 'Banking',
        change: -0.45,
        stocks: [
            { symbol: 'HDFCBANK', name: 'HDFC Bank', price: 1654.20, change: -8.30, changePercent: -0.50, marketCap: 1260000, sector: 'Banking' },
            { symbol: 'ICICIBANK', name: 'ICICI Bank', price: 1023.45, change: -5.60, changePercent: -0.54, marketCap: 715000, sector: 'Banking' },
            { symbol: 'SBIN', name: 'SBI', price: 628.90, change: 3.20, changePercent: 0.51, marketCap: 560000, sector: 'Banking' },
            { symbol: 'KOTAKBANK', name: 'Kotak Bank', price: 1789.50, change: -12.40, changePercent: -0.69, marketCap: 355000, sector: 'Banking' },
            { symbol: 'AXISBANK', name: 'Axis Bank', price: 1067.30, change: -4.80, changePercent: -0.45, marketCap: 328000, sector: 'Banking' },
        ]
    },
    {
        name: 'Oil & Gas',
        change: 2.15,
        stocks: [
            { symbol: 'RELIANCE', name: 'Reliance', price: 2456.30, change: 52.80, changePercent: 2.20, marketCap: 1660000, sector: 'Oil & Gas' },
            { symbol: 'ONGC', name: 'ONGC', price: 267.45, change: 5.30, changePercent: 2.02, marketCap: 336000, sector: 'Oil & Gas' },
            { symbol: 'BPCL', name: 'BPCL', price: 567.80, change: 8.90, changePercent: 1.59, marketCap: 123000, sector: 'Oil & Gas' },
        ]
    },
    {
        name: 'Auto',
        change: 0.82,
        stocks: [
            { symbol: 'TATAMOTORS', name: 'Tata Motors', price: 987.60, change: 12.30, changePercent: 1.26, marketCap: 329000, sector: 'Auto' },
            { symbol: 'MARUTI', name: 'Maruti Suzuki', price: 11234.50, change: 89.60, changePercent: 0.80, marketCap: 340000, sector: 'Auto' },
            { symbol: 'M&M', name: 'M&M', price: 1567.80, change: 8.40, changePercent: 0.54, marketCap: 195000, sector: 'Auto' },
        ]
    },
    {
        name: 'Pharma',
        change: -1.20,
        stocks: [
            { symbol: 'SUNPHARMA', name: 'Sun Pharma', price: 1234.80, change: -18.60, changePercent: -1.48, marketCap: 296000, sector: 'Pharma' },
            { symbol: 'DRREDDY', name: 'Dr Reddys', price: 5678.90, change: -45.30, changePercent: -0.79, marketCap: 94400, sector: 'Pharma' },
            { symbol: 'CIPLA', name: 'Cipla', price: 1456.30, change: -12.40, changePercent: -0.84, marketCap: 117600, sector: 'Pharma' },
        ]
    },
    {
        name: 'FMCG',
        change: 0.35,
        stocks: [
            { symbol: 'HINDUNILVR', name: 'HUL', price: 2456.70, change: 8.90, changePercent: 0.36, marketCap: 577000, sector: 'FMCG' },
            { symbol: 'ITC', name: 'ITC', price: 456.75, change: 1.80, changePercent: 0.40, marketCap: 569500, sector: 'FMCG' },
            { symbol: 'NESTLEIND', name: 'Nestle India', price: 24567.80, change: 78.90, changePercent: 0.32, marketCap: 237000, sector: 'FMCG' },
        ]
    },
]

// Transform API response to sector data
const transformToSectorData = (stocks: any[]): SectorData[] => {
    const sectorMap = new Map<string, StockCell[]>()

    stocks.forEach((stock: any) => {
        const sector = SECTOR_MAP[stock.symbol] || 'Other'
        const stockCell: StockCell = {
            symbol: stock.symbol,
            name: stock.name || stock.symbol,
            price: stock.current_price || stock.price || 0,
            change: stock.change || 0,
            changePercent: stock.change_percent || stock.changePercent || 0,
            marketCap: stock.market_cap || DEFAULT_MCAP[stock.symbol] || 100000,
            sector: sector
        }

        if (!sectorMap.has(sector)) {
            sectorMap.set(sector, [])
        }
        sectorMap.get(sector)!.push(stockCell)
    })

    // Convert to SectorData array
    const sectorData: SectorData[] = []
    sectorMap.forEach((stocks, name) => {
        const avgChange = stocks.reduce((sum, s) => sum + s.changePercent, 0) / stocks.length
        sectorData.push({
            name,
            change: Math.round(avgChange * 100) / 100,
            stocks: stocks.sort((a, b) => b.marketCap - a.marketCap)
        })
    })

    // Sort sectors by absolute change (most volatile first)
    return sectorData.sort((a, b) => Math.abs(b.change) - Math.abs(a.change))
}

// Get color based on change percentage
const getHeatColor = (change: number, colorMode: string): string => {
    const intensity = Math.min(Math.abs(change) / 3, 1)

    if (change > 0) {
        // Green shades
        if (colorMode === 'dark') {
            return `rgba(72, 187, 120, ${0.3 + intensity * 0.5})`
        }
        return `rgba(72, 187, 120, ${0.2 + intensity * 0.6})`
    } else if (change < 0) {
        // Red shades
        if (colorMode === 'dark') {
            return `rgba(245, 101, 101, ${0.3 + intensity * 0.5})`
        }
        return `rgba(245, 101, 101, ${0.2 + intensity * 0.6})`
    }

    return colorMode === 'dark' ? 'gray.700' : 'gray.100'
}

// Calculate cell size based on market cap
const getCellSize = (marketCap: number, maxCap: number): number => {
    const minSize = 80
    const maxSize = 150
    const ratio = marketCap / maxCap
    return minSize + (maxSize - minSize) * ratio
}

interface MarketHeatmapProps {
    onStockClick?: (symbol: string) => void
}

export default function MarketHeatmap({ onStockClick }: MarketHeatmapProps) {
    const { colorMode } = useColorMode()
    const toast = useToast()
    const [selectedSector, setSelectedSector] = useState<string>('all')
    const [sectorData, setSectorData] = useState<SectorData[]>(DEMO_SECTOR_STOCKS)
    const [isLoading, setIsLoading] = useState(true)
    const [isRefreshing, setIsRefreshing] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
    const [isLiveData, setIsLiveData] = useState(false)

    // WebSocket for real-time updates
    const { lastMessage, isConnected, subscribe, unsubscribe } = useWebSocket()

    // Extract all symbols from sector data for subscription
    const allSymbols = useMemo(() => {
        return sectorData.flatMap(sector => sector.stocks.map(stock => stock.symbol))
    }, [sectorData])

    // Subscribe to symbols when they change
    useEffect(() => {
        if (allSymbols.length > 0 && isConnected) {
            subscribe(allSymbols)
        }
        // Cleanup function to unsubscribe when component unmounts or symbols change
        return () => {
            if (allSymbols.length > 0 && isConnected) {
                unsubscribe(allSymbols)
            }
        }
    }, [allSymbols, isConnected, subscribe, unsubscribe])

    // Update sectorData when WebSocket message arrives
    useEffect(() => {
        if (lastMessage && lastMessage.type === 'price_update') {
            setSectorData(prev => prev.map(sector => {
                let sectorChangeSum = 0
                let sectorStockCount = 0
                const updatedStocks = sector.stocks.map(stock => {
                    if (stock.symbol === lastMessage.symbol) {
                        const updatedStock = {
                            ...stock,
                            price: lastMessage.price,
                            change: lastMessage.change,
                            changePercent: lastMessage.change_percent
                        }
                        sectorChangeSum += updatedStock.changePercent
                        sectorStockCount++
                        return updatedStock
                    }
                    sectorChangeSum += stock.changePercent
                    sectorStockCount++
                    return stock
                })

                const newSectorChange = sectorStockCount > 0 ? Math.round((sectorChangeSum / sectorStockCount) * 100) / 100 : sector.change

                return {
                    ...sector,
                    change: newSectorChange,
                    stocks: updatedStocks
                }
            }))
        }
    }, [lastMessage])

    // Fetch data from API
    const fetchData = useCallback(async (showRefreshToast = false) => {
        try {
            if (showRefreshToast) setIsRefreshing(true)
            else setIsLoading(true)

            const response = await stocksApi.getTopMovers(20)

            if (response.data && response.data.data) {
                const gainers = response.data.data.top_gainers || []
                const losers = response.data.data.top_losers || []
                const allStocks = [...gainers, ...losers]

                if (allStocks.length > 0) {
                    // Update current stocks with latest data and categorize
                    const transformedData = transformToSectorData(allStocks)
                    setSectorData(transformedData.length > 0 ? transformedData : DEMO_SECTOR_STOCKS)
                    setIsLiveData(transformedData.length > 0)
                    setError(null)
                } else {
                    // Use demo data if no stocks returned
                    setSectorData(DEMO_SECTOR_STOCKS)
                    setIsLiveData(false)
                }
            } else {
                setSectorData(DEMO_SECTOR_STOCKS)
                setIsLiveData(false)
            }

            setLastUpdated(new Date())

            if (showRefreshToast) {
                toast({
                    title: 'Data refreshed',
                    status: 'success',
                    duration: 2000,
                    isClosable: true,
                })
            }
        } catch (err) {
            console.error('Failed to fetch heatmap data:', err)
            setError('Using fallback data streams')
            setSectorData(DEMO_SECTOR_STOCKS)
            setIsLiveData(false)
        } finally {
            setIsLoading(false)
            setIsRefreshing(false)
        }
    }, [toast])

    // Initial load and auto-refresh
    useEffect(() => {
        fetchData()

        // Auto-refresh every 60 seconds during market hours
        const interval = setInterval(() => {
            fetchData()
        }, 60000)

        return () => clearInterval(interval)
    }, [fetchData])

    const filteredData = useMemo(() => {
        if (selectedSector === 'all') return sectorData
        return sectorData.filter((s: SectorData) => s.name === selectedSector)
    }, [selectedSector, sectorData])

    const maxMarketCap = useMemo(() => {
        return Math.max(...sectorData.flatMap((s: SectorData) => s.stocks.map((st: StockCell) => st.marketCap)))
    }, [sectorData])

    const cardBg = colorMode === 'dark' ? 'gray.800' : 'white'
    const borderColor = colorMode === 'dark' ? 'gray.700' : 'gray.200'

    if (isLoading) {
        return (
            <VStack spacing={4} align="stretch">
                <Skeleton height="40px" />
                <SimpleGrid columns={{ base: 2, md: 3, lg: 6 }} spacing={3}>
                    {[...Array(6)].map((_, i) => (
                        <Skeleton key={i} height="60px" borderRadius="lg" />
                    ))}
                </SimpleGrid>
                <Skeleton height="300px" borderRadius="lg" />
            </VStack>
        )
    }

    return (
        <VStack spacing={4} align="stretch">
            {/* Header */}
            <HStack justify="space-between" wrap="wrap" gap={2}>
                <HStack>
                    <Text fontSize="xl" fontWeight="800">Market Heatmap</Text>
                    {isLiveData ? (
                        <Badge colorScheme="green" variant="subtle" fontSize="xs">LIVE</Badge>
                    ) : (
                        <Badge colorScheme="orange" variant="subtle" fontSize="xs">DEMO</Badge>
                    )}
                </HStack>

                <HStack spacing={2}>
                    <Button
                        size="sm"
                        variant="ghost"
                        leftIcon={<Icon as={FiRefreshCw} />}
                        onClick={() => fetchData(true)}
                        isLoading={isRefreshing}
                        loadingText="Refreshing"
                    >
                        Refresh
                    </Button>
                    <Select size="sm" value={selectedSector} onChange={(e) => setSelectedSector(e.target.value)} w="140px">
                        <option value="all">All Sectors</option>
                        {sectorData.map((s: SectorData) => (
                            <option key={s.name} value={s.name}>{s.name}</option>
                        ))}
                    </Select>
                </HStack>
            </HStack>

            {/* Error Alert */}
            {error && (
                <Alert status="warning" borderRadius="lg" size="sm">
                    <AlertIcon />
                    {error}
                </Alert>
            )}

            {/* Sector Overview */}
            <SimpleGrid columns={{ base: 2, md: 3, lg: 6 }} spacing={3}>
                {sectorData.map((sector: SectorData) => (
                    <Box
                        key={sector.name}
                        p={3}
                        borderRadius="lg"
                        bg={getHeatColor(sector.change, colorMode)}
                        cursor="pointer"
                        onClick={() => setSelectedSector(sector.name === selectedSector ? 'all' : sector.name)}
                        border={selectedSector === sector.name ? '2px solid' : '1px solid'}
                        borderColor={selectedSector === sector.name ? 'blue.400' : borderColor}
                        transition="all 0.2s"
                        _hover={{ transform: 'scale(1.02)' }}
                    >
                        <Text fontWeight="600" fontSize="sm">{sector.name}</Text>
                        <HStack spacing={1}>
                            <Icon
                                as={sector.change >= 0 ? FiTrendingUp : FiTrendingDown}
                                color={sector.change >= 0 ? 'green.400' : 'red.400'}
                            />
                            <Text
                                fontWeight="700"
                                color={sector.change >= 0 ? 'green.400' : 'red.400'}
                            >
                                {sector.change >= 0 ? '+' : ''}{sector.change.toFixed(2)}%
                            </Text>
                        </HStack>
                    </Box>
                ))}
            </SimpleGrid>

            {/* Stock Heatmap Grid */}
            <Box
                bg={cardBg}
                p={4}
                borderRadius="xl"
                border="1px solid"
                borderColor={borderColor}
            >
                {filteredData.map((sector: SectorData) => (
                    <Box key={sector.name} mb={6} _last={{ mb: 0 }}>
                        <HStack mb={3}>
                            <Text fontWeight="700">{sector.name}</Text>
                            <Badge colorScheme={sector.change >= 0 ? 'green' : 'red'}>
                                {sector.change >= 0 ? '+' : ''}{sector.change.toFixed(2)}%
                            </Badge>
                        </HStack>

                        <Box display="flex" flexWrap="wrap" gap={2}>
                            {sector.stocks.map((stock: StockCell) => {
                                const size = getCellSize(stock.marketCap, maxMarketCap)

                                return (
                                    <Tooltip
                                        key={stock.symbol}
                                        label={
                                            <VStack align="start" spacing={1} p={1}>
                                                <Text fontWeight="bold">{stock.name}</Text>
                                                <Text>₹{stock.price.toLocaleString('en-IN')}</Text>
                                                <Text color={stock.changePercent >= 0 ? 'green.300' : 'red.300'}>
                                                    {stock.changePercent >= 0 ? '+' : ''}{stock.changePercent.toFixed(2)}%
                                                </Text>
                                                <Text fontSize="xs">MCap: ₹{(stock.marketCap / 1000).toFixed(0)}K Cr</Text>
                                            </VStack>
                                        }
                                        hasArrow
                                        placement="top"
                                    >
                                        <Box
                                            w={`${size}px`}
                                            h={`${size * 0.7}px`}
                                            minW="80px"
                                            minH="56px"
                                            bg={getHeatColor(stock.changePercent, colorMode)}
                                            borderRadius="md"
                                            p={2}
                                            cursor="pointer"
                                            display="flex"
                                            flexDirection="column"
                                            justifyContent="center"
                                            alignItems="center"
                                            transition="all 0.2s"
                                            _hover={{ transform: 'scale(1.05)', zIndex: 1 }}
                                            onClick={() => onStockClick?.(stock.symbol)}
                                        >
                                            <Text fontWeight="700" fontSize="sm">{stock.symbol}</Text>
                                            <Text
                                                fontSize="xs"
                                                fontWeight="600"
                                                color={stock.changePercent >= 0 ? 'green.300' : 'red.300'}
                                            >
                                                {stock.changePercent >= 0 ? '+' : ''}{stock.changePercent.toFixed(2)}%
                                            </Text>
                                        </Box>
                                    </Tooltip>
                                )
                            })}
                        </Box>
                    </Box>
                ))}
            </Box>

            {/* Legend */}
            <HStack justify="center" spacing={4}>
                <HStack>
                    <Box w={4} h={4} borderRadius="sm" bg="red.400" opacity={0.8} />
                    <Text fontSize="xs" color="gray.500">Strong Sell</Text>
                </HStack>
                <HStack>
                    <Box w={4} h={4} borderRadius="sm" bg="red.400" opacity={0.4} />
                    <Text fontSize="xs" color="gray.500">Weak</Text>
                </HStack>
                <HStack>
                    <Box w={4} h={4} borderRadius="sm" bg="gray.400" opacity={0.4} />
                    <Text fontSize="xs" color="gray.500">Neutral</Text>
                </HStack>
                <HStack>
                    <Box w={4} h={4} borderRadius="sm" bg="green.400" opacity={0.4} />
                    <Text fontSize="xs" color="gray.500">Positive</Text>
                </HStack>
                <HStack>
                    <Box w={4} h={4} borderRadius="sm" bg="green.400" opacity={0.8} />
                    <Text fontSize="xs" color="gray.500">Strong Buy</Text>
                </HStack>
            </HStack>
        </VStack>
    )
}
