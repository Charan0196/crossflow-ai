import React, { useEffect, useState } from 'react'
import { Power, Activity, TrendingUp, AlertCircle, Clock, Target } from 'lucide-react'
import axios from 'axios'

const AITradingControls = () => {
  const [status, setStatus] = useState(null)
  const [signals, setSignals] = useState([])
  const [loading, setLoading] = useState(true)
  const [toggling, setToggling] = useState(false)

  useEffect(() => {
    fetchStatus()
    fetchSignals()
    const interval = setInterval(() => {
      fetchStatus()
      fetchSignals()
    }, 10000)
    return () => clearInterval(interval)
  }, [])

  const fetchStatus = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/autonomous/ai/status')
      setStatus(response.data)
      setLoading(false)
    } catch (error) {
      console.error('Failed to fetch AI status:', error)
      setLoading(false)
    }
  }

  const fetchSignals = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/autonomous/ai/signals?limit=5')
      setSignals(response.data.signals || [])
    } catch (error) {
      console.error('Failed to fetch signals:', error)
    }
  }

  const toggleAITrading = async () => {
    try {
      setToggling(true)
      const response = await axios.post('http://localhost:8000/api/autonomous/ai/toggle', {
        enabled: !status?.is_running
      })
      if (response.data.success) {
        await fetchStatus()
      }
    } catch (error) {
      console.error('Failed to toggle AI trading:', error)
    } finally {
      setToggling(false)
    }
  }

  if (loading) {
    return (
      <div className="bg-[#0f1419] border border-gray-800 rounded-lg p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-800 rounded w-1/3"></div>
          <div className="h-20 bg-gray-800 rounded"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-[#0f1419] border border-gray-800 rounded-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-white flex items-center gap-2">
          <Activity className="w-5 h-5 text-purple-500" />
          AI Trading Controls
        </h2>
        <div className="flex items-center gap-3">
          <span className={`text-sm font-medium ${status?.is_running ? 'text-green-500' : 'text-gray-500'}`}>
            {status?.is_running ? 'Active' : 'Inactive'}
          </span>
          <button
            onClick={toggleAITrading}
            disabled={toggling}
            className={`relative inline-flex h-8 w-14 items-center rounded-full transition-colors ${
              status?.is_running ? 'bg-green-500' : 'bg-gray-700'
            } ${toggling ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            <span
              className={`inline-block h-6 w-6 transform rounded-full bg-white transition-transform ${
                status?.is_running ? 'translate-x-7' : 'translate-x-1'
              }`}
            />
          </button>
        </div>
      </div>

      {/* Status Info */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-gray-800/50 rounded-lg p-3">
          <div className="flex items-center gap-2 mb-1">
            <Target className="w-4 h-4 text-cyan-500" />
            <span className="text-xs text-gray-400">Confidence</span>
          </div>
          <div className="text-lg font-bold text-white">{status?.confidence_threshold}%</div>
        </div>
        <div className="bg-gray-800/50 rounded-lg p-3">
          <div className="flex items-center gap-2 mb-1">
            <Clock className="w-4 h-4 text-blue-500" />
            <span className="text-xs text-gray-400">Interval</span>
          </div>
          <div className="text-lg font-bold text-white">{status?.signal_interval}s</div>
        </div>
        <div className="bg-gray-800/50 rounded-lg p-3">
          <div className="flex items-center gap-2 mb-1">
            <Activity className="w-4 h-4 text-purple-500" />
            <span className="text-xs text-gray-400">Signals</span>
          </div>
          <div className="text-lg font-bold text-white">{signals.length}</div>
        </div>
      </div>

      {/* Recent Signals */}
      <div>
        <h3 className="text-sm font-semibold text-gray-400 mb-3">Recent Signals</h3>
        {signals.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <AlertCircle className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No signals generated yet</p>
          </div>
        ) : (
          <div className="space-y-2">
            {signals.map((signal, index) => (
              <div
                key={index}
                className="bg-gray-800/50 rounded-lg p-3 hover:bg-gray-800 transition-colors"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-1 rounded text-xs font-semibold ${
                      signal.action === 'buy' ? 'bg-green-500/20 text-green-500' : 'bg-red-500/20 text-red-500'
                    }`}>
                      {signal.action?.toUpperCase()}
                    </span>
                    <span className="text-white font-medium">{signal.token}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-400">{signal.confidence}%</span>
                    {signal.executed && (
                      <span className="px-2 py-1 rounded text-xs bg-blue-500/20 text-blue-500">
                        Executed
                      </span>
                    )}
                  </div>
                </div>
                <p className="text-xs text-gray-500">{signal.reason}</p>
                <p className="text-xs text-gray-600 mt-1">
                  {new Date(signal.timestamp * 1000).toLocaleString()}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Risk Settings Display */}
      <div className="mt-6 pt-6 border-t border-gray-800">
        <h3 className="text-sm font-semibold text-gray-400 mb-3">Risk Parameters</h3>
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-gray-800/30 rounded-lg p-3">
            <p className="text-xs text-gray-500 mb-1">Position Size Limit</p>
            <p className="text-sm font-semibold text-white">10% of portfolio</p>
          </div>
          <div className="bg-gray-800/30 rounded-lg p-3">
            <p className="text-xs text-gray-500 mb-1">Stop Loss</p>
            <p className="text-sm font-semibold text-white">5% below entry</p>
          </div>
          <div className="bg-gray-800/30 rounded-lg p-3">
            <p className="text-xs text-gray-500 mb-1">Take Profit</p>
            <p className="text-sm font-semibold text-white">10% above entry</p>
          </div>
          <div className="bg-gray-800/30 rounded-lg p-3">
            <p className="text-xs text-gray-500 mb-1">Daily Loss Limit</p>
            <p className="text-sm font-semibold text-white">5% of portfolio</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default AITradingControls
