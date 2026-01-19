/**
 * Fundamental Analysis Component
 * Displays comprehensive financial data including income statement, balance sheet,
 * cash flow, ratios, and SEC filings.
 */

import React, { useState, useEffect } from 'react'
import {
    Box,
    VStack,
    HStack,
    Text,
    Tabs,
    TabList,
    TabPanels,
    Tab,
    TabPanel,
    SimpleGrid,
    Select,
    Skeleton,
    Alert,
    AlertIcon,
    AlertTitle,
    useColorMode,
    Badge,
    Table,
    Thead,
    Tbody,
    Tr,
    Th,
    Td,
    TableContainer,
    Divider,
    Button,
    Link,
    Tooltip,
    Icon
} from '@chakra-ui/react'
import {
    LineChart,
    Line,
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip as RechartsTooltip,
    Legend,
    ResponsiveContainer,
    ComposedChart
} from 'recharts'
import { FiExternalLink, FiFileText, FiTrendingUp, FiDollarSign, FiInfo } from 'react-icons/fi'
import financialApi, {
    IncomeStatement,
    BalanceSheet,
    CashFlowStatement,
    SECFiling,
    FinancialRatios
} from '../services/financialApi'

interface FundamentalAnalysisProps {
    symbol: string
}

const FundamentalAnalysis: React.FC<FundamentalAnalysisProps> = ({ symbol }) => {
    const { colorMode } = useColorMode()
    const [activeTab, setActiveTab] = useState(0)
    const [period, setPeriod] = useState('annual')
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    // Data states
    const [incomeData, setIncomeData] = useState<IncomeStatement[]>([])
    const [balanceData, setBalanceData] = useState<BalanceSheet[]>([])
    const [cashFlowData, setCashFlowData] = useState<CashFlowStatement[]>([])
    const [filings, setFilings] = useState<SECFiling[]>([])
    const [ratios, setRatios] = useState<FinancialRatios | null>(null)

    // Colors based on theme
    const textColor = colorMode === 'dark' ? 'gray.200' : 'gray.700'
    const subTextColor = colorMode === 'dark' ? 'gray.400' : 'gray.600'
    const cardBg = colorMode === 'dark' ? 'gray.800' : 'white'
    const borderColor = colorMode === 'dark' ? 'gray.700' : 'gray.200'

    // Chart colors
    const chartColors = {
        primary: '#3182CE',
        secondary: '#38A169',
        tertiary: '#D69E2E',
        quaternary: '#E53E3E',
        grid: colorMode === 'dark' ? '#2D3748' : '#E2E8F0',
        text: colorMode === 'dark' ? '#A0AEC0' : '#718096'
    }

    // Format large numbers
    const formatNumber = (num: number) => {
        if (!num) return '-'
        if (Math.abs(num) >= 1e9) {
            return (num / 1e9).toFixed(2) + 'B'
        }
        if (Math.abs(num) >= 1e6) {
            return (num / 1e6).toFixed(2) + 'M'
        }
        return num.toLocaleString()
    }

    const fetchData = async () => {
        setIsLoading(true)
        setError(null)
        try {
            // Concurrent fetching for better performance
            const [
                incomeRes,
                balanceRes,
                cashFlowRes,
                ratiosRes,
                filingsRes
            ] = await Promise.allSettled([
                financialApi.getIncomeStatements(symbol, period),
                financialApi.getBalanceSheets(symbol, period),
                financialApi.getCashFlows(symbol, period),
                financialApi.getRatios(symbol),
                financialApi.getFilings(symbol)
            ])

            // Process Income Statements
            if (incomeRes.status === 'fulfilled' && incomeRes.value.data.success) {
                // Reverse to have oldest first for charts
                setIncomeData([...incomeRes.value.data.data.income_statements].reverse())
            } else {
                console.error("Failed to fetch income statements")
            }

            // Process Balance Sheets
            if (balanceRes.status === 'fulfilled' && balanceRes.value.data.success) {
                setBalanceData([...balanceRes.value.data.data.balance_sheets].reverse())
            }

            // Process Cash Flows
            if (cashFlowRes.status === 'fulfilled' && cashFlowRes.value.data.success) {
                setCashFlowData([...cashFlowRes.value.data.data.cash_flow_statements].reverse())
            }

            // Process Ratios
            if (ratiosRes.status === 'fulfilled' && ratiosRes.value.data.success) {
                setRatios(ratiosRes.value.data.data)
            }

            // Process Filings
            if (filingsRes.status === 'fulfilled' && filingsRes.value.data.success) {
                setFilings(filingsRes.value.data.data.filings)
            }

        } catch (err) {
            console.error(err)
            setError(err instanceof Error ? err.message : 'Failed to fetch financial data')
        } finally {
            setIsLoading(false)
        }
    }

    useEffect(() => {
        if (symbol) {
            fetchData()
        }
    }, [symbol, period])

    // Render Logic
    if (!symbol) return null
    if (isLoading && incomeData.length === 0) {
        return (
            <VStack spacing={6} align="stretch" w="full">
                <HStack justify="space-between">
                    <Skeleton height="40px" width="200px" />
                    <Skeleton height="40px" width="120px" />
                </HStack>
                <SimpleGrid columns={{ base: 1, md: 3 }} spacing={6}>
                    <Skeleton height="150px" />
                    <Skeleton height="150px" />
                    <Skeleton height="150px" />
                </SimpleGrid>
                <Skeleton height="400px" />
            </VStack>
        )
    }

    return (
        <Box
            p={6}
            bg={cardBg}
            borderRadius="xl"
            border="1px solid"
            borderColor={borderColor}
            shadow="sm"
        >
            <HStack justify="space-between" mb={6} align="center">
                <HStack>
                    <Icon as={FiDollarSign} boxSize={6} color="blue.500" />
                    <Text fontSize="2xl" fontWeight="bold" color={textColor}>
                        Fundamental Analysis
                    </Text>
                    <Badge colorScheme="blue" variant="subtle">
                        {symbol.toUpperCase()}
                    </Badge>
                </HStack>

                <Select
                    width="150px"
                    value={period}
                    onChange={(e) => setPeriod(e.target.value)}
                    size="sm"
                    borderRadius="md"
                >
                    <option value="annual">Annual</option>
                    <option value="quarterly">Quarterly</option>
                    <option value="ttm">TTM</option>
                </Select>
            </HStack>

            {error && (
                <Alert status="error" variant="subtle" borderRadius="md" mb={6}>
                    <AlertIcon />
                    <AlertTitle>{error}</AlertTitle>
                </Alert>
            )}

            <Tabs
                variant="enclosed"
                colorScheme="blue"
                index={activeTab}
                onChange={setActiveTab}
                isLazy
            >
                <TabList mb={4} borderBottomColor={borderColor}>
                    <Tab fontWeight="600">Income</Tab>
                    <Tab fontWeight="600">Balance Sheet</Tab>
                    <Tab fontWeight="600">Cash Flow</Tab>
                    <Tab fontWeight="600">Ratios</Tab>
                    <Tab fontWeight="600">Filings</Tab>
                </TabList>

                <TabPanels>
                    {/* Income Statement Panel */}
                    <TabPanel px={0}>
                        <VStack spacing={8} align="stretch">
                            {/* Chart */}
                            <Box h="300px" w="full">
                                <ResponsiveContainer>
                                    <ComposedChart data={incomeData}>
                                        <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} />
                                        <XAxis
                                            dataKey="calendar_date"
                                            tickFormatter={(val) => val.substring(0, 4)}
                                            stroke={chartColors.text}
                                        />
                                        <YAxis
                                            tickFormatter={formatNumber}
                                            stroke={chartColors.text}
                                        />
                                        <RechartsTooltip
                                            contentStyle={{ backgroundColor: cardBg, borderColor: borderColor }}
                                            formatter={(value: any) => formatNumber(value)}
                                        />
                                        <Legend />
                                        <Bar dataKey="revenue" name="Revenue" fill={chartColors.primary} barSize={40} />
                                        <Line type="monotone" dataKey="net_income" name="Net Income" stroke={chartColors.secondary} strokeWidth={2} />
                                        <Line type="monotone" dataKey="operating_income" name="Op. Income" stroke={chartColors.tertiary} strokeWidth={2} />
                                    </ComposedChart>
                                </ResponsiveContainer>
                            </Box>

                            {/* Table */}
                            <TableContainer>
                                <Table size="sm" variant="simple">
                                    <Thead>
                                        <Tr>
                                            <Th color={subTextColor}>Period</Th>
                                            <Th isNumeric color={subTextColor}>Revenue</Th>
                                            <Th isNumeric color={subTextColor}>Gross Profit</Th>
                                            <Th isNumeric color={subTextColor}>Op. Income</Th>
                                            <Th isNumeric color={subTextColor}>Net Income</Th>
                                            <Th isNumeric color={subTextColor}>EPS</Th>
                                        </Tr>
                                    </Thead>
                                    <Tbody>
                                        {[...incomeData].reverse().map((item, idx) => (
                                            <Tr key={idx} _hover={{ bg: colorMode === 'dark' ? 'whiteAlpha.50' : 'gray.50' }}>
                                                <Td fontWeight="medium">{item.calendar_date}</Td>
                                                <Td isNumeric>{formatNumber(item.revenue)}</Td>
                                                <Td isNumeric>{formatNumber(item.gross_profit)}</Td>
                                                <Td isNumeric>{formatNumber(item.operating_income)}</Td>
                                                <Td isNumeric fontWeight="bold" color={item.net_income >= 0 ? 'green.400' : 'red.400'}>
                                                    {formatNumber(item.net_income)}
                                                </Td>
                                                <Td isNumeric>{item.eps_diluted?.toFixed(2)}</Td>
                                            </Tr>
                                        ))}
                                    </Tbody>
                                </Table>
                            </TableContainer>
                        </VStack>
                    </TabPanel>

                    {/* Balance Sheet Panel */}
                    <TabPanel px={0}>
                        <VStack spacing={8} align="stretch">
                            <Box h="300px" w="full">
                                <ResponsiveContainer>
                                    <BarChart data={balanceData}>
                                        <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} />
                                        <XAxis
                                            dataKey="calendar_date"
                                            tickFormatter={(val) => val.substring(0, 4)}
                                            stroke={chartColors.text}
                                        />
                                        <YAxis
                                            tickFormatter={formatNumber}
                                            stroke={chartColors.text}
                                        />
                                        <RechartsTooltip
                                            contentStyle={{ backgroundColor: cardBg, borderColor: borderColor }}
                                            formatter={(value: any) => formatNumber(value)}
                                        />
                                        <Legend />
                                        <Bar dataKey="total_assets" name="Total Assets" fill={chartColors.primary} stackId="a" />
                                        <Bar dataKey="total_liabilities" name="Total Liabilities" fill={chartColors.quaternary} stackId="b" />
                                        <Bar dataKey="stockholders_equity" name="Equity" fill={chartColors.secondary} stackId="b" />
                                    </BarChart>
                                </ResponsiveContainer>
                            </Box>

                            <TableContainer>
                                <Table size="sm" variant="simple">
                                    <Thead>
                                        <Tr>
                                            <Th color={subTextColor}>Period</Th>
                                            <Th isNumeric color={subTextColor}>Total Assets</Th>
                                            <Th isNumeric color={subTextColor}>Total Liabilities</Th>
                                            <Th isNumeric color={subTextColor}>Equity</Th>
                                            <Th isNumeric color={subTextColor}>Debt</Th>
                                            <Th isNumeric color={subTextColor}>Cash</Th>
                                        </Tr>
                                    </Thead>
                                    <Tbody>
                                        {[...balanceData].reverse().map((item, idx) => (
                                            <Tr key={idx} _hover={{ bg: colorMode === 'dark' ? 'whiteAlpha.50' : 'gray.50' }}>
                                                <Td fontWeight="medium">{item.calendar_date}</Td>
                                                <Td isNumeric>{formatNumber(item.total_assets)}</Td>
                                                <Td isNumeric>{formatNumber(item.total_liabilities)}</Td>
                                                <Td isNumeric>{formatNumber(item.stockholders_equity)}</Td>
                                                <Td isNumeric>{formatNumber(item.total_debt)}</Td>
                                                <Td isNumeric>{formatNumber(item.cash_and_equivalents)}</Td>
                                            </Tr>
                                        ))}
                                    </Tbody>
                                </Table>
                            </TableContainer>
                        </VStack>
                    </TabPanel>

                    {/* Cash Flow Panel */}
                    <TabPanel px={0}>
                        <VStack spacing={8} align="stretch">
                            <Box h="300px" w="full">
                                <ResponsiveContainer>
                                    <BarChart data={cashFlowData}>
                                        <CartesianGrid strokeDasharray="3 3" stroke={chartColors.grid} />
                                        <XAxis
                                            dataKey="calendar_date"
                                            tickFormatter={(val) => val.substring(0, 4)}
                                            stroke={chartColors.text}
                                        />
                                        <YAxis
                                            tickFormatter={formatNumber}
                                            stroke={chartColors.text}
                                        />
                                        <RechartsTooltip
                                            contentStyle={{ backgroundColor: cardBg, borderColor: borderColor }}
                                            formatter={(value: any) => formatNumber(value)}
                                        />
                                        <Legend />
                                        <Bar dataKey="net_cash_flow_from_operations" name="Operating" fill={chartColors.primary} />
                                        <Bar dataKey="net_cash_flow_from_investing" name="Investing" fill={chartColors.tertiary} />
                                        <Bar dataKey="net_cash_flow_from_financing" name="Financing" fill={chartColors.secondary} />
                                        <Bar dataKey="free_cash_flow" name="Free Cash Flow" fill={chartColors.quaternary} />
                                    </BarChart>
                                </ResponsiveContainer>
                            </Box>

                            <TableContainer>
                                <Table size="sm" variant="simple">
                                    <Thead>
                                        <Tr>
                                            <Th color={subTextColor}>Period</Th>
                                            <Th isNumeric color={subTextColor}>Operating</Th>
                                            <Th isNumeric color={subTextColor}>Investing</Th>
                                            <Th isNumeric color={subTextColor}>Financing</Th>
                                            <Th isNumeric color={subTextColor}>Free Cash Flow</Th>
                                        </Tr>
                                    </Thead>
                                    <Tbody>
                                        {[...cashFlowData].reverse().map((item, idx) => (
                                            <Tr key={idx} _hover={{ bg: colorMode === 'dark' ? 'whiteAlpha.50' : 'gray.50' }}>
                                                <Td fontWeight="medium">{item.calendar_date}</Td>
                                                <Td isNumeric color={item.net_cash_flow_from_operations >= 0 ? 'green.400' : 'red.400'}>
                                                    {formatNumber(item.net_cash_flow_from_operations)}
                                                </Td>
                                                <Td isNumeric>{formatNumber(item.net_cash_flow_from_investing)}</Td>
                                                <Td isNumeric>{formatNumber(item.net_cash_flow_from_financing)}</Td>
                                                <Td isNumeric fontWeight="bold">{formatNumber(item.free_cash_flow)}</Td>
                                            </Tr>
                                        ))}
                                    </Tbody>
                                </Table>
                            </TableContainer>
                        </VStack>
                    </TabPanel>

                    {/* Ratios Panel */}
                    <TabPanel px={0}>
                        <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={6}>
                            {ratios?.ratios ? Object.entries(ratios.ratios).map(([key, value]) => (
                                <Box
                                    key={key}
                                    p={4}
                                    borderRadius="lg"
                                    bg={colorMode === 'dark' ? 'whiteAlpha.50' : 'gray.50'}
                                    border="1px solid"
                                    borderColor={borderColor}
                                >
                                    <Text fontSize="sm" color={subTextColor} fontWeight="medium" textTransform="uppercase">
                                        {key.replace(/_/g, ' ')}
                                    </Text>
                                    <Text fontSize="2xl" fontWeight="bold" mt={1}>
                                        {typeof value === 'number' ? value.toFixed(2) : '-'}
                                        {['margin', 'roe', 'roa'].some(k => key.includes(k)) ? '%' : ''}
                                    </Text>
                                    <Tooltip label="Industry average comparison unavailable">
                                        <HStack mt={2} fontSize="xs" color="gray.500">
                                            <Icon as={FiInfo} />
                                            <Text>Vs Industry: N/A</Text>
                                        </HStack>
                                    </Tooltip>
                                </Box>
                            )) : (
                                <Text>No ratio data available.</Text>
                            )}
                        </SimpleGrid>
                    </TabPanel>

                    {/* Filings Panel */}
                    <TabPanel px={0}>
                        <VStack spacing={3} align="stretch" divider={<Divider />}>
                            {filings.length > 0 ? filings.map((filing, idx) => (
                                <HStack key={idx} justify="space-between" p={2} _hover={{ bg: colorMode === 'dark' ? 'whiteAlpha.50' : 'gray.50' }} borderRadius="md">
                                    <HStack spacing={4}>
                                        <Icon as={FiFileText} color="blue.400" boxSize={5} />
                                        <VStack align="start" spacing={0}>
                                            <Text fontWeight="bold">{filing.form_type}</Text>
                                            <Text fontSize="xs" color={subTextColor}>{filing.filing_date}</Text>
                                        </VStack>
                                    </HStack>
                                    <Button
                                        as={Link}
                                        href={filing.filing_url}
                                        isExternal
                                        size="xs"
                                        variant="outline"
                                        rightIcon={<FiExternalLink />}
                                    >
                                        View
                                    </Button>
                                </HStack>
                            )) : (
                                <Text>No SEC filings found.</Text>
                            )}
                        </VStack>
                    </TabPanel>
                </TabPanels>
            </Tabs>
        </Box>
    )
}

export default FundamentalAnalysis
