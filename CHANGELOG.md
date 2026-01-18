# Changelog

All notable changes to StockAI Dashboard will be documented in this file.

## [1.1.0] - 2026-01-18

### Added
- 🕐 **Dynamic Market Status** - Navbar now shows real-time market status (Open, Closed, Pre-Market, After Hours, Holiday) based on IST
- 📊 **Live Market Heatmap** - MarketHeatmap component now fetches real data from API with automatic 60-second refresh
- 🔌 **Enhanced WebSocket Hook** - New `useWebSocketEnhanced` hook with automatic reconnection, heartbeat, and subscription management
- 🏷️ **Live/Demo Indicators** - Visual badges showing whether data is live or demo mode
- 📅 **Market Holiday Calendar** - Indian market holidays for 2026 integrated into status detection
- ⏰ **IST Time Display** - Current Indian Standard Time shown in navbar
- 🔄 **Manual Refresh Controls** - Added refresh buttons with loading states to data components

### Improved
- 💡 Navbar now uses glassmorphism effect with improved contrast
- 🎯 Sector-wise stock categorization in heatmap with dynamic sector detection
- 📱 Better loading skeletons and error states for data components
- 🎨 Pulse animation for live market indicator

### Technical
- Added proper TypeScript types throughout components
- Improved error handling with fallback to demo data
- Auto-refresh intervals for real-time data updates

---

## [1.0.0] - 2026-01-17

### Added
- 🚀 Initial release of StockAI Dashboard
- 📊 Real-time stock price tracking for NSE/BSE
- 🤖 AI-powered price predictions using ensemble ML models
- 📈 Interactive candlestick charts with technical indicators
- 💼 Portfolio management with P&L tracking
- 🔥 Market heatmap with sector-wise performance
- 📰 Aggregated financial news with sentiment analysis
- ⚡ WebSocket real-time price updates
- 🔍 Global stock search with autocomplete
- 🌙 Dark/Light theme support
- 📱 Fully responsive design

### Features

#### Backend (FastAPI)
- RESTful API with OpenAPI documentation
- WebSocket support for real-time updates
- Rate limiting and caching
- PostgreSQL database integration
- Comprehensive error handling
- Structured logging

#### Frontend (React + TypeScript)
- Modern Chakra UI components
- Recharts for data visualization
- Custom hooks for data fetching
- LocalStorage persistence
- Error boundaries

#### ML Models
- LSTM neural network
- GRU neural network
- XGBoost
- Random Forest
- Ensemble prediction with weighted averaging

#### DevOps
- Docker and Docker Compose
- GitHub Actions CI/CD
- Kubernetes configurations
- Comprehensive testing

### Technical Specifications
- Python 3.11+
- Node.js 20+
- FastAPI 0.109
- React 18
- TensorFlow 2.15
- PostgreSQL 15
- Redis 7

---

## [0.1.0] - 2026-01-10

### Added
- Initial project structure
- Basic API endpoints
- Frontend scaffolding
- ML model architecture

---

## Future Roadmap

### [1.1.0] - Planned
- [ ] Multi-language support (Hindi)
- [ ] Push notifications
- [ ] Social trading features
- [ ] Options analysis
- [ ] Mobile app (React Native)

### [1.2.0] - Planned
- [ ] Advanced backtesting UI
- [ ] Portfolio optimization
- [ ] Custom alert rules
- [ ] API key authentication
- [ ] Premium features tier
