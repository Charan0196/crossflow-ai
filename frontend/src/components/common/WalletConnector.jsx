import React, { useState } from 'react'
import { useConnect, useAccount, useDisconnect, useNetwork } from 'wagmi'
import { useWalletStore } from '../../stores/walletStore'
import { chainConfig } from '../../config/wagmi'
import { Wallet, ChevronDown, ExternalLink, Copy, Check } from 'lucide-react'
import { toast } from 'react-toastify'

const WalletConnector = () => {
  const [isOpen, setIsOpen] = useState(false)
  const [copied, setCopied] = useState(false)
  
  const { connect, connectors, isLoading } = useConnect()
  const { address, isConnected } = useAccount()
  const { chain } = useNetwork()
  const { disconnect } = useDisconnect()
  // const { switchNetwork } = useSwitchNetwork() // Removed - Wagmi v1 doesn't have this
  
  const { selectedChain, setSelectedChain } = useWalletStore()

  const handleConnect = (connector) => {
    connect({ connector })
    setIsOpen(false)
  }

  const handleDisconnect = () => {
    disconnect()
    setIsOpen(false)
  }

  const handleChainSwitch = (chainId) => {
    // if (switchNetwork) {
    //   switchNetwork(chainId)
    // }
    // Note: Chain switching not available in Wagmi v1
    setSelectedChain(chainId)
    setIsOpen(false)
  }

  const copyAddress = () => {
    if (address) {
      navigator.clipboard.writeText(address)
      setCopied(true)
      toast.success('Address copied to clipboard')
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const formatAddress = (addr) => {
    if (!addr) return ''
    return `${addr.slice(0, 6)}...${addr.slice(-4)}`
  }

  const getExplorerUrl = (chainId, address) => {
    const config = chainConfig[chainId]
    return config ? `${config.blockExplorer}/address/${address}` : '#'
  }

  if (!isConnected) {
    return (
      <div className="relative">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          disabled={isLoading}
        >
          <Wallet className="w-4 h-4" />
          <span>{isLoading ? 'Connecting...' : 'Connect Wallet'}</span>
        </button>

        {isOpen && (
          <div className="absolute right-0 mt-2 w-64 bg-gray-800 border border-gray-700 rounded-lg shadow-lg z-50">
            <div className="p-4">
              <h3 className="text-sm font-semibold text-gray-200 mb-3">Connect Wallet</h3>
              <div className="space-y-2">
                {connectors.map((connector) => (
                  <button
                    key={connector.id}
                    onClick={() => handleConnect(connector)}
                    className="w-full flex items-center space-x-3 px-3 py-2 text-sm text-gray-300 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
                    disabled={!connector.ready}
                  >
                    <div className="w-6 h-6 bg-gray-600 rounded-full flex items-center justify-center">
                      <Wallet className="w-3 h-3" />
                    </div>
                    <span>{connector.name}</span>
                    {!connector.ready && <span className="text-xs text-gray-500">(Not installed)</span>}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
      >
        <div 
          className="w-3 h-3 rounded-full"
          style={{ backgroundColor: chainConfig[chain?.id]?.color || '#gray' }}
        />
        <span className="text-sm">{formatAddress(address)}</span>
        <ChevronDown className="w-4 h-4" />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 bg-gray-800 border border-gray-700 rounded-lg shadow-lg z-50">
          <div className="p-4">
            {/* Wallet Info */}
            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-semibold text-gray-200">Connected Wallet</span>
                <button
                  onClick={handleDisconnect}
                  className="text-xs text-red-400 hover:text-red-300"
                >
                  Disconnect
                </button>
              </div>
              
              <div className="flex items-center space-x-2 p-3 bg-gray-700 rounded-lg">
                <div className="flex-1">
                  <div className="text-sm text-gray-300">{address}</div>
                  <div className="text-xs text-gray-400">
                    {chainConfig[chain?.id]?.name || 'Unknown Network'}
                  </div>
                </div>
                <div className="flex space-x-1">
                  <button
                    onClick={copyAddress}
                    className="p-1 text-gray-400 hover:text-white transition-colors"
                  >
                    {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                  </button>
                  <a
                    href={getExplorerUrl(chain?.id, address)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-1 text-gray-400 hover:text-white transition-colors"
                  >
                    <ExternalLink className="w-4 h-4" />
                  </a>
                </div>
              </div>
            </div>

            {/* Network Switcher */}
            <div>
              <h4 className="text-sm font-semibold text-gray-200 mb-2">Switch Network</h4>
              <div className="space-y-1">
                {Object.entries(chainConfig).map(([chainId, config]) => (
                  <button
                    key={chainId}
                    onClick={() => handleChainSwitch(parseInt(chainId))}
                    className={`w-full flex items-center space-x-3 px-3 py-2 text-sm rounded-lg transition-colors ${
                      chain?.id === parseInt(chainId)
                        ? 'bg-blue-600 text-white'
                        : 'text-gray-300 hover:text-white hover:bg-gray-700'
                    }`}
                  >
                    <div 
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: config.color }}
                    />
                    <span>{config.name}</span>
                    {chain?.id === parseInt(chainId) && (
                      <span className="ml-auto text-xs text-blue-200">Connected</span>
                    )}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default WalletConnector