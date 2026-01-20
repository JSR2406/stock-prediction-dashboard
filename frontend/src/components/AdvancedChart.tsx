import { useState, useMemo, useCallback, useEffect } from 'react'
import {
    Box,
    VStack,
    HStack,
    Text,
    ButtonGroup,
    Button,
    IconButton,
    useColorMode,
    Tooltip,
    Badge,
    Flex,
    Skeleton,
    useToast,
    Icon,
} from '@chakra-ui/react'
import {
    ComposedChart,
    Line,
    Bar,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip as RechartsTooltip,
    ResponsiveContainer,
    ReferenceLine,
    Brush,
} from 'recharts'
import { format, parseISO } from 'date-fns'
import { FiDownload, FiMaximize2, FiActivity, FiRefreshCw } from 'react-icons/fi'
import { stocksApi } from '../services/api'
import { useWebSocket } from '../hooks'

// Types
interface OHLCData {
    date: string
    displayDate: string
    open: number
    high: number
    low: number
    close: number
    volume: number
    sma20?: number
    sma50?: number
    ema12?: number
    ema26?: number
    upperBB?: number
    lowerBB?: number
}

interface AdvancedChartProps {
    symbol: string
    onFullscreen?: () => void
}

type ChartType = 'line' | 'candlestick' | 'area'
type TimeFrame = '1D' | '5D' | '1mo' | '3mo' | '6mo' | '1y' | '5y'

