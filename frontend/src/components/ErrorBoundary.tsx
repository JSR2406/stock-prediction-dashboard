import { Component, ReactNode } from 'react'
import {
    Box,
    VStack,
    Text,
    Button,
    Icon,
    Heading,
    Code,
    Alert,
    AlertIcon,
    AlertTitle,
    AlertDescription,
} from '@chakra-ui/react'
import { FiAlertTriangle, FiRefreshCw, FiHome } from 'react-icons/fi'

interface ErrorBoundaryProps {
    children: ReactNode
    fallback?: ReactNode
}

interface ErrorBoundaryState {
    hasError: boolean
    error: Error | null
    errorInfo: React.ErrorInfo | null
}

/**
 * Error Boundary component to catch and display React errors gracefully.
 * Prevents the entire app from crashing on component errors.
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
    constructor(props: ErrorBoundaryProps) {
        super(props)
        this.state = {
            hasError: false,
            error: null,
            errorInfo: null
        }
    }

    static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
        return { hasError: true, error }
    }

    componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
        this.setState({ errorInfo })

        // Log error to console in development
        console.error('ErrorBoundary caught an error:', error, errorInfo)

        // In production, you would send this to an error tracking service like Sentry
        // Example:
        // Sentry.captureException(error, { extra: { componentStack: errorInfo.componentStack } })
    }

    handleReset = () => {
        this.setState({ hasError: false, error: null, errorInfo: null })
    }

    handleGoHome = () => {
        window.location.href = '/'
    }

    render() {
        if (this.state.hasError) {
            if (this.props.fallback) {
                return this.props.fallback
            }

            return (
                <ErrorFallback
                    error={this.state.error}
                    onReset={this.handleReset}
                    onGoHome={this.handleGoHome}
                />
            )
        }

        return this.props.children
    }
}

/**
 * Default error fallback UI component
 */
interface ErrorFallbackProps {
    error: Error | null
    onReset: () => void
    onGoHome: () => void
}

function ErrorFallback({ error, onReset, onGoHome }: ErrorFallbackProps) {
    return (
        <Box
            minH="100vh"
            display="flex"
            alignItems="center"
            justifyContent="center"
            p={8}
            bg="gray.900"
        >
            <VStack spacing={6} maxW="600px" textAlign="center">
                <Icon as={FiAlertTriangle} boxSize={16} color="red.400" />

                <Heading size="xl" color="white">
                    Oops! Something went wrong
                </Heading>

                <Text color="gray.400" fontSize="lg">
                    We're sorry, but something unexpected happened. Our team has been notified and is working on a fix.
                </Text>

                {error && import.meta.env.MODE === 'development' && (
                    <Alert status="error" borderRadius="lg" textAlign="left">
                        <AlertIcon />
                        <Box>
                            <AlertTitle>Error Details</AlertTitle>
                            <AlertDescription>
                                <Code colorScheme="red" p={2} borderRadius="md" display="block" whiteSpace="pre-wrap">
                                    {error.message}
                                </Code>
                            </AlertDescription>
                        </Box>
                    </Alert>
                )}

                <Box display="flex" gap={4}>
                    <Button
                        leftIcon={<FiRefreshCw />}
                        colorScheme="blue"
                        onClick={onReset}
                    >
                        Try Again
                    </Button>

                    <Button
                        leftIcon={<FiHome />}
                        variant="outline"
                        colorScheme="gray"
                        onClick={onGoHome}
                    >
                        Go Home
                    </Button>
                </Box>

                <Text fontSize="sm" color="gray.500">
                    If the problem persists, please contact support.
                </Text>
            </VStack>
        </Box>
    )
}

/**
 * HOC to wrap components with error boundary
 */
export function withErrorBoundary<P extends object>(
    Component: React.ComponentType<P>,
    fallback?: ReactNode
) {
    return function WithErrorBoundary(props: P) {
        return (
            <ErrorBoundary fallback={fallback}>
                <Component {...props} />
            </ErrorBoundary>
        )
    }
}

/**
 * Async Error Boundary for handling async errors
 */
interface AsyncErrorBoundaryProps {
    children: ReactNode
    onError?: (error: Error) => void
}

export function AsyncErrorBoundary({ children, onError }: AsyncErrorBoundaryProps) {
    // Use effect to catch unhandled promise rejections
    if (typeof window !== 'undefined') {
        window.addEventListener('unhandledrejection', (event) => {
            console.error('Unhandled promise rejection:', event.reason)
            onError?.(event.reason)
        })
    }

    return <ErrorBoundary>{children}</ErrorBoundary>
}

export default ErrorBoundary
