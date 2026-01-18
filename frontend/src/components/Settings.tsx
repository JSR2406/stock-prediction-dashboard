import { useState, useEffect } from 'react'
import {
    Box,
    VStack,
    HStack,
    Text,
    Switch,
    Select,
    Button,
    useColorMode,
    Divider,
    Icon,
    Badge,
    Slider,
    SliderTrack,
    SliderFilledTrack,
    SliderThumb,
    FormControl,
    FormLabel,
    useToast,
    Flex,
} from '@chakra-ui/react'
import {
    FiMoon,
    FiSun,
    FiBell,
    FiGlobe,
    FiDownload,
    FiRefreshCw,
    FiTrash2,
    FiCheck,
} from 'react-icons/fi'

interface SettingsState {
    theme: 'light' | 'dark' | 'system'
    refreshInterval: number
    notifications: {
        priceAlerts: boolean
        predictions: boolean
        marketOpen: boolean
    }
    defaultChart: 'line' | 'candlestick' | 'area'
    language: 'en' | 'hi'
}

const DEFAULT_SETTINGS: SettingsState = {
    theme: 'dark',
    refreshInterval: 30,
    notifications: {
        priceAlerts: true,
        predictions: true,
        marketOpen: false
    },
    defaultChart: 'candlestick',
    language: 'en'
}

