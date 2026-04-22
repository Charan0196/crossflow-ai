import React, { useEffect, useState } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './stores/authStore'
import { useAccount, useConnect, useDisconnect } from 'wagmi'
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

// Enhanced Professional Wallet Connector - Updated Design
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
        <div className="flex items-center gap-2 bg-green-400/10 border border-green-400/30 px-4 py-2 rounded-full">
          <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
          <span className="text-green-400 text-sm font-medium">
            {ensName || walletService.formatAddress(address)}
          </span>
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
        className="flex items-center gap-2 bg-cyan-500 hover:bg-cyan-400 transition-colors px-6 py-2 rounded-full font-semibold text-black"
        disabled={isLoading}
      >
        <Wallet size={18} />
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

// Professional Dashboard with Real-time Data - Updated Design
const ProfessionalDashboard = () => {
  const { user, logout } = useAuthStore()
  const { address, isConnected } = useAccount()
  const [liveData, setLiveData] = useState({
    prices: {},
    marketData: [],
    portfolio: null,
    trending: [],
    defiProtocols: []
  })
  const [isLoading, setIsLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState(new Date())
  const [timeframe, setTimeframe] = useState('24H')

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

  // Generate chart data from live market data
  const generateChartData = () => {
    if (liveData.marketData.length > 0) {
      return liveData.marketData.slice(0, 10).map((coin, index) => ({
        name: index.toString(),
        value: coin.current_price,
        volume: coin.total_volume
      }))
    }
    // Fallback data
    return Array.from({ length: 24 }, (_, i) => ({
      name: i.toString(),
      value: 32000 + Math.sin(i * 0.5) * 2000 + Math.random() * 1000,
      volume: 50000 + Math.random() * 30000
    }))
  }

  const chartData = generateChartData()

  return (
    <div className="min-h-screen bg-[#050b1a] text-slate-100 p-6 font-sans">
      {/* Navigation */}
      <nav className="flex justify-between items-center mb-10 bg-slate-900/50 p-4 rounded-2xl border border-slate-800 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-cyan-400 to-blue-600 rounded-lg flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <Zap size={24} className="text-white" />
          </div>
          <span className="text-xl font-bold tracking-tight">
            CROSSFLOW <span className="text-cyan-400">AI</span>
          </span>
          <div className="flex items-center space-x-2 ml-4">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
            <span className="text-xs text-green-400 font-medium">LIVE DATA</span>
          </div>
        </div>
        
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-4 text-sm text-slate-400">
            <div className="flex items-center space-x-2">
              <Globe className="w-4 h-4" />
              <span>6 Networks</span>
            </div>
            <div className="flex items-center space-x-2">
              <Database className="w-4 h-4" />
              <span>Live Prices</span>
            </div>
          </div>
          <WalletConnector />
          <button
            onClick={logout}
            className="flex items-center gap-2 text-slate-400 hover:text-white px-4 py-2 rounded-lg hover:bg-red-500/20 transition-all"
          >
            <LogOut size={16} />
            Logout
          </button>
        </div>
      </nav>

      <div className="grid grid-cols-12 gap-6">
        {/* Left Panel: Agent Status */}
        <div className="col-span-12 lg:col-span-4 space-y-6">
          {/* AI Agent Status */}
          <div className="bg-slate-900/40 border border-slate-800 p-6 rounded-3xl backdrop-blur-xl">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-lg font-medium flex items-center gap-2">
                <Brain className="text-cyan-400" /> AI Agent Status
              </h3>
              <span className="flex items-center gap-2 text-xs text-green-400 bg-green-400/10 px-3 py-1 rounded-full animate-pulse">
                <div className="w-2 h-2 bg-green-400 rounded-full" /> ACTIVE
              </span>
            </div>
            
            <div className="space-y-4">
              <div className="p-4 bg-slate-800/50 rounded-xl border border-slate-700/50">
                <p className="text-slate-400 text-sm">Target Strategy</p>
                <p className="text-lg font-mono">Arbitrage: ETH ⇄ SOL</p>
              </div>
              
              <div className="p-4 bg-slate-800/50 rounded-xl border border-slate-700/50">
                <p className="text-slate-400 text-sm">Current APY</p>
                <p className="text-2xl font-bold text-cyan-400">24.8%</p>
              </div>
              
              <div className="p-4 bg-slate-800/50 rounded-xl border border-slate-700/50">
                <p className="text-slate-400 text-sm">Success Rate</p>
                <p className="text-xl font-bold text-green-400">94.2%</p>
              </div>
              
              <div className="p-4 bg-slate-800/50 rounded-xl border border-slate-700/50">
                <p className="text-slate-400 text-sm">Total Profit</p>
                <p className="text-xl font-bold text-green-400">$12,847</p>
              </div>
            </div>
          </div>

          {/* Cross-Chain Liquidity */}
          <div className="bg-gradient-to-br from-blue-600/20 to-purple-600/20 border border-blue-500/30 p-6 rounded-3xl">
            <h3 className="text-lg font-medium mb-4 flex items-center gap-2">
              <ArrowLeftRight size={20} /> Cross-Chain Liquidity
            </h3>
            
            <div className="space-y-3">
              {Object.values(chainConfig).slice(0, 6).map((chain, index) => (
                <div key={chain.name} className="flex justify-between items-center py-2 border-b border-slate-700/50 last:border-b-0">
                  <div className="flex items-center space-x-3">
                    <div 
                      className="w-6 h-6 rounded-full flex items-center justify-center text-white text-xs font-bold"
                      style={{ backgroundColor: chain.color }}
                    >
                      {chain.symbol.slice(0, 1)}
                    </div>
                    <span>{chain.name}</span>
                  </div>
                  <span className="font-mono">
                    ${(Math.random() * 2000000 + 500000).toLocaleString('en-US', { 
                      minimumFractionDigits: 0, 
                      maximumFractionDigits: 0 
                    })}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Portfolio Overview */}
          {isConnected && (
            <div className="bg-gradient-to-br from-purple-600/20 to-pink-600/20 border border-purple-500/30 p-6 rounded-3xl">
              <h3 className="text-lg font-medium mb-4 flex items-center gap-2">
                <Wallet size={20} /> Portfolio Value
              </h3>
              
              <div className="text-center mb-4">
                <div className="text-3xl font-bold bg-gradient-to-r from-cyan-400 to-purple-500 bg-clip-text text-transparent">
                  ${(Math.random() * 50000 + 10000).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                </div>
                <p className="text-slate-400 text-sm">Total Value</p>
              </div>
              
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="text-center">
                  <div className="text-lg font-bold text-green-400">+$2,340</div>
                  <div className="text-slate-400">24h P&L</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-bold text-blue-400">+5.2%</div>
                  <div className="text-slate-400">24h Change</div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Panel: Trading Terminal */}
        <div className="col-span-12 lg:col-span-8 bg-slate-900/40 border border-slate-800 rounded-3xl p-6 backdrop-blur-xl">
          <div className="flex justify-between items-center mb-8">
            <div>
              <h2 className="text-2xl font-bold">Market Flow Analysis</h2>
              <p className="text-slate-400">Real-time AI cross-chain monitoring</p>
              <div className="flex items-center space-x-2 mt-2">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <span className="text-xs text-slate-400">
                  Last updated: {lastUpdate.toLocaleTimeString()}
                </span>
              </div>
            </div>
            <div className="flex gap-2">
              <button 
                onClick={() => setTimeframe('1H')}
                className={`px-4 py-1 rounded-lg text-sm transition-all ${
                  timeframe === '1H' 
                    ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30' 
                    : 'bg-slate-800 text-slate-400 hover:text-white'
                }`}
              >
                1H
              </button>
              <button 
                onClick={() => setTimeframe('24H')}
                className={`px-4 py-1 rounded-lg text-sm transition-all ${
                  timeframe === '24H' 
                    ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30' 
                    : 'bg-slate-800 text-slate-400 hover:text-white'
                }`}
              >
                24H
              </button>
              <button 
                onClick={() => setTimeframe('7D')}
                className={`px-4 py-1 rounded-lg text-sm transition-all ${
                  timeframe === '7D' 
                    ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30' 
                    : 'bg-slate-800 text-slate-400 hover:text-white'
                }`}
              >
                7D
              </button>
            </div>
          </div>

          {/* Chart */}
          <div className="h-64 w-full mb-8">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <Line 
                  type="monotone" 
                  dataKey="value" 
                  stroke="#22d3ee" 
                  strokeWidth={3} 
                  dot={false}
                  strokeDasharray={isLoading ? "5 5" : "0"}
                />
                <YAxis 
                  axisLine={false} 
                  tickLine={false} 
                  tick={{ fontSize: 12, fill: '#64748b' }}
                  tickFormatter={(value) => `$${(value / 1000).toFixed(1)}k`}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#0f172a', 
                    border: '1px solid #1e293b',
                    borderRadius: '12px',
                    boxShadow: '0 10px 25px rgba(0, 0, 0, 0.5)'
                  }}
                  itemStyle={{ color: '#22d3ee' }}
                  labelStyle={{ color: '#94a3b8' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-slate-800/30 p-4 rounded-2xl border border-slate-700">
              <p className="text-xs text-slate-500 uppercase tracking-wider">Success Rate</p>
              <p className="text-xl font-bold text-green-400">99.2%</p>
              <p className="text-xs text-slate-400 mt-1">+0.3% from yesterday</p>
            </div>
            
            <div className="bg-slate-800/30 p-4 rounded-2xl border border-slate-700">
              <p className="text-xs text-slate-500 uppercase tracking-wider">Avg. Speed</p>
              <p className="text-xl font-bold text-cyan-400">1.2s</p>
              <p className="text-xs text-slate-400 mt-1">Cross-chain execution</p>
            </div>
            
            <div className="bg-slate-800/30 p-4 rounded-2xl border border-slate-700">
              <p className="text-xs text-slate-500 uppercase tracking-wider">Gas Saved</p>
              <p className="text-xl font-bold text-green-400">$4,201</p>
              <p className="text-xs text-slate-400 mt-1">This month</p>
            </div>
            
            <div className="bg-slate-800/30 p-4 rounded-2xl border border-slate-700">
              <p className="text-xs text-slate-500 uppercase tracking-wider">Active Pairs</p>
              <p className="text-xl font-bold text-purple-400">{liveData.marketData.length}</p>
              <p className="text-xs text-slate-400 mt-1">Live monitoring</p>
            </div>
          </div>

          {/* Live Market Data */}
          <div className="mt-8">
            <h3 className="text-lg font-medium mb-4 flex items-center gap-2">
              <Activity size={20} className="text-cyan-400" /> Live Market Data
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-h-48 overflow-y-auto">
              {liveData.marketData.slice(0, 8).map((coin, index) => (
                <div key={coin.id} className="flex items-center justify-between p-3 bg-slate-800/30 rounded-xl border border-slate-700/50 hover:bg-slate-800/50 transition-all">
                  <div className="flex items-center space-x-3">
                    <img src={coin.image} alt={coin.name} className="w-6 h-6 rounded-full" />
                    <div>
                      <div className="font-semibold text-white text-sm">{coin.symbol.toUpperCase()}</div>
                      <div className="text-xs text-slate-400">{coin.name}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-bold text-white text-sm">
                      {priceService.formatPrice(coin.current_price)}
                    </div>
                    <div className={`text-xs font-medium ${
                      coin.price_change_percentage_24h >= 0 ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {priceService.formatPercentChange(coin.price_change_percentage_24h)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
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
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800 flex items-center justify-center">
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