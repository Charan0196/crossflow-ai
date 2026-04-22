import React, { useEffect, useState } from 'react'
import { Wallet, Copy, Check } from 'lucide-react'
import { useWalletStore } from '../../stores/walletStore'

const WalletHeader = () => {
  const { address, ethBalance, isTrading, initialize } = useWalletStore()
  const [copied, setCopied] = useState(false)
  const [showTooltip, setShowTooltip] = useState(false)

  useEffect(() => {
    initialize()
    const interval = setInterval(() => initialize(), 30000)
    return () => clearInterval(interval)
  }, [])

  const formatAddress = (addr) => {
    if (!addr) return ''
    return `${addr.slice(0, 6)}...${addr.slice(-4)}`
  }

  const copyAddress = () => {
    navigator.clipboard.writeText(address)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="flex items-center gap-3 px-4 py-2 bg-gray-800/50 rounded-lg border border-gray-700">
      <Wallet className="w-5 h-5 text-green-500" />
      
      <div className="flex items-center gap-2">
        <div 
          className="relative"
          onMouseEnter={() => setShowTooltip(true)}
          onMouseLeave={() => setShowTooltip(false)}
        >
          <span className="text-sm text-gray-300 font-mono">
            {formatAddress(address)}
          </span>
          
          {showTooltip && (
            <div className="absolute top-full mt-2 left-0 z-50 bg-gray-900 border border-gray-700 rounded-lg p-3 shadow-xl min-w-[300px]">
              <div className="flex items-center justify-between gap-2">
                <span className="text-xs text-gray-400 font-mono break-all">{address}</span>
                <button
                  onClick={copyAddress}
                  className="p-1 hover:bg-gray-800 rounded transition-colors"
                >
                  {copied ? (
                    <Check className="w-4 h-4 text-green-500" />
                  ) : (
                    <Copy className="w-4 h-4 text-gray-400" />
                  )}
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="h-4 w-px bg-gray-700" />
        
        <span className="text-sm font-semibold text-white">
          {parseFloat(ethBalance).toFixed(4)} ETH
        </span>

        {isTrading && (
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            <span className="text-xs text-green-500">Trading</span>
          </div>
        )}
      </div>
    </div>
  )
}

export default WalletHeader
