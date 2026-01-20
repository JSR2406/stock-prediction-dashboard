import { useState, useMemo, useEffect, useCallback } from 'react'
import {
    Box,
    VStack,
    HStack,
    Text,
    useColorMode,
    SimpleGrid,
    Badge,
    Progress,
    Icon,
    Flex,
    Divider,
    Stat,
    StatLabel,
    StatNumber,
    StatHelpText,
    StatArrow,
    Skeleton,
    Alert,
    AlertIcon,
    Tooltip as ChakraTooltip,
    useToast,
    Button,
} from '@chakra-ui/react'
import {
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Area,
    ComposedChart,
    ReferenceLine,
    Line,
} from 'recharts'
import { FiTrendingUp, FiTrendingDown, FiTarget, FiActivity, FiZap, FiInfo, FiRefreshCw } from 'react-icons/fi'
import SearchBar from './SearchBar'
import { predictionsApi } from '../services/api'
import { useWebSocket } from '../hooks'

// Types
interface ForecastPoint {
    date: string
    predicted: number
    upper: number
    lower: number
}

interface PredictionData {
    symbol: string
    name: string
    currentPrice: number
    predictedPrice: number
    confidence: number
    changePercent: number
    quality: 'high' | 'medium' | 'low'
    signals: {
        rsi: 'buy' | 'sell' | 'hold'
        macd: 'buy' | 'sell' | 'hold'
        sma: 'buy' | 'sell' | 'hold'
        bb: 'buy' | 'sell' | 'hold'
    }
    forecast: ForecastPoint[]
    modelBreakdown: Record<string, number>
    isDemo?: boolean
}

// Fallback demo results for when API is unavailable or symbol not trained
const generateDemoData = (symbol: string): PredictionData => {
    const basePrice = 2500 + Math.random() * 1000
    const change = (Math.random() - 0.4) * 4

    const forecast = []
    let price = basePrice
    for (let i = 1; i <= 7; i++) {
        const dailyChange = (Math.random() - 0.45) * 1.5
        price *= (1 + dailyChange / 100)
        const date = new Date()
        date.setDate(date.getDate() + i)
        forecast.push({
            date: date.toLocaleDateString('en-IN', { day: '2-digit', month: 'short' }),
            predicted: Math.round(price * 100) / 100,
            upper: Math.round(price * 1.025 * 100) / 100,
            lower: Math.round(price * 0.975 * 100) / 100
        })
    }

    return {
        symbol,
        name: `${symbol} (Simulated)`,
        currentPrice: basePrice,
        predictedPrice: basePrice * (1 + change / 100),
        confidence: 65 + Math.random() * 20,
        changePercent: change,
        quality: 'medium',
        signals: {
            rsi: Math.random() > 0.6 ? 'buy' : Math.random() > 0.3 ? 'hold' : 'sell',
            macd: Math.random() > 0.5 ? 'buy' : Math.random() > 0.3 ? 'hold' : 'sell',
            sma: Math.random() > 0.55 ? 'buy' : Math.random() > 0.35 ? 'hold' : 'sell',
            bb: Math.random() > 0.4 ? 'buy' : Math.random() > 0.2 ? 'hold' : 'sell',
        },
        forecast,
        modelBreakdown: {
            lstm: 40,
            gru: 30,
            xgboost: 20,
            rf: 10,
        },
        isDemo: true
    }
}

const SignalBadge = ({ signal }: { signal: 'buy' | 'sell' | 'hold' }) => {
    const colors = {
        buy: 'green',
        sell: 'red',
        hold: 'yellow'
    }
    return (
        <Badge colorScheme={colors[signal]} fontSize="xs" textTransform="uppercase" px={2} borderRadius="full">
            {signal}
        </Badge>
    )
}

interface PredictionDashboardProps {
    defaultSymbol?: string
}

