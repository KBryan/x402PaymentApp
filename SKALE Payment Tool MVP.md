# SKALE Payment Tool MVP

A comprehensive subscription payment solution for SKALE Chain owners, supporting recurring payments with SKALE and ERC-20 tokens, utilizing X402 encryption and SKALE decentralized storage.

## Quick Start

```bash
# Clone the repository
git clone https://github.com/your-org/skale-payment-tool.git
cd skale-payment-tool

# Setup backend
cd backend
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Setup smart contracts
cd ../contracts
curl -L https://foundry.paradigm.xyz | bash
foundryup
forge install

# Setup frontend
cd ../frontend
npm install

# Start the application
# Terminal 1: Backend
cd backend && source venv/bin/activate && python main.py

# Terminal 2: Frontend
cd frontend && npm run dev
```

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [API Documentation](#api-documentation)
- [Smart Contracts](#smart-contracts)
- [Frontend Guide](#frontend-guide)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## Architecture Overview

The SKALE Payment Tool consists of four main components:

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   CLIENT    │    │   SERVER    │    │ FACILITATOR │    │ BLOCKCHAIN  │
│             │    │             │    │             │    │             │
│ Web3 Wallet │◄──►│ FastAPI     │◄──►│ X402        │◄──►│ SKALE Chain │
│ Frontend    │    │ Backend     │    │ Encryption  │    │ Smart       │
│ React/HTML  │    │ Python      │    │ Protocol    │    │ Contracts   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

### Key Features

- **Recurring Subscriptions**: Automated payment processing for subscription plans
- **Multi-Token Support**: Native SKALE tokens and ERC-20 token compatibility
- **X402 Encryption**: Secure API URL encryption and access control
- **Decentralized Storage**: SKALE native storage for data persistence
- **Web3 Integration**: MetaMask and wallet connectivity
- **Real-time Analytics**: Dashboard with subscription and payment tracking

## Prerequisites

### System Requirements

- **Python**: 3.11 or higher
- **Node.js**: 18.0 or higher
- **npm**: 9.0 or higher
- **Git**: Latest version
- **Foundry**: For smart contract development

### Blockchain Requirements

- **MetaMask**: Browser wallet extension
- **SKALE Chain Access**: RPC endpoint and chain configuration
- **Test Tokens**: For development and testing

### Development Tools (Optional)

- **Docker**: For containerized deployment
- **PostgreSQL**: For production database
- **Redis**: For caching and session management

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/your-org/skale-payment-tool.git
cd skale-payment-tool
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies (optional)
pip install -r ../requirements-dev.txt

# Create environment file
cp .env.example .env
# Edit .env with your configuration
```

### 3. Smart Contracts Setup

```bash
cd contracts

# Install Foundry (if not already installed)
curl -L https://foundry.paradigm.xyz | bash
foundryup

# Install dependencies
forge install

# Compile contracts
forge build

# Run tests
forge test -vv
```

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Install development dependencies
npm install --save-dev

# Start development server
npm run dev
```

## Configuration

### Backend Configuration (.env)

Create a `.env` file in the `backend` directory:

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# Database Configuration
DATABASE_URL=sqlite:///./skale_payment.db
# For PostgreSQL: postgresql://user:password@localhost/skale_payment

# Blockchain Configuration
SKALE_RPC_URL=https://your-skale-chain-rpc.com
CHAIN_ID=1234567890
PRIVATE_KEY=your_private_key_here

# X402 Configuration
X402_ENCRYPTION_KEY=your_x402_key_here
X402_API_BASE=https://x402-api.example.com

# Security
SECRET_KEY=your_secret_key_here
CORS_ORIGINS=["http://localhost:3000", "https://yourdomain.com"]

# Monitoring
SENTRY_DSN=your_sentry_dsn_here
LOG_LEVEL=INFO

# Redis (Optional)
REDIS_URL=redis://localhost:6379/0
```

### Frontend Configuration

Update `js/config.js` with your settings:

```javascript
const CONFIG = {
    API_BASE_URL: 'http://localhost:8000',
    CHAIN_ID: 1234567890,
    CHAIN_NAME: 'SKALE Chain',
    RPC_URL: 'https://your-skale-chain-rpc.com',
    BLOCK_EXPLORER: 'https://your-block-explorer.com',
    NATIVE_CURRENCY: {
        name: 'SKALE',
        symbol: 'SKL',
        decimals: 18
    }
};
```

### Smart Contract Configuration

Update `foundry.toml` for your deployment:

```toml
[profile.default]
src = "src"
out = "out"
libs = ["lib"]
solc_version = "0.8.19"
optimizer = true
optimizer_runs = 200

[rpc_endpoints]
skale = "https://your-skale-chain-rpc.com"
local = "http://localhost:8545"

[etherscan]
skale = { key = "your_api_key", url = "https://your-block-explorer.com/api" }
```


## Development

### Development Workflow

1. **Start Backend Development Server**
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

2. **Start Frontend Development Server**
```bash
cd frontend
npm run dev
# Or use live-server
live-server --port=3000 --host=0.0.0.0
```

3. **Start Local Blockchain (Optional)**
```bash
cd contracts
anvil --host 0.0.0.0 --port 8545
```

4. **Deploy Smart Contracts Locally**
```bash
cd contracts
forge script script/Deploy.s.sol --rpc-url http://localhost:8545 --broadcast
```

### Code Quality

#### Backend Code Quality
```bash
# Format code
black backend/
isort backend/

# Lint code
flake8 backend/
mypy backend/

# Security scan
bandit -r backend/
safety check
```

#### Frontend Code Quality
```bash
# Format code
npm run format

# Lint code
npm run lint

# Type checking (if using TypeScript)
npm run type-check
```

#### Smart Contract Quality
```bash
# Format contracts
forge fmt

# Lint contracts
npm run lint

# Security analysis
slither src/
mythril analyze src/SubscriptionManager.sol
```

### Database Management

#### SQLite (Development)
```bash
# Create database
python -c "from backend.database import create_tables; create_tables()"

# View database
sqlite3 backend/skale_payment.db
```

#### PostgreSQL (Production)
```bash
# Create database
createdb skale_payment

# Run migrations
alembic upgrade head

# Create migration
alembic revision --autogenerate -m "description"
```

## Testing

### Backend Testing

```bash
cd backend
source venv/bin/activate

# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_api.py

# Run with verbose output
pytest -v -s

# Run performance tests
pytest --benchmark-only
```

### Smart Contract Testing

```bash
cd contracts

# Run all tests
forge test -vv

# Run specific test
forge test --match-test testCreatePlan -vv

# Run with gas reporting
forge test --gas-report

# Run coverage
forge coverage

# Run fuzz tests
forge test --fuzz-runs 1000
```

### Frontend Testing

```bash
cd frontend

# Run unit tests
npm test

# Run with coverage
npm run test:coverage

# Run end-to-end tests
npm run test:e2e

# Run visual regression tests
npm run test:visual
```

### Integration Testing

```bash
# Start all services
docker-compose up -d

# Run integration tests
pytest tests/integration/

# Load testing
locust -f tests/load/locustfile.py --host=http://localhost:8000
```

## Deployment

### Local Deployment

#### Using Docker Compose
```bash
# Build and start all services
docker-compose up --build

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

#### Manual Deployment
```bash
# Backend
cd backend
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Frontend
cd frontend
npm run build
npm run serve
```

### Production Deployment

#### Smart Contract Deployment
```bash
cd contracts

# Deploy to SKALE Chain
forge script script/Deploy.s.sol \
  --rpc-url $SKALE_RPC_URL \
  --private-key $PRIVATE_KEY \
  --broadcast \
  --verify

# Verify contract
forge verify-contract $CONTRACT_ADDRESS \
  src/SubscriptionManager.sol:SubscriptionManager \
  --chain-id $CHAIN_ID \
  --etherscan-api-key $ETHERSCAN_API_KEY
```

#### Backend Deployment (AWS/GCP/Azure)
```bash
# Using Docker
docker build -t skale-payment-backend backend/
docker run -p 8000:8000 --env-file .env skale-payment-backend

# Using systemd service
sudo cp deployment/skale-payment.service /etc/systemd/system/
sudo systemctl enable skale-payment
sudo systemctl start skale-payment
```

#### Frontend Deployment (Netlify/Vercel/S3)
```bash
# Build for production
cd frontend
npm run build

# Deploy to Netlify
netlify deploy --prod --dir=dist

# Deploy to Vercel
vercel --prod

# Deploy to S3
aws s3 sync dist/ s3://your-bucket-name --delete
```

### Environment-Specific Configurations

#### Development
```env
DEBUG=true
LOG_LEVEL=DEBUG
DATABASE_URL=sqlite:///./dev.db
CORS_ORIGINS=["http://localhost:3000"]
```

#### Staging
```env
DEBUG=false
LOG_LEVEL=INFO
DATABASE_URL=postgresql://user:pass@staging-db/skale_payment
CORS_ORIGINS=["https://staging.yourdomain.com"]
```

#### Production
```env
DEBUG=false
LOG_LEVEL=WARNING
DATABASE_URL=postgresql://user:pass@prod-db/skale_payment
CORS_ORIGINS=["https://yourdomain.com"]
SENTRY_DSN=your_production_sentry_dsn
```

## API Documentation

### Authentication

The API uses X402 payment-based authentication. Include the payment header in requests:

```http
X-PAYMENT: b64:amount:token:signature:timestamp:from_address
```

### Core Endpoints

#### Plans Management
```http
GET    /plans              # List all active plans
POST   /plans              # Create new plan (requires payment)
GET    /plans/{plan_id}    # Get plan details
PUT    /plans/{plan_id}    # Update plan (requires payment)
DELETE /plans/{plan_id}    # Deactivate plan (requires payment)
```

#### Subscriptions Management
```http
POST   /subscribe          # Subscribe to plan (requires payment)
GET    /subscriptions      # Get user subscriptions
GET    /subscriptions/{id} # Get subscription details
DELETE /subscriptions/{id} # Cancel subscription (requires payment)
```

#### Payments and Access
```http
POST   /verify-access      # Verify API access
GET    /payment-history    # Get payment history
POST   /process-payment    # Process subscription payment
```

#### Development Endpoints
```http
GET    /dev/plans          # List all plans (no auth)
GET    /dev/subscriptions  # List all subscriptions (no auth)
GET    /dev/payments       # List all payments (no auth)
POST   /dev/reset          # Reset all data (no auth)
```

### API Response Format

```json
{
  "success": true,
  "data": {
    "plan_id": "uuid",
    "amount": 100,
    "token": "native",
    "description": "Premium API Access"
  },
  "message": "Plan created successfully",
  "timestamp": "2025-07-20T15:30:00Z"
}
```

### Error Handling

```json
{
  "success": false,
  "error": {
    "code": "PAYMENT_REQUIRED",
    "message": "Payment verification failed",
    "details": "Invalid signature"
  },
  "timestamp": "2025-07-20T15:30:00Z"
}
```

## Smart Contracts

### SubscriptionManager Contract

The main smart contract handles subscription logic:

```solidity
// Core functions
function createPlan(
    address token,
    uint256 amount,
    uint256 intervalDays,
    uint256 durationDays,
    string memory apiUrl
) external returns (bytes32 planId);

function subscribe(bytes32 planId) external payable;
function cancelSubscription(bytes32 planId) external;
function processPayment(bytes32 planId) external payable;
```

### Contract Addresses

#### SKALE Chain Mainnet
```
SubscriptionManager: 0x...
```

#### SKALE Chain Testnet
```
SubscriptionManager: 0x...
```

### Contract Interaction

```javascript
// Using ethers.js
const contract = new ethers.Contract(
    contractAddress,
    SubscriptionManagerABI,
    signer
);

// Create plan
const tx = await contract.createPlan(
    "0x0000000000000000000000000000000000000000", // native token
    ethers.parseEther("100"),
    30, // 30 days
    365, // 1 year
    "https://api.example.com/protected"
);
```

## Frontend Guide

### Component Structure

```
frontend/
├── index.html              # Main HTML file
├── styles.css             # Global styles
├── js/
│   ├── app.js            # Main application logic
│   ├── web3-integration.js # Web3 wallet integration
│   ├── api-client.js     # Backend API client
│   ├── ui-components.js  # UI components and utilities
│   └── config.js         # Configuration
└── assets/
    ├── images/           # Image assets
    └── icons/            # Icon assets
```

### Key Features

#### Wallet Integration
```javascript
// Connect wallet
const result = await web3Integration.connectWallet();
if (result.success) {
    console.log('Connected:', result.account);
}

// Sign transaction
const signature = await web3Integration.signMessage(message);
```

#### Plan Management
```javascript
// Create plan
const plan = await apiClient.createPlan({
    token: 'native',
    amount: 100,
    interval_days: 30,
    duration_days: 365,
    api_url: 'https://api.example.com/protected'
});
```

#### Subscription Handling
```javascript
// Subscribe to plan
const subscription = await apiClient.subscribeToPlan({
    plan_id: planId,
    subscriber_address: userAddress
});
```

### Styling Guidelines

The frontend uses a modern design system with:

- **Color Palette**: Purple/blue theme with semantic colors
- **Typography**: Inter font family with consistent sizing
- **Layout**: CSS Grid and Flexbox for responsive design
- **Components**: Modular CSS classes with BEM methodology
- **Animations**: Smooth transitions and micro-interactions

### Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+
- Mobile browsers with Web3 support


## Troubleshooting

### Common Issues

#### Backend Issues

**Issue: FastAPI server won't start**
```bash
# Check Python version
python --version  # Should be 3.11+

# Check virtual environment
which python
pip list

# Check port availability
lsof -i :8000
```

**Issue: Database connection errors**
```bash
# SQLite permissions
chmod 664 backend/skale_payment.db

# PostgreSQL connection
pg_isready -h localhost -p 5432
```

**Issue: CORS errors**
```python
# Update CORS settings in main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### Smart Contract Issues

**Issue: Compilation errors**
```bash
# Update Foundry
foundryup

# Clean and rebuild
forge clean
forge build

# Check Solidity version
forge --version
```

**Issue: Deployment failures**
```bash
# Check network configuration
forge config

# Verify RPC endpoint
curl -X POST -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' \
  $SKALE_RPC_URL

# Check gas settings
forge script script/Deploy.s.sol --gas-estimate
```

**Issue: Test failures**
```bash
# Run specific test with verbose output
forge test --match-test testCreatePlan -vvv

# Check test coverage
forge coverage --report lcov
```

#### Frontend Issues

**Issue: Web3 connection problems**
```javascript
// Check MetaMask installation
if (typeof window.ethereum === 'undefined') {
    console.error('MetaMask not installed');
}

// Check network configuration
const chainId = await window.ethereum.request({ 
    method: 'eth_chainId' 
});
console.log('Current chain:', chainId);
```

**Issue: API connection errors**
```javascript
// Check CORS and API availability
fetch('http://localhost:8000/health')
    .then(response => response.json())
    .then(data => console.log('API Status:', data))
    .catch(error => console.error('API Error:', error));
```

**Issue: Build/deployment problems**
```bash
# Clear npm cache
npm cache clean --force

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install

# Check for conflicting ports
netstat -tulpn | grep :3000
```

### Performance Issues

#### Backend Performance
```bash
# Profile API endpoints
py-spy record -o profile.svg -- python main.py

# Monitor memory usage
memory_profiler python main.py

# Database query optimization
EXPLAIN ANALYZE SELECT * FROM subscriptions WHERE user_id = ?;
```

#### Frontend Performance
```bash
# Bundle analysis
npm run build -- --analyze

# Lighthouse audit
lighthouse http://localhost:3000 --output html

# Performance monitoring
npm install --save-dev webpack-bundle-analyzer
```

### Security Considerations

#### Backend Security
- Always validate input data
- Use environment variables for secrets
- Implement rate limiting
- Enable HTTPS in production
- Regular dependency updates

#### Smart Contract Security
- Use OpenZeppelin contracts
- Implement access controls
- Add reentrancy guards
- Conduct security audits
- Test edge cases thoroughly

#### Frontend Security
- Validate user inputs
- Sanitize displayed data
- Use HTTPS for API calls
- Implement CSP headers
- Regular dependency updates

### Monitoring and Logging

#### Application Monitoring
```python
# Sentry integration
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[FastApiIntegration()],
    traces_sample_rate=1.0,
)
```

#### Performance Monitoring
```python
# Prometheus metrics
from prometheus_fastapi_instrumentator import Instrumentator

instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app)
```

#### Log Configuration
```python
import structlog

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
```

## Contributing

### Development Setup

1. **Fork the repository**
2. **Create feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Install pre-commit hooks**
   ```bash
   pre-commit install
   ```
4. **Make changes and test**
   ```bash
   # Run all tests
   make test
   
   # Check code quality
   make lint
   ```
5. **Submit pull request**

### Code Standards

#### Python Code Style
- Follow PEP 8
- Use Black for formatting
- Use type hints
- Write docstrings
- Minimum 80% test coverage

#### JavaScript Code Style
- Use ES6+ features
- Follow Airbnb style guide
- Use Prettier for formatting
- Write JSDoc comments
- Use meaningful variable names

#### Solidity Code Style
- Follow Solidity style guide
- Use NatSpec comments
- Implement comprehensive tests
- Use OpenZeppelin patterns
- Document gas optimizations

### Pull Request Process

1. **Update documentation**
2. **Add/update tests**
3. **Ensure CI passes**
4. **Request code review**
5. **Address feedback**
6. **Merge after approval**

### Issue Reporting

When reporting issues, please include:

- **Environment details** (OS, Python/Node version, etc.)
- **Steps to reproduce**
- **Expected vs actual behavior**
- **Error messages/logs**
- **Screenshots** (for UI issues)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **SKALE Network** for the blockchain infrastructure
- **OpenZeppelin** for secure smart contract patterns
- **FastAPI** for the excellent Python web framework
- **Foundry** for smart contract development tools
- **Chart.js** for data visualization components


### Professional Support
- Email: kwame@playonquake.com

---

## Project Status

### Current Version: 1.0.0 (MVP)

#### Completed Features
- [x] Smart contract implementation
- [x] FastAPI backend with X402 integration
- [x] Modern HTML/CSS/JavaScript frontend
- [x] Web3 wallet integration
- [x] Subscription management system
- [x] Payment processing
- [x] Analytics dashboard
- [x] Comprehensive testing suite

#### In Progress
- [ ] Production deployment
- [ ] Advanced analytics
- [ ] Mobile app development
- [ ] Multi-chain support

#### Roadmap
- [ ] Advanced subscription features
- [ ] Integration with more wallets
- [ ] Enhanced security features
- [ ] Performance optimizations
- [ ] Additional payment methods

### Development Statistics
- **Lines of Code**: ~5,000
- **Test Coverage**: 85%+
- **Documentation**: Comprehensive
- **Security Audits**: Pending
- **Performance**: Optimized for MVP

---

**Built with ❤️ for the SKALE ecosystem**

