import axios from 'axios'

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// Create axios instance
export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authAPI = {
  login: (username, password) =>
    api.post('/api/auth/login', new URLSearchParams({ username, password }), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    }),
  register: (userData) => api.post('/api/auth/register', userData),
  getProfile: () => api.get('/api/auth/me'),
  updateWalletAddresses: (walletData) => api.put('/api/auth/wallet-addresses', walletData),
}

// Trading API
export const tradingAPI = {
  getTokens: (chainId) => api.get(`/api/trading/tokens/${chainId}`),
  getSwapQuote: (swapData) => api.post('/api/trading/swap/quote', swapData),
  getSwapTransaction: (swapData, fromAddress) => 
    api.post('/api/trading/swap/transaction', swapData, { params: { from_address: fromAddress } }),
  checkAllowance: (chainId, tokenAddress, walletAddress) =>
    api.get(`/api/trading/swap/allowance/${chainId}`, {
      params: { token_address: tokenAddress, wallet_address: walletAddress }
    }),
  getApproveTransaction: (chainId, tokenAddress, amount) =>
    api.post(`/api/trading/swap/approve/${chainId}`, null, {
      params: { token_address: tokenAddress, amount }
    }),
  getBridgeChains: () => api.get('/api/trading/bridge/chains'),
  getBridgeTokens: (chainId) => api.get('/api/trading/bridge/tokens', { params: { chain_id: chainId } }),
  getBridgeQuote: (bridgeData, fromAddress) =>
    api.post('/api/trading/bridge/quote', bridgeData, { params: { from_address: fromAddress } }),
  getBridgeRoutes: (bridgeData, fromAddress) =>
    api.post('/api/trading/bridge/routes', bridgeData, { params: { from_address: fromAddress } }),
  getBridgeStatus: (txHash, bridge, fromChain, toChain) =>
    api.get('/api/trading/bridge/status', {
      params: { tx_hash: txHash, bridge, from_chain: fromChain, to_chain: toChain }
    }),
  getGasPrice: (chainId) => api.get(`/api/trading/gas-price/${chainId}`),
}

// Portfolio API
export const portfolioAPI = {
  getBalance: (chainId, address) => api.get(`/api/portfolio/balance/${chainId}`, { params: { address } }),
  getSummary: () => api.get('/api/portfolio/summary'),
  refreshPortfolio: (chainId, address) => 
    api.post(`/api/portfolio/refresh/${chainId}`, null, { params: { address } }),
  createTransaction: (transactionData) => api.post('/api/portfolio/transactions', transactionData),
  getTransactions: (limit = 50, offset = 0) =>
    api.get('/api/portfolio/transactions', { params: { limit, offset } }),
  getTransactionStatus: (txHash, chainId) =>
    api.get(`/api/portfolio/transactions/${txHash}`, { params: { chain_id: chainId } }),
  createSnapshot: () => api.post('/api/portfolio/snapshot'),
}

// Admin API
export const adminAPI = {
  getStats: () => api.get('/api/admin/stats'),
  getUsers: (limit = 50, offset = 0) => api.get('/api/admin/users', { params: { limit, offset } }),
  updateUserStatus: (userId, isActive) => api.put(`/api/admin/users/${userId}/status`, { is_active: isActive }),
  getRecentTransactions: (limit = 100) => api.get('/api/admin/transactions/recent', { params: { limit } }),
  getVolumeAnalytics: (days = 30) => api.get('/api/admin/analytics/volume', { params: { days } }),
  getChainAnalytics: () => api.get('/api/admin/analytics/chains'),
  cleanupOldData: (days = 90) => api.post('/api/admin/maintenance/cleanup', { days }),
}