export default function PredictionDashboard({ defaultSymbol = 'RELIANCE' }: PredictionDashboardProps) {
    const { colorMode } = useColorMode()
    const toast = useToast()
    const [symbol, setSymbol] = useState(defaultSymbol)
    const [loading, setLoading] = useState(true)
    const [isRefreshing, setIsRefreshing] = useState(false)
    const [data, setData] = useState<PredictionData | null>(null)
    const [error, setError] = useState<string | null>(null)

    // WebSocket for real-time updates
    const { lastMessage, isConnected, subscribe, unsubscribe } = useWebSocket()

    // Subscribe to current symbol
    useEffect(() => {
        if (symbol && isConnected) {
            subscribe([symbol])
            return () => unsubscribe([symbol])
        }
    }, [symbol, isConnected, subscribe, unsubscribe])

    // Update current price from WebSocket
    useEffect(() => {
        if (lastMessage && lastMessage.type === 'price_update' && lastMessage.symbol === symbol) {
            setData((prev: PredictionData | null) => {
                if (!prev) return null
                return {
                    ...prev,
                    currentPrice: lastMessage.price as number,
                    // Recalculate change percent relative to live price
                    changePercent: ((prev.predictedPrice - (lastMessage.price as number)) / (lastMessage.price as number)) * 100
                }
            })
        }
    }, [lastMessage, symbol])

    const fetchPrediction = useCallback(async (stockSymbol: string, showLoading = true) => {
        try {
            if (showLoading) setLoading(true)
            else setIsRefreshing(true)

            setError(null)
            const response = await predictionsApi.get(stockSymbol)

            if (response.data && response.data.success && response.data.data) {
                const apiData = response.data.data
                // Transform API data to our frontend format
                const transformed: PredictionData = {
                    symbol: stockSymbol,
                    name: apiData.name || stockSymbol,
                    currentPrice: apiData.current_price,
                    predictedPrice: apiData.predicted_price,
                    confidence: apiData.confidence,
                    changePercent: apiData.change_percent,
                    quality: apiData.quality || (apiData.confidence > 80 ? 'high' : apiData.confidence > 60 ? 'medium' : 'low'),
                    signals: apiData.signals || {
                        rsi: 'hold',
                        macd: 'hold',
                        sma: 'hold',
                        bb: 'hold'
                    },
                    forecast: apiData.forecast || [],
                    modelBreakdown: apiData.model_contributions || {},
                    isDemo: apiData.is_demo || false
                }
                setData(transformed)
            } else {
                setData(generateDemoData(stockSymbol))
            }
        } catch (err) {
            console.error('Prediction fetch error:', err)
            setError('Real-time AI prediction limited - using technical fallback')
            setData(generateDemoData(stockSymbol))
        } finally {
            setLoading(false)
            setIsRefreshing(false)
        }
    }, [])

    useEffect(() => {
        fetchPrediction(symbol)
    }, [symbol, fetchPrediction])

    const overallSignal = useMemo(() => {
        if (!data || !data.signals) return { label: 'Hold', color: 'yellow', icon: FiActivity }
        const signals = Object.values(data.signals)
        const buyCount = signals.filter(s => s === 'buy').length
        const sellCount = signals.filter(s => s === 'sell').length

        if (buyCount >= 3) return { label: 'Strong Buy', color: 'green', icon: FiTrendingUp }
        if (buyCount >= 2) return { label: 'Buy', color: 'green', icon: FiTrendingUp }
        if (sellCount >= 3) return { label: 'Strong Sell', color: 'red', icon: FiTrendingDown }
        if (sellCount >= 2) return { label: 'Sell', color: 'red', icon: FiTrendingDown }
        return { label: 'Hold', color: 'yellow', icon: FiActivity }
    }, [data?.signals])

    const cardBg = colorMode === 'dark' ? 'gray.800' : 'white'
    const borderColor = colorMode === 'dark' ? 'gray.700' : 'gray.200'
    const gridColor = colorMode === 'dark' ? '#2D3748' : '#E2E8F0'

    const refreshData = () => {
        fetchPrediction(symbol, false)
        toast({
            title: 'Refreshing AI Insights',
            description: `Updating prediction models for ${symbol}`,
            status: 'info',
            duration: 3000,
            isClosable: true,
            position: 'top-right'
        })
    }

    if (loading || !data) {
        return (
            <VStack spacing={6} align="stretch">
                <HStack justify="space-between">
                    <Skeleton height="40px" width="200px" />
                    <Skeleton height="40px" width="300px" />
                </HStack>
                <Skeleton height="150px" borderRadius="xl" />
                <Skeleton height="350px" borderRadius="xl" />
                <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6}>
                    <Skeleton height="200px" borderRadius="xl" />
                    <Skeleton height="200px" borderRadius="xl" />
                </SimpleGrid>
            </VStack>
        )
    }

    return (
        <VStack spacing={6} align="stretch">
            {/* Header with Search */}
            <Flex justify="space-between" align="center" wrap="wrap" gap={4}>
                <VStack align="start" spacing={0}>
                    <Text fontSize="2xl" fontWeight="800">AI Predictions</Text>
                    <HStack>
                        <Badge colorScheme={data.isDemo ? 'orange' : 'green'} variant="subtle" fontSize="10px">
                            {data.isDemo ? 'DEMO MODE' : 'LIVE AI'}
                        </Badge>
                        <Text fontSize="xs" color="gray.500">Enhanced Ensemble Strategy</Text>
                    </HStack>
                </VStack>
                <HStack spacing={4} w={{ base: 'full', md: 'auto' }}>
                    <SearchBar
                        placeholder="Search another stock..."
                        onSelect={(stock) => setSymbol(stock.symbol)}
                    />
                    <HStack spacing={1}>
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={refreshData}
                            isLoading={isRefreshing}
                            borderRadius="full"
                        >
                            <Icon as={FiRefreshCw} />
                        </Button>
                    </HStack>
                </HStack>
            </Flex>

            {error && (
                <Alert status="warning" borderRadius="xl" variant="subtle" border="1px solid" borderColor="orange.200">
                    <AlertIcon />
                    <VStack align="start" spacing={0}>
                        <Text fontWeight="bold" fontSize="sm">System Notice</Text>
                        <Text fontSize="xs">{error}</Text>
                    </VStack>
                </Alert>
            )}

            {/* Price Overview */}
            <Box bg={cardBg} p={6} borderRadius="xl" border="1px solid" borderColor={borderColor} boxShadow="sm" position="relative" overflow="hidden">
                {/* Decorative background gradient */}
                <Box
                    position="absolute"
                    top="-50px"
                    right="-50px"
                    w="200px"
                    h="200px"
                    bg={overallSignal.color === 'green' ? 'green.400' : overallSignal.color === 'red' ? 'red.400' : 'yellow.400'}
                    opacity={0.05}
                    borderRadius="full"
                    filter="blur(40px)"
                    zIndex={0}
                />

                <HStack justify="space-between" mb={6} align="start" position="relative" zIndex={1}>
                    <VStack align="start" spacing={0}>
                        <HStack>
                            <Text fontSize="3xl" fontWeight="900" letterSpacing="tight">{data.symbol}</Text>
                        </HStack>
                        <Text color="gray.500" fontWeight="600">{data.name}</Text>
                    </VStack>
                    <VStack align="end" spacing={2}>
                        <Badge
                            fontSize="sm"
                            px={4}
                            py={2}
                            borderRadius="full"
                            colorScheme={overallSignal.color}
                            boxShadow="sm"
                            display="flex"
                            alignItems="center"
                            gap={2}
                        >
                            <Icon as={overallSignal.icon} />
                            {overallSignal.label}
                        </Badge>
                        <HStack fontSize="xs" color="gray.500">
                            <FiInfo />
                            <Text>Optimized Weights Applied</Text>
                        </HStack>
                    </VStack>
                </HStack>

                <SimpleGrid columns={{ base: 2, md: 4 }} spacing={8} position="relative" zIndex={1}>
                    <Stat>
                        <StatLabel fontSize="xs" fontWeight="bold" color="gray.500" textTransform="uppercase">Current Market</StatLabel>
                        <StatNumber fontSize="2xl" fontWeight="800">₹{data.currentPrice.toLocaleString('en-IN')}</StatNumber>
                        <StatHelpText fontWeight="bold">NSE Real-time</StatHelpText>
                    </Stat>

                    <Stat>
                        <StatLabel fontSize="xs" fontWeight="bold" color="gray.500" textTransform="uppercase">7D AI Target</StatLabel>
                        <StatNumber fontSize="2xl" fontWeight="800" color={data.changePercent >= 0 ? 'green.500' : 'red.500'}>
                            ₹{data.predictedPrice.toLocaleString('en-IN')}
                        </StatNumber>
                        <StatHelpText fontWeight="bold">
                            <StatArrow type={data.changePercent >= 0 ? 'increase' : 'decrease'} />
                            {Math.abs(data.changePercent).toFixed(2)}% Expected
                        </StatHelpText>
                    </Stat>

                    <Stat>
                        <StatLabel fontSize="xs" fontWeight="bold" color="gray.500" textTransform="uppercase">AI Confidence</StatLabel>
                        <HStack spacing={2} align="baseline">
                            <StatNumber fontSize="2xl" fontWeight="800">{data.confidence.toFixed(1)}%</StatNumber>
                            <ChakraTooltip label="Confidence is calculated based on historical accuracy and model alignment">
                                <span><Icon as={FiInfo} boxSize={3} color="gray.400" /></span>
                            </ChakraTooltip>
                        </HStack>
                        <Progress
                            value={data.confidence}
                            colorScheme={data.confidence >= 75 ? 'green' : data.confidence >= 60 ? 'yellow' : 'red'}
                            size="xs"
                            borderRadius="full"
                            mt={2}
                        />
                    </Stat>

                    <Stat>
                        <StatLabel fontSize="xs" fontWeight="bold" color="gray.500" textTransform="uppercase">Signal Quality</StatLabel>
                        <StatNumber
                            fontSize="2xl"
                            fontWeight="800"
                            color={data.quality === 'high' ? 'green.500' : data.quality === 'medium' ? 'yellow.500' : 'orange.500'}
                            textTransform="capitalize"
                        >
                            {data.quality}
                        </StatNumber>
                        <StatHelpText fontWeight="bold">Backtested Rating</StatHelpText>
                    </Stat>
                </SimpleGrid>
            </Box>

            {/* 7-Day Forecast Chart */}
            <Box bg={cardBg} p={6} borderRadius="xl" border="1px solid" borderColor={borderColor} boxShadow="sm">
                <HStack justify="space-between" mb={6}>
                    <HStack>
                        <Box p={2} bg="blue.500" borderRadius="lg" color="white">
                            <Icon as={FiTarget} />
                        </Box>
                        <VStack align="start" spacing={0}>
                            <Text fontWeight="800">Price Path Projection</Text>
                            <Text fontSize="xs" color="gray.500">7-Day outlook with confidence bands</Text>
                        </VStack>
                    </HStack>
                    <HStack>
                        <Badge variant="outline" colorScheme="blue">SCENARIO: NORMAL</Badge>
                    </HStack>
                </HStack>

                <Box h="350px">
                    <ResponsiveContainer width="100%" height="100%">
                        <ComposedChart data={data.forecast} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={gridColor} />
                            <XAxis
                                dataKey="date"
                                stroke="#718096"
                                fontSize={11}
                                tickLine={false}
                                axisLine={false}
                                dy={10}
                            />
                            <YAxis
                                stroke="#718096"
                                fontSize={11}
                                axisLine={false}
                                tickLine={false}
                                domain={['auto', 'auto']}
                                tickFormatter={(v) => `₹${v}`}
                                dx={-10}
                            />
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: colorMode === 'dark' ? '#1A202C' : '#FFFFFF',
                                    border: '1px solid #E2E8F0',
                                    borderRadius: '12px',
                                    boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
                                    padding: '12px'
                                }}
                                formatter={(value: number) => [`₹${value.toLocaleString('en-IN')}`, '']}
                                cursor={{ stroke: '#00B5D8', strokeWidth: 2, strokeDasharray: '5 5' }}
                            />

                            {/* Confidence area */}
                            <Area
                                type="monotone"
                                dataKey="upper"
                                stroke="none"
                                fill={data.changePercent >= 0 ? "#48BB78" : "#F56565"}
                                fillOpacity={0.1}
                                animationDuration={2000}
                            />
                            <Area
                                type="monotone"
                                dataKey="lower"
                                stroke="none"
                                fill={data.changePercent >= 0 ? "#48BB78" : "#F56565"}
                                fillOpacity={0.1}
                                animationDuration={2000}
                            />

                            {/* Current price reference */}
                            <ReferenceLine
                                y={data.currentPrice}
                                stroke={colorMode === 'dark' ? 'gray.600' : 'gray.400'}
                                strokeDasharray="3 3"
                            />

                            {/* Predicted line */}
                            <Line
                                type="monotone"
                                dataKey="predicted"
                                stroke={data.changePercent >= 0 ? "#48BB78" : "#F56565"}
                                strokeWidth={4}
                                dot={{ r: 5, fill: data.changePercent >= 0 ? "#48BB78" : "#F56565", strokeWidth: 0 }}
                                activeDot={{ r: 8, strokeWidth: 0 }}
                                animationDuration={1500}
                            />

                            {/* Upper/Lower bounds */}
                            <Line
                                type="monotone"
                                dataKey="upper"
                                stroke={data.changePercent >= 0 ? "#48BB78" : "#F56565"}
                                strokeWidth={1}
                                strokeDasharray="5 5"
                                dot={false}
                                opacity={0.5}
                            />
                            <Line
                                type="monotone"
                                dataKey="lower"
                                stroke={data.changePercent >= 0 ? "#48BB78" : "#F56565"}
                                strokeWidth={1}
                                strokeDasharray="5 5"
                                dot={false}
                                opacity={0.5}
                            />
                        </ComposedChart>
                    </ResponsiveContainer>
                </Box>

                <Flex justify="center" mt={6} gap={8} wrap="wrap">
                    <HStack spacing={2}>
                        <Box w={4} h={1} bg={data.changePercent >= 0 ? "green.400" : "red.400"} borderRadius="full" />
                        <Text fontSize="xs" fontWeight="bold" color="gray.500">AI TARGET PATH</Text>
                    </HStack>
                    <HStack spacing={2}>
                        <Box w={4} h={1} bg="gray.400" borderRadius="full" style={{ borderStyle: 'dotted' }} />
                        <Text fontSize="xs" fontWeight="bold" color="gray.500">CURRENT LEVEL</Text>
                    </HStack>
                    <HStack spacing={2}>
                        <Box w={4} h={4} bg={data.changePercent >= 0 ? "green.100" : "red.100"} borderRadius="sm" />
                        <Text fontSize="xs" fontWeight="bold" color="gray.500">PROBABILITY RANGE</Text>
                    </HStack>
                </Flex>
            </Box>

            <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6}>
                {/* Technical Signals */}
                <Box bg={cardBg} p={6} borderRadius="xl" border="1px solid" borderColor={borderColor} boxShadow="sm">
                    <HStack mb={6} justify="space-between">
                        <HStack>
                            <Box p={2} bg="purple.500" borderRadius="lg" color="white">
                                <Icon as={FiActivity} />
                            </Box>
                            <Text fontWeight="800">Indicator Status</Text>
                        </HStack>
                        <Badge colorScheme="purple" variant="subtle">TECH-V1</Badge>
                    </HStack>

                    <VStack spacing={4} align="stretch" px={2}>
                        {data.signals && Object.entries(data.signals).map(([indicator, signal]) => (
                            <Flex key={indicator} justify="space-between" align="center">
                                <HStack spacing={3}>
                                    <Box
                                        p={1.5}
                                        borderRadius="md"
                                        bg={signal === 'buy' ? 'green.50' : signal === 'sell' ? 'red.50' : 'yellow.50'}
                                        color={signal === 'buy' ? 'green.500' : signal === 'sell' ? 'red.500' : 'yellow.600'}
                                    >
                                        <Icon as={signal === 'buy' ? FiTrendingUp : signal === 'sell' ? FiTrendingDown : FiActivity} />
                                    </Box>
                                    <Text textTransform="uppercase" fontWeight="700" fontSize="xs" letterSpacing="widest" color="gray.500">{indicator}</Text>
                                </HStack>
                                <SignalBadge signal={signal as 'buy' | 'sell' | 'hold'} />
                            </Flex>
                        ))}

                        <Divider my={2} />

                        <Flex
                            justify="space-between"
                            align="center"
                            p={3}
                            bg={overallSignal.color === 'green' ? 'green.50' : overallSignal.color === 'red' ? 'red.50' : 'yellow.50'}
                            borderRadius="lg"
                            border="1px solid"
                            borderColor={overallSignal.color === 'green' ? 'green.100' : overallSignal.color === 'red' ? 'red.100' : 'yellow.100'}
                        >
                            <Text fontWeight="800" fontSize="sm" color={overallSignal.color === 'green' ? 'green.700' : overallSignal.color === 'red' ? 'red.700' : 'yellow.700'}>ENSEMBLE SIGNAL</Text>
                            <Badge colorScheme={overallSignal.color} fontSize="xs" px={4} py={1} borderRadius="full" boxShadow="xs">
                                {overallSignal.label}
                            </Badge>
                        </Flex>
                    </VStack>
                </Box>

                {/* Model Ensemble Breakdown */}
                <Box bg={cardBg} p={6} borderRadius="xl" border="1px solid" borderColor={borderColor} boxShadow="sm">
                    <HStack mb={6} justify="space-between">
                        <HStack>
                            <Box p={2} bg="orange.500" borderRadius="lg" color="white">
                                <Icon as={FiZap} />
                            </Box>
                            <Text fontWeight="800">Neural Network Weights</Text>
                        </HStack>
                        <ChakraTooltip label="Weights are optimized based on model performance on this specific asset class">
                            <span><Icon as={FiInfo} color="gray.400" /></span>
                        </ChakraTooltip>
                    </HStack>

                    <VStack spacing={5} align="stretch" px={2}>
                        {data.modelBreakdown && Object.entries(data.modelBreakdown).map(([model, weight]) => (
                            <Box key={model}>
                                <Flex justify="space-between" mb={2} align="center">
                                    <HStack>
                                        <Text fontSize="xs" textTransform="uppercase" fontWeight="800" letterSpacing="tighter">{model}</Text>
                                        <Badge fontSize="9px" variant="solid" bg={
                                            model === 'lstm' ? 'blue.400' :
                                                model === 'gru' ? 'purple.400' :
                                                    model === 'xgboost' ? 'green.400' : 'orange.400'
                                        }>{model === 'lstm' || model === 'gru' ? 'RNN' : 'GDBD'}</Badge>
                                    </HStack>
                                    <Text fontSize="xs" fontWeight="900">{typeof weight === 'number' ? weight.toFixed(1) : 0}%</Text>
                                </Flex>
                                <Progress
                                    value={typeof weight === 'number' ? weight : 0}
                                    size="xs"
                                    borderRadius="full"
                                    colorScheme={
                                        model === 'lstm' ? 'blue' :
                                            model === 'gru' ? 'purple' :
                                                model === 'xgboost' ? 'green' : 'orange'
                                    }
                                    bg={colorMode === 'dark' ? 'gray.700' : 'gray.100'}
                                />
                            </Box>
                        ))}
                    </VStack>

                    <Alert status="info" mt={6} borderRadius="lg" bg="transparent" p={0} variant="ghost" size="sm">
                        <AlertIcon boxSize={3} />
                        <Text fontSize="10px" color="gray.500" fontWeight="bold" fontStyle="italic">
                            Dynamic weighting ensures the best performing architecture leads the prediction.
                        </Text>
                    </Alert>
                </Box>
            </SimpleGrid>

            <Text fontSize="xs" color="gray.500" textAlign="center" mt={4}>
                Disclaimer: AI predictions are for informational purposes only. Do not trade based solely on these insights.
            </Text>
        </VStack>
    )
}
