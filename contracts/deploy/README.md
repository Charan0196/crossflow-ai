# CrossFlow AI Phase 1 - Smart Escrow Deployment Guide

This directory contains deployment scripts, configuration, and monitoring tools for the CrossFlow AI Smart Escrow system.

## Overview

The Smart Escrow system consists of:
- **SmartEscrowUpgradeable**: Main escrow contract with UUPS proxy pattern
- **MultiSigWallet**: Multi-signature governance wallet
- **Monitoring System**: Health checks and alerting

## Prerequisites

1. **Environment Setup**
   ```bash
   # Install dependencies
   npm install
   
   # Set up environment variables
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Required Environment Variables**
   ```bash
   PRIVATE_KEY=your_deployer_private_key
   ALCHEMY_API_KEY=your_alchemy_api_key
   ETHERSCAN_API_KEY=your_etherscan_api_key
   ARBISCAN_API_KEY=your_arbiscan_api_key
   ```

3. **Network Configuration**
   - Update `config.json` with your governance member addresses
   - Verify RPC endpoints and API keys
   - Set appropriate gas limits and confirmation requirements

## Deployment Process

### Phase 1: Testnet Deployment

1. **Deploy to Sepolia**
   ```bash
   npm run deploy-escrow:sepolia
   ```

2. **Deploy to Arbitrum Sepolia**
   ```bash
   npm run deploy-escrow:arbitrum-sepolia
   ```

3. **Verify Contracts**
   ```bash
   # Update addresses in scripts after deployment
   npm run verify:sepolia
   npm run verify:arbitrum-sepolia
   ```

4. **Test Functionality**
   ```bash
   # Run monitoring to verify deployment
   npm run monitor:sepolia
   npm run monitor:arbitrum-sepolia
   ```

### Phase 2: Mainnet Deployment

⚠️ **Only proceed after thorough testnet validation**

1. **Deploy to Ethereum Mainnet**
   ```bash
   npm run deploy-escrow:ethereum
   ```

2. **Deploy to Arbitrum One**
   ```bash
   npm run deploy-escrow:arbitrum
   ```

3. **Set up Monitoring**
   ```bash
   npm run monitor:ethereum
   npm run monitor:arbitrum
   ```

## Contract Architecture

### UUPS Proxy Pattern

The Smart Escrow uses the UUPS (Universal Upgradeable Proxy Standard) pattern:

```
User/Frontend
     ↓
Proxy Contract (SmartEscrowUpgradeable)
     ↓
Implementation Contract
     ↓
Storage (in Proxy)
```

**Benefits:**
- Upgradeable functionality
- Gas-efficient upgrades
- Preserves contract address
- Maintains state across upgrades

### Multi-Signature Governance

Governance operations require multiple signatures:

```
Governance Member 1 ──┐
Governance Member 2 ──┼── Multi-Sig Wallet ──→ Smart Escrow
Governance Member 3 ──┘
```

**Governance Functions:**
- Contract upgrades
- Emergency pause/unpause
- Solver authorization
- Parameter updates
- Emergency withdrawals

## Security Features

### 1. Multi-Signature Requirements
- **Mainnet**: 2-of-3 signatures required
- **Testnet**: 1-of-2 signatures for testing
- All critical operations require governance approval

### 2. Emergency Controls
- **Pause Mechanism**: Halt all operations if needed
- **Emergency Withdrawal**: Governance can recover funds
- **Upgrade Controls**: Only authorized addresses can upgrade

### 3. Timeouts and Refunds
- **Automatic Refunds**: Users get funds back after timeout
- **Configurable Timeouts**: Adjustable based on network conditions
- **Solver Authorization**: Only approved solvers can fulfill intents

### 4. Event Logging
- **Comprehensive Events**: All operations emit events
- **Audit Trail**: Complete history of all actions
- **Monitoring Integration**: Events trigger alerts

## Monitoring and Maintenance

### Health Checks

Run regular health checks:
```bash
# Check contract status
npm run monitor:ethereum
npm run monitor:arbitrum
```

### Key Metrics to Monitor

1. **Contract Health**
   - Pause status
   - Owner configuration
   - Governance member count
   - Timeout periods

2. **Multi-Sig Status**
   - Pending transactions
   - Owner list
   - Required signatures
   - Wallet balance

3. **Solver Activity**
   - Authorized solver count
   - Recent authorizations/deauthorizations
   - Solver performance metrics

4. **Event Activity**
   - Fund locks/releases/refunds
   - Emergency actions
   - Governance proposals
   - Contract upgrades

### Alerting Thresholds

Configure alerts for:
- Large transactions (>$100k mainnet, >$1k testnet)
- High pending transaction count (>5 mainnet, >10 testnet)
- Emergency events (pause, emergency withdrawal)
- Failed transactions
- Unusual solver activity

## Upgrade Process

### 1. Prepare Upgrade
```bash
# Validate upgrade compatibility
npm run upgrade-escrow:ethereum
```

### 2. Multi-Sig Approval
1. Upgrade script creates multi-sig proposal
2. Governance members confirm transaction
3. Execute upgrade when threshold reached

### 3. Verify Upgrade
```bash
# Check new implementation
npm run monitor:ethereum
```

## Troubleshooting

### Common Issues

1. **Deployment Fails**
   - Check gas limits in config
   - Verify network connectivity
   - Ensure sufficient ETH balance

2. **Verification Fails**
   - Wait for block confirmations
   - Check API key configuration
   - Verify constructor arguments

3. **Upgrade Issues**
   - Validate upgrade compatibility
   - Check governance permissions
   - Ensure multi-sig has sufficient confirmations

### Emergency Procedures

1. **Contract Compromise**
   ```bash
   # Emergency pause (requires governance)
   # Use multi-sig to call pause() function
   ```

2. **Stuck Funds**
   ```bash
   # Emergency withdrawal (requires governance)
   # Use multi-sig to call emergencyWithdraw()
   ```

3. **Governance Issues**
   ```bash
   # Check multi-sig status
   npm run monitor:ethereum
   # Review pending transactions
   # Contact governance members
   ```

## Support and Contacts

- **Development Team**: dev@crossflow.ai
- **Security Team**: security@crossflow.ai
- **Governance Council**: governance@crossflow.ai

## Additional Resources

- [OpenZeppelin Upgrades Documentation](https://docs.openzeppelin.com/upgrades-plugins/1.x/)
- [Multi-Signature Wallet Best Practices](https://blog.openzeppelin.com/multisig-wallet-best-practices/)
- [Hardhat Deployment Guide](https://hardhat.org/tutorial/deploying-to-a-live-network.html)
- [Contract Verification Guide](https://hardhat.org/plugins/nomiclabs-hardhat-etherscan.html)