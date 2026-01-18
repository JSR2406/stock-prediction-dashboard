import { useState, useEffect } from 'react'
import {
    Box,
    VStack,
    HStack,
    Text,
    IconButton,
    Input,
    InputGroup,
    InputLeftElement,
    useColorMode,
    Badge,
    Flex,
    Icon,
    useToast,
} from '@chakra-ui/react'
import { FiSearch, FiPlus, FiX, FiTrendingUp, FiTrendingDown } from 'react-icons/fi'
import { useWebSocket } from '../hooks'
import { stocksApi } from '../services/api'

interface WatchlistItem {
    symbol: string
    name: string
    price: number
    changePercent: number
    prediction?: number
}

const defaultWatchlist: WatchlistItem[] = [
    { symbol: 'RELIANCE', name: 'Reliance Industries', price: 2456.30, changePercent: 1.25, prediction: 2502.50 },
    { symbol: 'TCS', name: 'Tata Consultancy', price: 3892.45, changePercent: -0.85, prediction: 3950.00 },
    { symbol: 'INFY', name: 'Infosys Limited', price: 1678.90, changePercent: 2.15, prediction: 1725.00 },
    { symbol: 'HDFCBANK', name: 'HDFC Bank', price: 1654.20, changePercent: 0.45, prediction: 1680.00 },
]

