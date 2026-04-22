# CrossFlow AI - Cross-Chain DeFi Trading Platform

A full-stack AI-powered DeFi trading platform that enables seamless token swaps and cross-chain bridging with real-time portfolio tracking and analytics.

## 🚀 Features

### Core Trading Features
- **Multi-Chain Wallet Support** - MetaMask, WalletConnect, Phantom integration
- **DEX Aggregation** - Best prices via 1inch API across multiple chains
- **Cross-Chain Bridging** - Asset transfers using LI.FI protocol
- **Real-Time Portfolio Tracking** - Live balance and P&L monitoring
- **Gas Optimization** - Smart gas estimation and slippage protection

### Supported Networks
- Ethereum (ETH)
- Polygon (MATIC)
- Arbitrum (ETH)
- Optimism (ETH)
- Binance Smart Chain (BNB)

### Web3 Infrastructure
- **Wallet Connectors**: MetaMask, WalletConnect, Injected wallets
- **DEX Aggregators**: 1inch API for optimal swap routes
- **Cross-Chain Bridges**: LI.FI for secure asset bridging
- **RPC Providers**: Alchemy for reliable blockchain connectivity
- **Price Feeds**: CoinGecko API for real-time token prices

## 🛠 Tech Stack

### Backend
- **FastAPI** - High-performance Python web framework
- **SQLAlchemy** - Database ORM with PostgreSQL
- **Web3.py** - Ethereum blockchain interaction
- **Pydantic** - Data validation and serialization
- **Alembic** - Database migrations

### Frontend
- **React 18** - Modern UI framework
- **Wagmi** - React hooks for Ethereum
- **Viem** - TypeScript Ethereum library
- **TanStack Query** - Data fetching and caching
- **Zustand** - State management
- **Tailwind CSS** - Utility-first styling

### Infrastructure
- **PostgreSQL** - Primary database
- **Redis** - Caching and session storage (optional)
- **Docker** - Containerization support

## 🚀 Quick Start

### Automated Setup
```bash
# Clone and setup everything
./setup.sh

# Start the platform
./run.sh
```

### Manual Setup

#### 1. Prerequisites
- Python 3.8+
- Node.js 16+
- PostgreSQL 13+
- Git

#### 2. Database Setup
```bash
# Create database
createdb ai_trading_platform

# Or using psql
psql -U postgres
CREATE DATABASE ai_trading_platform;
CREATE USER trading_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE ai_trading_platform TO trading_user;
```

#### 3. Backend Setup
```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your configuration

# Start server
python -m src.main
```

#### 4. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Setup environment
cp .env.example .env
# Edit .env with your API keys

# Start development server
npm run dev
```

## 🔑 Required API Keys

### Essential (Free)
- **Alchemy** - Blockchain RPC access
  - Get at: https://www.alchemy.com/
  - Used for: Ethereum, Polygon, Arbitrum, Optimism RPCs

- **CoinGecko** - Token price data
  - Get at: https://www.coingecko.com/en/api
  - Used for: Real-time token prices and market data

### Optional (Enhanced Features)
- **1inch API** - DEX aggregation
  - Get at: https://portal.1inch.dev/
  - Used for: Optimal swap routes and pricing

- **LI.FI API** - Cross-chain bridging
  - Get at: https://docs.li.fi/
  - Used for: Cross-chain asset transfers

## 📁 Project Structure

```
crossflow-ai/
├── backend/                 # FastAPI backend
│   ├── src/
│   │   ├── api/            # API routes
│   │   ├── config/         # Configuration
│   │   ├── core/           # Core schemas
│   │   ├── models/         # Database models
│   │   └── services/       # Business logic
│   ├── requirements.txt    # Python dependencies
│   └── .env.example       # Environment template
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── config/         # Configuration
│   │   ├── pages/          # Page components
│   │   └── stores/         # State management
│   ├── package.json       # Node dependencies
│   └── .env.example       # Environment template
├── run.sh                 # Development runner
└── setup.sh              # Initial setup script
```

## 🌐 API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get user profile

### Trading
- `GET /api/trading/tokens/{chain_id}` - Get supported tokens
- `POST /api/trading/swap/quote` - Get swap quote
- `POST /api/trading/swap/transaction` - Get swap transaction data
- `POST /api/trading/bridge/quote` - Get bridge quote

### Portfolio
- `GET /api/portfolio/summary` - Portfolio overview
- `GET /api/portfolio/balance/{chain_id}` - Chain-specific balance
- `GET /api/portfolio/transactions` - Transaction history

### Admin
- `GET /api/admin/stats` - Platform statistics
- `GET /api/admin/users` - User management
- `GET /api/admin/analytics/volume` - Volume analytics

## 🔧 Configuration

### Backend Environment (.env)
```bash
# Database
DATABASE_URL=postgresql://trading_user:password@localhost/ai_trading_platform

# Security
SECRET_KEY=your-super-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Blockchain RPCs
ETHEREUM_RPC=https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY
POLYGON_RPC=https://polygon-mainnet.g.alchemy.com/v2/YOUR_KEY

# API Keys
COINGECKO_API_KEY=your-coingecko-key
ONEINCH_API_KEY=your-1inch-key
LIFI_API_KEY=your-lifi-key
```

### Frontend Environment (.env)
```bash
# API Configuration
VITE_API_BASE_URL=http://localhost:8000

# Blockchain
VITE_ALCHEMY_API_KEY=your-alchemy-key
VITE_WALLETCONNECT_PROJECT_ID=your-walletconnect-id
```

## 🚀 Deployment

### Production Setup
1. Set up PostgreSQL database
2. Configure environment variables
3. Set up reverse proxy (nginx)
4. Use process manager (PM2, systemd)
5. Enable SSL/TLS certificates

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up -d
```

## 🔒 Security Features

- JWT-based authentication
- Password hashing with bcrypt
- SQL injection prevention
- CORS protection
- Rate limiting
- Input validation
- Secure API key management

## 📊 Monitoring & Analytics

- Real-time portfolio tracking
- Transaction history
- Chain-specific analytics
- Volume and TVL metrics
- User activity monitoring
- System health checks

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

- Documentation: See SETUP.md for detailed setup
- Issues: Create GitHub issues for bugs
- API Docs: http://localhost:8000/docs (when running)

## 🎯 Roadmap

- [ ] AI trading signals integration
- [ ] Advanced portfolio analytics
- [ ] Mobile app development
- [ ] Additional DEX integrations
- [ ] Yield farming features
- [ ] NFT trading support
