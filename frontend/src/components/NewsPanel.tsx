import { useState, useEffect, useMemo } from 'react'
import {
    Box,
    VStack,
    HStack,
    Text,
    useColorMode,
    Badge,
    Input,
    InputGroup,
    InputLeftElement,
    Tabs,
    TabList,
    Tab,
    TabPanels,
    TabPanel,
    Icon,
    Image,
    Skeleton,
    Link,
    Flex,
    IconButton,
    useToast,
} from '@chakra-ui/react'
import { FiSearch, FiClock, FiExternalLink, FiBookmark, FiTrendingUp } from 'react-icons/fi'

// Types
interface NewsArticle {
    id: string
    title: string
    summary: string
    source: string
    url: string
    imageUrl?: string
    publishedAt: string
    category: 'stocks' | 'crypto' | 'commodities' | 'general'
    sentiment: 'positive' | 'negative' | 'neutral'
    relatedSymbols?: string[]
}

// Demo news data
const DEMO_NEWS: NewsArticle[] = [
    {
        id: '1',
        title: 'Reliance Industries Reports Record Q3 Earnings, Beats Estimates',
        summary: 'Reliance Industries Ltd reported a 15% increase in consolidated net profit for Q3 FY26, exceeding analyst expectations on strong retail and telecom performance.',
        source: 'Economic Times',
        url: '#',
        publishedAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
        category: 'stocks',
        sentiment: 'positive',
        relatedSymbols: ['RELIANCE']
    },
    {
        id: '2',
        title: 'Bitcoin Surges Past $50,000 Amid ETF Inflows',
        summary: 'Bitcoin crossed the $50,000 mark for the first time in two years as spot ETF inflows continue to drive institutional demand.',
        source: 'CoinDesk',
        url: '#',
        publishedAt: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
        category: 'crypto',
        sentiment: 'positive'
    },
    {
        id: '3',
        title: 'RBI Keeps Repo Rate Unchanged at 6.5%',
        summary: 'The Reserve Bank of India maintained its key lending rate, citing persistent inflation concerns amid global economic uncertainty.',
        source: 'Mint',
        url: '#',
        publishedAt: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(),
        category: 'general',
        sentiment: 'neutral',
        relatedSymbols: ['HDFCBANK', 'ICICIBANK', 'SBIN']
    },
    {
        id: '4',
        title: 'TCS Wins $500M Deal from European Bank',
        summary: 'Tata Consultancy Services secured a major digital transformation contract, reinforcing its position in the BFSI vertical.',
        source: 'Business Standard',
        url: '#',
        publishedAt: new Date(Date.now() - 8 * 60 * 60 * 1000).toISOString(),
        category: 'stocks',
        sentiment: 'positive',
        relatedSymbols: ['TCS']
    },
    {
        id: '5',
        title: 'Gold Prices Hit All-Time High on Geopolitical Tensions',
        summary: 'Gold reached a new record high as investors flock to safe-haven assets amid rising geopolitical concerns.',
        source: 'Reuters',
        url: '#',
        publishedAt: new Date(Date.now() - 10 * 60 * 60 * 1000).toISOString(),
        category: 'commodities',
        sentiment: 'positive'
    },
    {
        id: '6',
        title: 'IT Sector Faces Headwinds as US Tech Spending Slows',
        summary: 'Indian IT companies may face near-term challenges as major US clients reduce technology budgets amid economic uncertainty.',
        source: 'Moneycontrol',
        url: '#',
        publishedAt: new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString(),
        category: 'stocks',
        sentiment: 'negative',
        relatedSymbols: ['TCS', 'INFY', 'WIPRO', 'HCLTECH']
    },
]

const SentimentBadge = ({ sentiment }: { sentiment: 'positive' | 'negative' | 'neutral' }) => {
    const colors = {
        positive: 'green',
        negative: 'red',
        neutral: 'gray'
    }
    return (
        <Badge colorScheme={colors[sentiment]} fontSize="xs" textTransform="capitalize">
            {sentiment}
        </Badge>
    )
}

const formatTimeAgo = (dateString: string): string => {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMins / 60)
    const diffDays = Math.floor(diffHours / 24)

    if (diffDays > 0) return `${diffDays}d ago`
    if (diffHours > 0) return `${diffHours}h ago`
    if (diffMins > 0) return `${diffMins}m ago`
    return 'Just now'
}

