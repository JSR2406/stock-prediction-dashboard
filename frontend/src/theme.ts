import { extendTheme, type ThemeConfig } from '@chakra-ui/react'

const config: ThemeConfig = {
    initialColorMode: 'dark',
    useSystemColorMode: false,
}

const theme = extendTheme({
    config,
    fonts: {
        heading: `'Inter', sans-serif`,
        body: `'Inter', sans-serif`,
    },
    colors: {
        brand: {
            50: '#E6FFFA',
            100: '#B2F5EA',
            200: '#81E6D9',
            300: '#4FD1C5',
            400: '#38B2AC',
            500: '#319795',
            600: '#2C7A7B',
            700: '#285E61',
            800: '#234E52',
            900: '#1D4044',
        },
        profit: {
            light: '#48BB78',
            dark: '#68D391',
            bg: 'rgba(72, 187, 120, 0.1)',
        },
        loss: {
            light: '#F56565',
            dark: '#FC8181',
            bg: 'rgba(245, 101, 101, 0.1)',
        },
        glass: {
            bg: 'rgba(26, 32, 44, 0.8)',
            border: 'rgba(255, 255, 255, 0.1)',
        },
    },
    styles: {
        global: (props: { colorMode: string }) => ({
            body: {
                bg: props.colorMode === 'dark' ? 'gray.900' : 'gray.50',
                color: props.colorMode === 'dark' ? 'white' : 'gray.800',
            },
        }),
    },
    components: {
        Card: {
            baseStyle: (props: { colorMode: string }) => ({
                container: {
                    bg: props.colorMode === 'dark' ? 'gray.800' : 'white',
                    borderRadius: 'xl',
                    boxShadow: 'xl',
                    border: '1px solid',
                    borderColor: props.colorMode === 'dark' ? 'gray.700' : 'gray.200',
                    overflow: 'hidden',
                    transition: 'all 0.3s ease',
                    _hover: {
                        transform: 'translateY(-2px)',
                        boxShadow: '2xl',
                    },
                },
            }),
        },
        Button: {
            baseStyle: {
                fontWeight: 'semibold',
                borderRadius: 'lg',
            },
            variants: {
                glass: (props: { colorMode: string }) => ({
                    bg: props.colorMode === 'dark' ? 'whiteAlpha.100' : 'blackAlpha.50',
                    backdropFilter: 'blur(10px)',
                    _hover: {
                        bg: props.colorMode === 'dark' ? 'whiteAlpha.200' : 'blackAlpha.100',
                    },
                }),
            },
        },
        Stat: {
            baseStyle: {
                container: {
                    p: 4,
                    borderRadius: 'lg',
                },
            },
        },
    },
})

export default theme
