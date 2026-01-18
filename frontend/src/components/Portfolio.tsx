import { useState, useEffect, useMemo } from 'react'
import {
    Box,
    VStack,
    HStack,
    Text,
    Input,
    Button,
    IconButton,
    useColorMode,
    Badge,
    Table,
    Thead,
    Tbody,
    Tr,
    Th,
    Td,
    Modal,
    ModalOverlay,
    ModalContent,
    ModalHeader,
    ModalBody,
    ModalFooter,
    ModalCloseButton,
    useDisclosure,
    FormControl,
    FormLabel,
    NumberInput,
    NumberInputField,
    Stat,
    StatLabel,
    StatNumber,
    StatHelpText,
    StatArrow,
    SimpleGrid,
    Progress,
    Tooltip,
    Flex,
    Icon,
} from '@chakra-ui/react'
import { FiPlus, FiTrash2, FiEdit2, FiPieChart, FiTrendingUp } from 'react-icons/fi'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip as RechartsTooltip } from 'recharts'

// Types
interface PortfolioHolding {
    id: string
    symbol: string
    name: string
    quantity: number
    buyPrice: number
    currentPrice: number
    sector?: string
}

interface PortfolioStats {
    totalInvested: number
    currentValue: number
    totalPnL: number
    totalPnLPercent: number
    dayChange: number
    dayChangePercent: number
}

// Demo current prices
const DEMO_PRICES: Record<string, number> = {
    'RELIANCE': 2456.30,
    'TCS': 3892.45,
    'HDFCBANK': 1654.20,
    'INFY': 1567.80,
    'ICICIBANK': 1023.45,
    'SBIN': 628.90,
    'BHARTIARTL': 1245.60,
    'ITC': 456.75,
}

const SECTOR_COLORS: Record<string, string> = {
    'IT': '#3182CE',
    'Banking': '#48BB78',
    'Oil & Gas': '#ED8936',
    'FMCG': '#9F7AEA',
    'Telecom': '#F56565',
    'Automobile': '#38B2AC',
    'Pharma': '#ED64A6',
    'Metals': '#667EEA',
}

const DEMO_HOLDINGS: PortfolioHolding[] = [
    { id: '1', symbol: 'RELIANCE', name: 'Reliance Industries', quantity: 10, buyPrice: 2350, currentPrice: 2456.30, sector: 'Oil & Gas' },
    { id: '2', symbol: 'TCS', name: 'Tata Consultancy', quantity: 5, buyPrice: 3750, currentPrice: 3892.45, sector: 'IT' },
    { id: '3', symbol: 'HDFCBANK', name: 'HDFC Bank', quantity: 15, buyPrice: 1580, currentPrice: 1654.20, sector: 'Banking' },
    { id: '4', symbol: 'INFY', name: 'Infosys', quantity: 20, buyPrice: 1450, currentPrice: 1567.80, sector: 'IT' },
]

