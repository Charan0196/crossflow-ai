import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { adminAPI } from '../config/api'
import { 
  Users, 
  Activity, 
  DollarSign, 
  TrendingUp,
  Shield,
  Database,
  BarChart3,
  RefreshCw
} from 'lucide-react'

const AdminPage = () => {
  const [activeTab, setActiveTab] = useState('overview')

  // Fetch admin data
  const { data: stats, isLoading: statsLoading, refetch: refetchStats } = useQuery({
    queryKey: ['admin-stats'],
    queryFn: () => adminAPI.getStats(),
  })

  const { data: users, isLoading: usersLoading } = useQuery({
    queryKey: ['admin-users'],
    queryFn: () => adminAPI.getUsers(50, 0),
    enabled: activeTab === 'users',
  })

  const { data: recentTx, isLoading: txLoading } = useQuery({
    queryKey: ['admin-recent-transactions'],
    queryFn: () => adminAPI.getRecentTransactions(20),
    enabled: activeTab === 'transactions',
  })

  const { data: analytics, isLoading: analyticsLoading } = useQuery({
    queryKey: ['admin-analytics'],
    queryFn: () => adminAPI.getChainAnalytics(),
    enabled: activeTab === 'analytics',
  })

  const statsData = stats?.data
  const usersData = users?.data || []
  const transactionsData = recentTx?.data || []
  const analyticsData = analytics?.data

  const tabs = [
    { id: 'overview', name: 'Overview', icon: BarChart3 },
    { id: 'users', name: 'Users', icon: Users },
    { id: 'transactions', name: 'Transactions', icon: Activity },
    { id: 'analytics', name: 'Analytics', icon: TrendingUp },
  ]

  const overviewStats = [
    {
      name: 'Total Users',
      value: statsData?.users?.total || 0,
      change: `${statsData?.users?.active || 0} active`,
      icon: Users,
      color: 'blue'
    },
    {
      name: 'Total Volume',
      value: statsData?.transactions?.volume_usd ? `$${parseFloat(statsData.transactions.volume_usd).toLocaleString()}` : '$0',
      change: `${statsData?.transactions?.total || 0} transactions`,
      icon: DollarSign,
      color: 'green'
    },
    {
      name: 'Total TVL',
      value: statsData?.portfolio?.total_tvl_usd ? `$${parseFloat(statsData.portfolio.total_tvl_usd).toLocaleString()}` : '$0',
      change: `${statsData?.portfolio?.total_portfolios || 0} portfolios`,
      icon: TrendingUp,
      color: 'purple'
    },
    {
      name: 'Platform Health',
      value: 'Healthy',
      change: 'All systems operational',
      icon: Shield,
      color: 'emerald'
    }
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Admin Dashboard</h1>
          <p className="text-gray-400 mt-1">Platform management and analytics</p>
        </div>
        <button
          onClick={() => refetchStats()}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          <span>Refresh</span>
        </button>
      </div>

      {/* Tab Navigation */}
      <div className="bg-gray-800 rounded-lg p-1 inline-flex">
        {tabs.map((tab) => {
          const Icon = tab.icon
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center space-x-2 px-4 py-2 rounded-md transition-colors ${
                activeTab === tab.id
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{tab.name}</span>
            </button>
          )
        })}
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {overviewStats.map((stat) => {
              const Icon = stat.icon
              return (
                <div key={stat.name} className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-400">{stat.name}</p>
                      <p className="text-2xl font-bold text-white mt-1">{stat.value}</p>
                    </div>
                    <div className={`p-3 bg-${stat.color}-600/20 rounded-lg`}>
                      <Icon className={`w-6 h-6 text-${stat.color}-400`} />
                    </div>
                  </div>
                  <p className="text-sm text-gray-400 mt-4">{stat.change}</p>
                </div>
              )
            })}
          </div>

          {/* System Status */}
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h3 className="text-lg font-semibold text-white mb-4">System Status</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="flex items-center justify-between p-3 bg-gray-700 rounded-lg">
                <span className="text-sm text-gray-300">API Status</span>
                <span className="text-sm text-green-400">Operational</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-700 rounded-lg">
                <span className="text-sm text-gray-300">Database</span>
                <span className="text-sm text-green-400">Connected</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-700 rounded-lg">
                <span className="text-sm text-gray-300">Web3 Services</span>
                <span className="text-sm text-green-400">Active</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'users' && (
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h3 className="text-lg font-semibold text-white mb-4">User Management</h3>
          {usersLoading ? (
            <div className="flex items-center justify-center h-32">
              <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                    <th className="pb-3">User</th>
                    <th className="pb-3">Email</th>
                    <th className="pb-3">Status</th>
                    <th className="pb-3">Role</th>
                    <th className="pb-3">Joined</th>
                    <th className="pb-3">Last Login</th>
                  </tr>
                </thead>
                <tbody>
                  {usersData.map((user) => (
                    <tr key={user.id} className="border-t border-gray-700">
                      <td className="py-3 text-sm font-medium text-white">{user.username}</td>
                      <td className="py-3 text-sm text-gray-300">{user.email}</td>
                      <td className="py-3">
                        <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                          user.is_active ? 'bg-green-600/20 text-green-400' : 'bg-red-600/20 text-red-400'
                        }`}>
                          {user.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="py-3">
                        <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                          user.is_admin ? 'bg-purple-600/20 text-purple-400' : 'bg-gray-600/20 text-gray-400'
                        }`}>
                          {user.is_admin ? 'Admin' : 'User'}
                        </span>
                      </td>
                      <td className="py-3 text-sm text-gray-400">
                        {new Date(user.created_at).toLocaleDateString()}
                      </td>
                      <td className="py-3 text-sm text-gray-400">
                        {user.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {activeTab === 'transactions' && (
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h3 className="text-lg font-semibold text-white mb-4">Recent Transactions</h3>
          {txLoading ? (
            <div className="flex items-center justify-center h-32">
              <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                    <th className="pb-3">Hash</th>
                    <th className="pb-3">User</th>
                    <th className="pb-3">Type</th>
                    <th className="pb-3">Tokens</th>
                    <th className="pb-3">Value</th>
                    <th className="pb-3">Status</th>
                    <th className="pb-3">Date</th>
                  </tr>
                </thead>
                <tbody>
                  {transactionsData.map((tx) => (
                    <tr key={tx.id} className="border-t border-gray-700">
                      <td className="py-3 text-sm font-mono text-gray-300">
                        {tx.tx_hash ? `${tx.tx_hash.slice(0, 10)}...` : 'N/A'}
                      </td>
                      <td className="py-3 text-sm text-white">User #{tx.user_id}</td>
                      <td className="py-3">
                        <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                          tx.type === 'swap' ? 'bg-blue-600/20 text-blue-400' :
                          tx.type === 'bridge' ? 'bg-purple-600/20 text-purple-400' :
                          'bg-green-600/20 text-green-400'
                        }`}>
                          {tx.type}
                        </span>
                      </td>
                      <td className="py-3 text-sm text-gray-300">
                        {tx.from_token_symbol} → {tx.to_token_symbol}
                      </td>
                      <td className="py-3 text-sm text-white">
                        {tx.usd_value ? `$${parseFloat(tx.usd_value).toLocaleString()}` : '-'}
                      </td>
                      <td className="py-3">
                        <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                          tx.status === 'confirmed' ? 'bg-green-600/20 text-green-400' :
                          tx.status === 'pending' ? 'bg-yellow-600/20 text-yellow-400' :
                          'bg-red-600/20 text-red-400'
                        }`}>
                          {tx.status}
                        </span>
                      </td>
                      <td className="py-3 text-sm text-gray-400">
                        {new Date(tx.created_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {activeTab === 'analytics' && (
        <div className="space-y-6">
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h3 className="text-lg font-semibold text-white mb-4">Chain Analytics</h3>
            {analyticsLoading ? (
              <div className="flex items-center justify-center h-32">
                <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
              </div>
            ) : analyticsData?.chains ? (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                      <th className="pb-3">Chain</th>
                      <th className="pb-3">Transactions</th>
                      <th className="pb-3">Volume</th>
                      <th className="pb-3">TVL</th>
                    </tr>
                  </thead>
                  <tbody>
                    {analyticsData.chains.map((chain) => (
                      <tr key={chain.chain_id} className="border-t border-gray-700">
                        <td className="py-3">
                          <div className="flex items-center space-x-2">
                            <span className="text-sm font-medium text-white">{chain.chain_name}</span>
                          </div>
                        </td>
                        <td className="py-3 text-sm text-white">{chain.transaction_count.toLocaleString()}</td>
                        <td className="py-3 text-sm text-white">
                          ${parseFloat(chain.volume_usd).toLocaleString()}
                        </td>
                        <td className="py-3 text-sm text-white">
                          ${parseFloat(chain.tvl_usd).toLocaleString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-gray-400">No analytics data available</p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default AdminPage