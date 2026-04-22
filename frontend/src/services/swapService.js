/**
 * Real Swap Service - Uniswap V3 Integration
 * Handles actual blockchain transactions for token swaps
 */

import { parseUnits, formatUnits, parseEther } from 'viem'

// Uniswap V3 Router Contract Addresses
const UNISWAP_V3_ROUTER = {
  1: '0xE592427A0AEce92De3Edee1F18E0157C05861564', // Ethereum Mainnet
  11155111: '0xE592427A0AEce92De3Edee1F18E0157C05861564', // Sepolia Testnet
  137: '0xE592427A0AEce92De3Edee1F18E0157C05861564', // Polygon
  42161: '0xE592427A0AEce92De3Edee1F18E0157C05861564', // Arbitrum
  10: '0xE592427A0AEce92De3Edee1F18E0157C05861564', // Optimism
  8453: '0x2626664c2603336E57B271c5C0b26F421741e481', // Base
}

// WETH Contract Addresses
const WETH_ADDRESSES = {
  1: '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
  11155111: '0x7b79995e5f793A07Bc00c21412e50Ecae098E7f9',
  137: '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619',
  42161: '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1',
  10: '0x4200000000000000000000000000000000000006',
  8453: '0x4200000000000000000000000000000000000006',
}

// Common Token Addresses (Sepolia Testnet)
const TOKEN_ADDRESSES = {
  11155111: {
    WETH: '0x7b79995e5f793A07Bc00c21412e50Ecae098E7f9',
    USDC: '0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238',
    USDT: '0x7169D38820dfd117C3FA1f22a697dBA58d90BA06',
    DAI: '0x3e622317f8C93f7328350cF0B56d9eD4C620C5d6',
  },
  1: {
    WETH: '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
    USDC: '0xA0b86a33E6441b8435b662303c0f218C404c9cd4',
    USDT: '0xdAC17F958D2ee523a2206206994597C13D831ec7',
    DAI: '0x6B175474E89094C44Da98b954EedeAC495271d0F',
  }
}

// ERC-20 ABI (minimal)
const ERC20_ABI = [
  {
    name: 'balanceOf',
    type: 'function',
    stateMutability: 'view',
    inputs: [{ name: 'account', type: 'address' }],
    outputs: [{ name: '', type: 'uint256' }],
  },
  {
    name: 'allowance',
    type: 'function',
    stateMutability: 'view',
    inputs: [
      { name: 'owner', type: 'address' },
      { name: 'spender', type: 'address' },
    ],
    outputs: [{ name: '', type: 'uint256' }],
  },
  {
    name: 'approve',
    type: 'function',
    stateMutability: 'nonpayable',
    inputs: [
      { name: 'spender', type: 'address' },
      { name: 'amount', type: 'uint256' },
    ],
    outputs: [{ name: '', type: 'bool' }],
  },
  {
    name: 'decimals',
    type: 'function',
    stateMutability: 'view',
    inputs: [],
    outputs: [{ name: '', type: 'uint8' }],
  },
]

// Uniswap V3 Router ABI (minimal)
const UNISWAP_V3_ROUTER_ABI = [
  {
    name: 'exactInputSingle',
    type: 'function',
    stateMutability: 'payable',
    inputs: [
      {
        name: 'params',
        type: 'tuple',
        components: [
          { name: 'tokenIn', type: 'address' },
          { name: 'tokenOut', type: 'address' },
          { name: 'fee', type: 'uint24' },
          { name: 'recipient', type: 'address' },
          { name: 'deadline', type: 'uint256' },
          { name: 'amountIn', type: 'uint256' },
          { name: 'amountOutMinimum', type: 'uint256' },
          { name: 'sqrtPriceLimitX96', type: 'uint160' },
        ],
      },
    ],
    outputs: [{ name: 'amountOut', type: 'uint256' }],
  },
]

class SwapService {
  constructor() {
    this.slippageTolerance = 0.5 // 0.5% default slippage
  }

  /**
   * Get token address for a given symbol and chain
   */
  getTokenAddress(symbol, chainId) {
    const tokens = TOKEN_ADDRESSES[chainId]
    if (!tokens) {
      throw new Error(`Unsupported chain: ${chainId}`)
    }
    
    if (symbol === 'ETH') {
      return WETH_ADDRESSES[chainId]
    }
    
    const address = tokens[symbol]
    if (!address) {
      throw new Error(`Token ${symbol} not supported on chain ${chainId}`)
    }
    
    return address
  }

  /**
   * Check if token needs approval and get current allowance
   */
  async checkAllowance(tokenAddress, ownerAddress, spenderAddress, publicClient) {
    try {
      const allowance = await publicClient.readContract({
        address: tokenAddress,
        abi: ERC20_ABI,
        functionName: 'allowance',
        args: [ownerAddress, spenderAddress],
      })
      
      return allowance
    } catch (error) {
      console.error('Error checking allowance:', error)
      return 0n
    }
  }

  /**
   * Approve token spending
   */
  async approveToken(tokenAddress, spenderAddress, amount, walletClient) {
    try {
      const hash = await walletClient.writeContract({
        address: tokenAddress,
        abi: ERC20_ABI,
        functionName: 'approve',
        args: [spenderAddress, amount],
      })
      
      return hash
    } catch (error) {
      throw new Error(`Token approval failed: ${error.message}`)
    }
  }

  /**
   * Get token decimals
   */
  async getTokenDecimals(tokenAddress, publicClient) {
    try {
      const decimals = await publicClient.readContract({
        address: tokenAddress,
        abi: ERC20_ABI,
        functionName: 'decimals',
      })
      
      return decimals
    } catch (error) {
      console.error('Error getting token decimals:', error)
      return 18 // Default to 18 decimals
    }
  }