export default function Settings() {
    const { colorMode, setColorMode } = useColorMode()
    const toast = useToast()
    const [settings, setSettings] = useState<SettingsState>(DEFAULT_SETTINGS)
    const [hasChanges, setHasChanges] = useState(false)

    // Load settings from localStorage
    useEffect(() => {
        const saved = localStorage.getItem('appSettings')
        if (saved) {
            try {
                setSettings(JSON.parse(saved))
            } catch { }
        }
    }, [])

    // Save settings
    const saveSettings = () => {
        localStorage.setItem('appSettings', JSON.stringify(settings))

        // Apply theme
        if (settings.theme !== 'system') {
            setColorMode(settings.theme)
        }

        setHasChanges(false)

        toast({
            title: 'Settings saved',
            status: 'success',
            duration: 2000,
            isClosable: true,
        })
    }

    // Update setting
    const updateSetting = <K extends keyof SettingsState>(key: K, value: SettingsState[K]) => {
        setSettings(prev => ({ ...prev, [key]: value }))
        setHasChanges(true)
    }

    // Update nested notification setting
    const updateNotification = (key: keyof SettingsState['notifications'], value: boolean) => {
        setSettings(prev => ({
            ...prev,
            notifications: { ...prev.notifications, [key]: value }
        }))
        setHasChanges(true)
    }

    // Export user data
    const exportData = () => {
        const data = {
            settings,
            watchlist: JSON.parse(localStorage.getItem('watchlist') || '[]'),
            portfolio: JSON.parse(localStorage.getItem('portfolio') || '[]'),
            recentSearches: JSON.parse(localStorage.getItem('recentSearches') || '[]'),
            exportedAt: new Date().toISOString()
        }

        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `stockai-data-${new Date().toISOString().split('T')[0]}.json`
        a.click()
        URL.revokeObjectURL(url)

        toast({
            title: 'Data exported',
            description: 'Your data has been downloaded',
            status: 'success',
            duration: 3000,
        })
    }

    // Clear all data
    const clearAllData = () => {
        if (window.confirm('Are you sure? This will delete all your saved data including watchlist and portfolio.')) {
            localStorage.clear()
            setSettings(DEFAULT_SETTINGS)

            toast({
                title: 'Data cleared',
                description: 'All saved data has been deleted',
                status: 'info',
                duration: 3000,
            })
        }
    }

    const cardBg = colorMode === 'dark' ? 'gray.800' : 'white'
    const borderColor = colorMode === 'dark' ? 'gray.700' : 'gray.200'

    const SettingSection = ({ title, children }: { title: string, children: React.ReactNode }) => (
        <Box bg={cardBg} p={5} borderRadius="xl" border="1px solid" borderColor={borderColor}>
            <Text fontWeight="700" mb={4} fontSize="lg">{title}</Text>
            <VStack spacing={4} align="stretch">
                {children}
            </VStack>
        </Box>
    )

    const SettingRow = ({
        icon,
        title,
        description,
        children
    }: {
        icon: any
        title: string
        description?: string
        children: React.ReactNode
    }) => (
        <Flex justify="space-between" align="center" gap={4}>
            <HStack spacing={3}>
                <Icon as={icon} color="blue.400" boxSize={5} />
                <Box>
                    <Text fontWeight="500">{title}</Text>
                    {description && <Text fontSize="sm" color="gray.500">{description}</Text>}
                </Box>
            </HStack>
            {children}
        </Flex>
    )

    return (
        <VStack spacing={6} align="stretch">
            {/* Header */}
            <Flex justify="space-between" align="center">
                <Text fontSize="2xl" fontWeight="800">Settings</Text>
                {hasChanges && (
                    <Button
                        colorScheme="blue"
                        leftIcon={<FiCheck />}
                        onClick={saveSettings}
                    >
                        Save Changes
                    </Button>
                )}
            </Flex>

            {/* Appearance */}
            <SettingSection title="🎨 Appearance">
                <SettingRow icon={colorMode === 'dark' ? FiMoon : FiSun} title="Theme" description="Choose your preferred color theme">
                    <Select
                        value={settings.theme}
                        onChange={(e) => updateSetting('theme', e.target.value as any)}
                        w="150px"
                    >
                        <option value="light">Light</option>
                        <option value="dark">Dark</option>
                        <option value="system">System</option>
                    </Select>
                </SettingRow>

                <SettingRow icon={FiGlobe} title="Language" description="Select your preferred language">
                    <Select
                        value={settings.language}
                        onChange={(e) => updateSetting('language', e.target.value as any)}
                        w="150px"
                    >
                        <option value="en">English</option>
                        <option value="hi">हिंदी (Hindi)</option>
                    </Select>
                </SettingRow>
            </SettingSection>

            {/* Data Refresh */}
            <SettingSection title="🔄 Data Refresh">
                <SettingRow icon={FiRefreshCw} title="Auto Refresh Interval" description={`Every ${settings.refreshInterval} seconds`}>
                    <Box w="200px">
                        <Slider
                            value={settings.refreshInterval}
                            onChange={(val) => updateSetting('refreshInterval', val)}
                            min={10}
                            max={120}
                            step={10}
                        >
                            <SliderTrack>
                                <SliderFilledTrack bg="blue.400" />
                            </SliderTrack>
                            <SliderThumb boxSize={5} />
                        </Slider>
                    </Box>
                </SettingRow>

                <FormControl>
                    <FormLabel>Default Chart Type</FormLabel>
                    <Select
                        value={settings.defaultChart}
                        onChange={(e) => updateSetting('defaultChart', e.target.value as any)}
                    >
                        <option value="line">Line Chart</option>
                        <option value="candlestick">Candlestick</option>
                        <option value="area">Area Chart</option>
                    </Select>
                </FormControl>
            </SettingSection>

            {/* Notifications */}
            <SettingSection title="🔔 Notifications">
                <SettingRow icon={FiBell} title="Price Alerts" description="Get notified when stocks hit your target price">
                    <Switch
                        isChecked={settings.notifications.priceAlerts}
                        onChange={(e) => updateNotification('priceAlerts', e.target.checked)}
                        colorScheme="blue"
                    />
                </SettingRow>

                <SettingRow icon={FiBell} title="Prediction Updates" description="Notify when new predictions are available">
                    <Switch
                        isChecked={settings.notifications.predictions}
                        onChange={(e) => updateNotification('predictions', e.target.checked)}
                        colorScheme="blue"
                    />
                </SettingRow>

                <SettingRow icon={FiBell} title="Market Open/Close" description="Alert when market opens or closes">
                    <Switch
                        isChecked={settings.notifications.marketOpen}
                        onChange={(e) => updateNotification('marketOpen', e.target.checked)}
                        colorScheme="blue"
                    />
                </SettingRow>
            </SettingSection>

            {/* Data Management */}
            <SettingSection title="💾 Data Management">
                <HStack spacing={4}>
                    <Button
                        leftIcon={<FiDownload />}
                        variant="outline"
                        onClick={exportData}
                    >
                        Export All Data
                    </Button>
                    <Button
                        leftIcon={<FiTrash2 />}
                        colorScheme="red"
                        variant="outline"
                        onClick={clearAllData}
                    >
                        Clear All Data
                    </Button>
                </HStack>

                <Text fontSize="sm" color="gray.500">
                    Your data is stored locally in your browser and is never sent to any server.
                </Text>
            </SettingSection>

            {/* About */}
            <SettingSection title="ℹ️ About">
                <HStack justify="space-between">
                    <Text>Version</Text>
                    <Badge colorScheme="blue">v1.0.0</Badge>
                </HStack>
                <HStack justify="space-between">
                    <Text>Last Updated</Text>
                    <Text color="gray.500">January 2026</Text>
                </HStack>
                <Divider />
                <Text fontSize="sm" color="gray.500">
                    StockAI is an AI-powered stock prediction dashboard for educational purposes only.
                    Not financial advice.
                </Text>
            </SettingSection>
        </VStack>
    )
}