export default function Watchlist() {
    const { colorMode } = useColorMode()
    const toast = useToast()
    const [watchlist, setWatchlist] = useState<WatchlistItem[]>([])
    const [searchQuery, setSearchQuery] = useState('')
    const [isAdding, setIsAdding] = useState(false)
    const [isSearching, setIsSearching] = useState(false)

    const itemBg = colorMode === 'dark' ? 'gray.700' : 'gray.50'
    const hoverBg = colorMode === 'dark' ? 'gray.600' : 'gray.100'

    // Real-time WebSocket integration
    const { lastMessage, isConnected, subscribe, unsubscribe } = useWebSocket()

    // Initialize watchlist
    useEffect(() => {
        const saved = localStorage.getItem('stockWatchlist')
        if (saved) {
            try {
                setWatchlist(JSON.parse(saved))
            } catch {
                setWatchlist(defaultWatchlist)
            }
        } else {
            setWatchlist(defaultWatchlist)
        }
    }, [])

    // Subscribe to all symbols in watchlist
    useEffect(() => {
        if (watchlist.length > 0 && isConnected) {
            const symbols = watchlist.map(item => item.symbol)
            subscribe(symbols)
            return () => unsubscribe(symbols)
        }
    }, [watchlist.length, isConnected, subscribe, unsubscribe])

    // Update prices from WebSocket
    useEffect(() => {
        if (lastMessage && lastMessage.type === 'price_update') {
            setWatchlist(prev => prev.map(item => {
                if (item.symbol === lastMessage.symbol) {
                    return {
                        ...item,
                        price: lastMessage.price,
                        changePercent: lastMessage.change_percent
                    }
                }
                return item
            }))
        }
    }, [lastMessage])

    useEffect(() => {
        if (watchlist.length > 0) {
            localStorage.setItem('stockWatchlist', JSON.stringify(watchlist))
        }
    }, [watchlist])

    const removeFromWatchlist = (symbol: string) => {
        setWatchlist((prev) => prev.filter((item) => item.symbol !== symbol))
        unsubscribe([symbol])
        toast({
            title: 'Removed from watchlist',
            status: 'info',
            duration: 2000,
            isClosable: true,
        })
    }

    const addToWatchlist = async (symbol: string) => {
        const upperSymbol = symbol.toUpperCase().trim()
        if (!upperSymbol) return

        if (watchlist.find((item) => item.symbol === upperSymbol)) {
            toast({ title: 'Already in watchlist', status: 'warning', duration: 2000 })
            return
        }

        setIsSearching(true)
        try {
            // Fetch initial data from API
            const response = await stocksApi.getQuote(upperSymbol)
            if (response.data && response.data.price) {
                const newItem: WatchlistItem = {
                    symbol: upperSymbol,
                    name: response.data.name || `${upperSymbol} Ltd.`,
                    price: response.data.price,
                    changePercent: response.data.change_percent || 0,
                    prediction: response.data.price * (1 + (Math.random() * 0.05 - 0.01)) // Mock prediction
                }
                setWatchlist((prev) => [...prev, newItem])
                setSearchQuery('')
                setIsAdding(false)
                toast({ title: `${upperSymbol} added`, status: 'success', duration: 2000 })
            } else {
                throw new Error('Stock not found')
            }
        } catch (error) {
            toast({
                title: 'Error',
                description: `Could not find stock ${upperSymbol}`,
                status: 'error',
                duration: 3000,
            })
        } finally {
            setIsSearching(false)
        }
    }

    const WatchlistItemCard = ({ item }: { item: WatchlistItem }) => {
        const isPositive = item.changePercent >= 0
        const predictionChange = item.prediction
            ? ((item.prediction - item.price) / item.price) * 100
            : 0

        return (
            <Box bg={itemBg} borderRadius="lg" p={3} _hover={{ bg: hoverBg }} transition="all 0.2s">
                <Flex justify="space-between" align="center">
                    <HStack spacing={3}>
                        <Box w="3px" h="40px" borderRadius="full" bg={isPositive ? 'green.400' : 'red.400'} />
                        <VStack align="start" spacing={0}>
                            <Text fontWeight="700" fontSize="sm">{item.symbol}</Text>
                            <Text fontSize="xs" color="gray.500" noOfLines={1} maxW="100px">{item.name}</Text>
                        </VStack>
                    </HStack>

                    <VStack align="end" spacing={0}>
                        <Text fontWeight="600" fontSize="sm">
                            ₹{item.price.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                        </Text>
                        <HStack spacing={1}>
                            <Icon as={isPositive ? FiTrendingUp : FiTrendingDown} color={isPositive ? 'green.400' : 'red.400'} boxSize={3} />
                            <Text fontSize="xs" fontWeight="600" color={isPositive ? 'green.400' : 'red.400'}>
                                {isPositive ? '+' : ''}{item.changePercent.toFixed(2)}%
                            </Text>
                        </HStack>
                    </VStack>

                    <HStack spacing={2}>
                        {item.prediction && (
                            <Badge colorScheme={predictionChange >= 0 ? 'green' : 'red'} fontSize="xs" variant="subtle">
                                {predictionChange >= 0 ? '↑' : '↓'}{Math.abs(predictionChange).toFixed(1)}%
                            </Badge>
                        )}
                        <IconButton
                            aria-label="Remove"
                            icon={<FiX />}
                            size="xs"
                            variant="ghost"
                            colorScheme="red"
                            opacity={0.5}
                            _hover={{ opacity: 1 }}
                            onClick={() => removeFromWatchlist(item.symbol)}
                        />
                    </HStack>
                </Flex>
            </Box>
        )
    }

    return (
        <VStack spacing={3} align="stretch">
            {isAdding ? (
                <HStack>
                    <InputGroup size="sm">
                        <InputLeftElement><Icon as={FiSearch} color="gray.400" /></InputLeftElement>
                        <Input
                            placeholder="Enter symbol (e.g. RELIANCE)"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            onKeyPress={(e) => e.key === 'Enter' && addToWatchlist(searchQuery)}
                            autoFocus
                        />
                    </InputGroup>
                    <IconButton
                        aria-label="Add"
                        icon={<FiPlus />}
                        size="sm"
                        colorScheme="green"
                        onClick={() => addToWatchlist(searchQuery)}
                        isLoading={isSearching}
                        isDisabled={!searchQuery}
                    />
                    <IconButton aria-label="Cancel" icon={<FiX />} size="sm" variant="ghost" onClick={() => setIsAdding(false)} />
                </HStack>
            ) : (
                <IconButton aria-label="Add stock" icon={<FiPlus />} size="sm" variant="outline" w="full" onClick={() => setIsAdding(true)} />
            )}

            {watchlist.map((item) => (
                <WatchlistItemCard key={item.symbol} item={item} />
            ))}

            {watchlist.length === 0 && (
                <Text fontSize="sm" color="gray.500" textAlign="center" py={4}>
                    Your watchlist is empty. Add stocks to track!
                </Text>
            )}
        </VStack>
    )
}
