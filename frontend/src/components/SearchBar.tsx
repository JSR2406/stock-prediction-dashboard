import { useState, useEffect, useRef, useCallback } from 'react'
import {
    Box,
    Input,
    InputGroup,
    InputLeftElement,
    InputRightElement,
    VStack,
    HStack,
    Text,
    useColorMode,
    useDisclosure,
    Modal,
    ModalOverlay,
    ModalContent,
    ModalBody,
    IconButton,
    Kbd,
    Badge,
    Flex,
    Icon,
} from '@chakra-ui/react'
import { FiSearch, FiX, FiClock, FiPlus, FiTrendingUp } from 'react-icons/fi'

// Types
interface StockResult {
    symbol: string
    name: string
    exchange: string
    sector?: string
}

// Demo stock data
const NSE_STOCKS: StockResult[] = [
    { symbol: 'RELIANCE', name: 'Reliance Industries Ltd', exchange: 'NSE', sector: 'Oil & Gas' },
    { symbol: 'TCS', name: 'Tata Consultancy Services', exchange: 'NSE', sector: 'IT' },
    { symbol: 'HDFCBANK', name: 'HDFC Bank Limited', exchange: 'NSE', sector: 'Banking' },
    { symbol: 'INFY', name: 'Infosys Limited', exchange: 'NSE', sector: 'IT' },
    { symbol: 'ICICIBANK', name: 'ICICI Bank Limited', exchange: 'NSE', sector: 'Banking' },
    { symbol: 'SBIN', name: 'State Bank of India', exchange: 'NSE', sector: 'Banking' },
    { symbol: 'BHARTIARTL', name: 'Bharti Airtel Limited', exchange: 'NSE', sector: 'Telecom' },
    { symbol: 'ITC', name: 'ITC Limited', exchange: 'NSE', sector: 'FMCG' },
    { symbol: 'KOTAKBANK', name: 'Kotak Mahindra Bank', exchange: 'NSE', sector: 'Banking' },
    { symbol: 'LT', name: 'Larsen & Toubro Limited', exchange: 'NSE', sector: 'Infrastructure' },
    { symbol: 'WIPRO', name: 'Wipro Limited', exchange: 'NSE', sector: 'IT' },
    { symbol: 'ADANIENT', name: 'Adani Enterprises', exchange: 'NSE', sector: 'Conglomerate' },
    { symbol: 'TATAMOTORS', name: 'Tata Motors Limited', exchange: 'NSE', sector: 'Automobile' },
    { symbol: 'SUNPHARMA', name: 'Sun Pharmaceutical', exchange: 'NSE', sector: 'Pharma' },
    { symbol: 'TITAN', name: 'Titan Company Limited', exchange: 'NSE', sector: 'Consumer' },
    { symbol: 'ASIANPAINT', name: 'Asian Paints Limited', exchange: 'NSE', sector: 'Consumer' },
    { symbol: 'MARUTI', name: 'Maruti Suzuki India', exchange: 'NSE', sector: 'Automobile' },
    { symbol: 'BAJFINANCE', name: 'Bajaj Finance Limited', exchange: 'NSE', sector: 'Finance' },
    { symbol: 'HCLTECH', name: 'HCL Technologies', exchange: 'NSE', sector: 'IT' },
    { symbol: 'AXISBANK', name: 'Axis Bank Limited', exchange: 'NSE', sector: 'Banking' },
]

interface SearchBarProps {
    onSelect?: (stock: StockResult) => void
    onAddToWatchlist?: (symbol: string) => void
    placeholder?: string
}

