import { useState, useEffect, useMemo, useCallback } from 'react'
import {
    Box,
    VStack,
    HStack,
    Text,
    Input,
    Select,
    useColorMode,
    Icon,
    Flex,
    NumberInput,
    NumberInputField,
    Button,
    Badge,
    Divider,
    SimpleGrid,
    Skeleton,
    Alert,
    AlertIcon,
    useToast,
} from '@chakra-ui/react'
import { FiRefreshCw, FiArrowRight, FiTrendingUp, FiTrendingDown, FiActivity } from 'react-icons/fi'
import { LineChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { cryptoApi, CryptoData } from '../services/api'

// Types
interface CryptoRate extends CryptoData {
    // Extended fields if needed
}

// Fallback demo crypto data
const DEMO_CRYPTOS: any[] = [
    { id: 'bitcoin', symbol: 'BTC', name: 'Bitcoin', current_price: 5250000, price_change_percentage_24h: 2.34, trend: 'up', image: '' },
    { id: 'ethereum', symbol: 'ETH', name: 'Ethereum', current_price: 245000, price_change_percentage_24h: 1.89, trend: 'up', image: '' },
    { id: 'binancecoin', symbol: 'BNB', name: 'BNB', current_price: 32500, price_change_percentage_24h: -0.45, trend: 'down', image: '' },
    { id: 'solana', symbol: 'SOL', name: 'Solana', current_price: 9200, price_change_percentage_24h: 5.67, trend: 'up', image: '' },
    { id: 'ripple', symbol: 'XRP', name: 'XRP', current_price: 45, price_change_percentage_24h: -1.23, trend: 'down', image: '' },
    { id: 'cardano', symbol: 'ADA', name: 'Cardano', current_price: 42, price_change_percentage_24h: 0.89, trend: 'up', image: '' },
]

// Generate price history (simulated for visual)
const generatePriceHistory = (basePrice: number, change: number) => {
    const data = []
    let price = basePrice / (1 + change / 100)
    for (let i = 24; i >= 0; i--) {
        const volatility = 0.005 + (Math.abs(change) / 2000)
        price *= (1 + (Math.random() - 0.48 + (change / 1000)) * volatility)
        data.push({
            time: `${i}h ago`,
            price: Math.round(price)
        })
    }
    return data
}

export default function CryptoConverter() {
    const { colorMode } = useColorMode()
    const toast = useToast()
    const [cryptos, setCryptos] = useState<CryptoData[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [isRefreshing, setIsRefreshing] = useState(false)
    const [fromCryptoId, setFromCryptoId] = useState('bitcoin')
    const [amount, setAmount] = useState(1)
    const [error, setError] = useState<string | null>(null)

    // Fetch crypto data
    const fetchCryptos = useCallback(async (isManual = false) => {
        try {
            if (isManual) setIsRefreshing(true)
            else setIsLoading(true)

            const response = await cryptoApi.getTop(12)
            if (response.data && response.data.success) {
                setCryptos(response.data.data)
                setError(null)
            } else {
                setCryptos(DEMO_CRYPTOS)
                setError('Using demo data - API returned invalid response')
            }
        } catch (err) {
            console.error('Failed to fetch crypto data:', err)
            setCryptos(DEMO_CRYPTOS)
            setError('Using demo data - API connection failed')
        } finally {
            setIsLoading(false)
            setIsRefreshing(false)
        }
    }, [])

    useEffect(() => {
        fetchCryptos()
        // Refresh every 5 minutes
        const interval = setInterval(() => fetchCryptos(), 300000)
        return () => clearInterval(interval)
    }, [fetchCryptos])

    const selectedCrypto = useMemo(() => {
        return cryptos.find(c => c.id === fromCryptoId) || cryptos[0] || (DEMO_CRYPTOS[0] as CryptoData)
    }, [cryptos, fromCryptoId])

    const result = useMemo(() => {
        return amount * (selectedCrypto?.current_price || 0)
    }, [amount, selectedCrypto])

    const priceHistory = useMemo(() => {
        if (!selectedCrypto) return []
        return generatePriceHistory(selectedCrypto.current_price, selectedCrypto.price_change_percentage_24h)
    }, [selectedCrypto])

    const cardBg = colorMode === 'dark' ? 'gray.800' : 'white'
    const borderColor = colorMode === 'dark' ? 'gray.700' : 'gray.200'

    if (isLoading && cryptos.length === 0) {
        return (
            <VStack spacing={6} align="stretch">
                <Skeleton height="30px" width="200px" />
                <Skeleton height="150px" borderRadius="xl" />
                <Skeleton height="250px" borderRadius="xl" />
            </VStack>
        )
    }

    return (
        <VStack spacing={6} align="stretch">
            <HStack justify="space-between">
                <HStack>
                    <Text fontSize="xl" fontWeight="800">Crypto Converter</Text>
                    {!error && <Badge colorScheme="green" variant="subtle">LIVE</Badge>}
                </HStack>
                <Button
                    size="sm"
                    variant="ghost"
                    leftIcon={<FiRefreshCw />}
                    isLoading={isRefreshing}
                    onClick={() => fetchCryptos(true)}
                >
                    Refresh
                </Button>
            </HStack>

            {error && (
                <Alert status="warning" borderRadius="md" size="sm">
                    <AlertIcon />
                    {error}
                </Alert>
            )}

            {/* Converter */}
            <Box bg={cardBg} p={5} borderRadius="xl" border="1px solid" borderColor={borderColor} boxShadow="sm">
                <SimpleGrid columns={{ base: 1, md: 3 }} spacing={6} alignItems="center">
                    {/* From */}
                    <VStack align="start">
                        <Text fontSize="xs" fontWeight="bold" color="gray.500" textTransform="uppercase" letterSpacing="wider">From</Text>
                        <Select
                            value={fromCryptoId}
                            onChange={(e) => setFromCryptoId(e.target.value)}
                            bg={colorMode === 'dark' ? 'gray.700' : 'gray.50'}
                            fontWeight="600"
                        >
                            {cryptos.map(c => (
                                <option key={c.id} value={c.id}>{c.symbol} - {c.name}</option>
                            ))}
                        </Select>
                        <NumberInput w="full" value={amount} min={0} onChange={(_, val) => setAmount(val || 0)}>
                            <NumberInputField
                                placeholder="Amount"
                                fontWeight="bold"
                                fontSize="lg"
                            />
                        </NumberInput>
                    </VStack>

                    {/* Arrow */}
                    <Flex justify="center" display={{ base: 'none', md: 'flex' }}>
                        <Box p={2} bg="blue.500" borderRadius="full" color="white" boxShadow="0 0 15px rgba(66, 153, 225, 0.4)">
                            <Icon as={FiArrowRight} boxSize={5} />
                        </Box>
                    </Flex>
                    <Flex justify="center" display={{ base: 'flex', md: 'none' }} py={2}>
                        <Icon as={FiActivity} boxSize={5} color="blue.400" />
                    </Flex>

                    {/* To */}
                    <VStack align="start">
                        <Text fontSize="xs" fontWeight="bold" color="gray.500" textTransform="uppercase" letterSpacing="wider">To</Text>
                        <Input value="INR - Indian Rupee" isReadOnly bg={colorMode === 'dark' ? 'gray.700' : 'gray.50'} fontWeight="600" />
                        <Box
                            w="full"
                            p={2}
                            bg={colorMode === 'dark' ? 'gray.900' : 'blue.50'}
                            borderRadius="md"
                            border="1px solid"
                            borderColor="blue.200"
                        >
                            <Text fontWeight="800" fontSize="xl" color="blue.500">
                                ₹ {result.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                            </Text>
                        </Box>
                    </VStack>
                </SimpleGrid>

                <Divider my={5} />

                {/* Rate info */}
                {selectedCrypto && (
                    <HStack justify="space-between" wrap="wrap" gap={2}>
                        <VStack align="start" spacing={0}>
                            <Text fontSize="xs" color="gray.500" fontWeight="bold" textTransform="uppercase">Exchange Rate</Text>
                            <Text fontSize="sm" fontWeight="600">
                                1 {selectedCrypto.symbol} = ₹{selectedCrypto.current_price.toLocaleString('en-IN')}
                            </Text>
                        </VStack>
                        <Badge
                            p={2}
                            borderRadius="lg"
                            colorScheme={selectedCrypto.price_change_percentage_24h >= 0 ? 'green' : 'red'}
                            variant="subtle"
                        >
                            <HStack spacing={1}>
                                <Icon as={selectedCrypto.price_change_percentage_24h >= 0 ? FiTrendingUp : FiTrendingDown} />
                                <Text fontWeight="700">24h: {selectedCrypto.price_change_percentage_24h >= 0 ? '+' : ''}{selectedCrypto.price_change_percentage_24h.toFixed(2)}%</Text>
                            </HStack>
                        </Badge>
                    </HStack>
                )}
            </Box>

            {/* 24h Price Chart */}
            {selectedCrypto && (
                <Box bg={cardBg} p={5} borderRadius="xl" border="1px solid" borderColor={borderColor} boxShadow="sm">
                    <HStack justify="space-between" mb={4}>
                        <HStack>
                            <Box w={8} h={8} bg="blue.500" color="white" borderRadius="md" display="flex" alignItems="center" justifyContent="center" fontWeight="bold">
                                {selectedCrypto.symbol[0]}
                            </Box>
                            <VStack align="start" spacing={0}>
                                <Text fontWeight="800" fontSize="md">{selectedCrypto.symbol}/INR</Text>
                                <Text fontSize="xs" color="gray.500">24H Simulated Trend</Text>
                            </VStack>
                        </HStack>
                        <VStack align="end" spacing={0}>
                            <Text fontWeight="800" color={selectedCrypto.price_change_percentage_24h >= 0 ? 'green.400' : 'red.400'}>
                                {selectedCrypto.price_change_percentage_24h >= 0 ? '+' : ''}{selectedCrypto.price_change_percentage_24h.toFixed(2)}%
                            </Text>
                            <Text fontSize="xs" color="gray.500">Price Movement</Text>
                        </VStack>
                    </HStack>

                    <Box h="200px" mt={2}>
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={priceHistory}>
                                <XAxis dataKey="time" hide />
                                <YAxis hide domain={['auto', 'auto']} />
                                <Tooltip
                                    formatter={(value: number) => [`₹${value.toLocaleString('en-IN')}`, 'Price']}
                                    contentStyle={{
                                        backgroundColor: colorMode === 'dark' ? '#1A202C' : '#FFFFFF',
                                        border: '1px solid #E2E8F0',
                                        borderRadius: '8px',
                                        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                                    }}
                                />
                                <Line
                                    type="monotone"
                                    dataKey="price"
                                    stroke={selectedCrypto.price_change_percentage_24h >= 0 ? '#48BB78' : '#F56565'}
                                    strokeWidth={3}
                                    dot={false}
                                    animationDuration={1500}
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </Box>
                </Box>
            )}

            {/* Quick Rates */}
            <Box bg={cardBg} p={5} borderRadius="xl" border="1px solid" borderColor={borderColor} boxShadow="sm">
                <Text fontWeight="800" mb={4} fontSize="lg">Market Overview</Text>

                <SimpleGrid columns={{ base: 1, sm: 2, md: 3 }} spacing={4}>
                    {cryptos.map(crypto => (
                        <Box
                            key={crypto.id}
                            p={4}
                            borderRadius="xl"
                            border="2px solid"
                            borderColor={fromCryptoId === crypto.id ? 'blue.400' : 'transparent'}
                            bg={colorMode === 'dark' ? 'gray.700' : 'gray.50'}
                            cursor="pointer"
                            onClick={() => setFromCryptoId(crypto.id)}
                            _hover={{ transform: 'translateY(-2px)', shadow: 'md', borderColor: 'blue.200' }}
                            transition="all 0.3s ease"
                        >
                            <HStack justify="space-between">
                                <HStack spacing={3}>
                                    <Box
                                        w={10}
                                        h={10}
                                        borderRadius="full"
                                        bg={colorMode === 'dark' ? 'gray.600' : 'white'}
                                        display="flex"
                                        alignItems="center"
                                        justifyContent="center"
                                        boxShadow="xs"
                                        overflow="hidden"
                                    >
                                        {crypto.image ? (
                                            <img src={crypto.image} alt={crypto.name} width="100%" />
                                        ) : (
                                            <Text fontWeight="bold" color="blue.400">{crypto.symbol[0]}</Text>
                                        )}
                                    </Box>
                                    <VStack align="start" spacing={0}>
                                        <Text fontWeight="700" fontSize="sm">{crypto.symbol}</Text>
                                        <Text fontSize="10px" color="gray.500" fontWeight="bold" textTransform="uppercase">{crypto.name}</Text>
                                    </VStack>
                                </HStack>
                                <VStack align="end" spacing={0}>
                                    <Text fontWeight="800" fontSize="sm">
                                        ₹{crypto.current_price.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                                    </Text>
                                    <Badge
                                        fontSize="9px"
                                        colorScheme={crypto.price_change_percentage_24h >= 0 ? 'green' : 'red'}
                                        variant="subtle"
                                        borderRadius="full"
                                        px={2}
                                    >
                                        {crypto.price_change_percentage_24h >= 0 ? '+' : ''}{crypto.price_change_percentage_24h.toFixed(2)}%
                                    </Badge>
                                </VStack>
                            </HStack>
                        </Box>
                    ))}
                </SimpleGrid>
            </Box>
        </VStack>
    )
}

