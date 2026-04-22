import React, { useEffect, useState } from 'react'
import { ExternalLink, Download } from 'lucide-react'

const TradeHistoryTable = ({ address = "0x6739659248061A54E0f4de8f2cd60278B69468b3" }) => {
  const [trades, setTrades] = useState([])
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchTrades()
  }, [page, address])

  const fetchTrades = async () => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/autonomous/wallet/trades?address=${address}&page=${page}&page_size=20`
      )
      const data = await response.json()
      setTrades(data.trades)
      setTotal(data.total)
    } catch (error) {
      console.error('Failed to fetch trades:', error)
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'confirmed': return 'text-green-500 bg-green-500/10'
      case 'pending': return 'text-yellow-500 bg-yellow-500/10'
      case 'failed': return 'text-red-500 bg-red-500/10'
      default: return 'text-gray-500 bg-gray-500/10'
    }
  }

  const exportCSV = () => {
    const headers = ['Timestamp', 'From', 'To', 'Amount', 'Gas', 'Status', 'TX Hash']
    const rows = trades.map(t => [
      new Date(t.timestamp * 1000).toLocaleString(),
      `${t.from_token_symbol} ${t.from_amount}`,
      `${t.to_token_symbol} ${t.to_amount}`,
      t.gas_fee,
      t.status,
      t.tx_hash
    ])
    
    const csv = [headers, ...rows].map(row => row.join(',')).join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'trade_history.csv'
    a.click()
  }

  if (loading) {
    return <div className="text-gray-400">Loading trades...</div>
  }

  if (trades.length === 0) {
    return (
      <div className="card-goodcrypto text-center py-12">
        <p className="text-gray-400">No trades found</p>
      </div>
    )
  }

  return (
    <div className="card-goodcrypto">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-white">Trade History</h2>
        <button onClick={exportCSV} className="btn-secondary-goodcrypto flex items-center gap-2">
          <Download className="w-4 h-4" />
          Export CSV
        </button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-700">
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">Time</th>
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">From</th>
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">To</th>
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">Type</th>
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">Status</th>
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">TX</th>
            </tr>
          </thead>
          <tbody>
            {trades.map((trade, idx) => (
              <tr key={idx} className="border-b border-gray-800 hover:bg-gray-800/30">
                <td className="py-3 px-4 text-sm text-gray-300">
                  {new Date(trade.timestamp * 1000).toLocaleString()}
                </td>
                <td className="py-3 px-4 text-sm text-white">
                  {trade.from_token_symbol} {parseFloat(trade.from_amount).toFixed(4)}
                </td>
                <td className="py-3 px-4 text-sm text-white">
                  {trade.to_token_symbol} {parseFloat(trade.to_amount).toFixed(4)}
                </td>
                <td className="py-3 px-4 text-sm">
                  <span className="px-2 py-1 rounded text-xs bg-gray-700 text-gray-300">
                    {trade.trade_type}
                  </span>
                </td>
                <td className="py-3 px-4 text-sm">
                  <span className={`px-2 py-1 rounded text-xs ${getStatusColor(trade.status)}`}>
                    {trade.status}
                  </span>
                </td>
                <td className="py-3 px-4 text-sm">
                  <a
                    href={`https://sepolia.etherscan.io/tx/${trade.tx_hash}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-cyan-500 hover:text-cyan-400 flex items-center gap-1"
                  >
                    {trade.tx_hash.slice(0, 6)}...
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between mt-6">
        <p className="text-sm text-gray-400">
          Showing {trades.length} of {total} trades
        </p>
        <div className="flex gap-2">
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
            className="btn-secondary-goodcrypto disabled:opacity-50"
          >
            Previous
          </button>
          <button
            onClick={() => setPage(p => p + 1)}
            disabled={trades.length < 20}
            className="btn-secondary-goodcrypto disabled:opacity-50"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  )
}

export default TradeHistoryTable
