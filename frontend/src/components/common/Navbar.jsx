import React from 'react'
import { Link } from 'react-router-dom'
import { useAuthStore } from '../../stores/authStore'
import WalletConnector from './WalletConnector'
import { LogOut, User, Settings } from 'lucide-react'

const Navbar = () => {
  const { user, logout } = useAuthStore()

  return (
    <nav className="bg-gray-800 border-b border-gray-700 px-6 py-4">
      <div className="flex items-center justify-between">
        {/* Logo */}
        <Link to="/dashboard" className="flex items-center space-x-2">
          <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-sm">CF</span>
          </div>
          <span className="text-xl font-bold text-white">CrossFlow AI</span>
        </Link>

        {/* Right side */}
        <div className="flex items-center space-x-4">
          {/* Wallet Connector */}
          <WalletConnector />

          {/* User Menu */}
          <div className="flex items-center space-x-2">
            <div className="flex items-center space-x-2 text-gray-300">
              <User className="w-4 h-4" />
              <span className="text-sm">{user?.username}</span>
            </div>
            
            <button
              onClick={logout}
              className="flex items-center space-x-1 px-3 py-2 text-sm text-gray-300 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
            >
              <LogOut className="w-4 h-4" />
              <span>Logout</span>
            </button>
          </div>
        </div>
      </div>
    </nav>
  )
}

export default Navbar