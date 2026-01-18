import { useState, useMemo } from 'react'
import {
    Box,
    VStack,
    HStack,
    Text,
    Select,
    useColorMode,
    Badge,
    SimpleGrid,
    Checkbox,
    CheckboxGroup,
    Icon,
    Flex,
    Table,
    Thead,
    Tbody,
    Tr,
    Th,
    Td,
} from '@chakra-ui/react'
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Legend,
} from 'recharts'
import { FiTrendingUp, FiTrendingDown, FiBarChart2 } from 'react-icons/fi'

// Types
interface StockData {
    symbol: string
    name: string
    data: Array<{ date: string; price: number }>
    currentPrice: number
    change: number
    changePercent: number
}

// Generate normalized demo data
const generateNormalizedData = (symbols: string[]): Array<{ date: string;[key: string]: number | string }> => {
    const days = 90
    const data: Array<{ date: string;[key: string]: number | string }> = []

    // Start all stocks at 100
    const baseValues: Record<string, number> = {}
    symbols.forEach(s => baseValues[s] = 100)

    for (let i = 0; i < days; i++) {
        const date = new Date()
        date.setDate(date.getDate() - (days - i))

        const point: { date: string;[key: string]: number | string } = {
            date: date.toLocaleDateString('en-IN', { day: '2-digit', month: 'short' })
        }

        symbols.forEach(symbol => {
            const change = (Math.random() - 0.48) * 3
            baseValues[symbol] *= (1 + change / 100)
            point[symbol] = Math.round(baseValues[symbol] * 100) / 100
        })

        data.push(point)
    }

    return data
}

// Demo stock list
const STOCKS: StockData[] = [
    { symbol: 'RELIANCE', name: 'Reliance Industries', data: [], currentPrice: 2456.30, change: 52.80, changePercent: 2.20 },
    { symbol: 'TCS', name: 'Tata Consultancy', data: [], currentPrice: 3892.45, change: 45.30, changePercent: 1.18 },
    { symbol: 'HDFCBANK', name: 'HDFC Bank', data: [], currentPrice: 1654.20, change: -8.30, changePercent: -0.50 },
    { symbol: 'INFY', name: 'Infosys', data: [], currentPrice: 1567.80, change: 23.45, changePercent: 1.52 },
    { symbol: 'ICICIBANK', name: 'ICICI Bank', data: [], currentPrice: 1023.45, change: -5.60, changePercent: -0.54 },
    { symbol: 'SBIN', name: 'State Bank of India', data: [], currentPrice: 628.90, change: 3.20, changePercent: 0.51 },
]

const COLORS = ['#00B5D8', '#ED8936', '#48BB78', '#9F7AEA', '#F56565', '#38B2AC']

interface StockComparisonProps {
    defaultSymbols?: string[]
}

