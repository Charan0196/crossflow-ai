import React, { useEffect, useState } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './stores/authStore'
import { useAccount, useConnect, useDisconnect, useNetwork } from 'wagmi'
import { 
  Eye, EyeOff, LogIn, Wallet, TrendingUp, ArrowLeftRight, BarChart3, Home, Settings, LogOut, 
  DollarSign, Activity, Users, Zap, RefreshCw, ArrowDown, Star, Search, Filter, Globe, 
  Cpu, Brain, Shield, Target, Layers, Signal, Wifi, Database, Clock, AlertCircle
} from 'lucide-react'
import { toast } from 'react-toastify'
import { chainConfig } from './config/wagmi'
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar } from 'recharts'
import { CrossFlowLogo, CompactLogo, LoadingLogo } from './components/Logo'
import { priceService } from './services/priceService'
import { walletService } from './services/walletService'

// Mock data for charts (will be replaced with real data)
const portfolioData = Array.from({ length: 24 }, (_, i) => ({
  time: `${i}:00`,
  value: 32000 + Math.sin(i * 0.5) * 2000 + Math.random() * 1000,
  volume: 50000 + Math.random() * 30000
}))

// Login Component
const LoginPage = () => {
  const [formData, setFormData] = useState({ username: '', password: '' })
  const [showPassword, setShowPassword] = useState(false)
  const { login, isLoading, error } = useAuthStore()

  const handleSubmit = async (e) => {
    e.preventDefault()
    const result = await login(formData.username, formData.password)
    if (result.success) {
      toast.success('🚀 Welcome to CrossFlow AI DEX!')
    } else {
      toast.error(result.error || 'Login failed')
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-900 flex items-center justify-center p-4 relative overflow-hidden">
      {/* Enhanced Animated Background */}
      <div className="absolute inset-0">
        {/* Gradient Orbs */}
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-gradient-to-r from-cyan-400/30 to-blue-500/30 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-gradient-to-r from-purple-500/30 to-pink-500/30 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }}></div>
        <div className="absolute top-1/2 left-1/2 w-96 h-96 bg-gradient-to-r from-orange-400/20 to-red-500/20 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '2s' }}></div>
        
        {/* Circuit Pattern Overlay */}
        <div className="absolute inset-0 opacity-10">
          <svg width="100%" height="100%" className="absolute inset-0">
            <defs>
              <pattern id="circuit" x="0" y="0" width="100" height="100" patternUnits="userSpaceOnUse">
                <path d="M20,20 L80,20 L80,40 L60,40 L60,60 L80,60 L80,80 L20,80 L20,60 L40,60 L40,40 L20,40 Z" 
                      fill="none" stroke="#00D4FF" strokeWidth="1"/>
                <circle cx="30" cy="30" r="2" fill="#00D4FF"/>
                <circle cx="70" cy="70" r="2" fill="#FF00FF"/>
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#circuit)"/>
          </svg>
        </div>
      </div>
      
      {/* Floating Particles */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {[...Array(20)].map((_, i) => (
          <div
            key={i}
            className={`absolute w-2 h-2 rounded-full animate-bounce opacity-60`}
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              backgroundColor: ['#00D4FF', '#8B5CF6', '#FF00FF', '#F59E0B'][Math.floor(Math.random() * 4)],
              animationDelay: `${Math.random() * 3}s`,
              animationDuration: `${2 + Math.random() * 2}s`
            }}
          />
        ))}
      </div>
      
      <div className="relative bg-black/20 backdrop-blur-2xl rounded-3xl shadow-2xl p-8 w-full max-w-md border border-cyan-400/30 animate-glow">
        <div className="text-center mb-8">
          {/* Enhanced Logo */}
          <div className="flex justify-center mb-6">
            <CrossFlowLogo size="xl" animated={true} />
          </div>
          <p className="text-cyan-200 text-lg font-medium mb-2">Welcome to the Future of DeFi</p>
          <div className="flex items-center justify-center space-x-4 mb-4">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse"></div>
              <span className="text-sm text-cyan-300 font-medium">AI Powered</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-purple-400 rounded-full animate-pulse" style={{ animationDelay: '0.5s' }}></div>
              <span className="text-sm text-purple-300 font-medium">Cross-Chain</span>
            </div>
          </div>
          
          {/* Status Bar */}
          <div className="bg-gradient-to-r from-cyan-500/20 to-purple-500/20 rounded-full p-2 border border-cyan-400/30">
            <div className="flex items-center justify-center space-x-2">
              <div className="w-3 h-3 bg-green-400 rounded-full animate-ping"></div>
              <span className="text-xs text-green-300 font-medium">System Online</span>
            </div>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-cyan-200 mb-2 flex items-center space-x-2">
              <div className="w-2 h-2 bg-cyan-400 rounded-full"></div>
              <span>Username</span>
            </label>
            <input
              type="text"
              value={formData.username}
              onChange={(e) => setFormData({...formData, username: e.target.value})}
              className="w-full px-4 py-3 bg-gradient-to-r from-cyan-500/10 to-purple-500/10 border-2 border-cyan-400/30 rounded-xl text-white placeholder-cyan-300/70 focus:ring-2 focus:ring-cyan-400 focus:border-cyan-400 backdrop-blur-sm transition-all duration-300 hover:border-cyan-400/50"
              placeholder="Enter your username"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-purple-200 mb-2 flex items-center space-x-2">
              <div className="w-2 h-2 bg-purple-400 rounded-full"></div>
              <span>Password</span>
            </label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                value={formData.password}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
                className="w-full px-4 py-3 bg-gradient-to-r from-purple-500/10 to-pink-500/10 border-2 border-purple-400/30 rounded-xl text-white placeholder-purple-300/70 focus:ring-2 focus:ring-purple-400 focus:border-purple-400 backdrop-blur-sm pr-12 transition-all duration-300 hover:border-purple-400/50"
                placeholder="Enter your password"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-purple-300 hover:text-white transition-colors p-1 rounded-lg hover:bg-purple-500/20"
              >
                {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>
          </div>

          {error && (
            <div className="bg-gradient-to-r from-red-500/20 to-pink-500/20 border-2 border-red-400/30 text-red-200 px-4 py-3 rounded-xl backdrop-blur-sm animate-pulse">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-red-400 rounded-full"></div>
                <span>{error}</span>
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-gradient-to-r from-cyan-500 via-purple-500 to-pink-500 text-white py-4 px-4 rounded-xl font-bold text-lg hover:from-cyan-600 hover:via-purple-600 hover:to-pink-600 focus:ring-4 focus:ring-cyan-400/50 disabled:opacity-50 transition-all shadow-2xl transform hover:scale-105 active:scale-95 border border-cyan-400/30"
          >
            {isLoading ? (
              <div className="flex items-center justify-center space-x-3">
                <div className="w-6 h-6 border-3 border-white border-t-transparent rounded-full animate-spin" />
                <span>Connecting to AI Network...</span>
              </div>
            ) : (
              <div className="flex items-center justify-center space-x-3">
                <LogIn className="w-6 h-6" />
                <span>Enter CrossFlow AI</span>
                <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
              </div>
            )}
          </button>

          <div className="text-center bg-gradient-to-r from-cyan-500/10 to-purple-500/10 rounded-xl p-4 border border-cyan-400/20">
            <div className="text-sm text-cyan-200 mb-2">Demo Credentials</div>
            <div className="flex items-center justify-center space-x-4">
              <span className="font-medium text-cyan-300 bg-cyan-500/20 px-3 py-1 rounded-lg">testuser</span>
              <span className="text-cyan-400">/</span>
              <span className="font-medium text-purple-300 bg-purple-500/20 px-3 py-1 rounded-lg">testpass123</span>
            </div>
          </div>
        </form>
      </div>
    </div>
  )
}

// Enhanced Professional Wallet Connector
const WalletConnector = () => {
  const { address, isConnected } = useAccount()
  const { connect, connectors, isLoading } = useConnect()
  const { disconnect } = useDisconnect()
  const [showConnectors, setShowConnectors] = useState(false)
  const [ensName, setEnsName] = useState(null)

  // Get ENS name if available
  useEffect(() => {
    if (address && isConnected) {
      walletService.getENSName(address).then(setEnsName)
    }
  }, [address, isConnected])

  if (isConnected) {
    return (
      <div className="flex items-center space-x-3">
        <div className="bg-gradient-to-r from-green-500/20 to-emerald-500/20 border border-green-500/30 rounded-xl px-4 py-2 backdrop-blur-sm">
          <div className="flex items-center space-x-3">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
            <div>
              <div className="text-green-300 text-sm font-medium">
                {ensName || walletService.formatAddress(address)}
              </div>
              <div className="text-green-400/70 text-xs">Connected</div>
            </div>
          </div>
        </div>
        <button
          onClick={() => disconnect()}
          className="text-slate-400 hover:text-red-400 text-sm px-3 py-2 rounded-lg hover:bg-red-500/10 transition-all"
        >
          Disconnect
        </button>
      </div>
    )
  }

  return (
    <div className="relative">
      <button
        onClick={() => setShowConnectors(!showConnectors)}
        className="flex items-center space-x-2 bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white px-6 py-3 rounded-xl transition-all shadow-lg font-medium"
        disabled={isLoading}
      >
        <Wallet className="w-4 h-4" />
        <span>{isLoading ? 'Connecting...' : 'Connect Wallet'}</span>
      </button>

      {showConnectors && (
        <div className="absolute right-0 top-full mt-2 w-72 bg-slate-900/95 backdrop-blur-xl border border-slate-700 rounded-2xl shadow-2xl z-50 p-4">
          <div className="mb-4">
            <h3 className="font-semibold text-white mb-2">Connect Wallet</h3>
            <p className="text-slate-400 text-sm">Choose your preferred wallet to connect</p>
          </div>
          <div className="space-y-2">
            {connectors.map((connector) => (
              <button
                key={connector.id}
                onClick={() => {
                  connect({ connector })
                  setShowConnectors(false)
                }}
                className="w-full flex items-center space-x-3 px-4 py-3 text-slate-300 hover:text-white hover:bg-slate-800/50 rounded-xl transition-all border border-slate-700/50 hover:border-slate-600"
                disabled={!connector.ready}
              >
                <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg flex items-center justify-center">
                  <Wallet className="w-4 h-4 text-white" />
                </div>
                <div className="text-left">
                  <div className="font-medium">{connector.name}</div>
                  <div className="text-xs text-slate-400">
                    {connector.ready ? 'Ready to connect' : 'Not installed'}
                  </div>
                </div>
              </button>
            ))}
          </div>
          <div className="mt-4 p-3 bg-blue-500/10 border border-blue-500/20 rounded-xl">
            <div className="flex items-center space-x-2 mb-1">
              <Shield className="w-4 h-4 text-blue-400" />
              <span className="text-blue-400 text-sm font-medium">Secure Connection</span>
            </div>
            <p className="text-slate-400 text-xs">
              Your wallet connection is encrypted and secure. We never store your private keys.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}

// Trading Interface
const TradingInterface = () => {
  const [fromToken, setFromToken] = useState('ETH')
  const [toToken, setToToken] = useState('USDC')
  const [fromAmount, setFromAmount] = useState('')
  const [slippage, setSlippage] = useState(0.5)

  const tokens = ['ETH', 'BTC', 'SOL', 'UNI', 'USDC', 'USDT']

  const handleSwap = () => {
    setFromToken(toToken)
    setToToken(fromToken)
  }

  return (
    <div className="max-w-md mx-auto">
      <div className="bg-gradient-to-br from-gray-900/90 to-gray-800/90 backdrop-blur-xl rounded-2xl p-6 border border-gray-700/50 shadow-2xl">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <CompactLogo animated={true} />
            <h3 className="text-xl font-bold text-white">Swap</h3>
          </div>
          <Settings className="w-5 h-5 text-gray-400 hover:text-white cursor-pointer transition-colors" />
        </div>

        {/* From Token */}
        <div className="mb-4">
          <div className="flex justify-between items-center mb-2">
            <label className="text-sm font-medium text-gray-300">From</label>
            <span className="text-sm text-gray-400">Balance: 2.5 ETH</span>
          </div>
          <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700">
            <div className="flex items-center space-x-3">
              <select 
                value={fromToken}
                onChange={(e) => setFromToken(e.target.value)}
                className="bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2 focus:ring-2 focus:ring-cyan-400"
              >
                {tokens.map(token => (
                  <option key={token} value={token}>{token}</option>
                ))}
              </select>
              <input
                type="number"
                value={fromAmount}
                onChange={(e) => setFromAmount(e.target.value)}
                placeholder="0.0"
                className="flex-1 bg-transparent text-white text-xl font-medium placeholder-gray-500 focus:outline-none"
              />
            </div>
            <div className="mt-2 text-sm text-gray-400">
              ≈ ${(parseFloat(fromAmount) * (tokenPrices[fromToken]?.price || 0)).toLocaleString()}
            </div>
          </div>
        </div>

        {/* Swap Button */}
        <div className="flex justify-center mb-4">
          <button 
            onClick={handleSwap}
            className="p-3 bg-gradient-to-r from-cyan-500 to-purple-500 hover:from-cyan-600 hover:to-purple-600 rounded-full transition-all shadow-lg transform hover:scale-110"
          >
            <ArrowDown className="w-5 h-5 text-white" />
          </button>
        </div>

        {/* To Token */}
        <div className="mb-6">
          <div className="flex justify-between items-center mb-2">
            <label className="text-sm font-medium text-gray-300">To</label>
            <span className="text-sm text-gray-400">Balance: 1,250 USDC</span>
          </div>
          <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700">
            <div className="flex items-center space-x-3">
              <select 
                value={toToken}
                onChange={(e) => setToToken(e.target.value)}
                className="bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2 focus:ring-2 focus:ring-cyan-400"
              >
                {tokens.map(token => (
                  <option key={token} value={token}>{token}</option>
                ))}
              </select>
              <input
                type="number"
                placeholder="0.0"
                className="flex-1 bg-transparent text-white text-xl font-medium placeholder-gray-500 focus:outline-none"
                readOnly
              />
            </div>
          </div>
        </div>

        {/* Swap Button */}
        <button className="w-full py-4 bg-gradient-to-r from-cyan-500 via-purple-500 to-pink-500 hover:from-cyan-600 hover:via-purple-600 hover:to-pink-600 text-white font-bold rounded-xl transition-all shadow-lg transform hover:scale-105">
          {fromAmount ? `Swap ${fromToken} for ${toToken}` : 'Enter Amount'}
        </button>
      </div>
    </div>
  )
}

// Portfolio Component
const PortfolioComponent = () => {
  const { address, isConnected } = useAccount()

  const portfolioTokens = [
    { symbol: 'ETH', name: 'Ethereum', balance: '2.5', value: '$7,468.55', change: '+5.2%', positive: true },
    { symbol: 'BTC', name: 'Bitcoin', balance: '0.3', value: '$20,367.37', change: '+3.1%', positive: true },
    { symbol: 'SOL', name: 'Solana', balance: '150', value: '$16,300.50', change: '-1.8%', positive: false },
    { symbol: 'UNI', name: 'Uniswap', balance: '45.2', value: '$313.69', change: '+8.3%', positive: true }
  ]

  const totalValue = 44450.11

  return (
    <div className="space-y-6">
      {/* Portfolio Overview */}
      <div className="bg-gradient-to-br from-gray-900/90 to-gray-800/90 backdrop-blur-xl rounded-2xl p-6 border border-gray-700/50">
        <div className="flex items-center space-x-3 mb-6">
          <CompactLogo animated={true} />
          <h3 className="text-2xl font-bold text-white">Portfolio Overview</h3>
        </div>
        
        {isConnected ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="text-4xl font-bold bg-gradient-to-r from-cyan-400 to-purple-500 bg-clip-text text-transparent mb-2">
                ${totalValue.toLocaleString()}
              </div>
              <p className="text-gray-400">Total Portfolio Value</p>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold bg-gradient-to-r from-green-400 to-emerald-500 bg-clip-text text-transparent mb-2">
                +$2,340
              </div>
              <p className="text-gray-400">24h P&L</p>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold bg-gradient-to-r from-yellow-400 to-orange-500 bg-clip-text text-transparent mb-2">
                4
              </div>
              <p className="text-gray-400">Assets</p>
            </div>
          </div>
        ) : (
          <div className="text-center py-12">
            <Wallet className="w-16 h-16 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-400 text-lg mb-4">Connect your wallet to view portfolio</p>
            <WalletConnector />
          </div>
        )}
      </div>

      {/* Token Holdings */}
      {isConnected && (
        <div className="bg-gradient-to-br from-gray-900/90 to-gray-800/90 backdrop-blur-xl rounded-2xl p-6 border border-gray-700/50">
          <div className="flex items-center space-x-3 mb-6">
            <CompactLogo animated={true} />
            <h3 className="text-xl font-bold text-white">Your Assets</h3>
          </div>
          
          <div className="space-y-4">
            {portfolioTokens.map((token, index) => (
              <div key={index} className="flex items-center justify-between p-4 bg-gray-800/30 rounded-xl border border-gray-700 hover:bg-gray-800/50 transition-colors">
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-bold shadow-lg">
                    {token.symbol.slice(0, 2)}
                  </div>
                  <div>
                    <h4 className="font-bold text-white">{token.symbol}</h4>
                    <p className="text-sm text-gray-400">{token.name}</p>
                  </div>
                </div>
                <div className="text-center">
                  <p className="font-bold text-white">{token.balance}</p>
                  <p className="text-sm text-gray-400">{token.symbol}</p>
                </div>
                <div className="text-right">
                  <p className="font-bold text-white">{token.value}</p>
                  <p className={`text-sm font-medium ${token.positive ? 'text-green-400' : 'text-red-400'}`}>
                    {token.change}
                  </p>
                </div>
                <button className="p-2 text-gray-400 hover:text-yellow-400 transition-colors">
                  <Star className="w-5 h-5" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// Professional Dashboard with Real-time Data
const ProfessionalDashboard = () => {
  const { user, logout } = useAuthStore()
  const { address, isConnected } = useAccount()
  const [activeTab, setActiveTab] = useState('overview')
  const [liveData, setLiveData] = useState({
    prices: {},
    marketData: [],
    portfolio: null,
    trending: [],
    defiProtocols: []
  })
  const [isLoading, setIsLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState(new Date())

  // Fetch live market data
  useEffect(() => {
    const fetchMarketData = async () => {
      try {
        setIsLoading(true)
        
        // Fetch multiple data sources simultaneously
        const [prices, marketData, trending, defiProtocols] = await Promise.all([
          priceService.getLivePrices(),
          priceService.getMarketData(1, 20),
          priceService.getTrendingCoins(),
          priceService.getDeFiProtocols()
        ])

        setLiveData(prev => ({
          ...prev,
          prices: prices || {},
          marketData: marketData || [],
          trending: trending || [],
          defiProtocols: defiProtocols || []
        }))

        setLastUpdate(new Date())
      } catch (error) {
        console.error('Error fetching market data:', error)
        toast.error('Failed to fetch market data')
      } finally {
        setIsLoading(false)
      }
    }

    // Fetch wallet portfolio if connected
    const fetchPortfolio = async () => {
      if (address && isConnected) {
        try {
          const portfolio = await walletService.getWalletPortfolio(address)
          setLiveData(prev => ({ ...prev, portfolio }))
        } catch (error) {
          console.error('Error fetching portfolio:', error)
        }
      }
    }

    fetchMarketData()
    fetchPortfolio()

    // Set up real-time updates every 30 seconds
    const interval = setInterval(() => {
      fetchMarketData()
      if (address && isConnected) {
        fetchPortfolio()
      }
    }, 30000)

    return () => clearInterval(interval)
  }, [address, isConnected])

  // Professional Market Overview Panel
  const MarketOverviewPanel = () => (
    <div className="bg-gradient-to-br from-slate-900/95 to-slate-800/95 backdrop-blur-xl rounded-2xl p-6 border border-slate-700/50 shadow-2xl">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-xl flex items-center justify-center">
            <TrendingUp className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-white">Market Overview</h3>
            <p className="text-slate-400 text-sm">Live cryptocurrency data</p>
          </div>
        </div>
        <div className="flex items-center space-x-2 text-xs text-slate-400">
          <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
          <span>Live • {lastUpdate.toLocaleTimeString()}</span>
        </div>
      </div>

      {/* Top Cryptocurrencies */}
      <div className="space-y-3 mb-6">
        {liveData.marketData.slice(0, 8).map((coin, index) => (
          <div key={coin.id} className="flex items-center justify-between p-3 bg-slate-800/50 rounded-xl hover:bg-slate-800/70 transition-all">
            <div className="flex items-center space-x-3">
              <div className="relative">
                <img src={coin.image} alt={coin.name} className="w-8 h-8 rounded-full" />
                <div className="absolute -top-1 -right-1 w-3 h-3 bg-slate-900 rounded-full flex items-center justify-center">
                  <span className="text-xs font-bold text-slate-300">#{index + 1}</span>
                </div>
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <span className="font-semibold text-white">{coin.symbol.toUpperCase()}</span>
                  <span className="text-slate-400 text-sm">{coin.name}</span>
                </div>
                <div className="text-xs text-slate-500">
                  MCap: {priceService.formatMarketCap(coin.market_cap)}
                </div>
              </div>
            </div>
            <div className="text-right">
              <div className="font-bold text-white">
                {priceService.formatPrice(coin.current_price)}
              </div>
              <div className={`text-sm font-medium ${
                coin.price_change_percentage_24h >= 0 ? 'text-green-400' : 'text-red-400'
              }`}>
                {priceService.formatPercentChange(coin.price_change_percentage_24h)}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Market Stats */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-gradient-to-r from-green-500/10 to-emerald-500/10 border border-green-500/20 rounded-xl p-4">
          <div className="flex items-center space-x-2 mb-2">
            <TrendingUp className="w-4 h-4 text-green-400" />
            <span className="text-green-400 text-sm font-medium">24h Gainers</span>
          </div>
          <div className="text-2xl font-bold text-white">
            {liveData.marketData.filter(coin => coin.price_change_percentage_24h > 0).length}
          </div>
        </div>
        <div className="bg-gradient-to-r from-red-500/10 to-pink-500/10 border border-red-500/20 rounded-xl p-4">
          <div className="flex items-center space-x-2 mb-2">
            <ArrowDown className="w-4 h-4 text-red-400" />
            <span className="text-red-400 text-sm font-medium">24h Losers</span>
          </div>
          <div className="text-2xl font-bold text-white">
            {liveData.marketData.filter(coin => coin.price_change_percentage_24h < 0).length}
          </div>
        </div>
      </div>
    </div>
  )

  // Professional Portfolio Panel
  const PortfolioPanel = () => (
    <div className="bg-gradient-to-br from-slate-900/95 to-slate-800/95 backdrop-blur-xl rounded-2xl p-6 border border-slate-700/50 shadow-2xl">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl flex items-center justify-center">
            <Wallet className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-white">Portfolio</h3>
            <p className="text-slate-400 text-sm">
              {isConnected ? walletService.formatAddress(address) : 'Connect wallet to view'}
            </p>
          </div>
        </div>
        {isConnected && (
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
            <span className="text-xs text-green-400 font-medium">Connected</span>
          </div>
        )}
      </div>

      {isConnected && liveData.portfolio ? (
        <div className="space-y-6">
          {/* Portfolio Value */}
          <div className="text-center">
            <div className="text-4xl font-bold bg-gradient-to-r from-cyan-400 to-purple-500 bg-clip-text text-transparent mb-2">
              ${(Math.random() * 50000 + 10000).toLocaleString('en-US', { minimumFractionDigits: 2 })}
            </div>
            <p className="text-slate-400">Total Portfolio Value</p>
            <div className="flex items-center justify-center space-x-4 mt-4">
              <div className="text-center">
                <div className="text-lg font-bold text-green-400">+$2,340</div>
                <div className="text-xs text-slate-400">24h P&L</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-bold text-blue-400">+5.2%</div>
                <div className="text-xs text-slate-400">24h Change</div>
              </div>
            </div>
          </div>

          {/* Chain Balances */}
          <div className="space-y-3">
            <h4 className="text-white font-semibold mb-3">Chain Balances</h4>
            {Object.values(liveData.portfolio.chains).map((chain) => (
              <div key={chain.chainId} className="flex items-center justify-between p-3 bg-slate-800/50 rounded-xl">
                <div className="flex items-center space-x-3">
                  <div 
                    className="w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-bold"
                    style={{ backgroundColor: chain.color }}
                  >
                    {chain.symbol.slice(0, 2)}
                  </div>
                  <div>
                    <div className="font-medium text-white">{chain.name}</div>
                    <div className="text-xs text-slate-400">{chain.symbol}</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-bold text-white">
                    {parseFloat(chain.nativeBalance).toFixed(4)} {chain.symbol}
                  </div>
                  <div className="text-xs text-slate-400">
                    ${(parseFloat(chain.nativeBalance) * (liveData.prices.ethereum?.usd || 0)).toFixed(2)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="text-center py-12">
          <Wallet className="w-16 h-16 text-slate-600 mx-auto mb-4" />
          <p className="text-slate-400 text-lg mb-4">Connect your wallet to view portfolio</p>
          <WalletConnector />
        </div>
      )}
    </div>
  )

  // AI Trading Agent Panel
  const AIAgentPanel = () => (
    <div className="bg-gradient-to-br from-slate-900/95 to-slate-800/95 backdrop-blur-xl rounded-2xl p-6 border border-slate-700/50 shadow-2xl">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-gradient-to-r from-orange-500 to-red-500 rounded-xl flex items-center justify-center">
            <Brain className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-white">AI Trading Agent</h3>
            <p className="text-slate-400 text-sm">Autonomous trading system</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
          <span className="text-xs text-green-400 font-medium">Active</span>
        </div>
      </div>

      {/* AI Status Metrics */}
      <div className="space-y-4 mb-6">
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-gradient-to-r from-blue-500/10 to-cyan-500/10 border border-blue-500/20 rounded-xl p-4">
            <div className="flex items-center space-x-2 mb-2">
              <Target className="w-4 h-4 text-blue-400" />
              <span className="text-blue-400 text-sm font-medium">Success Rate</span>
            </div>
            <div className="text-2xl font-bold text-white">94.2%</div>
          </div>
          <div className="bg-gradient-to-r from-green-500/10 to-emerald-500/10 border border-green-500/20 rounded-xl p-4">
            <div className="flex items-center space-x-2 mb-2">
              <DollarSign className="w-4 h-4 text-green-400" />
              <span className="text-green-400 text-sm font-medium">Total Profit</span>
            </div>
            <div className="text-2xl font-bold text-white">$12,847</div>
          </div>
        </div>

        <div className="bg-slate-800/50 rounded-xl p-4">
          <div className="flex items-center justify-between mb-3">
            <span className="text-slate-300 text-sm">Current Strategy</span>
            <span className="text-cyan-400 font-medium">Dynamic Arbitrage</span>
          </div>
          <div className="flex items-center justify-between mb-3">
            <span className="text-slate-300 text-sm">Risk Level</span>
            <span className="text-yellow-400 font-medium">Medium (7/10)</span>
          </div>
          <div className="flex items-center justify-between mb-3">
            <span className="text-slate-300 text-sm">Active Positions</span>
            <span className="text-white font-medium">3</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-300 text-sm">Uptime</span>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-400 rounded-full"></div>
              <span className="text-green-400 font-medium">99.8%</span>
            </div>
          </div>
        </div>
      </div>

      {/* AI Performance Chart */}
      <div className="mb-6">
        <h4 className="text-white font-semibold mb-3">Performance Trend</h4>
        <div className="h-32">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={Array.from({ length: 24 }, (_, i) => ({
              time: `${i}:00`,
              profit: 1000 + Math.sin(i * 0.5) * 200 + Math.random() * 100
            }))}>
              <defs>
                <linearGradient id="aiGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10B981" stopOpacity={0.4}/>
                  <stop offset="95%" stopColor="#10B981" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <XAxis dataKey="time" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: '#64748B' }} />
              <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: '#64748B' }} />
              <Tooltip 
                contentStyle={{
                  backgroundColor: 'rgba(15, 23, 42, 0.9)',
                  border: '1px solid #334155',
                  borderRadius: '12px',
                  color: 'white'
                }}
              />
              <Area 
                type="monotone" 
                dataKey="profit" 
                stroke="#10B981" 
                strokeWidth={2}
                fill="url(#aiGradient)" 
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Control Buttons */}
      <div className="grid grid-cols-2 gap-3">
        <button className="py-3 bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white font-semibold rounded-xl transition-all shadow-lg">
          Configure Agent
        </button>
        <button className="py-3 bg-slate-700 hover:bg-slate-600 text-white font-semibold rounded-xl transition-all border border-slate-600">
          View Logs
        </button>
      </div>
    </div>
  )

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800 relative overflow-hidden">
      {/* Professional Background */}
      <div className="absolute inset-0">
        {/* Subtle Grid Pattern */}
        <div className="absolute inset-0 opacity-5">
          <svg width="100%" height="100%">
            <defs>
              <pattern id="professionalGrid" width="40" height="40" patternUnits="userSpaceOnUse">
                <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#0EA5E9" strokeWidth="1"/>
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#professionalGrid)" />
          </svg>
        </div>
        
        {/* Ambient Glow Effects */}
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl"></div>
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl"></div>
      </div>

      {/* Header */}
      <header className="relative bg-slate-900/80 backdrop-blur-xl border-b border-slate-700/50 shadow-2xl">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-4">
              <CrossFlowLogo size="medium" animated={true} />
              <div className="text-xs text-green-400 bg-green-400/10 px-3 py-1 rounded-full border border-green-400/30 animate-pulse">
                ✅ LIVE DATA
              </div>
            </div>

            <div className="flex items-center space-x-6">
              <div className="flex items-center space-x-4 text-sm text-slate-400">
                <div className="flex items-center space-x-2">
                  <Globe className="w-4 h-4" />
                  <span>6 Networks</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Database className="w-4 h-4" />
                  <span>Live Prices</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Shield className="w-4 h-4" />
                  <span>Secure</span>
                </div>
              </div>
              <WalletConnector />
              <button
                onClick={logout}
                className="flex items-center space-x-2 text-slate-300 hover:text-white px-4 py-2 rounded-xl hover:bg-red-500/20 transition-all border border-red-400/30 hover:border-red-400/50"
              >
                <LogOut className="w-4 h-4" />
                <span>Logout</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Dashboard */}
      <main className="relative max-w-7xl mx-auto px-6 py-8">
        {/* Dashboard Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold mb-2">
            <span className="bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">CrossFlow AI</span>
          </h1>
          <p className="text-slate-400">Professional Cross-Chain DeFi Trading Platform</p>
          {isLoading && (
            <div className="flex items-center justify-center space-x-2 mt-4">
              <RefreshCw className="w-4 h-4 text-blue-400 animate-spin" />
              <span className="text-blue-400 text-sm">Loading live data...</span>
            </div>
          )}
        </div>

        {/* Dashboard Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <MarketOverviewPanel />
          <PortfolioPanel />
          <AIAgentPanel />
        </div>

        {/* Additional Features Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-8">
          {/* DeFi Protocols */}
          <div className="bg-gradient-to-br from-slate-900/95 to-slate-800/95 backdrop-blur-xl rounded-2xl p-6 border border-slate-700/50 shadow-2xl">
            <div className="flex items-center space-x-3 mb-6">
              <div className="w-10 h-10 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-xl flex items-center justify-center">
                <Layers className="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-white">DeFi Protocols</h3>
                <p className="text-slate-400 text-sm">Top performing protocols</p>
              </div>
            </div>
            
            <div className="space-y-3">
              {liveData.defiProtocols.slice(0, 5).map((protocol, index) => (
                <div key={protocol.id} className="flex items-center justify-between p-3 bg-slate-800/50 rounded-xl hover:bg-slate-800/70 transition-all">
                  <div className="flex items-center space-x-3">
                    <img src={protocol.image} alt={protocol.name} className="w-8 h-8 rounded-full" />
                    <div>
                      <div className="font-medium text-white">{protocol.name}</div>
                      <div className="text-xs text-slate-400">{protocol.symbol.toUpperCase()}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-bold text-white">
                      {priceService.formatPrice(protocol.current_price)}
                    </div>
                    <div className={`text-sm font-medium ${
                      protocol.price_change_percentage_24h >= 0 ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {priceService.formatPercentChange(protocol.price_change_percentage_24h)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Trending Coins */}
          <div className="bg-gradient-to-br from-slate-900/95 to-slate-800/95 backdrop-blur-xl rounded-2xl p-6 border border-slate-700/50 shadow-2xl">
            <div className="flex items-center space-x-3 mb-6">
              <div className="w-10 h-10 bg-gradient-to-r from-pink-500 to-rose-500 rounded-xl flex items-center justify-center">
                <TrendingUp className="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-white">Trending Now</h3>
                <p className="text-slate-400 text-sm">Most searched coins</p>
              </div>
            </div>
            
            <div className="space-y-3">
              {liveData.trending.slice(0, 5).map((coin, index) => (
                <div key={coin.item.id} className="flex items-center justify-between p-3 bg-slate-800/50 rounded-xl hover:bg-slate-800/70 transition-all">
                  <div className="flex items-center space-x-3">
                    <div className="relative">
                      <img src={coin.item.small} alt={coin.item.name} className="w-8 h-8 rounded-full" />
                      <div className="absolute -top-1 -right-1 w-4 h-4 bg-orange-500 rounded-full flex items-center justify-center">
                        <span className="text-xs font-bold text-white">🔥</span>
                      </div>
                    </div>
                    <div>
                      <div className="font-medium text-white">{coin.item.name}</div>
                      <div className="text-xs text-slate-400">{coin.item.symbol}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium text-orange-400">
                      Rank #{coin.item.market_cap_rank}
                    </div>
                    <div className="text-xs text-slate-400">Trending</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
  const { user, logout } = useAuthStore()
  const { address, isConnected } = useAccount()
  const [activeTab, setActiveTab] = useState('overview')

  const renderContent = () => {
    switch (activeTab) {
      case 'trading':
        return <TradingInterface />
      case 'portfolio':
        return <PortfolioComponent />
      case 'analytics':
        return (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-gradient-to-br from-gray-900/90 to-gray-800/90 backdrop-blur-xl rounded-2xl p-6 border border-gray-700/50">
              <h3 className="text-xl font-bold text-white mb-4">📈 Portfolio Performance</h3>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={portfolioData}>
                  <defs>
                    <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#06B6D4" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#8B5CF6" stopOpacity={0.1}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="time" stroke="#9CA3AF" />
                  <YAxis stroke="#9CA3AF" tickFormatter={(value) => `$${value.toLocaleString()}`} />
                  <Tooltip 
                    contentStyle={{
                      backgroundColor: 'rgba(17, 24, 39, 0.9)',
                      border: '1px solid #374151',
                      borderRadius: '12px',
                      color: 'white'
                    }}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="value" 
                    stroke="#06B6D4" 
                    strokeWidth={3}
                    fill="url(#colorValue)" 
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
            
            <div className="bg-gradient-to-br from-gray-900/90 to-gray-800/90 backdrop-blur-xl rounded-2xl p-6 border border-gray-700/50">
              <h3 className="text-xl font-bold text-white mb-4">📊 Trading Volume</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={portfolioData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="time" stroke="#9CA3AF" />
                  <YAxis stroke="#9CA3AF" />
                  <Tooltip 
                    contentStyle={{
                      backgroundColor: 'rgba(17, 24, 39, 0.9)',
                      border: '1px solid #374151',
                      borderRadius: '12px',
                      color: 'white'
                    }}
                  />
                  <Bar dataKey="volume" fill="#8B5CF6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )
      default:
        return (
          <div className="min-h-screen bg-gradient-to-br from-blue-900 via-indigo-900 to-purple-900 relative overflow-hidden">
            {/* Starfield Background */}
            <div className="absolute inset-0">
              {[...Array(50)].map((_, i) => (
                <div
                  key={i}
                  className="absolute w-1 h-1 bg-cyan-400 rounded-full animate-pulse"
                  style={{
                    left: `${Math.random() * 100}%`,
                    top: `${Math.random() * 100}%`,
                    animationDelay: `${Math.random() * 3}s`,
                    opacity: Math.random() * 0.8 + 0.2
                  }}
                />
              ))}
            </div>

            {/* Main Content */}
            <div className="relative z-10 p-8">
              {/* Header Logo */}
              <div className="flex justify-center mb-12">
                <CrossFlowLogo size="xxl" showText={true} animated={true} />
              </div>

              {/* Dashboard Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 max-w-7xl mx-auto">
                
                {/* Trade Activity Panel */}
                <div className="bg-gray-900/80 backdrop-blur-xl rounded-2xl p-6 border border-cyan-400/30">
                  <h3 className="text-xl font-bold text-white mb-2">Trade Activity</h3>
                  <p className="text-gray-400 text-sm mb-6">Daily Volume</p>
                  
                  {/* Volume Chart */}
                  <div className="h-32 mb-6">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={portfolioData.slice(-12)}>
                        <defs>
                          <linearGradient id="volumeGradient" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#00D4FF" stopOpacity={0.4}/>
                            <stop offset="95%" stopColor="#00D4FF" stopOpacity={0}/>
                          </linearGradient>
                        </defs>
                        <XAxis dataKey="time" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: '#6B7280' }} />
                        <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: '#6B7280' }} />
                        <Area 
                          type="monotone" 
                          dataKey="volume" 
                          stroke="#00D4FF" 
                          strokeWidth={2}
                          fill="url(#volumeGradient)" 
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                  
                  {/* Daily Volume Stats */}
                  <div className="mb-6">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-gray-400 text-sm">Daily Volume</span>
                      <span className="text-cyan-400 font-semibold">SOL 511.3%</span>
                    </div>
                  </div>
                  
                  {/* Trading Pairs List */}
                  <div className="space-y-3">
                    {[
                      { icon: '🟢', pair: 'ETH/USDC', value: '45.5.53%', positive: true },
                      { icon: '💎', pair: 'ETH/USC', value: '222.00.005', neutral: true },
                      { icon: '🔵', pair: 'BTC/UST', value: '37.05%', positive: true },
                      { icon: '🟣', pair: 'SOL/DAI', value: '-5.2.93%', negative: true },
                      { icon: '🔷', pair: 'DMAI/Chain', value: '123.2.99%', positive: true },
                      { icon: '🟠', pair: 'Binance Smart Chain', value: '45.6%', positive: true },
                      { icon: '🟣', pair: 'SOL/DAI', value: '-10.030.025', negative: true },
                      { icon: '🟣', pair: 'Solana', value: '-53.00%', negative: true },
                      { icon: '🔷', pair: 'Ethereum', value: '42.3%', positive: true }
                    ].map((item, index) => (
                      <div key={index} className="flex items-center justify-between py-1">
                        <div className="flex items-center space-x-3">
                          <span className="text-sm">{item.icon}</span>
                          <span className="text-gray-300 text-sm">{item.pair}</span>
                        </div>
                        <span className={`text-sm font-medium ${
                          item.positive ? 'text-green-400' : 
                          item.negative ? 'text-red-400' : 'text-blue-400'
                        }`}>
                          {item.value}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Portfolio Overview Panel */}
                <div className="bg-gray-900/80 backdrop-blur-xl rounded-2xl p-6 border border-cyan-400/30">
                  <h3 className="text-xl font-bold text-white mb-2">Portfolio Overview</h3>
                  <div className="text-3xl font-bold text-white mb-8">$1,250,000 USD</div>
                  
                  {/* Main Circular Chart */}
                  <div className="flex justify-center mb-8">
                    <div className="relative w-48 h-48">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={[
                              { name: 'Ethereum', value: 30, color: '#627EEA' },
                              { name: 'Polygon', value: 45, color: '#8247E5' },
                              { name: 'Solana', value: 25, color: '#00D4FF' }
                            ]}
                            cx="50%"
                            cy="50%"
                            innerRadius={65}
                            outerRadius={90}
                            startAngle={90}
                            endAngle={450}
                            dataKey="value"
                          >
                            {[
                              { name: 'Ethereum', value: 30, color: '#627EEA' },
                              { name: 'Polygon', value: 45, color: '#8247E5' },
                              { name: 'Solana', value: 25, color: '#00D4FF' }
                            ].map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={entry.color} />
                            ))}
                          </Pie>
                        </PieChart>
                      </ResponsiveContainer>
                      
                      {/* Center Percentage */}
                      <div className="absolute inset-0 flex items-center justify-center">
                        <div className="text-center">
                          <div className="text-4xl font-bold text-white">3.7%</div>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  {/* Portfolio Labels */}
                  <div className="grid grid-cols-2 gap-4 text-sm mb-8">
                    <div className="text-right">
                      <div className="text-gray-400">Ethereum</div>
                      <div className="text-white font-semibold">30%</div>
                    </div>
                    <div className="text-left">
                      <div className="text-gray-400">Polygon</div>
                      <div className="text-white font-semibold">45%</div>
                    </div>
                    <div className="text-right">
                      <div className="text-gray-400">Polygon</div>
                      <div className="text-white font-semibold">24%</div>
                    </div>
                    <div className="text-left">
                      <div className="text-gray-400">Solana</div>
                      <div className="text-white font-semibold">25%</div>
                    </div>
                  </div>
                  
                  {/* Secondary Portfolio Chart */}
                  <div>
                    <h4 className="text-white font-semibold mb-4">Portfolio Overview</h4>
                    <div className="flex justify-center">
                      <div className="relative w-24 h-24">
                        <ResponsiveContainer width="100%" height="100%">
                          <PieChart>
                            <Pie
                              data={[
                                { name: 'DeFi Protocols', value: 22, color: '#00D4FF' },
                                { name: 'Moderate', value: 59, color: '#10B981' },
                                { name: 'Stable', value: 65, color: '#3B82F6' }
                              ]}
                              cx="50%"
                              cy="50%"
                              innerRadius={25}
                              outerRadius={45}
                              dataKey="value"
                            >
                              {[
                                { name: 'DeFi Protocols', value: 22, color: '#00D4FF' },
                                { name: 'Moderate', value: 59, color: '#10B981' },
                                { name: 'Stable', value: 65, color: '#3B82F6' }
                              ].map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={entry.color} />
                              ))}
                            </Pie>
                          </PieChart>
                        </ResponsiveContainer>
                        <div className="absolute inset-0 flex items-center justify-center">
                          <div className="text-xl font-bold text-white">5%</div>
                        </div>
                      </div>
                    </div>
                    
                    {/* Small Chart Labels */}
                    <div className="grid grid-cols-3 gap-2 text-xs mt-4">
                      <div className="text-center">
                        <div className="text-gray-400">DeFi Protocols</div>
                        <div className="text-white">22%</div>
                      </div>
                      <div className="text-center">
                        <div className="text-gray-400">Moderate</div>
                        <div className="text-white">59%</div>
                      </div>
                      <div className="text-center">
                        <div className="text-gray-400">Stable</div>
                        <div className="text-white">65%</div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* AI Agent Status Panel */}
                <div className="bg-gray-900/80 backdrop-blur-xl rounded-2xl p-6 border border-cyan-400/30">
                  <h3 className="text-xl font-bold text-white mb-2">AI Agent Status</h3>
                  <p className="text-cyan-400 text-sm mb-6">Scheme Gerant</p>
                  
                  {/* Status Metrics */}
                  <div className="space-y-4 mb-8">
                    <div className="flex justify-between items-center">
                      <span className="text-gray-400 text-sm">Current Strategy: Dynamic AMM</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-400 text-sm">Risk Level:</span>
                      <span className="text-white font-bold text-xl">9%</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-400 text-sm">Uptime: 99.8%</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-400 text-sm">Uptime</span>
                      <div className="w-8 h-8 bg-cyan-400/20 rounded-full flex items-center justify-center border border-cyan-400/50">
                        <div className="w-4 h-4 bg-cyan-400 rounded-full animate-pulse"></div>
                      </div>
                    </div>
                  </div>
                  
                  {/* AI Performance Section */}
                  <div className="mb-8">
                    <h4 className="text-white font-semibold mb-2">AI gent Status</h4>
                    <div className="mb-2">
                      <span className="text-gray-400 text-sm">Performance Trend</span>
                    </div>
                    <div className="text-cyan-400 text-sm mb-4">19.8.5 Moelert</div>
                    
                    {/* Performance Chart */}
                    <div className="h-20 mb-4">
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={portfolioData.slice(-10)}>
                          <defs>
                            <linearGradient id="aiGradient" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#10B981" stopOpacity={0.4}/>
                              <stop offset="95%" stopColor="#10B981" stopOpacity={0}/>
                            </linearGradient>
                          </defs>
                          <Area 
                            type="monotone" 
                            dataKey="value" 
                            stroke="#10B981" 
                            strokeWidth={2}
                            fill="url(#aiGradient)" 
                          />
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                  
                  {/* Configure Button */}
                  <button className="w-full py-3 bg-transparent border-2 border-cyan-400 text-cyan-400 font-bold rounded-xl hover:bg-cyan-400/10 transition-all">
                    CONFIGURE AGENT
                  </button>
                </div>
              </div>
            </div>
          </div>
        )
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-indigo-900 relative overflow-hidden">
      {/* Enhanced Animated Background */}
      <div className="absolute inset-0 overflow-hidden">
        {/* Large Gradient Orbs */}
        <div className="absolute -top-40 -right-40 w-96 h-96 bg-gradient-to-r from-purple-500/30 to-pink-500/30 rounded-full mix-blend-multiply filter blur-3xl animate-pulse"></div>
        <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-gradient-to-r from-cyan-500/30 to-blue-500/30 rounded-full mix-blend-multiply filter blur-3xl animate-pulse" style={{ animationDelay: '1s' }}></div>
        <div className="absolute top-1/2 left-1/2 w-96 h-96 bg-gradient-to-r from-orange-400/20 to-red-500/20 rounded-full mix-blend-multiply filter blur-3xl animate-pulse" style={{ animationDelay: '2s' }}></div>
        
        {/* Circuit Grid Pattern */}
        <div className="absolute inset-0 opacity-5">
          <svg width="100%" height="100%">
            <defs>
              <pattern id="grid" width="50" height="50" patternUnits="userSpaceOnUse">
                <path d="M 50 0 L 0 0 0 50" fill="none" stroke="#00D4FF" strokeWidth="1"/>
                <circle cx="25" cy="25" r="2" fill="#FF00FF"/>
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid)" />
          </svg>
        </div>
        
        {/* Floating Data Particles */}
        {[...Array(15)].map((_, i) => (
          <div
            key={i}
            className="absolute w-1 h-1 rounded-full animate-ping"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              backgroundColor: ['#00D4FF', '#8B5CF6', '#FF00FF', '#F59E0B', '#10B981'][Math.floor(Math.random() * 5)],
              animationDelay: `${Math.random() * 3}s`,
              animationDuration: `${1 + Math.random() * 2}s`
            }}
          />
        ))}
      </div>

      {/* Header */}
      <header className="relative bg-black/30 backdrop-blur-2xl border-b border-cyan-400/30 shadow-2xl">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-20">
            <div className="flex items-center space-x-4">
              {/* Enhanced Logo */}
              <CrossFlowLogo size="medium" animated={true} />
              <div className="text-xs text-green-400 bg-green-400/10 px-2 py-1 rounded-full border border-green-400/30 animate-pulse">
                ✅ UPDATED
              </div>
            </div>

            <div className="flex items-center space-x-6">
              <WalletConnector />
              <button
                onClick={logout}
                className="flex items-center space-x-2 text-gray-300 hover:text-white px-4 py-2 rounded-xl hover:bg-red-500/20 transition-all border border-red-400/30 hover:border-red-400/50"
              >
                <LogOut className="w-4 h-4" />
                <span>Logout</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="relative bg-black/20 backdrop-blur-xl border-b border-purple-400/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {[
              { id: 'overview', name: 'Overview', icon: Home, color: 'cyan' },
              { id: 'trading', name: 'Swap', icon: ArrowLeftRight, color: 'purple' },
              { id: 'portfolio', name: 'Portfolio', icon: Wallet, color: 'pink' },
              { id: 'analytics', name: 'Analytics', icon: BarChart3, color: 'orange' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 py-4 px-4 border-b-3 font-medium text-sm transition-all relative group ${
                  activeTab === tab.id
                    ? `border-${tab.color}-400 text-${tab.color}-400 bg-${tab.color}-500/10`
                    : 'border-transparent text-gray-400 hover:text-white hover:border-gray-600'
                }`}
              >
                <tab.icon className={`w-4 h-4 ${activeTab === tab.id ? `text-${tab.color}-400` : ''}`} />
                <span>{tab.name}</span>
                {activeTab === tab.id && (
                  <div className={`absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-${tab.color}-400 to-${tab.color}-600 animate-pulse`}></div>
                )}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Message */}
        <div className="mb-8 text-center">
          <div className="flex items-center justify-center space-x-4 mb-6">
            <CrossFlowLogo size="large" animated={true} showText={false} />
          </div>
          
          {/* Main Logo Display */}
          <div className="mb-8">
            <div className="flex justify-center mb-4">
              <div className="w-32 h-32 relative">
                {/* Outer Glow Ring */}
                <div className="absolute inset-0 rounded-full border-2 border-cyan-400 animate-pulse shadow-2xl shadow-cyan-400/50"></div>
                
                {/* Inner Logo */}
                <div className="absolute inset-2 rounded-full bg-gradient-to-br from-gray-900 to-blue-900 flex items-center justify-center">
                  {/* Infinity Cross Pattern */}
                  <svg viewBox="0 0 100 100" className="w-20 h-20">
                    <defs>
                      <linearGradient id="logoGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stopColor="#00D4FF" />
                        <stop offset="50%" stopColor="#0EA5E9" />
                        <stop offset="100%" stopColor="#06B6D4" />
                      </linearGradient>
                    </defs>
                    {/* Infinity Cross Design */}
                    <path d="M20,30 Q30,20 40,30 Q50,40 60,30 Q70,20 80,30 Q70,40 60,50 Q50,60 40,50 Q30,40 20,30 Z" 
                          fill="none" stroke="url(#logoGradient)" strokeWidth="2"/>
                    <path d="M30,20 Q40,30 50,20 Q60,10 70,20 Q60,30 50,40 Q40,50 30,40 Q20,30 30,20 Z" 
                          fill="none" stroke="url(#logoGradient)" strokeWidth="2" opacity="0.7"/>
                    <circle cx="50" cy="35" r="8" fill="none" stroke="url(#logoGradient)" strokeWidth="1.5"/>
                  </svg>
                </div>
              </div>
            </div>
            
            <h1 className="text-5xl font-bold mb-2">
              <span className="bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">CROSSFLOW</span>
              <span className="text-cyan-400">.</span>
            </h1>
            <div className="text-2xl font-bold text-cyan-400 mb-2">AI</div>
            <p className="text-gray-400 text-sm tracking-wider">POWERED CROSS-CHAIN DEFI TRADING AGENT</p>
            <div className="text-xs text-green-400 mt-2 animate-pulse">🔄 LIVE UPDATE - {new Date().toLocaleTimeString()}</div>
          </div>
        </div>

        {/* Dashboard Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Trade Activity Panel */}
          <div className="bg-gray-800/50 backdrop-blur-xl rounded-2xl p-6 border border-gray-700/50">
            <h3 className="text-xl font-bold text-white mb-4">Trade Activity</h3>
            <p className="text-gray-400 text-sm mb-4">Daily Volume</p>
            
            {/* Mini Chart */}
            <div className="h-32 mb-4">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={portfolioData.slice(-10)}>
                  <defs>
                    <linearGradient id="tradeGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#00D4FF" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#00D4FF" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <Area 
                    type="monotone" 
                    dataKey="volume" 
                    stroke="#00D4FF" 
                    strokeWidth={2}
                    fill="url(#tradeGradient)" 
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
            
            {/* Trading Pairs */}
            <div className="space-y-3">
              {[
                { pair: 'ETH/USDC', change: '+5.53%', positive: true },
                { pair: 'ETH/USC', change: '222.00.005', neutral: true },
                { pair: 'BTC/UST', change: '37.05%', positive: true },
                { pair: 'SOL/DAI', change: '-5.2.93%', positive: false },
                { pair: 'DMAI/Chain', change: '123.2.99%', positive: true },
                { pair: 'Binance Smart Chain', change: '45.6%', positive: true },
                { pair: 'SOL/DAI', change: '-10.030.025', positive: false },
                { pair: 'Solana', change: '-53.00%', positive: false },
                { pair: 'Ethereum', change: '42.3%', positive: true }
              ].map((item, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className={`w-2 h-2 rounded-full ${
                      item.positive ? 'bg-green-400' : item.neutral ? 'bg-blue-400' : 'bg-red-400'
                    }`}></div>
                    <span className="text-gray-300 text-sm">{item.pair}</span>
                  </div>
                  <span className={`text-sm font-medium ${
                    item.positive ? 'text-green-400' : item.neutral ? 'text-blue-400' : 'text-red-400'
                  }`}>
                    {item.change}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Portfolio Overview Panel */}
          <div className="bg-gray-800/50 backdrop-blur-xl rounded-2xl p-6 border border-gray-700/50">
            <h3 className="text-xl font-bold text-white mb-2">Portfolio Overview</h3>
            <div className="text-3xl font-bold text-white mb-6">$1,250,000 USD</div>
            
            {/* Circular Chart */}
            <div className="flex justify-center mb-6">
              <div className="relative w-48 h-48">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={[
                        { name: 'Ethereum', value: 30, color: '#627EEA' },
                        { name: 'Polygon', value: 45, color: '#8247E5' },
                        { name: 'Solana', value: 25, color: '#00D4FF' }
                      ]}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={90}
                      startAngle={90}
                      endAngle={450}
                      dataKey="value"
                    >
                      {[
                        { name: 'Ethereum', value: 30, color: '#627EEA' },
                        { name: 'Polygon', value: 45, color: '#8247E5' },
                        { name: 'Solana', value: 25, color: '#00D4FF' }
                      ].map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
                
                {/* Center Text */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-white">3.7%</div>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Legend */}
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <div className="flex items-center space-x-2 mb-1">
                  <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                  <span className="text-gray-300">Ethereum</span>
                </div>
                <div className="text-gray-400">30%</div>
              </div>
              <div>
                <div className="flex items-center space-x-2 mb-1">
                  <div className="w-3 h-3 bg-cyan-400 rounded-full"></div>
                  <span className="text-gray-300">Polygon</span>
                </div>
                <div className="text-gray-400">45%</div>
              </div>
            </div>
            
            {/* Additional Portfolio Chart */}
            <div className="mt-6">
              <h4 className="text-white font-semibold mb-3">Portfolio Overview</h4>
              <div className="relative w-24 h-24 mx-auto">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={[
                        { name: 'DeFi Protocols', value: 22, color: '#00D4FF' },
                        { name: 'Moderate', value: 59, color: '#0EA5E9' },
                        { name: 'Stable', value: 65, color: '#06B6D4' }
                      ]}
                      cx="50%"
                      cy="50%"
                      innerRadius={25}
                      outerRadius={45}
                      dataKey="value"
                    >
                      {[
                        { name: 'DeFi Protocols', value: 22, color: '#00D4FF' },
                        { name: 'Moderate', value: 59, color: '#0EA5E9' },
                        { name: 'Stable', value: 65, color: '#06B6D4' }
                      ].map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="text-xl font-bold text-white">5%</div>
                </div>
              </div>
            </div>
          </div>

          {/* AI Agent Status Panel */}
          <div className="bg-gray-800/50 backdrop-blur-xl rounded-2xl p-6 border border-gray-700/50">
            <h3 className="text-xl font-bold text-white mb-4">AI Agent Status</h3>
            <p className="text-cyan-400 text-sm mb-4">Scheme Gerant</p>
            
            <div className="space-y-4 mb-6">
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-gray-300 text-sm">Current Strategy: Dynamic AMM</span>
                </div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-gray-300 text-sm">Risk Level:</span>
                  <span className="text-white font-semibold">9%</span>
                </div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-gray-300 text-sm">Uptime: 99.8%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-300 text-sm">Uptime</span>
                  <div className="w-8 h-8 bg-cyan-400/20 rounded-full flex items-center justify-center">
                    <div className="w-4 h-4 bg-cyan-400 rounded-full"></div>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="mb-6">
              <h4 className="text-white font-semibold mb-3">AI gent Status</h4>
              <div className="mb-2">
                <span className="text-gray-300 text-sm">Performance Trend</span>
              </div>
              <div className="text-cyan-400 text-sm mb-3">19.8.5 Moelert</div>
              
              {/* Performance Chart */}
              <div className="h-16">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={portfolioData.slice(-8)}>
                    <defs>
                      <linearGradient id="performanceGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#00D4FF" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#00D4FF" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <Area 
                      type="monotone" 
                      dataKey="value" 
                      stroke="#00D4FF" 
                      strokeWidth={2}
                      fill="url(#performanceGradient)" 
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
            
            {/* Configure Button */}
            <button className="w-full py-3 bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-400/50 text-cyan-400 font-semibold rounded-xl transition-all">
              CONFIGURE AGENT
            </button>
          </div>
        </div>

        {renderContent()}
      </main>
    </div>
  )
}

function App() {
  const { initializeAuth, isAuthenticated, isLoading } = useAuthStore()

  useEffect(() => {
    initializeAuth()
  }, [initializeAuth])

  // Show loading screen while initializing
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-indigo-900 flex items-center justify-center">
        <LoadingLogo />
      </div>
    )
  }

  return (
    <Routes>
      <Route 
        path="/login" 
        element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <LoginPage />} 
      />
      <Route 
        path="/dashboard" 
        element={isAuthenticated ? <ProfessionalDashboard /> : <Navigate to="/login" replace />} 
      />
      <Route path="*" element={<Navigate to={isAuthenticated ? "/dashboard" : "/login"} replace />} />
    </Routes>
  )
}

export default App