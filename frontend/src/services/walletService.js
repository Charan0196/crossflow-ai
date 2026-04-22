import { ethers } from 'ethers'
import { chainConfig } from '../config/wagmi'

class WalletService {
  constructor() {
    this.providers = {}
    this.initializeProviders()
  }

  // Initialize providers for different chains
  initializeProviders() {
    Object.entries(chainConfig).forEach(([chainId, config]) => {
      try {
        this.providers[chainId] = new ethers.providers.JsonRpcProvider(config.rpcUrl)
      } catch (error) {
        console.error(`Failed to initialize provider for chain ${chainId}:`, error)
      }
    })
  }

  // Get native token balance
  async getNativeBalance(address, chainId) {
    try {
      const provider = this.providers[chainId]
      if (!provider) throw new Error(`No provider for chain ${chainId}`)
      
      const balance = await provider.getBalance(address)
      return ethers.utils.formatEther(balance)
    } catch (error) {
      console.error(`Error getting native balance:`, error)
      return '0'
    }
  }

  // Get ERC20 token balance
  async getTokenBalance(tokenAddress, walletAddress, chainId) {
    try {
      const provider = this.providers[chainId]
      if (!provider) throw new Error(`No provider for chain ${chainId}`)

      const tokenContract = new ethers.Contract(
        tokenAddress,
        [
          'function balanceOf(address owner) view returns (uint256)',
          'function decimals() view returns (uint8)',
          'function symbol() view returns (string)',
          'function name() view returns (string)'
        ],
        provider
      )

      const [balance, decimals, symbol, name] = await Promise.all([
        tokenContract.balanceOf(walletAddress),
        tokenContract.decimals(),
        tokenContract.symbol(),
        tokenContract.name()
      ])

      return {
        balance: ethers.utils.formatUnits(balance, decimals),
        decimals,
        symbol,
        name,
        address: tokenAddress
      }
    } catch (error) {
      console.error(`Error getting token balance:`, error)
      return null
    }
  }

  // Get portfolio for a wallet address across multiple chains
  async getWalletPortfolio(address) {
    const portfolio = {
      totalValue: 0,
      chains: {},
      tokens: []
    }

    try {
      // Get balances from all supported chains
      const chainPromises = Object.entries(chainConfig).map(async ([chainId, config]) => {
        try {
          const nativeBalance = await this.getNativeBalance(address, chainId)
          
          return {
            chainId: parseInt(chainId),
            name: config.name,
            symbol: config.symbol,
            nativeBalance,
            color: config.color,
            tokens: [] // Will be populated with token balances
          }
        } catch (error) {
          console.error(`Error getting portfolio for chain ${chainId}:`, error)
          return null
        }
      })

      const chainResults = await Promise.all(chainPromises)
      
      chainResults.forEach(result => {
        if (result) {
          portfolio.chains[result.chainId] = result
        }
      })

      return portfolio
    } catch (error) {
      console.error('Error getting wallet portfolio:', error)
      return portfolio
    }
  }

  // Get transaction history
  async getTransactionHistory(address, chainId, limit = 10) {
    try {
      const provider = this.providers[chainId]
      if (!provider) throw new Error(`No provider for chain ${chainId}`)

      const latestBlock = await provider.getBlockNumber()
      const transactions = []

      // Get recent transactions (simplified - in production use indexing service)
      for (let i = 0; i < limit && i < 100; i++) {
        try {
          const block = await provider.getBlockWithTransactions(latestBlock - i)
          const userTxs = block.transactions.filter(tx => 
            tx.from?.toLowerCase() === address.toLowerCase() || 
            tx.to?.toLowerCase() === address.toLowerCase()
          )
          
          transactions.push(...userTxs.slice(0, limit - transactions.length))
          
          if (transactions.length >= limit) break
        } catch (error) {
          continue
        }
      }

      return transactions.map(tx => ({
        hash: tx.hash,
        from: tx.from,
        to: tx.to,
        value: ethers.utils.formatEther(tx.value || '0'),
        gasPrice: tx.gasPrice ? ethers.utils.formatUnits(tx.gasPrice, 'gwei') : '0',
        blockNumber: tx.blockNumber,
        timestamp: Date.now() - (latestBlock - tx.blockNumber) * 12000 // Approximate
      }))
    } catch (error) {
      console.error('Error getting transaction history:', error)
      return []
    }
  }

  // Validate wallet address
  isValidAddress(address) {
    try {
      return ethers.utils.isAddress(address)
    } catch {
      return false
    }
  }

  // Get ENS name if available
  async getENSName(address) {
    try {
      const provider = this.providers['1'] // Ethereum mainnet
      if (!provider) return null
      
      return await provider.lookupAddress(address)
    } catch (error) {
      return null
    }
  }

  // Format address for display
  formatAddress(address, length = 6) {
    if (!address) return ''
    return `${address.slice(0, length)}...${address.slice(-4)}`
  }

  // Get gas price for a chain
  async getGasPrice(chainId) {
    try {
      const provider = this.providers[chainId]
      if (!provider) return null
      
      const gasPrice = await provider.getGasPrice()
      return ethers.utils.formatUnits(gasPrice, 'gwei')
    } catch (error) {
      console.error(`Error getting gas price for chain ${chainId}:`, error)
      return null
    }
  }

  // Common token addresses for each chain
  getCommonTokens(chainId) {
    const tokens = {
      1: [ // Ethereum
        { address: '0xA0b86a33E6C6C9c6C6C6C6C6C6C6C6C6C6C6C6C6', symbol: 'USDC', name: 'USD Coin' },
        { address: '0xdAC17F958D2ee523a2206206994597C13D831ec7', symbol: 'USDT', name: 'Tether USD' },
        { address: '0x6B175474E89094C44Da98b954EedeAC495271d0F', symbol: 'DAI', name: 'Dai Stablecoin' },
        { address: '0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984', symbol: 'UNI', name: 'Uniswap' }
      ],
      137: [ // Polygon
        { address: '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174', symbol: 'USDC', name: 'USD Coin' },
        { address: '0xc2132D05D31c914a87C6611C10748AEb04B58e8F', symbol: 'USDT', name: 'Tether USD' },
        { address: '0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063', symbol: 'DAI', name: 'Dai Stablecoin' }
      ],
      56: [ // BSC
        { address: '0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d', symbol: 'USDC', name: 'USD Coin' },
        { address: '0x55d398326f99059fF775485246999027B3197955', symbol: 'USDT', name: 'Tether USD' },
        { address: '0x1AF3F329e8BE154074D8769D1FFa4eE058B1DBc3', symbol: 'DAI', name: 'Dai Stablecoin' }
      ]
    }
    
    return tokens[chainId] || []
  }
}

export const walletService = new WalletService()
export default walletService