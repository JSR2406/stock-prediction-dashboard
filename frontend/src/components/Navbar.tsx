import { useState, useEffect, useMemo } from 'react'
import {
    Box,
    HStack,
    Text,
    Icon,
    useColorMode,
    Button,
    Badge,
    Tooltip,
    Spinner,
} from '@chakra-ui/react'
import { keyframes } from '@emotion/react'
import { FiActivity, FiRefreshCw, FiMoon, FiSun, FiClock } from 'react-icons/fi'

// Market status types
type MarketStatus = 'open' | 'closed' | 'pre-market' | 'after-hours' | 'holiday'

interface MarketInfo {
    status: MarketStatus
    message: string
    nextEvent: string
    colorScheme: string
    pulseColor: string
}

// Pulse animation for live indicator
const pulseAnimation = keyframes`
    0% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.5; transform: scale(1.2); }
    100% { opacity: 1; transform: scale(1); }
`

// Indian market holidays 2026 (example - should be updated yearly)
const MARKET_HOLIDAYS_2026 = [
    '2026-01-26', // Republic Day
    '2026-03-10', // Holi
    '2026-04-14', // Ambedkar Jayanti
    '2026-04-18', // Good Friday
    '2026-05-01', // May Day
    '2026-08-15', // Independence Day
    '2026-10-02', // Gandhi Jayanti
    '2026-10-20', // Diwali (Laxmi Puja)
    '2026-11-04', // Guru Nanak Jayanti
    '2026-12-25', // Christmas
]

// Get current IST time
const getISTTime = (): Date => {
    const now = new Date()
    // Convert to IST (UTC+5:30)
    const istOffset = 5.5 * 60 * 60 * 1000
    const utc = now.getTime() + now.getTimezoneOffset() * 60 * 1000
    return new Date(utc + istOffset)
}

// Check market status
const getMarketStatus = (): MarketInfo => {
    const istNow = getISTTime()
    const day = istNow.getDay() // 0 = Sunday, 6 = Saturday
    const hours = istNow.getHours()
    const minutes = istNow.getMinutes()
    const currentTime = hours * 60 + minutes // Time in minutes from midnight

    // Format current date for holiday check
    const dateStr = istNow.toISOString().split('T')[0]

    // Check for holidays
    if (MARKET_HOLIDAYS_2026.includes(dateStr)) {
        return {
            status: 'holiday',
            message: 'Market Holiday',
            nextEvent: 'Opens next trading day at 9:15 AM',
            colorScheme: 'purple',
            pulseColor: 'purple.400'
        }
    }

    // Check for weekend
    if (day === 0 || day === 6) {
        return {
            status: 'closed',
            message: 'Weekend',
            nextEvent: day === 0 ? 'Opens Monday 9:15 AM' : 'Opens Monday 9:15 AM',
            colorScheme: 'gray',
            pulseColor: 'gray.400'
        }
    }

    // Market times in minutes
    const marketOpen = 9 * 60 + 15  // 9:15 AM
    const marketClose = 15 * 60 + 30 // 3:30 PM
    const preMarketStart = 9 * 60    // 9:00 AM
    const afterHoursEnd = 16 * 60    // 4:00 PM

    if (currentTime >= marketOpen && currentTime < marketClose) {
        const closeIn = marketClose - currentTime
        const closeHours = Math.floor(closeIn / 60)
        const closeMins = closeIn % 60
        return {
            status: 'open',
            message: 'Market Open',
            nextEvent: `Closes in ${closeHours}h ${closeMins}m`,
            colorScheme: 'green',
            pulseColor: 'green.400'
        }
    } else if (currentTime >= preMarketStart && currentTime < marketOpen) {
        const openIn = marketOpen - currentTime
        return {
            status: 'pre-market',
            message: 'Pre-Market',
            nextEvent: `Opens in ${openIn} minutes`,
            colorScheme: 'yellow',
            pulseColor: 'yellow.400'
        }
    } else if (currentTime >= marketClose && currentTime < afterHoursEnd) {
        return {
            status: 'after-hours',
            message: 'After Hours',
            nextEvent: 'Opens tomorrow 9:15 AM',
            colorScheme: 'orange',
            pulseColor: 'orange.400'
        }
    } else {
        return {
            status: 'closed',
            message: 'Market Closed',
            nextEvent: 'Opens 9:15 AM IST',
            colorScheme: 'red',
            pulseColor: 'red.400'
        }
    }
}

