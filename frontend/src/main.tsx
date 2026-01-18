import React from 'react'
import ReactDOM from 'react-dom/client'
import { ChakraProvider } from '@chakra-ui/react'
import theme from './theme'
import App from './App'
import { WebSocketProvider } from './contexts/WebSocketContext'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
        <ChakraProvider theme={theme}>
            <WebSocketProvider>
                <App />
            </WebSocketProvider>
        </ChakraProvider>
    </React.StrictMode>
)
