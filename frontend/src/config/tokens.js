// Token list for CrossFlow AI
export const tokens = {
  // Ethereum Mainnet
  1: [
    { symbol: 'ETH', name: 'Ethereum', address: '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE', decimals: 18, logo: '⟠', color: '#627EEA' },
    { symbol: 'WETH', name: 'Wrapped Ether', address: '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2', decimals: 18, logo: '⟠', color: '#627EEA' },
    { symbol: 'USDC', name: 'USD Coin', address: '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48', decimals: 6, logo: '💵', color: '#2775CA' },
    { symbol: 'USDT', name: 'Tether USD', address: '0xdAC17F958D2ee523a2206206994597C13D831ec7', decimals: 6, logo: '💲', color: '#26A17B' },
    { symbol: 'DAI', name: 'Dai Stablecoin', address: '0x6B175474E89094C44Da98b954EescdeCB5BE3830', decimals: 18, logo: '◈', color: '#F5AC37' },
    { symbol: 'WBTC', name: 'Wrapped Bitcoin', address: '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599', decimals: 8, logo: '₿', color: '#F7931A' },
    { symbol: 'LINK', name: 'Chainlink', address: '0x514910771AF9Ca656af840dff83E8264EcF986CA', decimals: 18, logo: '⬡', color: '#2A5ADA' },
    { symbol: 'UNI', name: 'Uniswap', address: '0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984', decimals: 18, logo: '🦄', color: '#FF007A' },
    { symbol: 'AAVE', name: 'Aave', address: '0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9', decimals: 18, logo: '👻', color: '#B6509E' },
    { symbol: 'CRV', name: 'Curve DAO', address: '0xD533a949740bb3306d119CC777fa900bA034cd52', decimals: 18, logo: '🌊', color: '#FF0000' },
    { symbol: 'LDO', name: 'Lido DAO', address: '0x5A98FcBEA516Cf06857215779Fd812CA3beF1B32', decimals: 18, logo: '🔷', color: '#00A3FF' },
    { symbol: 'ARB', name: 'Arbitrum', address: '0xB50721BCf8d664c30412Cfbc6cf7a15145234ad1', decimals: 18, logo: '🔵', color: '#28A0F0' },
    { symbol: 'OP', name: 'Optimism', address: '0x4200000000000000000000000000000000000042', decimals: 18, logo: '🔴', color: '#FF0420' },
    { symbol: 'MATIC', name: 'Polygon', address: '0x7D1AfA7B718fb893dB30A3aBc0Cfc608AaCfeBB0', decimals: 18, logo: '💜', color: '#8247E5' },
    { symbol: 'SHIB', name: 'Shiba Inu', address: '0x95aD61b0a150d79219dCF64E1E6Cc01f0B64C4cE', decimals: 18, logo: '🐕', color: '#FFA409' },
    { symbol: 'PEPE', name: 'Pepe', address: '0x6982508145454Ce325dDbE47a25d4ec3d2311933', decimals: 18, logo: '🐸', color: '#3D9C3D' },
  ],
  // Polygon
  137: [
    { symbol: 'MATIC', name: 'Polygon', address: '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE', decimals: 18, logo: '💜', color: '#8247E5' },
    { symbol: 'WMATIC', name: 'Wrapped Matic', address: '0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270', decimals: 18, logo: '💜', color: '#8247E5' },
    { symbol: 'USDC', name: 'USD Coin', address: '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174', decimals: 6, logo: '💵', color: '#2775CA' },
    { symbol: 'USDT', name: 'Tether USD', address: '0xc2132D05D31c914a87C6611C10748AEb04B58e8F', decimals: 6, logo: '💲', color: '#26A17B' },
    { symbol: 'WETH', name: 'Wrapped Ether', address: '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619', decimals: 18, logo: '⟠', color: '#627EEA' },
    { symbol: 'WBTC', name: 'Wrapped Bitcoin', address: '0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6', decimals: 8, logo: '₿', color: '#F7931A' },
  ],
  // Arbitrum
  42161: [
    { symbol: 'ETH', name: 'Ethereum', address: '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE', decimals: 18, logo: '⟠', color: '#627EEA' },
    { symbol: 'ARB', name: 'Arbitrum', address: '0x912CE59144191C1204E64559FE8253a0e49E6548', decimals: 18, logo: '🔵', color: '#28A0F0' },
    { symbol: 'USDC', name: 'USD Coin', address: '0xaf88d065e77c8cC2239327C5EDb3A432268e5831', decimals: 6, logo: '💵', color: '#2775CA' },
    { symbol: 'USDT', name: 'Tether USD', address: '0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9', decimals: 6, logo: '💲', color: '#26A17B' },
    { symbol: 'WBTC', name: 'Wrapped Bitcoin', address: '0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f', decimals: 8, logo: '₿', color: '#F7931A' },
    { symbol: 'GMX', name: 'GMX', address: '0xfc5A1A6EB076a2C7aD06eD22C90d7E710E35ad0a', decimals: 18, logo: '🔷', color: '#2D42FC' },
  ],
  // Base
  8453: [
    { symbol: 'ETH', name: 'Ethereum', address: '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE', decimals: 18, logo: '⟠', color: '#627EEA' },
    { symbol: 'USDC', name: 'USD Coin', address: '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913', decimals: 6, logo: '💵', color: '#2775CA' },
    { symbol: 'cbETH', name: 'Coinbase ETH', address: '0x2Ae3F1Ec7F1F5012CFEab0185bfc7aa3cf0DEc22', decimals: 18, logo: '🔵', color: '#0052FF' },
  ],
  // Optimism
  10: [
    { symbol: 'ETH', name: 'Ethereum', address: '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE', decimals: 18, logo: '⟠', color: '#627EEA' },
    { symbol: 'OP', name: 'Optimism', address: '0x4200000000000000000000000000000000000042', decimals: 18, logo: '🔴', color: '#FF0420' },
    { symbol: 'USDC', name: 'USD Coin', address: '0x7F5c764cBc14f9669B88837ca1490cCa17c31607', decimals: 6, logo: '💵', color: '#2775CA' },
    { symbol: 'USDT', name: 'Tether USD', address: '0x94b008aA00579c1307B0EF2c499aD98a8ce58e58', decimals: 6, logo: '💲', color: '#26A17B' },
  ]
}

// Popular trading pairs
export const popularPairs = [
  { from: 'ETH', to: 'USDC' },
  { from: 'ETH', to: 'USDT' },
  { from: 'WBTC', to: 'ETH' },
  { from: 'USDC', to: 'USDT' },
  { from: 'ETH', to: 'DAI' },
  { from: 'LINK', to: 'ETH' },
  { from: 'UNI', to: 'ETH' },
  { from: 'ARB', to: 'ETH' },
]

// Get tokens for a specific chain
export const getTokensForChain = (chainId) => {
  return tokens[chainId] || tokens[1]
}

// Get token by symbol
export const getTokenBySymbol = (chainId, symbol) => {
  const chainTokens = getTokensForChain(chainId)
  return chainTokens.find(t => t.symbol === symbol)
}

// Default tokens
export const defaultFromToken = tokens[1][0] // ETH
export const defaultToToken = tokens[1][2] // USDC
