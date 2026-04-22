import React from 'react'
import { NavLink } from 'react-router-dom'
import { useAuthStore } from '../../stores/authStore'
import { 
  LayoutDashboard, 
  TrendingUp, 
  Wallet, 
  Settings, 
  Shield,
  BarChart3,
  Zap
} from 'lucide-react'

const Sidebar = () => {
  const { user } = useAuthStore()

  const navItems = [
    {
      name: 'Dashboard',
      path: '/dashboard',
      icon: LayoutDashboard,
    },
    {
      name: 'Trading',
      path: '/trading',
      icon: TrendingUp,
    },
    {
      name: 'Portfolio',
      path: '/portfolio',
      icon: Wallet,
    },
    {
      name: 'Analytics',
      path: '/analytics',
      icon: BarChart3,
    },
  ]

  // Add admin route if user is admin
  if (user?.is_admin) {
    navItems.push({
      name: 'Admin',
      path: '/admin',
      icon: Shield,
    })
  }

  return (
    <aside className="w-64 bg-gray-800 border-r border-gray-700 min-h-screen">
      <div className="p-6">
        <nav className="space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-300 hover:text-white hover:bg-gray-700'
                  }`
                }
              >
                <Icon className="w-5 h-5" />
                <span>{item.name}</span>
              </NavLink>
            )
          })}
        </nav>

        {/* Quick Actions */}
        <div className="mt-8">
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
            Quick Actions
          </h3>
          <div className="space-y-2">
            <button className="w-full flex items-center space-x-3 px-4 py-2 text-sm text-gray-300 hover:text-white hover:bg-gray-700 rounded-lg transition-colors">
              <Zap className="w-4 h-4" />
              <span>Auto Trade</span>
            </button>
            <button className="w-full flex items-center space-x-3 px-4 py-2 text-sm text-gray-300 hover:text-white hover:bg-gray-700 rounded-lg transition-colors">
              <Settings className="w-4 h-4" />
              <span>Settings</span>
            </button>
          </div>
        </div>
      </div>
    </aside>
  )
}

export default Sidebar