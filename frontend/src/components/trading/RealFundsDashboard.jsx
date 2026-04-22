import React, { useState, useEffect } from 'react'
import { 
  Play, 
  Pause,
  AlertTriangle, 
  DollarSign, 
  RefreshCw,
  Target,
  Wallet,
  ExternalLink,
  Zap,
  StopCircle,
  Eye,
  Key,
  Network,
  BarChart3
} from 'lucide-react'

const RealFundsDashboard = () => {
  const [status, setStatus] = useState(null)
  const [trades, setTrades] = useState([])
  const [positions, setPositions] = useState([])
  const [performance, setPerformance] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [privateKey, setPrivateKey] = useState('')
  const [seedPhrase, setSeedPhrase] = useState('')
  const [accountIndex, setAccountIndex] = useState(0)
  const [walletType, setWalletType] = useState('private_key')
  const [selectedNetwork, setSelectedNetwork] = useState('sepolia')
  const [showPrivateKey, setShowPrivateKey] = useState(false)
  const [showSeedPhrase, setShowSeedPhrase] = useState(false)

  const fetchStatus = async () => {
    try {
      const response = await fetch('/api/real-trading/status')
      const data = await response.json()
      if (data.success) {
        setStatus(data.data)
      }
    } catch (err) {
      setError('Failed to fetch real trading status')
      console.error('Error fetching status:', err)
    }
  }

  const fetchTrades = async () => {
    try {
      const response = await fetch('/api/real-trading/trades?limit=10')
      const data = await response.json()
      if (data.success) {
        setTrades(data.data.trades)
      }
    } catch (err) {
      console.error('Error fetching trades:', err)
    }
  }

  const fetchPositions = async () => {
    try {
      const response = await fetch('/api/real-trading/positions')
      const data = await response.json()
      if (data.success) {
        setPositions(data.data.positions)
      }
    } catch (err) {
      console.error('Error fetching positions:', err)
    }
  }

  const fetchPerformance = async () => {
    try {
      const response = await fetch('/api/real-trading/performance')
      const data = await response.json()
      if (data.success) {
        setPerformance(data.data)
      }
    } catch (err) {
      console.error('Error fetching performance:', err)
    }
  }

  const setupWallet = async () => {
    if (walletType === 'private_key' && !privateKey) return
    if (walletType === 'seed_phrase' && !seedPhrase) return
    
    try {
      const payload = {
        network: selectedNetwork
      }
      
      if (walletType === 'private_key') {
        payload.private_key = privateKey
      } else {
        payload.seed_phrase = seedPhrase
        payload.account_index = accountIndex
      }
      
      const response = await fetch('/api/real-trading/setup-wallet', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      const data = await response.json()
      
      if (data.success) {
        await fetchStatus()
        setPrivateKey('')
        setSeedPhrase('')
        setShowPrivateKey(false)
        setShowSeedPhrase(false)
      } else {
        setError(data.message || 'Failed to setup wallet')
      }
    } catch (err) {
      setError('Failed to setup wallet')
      console.error('Error setting up wallet:', err)
    }
  }

  const toggleTrading = async () => {
    try {
      const endpoint = status?.stats?.is_enabled ? '/api/real-trading/disable' : '/api/real-trading/enable'
      const response = await fetch(endpoint, { method: 'POST' })
      const data = await response.json()
      
      if (data.success) {
        await fetchStatus()
      }
    } catch (err) {
      setError('Failed to toggle trading')
      console.error('Error toggling trading:', err)
    }
  }

  const emergencyStop = async () => {
    if (!confirm('Are you sure you want to execute emergency stop? This will close all positions and disable trading.')) {
      return
    }
    
    try {
      const response = await fetch('/api/real-trading/emergency-stop', { method: 'POST' })
      const data = await response.json()
      
      if (data.success) {
        await Promise.all([fetchStatus(), fetchPositions(), fetchTrades()])
      }
    } catch (err) {
      setError('Failed to execute emergency stop')
      console.error('Error executing emergency stop:', err)
    }
  }

  const disconnectWallet = async () => {
    if (!confirm('Are you sure you want to disconnect your wallet? This will stop all trading and clear your wallet connection.')) {
      return
    }
    
    try {
      const response = await fetch('/api/real-trading/disconnect', { method: 'POST' })
      const data = await response.json()
      
      if (data.success) {
        // Clear local state
        setStatus(null)
        setTrades([])
        setPositions([])
        setPerformance(null)
        setPrivateKey('')
        setSeedPhrase('')
        setShowPrivateKey(false)
        setShowSeedPhrase(false)
        
        // Refresh to get updated status
        await Promise.all([fetchStatus(), fetchTrades(), fetchPositions(), fetchPerformance()])
      } else {
        setError(data.message || 'Failed to disconnect wallet')
      }
      
    } catch (err) {
      setError('Failed to disconnect wallet')
      console.error('Error disconnecting wallet:', err)
    }
  }

  useEffect(() => {
    const loadData = async () => {
      setLoading(true)
      await Promise.all([fetchStatus(), fetchTrades(), fetchPositions(), fetchPerformance()])
      setLoading(false)
    }

    loadData()
    
    const interval = setInterval(loadData, 30000)
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <div className="card-goodcrypto">
        <div className="flex items-center justify-center py-8">
          <RefreshCw className="w-6 h-6 animate-spin text-green-500" />
          <span className="ml-2 text-gray-300">Loading automated trading data...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="card-goodcrypto">
        <div className="text-center py-8">
          <div className="text-red-400 mb-2">{error}</div>
          <button 
            onClick={() => {
              setError(null)
              window.location.reload()
            }} 
            className="btn-secondary-goodcrypto"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  const stats = status?.stats || {}
  const isEnabled = stats?.is_enabled || false
  const walletConnected = !!stats?.wallet_address
  const currentNetwork = stats?.network || 'sepolia'
  const isMainnet = currentNetwork === 'mainnet'

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className={`card-goodcrypto border-2 ${isMainnet ? 'border-red-500/30 bg-red-500/5' : 'border-green-500/30 bg-green-500/5'}`}>
        <div className="flex items-start space-x-4">
          <Zap className={`w-8 h-8 flex-shrink-0 mt-1 ${isMainnet ? 'text-red-500' : 'text-green-500'}`} />
          <div className="flex-1">
            <h2 className="text-2xl font-bold text-white mb-2">
              Real Funds Automated Trading
              {isMainnet && <span className="text-red-500 ml-2">(LIVE FUNDS)</span>}
            </h2>
            
            <div className={`border rounded-lg p-4 mb-4 ${isMainnet ? 'bg-red-500/10 border-red-500/30' : 'bg-green-500/10 border-green-500/30'}`}>
              <div className="flex items-center space-x-2 mb-2">
                <Zap className={`w-5 h-5 ${isMainnet ? 'text-red-500' : 'text-green-500'}`} />
                <span className={`font-semibold ${isMainnet ? 'text-red-500' : 'text-green-500'}`}>
                  {isMainnet ? 'LIVE TRADING MODE' : 'TESTNET TRADING MODE'}
                </span>
              </div>
              <p className="text-gray-300 text-sm">
                {isMainnet 
                  ? 'This system executes REAL trades with actual USD value on Ethereum mainnet. Use with caution!'
                  : 'This system executes real trades on Sepolia testnet with test ETH. Safe for testing and learning.'
                }
              </p>
            </div>
            
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <div className={`w-3 h-3 rounded-full ${isEnabled ? 'bg-green-500' : 'bg-red-500'}`}></div>
                  <span className="text-sm text-gray-300">
                    {isEnabled ? 'Trading Active' : 'Trading Stopped'}
                  </span>
                </div>
                <div className="flex items-center space-x-2">
                  <Network className="w-4 h-4 text-gray-400" />
                  <span className="text-sm text-gray-400">
                    {currentNetwork === 'mainnet' ? 'Ethereum Mainnet' : 'Sepolia Testnet'}
                  </span>
                </div>
                {walletConnected && (
                  <div className="flex items-center space-x-2">
                    <Wallet className="w-4 h-4 text-green-400" />
                    <span className="text-sm text-green-400">
                      Wallet Connected: {stats?.wallet_address?.slice(0, 6)}...{stats?.wallet_address?.slice(-4)}
                    </span>
                    <button
                      onClick={disconnectWallet}
                      className="ml-2 px-2 py-1 bg-gray-600 hover:bg-gray-700 text-white rounded text-xs transition-all duration-200"
                      title="Disconnect Wallet"
                    >
                      Disconnect
                    </button>
                  </div>
                )}
              </div>
              
              <div className="flex items-center space-x-2">
                {walletConnected && (
                  <button
                    onClick={emergencyStop}
                    className="flex items-center space-x-2 px-3 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-all duration-200"
                  >
                    <StopCircle className="w-4 h-4" />
                    <span>Emergency Stop</span>
                  </button>
                )}
                
                <button
                  onClick={toggleTrading}
                  disabled={!walletConnected}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed ${
                    isEnabled 
                      ? 'bg-red-600 hover:bg-red-700 text-white' 
                      : 'bg-green-600 hover:bg-green-700 text-white'
                  }`}
                >
                  {isEnabled ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                  <span>{isEnabled ? 'Stop Trading' : 'Start Trading'}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Wallet Setup */}
      {!walletConnected && (
        <div className="card-goodcrypto">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">Wallet Setup</h3>
            <button
              onClick={async () => {
                try {
                  await fetch('/api/real-trading/disconnect', { method: 'POST' })
                  await Promise.all([fetchStatus(), fetchTrades(), fetchPositions(), fetchPerformance()])
                } catch (err) {
                  console.error('Error clearing state:', err)
                }
              }}
              className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white rounded text-sm transition-all duration-200"
              title="Clear any existing wallet connection"
            >
              Clear State
            </button>
          </div>
          
          {/* Network Selection */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-300 mb-2">Network</label>
            <div className="flex space-x-4">
              <button
                onClick={() => setSelectedNetwork('sepolia')}
                className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
                  selectedNetwork === 'sepolia'
                    ? 'bg-green-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                Sepolia Testnet (Safe)
              </button>
              <button
                onClick={() => setSelectedNetwork('mainnet')}
                className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
                  selectedNetwork === 'mainnet'
                    ? 'bg-red-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                Ethereum Mainnet (Live Funds)
              </button>
            </div>
          </div>
          
          {/* Wallet Type Selection */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-300 mb-2">Wallet Type</label>
            <div className="flex space-x-4">
              <button
                onClick={() => setWalletType('private_key')}
                className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
                  walletType === 'private_key'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                Private Key
              </button>
              <button
                onClick={() => setWalletType('seed_phrase')}
                className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
                  walletType === 'seed_phrase'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                Seed Phrase
              </button>
            </div>
          </div>
          
          {/* Private Key Input */}
          {walletType === 'private_key' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Private Key</label>
                <div className="flex items-center space-x-2">
                  <div className="flex-1 relative">
                    <input
                      type={showPrivateKey ? "text" : "password"}
                      placeholder="Enter your private key (0x...)"
                      value={privateKey}
                      onChange={(e) => setPrivateKey(e.target.value)}
                      className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-green-500"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPrivateKey(!showPrivateKey)}
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                  </div>
                  <button
                    onClick={setupWallet}
                    disabled={!privateKey}
                    className="btn-goodcrypto disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Key className="w-4 h-4 mr-2" />
                    Setup Wallet
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Seed Phrase Input */}
          {walletType === 'seed_phrase' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Seed Phrase (12 or 24 words)</label>
                <div className="space-y-3">
                  <div className="relative">
                    <textarea
                      placeholder="Enter your 12 or 24 word seed phrase..."
                      value={seedPhrase}
                      onChange={(e) => setSeedPhrase(e.target.value)}
                      rows={3}
                      className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-green-500 resize-none"
                      style={{ 
                        WebkitTextSecurity: showSeedPhrase ? 'none' : 'disc',
                        fontFamily: showSeedPhrase ? 'inherit' : 'monospace'
                      }}
                    />
                    <button
                      type="button"
                      onClick={() => setShowSeedPhrase(!showSeedPhrase)}
                      className="absolute right-3 top-3 text-gray-400 hover:text-white"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                  </div>
                  
                  <div className="flex items-center space-x-4">
                    <div className="flex items-center space-x-2">
                      <label className="text-sm font-medium text-gray-300">Account Index:</label>
                      <input
                        type="number"
                        min="0"
                        max="99"
                        value={accountIndex}
                        onChange={(e) => setAccountIndex(parseInt(e.target.value) || 0)}
                        className="w-20 px-2 py-1 bg-gray-800 border border-gray-700 rounded text-white text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                      />
                      <span className="text-xs text-gray-400">(0 = first account)</span>
                    </div>
                    
                    <button
                      onClick={setupWallet}
                      disabled={!seedPhrase}
                      className="btn-goodcrypto disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <Key className="w-4 h-4 mr-2" />
                      Setup Wallet
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
            
          {selectedNetwork === 'mainnet' && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 mt-4">
              <div className="flex items-center space-x-2 mb-2">
                <AlertTriangle className="w-5 h-5 text-red-500" />
                <span className="font-semibold text-red-500">MAINNET WARNING</span>
              </div>
              <p className="text-gray-300 text-sm">
                You are about to connect to Ethereum mainnet with real funds. 
                The AI will execute actual trades that can result in real profits or losses. 
                Only proceed if you understand the risks.
              </p>
            </div>
          )}
        </div>
      )}

      {/* Performance Summary */}
      {walletConnected && performance && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="card-goodcrypto">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Total Trades</p>
                <p className="text-2xl font-bold text-white">{performance.total_trades}</p>
              </div>
              <BarChart3 className="w-8 h-8 text-blue-500" />
            </div>
          </div>

          <div className="card-goodcrypto">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Win Rate</p>
                <p className="text-2xl font-bold text-white">{performance.win_rate}%</p>
              </div>
              <Target className="w-8 h-8 text-green-500" />
            </div>
          </div>

          <div className="card-goodcrypto">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Total P&L</p>
                <p className={`text-2xl font-bold ${parseFloat(performance.total_profit_usd) >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                  ${parseFloat(performance.total_profit_usd).toFixed(2)}
                </p>
              </div>
              <DollarSign className="w-8 h-8 text-green-500" />
            </div>
          </div>

          <div className="card-goodcrypto">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Portfolio Value</p>
                <p className="text-2xl font-bold text-white">${parseFloat(performance.portfolio_value).toFixed(2)}</p>
              </div>
              <Wallet className="w-8 h-8 text-purple-500" />
            </div>
          </div>
        </div>
      )}

      {/* Open Positions */}
      {walletConnected && positions.length > 0 && (
        <div className="card-goodcrypto">
          <h3 className="text-lg font-semibold text-white mb-4">Open Positions</h3>
          <div className="space-y-4">
            {positions.map((position, index) => (
              <div key={index} className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-3">
                    <div className="text-lg font-bold text-white">{position.token}</div>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      position.signal_type.includes('buy') 
                        ? 'bg-green-900 text-green-300' 
                        : 'bg-red-900 text-red-300'
                    }`}>
                      {position.signal_type.toUpperCase()}
                    </span>
                    <div className="text-sm text-gray-400">
                      {new Date(position.created_at).toLocaleDateString()}
                    </div>
                  </div>
                  
                  <div className="text-right">
                    <div className="text-white font-medium">${parseFloat(position.entry_price).toFixed(2)}</div>
                    <div className="text-sm text-gray-400">Entry Price</div>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <div className="text-gray-400">Position Size</div>
                    <div className="text-white">${parseFloat(position.position_size_usd).toFixed(0)}</div>
                  </div>
                  <div>
                    <div className="text-gray-400">Take Profit</div>
                    <div className="text-green-400">${parseFloat(position.take_profit).toFixed(2)}</div>
                  </div>
                  <div>
                    <div className="text-gray-400">Stop Loss</div>
                    <div className="text-red-400">${parseFloat(position.stop_loss).toFixed(2)}</div>
                  </div>
                  <div>
                    <div className="text-gray-400">Status</div>
                    <div className="text-yellow-400">{position.status.toUpperCase()}</div>
                  </div>
                </div>
                
                <div className="mt-3 flex items-center justify-between">
                  <div className="text-sm text-gray-400">
                    TX: {position.entry_tx_hash.slice(0, 10)}...
                  </div>
                  <button className="flex items-center space-x-2 px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded text-sm text-white transition-colors">
                    <ExternalLink className="w-3 h-3" />
                    <span>View on Explorer</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Trades */}
      {walletConnected && trades.length > 0 && (
        <div className="card-goodcrypto">
          <h3 className="text-lg font-semibold text-white mb-4">Recent Trades</h3>
          <div className="space-y-4">
            {trades.slice(0, 5).map((trade, index) => (
              <div key={index} className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-3">
                    <div className="text-lg font-bold text-white">{trade.token}</div>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      trade.signal_type.includes('buy') 
                        ? 'bg-green-900 text-green-300' 
                        : 'bg-red-900 text-red-300'
                    }`}>
                      {trade.signal_type.toUpperCase()}
                    </span>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      trade.status === 'closed_profit' ? 'bg-green-900 text-green-300' :
                      trade.status === 'closed_loss' ? 'bg-red-900 text-red-300' :
                      'bg-yellow-900 text-yellow-300'
                    }`}>
                      {trade.status.replace('_', ' ').toUpperCase()}
                    </span>
                  </div>
                  
                  <div className="text-right">
                    {trade.profit_loss_usd && (
                      <div className={`font-medium ${parseFloat(trade.profit_loss_usd) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {parseFloat(trade.profit_loss_usd) >= 0 ? '+' : ''}${parseFloat(trade.profit_loss_usd).toFixed(2)}
                      </div>
                    )}
                    <div className="text-sm text-gray-400">P&L</div>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <div className="text-gray-400">Entry</div>
                    <div className="text-white">${parseFloat(trade.entry_price).toFixed(2)}</div>
                  </div>
                  <div>
                    <div className="text-gray-400">Exit</div>
                    <div className="text-white">
                      {trade.exit_price ? `$${parseFloat(trade.exit_price).toFixed(2)}` : '-'}
                    </div>
                  </div>
                  <div>
                    <div className="text-gray-400">Size</div>
                    <div className="text-white">${parseFloat(trade.position_size_usd).toFixed(0)}</div>
                  </div>
                  <div>
                    <div className="text-gray-400">Gas Cost</div>
                    <div className="text-white">${parseFloat(trade.gas_cost_usd).toFixed(2)}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Instructions */}
      <div className="card-goodcrypto bg-blue-500/5 border border-blue-500/30">
        <h3 className="text-lg font-semibold text-white mb-3">How It Works</h3>
        <div className="space-y-2 text-sm text-gray-300">
          <div className="flex items-start space-x-2">
            <span className="text-blue-400 font-bold">1.</span>
            <span>Setup your wallet with private key or seed phrase (testnet recommended for first use)</span>
          </div>
          <div className="flex items-start space-x-2">
            <span className="text-blue-400 font-bold">2.</span>
            <span>The AI monitors market signals and automatically executes trades</span>
          </div>
          <div className="flex items-start space-x-2">
            <span className="text-blue-400 font-bold">3.</span>
            <span>Stop-loss and take-profit orders are managed automatically</span>
          </div>
          <div className="flex items-start space-x-2">
            <span className="text-blue-400 font-bold">4.</span>
            <span>Use emergency stop to close all positions and halt trading</span>
          </div>
        </div>
        
        <div className="mt-4 p-3 bg-green-500/10 border border-green-500/30 rounded-lg">
          <h4 className="text-sm font-semibold text-green-400 mb-2">Seed Phrase Support</h4>
          <div className="text-xs text-gray-300 space-y-1">
            <div>• Use your MetaMask or hardware wallet seed phrase</div>
            <div>• Select account index (0 = first account, 1 = second, etc.)</div>
            <div>• More secure than exporting private keys</div>
            <div>• Works with 12 or 24 word seed phrases</div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default RealFundsDashboard