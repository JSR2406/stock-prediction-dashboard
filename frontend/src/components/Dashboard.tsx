import { useState, useEffect, useCallback } from 'react'
import {
    Box,
    Container,
    Grid,
    GridItem,
    Heading,
    Text,
    VStack,
    useColorMode,
    Alert,
    AlertIcon,
    HStack,
    Icon,
    Tabs,
    TabList,
    TabPanels,
    Tab,
    TabPanel,
} from '@chakra-ui/react'
import { FiTrendingUp, FiActivity, FiBriefcase, FiGrid, FiPieChart } from 'react-icons/fi'

import MarketOverview from './MarketOverview'
import StockCard from './StockCard'
import PredictionDashboard from './PredictionDashboard'
import MarketHeatmap from './MarketHeatmap'
import CommoditiesPanel from './CommoditiesPanel'
import CryptoPanel from './CryptoPanel'
import Watchlist from './Watchlist'
import AdvancedChart from './AdvancedChart'
import { stocksApi, commoditiesApi, cryptoApi } from '../services/api'
import { useWebSocket } from '../hooks'

export default function Dashboard() {
    const { colorMode } = useColorMode()
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [data, setData] = useState<any>({
        indices: null,
        movers: null,
        commodities: null,
        crypto: null,
    })
    const [lastUpdated, setLastUpdated] = useState<Date>(new Date())

    // WebSocket for real-time updates
    const { lastMessage, isConnected, subscribe } = useWebSocket()

    // Subscribe to indices and movers
    useEffect(() => {
        const symbolsToSubscribe = ['^NSEI', '^BSESN']

        if (data.movers?.top_gainers) {
            data.movers.top_gainers.forEach((s: any) => symbolsToSubscribe.push(s.symbol))
        }
        if (data.movers?.top_losers) {
            data.movers.top_losers.forEach((s: any) => symbolsToSubscribe.push(s.symbol))
        }

        if (isConnected && symbolsToSubscribe.length > 0) {
            subscribe(symbolsToSubscribe)
        }
    }, [data.movers, isConnected, subscribe])

    // Update state from WebSocket messages
    useEffect(() => {
        if (lastMessage && lastMessage.type === 'price_update') {
            setData((prev: any) => {
                const newData = { ...prev }

                // Update indices
                if (lastMessage.symbol === '^NSEI' && newData.indices?.nifty50) {
                    newData.indices.nifty50 = {
                        ...newData.indices.nifty50,
                        value: lastMessage.price,
                        change: lastMessage.change,
                        change_percent: lastMessage.change_percent
                    }
                }
                if (lastMessage.symbol === '^BSESN' && newData.indices?.sensex) {
                    newData.indices.sensex = {
                        ...newData.indices.sensex,
                        value: lastMessage.price,
                        change: lastMessage.change,
                        change_percent: lastMessage.change_percent
                    }
                }

                // Update movers
                if (newData.movers) {
                    ['top_gainers', 'top_losers'].forEach(key => {
                        if (newData.movers[key]) {
                            newData.movers[key] = newData.movers[key].map((s: any) => {
                                if (s.symbol === lastMessage.symbol) {
                                    return {
                                        ...s,
                                        price: lastMessage.price,
                                        change_percent: lastMessage.change_percent
                                    }
                                }
                                return s
                            })
                        }
                    })
                }

                return newData
            })
        }
    }, [lastMessage])

    const fetchData = useCallback(async () => {
        try {
            setLoading(true)
            const [indicesRes, moversRes, commoditiesRes, cryptoRes] = await Promise.allSettled([
                stocksApi.getIndices(),
                stocksApi.getTopMovers(5),
                commoditiesApi.getAll(),
                cryptoApi.getTop(10),
            ])

            setData({
                indices: indicesRes.status === 'fulfilled' ? indicesRes.value.data : null,
                movers: moversRes.status === 'fulfilled' ? moversRes.value.data : null,
                commodities: commoditiesRes.status === 'fulfilled' ? commoditiesRes.value.data : null,
                crypto: cryptoRes.status === 'fulfilled' ? cryptoRes.value.data?.data : null,
            })

            setLastUpdated(new Date())
        } catch (err) {
            setError('Failed to fetch market data.')
            console.error('Dashboard fetch error:', err)
        } finally {
            setLoading(false)
        }
    }, [])

    useEffect(() => {
        fetchData()
        const interval = setInterval(fetchData, 60000) // Refresh every minute
        return () => clearInterval(interval)
    }, [fetchData])

    const cardBg = colorMode === 'dark' ? 'gray.800' : 'white'
    const borderColor = colorMode === 'dark' ? 'gray.700' : 'gray.200'

    return (
        <Container maxW="container.xl" py={6}>
            {/* Header Section */}
            <Box mb={8}>
                <VStack align="start" spacing={1}>
                    <Heading size="xl" fontWeight="800" letterSpacing="tight">
                        Market Intelligence
                    </Heading>
                    <HStack spacing={2}>
                        <Icon as={FiActivity} color="blue.500" />
                        <Text color="gray.500" fontSize="sm" fontWeight="600">
                            AI-powered analytics for Indian Markets • Updated {lastUpdated.toLocaleTimeString('en-IN')}
                        </Text>
                    </HStack>
                </VStack>
            </Box>

            {error && (
                <Alert status="warning" borderRadius="xl" mb={6} variant="subtle">
                    <AlertIcon />
                    {error} - Using fallback data streams
                </Alert>
            )}

            {/* Main Tabs for different views */}
            <Tabs variant="soft-rounded" colorScheme="blue" mb={8}>
                <TabList bg={cardBg} p={1} borderRadius="full" border="1px solid" borderColor={borderColor} w="fit-content">
                    <Tab fontSize="xs" fontWeight="bold">
                        <HStack spacing={2}>
                            <Icon as={FiGrid} />
                            <Text>Overview</Text>
                        </HStack>
                    </Tab>
                    <Tab fontSize="xs" fontWeight="bold">
                        <HStack spacing={2}>
                            <Icon as={FiPieChart} />
                            <Text>Heatmap</Text>
                        </HStack>
                    </Tab>
                    <Tab fontSize="xs" fontWeight="bold">
                        <HStack spacing={2}>
                            <Icon as={FiActivity} />
                            <Text>AI Predictions</Text>
                        </HStack>
                    </Tab>
                </TabList>

                <TabPanels>
                    {/* Overview Tab */}
                    <TabPanel px={0} pt={6}>
                        <Grid templateColumns={{ base: '1fr', lg: 'repeat(3, 1fr)' }} gap={6}>
                            <GridItem colSpan={{ base: 1, lg: 3 }}>
                                <MarketOverview indices={data.indices} loading={loading} />
                            </GridItem>

                            <GridItem colSpan={{ base: 1, lg: 2 }}>
                                <VStack spacing={6} align="stretch">
                                    <AdvancedChart symbol="RELIANCE" />
                                    <Grid templateColumns={{ base: '1fr', md: '1fr 1fr' }} gap={6}>
                                        <Box bg={cardBg} borderRadius="xl" border="1px solid" borderColor={borderColor} p={5}>
                                            <HStack mb={4} justify="space-between">
                                                <HStack>
                                                    <Icon as={FiTrendingUp} color="green.400" />
                                                    <Heading size="sm">Top Gainers</Heading>
                                                </HStack>
                                            </HStack>
                                            <VStack spacing={3} align="stretch">
                                                {data.movers?.top_gainers?.map((stock: any) => (
                                                    <StockCard key={stock.symbol} {...stock} price={stock.price} changePercent={stock.change_percent} compact />
                                                ))}
                                            </VStack>
                                        </Box>
                                        <Box bg={cardBg} borderRadius="xl" border="1px solid" borderColor={borderColor} p={5}>
                                            <HStack mb={4} justify="space-between">
                                                <HStack>
                                                    <Icon as={FiTrendingUp} color="red.400" transform="scaleY(-1)" />
                                                    <Heading size="sm">Top Losers</Heading>
                                                </HStack>
                                            </HStack>
                                            <VStack spacing={3} align="stretch">
                                                {data.movers?.top_losers?.map((stock: any) => (
                                                    <StockCard key={stock.symbol} {...stock} price={stock.price} changePercent={stock.change_percent} compact />
                                                ))}
                                            </VStack>
                                        </Box>
                                    </Grid>
                                </VStack>
                            </GridItem>

                            <GridItem>
                                <VStack spacing={6} align="stretch">
                                    <Box bg={cardBg} borderRadius="xl" border="1px solid" borderColor={borderColor} p={5}>
                                        <HStack mb={4}>
                                            <Icon as={FiBriefcase} color="purple.400" />
                                            <Heading size="sm">My Watchlist</Heading>
                                        </HStack>
                                        <Watchlist />
                                    </Box>
                                    <CommoditiesPanel data={data.commodities} loading={loading} />
                                </VStack>
                            </GridItem>

                            <GridItem colSpan={{ base: 1, lg: 3 }}>
                                <CryptoPanel data={data.crypto} loading={loading} />
                            </GridItem>
                        </Grid>
                    </TabPanel>

                    {/* Heatmap Tab */}
                    <TabPanel px={0} pt={6}>
                        <MarketHeatmap />
                    </TabPanel>

                    {/* AI Predictions Tab */}
                    <TabPanel px={0} pt={6}>
                        <PredictionDashboard defaultSymbol="RELIANCE" />
                    </TabPanel>
                </TabPanels>
            </Tabs>

            {/* Disclaimer */}
            <Box mt={10}>
                <Alert status="info" variant="subtle" borderRadius="xl" border="1px solid" borderColor="blue.100">
                    <AlertIcon />
                    <VStack align="start" spacing={0}>
                        <Text fontSize="sm" fontWeight="bold">Data Disclaimer</Text>
                        <Text fontSize="xs" color="gray.600">
                            Market data is provided for informational purposes only. AI predictions are based on historical patterns and technical indicators and should not be considered financial advice.
                        </Text>
                    </VStack>
                </Alert>
            </Box>
        </Container>
    )
}
