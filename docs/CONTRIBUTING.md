# Contributing to StockAI Dashboard

Thank you for your interest in contributing to StockAI Dashboard! This document provides guidelines and information for contributors.

## 🤝 Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment.

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+
- Git
- Docker (optional but recommended)

### Development Setup

1. **Fork the repository**
   ```bash
   git clone https://github.com/yourusername/stock-prediction-dashboard.git
   cd stock-prediction-dashboard
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   # source venv/bin/activate  # Linux/Mac
   pip install -r requirements.txt
   pip install pytest pytest-cov black flake8  # Dev dependencies
   ```

3. **Frontend Setup**
   ```bash
   cd ../frontend
   npm install
   ```

4. **Start Development Servers**
   ```bash
   # Terminal 1 - Backend
   cd backend
   uvicorn app.main:app --reload --port 8000

   # Terminal 2 - Frontend
   cd frontend
   npm run dev
   ```

## 📝 How to Contribute

### Reporting Bugs

1. Check if the issue already exists
2. Create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details

### Feature Requests

1. Open an issue with the `enhancement` label
2. Describe the feature and its use case
3. Discuss implementation approach

### Pull Requests

1. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow the coding style guidelines
   - Write tests for new features
   - Update documentation as needed

3. **Run tests**
   ```bash
   # Backend
   cd backend
   pytest tests/ -v

   # Frontend
   cd frontend
   npm test
   ```

4. **Commit with meaningful messages**
   ```bash
   git commit -m "feat: add new stock comparison feature"
   ```

5. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

## 📋 Coding Guidelines

### Python (Backend)

- Follow PEP 8 style guide
- Use type hints
- Write docstrings for public functions
- Keep functions focused and small

```python
def calculate_prediction(
    symbol: str,
    horizon: int = 7
) -> PredictionResult:
    """
    Calculate stock price prediction.
    
    Args:
        symbol: Stock ticker symbol
        horizon: Prediction horizon in days
        
    Returns:
        PredictionResult with predicted prices
    """
    ...
```

### TypeScript (Frontend)

- Use TypeScript for all new code
- Define interfaces for props and state
- Use functional components with hooks
- Keep components small and focused

```typescript
interface StockCardProps {
    symbol: string;
    onSelect?: (symbol: string) => void;
}

export default function StockCard({ symbol, onSelect }: StockCardProps) {
    ...
}
```

### Commit Messages

Follow conventional commits:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes
- `refactor:` - Code refactoring
- `test:` - Test changes
- `chore:` - Maintenance tasks

## 🧪 Testing Guidelines

### Backend Tests

```python
def test_get_stock_quote():
    """Test stock quote endpoint."""
    response = client.get("/api/v1/stocks/RELIANCE")
    assert response.status_code == 200
    assert response.json()["success"] is True
```

### Frontend Tests

```typescript
test('renders stock card', () => {
    render(<StockCard symbol="TCS" />);
    expect(screen.getByText('TCS')).toBeInTheDocument();
});
```

## 📁 Project Structure

```
stock-prediction-dashboard/
├── backend/
│   ├── app/
│   │   ├── routes/      # API endpoints
│   │   ├── services/    # Business logic
│   │   ├── models/      # Pydantic schemas
│   │   ├── database/    # SQLAlchemy models
│   │   └── utils/       # Utilities
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── hooks/       # Custom hooks
│   │   └── services/    # API clients
│   └── tests/
└── ml-models/           # ML training scripts
```

## 🎨 UI/UX Guidelines

- Use Chakra UI components
- Support dark and light themes
- Make components responsive
- Add loading states
- Handle errors gracefully

## 📚 Documentation

- Update README for significant changes
- Add JSDoc/docstrings for public APIs
- Include examples in documentation
- Keep changelog updated

## ❓ Questions?

- Open a discussion on GitHub
- Check existing documentation
- Review similar issues/PRs

Thank you for contributing! 🙏
