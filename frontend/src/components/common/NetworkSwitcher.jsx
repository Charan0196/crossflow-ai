import React, { useState } from 'react'
import { useNetwork, useSwitchNetwork } from 'wagmi'
import { ChevronDown, Check } from 'lucide-react'

const networks = [
  { id: 1, name: 'Ethereum', symbol: 'ETH', icon: '⟠', color: '#627EEA' },
  { id: 137, name: 'Polygon', symbol: 'MATIC', icon: '⬡', color: '#8247E5' },
  { id: 42161, name: 'Arbitrum', symbol: 'ETH', icon: '🔵', color: '#28A0F0' },
  { id: 10, name: 'Optimism', symbol: 'ETH', icon: '🔴', color: '#FF0420' },
  { id: 56, name: 'BNB Chain', symbol: 'BNB', icon: '🟡', color: '#F3BA2F' },
  { id: 43114, name: 'Avalanche', symbol: 'AVAX', icon: '🔺', color: '#E84142' },
  { id: 8453, name: 'Base', symbol: 'ETH', icon: '🔵', color: '#0052FF' },
  { id: 11155111, name: 'Sepolia', symbol: 'ETH', icon: '🧪', color: '#CFB5F0' },
]

const NetworkSwitcher = () => {
  const { chain } = useNetwork()
  const { switchNetwork } = useSwitchNetwork()
  const [isOpen, setIsOpen] = useState(false)

  const currentNetwork = networks.find(n => n.id === chain?.id) || networks[0]

  const handleNetworkSwitch = (networkId) => {
    if (switchNetwork) {
      switchNetwork(networkId)
    }
    setIsOpen(false)
  }

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg hover:border-green-500 transition-colors"
      >
        <span className="text-xl">{currentNetwork.icon}</span>
        <span className="text-sm font-medium text-white">{currentNetwork.name}</span>
        <ChevronDown 
          size={16} 
          className={`text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} 
        />
      </button>

      {isOpen && (
        <>
          <div 
            className="fixed inset-0 z-40" 
            onClick={() => setIsOpen(false)} 
          />
          <div className="absolute top-full right-0 mt-2 w-64 bg-gray-800 border border-gray-700 rounded-xl py-2 z-50 shadow-2xl">
            {networks.map((network) => (
              <button
                key={network.id}
                onClick={() => handleNetworkSwitch(network.id)}
                className={`w-full px-4 py-3 text-left hover:bg-gray-700 transition-colors flex items-center gap-3 ${
                  chain?.id === network.id ? 'bg-gray-700/50' : ''
                }`}
              >
                <span className="text-2xl">{network.icon}</span>
                <div className="flex-1">
                  <p className="text-sm font-semibold text-white">{network.name}</p>
                  <p className="text-xs text-gray-400">{network.symbol}</p>
                </div>
                {chain?.id === network.id && (
                  <Check size={16} className="text-green-500" />
                )}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  )
}

export default NetworkSwitcher
