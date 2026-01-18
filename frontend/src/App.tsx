import { Box, Flex, useColorMode } from '@chakra-ui/react'
import Dashboard from './components/Dashboard'
import Navbar from './components/Navbar'

function App() {
    const { colorMode } = useColorMode()

    return (
        <Box
            minH="100vh"
            bg={colorMode === 'dark' ? 'gray.900' : 'gray.50'}
        >
            <Flex direction="column">
                <Navbar />
                <Dashboard />
            </Flex>
        </Box>
    )
}

export default App
