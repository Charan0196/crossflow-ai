import React, { useEffect, useState } from 'react'
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts'

const COLORS = ['#10b981', '#06b6d4', '#8b5cf6', '#f59e0b', '#ef4444']

const PortfolioHoldings = ({ address = "0x6739659248061A54E0f4de8f2cd60278B69468b3" }) => {
  const [portfolio, setPortfolio] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchPortfolio()
    const interval = setInterval(fetchPortfolio, 30000)
    return () => clearInterval(interval)
  }, [address])

  const fetchPortfolio = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/autonomous/wallet/portfolio?address=${address}`)
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }
      
      const data = await response.json()
      setPortfolio(data)
    } catch (error) {
      console.error('Failed to fetch portfolio:', error)
      
      // Use mock data as fallback
      setPortfolio({
        address: address,
        total_value_usd: 0,
        holdings: [],
        allocation: {},
        change_24h: 0
      })
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="text-gray-400">Loading portfolio...</div>
  }

  if (!portfolio || portfolio.total_value_usd === 0) {
    return (
      <div className="card-goodcrypto text-center py-12">
        <p className="text-gray-400">No holdings found</p>
        <p className="text-sm text-gray-500 mt-2">Fund your wallet to start trading</p>
      </div>
    )
  }

  const chartData = Object.entries(portfolio.allocation).map(([name, value]) => ({
    name,
    value: parseFloat(value.toFixed(2))
  }))

  return (
    <div className="card-goodcrypto">
      <h2 className="text-xl font-semibold text-white mb-6">Portfolio Holdings</h2>
      
      <div className="mb-6">
        <p className="text-sm text-gray-400">Total Value</p>
        <p className="text-3xl font-bold text-green-500">
          ${portfolio.total_value_usd.toFixed(2)}
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          <h3 className="text-sm font-medium text-gray-300 mb-4">Holdings</h3>
          <div className="space-y-3">
            {portfolio.holdings.map((token, idx) => (
              <div key={idx} className="flex items-center justify-between p-3 bg-gray-800/50 rounded-lg">
                <div>
                  <p className="text-white font-medium">{token.symbol}</p>
                  <p className="text-sm text-gray-400">{token.name}</p>
                </div>
                <div className="text-right">
                  <p className="text-white">{parseFloat(token.balance).toFixed(6)}</p>
                  <p className="text-sm text-gray-400">${token.usd_value.toFixed(2)}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div>
          <h3 className="text-sm font-medium text-gray-300 mb-4">Allocation</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${value}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}

export default PortfolioHoldings