export default function SearchBar({ onSelect, onAddToWatchlist, placeholder = "Search stocks..." }: SearchBarProps) {
    const { colorMode } = useColorMode()
    const { isOpen, onOpen, onClose } = useDisclosure()
    const [query, setQuery] = useState('')
    const [results, setResults] = useState<StockResult[]>([])
    const [recentSearches, setRecentSearches] = useState<string[]>([])
    const [selectedIndex, setSelectedIndex] = useState(0)
    const inputRef = useRef<HTMLInputElement>(null)

    // Load recent searches from localStorage
    useEffect(() => {
        const saved = localStorage.getItem('recentSearches')
        if (saved) {
            try {
                setRecentSearches(JSON.parse(saved))
            } catch { }
        }
    }, [])

    // Save recent searches
    const addToRecent = useCallback((symbol: string) => {
        setRecentSearches(prev => {
            const updated = [symbol, ...prev.filter(s => s !== symbol)].slice(0, 5)
            localStorage.setItem('recentSearches', JSON.stringify(updated))
            return updated
        })
    }, [])

    // Search stocks
    useEffect(() => {
        if (!query.trim()) {
            setResults([])
            return
        }

        const q = query.toLowerCase()
        const filtered = NSE_STOCKS.filter(
            stock =>
                stock.symbol.toLowerCase().includes(q) ||
                stock.name.toLowerCase().includes(q) ||
                stock.sector?.toLowerCase().includes(q)
        ).slice(0, 10)

        setResults(filtered)
        setSelectedIndex(0)
    }, [query])

    // Keyboard shortcut (Cmd/Ctrl + K)
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
                e.preventDefault()
                onOpen()
            }
        }

        window.addEventListener('keydown', handleKeyDown)
        return () => window.removeEventListener('keydown', handleKeyDown)
    }, [onOpen])

    // Focus input when modal opens
    useEffect(() => {
        if (isOpen) {
            setTimeout(() => inputRef.current?.focus(), 100)
        }
    }, [isOpen])

    // Handle keyboard navigation
    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'ArrowDown') {
            e.preventDefault()
            setSelectedIndex(prev => Math.min(prev + 1, results.length - 1))
        } else if (e.key === 'ArrowUp') {
            e.preventDefault()
            setSelectedIndex(prev => Math.max(prev - 1, 0))
        } else if (e.key === 'Enter' && results[selectedIndex]) {
            handleSelect(results[selectedIndex])
        } else if (e.key === 'Escape') {
            onClose()
        }
    }

    const handleSelect = (stock: StockResult) => {
        addToRecent(stock.symbol)
        onSelect?.(stock)
        setQuery('')
        onClose()
    }

    const handleAddToWatchlist = (e: React.MouseEvent, symbol: string) => {
        e.stopPropagation()
        onAddToWatchlist?.(symbol)
    }

    const cardBg = colorMode === 'dark' ? 'gray.800' : 'white'
    const hoverBg = colorMode === 'dark' ? 'gray.700' : 'gray.50'
    const borderColor = colorMode === 'dark' ? 'gray.600' : 'gray.200'

    return (
        <>
            {/* Search Trigger Button */}
            <InputGroup maxW="400px" onClick={onOpen} cursor="pointer">
                <InputLeftElement>
                    <Icon as={FiSearch} color="gray.400" />
                </InputLeftElement>
                <Input
                    placeholder={placeholder}
                    readOnly
                    cursor="pointer"
                    bg={colorMode === 'dark' ? 'gray.700' : 'gray.50'}
                    _hover={{ borderColor: 'blue.400' }}
                />
                <InputRightElement width="auto" pr={2}>
                    <HStack spacing={1}>
                        <Kbd>⌘</Kbd>
                        <Kbd>K</Kbd>
                    </HStack>
                </InputRightElement>
            </InputGroup>

            {/* Search Modal */}
            <Modal isOpen={isOpen} onClose={onClose} size="lg">
                <ModalOverlay bg="blackAlpha.600" backdropFilter="blur(4px)" />
                <ModalContent bg={cardBg} borderRadius="xl" overflow="hidden" mt={20}>
                    <ModalBody p={0}>
                        {/* Search Input */}
                        <InputGroup size="lg">
                            <InputLeftElement h="60px">
                                <Icon as={FiSearch} color="gray.400" boxSize={5} />
                            </InputLeftElement>
                            <Input
                                ref={inputRef}
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                                onKeyDown={handleKeyDown}
                                placeholder="Search by symbol or company name..."
                                border="none"
                                h="60px"
                                fontSize="md"
                                _focus={{ boxShadow: 'none' }}
                            />
                            {query && (
                                <InputRightElement h="60px">
                                    <IconButton
                                        aria-label="Clear"
                                        icon={<FiX />}
                                        size="sm"
                                        variant="ghost"
                                        onClick={() => setQuery('')}
                                    />
                                </InputRightElement>
                            )}
                        </InputGroup>

                        <Box borderTop="1px solid" borderColor={borderColor} maxH="400px" overflowY="auto">
                            {/* Recent Searches */}
                            {!query && recentSearches.length > 0 && (
                                <Box p={4}>
                                    <HStack mb={3}>
                                        <Icon as={FiClock} color="gray.400" />
                                        <Text fontSize="sm" color="gray.500" fontWeight="500">Recent</Text>
                                    </HStack>
                                    <VStack align="stretch" spacing={1}>
                                        {recentSearches.map(symbol => {
                                            const stock = NSE_STOCKS.find(s => s.symbol === symbol)
                                            if (!stock) return null
                                            return (
                                                <Box
                                                    key={symbol}
                                                    p={3}
                                                    borderRadius="lg"
                                                    cursor="pointer"
                                                    _hover={{ bg: hoverBg }}
                                                    onClick={() => handleSelect(stock)}
                                                >
                                                    <HStack justify="space-between">
                                                        <HStack>
                                                            <Text fontWeight="600">{stock.symbol}</Text>
                                                            <Text color="gray.500" fontSize="sm">{stock.name}</Text>
                                                        </HStack>
                                                        <Badge colorScheme="gray">{stock.exchange}</Badge>
                                                    </HStack>
                                                </Box>
                                            )
                                        })}
                                    </VStack>
                                </Box>
                            )}

                            {/* Search Results */}
                            {query && results.length > 0 && (
                                <VStack align="stretch" spacing={0} p={2}>
                                    {results.map((stock, index) => (
                                        <Flex
                                            key={stock.symbol}
                                            p={3}
                                            borderRadius="lg"
                                            cursor="pointer"
                                            bg={index === selectedIndex ? hoverBg : 'transparent'}
                                            _hover={{ bg: hoverBg }}
                                            onClick={() => handleSelect(stock)}
                                            justify="space-between"
                                            align="center"
                                        >
                                            <HStack spacing={3}>
                                                <Icon as={FiTrendingUp} color="blue.400" />
                                                <Box>
                                                    <HStack>
                                                        <Text fontWeight="600">{stock.symbol}</Text>
                                                        <Badge colorScheme="blue" size="sm">{stock.exchange}</Badge>
                                                    </HStack>
                                                    <Text fontSize="sm" color="gray.500">{stock.name}</Text>
                                                </Box>
                                            </HStack>

                                            <HStack>
                                                {stock.sector && (
                                                    <Badge colorScheme="purple" variant="subtle">{stock.sector}</Badge>
                                                )}
                                                {onAddToWatchlist && (
                                                    <IconButton
                                                        aria-label="Add to watchlist"
                                                        icon={<FiPlus />}
                                                        size="sm"
                                                        variant="ghost"
                                                        colorScheme="blue"
                                                        onClick={(e) => handleAddToWatchlist(e, stock.symbol)}
                                                    />
                                                )}
                                            </HStack>
                                        </Flex>
                                    ))}
                                </VStack>
                            )}

                            {/* No Results */}
                            {query && results.length === 0 && (
                                <Box p={8} textAlign="center">
                                    <Text color="gray.500">No stocks found for "{query}"</Text>
                                </Box>
                            )}

                            {/* Trending (when empty) */}
                            {!query && recentSearches.length === 0 && (
                                <Box p={4}>
                                    <HStack mb={3}>
                                        <Icon as={FiTrendingUp} color="green.400" />
                                        <Text fontSize="sm" color="gray.500" fontWeight="500">Popular Stocks</Text>
                                    </HStack>
                                    <Flex flexWrap="wrap" gap={2}>
                                        {['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK'].map(symbol => (
                                            <Badge
                                                key={symbol}
                                                px={3}
                                                py={1}
                                                borderRadius="full"
                                                cursor="pointer"
                                                colorScheme="blue"
                                                variant="subtle"
                                                onClick={() => {
                                                    const stock = NSE_STOCKS.find(s => s.symbol === symbol)
                                                    if (stock) handleSelect(stock)
                                                }}
                                            >
                                                {symbol}
                                            </Badge>
                                        ))}
                                    </Flex>
                                </Box>
                            )}
                        </Box>

                        {/* Footer */}
                        <Box p={3} borderTop="1px solid" borderColor={borderColor} bg={colorMode === 'dark' ? 'gray.750' : 'gray.50'}>
                            <HStack justify="center" spacing={4} fontSize="xs" color="gray.500">
                                <HStack>
                                    <Kbd>↑</Kbd><Kbd>↓</Kbd>
                                    <Text>Navigate</Text>
                                </HStack>
                                <HStack>
                                    <Kbd>↵</Kbd>
                                    <Text>Select</Text>
                                </HStack>
                                <HStack>
                                    <Kbd>Esc</Kbd>
                                    <Text>Close</Text>
                                </HStack>
                            </HStack>
                        </Box>
                    </ModalBody>
                </ModalContent>
            </Modal>
        </>
    )
}
