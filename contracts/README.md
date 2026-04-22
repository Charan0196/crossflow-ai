# CrossFlow AI Smart Contracts

Phase 1: Foundation & Intent Architecture smart contracts for the CrossFlow AI cross-chain trading platform.

## Overview

This directory contains the smart contracts implementing:

- **ERC-7683 Intent Engine**: Cross-chain intent processing and validation
- **Smart Escrow Settlement Layer**: Secure fund custody during cross-chain trades
- **Cross-Chain Messaging**: LayerZero V2 and Chainlink CCIP integration
- **Solver Network**: Competitive market maker system

## Architecture

```
contracts/
├── contracts/           # Solidity smart contracts
├── test/               # Contract tests
├── scripts/            # Deployment and utility scripts
├── deploy/             # Deployment configurations
└── hardhat.config.js   # Hardhat configuration
```

## Supported Networks

- **Ethereum Mainnet** (Chain ID: 1)
- **Arbitrum** (Chain ID: 42161)
- **Polygon** (Chain ID: 137)
- **Optimism** (Chain ID: 10)
- **BSC** (Chain ID: 56)
- **Base** (Chain ID: 8453)

### Testnets
- **Sepolia** (Chain ID: 11155111)
- **Arbitrum Sepolia** (Chain ID: 421614)

## Setup

1. Install dependencies:
```bash
npm install
```

2. Copy environment file:
```bash
cp .env.example .env
```

3. Configure your environment variables in `.env`:
```bash
ALCHEMY_API_KEY=your_alchemy_api_key
PRIVATE_KEY=your_private_key_for_deployment
```

## Development

### Compile Contracts
```bash
npm run compile
```

### Run Tests
```bash
npm run test
```

### Run Tests with Gas Reporting
```bash
npm run test:gas
```

### Coverage Report
```bash
npm run coverage
```

### Start Local Node
```bash
npm run node
```

## Deployment

### Local Network
```bash
npm run deploy:localhost
```

### Testnets
```bash
npm run deploy:sepolia
npm run deploy:arbitrum-sepolia
```

### Mainnet (Production)
```bash
# Configure mainnet networks in hardhat.config.js first
npx hardhat run scripts/deploy.js --network ethereum
npx hardhat run scripts/deploy.js --network arbitrum
```

## Contract Verification

After deployment, verify contracts on block explorers:

```bash
npm run verify:sepolia <CONTRACT_ADDRESS>
npm run verify:arbitrum-sepolia <CONTRACT_ADDRESS>
```

## Security

- All contracts use OpenZeppelin's battle-tested implementations
- Comprehensive test coverage with property-based testing
- Multi-signature governance for critical operations
- Time-locked upgrades and emergency pause functionality

## Phase 1 Implementation Status

- [x] Development environment setup
- [ ] ERC-7683 Intent Engine contracts
- [ ] Smart Escrow Settlement Layer
- [ ] LayerZero V2 integration
- [ ] Chainlink CCIP integration
- [ ] Solver Network contracts
- [ ] Multi-chain deployment
- [ ] Security audits

## Contributing

1. Follow the established coding standards
2. Write comprehensive tests for all new contracts
3. Update documentation for any interface changes
4. Ensure all tests pass before submitting PRs

## License

MIT License - see LICENSE file for details.