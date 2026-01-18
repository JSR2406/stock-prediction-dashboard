import {
    Box,
    Grid,
    HStack,
    VStack,
    Text,
    Image,
    Icon,
    useColorMode,
    Skeleton,
    Badge,
    Flex,
} from '@chakra-ui/react'
import { FiCircle, FiTrendingUp, FiTrendingDown } from 'react-icons/fi'

interface CryptoData {
    id: string
    symbol: string
    name: string
    current_price: number
    price_change_percentage_24h: number
    market_cap: number
    image?: string
    trend: 'up' | 'down'
}

interface CryptoPanelProps {
    data: CryptoData[] | null
    loading: boolean
}

// Demo crypto data
const demoCryptos: CryptoData[] = [
    { id: 'bitcoin', symbol: 'BTC', name: 'Bitcoin', current_price: 5628450, price_change_percentage_24h: 2.45, market_cap: 109800000000000, trend: 'up' },
    { id: 'ethereum', symbol: 'ETH', name: 'Ethereum', current_price: 287650, price_change_percentage_24h: 3.12, market_cap: 34500000000000, trend: 'up' },
    { id: 'tether', symbol: 'USDT', name: 'Tether', current_price: 83.52, price_change_percentage_24h: 0.02, market_cap: 9530000000000, trend: 'up' },
    { id: 'binancecoin', symbol: 'BNB', name: 'BNB', current_price: 52480, price_change_percentage_24h: -1.23, market_cap: 7850000000000, trend: 'down' },
    { id: 'ripple', symbol: 'XRP', name: 'XRP', current_price: 254.75, price_change_percentage_24h: 5.67, market_cap: 2940000000000, trend: 'up' },
    { id: 'cardano', symbol: 'ADA', name: 'Cardano', current_price: 108.32, price_change_percentage_24h: -2.34, market_cap: 3830000000000, trend: 'down' },
    { id: 'solana', symbol: 'SOL', name: 'Solana', current_price: 17520, price_change_percentage_24h: 4.89, market_cap: 7640000000000, trend: 'up' },
    { id: 'polkadot', symbol: 'DOT', name: 'Polkadot', current_price: 854.20, price_change_percentage_24h: 1.56, market_cap: 1120000000000, trend: 'up' },
    { id: 'dogecoin', symbol: 'DOGE', name: 'Dogecoin', current_price: 26.84, price_change_percentage_24h: -0.78, market_cap: 3820000000000, trend: 'down' },
    { id: 'polygon', symbol: 'MATIC', name: 'Polygon', current_price: 136.45, price_change_percentage_24h: 2.34, market_cap: 1340000000000, trend: 'up' },
]

const formatMarketCap = (value: number): string => {
    if (value >= 10000000000000) {
        return `₹${(value / 10000000000000).toFixed(1)}L Cr`
    }
    if (value >= 100000000000) {
        return `₹${(value / 10000000).toFixed(0)} Cr`
    }
    return `₹${value.toLocaleString('en-IN')}`
}

export default function CryptoPanel({ data, loading }: CryptoPanelProps) {
    const { colorMode } = useColorMode()

    const cardBg = colorMode === 'dark' ? 'gray.800' : 'white'
    const borderColor = colorMode === 'dark' ? 'gray.700' : 'gray.200'
    const itemBg = colorMode === 'dark' ? 'gray.700' : 'gray.50'

    const cryptos = data || demoCryptos

    const CryptoCard = ({ crypto, index }: { crypto: CryptoData; index: number }) => {
        const isPositive = crypto.price_change_percentage_24h >= 0

        return (
            <Box
                bg={itemBg}
                borderRadius="lg"
                p={4}
                transition="all 0.2s"
                _hover={{ transform: 'scale(1.02)' }}
            >
                <Flex justify="space-between" align="start" mb={3}>
                    <HStack spacing={3}>
                        {crypto.image ? (
                            <Image src={crypto.image} alt={crypto.name} boxSize="32px" borderRadius="full" />
                        ) : (
                            <Box
                                w="32px"
                                h="32px"
                                borderRadius="full"
                                bg="orange.400"
                                display="flex"
                                alignItems="center"
                                justifyContent="center"
                            >
                                <Text fontSize="sm" fontWeight="bold" color="white">
                                    {crypto.symbol[0]}
                                </Text>
                            </Box>
                        )}
                        <VStack align="start" spacing={0}>
                            <Text fontWeight="700" fontSize="sm">{crypto.symbol}</Text>
                            <Text fontSize="xs" color="gray.500" noOfLines={1}>{crypto.name}</Text>
                        </VStack>
                    </HStack>
                    <Badge
                        colorScheme={crypto.market_cap > 50000000000000 ? 'green' : 'gray'}
                        fontSize="xs"
                        variant="subtle"
                    >
                        #{index + 1}
                    </Badge>
                </Flex>

                <VStack align="start" spacing={1}>
                    <Text fontSize="lg" fontWeight="800">
                        ₹{crypto.current_price.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                    </Text>
                    <HStack justify="space-between" w="full">
                        <HStack spacing={1}>
                            <Icon
                                as={isPositive ? FiTrendingUp : FiTrendingDown}
                                color={isPositive ? 'green.400' : 'red.400'}
                                boxSize={3}
                            />
                            <Text
                                fontSize="sm"
                                fontWeight="600"
                                color={isPositive ? 'green.400' : 'red.400'}
                            >
                                {isPositive ? '+' : ''}{crypto.price_change_percentage_24h.toFixed(2)}%
                            </Text>
                        </HStack>
                        <Text fontSize="xs" color="gray.500">
                            MCap: {formatMarketCap(crypto.market_cap)}
                        </Text>
                    </HStack>
                </VStack>
            </Box>
        )
    }

    return (
        <Box bg={cardBg} borderRadius="xl" border="1px solid" borderColor={borderColor} p={5}>
            <HStack justify="space-between" mb={4}>
                <HStack>
                    <Icon as={FiCircle} color="orange.400" boxSize={5} />
                    <Text fontWeight="700" fontSize="lg">Cryptocurrency</Text>
                </HStack>
                <Badge colorScheme="orange" variant="subtle">
                    Top 10 by Market Cap
                </Badge>
            </HStack>

            {loading ? (
                <Grid templateColumns={{ base: 'repeat(2, 1fr)', md: 'repeat(5, 1fr)' }} gap={3}>
                    {Array(10).fill(0).map((_, i) => (
                        <Skeleton key={i} height="120px" borderRadius="lg" />
                    ))}
                </Grid>
            ) : (
                <Grid templateColumns={{ base: 'repeat(2, 1fr)', md: 'repeat(5, 1fr)' }} gap={3}>
                    {cryptos.slice(0, 10).map((crypto, index) => (
                        <CryptoCard key={crypto.id} crypto={crypto} index={index} />
                    ))}
                </Grid>
            )}

            <Text fontSize="xs" color="gray.500" mt={4} textAlign="center">
                Prices in Indian Rupees (₹) • Data from CoinGecko
            </Text>
        </Box>
    )
}