export default function StockComparison({ defaultSymbols = ['RELIANCE', 'TCS'] }: StockComparisonProps) {
    const { colorMode } = useColorMode()
    const [selectedSymbols, setSelectedSymbols] = useState<string[]>(defaultSymbols)
    const [period, setPeriod] = useState('3M')

    // Generate comparison data
    const chartData = useMemo(() => {
        return generateNormalizedData(selectedSymbols)
    }, [selectedSymbols])

    // Calculate metrics
    const metrics = useMemo(() => {
        if (chartData.length === 0) return []

        return selectedSymbols.map(symbol => {
            const stock = STOCKS.find(s => s.symbol === symbol)
            const startValue = chartData[0][symbol] as number
            const endValue = chartData[chartData.length - 1][symbol] as number
            const performance = ((endValue - startValue) / startValue) * 100

            // Calculate volatility
            const values = chartData.map(d => d[symbol] as number)
            const mean = values.reduce((a, b) => a + b, 0) / values.length
            const variance = values.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / values.length
            const volatility = Math.sqrt(variance)

            return {
                symbol,
                name: stock?.name || symbol,
                startValue,
                endValue,
                performance,
                volatility,
                currentPrice: stock?.currentPrice || 0,
                change: stock?.changePercent || 0
            }
        })
    }, [chartData, selectedSymbols])

    // Correlation matrix (simplified)
    const correlations = useMemo(() => {
        if (selectedSymbols.length < 2) return []

        const matrix: Array<{ pair: string; correlation: number }> = []
        for (let i = 0; i < selectedSymbols.length; i++) {
            for (let j = i + 1; j < selectedSymbols.length; j++) {
                // Simplified correlation (would use proper Pearson in production)
                const correlation = 0.3 + Math.random() * 0.6
                matrix.push({
                    pair: `${selectedSymbols[i]} / ${selectedSymbols[j]}`,
                    correlation
                })
            }
        }
        return matrix
    }, [selectedSymbols])

    const cardBg = colorMode === 'dark' ? 'gray.800' : 'white'
    const borderColor = colorMode === 'dark' ? 'gray.700' : 'gray.200'
    const gridColor = colorMode === 'dark' ? '#2D3748' : '#E2E8F0'

    return (
        <VStack spacing={6} align="stretch">
            {/* Header */}
            <Flex justify="space-between" align="center" wrap="wrap" gap={4}>
                <Text fontSize="xl" fontWeight="800">Stock Comparison</Text>

                <HStack>
                    <Select size="sm" value={period} onChange={(e) => setPeriod(e.target.value)} w="100px">
                        <option value="1M">1 Month</option>
                        <option value="3M">3 Months</option>
                        <option value="6M">6 Months</option>
                        <option value="1Y">1 Year</option>
                    </Select>
                </HStack>
            </Flex>

            {/* Stock Selection */}
            <Box bg={cardBg} p={4} borderRadius="xl" border="1px solid" borderColor={borderColor}>
                <Text fontWeight="600" mb={3}>Select Stocks (max 4)</Text>
                <CheckboxGroup
                    value={selectedSymbols}
                    onChange={(values) => setSelectedSymbols(values.slice(0, 4) as string[])}
                >
                    <Flex flexWrap="wrap" gap={4}>
                        {STOCKS.map((stock, idx) => (
                            <Checkbox
                                key={stock.symbol}
                                value={stock.symbol}
                                isDisabled={selectedSymbols.length >= 4 && !selectedSymbols.includes(stock.symbol)}
                            >
                                <HStack>
                                    <Box w={3} h={3} borderRadius="sm" bg={COLORS[idx % COLORS.length]} />
                                    <Text>{stock.symbol}</Text>
                                </HStack>
                            </Checkbox>
                        ))}
                    </Flex>
                </CheckboxGroup>
            </Box>

            {/* Normalized Chart */}
            <Box bg={cardBg} p={5} borderRadius="xl" border="1px solid" borderColor={borderColor}>
                <HStack mb={4}>
                    <Icon as={FiBarChart2} color="blue.400" />
                    <Text fontWeight="700">Normalized Price (Base = 100)</Text>
                </HStack>

                <Box h="350px">
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                            <XAxis dataKey="date" stroke="#718096" fontSize={11} interval="preserveStartEnd" />
                            <YAxis stroke="#718096" fontSize={11} domain={['auto', 'auto']} />
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: colorMode === 'dark' ? '#1A202C' : '#FFFFFF',
                                    border: 'none',
                                    borderRadius: '8px',
                                    boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
                                }}
                            />
                            <Legend />

                            {selectedSymbols.map((symbol, idx) => (
                                <Line
                                    key={symbol}
                                    type="monotone"
                                    dataKey={symbol}
                                    stroke={COLORS[idx % COLORS.length]}
                                    strokeWidth={2}
                                    dot={false}
                                />
                            ))}
                        </LineChart>
                    </ResponsiveContainer>
                </Box>
            </Box>

            {/* Performance Table */}
            <Box bg={cardBg} p={5} borderRadius="xl" border="1px solid" borderColor={borderColor}>
                <HStack mb={4}>
                    <Icon as={FiTrendingUp} color="green.400" />
                    <Text fontWeight="700">Performance Metrics</Text>
                </HStack>

                <Box overflowX="auto">
                    <Table variant="simple" size="sm">
                        <Thead>
                            <Tr>
                                <Th>Stock</Th>
                                <Th isNumeric>Current Price</Th>
                                <Th isNumeric>Today</Th>
                                <Th isNumeric>{period} Performance</Th>
                                <Th isNumeric>Volatility</Th>
                            </Tr>
                        </Thead>
                        <Tbody>
                            {metrics.map((m, idx) => (
                                <Tr key={m.symbol}>
                                    <Td>
                                        <HStack>
                                            <Box w={3} h={3} borderRadius="sm" bg={COLORS[idx % COLORS.length]} />
                                            <VStack align="start" spacing={0}>
                                                <Text fontWeight="600">{m.symbol}</Text>
                                                <Text fontSize="xs" color="gray.500">{m.name}</Text>
                                            </VStack>
                                        </HStack>
                                    </Td>
                                    <Td isNumeric fontWeight="600">₹{m.currentPrice.toLocaleString('en-IN')}</Td>
                                    <Td isNumeric>
                                        <Badge colorScheme={m.change >= 0 ? 'green' : 'red'}>
                                            {m.change >= 0 ? '+' : ''}{m.change.toFixed(2)}%
                                        </Badge>
                                    </Td>
                                    <Td isNumeric>
                                        <HStack justify="flex-end">
                                            <Icon
                                                as={m.performance >= 0 ? FiTrendingUp : FiTrendingDown}
                                                color={m.performance >= 0 ? 'green.400' : 'red.400'}
                                            />
                                            <Text color={m.performance >= 0 ? 'green.400' : 'red.400'} fontWeight="600">
                                                {m.performance >= 0 ? '+' : ''}{m.performance.toFixed(2)}%
                                            </Text>
                                        </HStack>
                                    </Td>
                                    <Td isNumeric>{m.volatility.toFixed(2)}</Td>
                                </Tr>
                            ))}
                        </Tbody>
                    </Table>
                </Box>
            </Box>

            {/* Correlation Matrix */}
            {correlations.length > 0 && (
                <Box bg={cardBg} p={5} borderRadius="xl" border="1px solid" borderColor={borderColor}>
                    <Text fontWeight="700" mb={4}>Correlation Analysis</Text>

                    <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={3}>
                        {correlations.map(c => (
                            <Box
                                key={c.pair}
                                p={3}
                                borderRadius="lg"
                                bg={colorMode === 'dark' ? 'gray.700' : 'gray.50'}
                            >
                                <Text fontSize="sm" color="gray.500">{c.pair}</Text>
                                <Text fontSize="xl" fontWeight="700" color={c.correlation > 0.7 ? 'green.400' : c.correlation > 0.4 ? 'yellow.400' : 'red.400'}>
                                    {c.correlation.toFixed(3)}
                                </Text>
                                <Text fontSize="xs" color="gray.500">
                                    {c.correlation > 0.7 ? 'Strong positive' : c.correlation > 0.4 ? 'Moderate' : 'Weak'} correlation
                                </Text>
                            </Box>
                        ))}
                    </SimpleGrid>
                </Box>
            )}
        </VStack>
    )
}
