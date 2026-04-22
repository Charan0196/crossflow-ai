import React, { useState, useEffect } from 'react'
import { 
  Play, 
  Pause, 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  Activity,
  Settings,
  RefreshCw,
  Target,
  Shield
} from 'lucide-react'

const AutoTradingDashboard = () => {
  const [tradingStatus, setTradingStatus] = useState(null)
  const [recentTrades, setRecentTrades] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchTradingStatus = async () => {
    try {
      const response = await fetch('/api/auto-trading/status')
      const data = await response.json()
      if (data.success) {
        setTradingStatus(data.data)
      }
    } catch (err) {
      setError('Failed to fetch trading status')
      console.error('Error fetching trading status:', err)
    }
  }

  const fetchRecentTrades = async () => {
    try {
      const response = await fetch('/api/auto-trading/trades/recent?limit=10')
      const data = await response.json()
      if (data.success) {
        setRecentTrades(data.data.trades)
      }
    } catch (err) {
      console.error('Error fetching recent trades:', err)
    }
  }

  const toggleTrading = async () => {
    try {
      const endpoint = tradingStatus?.is_enabled ? '/api/auto-trading/disable' : '/api/auto-trading/enable'
      const response = await fetch(endpoint, { method: 'POST' })
      const data = await response.json()
      
      if (data.success) {
        await fetchTradingStatus()
      }
    } catch (err) {
      setError('Failed to toggle trading')
      console.error('Error toggling trading:', err)
    }
  }

  const resetPortfolio = async () => {
    if (!window.confirm('Are you sure you want to reset the portfolio? This will clear all trades and reset to $10,000.')) {
      return
    }
    
    try {
      const response = await fetch('/api/auto-trading/reset', { method: 'POST' })
      const data = await response.json()
      
      if (data.success) {
        await fetchTradingStatus()
        await fetchRecentTrades()
      }
    } catch (err) {
      setError('Failed to reset portfolio')
      console.error('Error resetting portfolio:', err)
    }
  }

  useEffect(() => {
    const loadData = async () => {
      setLoading(true)
      await Promise.all([fetchTradingStatus(), fetchRecentTrades()])
      setLoading(false)
    }

    loadData()
    
    // Refresh data every 30 seconds
    const interval = setInterval(loadData, 30000)
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <div className="card-goodcrypto">
        <div className="flex items-center justify-center py-8">
          <RefreshCw className="w-6 h-6 animate-spin text-green-500" />
          <span className="ml-2 text-gray-300">Loading auto trading data...</span>
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
            onClick={() => window.location.reload()} 
            className="btn-secondary-goodcrypto"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  const portfolio = tradingStatus?.portfolio || {}
  const stats = tradingStatus?.stats || {}
  const isEnabled = tradingStatus?.is_enabled || false

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="card-goodcrypto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-white mb-2">Auto Trading Dashboard</h2>
            <p className="text-gray-400">Automated trading with mock USD based on AI signals</p>
          </div>
          
          <div className="flex items-center space-x-3">
            <button
              onClick={toggleTrading}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
                isEnabled 
                  ? 'bg-red-600 hover:bg-red-700 text-white' 
                  : 'bg-green-600 hover:bg-green-700 text-white'
              }`}
            >
              {isEnabled ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
              <span>{isEnabled ? 'Stop Trading' : 'Start Trading'}</span>
            </button>
            
            <button
              onClick={resetPortfolio}
              className="btn-secondary-goodcrypto"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Status Indicator */}
        <div className="flex items-center space-x-2 mb-4">
          <div className={`w-3 h-3 rounded-full ${isEnabled ? 'bg-green-500' : 'bg-red-500'}`}></div>
          <span className="text-sm text-gray-300">
            {isEnabled ? 'Auto Trading Active' : 'Auto Trading Stopped'}
          </span>
        </div>
      </div>

      {/* Portfolio Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card-goodcrypto">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Portfolio Value</p>
              <p className="text-2xl font-bold text-white">
                ${parseFloat(portfolio.total_value || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </p>
            </div>
            <DollarSign className="w-8 h-8 text-green-500" />
          </div>
        </div>

        <div className="card-goodcrypto">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">P&L</p>
              <p className={`text-2xl font-bold ${parseFloat(portfolio.profit_loss || 0) >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                {parseFloat(portfolio.profit_loss || 0) >= 0 ? '+' : ''}
                ${parseFloat(portfolio.profit_loss || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </p>
            </div>
            {parseFloat(portfolio.profit_loss || 0) >= 0 ? 
              <TrendingUp className="w-8 h-8 text-green-500" /> : 
              <TrendingDown className="w-8 h-8 text-red-500" />
            }
          </div>
        </div>

        <div className="card-goodcrypto">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">ROI</p>
              <p className={`text-2xl font-bold ${parseFloat(portfolio.roi_percentage || 0) >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                {parseFloat(portfolio.roi_percentage || 0) >= 0 ? '+' : ''}
                {parseFloat(portfolio.roi_percentage || 0).toFixed(2)}%
              </p>
            </div>
            <Target className="w-8 h-8 text-cyan-500" />
          </div>
        </div>

        <div className="card-goodcrypto">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Win Rate</p>
              <p className="text-2xl font-bold text-white">
                {parseFloat(portfolio.win_rate || 0).toFixed(1)}%
              </p>
            </div>
            <Activity className="w-8 h-8 text-purple-500" />
          </div>
        </div>
      </div>

      {/* Trading Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card-goodcrypto">
          <h3 className="text-lg font-semibold text-white mb-3">Trading Activity</h3>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-400">Total Trades</span>
              <span className="text-white">{portfolio.trades_count || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Winning Trades</span>
              <span className="text-green-500">{portfolio.winning_trades || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Losing Trades</span>
              <span className="text-red-500">{portfolio.losing_trades || 0}</span>
            </div>
          </div>
        </div>

        <div className="card-goodcrypto">
          <h3 className="text-lg font-semibold text-white mb-3">Settings</h3>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-400">Min Confidence</span>
              <span className="text-white">{stats.min_confidence || 70}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Max Position</span>
              <span className="text-white">{((stats.max_position_size || 0.1) * 100).toFixed(0)}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Active Positions</span>
              <span className="text-white">{tradingStatus?.active_positions?.length || 0}</span>
            </div>
          </div>
        </div>

        <div className="card-goodcrypto">
          <h3 className="text-lg font-semibold text-white mb-3">Holdings</h3>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-400">USD Balance</span>
              <span className="text-white">${parseFloat(portfolio.usd_balance || 0).toLocaleString()}</span>
            </div>
            {portfolio.token_holdings && Object.keys(portfolio.token_holdings).length > 0 ? (
              Object.entries(portfolio.token_holdings).slice(0, 3).map(([token, amount]) => (
                <div key={token} className="flex justify-between">
                  <span className="text-gray-400">{token}</span>
                  <span className="text-white">{parseFloat(amount).toFixed(6)}</span>
                </div>
              ))
            ) : (
              <div className="text-gray-500 text-sm">No token holdings</div>
            )}
          </div>
        </div>
      </div>

      {/* Recent Trades */}
      <div className="card-goodcrypto">
        <h3 className="text-lg font-semibold text-white mb-4">Recent Trades</h3>
        
        {recentTrades.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-700">
                  <th className="text-left py-2 text-gray-400">Time</th>
                  <th className="text-left py-2 text-gray-400">Token</th>
                  <th className="text-left py-2 text-gray-400">Type</th>
                  <th className="text-right py-2 text-gray-400">Amount</th>
                  <th className="text-right py-2 text-gray-400">Price</th>
                  <th className="text-right py-2 text-gray-400">Value</th>
                  <th className="text-right py-2 text-gray-400">Confidence</th>
                </tr>
              </thead>
              <tbody>
                {recentTrades.map((trade, index) => (
                  <tr key={index} className="border-b border-gray-800">
                    <td className="py-2 text-gray-300 text-sm">
                      {new Date(trade.created_at).toLocaleTimeString()}
                    </td>
                    <td className="py-2 text-white font-medium">{trade.token}</td>
                    <td className="py-2">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        trade.trade_type === 'buy' 
                          ? 'bg-green-900 text-green-300' 
                          : 'bg-red-900 text-red-300'
                      }`}>
                        {trade.trade_type.toUpperCase()}
                      </span>
                    </td>
                    <td className="py-2 text-right text-white">
                      {parseFloat(trade.amount).toFixed(6)}
                    </td>
                    <td className="py-2 text-right text-white">
                      ${parseFloat(trade.price).toFixed(2)}
                    </td>
                    <td className="py-2 text-right text-white">
                      ${parseFloat(trade.total_value).toFixed(2)}
                    </td>
                    <td className="py-2 text-right text-gray-300">
                      {trade.signal_confidence.toFixed(0)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            No trades executed yet
          </div>
        )}
      </div>
    </div>
  )
}

export default AutoTradingDashboard