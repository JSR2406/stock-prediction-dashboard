# 🚀 StockAI - Stock Prediction Dashboard

<div align="center">

![StockAI Banner](https://img.shields.io/badge/StockAI-v1.0.0-blue?style=for-the-badge&logo=chart-line)

**AI-powered stock market prediction dashboard for Indian markets (NSE/BSE)**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg?logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg?logo=react)](https://reactjs.org/)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-2.15+-orange.svg?logo=tensorflow)](https://www.tensorflow.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[Features](#-features) • [Demo](#-demo) • [Installation](#-installation) • [API Docs](#-api-documentation) • [Contributing](#-contributing)

</div>

---

## ✨ Features

### 📊 **Real-time Market Data**
- Live stock prices from NSE/BSE
- Cryptocurrency tracking (BTC, ETH, 50+ coins)
- Commodities (Gold, Silver, Crude Oil)
- WebSocket-powered real-time updates

### 🤖 **AI-Powered Predictions**
- **Ensemble ML Models**: LSTM + GRU + XGBoost + Random Forest
- 7-day price forecasts with confidence intervals
- Technical indicator analysis (RSI, MACD, Bollinger Bands)
- Automated signal generation (Buy/Sell/Hold)

### 📈 **Advanced Charting**
- Interactive candlestick charts
- Technical indicator overlays
- Multi-timeframe analysis (1D to 5Y)
- Compare up to 4 stocks simultaneously

### 💼 **Portfolio Management**
- Track your holdings and P&L
- Sector allocation visualization
- Predicted portfolio value
- LocalStorage persistence

### 🔔 **Smart Alerts**
- Price movement notifications
- Prediction accuracy tracking
- Market status updates

---

## 🎬 Demo

<div align="center">
<img src="docs/screenshots/dashboard.png" alt="Dashboard Preview" width="800"/>
</div>

### Dashboard Features:
- 📱 Fully responsive design (mobile-friendly)
- 🌙 Dark/Light theme toggle
- ⚡ Real-time price updates
- 📊 Live prediction charts

---

## 🛠️ Tech Stack

### Backend
| Technology | Purpose |
|------------|---------|
| ![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white) | REST API Framework |
| ![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white) | Core Language |
| ![TensorFlow](https://img.shields.io/badge/TensorFlow-FF6F00?logo=tensorflow&logoColor=white) | Deep Learning |
| ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?logo=postgresql&logoColor=white) | Database |
| ![Redis](https://img.shields.io/badge/Redis-DC382D?logo=redis&logoColor=white) | Caching |

### Frontend
| Technology | Purpose |
|------------|---------|
| ![React](https://img.shields.io/badge/React-20232A?logo=react&logoColor=61DAFB) | UI Framework |
| ![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?logo=typescript&logoColor=white) | Type Safety |
| ![Chakra UI](https://img.shields.io/badge/Chakra_UI-319795?logo=chakraui&logoColor=white) | Component Library |
| ![Recharts](https://img.shields.io/badge/Recharts-FF6384?logo=chart.js&logoColor=white) | Data Visualization |
| ![Vite](https://img.shields.io/badge/Vite-646CFF?logo=vite&logoColor=white) | Build Tool |

---

## 📦 Installation

### Prerequisites
- **Node.js** 18+ and npm
- **Python** 3.11+
- **Docker** (optional, for containerized deployment)

### Quick Start (Development)

```bash
# Clone the repository
git clone https://github.com/yourusername/stock-prediction-dashboard.git
cd stock-prediction-dashboard

# Backend setup
cd backend
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# Start backend (Terminal 1)
uvicorn app.main:app --reload --port 8000

# Frontend setup (Terminal 2)
cd ../frontend
npm install
npm run dev
```

### Docker Deployment

```bash
# Build and run all services
docker-compose up --build

# Access the application
# Frontend: http://localhost:80
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/api/v1/docs
```

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the `backend` directory:

```env
# Application
ENVIRONMENT=development
DEBUG=true

# API Keys (Optional - get free keys from these services)
METALS_API_KEY=your_metals_api_key      # metals-api.com
ALPHA_VANTAGE_KEY=your_alpha_key        # alphavantage.co
COINGECKO_API_KEY=your_coingecko_key    # coingecko.com

# Database (for production)
DATABASE_URL=postgresql://user:pass@localhost:5432/stockai

# Redis (for caching)
REDIS_URL=redis://localhost:6379/0
```

---

## 📚 API Documentation

### Interactive Docs
- **Swagger UI**: `http://localhost:8000/api/v1/docs`
- **ReDoc**: `http://localhost:8000/api/v1/redoc`

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/stocks/{symbol}` | GET | Get stock quote |
| `/api/v1/stocks/{symbol}/historical` | GET | Get historical data |
| `/api/v1/predictions` | POST | Get price prediction |
| `/api/v1/analysis/{symbol}/technical` | GET | Technical indicators |
| `/api/v1/analysis/{symbol}/signals` | GET | Trading signals |
| `/ws/stocks` | WebSocket | Real-time price stream |

### Example Request

```bash
# Get stock prediction
curl -X POST "http://localhost:8000/api/v1/predictions" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "RELIANCE", "horizon": "7d"}'
```

---

## 📁 Project Structure

```
stock-prediction-dashboard/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── config.py            # Settings management
│   │   ├── routes/              # API endpoints
│   │   ├── services/            # Business logic
│   │   ├── models/              # Pydantic schemas
│   │   └── utils/               # Utilities
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/          # React components
│   │   ├── hooks/               # Custom hooks
│   │   ├── services/            # API clients
│   │   └── App.tsx              # Main component
│   ├── package.json
│   └── Dockerfile
├── ml-models/
│   ├── ensemble_model.py        # ML ensemble
│   ├── train_all_models.py      # Training script
│   └── backtesting.py           # Backtesting
├── docker-compose.yml
└── README.md
```

---

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest tests/ -v --cov=app

# Frontend tests
cd frontend
npm test

# Load testing (Locust)
cd backend
locust -f tests/locustfile.py
```

---

## 📈 Model Training

Train prediction models for your stocks:

```bash
cd ml-models

# Train all models for top 50 NSE stocks
python train_all_models.py --epochs 100

# Train specific stocks
python train_all_models.py --stocks RELIANCE TCS INFY

# Quick training mode
python train_all_models.py --quick --limit 10
```

---

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](docs/CONTRIBUTING.md)

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## ⚠️ Disclaimer

> **This application is for educational and informational purposes only.**
> 
> - Stock predictions are based on historical data and machine learning models
> - Past performance does not guarantee future results
> - This is NOT financial advice - always do your own research
> - The developers are not responsible for any financial losses

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- [Yahoo Finance](https://finance.yahoo.com/) for market data
- [CoinGecko](https://www.coingecko.com/) for crypto data
- [NSE India](https://www.nseindia.com/) for Indian market information
- [Metals-API](https://www.metals-api.com/) for commodity prices

---

<div align="center">

**Made with ❤️ for the Indian Stock Market**

⭐ Star this repo if you find it helpful!

</div>
