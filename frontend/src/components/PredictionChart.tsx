import { useState, useEffect } from 'react'
import {
    Box,
    Text,
    VStack,
    HStack,
    Select,
    useColorMode,
    Badge,
    Skeleton,
} from '@chakra-ui/react'
import {
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    ReferenceLine,
    Area,
    ComposedChart,
} from 'recharts'
import { format, subDays } from 'date-fns'

interface PredictionChartProps {
    symbol: string
}

// Generate demo data
const generateDemoData = (symbol: string) => {
    const data = []
    const basePrice = symbol === 'RELIANCE' ? 2450 : 3500
    let currentPrice = basePrice

    for (let i = 180; i >= 0; i--) {
        const date = subDays(new Date(), i)
        const change = (Math.random() - 0.48) * 50
        currentPrice = Math.max(basePrice * 0.8, Math.min(basePrice * 1.3, currentPrice + change))

        data.push({
            date: format(date, 'MMM dd'),
            fullDate: format(date, 'yyyy-MM-dd'),
            price: currentPrice,
            sma20: currentPrice * (0.98 + Math.random() * 0.04),
            sma50: currentPrice * (0.96 + Math.random() * 0.08),
            predicted: i === 0 ? currentPrice * 1.015 : null,
        })
    }

    // Add predictions
    for (let i = 1; i <= 7; i++) {
        const date = subDays(new Date(), -i)
        currentPrice = currentPrice * (1 + (Math.random() - 0.4) * 0.015)

        data.push({
            date: format(date, 'MMM dd'),
            fullDate: format(date, 'yyyy-MM-dd'),
            price: null,
            sma20: null,
            sma50: null,
            predicted: currentPrice,
            upperBound: currentPrice * 1.03,
            lowerBound: currentPrice * 0.97,
        })
    }

    return data
}

export default function PredictionChart({ symbol }: PredictionChartProps) {
    const { colorMode } = useColorMode()
    const [loading, setLoading] = useState(true)
    const [selectedSymbol, setSelectedSymbol] = useState(symbol)
    const [chartData, setChartData] = useState<any[]>([])

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true)
            try {
                await new Promise((resolve) => setTimeout(resolve, 500))
                setChartData(generateDemoData(selectedSymbol))
            } catch (error) {
                console.error('Failed to fetch chart data:', error)
                setChartData(generateDemoData(selectedSymbol))
            } finally {
                setLoading(false)
            }
        }

        fetchData()
    }, [selectedSymbol])

    const gridColor = colorMode === 'dark' ? '#2D3748' : '#E2E8F0'
    const textColor = colorMode === 'dark' ? '#A0AEC0' : '#718096'

    const lastPrice = chartData.find((d: any) => d.price)?.price || 0
    const lastPredicted = chartData.filter((d: any) => d.predicted).slice(-1)[0]?.predicted || 0
    const changePercent = lastPrice ? ((lastPredicted - lastPrice) / lastPrice) * 100 : 0

    const CustomTooltip = ({ active, payload, label }: any) => {
        if (active && payload && payload.length) {
            const data = payload[0].payload
            return (
                <Box
                    bg={colorMode === 'dark' ? 'gray.700' : 'white'}
                    p={3}
                    borderRadius="md"
                    boxShadow="lg"
                    border="1px solid"
                    borderColor={colorMode === 'dark' ? 'gray.600' : 'gray.200'}
                >
                    <Text fontWeight="600" mb={2}>{label}</Text>
                    {data.price && <Text fontSize="sm" color="cyan.400">Price: ₹{data.price.toFixed(2)}</Text>}
                    {data.predicted && <Text fontSize="sm" color="purple.400">Predicted: ₹{data.predicted.toFixed(2)}</Text>}
                    {data.sma20 && <Text fontSize="sm" color="orange.400">SMA 20: ₹{data.sma20.toFixed(2)}</Text>}
                </Box>
            )
        }
        return null
    }

    const stocks = ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK']

    return (
        <VStack spacing={4} align="stretch">
            <HStack justify="space-between">
                <HStack>
                    <Select
                        value={selectedSymbol}
                        onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setSelectedSymbol(e.target.value)}
                        size="sm"
                        w="150px"
                        borderRadius="lg"
                    >
                        {stocks.map((s) => (
                            <option key={s} value={s}>{s}</option>
                        ))}
                    </Select>
                    <Badge colorScheme="purple" px={2} py={1} borderRadius="md">
                        6M + 7D Forecast
                    </Badge>
                </HStack>

                <HStack>
                    <Text fontSize="sm" color="gray.500">Expected Change:</Text>
                    <Badge colorScheme={changePercent >= 0 ? 'green' : 'red'} fontSize="sm" px={2} py={1} borderRadius="md">
                        {changePercent >= 0 ? '+' : ''}{changePercent.toFixed(2)}%
                    </Badge>
                </HStack>
            </HStack>

            {loading ? (
                <Skeleton height="350px" borderRadius="lg" />
            ) : (
                <Box h="350px">
                    <ResponsiveContainer width="100%" height="100%">
                        <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                            <XAxis dataKey="date" stroke={textColor} fontSize={11} tickLine={false} interval="preserveStartEnd" />
                            <YAxis stroke={textColor} fontSize={11} tickLine={false} domain={['auto', 'auto']} tickFormatter={(value: number) => `₹${value.toFixed(0)}`} />
                            <Tooltip content={<CustomTooltip />} />

                            <Area type="monotone" dataKey="upperBound" stroke="none" fill="rgba(159, 122, 234, 0.2)" />
                            <Area type="monotone" dataKey="lowerBound" stroke="none" fill="rgba(159, 122, 234, 0.2)" />

                            <Line type="monotone" dataKey="sma20" stroke="#ED8936" strokeWidth={1} dot={false} strokeDasharray="5 5" name="SMA 20" />
                            <Line type="monotone" dataKey="sma50" stroke="#F6AD55" strokeWidth={1} dot={false} strokeDasharray="5 5" name="SMA 50" />
                            <Line type="monotone" dataKey="price" stroke="#00B5D8" strokeWidth={2} dot={false} name="Price" />
                            <Line type="monotone" dataKey="predicted" stroke="#9F7AEA" strokeWidth={2} strokeDasharray="5 5" dot={{ fill: '#9F7AEA', r: 4 }} name="Predicted" />

                            <ReferenceLine
                                x={chartData[180]?.date}
                                stroke="#CBD5E0"
                                strokeDasharray="3 3"
                                label={{ value: 'Today', position: 'top', fill: textColor, fontSize: 11 }}
                            />
                        </ComposedChart>
                    </ResponsiveContainer>
                </Box>
            )}

            <HStack spacing={6} justify="center" flexWrap="wrap">
                <HStack><Box w={4} h={0.5} bg="cyan.400" /><Text fontSize="xs" color="gray.500">Historical</Text></HStack>
                <HStack><Box w={4} h={0.5} bg="purple.400" borderStyle="dashed" borderWidth="1px" /><Text fontSize="xs" color="gray.500">Predicted</Text></HStack>
                <HStack><Box w={4} h={0.5} bg="orange.400" opacity={0.7} /><Text fontSize="xs" color="gray.500">SMA 20/50</Text></HStack>
            </HStack>
        </VStack>
    )
}
