import {
    Box,
    HStack,
    VStack,
    Text,
    Icon,
    useColorMode,
    Badge,
} from '@chakra-ui/react'
import { FiTrendingUp, FiTrendingDown, FiClock } from 'react-icons/fi'

interface IndexData {
    name: string
    value: number
    change: number
    change_percent: number
    trend: 'up' | 'down'
}

interface MarketOverviewProps {
    indices: {
        nifty50: IndexData
        sensex: IndexData
        market_status?: string
    } | null
    loading: boolean
}

export default function MarketOverview({ indices, loading }: MarketOverviewProps) {
    const { colorMode } = useColorMode()

    const cardBg = colorMode === 'dark' ? 'gray.800' : 'white'
    const borderColor = colorMode === 'dark' ? 'gray.700' : 'gray.200'

    // Default data if not provided
    const defaultIndices = {
        nifty50: { name: 'NIFTY 50', value: 22456.80, change: 156.35, change_percent: 0.70, trend: 'up' as const },
        sensex: { name: 'SENSEX', value: 73852.94, change: 512.48, change_percent: 0.70, trend: 'up' as const },
        market_status: 'closed'
    }

    const data = indices || defaultIndices
    const marketStatus = data.market_status || 'closed'

    const IndexCard = ({ index }: { index: IndexData }) => {
        const isPositive = index.change_percent >= 0
        const TrendIcon = isPositive ? FiTrendingUp : FiTrendingDown
        const trendColor = isPositive ? 'green.400' : 'red.400'

        return (
            <Box
                bg={cardBg}
                borderRadius="xl"
                p={6}
                border="1px solid"
                borderColor={borderColor}
                flex={1}
                position="relative"
                overflow="hidden"
                transition="all 0.2s"
                _hover={{ transform: 'translateY(-2px)', boxShadow: 'lg' }}
            >
                {/* Gradient accent */}
                <Box
                    position="absolute"
                    top={0}
                    left={0}
                    right={0}
                    h="3px"
                    bg={isPositive ? 'linear-gradient(90deg, #48BB78 0%, #38A169 100%)' : 'linear-gradient(90deg, #F56565 0%, #E53E3E 100%)'}
                />

                <VStack align="start" spacing={2}>
                    <HStack justify="space-between" w="full">
                        <Text fontSize="sm" color="gray.500" fontWeight="600">
                            {index.name}
                        </Text>
                        <Icon as={TrendIcon} color={trendColor} boxSize={5} />
                    </HStack>

                    <Text fontSize="3xl" fontWeight="800">
                        {index.value.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                    </Text>

                    <HStack spacing={3}>
                        <HStack spacing={1}>
                            <Text color={trendColor} fontWeight="600">
                                {isPositive ? '+' : ''}{index.change.toFixed(2)}
                            </Text>
                        </HStack>
                        <Badge colorScheme={isPositive ? 'green' : 'red'} variant="subtle" fontSize="sm" px={2} py={1} borderRadius="md">
                            {isPositive ? '+' : ''}{index.change_percent.toFixed(2)}%
                        </Badge>
                    </HStack>
                </VStack>
            </Box>
        )
    }

    return (
        <Box>
            <HStack justify="space-between" mb={4}>
                <HStack spacing={2}>
                    <Icon as={FiClock} color="gray.500" />
                    <Badge colorScheme={marketStatus === 'open' ? 'green' : 'orange'} variant="subtle">
                        Market {marketStatus === 'open' ? 'Open' : 'Closed'}
                    </Badge>
                </HStack>
            </HStack>

            <HStack spacing={6} align="stretch" flexWrap={{ base: 'wrap', md: 'nowrap' }}>
                <IndexCard index={data.nifty50} />
                <IndexCard index={data.sensex} />
            </HStack>
        </Box>
    )
}