export default function Portfolio() {
    const { colorMode } = useColorMode()
    const { isOpen, onOpen, onClose } = useDisclosure()
    const [holdings, setHoldings] = useState<PortfolioHolding[]>([])
    const [editingHolding, setEditingHolding] = useState<PortfolioHolding | null>(null)

    // Form state
    const [formData, setFormData] = useState({
        symbol: '',
        name: '',
        quantity: 1,
        buyPrice: 0,
        sector: 'IT'
    })

    // Load from localStorage
    useEffect(() => {
        const saved = localStorage.getItem('portfolio')
        if (saved) {
            try {
                const parsed = JSON.parse(saved)
                // Update current prices
                const updated = parsed.map((h: PortfolioHolding) => ({
                    ...h,
                    currentPrice: DEMO_PRICES[h.symbol] || h.currentPrice * (1 + (Math.random() - 0.5) * 0.02)
                }))
                setHoldings(updated)
            } catch {
                setHoldings(DEMO_HOLDINGS)
            }
        } else {
            setHoldings(DEMO_HOLDINGS)
        }
    }, [])

    // Save to localStorage
    useEffect(() => {
        if (holdings.length > 0) {
            localStorage.setItem('portfolio', JSON.stringify(holdings))
        }
    }, [holdings])

    // Calculate statistics
    const stats = useMemo((): PortfolioStats => {
        const totalInvested = holdings.reduce((sum, h) => sum + h.quantity * h.buyPrice, 0)
        const currentValue = holdings.reduce((sum, h) => sum + h.quantity * h.currentPrice, 0)
        const totalPnL = currentValue - totalInvested
        const totalPnLPercent = totalInvested > 0 ? (totalPnL / totalInvested) * 100 : 0

        // Simulate day change
        const dayChange = currentValue * 0.008
        const dayChangePercent = 0.8

        return {
            totalInvested,
            currentValue,
            totalPnL,
            totalPnLPercent,
            dayChange,
            dayChangePercent
        }
    }, [holdings])

    // Sector allocation for pie chart
    const sectorData = useMemo(() => {
        const sectors: Record<string, number> = {}
        holdings.forEach(h => {
            const sector = h.sector || 'Other'
            const value = h.quantity * h.currentPrice
            sectors[sector] = (sectors[sector] || 0) + value
        })
        return Object.entries(sectors).map(([name, value]) => ({
            name,
            value: Math.round(value),
            color: SECTOR_COLORS[name] || '#718096'
        }))
    }, [holdings])

    const handleAddHolding = () => {
        setEditingHolding(null)
        setFormData({ symbol: '', name: '', quantity: 1, buyPrice: 0, sector: 'IT' })
        onOpen()
    }

    const handleEditHolding = (holding: PortfolioHolding) => {
        setEditingHolding(holding)
        setFormData({
            symbol: holding.symbol,
            name: holding.name,
            quantity: holding.quantity,
            buyPrice: holding.buyPrice,
            sector: holding.sector || 'IT'
        })
        onOpen()
    }

    const handleSave = () => {
        if (!formData.symbol || formData.quantity <= 0) return

        if (editingHolding) {
            setHoldings(prev => prev.map(h =>
                h.id === editingHolding.id
                    ? {
                        ...h,
                        ...formData,
                        currentPrice: DEMO_PRICES[formData.symbol.toUpperCase()] || formData.buyPrice * 1.05
                    }
                    : h
            ))
        } else {
            const newHolding: PortfolioHolding = {
                id: Date.now().toString(),
                symbol: formData.symbol.toUpperCase(),
                name: formData.name || `${formData.symbol} Ltd.`,
                quantity: formData.quantity,
                buyPrice: formData.buyPrice,
                currentPrice: DEMO_PRICES[formData.symbol.toUpperCase()] || formData.buyPrice * 1.05,
                sector: formData.sector
            }
            setHoldings(prev => [...prev, newHolding])
        }
        onClose()
    }

    const handleDelete = (id: string) => {
        setHoldings(prev => prev.filter(h => h.id !== id))
    }

    const cardBg = colorMode === 'dark' ? 'gray.800' : 'white'
    const borderColor = colorMode === 'dark' ? 'gray.700' : 'gray.200'

    return (
        <VStack spacing={6} align="stretch">
            {/* Portfolio Summary */}
            <SimpleGrid columns={{ base: 2, md: 4 }} spacing={4}>
                <Stat bg={cardBg} p={4} borderRadius="lg" border="1px solid" borderColor={borderColor}>
                    <StatLabel color="gray.500">Total Invested</StatLabel>
                    <StatNumber fontSize="xl">₹{stats.totalInvested.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</StatNumber>
                </Stat>

                <Stat bg={cardBg} p={4} borderRadius="lg" border="1px solid" borderColor={borderColor}>
                    <StatLabel color="gray.500">Current Value</StatLabel>
                    <StatNumber fontSize="xl">₹{stats.currentValue.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</StatNumber>
                </Stat>

                <Stat bg={cardBg} p={4} borderRadius="lg" border="1px solid" borderColor={borderColor}>
                    <StatLabel color="gray.500">Total P&L</StatLabel>
                    <StatNumber fontSize="xl" color={stats.totalPnL >= 0 ? 'green.400' : 'red.400'}>
                        {stats.totalPnL >= 0 ? '+' : ''}₹{stats.totalPnL.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                    </StatNumber>
                    <StatHelpText>
                        <StatArrow type={stats.totalPnLPercent >= 0 ? 'increase' : 'decrease'} />
                        {stats.totalPnLPercent.toFixed(2)}%
                    </StatHelpText>
                </Stat>

                <Stat bg={cardBg} p={4} borderRadius="lg" border="1px solid" borderColor={borderColor}>
                    <StatLabel color="gray.500">Day Change</StatLabel>
                    <StatNumber fontSize="xl" color={stats.dayChange >= 0 ? 'green.400' : 'red.400'}>
                        {stats.dayChange >= 0 ? '+' : ''}₹{stats.dayChange.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                    </StatNumber>
                    <StatHelpText>
                        <StatArrow type={stats.dayChangePercent >= 0 ? 'increase' : 'decrease'} />
                        {stats.dayChangePercent.toFixed(2)}%
                    </StatHelpText>
                </Stat>
            </SimpleGrid>

            {/* Sector Allocation */}
            <Box bg={cardBg} p={5} borderRadius="xl" border="1px solid" borderColor={borderColor}>
                <HStack justify="space-between" mb={4}>
                    <HStack>
                        <Icon as={FiPieChart} color="purple.400" />
                        <Text fontWeight="700">Sector Allocation</Text>
                    </HStack>
                </HStack>

                <Flex direction={{ base: 'column', md: 'row' }} align="center" gap={4}>
                    <Box h="200px" w={{ base: '100%', md: '200px' }}>
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie
                                    data={sectorData}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={40}
                                    outerRadius={80}
                                    paddingAngle={2}
                                    dataKey="value"
                                >
                                    {sectorData.map((entry, index) => (
                                        <Cell key={index} fill={entry.color} />
                                    ))}
                                </Pie>
                                <RechartsTooltip
                                    formatter={(value: number) => `₹${value.toLocaleString('en-IN')}`}
                                />
                            </PieChart>
                        </ResponsiveContainer>
                    </Box>

                    <VStack align="stretch" flex={1} spacing={2}>
                        {sectorData.map(sector => (
                            <HStack key={sector.name} justify="space-between">
                                <HStack>
                                    <Box w={3} h={3} borderRadius="sm" bg={sector.color} />
                                    <Text fontSize="sm">{sector.name}</Text>
                                </HStack>
                                <Text fontSize="sm" fontWeight="600">
                                    ₹{sector.value.toLocaleString('en-IN')}
                                </Text>
                            </HStack>
                        ))}
                    </VStack>
                </Flex>
            </Box>

            {/* Holdings Table */}
            <Box bg={cardBg} borderRadius="xl" border="1px solid" borderColor={borderColor} overflow="hidden">
                <Flex justify="space-between" align="center" p={4} borderBottom="1px solid" borderColor={borderColor}>
                    <HStack>
                        <Icon as={FiTrendingUp} color="cyan.400" />
                        <Text fontWeight="700">Holdings ({holdings.length})</Text>
                    </HStack>
                    <Button size="sm" leftIcon={<FiPlus />} colorScheme="blue" onClick={handleAddHolding}>
                        Add Stock
                    </Button>
                </Flex>

                <Box overflowX="auto">
                    <Table variant="simple" size="sm">
                        <Thead>
                            <Tr>
                                <Th>Stock</Th>
                                <Th isNumeric>Qty</Th>
                                <Th isNumeric>Avg Cost</Th>
                                <Th isNumeric>LTP</Th>
                                <Th isNumeric>Invested</Th>
                                <Th isNumeric>Current</Th>
                                <Th isNumeric>P&L</Th>
                                <Th></Th>
                            </Tr>
                        </Thead>
                        <Tbody>
                            {holdings.map(holding => {
                                const invested = holding.quantity * holding.buyPrice
                                const current = holding.quantity * holding.currentPrice
                                const pnl = current - invested
                                const pnlPercent = (pnl / invested) * 100

                                return (
                                    <Tr key={holding.id} _hover={{ bg: colorMode === 'dark' ? 'gray.700' : 'gray.50' }}>
                                        <Td>
                                            <VStack align="start" spacing={0}>
                                                <Text fontWeight="600">{holding.symbol}</Text>
                                                <Text fontSize="xs" color="gray.500">{holding.name}</Text>
                                            </VStack>
                                        </Td>
                                        <Td isNumeric>{holding.quantity}</Td>
                                        <Td isNumeric>₹{holding.buyPrice.toLocaleString('en-IN')}</Td>
                                        <Td isNumeric fontWeight="600">₹{holding.currentPrice.toLocaleString('en-IN')}</Td>
                                        <Td isNumeric>₹{invested.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</Td>
                                        <Td isNumeric>₹{current.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</Td>
                                        <Td isNumeric>
                                            <VStack align="end" spacing={0}>
                                                <Text color={pnl >= 0 ? 'green.400' : 'red.400'} fontWeight="600">
                                                    {pnl >= 0 ? '+' : ''}₹{pnl.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                                                </Text>
                                                <Badge colorScheme={pnl >= 0 ? 'green' : 'red'} fontSize="xs">
                                                    {pnlPercent >= 0 ? '+' : ''}{pnlPercent.toFixed(2)}%
                                                </Badge>
                                            </VStack>
                                        </Td>
                                        <Td>
                                            <HStack spacing={1}>
                                                <IconButton
                                                    aria-label="Edit"
                                                    icon={<FiEdit2 />}
                                                    size="xs"
                                                    variant="ghost"
                                                    onClick={() => handleEditHolding(holding)}
                                                />
                                                <IconButton
                                                    aria-label="Delete"
                                                    icon={<FiTrash2 />}
                                                    size="xs"
                                                    variant="ghost"
                                                    colorScheme="red"
                                                    onClick={() => handleDelete(holding.id)}
                                                />
                                            </HStack>
                                        </Td>
                                    </Tr>
                                )
                            })}
                        </Tbody>
                    </Table>
                </Box>
            </Box>

            {/* Add/Edit Modal */}
            <Modal isOpen={isOpen} onClose={onClose}>
                <ModalOverlay />
                <ModalContent bg={cardBg}>
                    <ModalHeader>{editingHolding ? 'Edit Holding' : 'Add New Holding'}</ModalHeader>
                    <ModalCloseButton />
                    <ModalBody>
                        <VStack spacing={4}>
                            <FormControl isRequired>
                                <FormLabel>Symbol</FormLabel>
                                <Input
                                    placeholder="e.g., RELIANCE"
                                    value={formData.symbol}
                                    onChange={(e) => setFormData({ ...formData, symbol: e.target.value.toUpperCase() })}
                                />
                            </FormControl>

                            <FormControl>
                                <FormLabel>Company Name</FormLabel>
                                <Input
                                    placeholder="e.g., Reliance Industries Ltd."
                                    value={formData.name}
                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                />
                            </FormControl>

                            <HStack w="full">
                                <FormControl isRequired>
                                    <FormLabel>Quantity</FormLabel>
                                    <NumberInput min={1} value={formData.quantity} onChange={(_, val) => setFormData({ ...formData, quantity: val })}>
                                        <NumberInputField />
                                    </NumberInput>
                                </FormControl>

                                <FormControl isRequired>
                                    <FormLabel>Buy Price (₹)</FormLabel>
                                    <NumberInput min={0} value={formData.buyPrice} onChange={(_, val) => setFormData({ ...formData, buyPrice: val })}>
                                        <NumberInputField />
                                    </NumberInput>
                                </FormControl>
                            </HStack>
                        </VStack>
                    </ModalBody>
                    <ModalFooter>
                        <Button variant="ghost" mr={3} onClick={onClose}>Cancel</Button>
                        <Button colorScheme="blue" onClick={handleSave}>
                            {editingHolding ? 'Update' : 'Add'}
                        </Button>
                    </ModalFooter>
                </ModalContent>
            </Modal>
        </VStack>
    )
}