  /**
   * Calculate minimum amount out with slippage
   */
  calculateMinAmountOut(expectedAmountOut, slippagePercent = this.slippageTolerance) {
    const slippageMultiplier = (100 - slippagePercent) / 100
    return BigInt(Math.floor(Number(expectedAmountOut) * slippageMultiplier))
  }

  /**
   * Execute a real swap transaction
   */
  async executeSwap({
    fromToken,
    toToken,
    amount,
    slippage = 0.5,
    chainId,
    userAddress,
    publicClient,
    walletClient
  }) {
    try {
      console.log('Starting real swap execution...', {
        fromToken,
        toToken,
        amount,
        slippage,
        chainId,
        userAddress
      })

      // Get router address for the chain
      const routerAddress = UNISWAP_V3_ROUTER[chainId]
      if (!routerAddress) {
        throw new Error(`Uniswap V3 not supported on chain ${chainId}`)
      }

      // Get token addresses
      const tokenInAddress = this.getTokenAddress(fromToken, chainId)
      const tokenOutAddress = this.getTokenAddress(toToken, chainId)

      console.log('Token addresses:', { tokenInAddress, tokenOutAddress })

      // Get token decimals
      const tokenInDecimals = await this.getTokenDecimals(tokenInAddress, publicClient)
      const tokenOutDecimals = await this.getTokenDecimals(tokenOutAddress, publicClient)

      // Convert amount to proper units
      const amountIn = parseUnits(amount.toString(), tokenInDecimals)
      
      console.log('Amount in wei:', amountIn.toString())

      // For ETH swaps, we don't need approval
      const isETHSwap = fromToken === 'ETH'
      
      if (!isETHSwap) {
        // Check and handle token approval
        const currentAllowance = await this.checkAllowance(
          tokenInAddress,
          userAddress,
          routerAddress,
          publicClient
        )

        console.log('Current allowance:', currentAllowance.toString())

        if (currentAllowance < amountIn) {
          console.log('Approval needed, requesting approval...')
          
          // Request approval
          const approvalHash = await this.approveToken(
            tokenInAddress,
            routerAddress,
            amountIn,
            walletClient
          )

          console.log('Approval transaction hash:', approvalHash)

          // Wait for approval confirmation
          await publicClient.waitForTransactionReceipt({ hash: approvalHash })
          console.log('Approval confirmed')
        }
      }

      // Estimate output amount (simplified - in production use Uniswap SDK)
      const estimatedAmountOut = parseUnits((amount * 0.998).toString(), tokenOutDecimals) // Rough estimate
      const minAmountOut = this.calculateMinAmountOut(estimatedAmountOut, slippage)

      console.log('Estimated amount out:', estimatedAmountOut.toString())
      console.log('Min amount out:', minAmountOut.toString())

      // Prepare swap parameters
      const deadline = BigInt(Math.floor(Date.now() / 1000) + 1800) // 30 minutes
      const fee = 3000 // 0.3% fee tier

      const swapParams = {
        tokenIn: tokenInAddress,
        tokenOut: tokenOutAddress,
        fee,
        recipient: userAddress,
        deadline,
        amountIn,
        amountOutMinimum: minAmountOut,
        sqrtPriceLimitX96: 0n,
      }

      console.log('Swap parameters:', swapParams)

      // Execute the swap
      const swapHash = await walletClient.writeContract({
        address: routerAddress,
        abi: UNISWAP_V3_ROUTER_ABI,
        functionName: 'exactInputSingle',
        args: [swapParams],
        value: isETHSwap ? amountIn : 0n,
      })

      console.log('Swap transaction hash:', swapHash)

      // Wait for transaction confirmation
      const receipt = await publicClient.waitForTransactionReceipt({ 
        hash: swapHash,
        timeout: 60000 // 60 seconds timeout
      })

      console.log('Swap confirmed:', receipt)

      return {
        success: true,
        txHash: swapHash,
        receipt,
        fromToken,
        toToken,
        amountIn: formatUnits(amountIn, tokenInDecimals),
        estimatedAmountOut: formatUnits(estimatedAmountOut, tokenOutDecimals),
        gasUsed: receipt.gasUsed?.toString(),
        blockNumber: receipt.blockNumber?.toString(),
      }

    } catch (error) {
      console.error('Swap execution failed:', error)
      
      // Handle specific error types
      if (error.message.includes('user rejected')) {
        throw new Error('Transaction was rejected by user')
      } else if (error.message.includes('insufficient funds')) {
        throw new Error('Insufficient funds for transaction')
      } else if (error.message.includes('slippage')) {
        throw new Error('Transaction failed due to slippage. Try increasing slippage tolerance.')
      } else {
        throw new Error(`Swap failed: ${error.message}`)
      }
    }
  }

  /**
   * Get estimated swap output (for display purposes)
   */
  async getSwapQuote({
    fromToken,
    toToken,
    amount,
    chainId
  }) {
    try {
      // This is a simplified quote - in production, use Uniswap SDK or API
      // For now, we'll return a mock quote based on current market prices
      
      const mockRates = {
        'ETH-USDC': 1970,
        'ETH-USDT': 1970,
        'USDC-ETH': 1/1970,
        'USDT-ETH': 1/1970,
        'USDC-USDT': 1,
        'USDT-USDC': 1,
      }

      const pair = `${fromToken}-${toToken}`
      const rate = mockRates[pair] || 1

      const estimatedOutput = amount * rate * 0.997 // Account for fees

      return {
        inputAmount: amount,
        outputAmount: estimatedOutput,
        rate,
        priceImpact: 0.1, // 0.1%
        fee: amount * 0.003, // 0.3% fee
      }
    } catch (error) {
      console.error('Quote estimation failed:', error)
      return null
    }
  }
}

export const swapService = new SwapService()
export default swapService