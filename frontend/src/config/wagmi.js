import { configureChains, createConfig } from 'wagmi'
import { mainnet, polygon, arbitrum, optimism, base, sepolia, bsc, avalanche } from 'wagmi/chains'
import { publicProvider } from 'wagmi/providers/public'
import { alchemyProvider } from 'wagmi/providers/alchemy'
import { MetaMaskConnector } from 'wagmi/connectors/metaMask'
import { InjectedConnector } from 'wagmi/connectors/injected'
import { WalletConnectConnector } from 'wagmi/connectors/walletConnect'
import { CoinbaseWalletConnector } from 'wagmi/connectors/coinbaseWallet'

// WalletConnect Project ID - Get yours at https://cloud.walletconnect.com
const projectId = import.meta.env.VITE_WALLETCONNECT_PROJECT_ID || '3a8170812b534d0ff9d794f19a901d64'

// Configure chains with providers
const { chains, publicClient, webSocketPublicClient } = configureChains(
  [mainnet, polygon, arbitrum, optimism, base, bsc, avalanche, sepolia],
  [
    publicProvider(),
  ],
  { pollingInterval: 10000 }
)

// MetaMask connector with proper configuration
const metaMaskConnector = new MetaMaskConnector({ 
  chains,
  options: {
    shimDisconnect: true,
    UNSTABLE_shimOnConnectSelectAccount: true,
  }
})

// Injected connector for other browser wallets
const injectedConnector = new InjectedConnector({
  chains,
  options: {
    name: (detectedName) => `${detectedName}`,
    shimDisconnect: true,
  },
})

// WalletConnect connector
const walletConnectConnector = new WalletConnectConnector({
  chains,
  options: {
    projectId,
    showQrModal: true,
    metadata: {
      name: 'CrossFlow AI',
      description: 'Cross-chain AI-powered DeFi trading platform',
      url: typeof window !== 'undefined' ? window.location.origin : 'https://crossflow.ai',
      icons: ['https://crossflow.ai/logo.png']
    }
  },
})

// Coinbase Wallet connector
const coinbaseConnector = new CoinbaseWalletConnector({
  chains,
  options: {
    appName: 'CrossFlow AI',
    headlessMode: false,
  },
})


// Create wagmi config
export const wagmiConfig = createConfig({
  autoConnect: true,
  connectors: [
    metaMaskConnector,
    injectedConnector,
    walletConnectConnector,
    coinbaseConnector,
  ],
  publicClient,
  webSocketPublicClient,
})

export { chains }

// Chain configurations with metadata
export const chainConfig = {
  1: { name: 'Ethereum', symbol: 'ETH', color: '#627EEA', icon: '⟠' },
  137: { name: 'Polygon', symbol: 'MATIC', color: '#8247E5', icon: '⬡' },
  42161: { name: 'Arbitrum', symbol: 'ETH', color: '#28A0F0', icon: '🔵' },
  10: { name: 'Optimism', symbol: 'ETH', color: '#FF0420', icon: '🔴' },
  8453: { name: 'Base', symbol: 'ETH', color: '#0052FF', icon: '🔵' },
  56: { name: 'BNB Chain', symbol: 'BNB', color: '#F3BA2F', icon: '🟡' },
  43114: { name: 'Avalanche', symbol: 'AVAX', color: '#E84142', icon: '🔺' },
  11155111: { name: 'Sepolia', symbol: 'ETH', color: '#CFB5F0', icon: '🧪' }
}

// Helper to get chain info
export const getChainInfo = (chainId) => {
  return chainConfig[chainId] || { name: 'Unknown', symbol: 'ETH', color: '#627EEA', icon: '?' }
}