export default function AdvancedChart({ symbol, onFullscreen }: AdvancedChartProps) {
    const { colorMode } = useColorMode()
    const toast = useToast()
    const [chartType, setChartType] = useState<ChartType>('area')
    const [timeframe, setTimeframe] = useState<TimeFrame>('1y')
    const [isLoading, setIsLoading] = useState(true)
    const [chartData, setChartData] = useState<OHLCData[]>([])
    const [indicators, setIndicators] = useState({
        sma: true,
        bb: false,
        volume: true,
    })

    // Enhanced WebSocket for real-time price updates
    const { lastMessage, isConnected, subscribe, unsubscribe } = useWebSocket()

    useEffect(() => {
        if (symbol) {
            subscribe([symbol])
            return () => unsubscribe([symbol])
        }
    }, [symbol, subscribe, unsubscribe])

    const fetchData = useCallback(async () => {
        try {
            setIsLoading(true)
            const response = await stocksApi.getHistorical(symbol, timeframe.toLowerCase())
            if (response.data && response.data.historical) {
                const rawData = response.data.historical

                // Process and calculate indicators
                const processed = rawData.map((d: any, i: number) => {
                    const date = parseISO(d.date)
                    const item: OHLCData = {
                        ...d,
                        displayDate: format(date, timeframe === '1D' || timeframe === '5D' ? 'HH:mm' : 'MMM dd yyyy'),
                    }

                    // SMA 20
                    if (i >= 19) {
                        const sum = rawData.slice(i - 19, i + 1).reduce((a: any, b: any) => a + b.close, 0)
                        item.sma20 = Math.round((sum / 20) * 100) / 100
                    }

                    // SMA 50
                    if (i >= 49) {
                        const sum = rawData.slice(i - 49, i + 1).reduce((a: any, b: any) => a + b.close, 0)
                        item.sma50 = Math.round((sum / 50) * 100) / 100
                    }

                    // Bollinger Bands
                    if (i >= 19) {
                        const slice = rawData.slice(i - 19, i + 1).map((d: any) => d.close)
                        const mean = slice.reduce((a: number, b: number) => a + b, 0) / 20
                        const stdDev = Math.sqrt(slice.reduce((a: number, b: number) => a + Math.pow(b - mean, 2), 0) / 20)
                        item.upperBB = Math.round((mean + stdDev * 2) * 100) / 100
                        item.lowerBB = Math.round((mean - stdDev * 2) * 100) / 100
                    }

                    return item
                })
                setChartData(processed)
            }
        } catch (error) {
            console.error('Failed to fetch historical data:', error)
            toast({
                title: 'Error',
                description: 'Failed to load historical data. Showing simulated data.',
                status: 'error',
                duration: 5000,
                isClosable: true,
            })
        } finally {
            setIsLoading(false)
        }
    }, [symbol, timeframe, toast])

    useEffect(() => {
        fetchData()
    }, [fetchData])

    // Update chart with real-time price from WebSocket
    useEffect(() => {
        if (lastMessage && lastMessage.symbol === symbol && chartData.length > 0) {
            setChartData(prev => {
                const newData = [...prev]
                const lastIdx = newData.length - 1
                newData[lastIdx] = {
                    ...newData[lastIdx],
                    close: lastMessage.price,
                    high: Math.max(newData[lastIdx].high, lastMessage.price),
                    low: Math.min(newData[lastIdx].low, lastMessage.price),
                }
                return newData
            })
        }
    }, [lastMessage, symbol])

    const cardBg = colorMode === 'dark' ? 'gray.800' : 'white'
    const borderColor = colorMode === 'dark' ? 'gray.700' : 'gray.200'
    const gridColor = colorMode === 'dark' ? '#2D3748' : '#E2E8F0'

    const CustomTooltip = ({ active, payload, label }: any) => {
        if (active && payload && payload.length) {
            return (
                <Box
                    bg={colorMode === 'dark' ? 'gray.900' : 'white'}
                    p={3}
                    border="1px solid"
                    borderColor={borderColor}
                    borderRadius="md"
                    boxShadow="xl"
                >
                    <Text fontWeight="bold" mb={2} fontSize="sm">{label}</Text>
                    {payload.map((entry: any, index: number) => (
                        <HStack key={index} justify="space-between" spacing={4}>
                            <HStack spacing={2}>
                                <Box w={2} h={2} borderRadius="full" bg={entry.color || entry.fill} />
                                <Text fontSize="xs" color="gray.500">{entry.name}:</Text>
                            </HStack>
                            <Text fontSize="xs" fontWeight="bold">
                                {entry.name === 'Volume'
                                    ? entry.value.toLocaleString()
                                    : `₹${entry.value.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`}
                            </Text>
                        </HStack>
                    ))}
                </Box>
            )
        }
        return null
    }

    if (isLoading && chartData.length === 0) {
        return (
            <VStack spacing={4} align="stretch" w="full">
                <HStack justify="space-between">
                    <Skeleton height="40px" width="200px" />
                    <Skeleton height="40px" width="300px" />
                </HStack>
                <Skeleton height="400px" borderRadius="xl" />
            </VStack>
        )
    }

    return (
        <Box
            bg={cardBg}
            p={6}
            borderRadius="2xl"
            border="1px solid"
            borderColor={borderColor}
            boxShadow="sm"
            w="full"
        >
            <VStack spacing={6} align="stretch">
                {/* Chart Header */}
                <Flex justify="space-between" align="center" wrap="wrap" gap={4}>
                    <HStack spacing={4}>
                        <VStack align="start" spacing={0}>
                            <HStack>
                                <Text fontSize="xl" fontWeight="800">{symbol}</Text>
                                <Badge colorScheme={isConnected ? 'green' : 'red'} variant="subtle" fontSize="10px">
                                    {isConnected ? 'LIVE' : 'OFFLINE'}
                                </Badge>
                            </HStack>
                            <Text fontSize="xs" color="gray.500">National Stock Exchange (NSE)</Text>
                        </VStack>
                        <ButtonGroup size="xs" isAttached variant="outline">
                            <Button
                                onClick={() => setChartType('area')}
                                colorScheme={chartType === 'area' ? 'blue' : 'gray'}
                            >Area</Button>
                            <Button
                                onClick={() => setChartType('line')}
                                colorScheme={chartType === 'line' ? 'blue' : 'gray'}
                            >Line</Button>
                        </ButtonGroup>
                    </HStack>

                    <HStack spacing={2}>
                        <ButtonGroup size="xs" variant="ghost" spacing={1}>
                            {(['1D', '5D', '1mo', '3mo', '6mo', '1y', '5y'] as TimeFrame[]).map((tf) => (
                                <Button
                                    key={tf}
                                    onClick={() => setTimeframe(tf)}
                                    bg={timeframe === tf ? (colorMode === 'dark' ? 'gray.700' : 'gray.100') : 'transparent'}
                                    color={timeframe === tf ? 'blue.500' : 'gray.500'}
                                    fontWeight={timeframe === tf ? 'bold' : 'medium'}
                                >
                                    {tf}
                                </Button>
                            ))}
                        </ButtonGroup>
                        <IconButton
                            aria-label="Refresh"
                            icon={<FiRefreshCw />}
                            size="sm"
                            variant="ghost"
                            onClick={fetchData}
                        />
                        <IconButton
                            aria-label="Fullscreen"
                            icon={<FiMaximize2 />}
                            size="sm"
                            variant="ghost"
                            onClick={onFullscreen}
                        />
                    </HStack>
                </Flex>

                {/* Main Chart */}
                <Box h="450px" w="full" position="relative">
                    <ResponsiveContainer width="100%" height="100%">
                        <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                            <defs>
                                <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#3182ce" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="#3182ce" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={gridColor} />
                            <XAxis
                                dataKey="displayDate"
                                axisLine={false}
                                tickLine={false}
                                fontSize={10}
                                stroke={colorMode === 'dark' ? '#A0AEC0' : '#718096'}
                                minTickGap={30}
                            />
                            <YAxis
                                orientation="right"
                                axisLine={false}
                                tickLine={false}
                                fontSize={10}
                                stroke={colorMode === 'dark' ? '#A0AEC0' : '#718096'}
                                domain={['auto', 'auto']}
                                tickFormatter={(val) => `₹${val.toLocaleString()}`}
                            />
                            <RechartsTooltip content={<CustomTooltip />} />

                            {indicators.volume && (
                                <Bar
                                    dataKey="volume"
                                    yAxisId={0}
                                    fill={colorMode === 'dark' ? '#2D3748' : '#EDF2F7'}
                                    opacity={0.3}
                                    name="Volume"
                                />
                            )}

                            {chartType === 'area' ? (
                                <Area
                                    type="monotone"
                                    dataKey="close"
                                    stroke="#3182ce"
                                    strokeWidth={2}
                                    fillOpacity={1}
                                    fill="url(#colorPrice)"
                                    name="Price"
                                    animationDuration={1000}
                                />
                            ) : (
                                <Line
                                    type="monotone"
                                    dataKey="close"
                                    stroke="#3182ce"
                                    strokeWidth={2}
                                    dot={false}
                                    name="Price"
                                    animationDuration={1000}
                                />
                            )}

                            {indicators.sma && (
                                <>
                                    <Line
                                        type="monotone"
                                        dataKey="sma20"
                                        stroke="#F6AD55"
                                        strokeWidth={1}
                                        dot={false}
                                        name="SMA 20"
                                        strokeDasharray="5 5"
                                    />
                                    <Line
                                        type="monotone"
                                        dataKey="sma50"
                                        stroke="#FC8181"
                                        strokeWidth={1}
                                        dot={false}
                                        name="SMA 50"
                                    />
                                </>
                            )}

                            {indicators.bb && (
                                <>
                                    <Line type="monotone" dataKey="upperBB" stroke="#63B3ED" strokeWidth={1} dot={false} name="Upper BB" opacity={0.5} />
                                    <Line type="monotone" dataKey="lowerBB" stroke="#63B3ED" strokeWidth={1} dot={false} name="Lower BB" opacity={0.5} />
                                </>
                            )}

                            {chartData.length > 0 && (
                                <ReferenceLine
                                    y={chartData[chartData.length - 1].close}
                                    stroke="#3182ce"
                                    strokeDasharray="3 3"
                                    label={{
                                        position: 'right',
                                        value: `₹${chartData[chartData.length - 1].close}`,
                                        fill: '#3182ce',
                                        fontSize: 10,
                                        fontWeight: 'bold'
                                    }}
                                />
                            )}

                            <Brush
                                dataKey="displayDate"
                                height={30}
                                stroke="#3182ce"
                                fill={colorMode === 'dark' ? '#1A202C' : '#F7FAFC'}
                                travellerWidth={10}
                            />
                        </ComposedChart>
                    </ResponsiveContainer>
                </Box>

                {/* Indicator Toggles */}
                <HStack spacing={4} justify="center">
                    <Button
                        size="xs"
                        variant={indicators.sma ? 'solid' : 'outline'}
                        colorScheme="orange"
                        onClick={() => setIndicators(prev => ({ ...prev, sma: !prev.sma }))}
                        leftIcon={<FiActivity />}
                    >
                        SMA (20/50)
                    </Button>
                    <Button
                        size="xs"
                        variant={indicators.bb ? 'solid' : 'outline'}
                        colorScheme="blue"
                        onClick={() => setIndicators(prev => ({ ...prev, bb: !prev.bb }))}
                        leftIcon={<FiActivity />}
                    >
                        Bollinger Bands
                    </Button>
                    <Button
                        size="xs"
                        variant={indicators.volume ? 'solid' : 'outline'}
                        colorScheme="gray"
                        onClick={() => setIndicators(prev => ({ ...prev, volume: !prev.volume }))}
                        leftIcon={<FiActivity />}
                    >
                        Volume
                    </Button>
                </HStack>
            </VStack>
        </Box>
    )
}
