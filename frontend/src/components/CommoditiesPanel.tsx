import {
    Box,
    VStack,
    HStack,
    Text,
    Icon,
    useColorMode,
    Skeleton,
    Badge,
    Flex,
} from '@chakra-ui/react'
import { FiDroplet } from 'react-icons/fi'

interface CommodityData {
    symbol: string
    name: string
    price_per_gram?: number
    price_per_10g?: number
    price_per_kg?: number
    unit: string
    currency: string
}

interface CommoditiesPanelProps {
    data: { data?: CommodityData[] } | null
    loading: boolean
}

export default function CommoditiesPanel({ data, loading }: CommoditiesPanelProps) {
    const { colorMode } = useColorMode()

    const cardBg = colorMode === 'dark' ? 'gray.800' : 'white'
    const borderColor = colorMode === 'dark' ? 'gray.700' : 'gray.200'
    const itemBg = colorMode === 'dark' ? 'gray.700' : 'gray.50'

    // Demo data
    const gold = data?.data?.[0] || {
        symbol: 'XAU',
        name: 'Gold',
        price_per_gram: 6542.50,
        price_per_10g: 65425.00,
        unit: 'gram',
        currency: 'INR',
    }

    const silver = data?.data?.[1] || {
        symbol: 'XAG',
        name: 'Silver',
        price_per_gram: 78.25,
        price_per_kg: 78250.00,
        unit: 'gram',
        currency: 'INR',
    }

    const CommodityCard = ({ commodity, gradient, icon }: {
        commodity: CommodityData
        gradient: string
        icon: string
    }) => (
        <Box
            bg={itemBg}
            borderRadius="lg"
            p={4}
            position="relative"
            overflow="hidden"
            transition="all 0.2s"
            _hover={{ transform: 'scale(1.02)' }}
        >
            <Box position="absolute" top={0} left={0} w="4px" h="full" bg={gradient} />

            <Flex justify="space-between" align="start">
                <VStack align="start" spacing={1}>
                    <HStack>
                        <Text fontSize="2xl">{icon}</Text>
                        <Text fontWeight="700">{commodity.name}</Text>
                    </HStack>

                    <VStack align="start" spacing={0}>
                        {commodity.price_per_10g && (
                            <Text fontSize="xl" fontWeight="800">
                                ₹{commodity.price_per_10g.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                                <Text as="span" fontSize="sm" fontWeight="normal" color="gray.500"> /10g</Text>
                            </Text>
                        )}
                        {commodity.price_per_kg && (
                            <Text fontSize="xl" fontWeight="800">
                                ₹{commodity.price_per_kg.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                                <Text as="span" fontSize="sm" fontWeight="normal" color="gray.500"> /kg</Text>
                            </Text>
                        )}
                        {commodity.price_per_gram && (
                            <Text fontSize="sm" color="gray.500">
                                ₹{commodity.price_per_gram.toLocaleString('en-IN', { maximumFractionDigits: 2 })}/g
                            </Text>
                        )}
                    </VStack>
                </VStack>

                <Badge colorScheme="orange" variant="subtle" fontSize="xs">Live</Badge>
            </Flex>
        </Box>
    )

    return (
        <Box bg={cardBg} borderRadius="xl" border="1px solid" borderColor={borderColor} p={5} h="full">
            <HStack mb={4}>
                <Icon as={FiDroplet} color="yellow.400" boxSize={5} />
                <Text fontWeight="700" fontSize="lg">Commodities</Text>
            </HStack>

            {loading ? (
                <VStack spacing={3}>
                    <Skeleton height="100px" borderRadius="lg" w="full" />
                    <Skeleton height="100px" borderRadius="lg" w="full" />
                </VStack>
            ) : (
                <VStack spacing={3}>
                    <CommodityCard
                        commodity={gold}
                        gradient="linear-gradient(135deg, #f5af19 0%, #f12711 100%)"
                        icon="🥇"
                    />
                    <CommodityCard
                        commodity={silver}
                        gradient="linear-gradient(135deg, #bdc3c7 0%, #2c3e50 100%)"
                        icon="🥈"
                    />
                </VStack>
            )}

            <Text fontSize="xs" color="gray.500" mt={4} textAlign="center">
                Prices in Indian Rupees (₹)
            </Text>
        </Box>
    )
}
