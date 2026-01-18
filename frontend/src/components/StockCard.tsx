import {
    Box,
    HStack,
    VStack,
    Text,
    Icon,
    useColorMode,
    Badge,
} from '@chakra-ui/react'
import { FiTrendingUp, FiTrendingDown } from 'react-icons/fi'

interface StockCardProps {
    symbol: string
    name: string
    price: number
    changePercent: number
    prediction?: number
    confidence?: 'high' | 'medium' | 'low'
    compact?: boolean
}

export default function StockCard({
    symbol,
    name,
    price,
    changePercent,
    prediction,
    confidence,
    compact = false,
}: StockCardProps) {
    const { colorMode } = useColorMode()
    const isPositive = changePercent >= 0
    const TrendIcon = isPositive ? FiTrendingUp : FiTrendingDown
    const trendColor = isPositive ? 'green.400' : 'red.400'

    const bg = colorMode === 'dark' ? 'gray.700' : 'gray.50'
    const hoverBg = colorMode === 'dark' ? 'gray.600' : 'gray.100'

    if (compact) {
        return (
            <Box
                bg={bg}
                borderRadius="lg"
                p={3}
                transition="all 0.2s"
                _hover={{ bg: hoverBg, transform: 'translateX(4px)' }}
                cursor="pointer"
            >
                <HStack justify="space-between">
                    <VStack align="start" spacing={0}>
                        <Text fontWeight="700" fontSize="sm">{symbol}</Text>
                        <Text fontSize="xs" color="gray.500" noOfLines={1}>{name}</Text>
                    </VStack>

                    <VStack align="end" spacing={0}>
                        <Text fontWeight="600" fontSize="sm">
                            ₹{price.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                        </Text>
                        <HStack spacing={1}>
                            <Icon as={TrendIcon} color={trendColor} boxSize={3} />
                            <Text fontSize="xs" fontWeight="600" color={trendColor}>
                                {isPositive ? '+' : ''}{changePercent.toFixed(2)}%
                            </Text>
                        </HStack>
                    </VStack>
                </HStack>
            </Box>
        )
    }

    return (
        <Box
            bg={bg}
            borderRadius="xl"
            p={4}
            transition="all 0.2s"
            _hover={{ bg: hoverBg, transform: 'translateY(-2px)', boxShadow: 'md' }}
            cursor="pointer"
        >
            <HStack justify="space-between" mb={3}>
                <VStack align="start" spacing={0}>
                    <Text fontWeight="700">{symbol}</Text>
                    <Text fontSize="sm" color="gray.500">{name}</Text>
                </VStack>

                {prediction && confidence && (
                    <Badge
                        colorScheme={confidence === 'high' ? 'green' : confidence === 'medium' ? 'yellow' : 'red'}
                        variant="subtle"
                    >
                        AI: {confidence}
                    </Badge>
                )}
            </HStack>

            <HStack justify="space-between" align="end">
                <VStack align="start" spacing={1}>
                    <Text fontSize="xl" fontWeight="800">
                        ₹{price.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                    </Text>
                    <HStack spacing={1}>
                        <Icon as={TrendIcon} color={trendColor} />
                        <Text fontWeight="600" color={trendColor}>
                            {isPositive ? '+' : ''}{changePercent.toFixed(2)}%
                        </Text>
                    </HStack>
                </VStack>

                {prediction && (
                    <VStack align="end" spacing={0}>
                        <Text fontSize="xs" color="gray.500">Predicted</Text>
                        <Text fontWeight="600">₹{prediction.toFixed(2)}</Text>
                    </VStack>
                )}
            </HStack>
        </Box>
    )
}
