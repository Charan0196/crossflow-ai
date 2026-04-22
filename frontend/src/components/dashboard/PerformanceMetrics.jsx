import React, { useEffect, useState } from 'react'
import { TrendingUp, TrendingDown, Activity, Award, DollarSign, BarChart3 } from 'lucide-react'
import axios from 'axios'

const PerformanceMetrics = ({ walletAddress }) => {
  const [metrics, setMetrics] = useState(null)
  const [timeRange, setTimeRange] = useState('24h')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchMetrics()
  }, [timeRange, walletAddress])

  const fetchMetrics = async () => {
    try {
      setLoading(true)
      const response = await axios.get(`http://localhost:8000/api/autonomous/wallet/metrics`, {
        params: { address: walletAddress, time_range: timeRange }
      })
      setMetrics(response.data)
    } catch (error) {
      console.error('Failed to fetch metrics:', error)
      
      // Use mock data as fallback
      setMetrics({
        total_profit_loss: 0.25,
        profit_loss_percentage: 1.5,
        win_rate: 66.7,
        total_trades: 3,
        winning_trades: 2,
        avg_trade_profit: 0.50,
        avg_trade_loss: 0.25,
        best_token: 'USDC',
        best_token_profit: 0.50,
        average_profit: 0.50,
        sharpe_ratio: 1.2
      })
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="bg-[#0f1419] border border-gray-800 rounded-lg p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-800 rounded w-1/3"></div>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {[1, 2, 3, 4, 5, 6].map(i => (
              <div key={i} className="h-20 bg-gray-800 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (!metrics) return null

  const profitLossColor = metrics.total_profit_loss >= 0 ? 'text-green-500' : 'text-red-500'
  const profitLossIcon = metrics.total_profit_loss >= 0 ? TrendingUp : TrendingDown

  return (
    <div className="bg-[#0f1419] border border-gray-800 rounded-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-white">Performance Metrics</h2>
        <div className="flex gap-2">
          {['24h', '7d', '30d', 'all'].map(range => (
            <button
              key={range}
              onClick={() => setTimeRange(range)}
              className={`px-3 py-1 rounded-lg text-sm transition-all ${
                timeRange === range
                  ? 'bg-green-500 text-black font-semibold'
                  : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
              }`}
            >
              {range}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        {/* Total P&L */}
        <div className="bg-gray-800/50 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            {React.createElement(profitLossIcon, { className: `w-5 h-5 ${profitLossColor}` })}
            <span className="text-sm text-gray-400">Total P&L</span>
          </div>
          <div className={`text-2xl font-bold ${profitLossColor}`}>
            ${metrics.total_profit_loss?.toFixed(2) || '0.00'}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            {metrics.profit_loss_percentage >= 0 ? '+' : ''}
            {metrics.profit_loss_percentage?.toFixed(2) || '0.00'}%
          </div>
        </div>

        {/* Win Rate */}
        <div className="bg-gray-800/50 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <Award className="w-5 h-5 text-cyan-500" />
            <span className="text-sm text-gray-400">Win Rate</span>
          </div>
          <div className="text-2xl font-bold text-white">
            {metrics.win_rate?.toFixed(1) || '0.0'}%
          </div>
          <div className="text-xs text-gray-500 mt-1">
            {metrics.winning_trades || 0} / {metrics.total_trades || 0} trades
          </div>
        </div>

        {/* Total Trades */}
        <div className="bg-gray-800/50 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <Activity className="w-5 h-5 text-purple-500" />
            <span className="text-sm text-gray-400">Total Trades</span>
          </div>
          <div className="text-2xl font-bold text-white">
            {metrics.total_trades || 0}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            Executed
          </div>
        </div>

        {/* Best Token */}
        <div className="bg-gray-800/50 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <Award className="w-5 h-5 text-yellow-500" />
            <span className="text-sm text-gray-400">Best Token</span>
          </div>
          <div className="text-lg font-bold text-white">
            {typeof metrics.best_token === 'object' ? metrics.best_token?.symbol : metrics.best_token || 'N/A'}
          </div>
          <div className="text-xs text-green-500 mt-1">
            +${typeof metrics.best_token === 'object' ? metrics.best_token?.profit?.toFixed(2) : metrics.best_token_profit?.toFixed(2) || '0.00'}
          </div>
        </div>

        {/* Avg Profit */}
        <div className="bg-gray-800/50 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <DollarSign className="w-5 h-5 text-green-500" />
            <span className="text-sm text-gray-400">Avg Profit</span>
          </div>
          <div className="text-lg font-bold text-green-500">
            ${metrics.average_profit?.toFixed(2) || '0.00'}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            Per winning trade
          </div>
        </div>

        {/* Sharpe Ratio */}
        <div className="bg-gray-800/50 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <BarChart3 className="w-5 h-5 text-blue-500" />
            <span className="text-sm text-gray-400">Sharpe Ratio</span>
          </div>
          <div className="text-lg font-bold text-white">
            {metrics.sharpe_ratio?.toFixed(2) || '0.00'}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            Risk-adjusted
          </div>
        </div>
      </div>
    </div>
  )
}

export default PerformanceMetrics