export default function Navbar() {
    const { colorMode, toggleColorMode } = useColorMode()
    const [marketInfo, setMarketInfo] = useState<MarketInfo>(getMarketStatus())
    const [currentTime, setCurrentTime] = useState<string>('')
    const [isRefreshing, setIsRefreshing] = useState(false)

    // Update market status every minute
    useEffect(() => {
        const updateStatus = () => {
            setMarketInfo(getMarketStatus())
            const ist = getISTTime()
            setCurrentTime(ist.toLocaleTimeString('en-IN', {
                hour: '2-digit',
                minute: '2-digit',
                hour12: true,
                timeZone: 'Asia/Kolkata'
            }))
        }

        updateStatus()
        const interval = setInterval(updateStatus, 60000) // Update every minute

        return () => clearInterval(interval)
    }, [])

    const handleRefresh = () => {
        setIsRefreshing(true)
        setTimeout(() => {
            window.location.reload()
        }, 500)
    }

    const bg = colorMode === 'dark' ? 'rgba(26, 32, 44, 0.95)' : 'rgba(255, 255, 255, 0.95)'
    const borderColor = colorMode === 'dark' ? 'gray.700' : 'gray.200'

    return (
        <Box
            as="nav"
            bg={bg}
            borderBottom="1px solid"
            borderColor={borderColor}
            py={4}
            px={6}
            position="sticky"
            top={0}
            zIndex={100}
            backdropFilter="blur(10px)"
        >
            <HStack justify="space-between" maxW="container.xl" mx="auto">
                {/* Logo */}
                <HStack spacing={3}>
                    <Icon as={FiActivity} boxSize={6} color="cyan.400" />
                    <Text fontSize="xl" fontWeight="800">
                        StockAI
                    </Text>
                    <Badge colorScheme="cyan" variant="subtle" fontSize="xs">
                        BETA
                    </Badge>
                </HStack>

                {/* Status & Actions */}
                <HStack spacing={4}>
                    {/* Current IST Time */}
                    <Tooltip label="Indian Standard Time" hasArrow>
                        <HStack spacing={1} color="gray.500" fontSize="sm">
                            <Icon as={FiClock} />
                            <Text fontFamily="mono">{currentTime} IST</Text>
                        </HStack>
                    </Tooltip>

                    {/* Market Status Badge */}
                    <Tooltip label={marketInfo.nextEvent} hasArrow placement="bottom">
                        <Badge
                            colorScheme={marketInfo.colorScheme}
                            variant="subtle"
                            px={3}
                            py={1}
                            borderRadius="full"
                            cursor="help"
                        >
                            <HStack spacing={2}>
                                <Box
                                    w={2}
                                    h={2}
                                    bg={marketInfo.pulseColor}
                                    borderRadius="full"
                                    animation={marketInfo.status === 'open' ? `${pulseAnimation} 2s infinite` : undefined}
                                />
                                <Text>{marketInfo.message}</Text>
                            </HStack>
                        </Badge>
                    </Tooltip>

                    <Button
                        size="sm"
                        variant="ghost"
                        leftIcon={isRefreshing ? <Spinner size="xs" /> : <FiRefreshCw />}
                        onClick={handleRefresh}
                        isDisabled={isRefreshing}
                    >
                        Refresh
                    </Button>

                    <Tooltip label={`Switch to ${colorMode === 'dark' ? 'light' : 'dark'} mode`} hasArrow>
                        <Button
                            size="sm"
                            variant="ghost"
                            onClick={toggleColorMode}
                            aria-label="Toggle color mode"
                        >
                            <Icon as={colorMode === 'dark' ? FiSun : FiMoon} />
                        </Button>
                    </Tooltip>
                </HStack>
            </HStack>
        </Box>
    )
}