export default function NewsPanel() {
    const { colorMode } = useColorMode()
    const toast = useToast()
    const [news, setNews] = useState<NewsArticle[]>(DEMO_NEWS)
    const [searchQuery, setSearchQuery] = useState('')
    const [activeTab, setActiveTab] = useState(0)
    const [savedArticles, setSavedArticles] = useState<string[]>([])
    const [loading, setLoading] = useState(false)

    // Load saved articles
    useEffect(() => {
        const saved = localStorage.getItem('savedArticles')
        if (saved) {
            try {
                setSavedArticles(JSON.parse(saved))
            } catch { }
        }
    }, [])

    // Filter news based on tab and search
    const filteredNews = useMemo(() => {
        let filtered = news

        // Filter by category
        const categories = ['all', 'stocks', 'crypto', 'commodities']
        if (activeTab > 0 && activeTab < categories.length) {
            filtered = filtered.filter(n => n.category === categories[activeTab])
        }

        // Filter by search
        if (searchQuery) {
            const q = searchQuery.toLowerCase()
            filtered = filtered.filter(n =>
                n.title.toLowerCase().includes(q) ||
                n.summary.toLowerCase().includes(q) ||
                n.relatedSymbols?.some(s => s.toLowerCase().includes(q))
            )
        }

        return filtered
    }, [news, activeTab, searchQuery])

    const handleSaveArticle = (articleId: string) => {
        setSavedArticles(prev => {
            const updated = prev.includes(articleId)
                ? prev.filter(id => id !== articleId)
                : [...prev, articleId]
            localStorage.setItem('savedArticles', JSON.stringify(updated))
            toast({
                title: prev.includes(articleId) ? 'Removed from reading list' : 'Added to reading list',
                status: 'success',
                duration: 2000,
            })
            return updated
        })
    }

    const cardBg = colorMode === 'dark' ? 'gray.800' : 'white'
    const borderColor = colorMode === 'dark' ? 'gray.700' : 'gray.200'
    const hoverBg = colorMode === 'dark' ? 'gray.700' : 'gray.50'

    const NewsCard = ({ article }: { article: NewsArticle }) => (
        <Box
            p={4}
            borderRadius="lg"
            border="1px solid"
            borderColor={borderColor}
            _hover={{ bg: hoverBg }}
            transition="all 0.2s"
        >
            <Flex gap={4}>
                {article.imageUrl && (
                    <Image
                        src={article.imageUrl}
                        alt={article.title}
                        w="100px"
                        h="70px"
                        borderRadius="md"
                        objectFit="cover"
                        fallback={<Skeleton w="100px" h="70px" borderRadius="md" />}
                    />
                )}

                <VStack align="start" flex={1} spacing={2}>
                    <HStack justify="space-between" w="full">
                        <HStack spacing={2}>
                            <SentimentBadge sentiment={article.sentiment} />
                            <Badge colorScheme="blue" variant="subtle">{article.category}</Badge>
                        </HStack>
                        <HStack>
                            <IconButton
                                aria-label="Save"
                                icon={<FiBookmark fill={savedArticles.includes(article.id) ? 'currentColor' : 'none'} />}
                                size="sm"
                                variant="ghost"
                                colorScheme={savedArticles.includes(article.id) ? 'blue' : 'gray'}
                                onClick={() => handleSaveArticle(article.id)}
                            />
                            <Link href={article.url} isExternal>
                                <IconButton
                                    aria-label="Open"
                                    icon={<FiExternalLink />}
                                    size="sm"
                                    variant="ghost"
                                />
                            </Link>
                        </HStack>
                    </HStack>

                    <Text fontWeight="600" fontSize="sm" noOfLines={2}>
                        {article.title}
                    </Text>

                    <Text fontSize="xs" color="gray.500" noOfLines={2}>
                        {article.summary}
                    </Text>

                    <HStack spacing={4} fontSize="xs" color="gray.500">
                        <Text>{article.source}</Text>
                        <HStack>
                            <Icon as={FiClock} />
                            <Text>{formatTimeAgo(article.publishedAt)}</Text>
                        </HStack>
                    </HStack>

                    {article.relatedSymbols && article.relatedSymbols.length > 0 && (
                        <HStack spacing={1}>
                            <Icon as={FiTrendingUp} color="cyan.400" boxSize={3} />
                            {article.relatedSymbols.slice(0, 4).map(symbol => (
                                <Badge key={symbol} size="sm" colorScheme="cyan" variant="outline" fontSize="xs">
                                    {symbol}
                                </Badge>
                            ))}
                        </HStack>
                    )}
                </VStack>
            </Flex>
        </Box>
    )

    return (
        <VStack spacing={4} align="stretch">
            {/* Search */}
            <InputGroup>
                <InputLeftElement>
                    <Icon as={FiSearch} color="gray.400" />
                </InputLeftElement>
                <Input
                    placeholder="Search news..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    bg={cardBg}
                />
            </InputGroup>

            {/* Tabs */}
            <Box bg={cardBg} borderRadius="xl" border="1px solid" borderColor={borderColor} overflow="hidden">
                <Tabs index={activeTab} onChange={setActiveTab}>
                    <TabList>
                        <Tab>All</Tab>
                        <Tab>Stocks</Tab>
                        <Tab>Crypto</Tab>
                        <Tab>Commodities</Tab>
                    </TabList>

                    <TabPanels>
                        {[0, 1, 2, 3].map(idx => (
                            <TabPanel key={idx} p={4}>
                                <VStack spacing={3} align="stretch">
                                    {loading ? (
                                        Array(3).fill(0).map((_, i) => (
                                            <Skeleton key={i} h="120px" borderRadius="lg" />
                                        ))
                                    ) : filteredNews.length > 0 ? (
                                        filteredNews.map(article => (
                                            <NewsCard key={article.id} article={article} />
                                        ))
                                    ) : (
                                        <Box py={8} textAlign="center">
                                            <Text color="gray.500">No news found</Text>
                                        </Box>
                                    )}
                                </VStack>
                            </TabPanel>
                        ))}
                    </TabPanels>
                </Tabs>
            </Box>
        </VStack>
    )
}
