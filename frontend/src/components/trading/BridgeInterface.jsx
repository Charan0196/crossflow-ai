import React, { useState, useEffect } from 'react'
import { useAccount, useNetwork } from 'wagmi'
import { useQuery } from '@tanstack/react-query'
import { tradingAPI } from '../../config/api'
import { chainConfig } from '../../config/wagmi'
import { toast } from 'react-toastify'
import { 
  Bridge, 
  ArrowRight, 
  Clock, 
  DollarSign,
  ChevronDown,
  AlertTriangle,
  Loader2
} from 'lucide-react'

const BridgeInterface = () => {
  const { address } = useAccount()
  const { chain } = useNetwork()
  
  const [fromChain, setFromChain] = useState(1) // Ethereum
  const [toChain, setToChain] = useState(137) // Polygon
  const [fromToken, setFromToken] = useState({
    address: 'native',
    symbol: 'ETH',
    name: 'Ethereum'
  })
  const [toToken, setToToken] = useState({
    address: 'native',
    symbol: 'MATIC',
    name: 'Polygon'
  })
  const [amount, setAmount] = useState('')
  const [toAddress, setToAddress] = useState(address || '')
  const [quote, setQuote] = useState(null)
  const [routes, setRoutes] = useState([])
  const [selectedRoute, setSelectedRoute] = useState(null)
  const [isGettingQuote, setIsGettingQuote] = useState(false)

  // Fetch supported chains
  const { data: chainsData } = useQuery({
    queryKey: ['bridge-chains'],
    queryFn: () => tradingAPI.getBridgeChains(),
  })

  // Fetch supported tokens
  const { data: tokensData } = useQuery({
    queryKey: ['bridge-tokens', fromChain],
    queryFn: () => tradingAPI.getBridgeTokens(fromChain),
    enabled: !!fromChain,
  })

  const chains = chainsData?.data?.chains || []
  const tokens = tokensData?.data?.tokens || {}

  useEffect(() => {
    setToAddress(address || '')
  }, [address])

  useEffect(() => {
    if (amount && parseFloat(amount) > 0 && fromToken && toToken && address) {
      getBridgeQuote()
    }
  }, [amount, fromToken, toToken, fromChain, toChain, address])

  const getBridgeQuote = async () => {
    if (!amount || parseFloat(amount) <= 0 || !address) return
    
    setIsGettingQuote(true)
    try {
      const amountWei = (parseFloat(amount) * Math.pow(10, 18)).toString()
      
      const [quoteResponse, routesResponse] = await Promise.all([
        tradingAPI.getBridgeQuote({
          from_chain: fromChain,
          to_chain: toChain,
          from_token: fromToken.address,
          to_token: toToken.address,
          amount: amountWei,
          to_address: toAddress
        }, address),
        tradingAPI.getBridgeRoutes({
          from_chain: fromChain,
          to_chain: toChain,
          from_token: fromToken.address,
          to_token: toToken.address,
          amount: amountWei,
          to_address: toAddress
        }, address)
      ])
      
      if (quoteResponse.data) {
        setQuote(quoteResponse.data)
      }
      
      if (routesResponse.data?.routes) {
        setRoutes(routesResponse.data.routes)
        if (routesResponse.data.routes.length > 0) {
          setSelectedRoute(routesResponse.data.routes[0])
        }
      }
    } catch (error) {
      console.error('Error getting bridge quote:', error)
      toast.error('Failed to get bridge quote')
    } finally {
      setIsGettingQuote(false)
    }
  }

  const handleBridge = async () => {
    if (!selectedRoute || !address) return
    
    try {
      // Here you would execute the bridge transaction
      console.log('Bridge route:', selectedRoute)
      toast.success('Bridge transaction prepared! Please confirm in your wallet.')
    } catch (error) {
      console.error('Error executing bridge:', error)
      toast.error('Failed to execute bridge transaction')
    }
  }

  const ChainSelector = ({ chainId, onSelect, label }) => {
    const chainInfo = chainConfig[chainId] || { name: 'Unknown', color: '#gray' }
    
    return (
      <div className="space-y-2">
        <label className="text-sm font-medium text-gray-300">{label}</label>
        <button className="w-full flex items-center justify-between p-3 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors">
          <div className="flex items-center space-x-3">
            <div 
              className="w-8 h-8 rounded-full flex items-center justify-center"
              style={{ backgroundColor: chainInfo.color }}
            >
              <span className="text-xs font-bold text-white">
                {chainInfo.name.slice(0, 2)}
              </span>
            </div>
            <div className="text-left">
              <p className="text-sm font-medium text-white">{chainInfo.name}</p>
              <p className="text-xs text-gray-400">Chain ID: {chainId}</p>
            </div>
          </div>
          <ChevronDown className="w-4 h-4 text-gray-400" />
        </button>
      </div>
    )
  }

  const formatTime = (seconds) => {
    if (seconds < 60) return `${seconds}s`
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m`
    return `${Math.floor(seconds / 3600)}h`
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <div className="flex items-center space-x-2 mb-6">
        <Bridge className="w-6 h-6 text-blue-400" />
        <h2 className="text-xl font-semibold text-white">Bridge Assets</h2>
      </div>

      <div className="space-y-6">
        {/* Chain Selection */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <ChainSelector 
            chainId={fromChain}
            onSelect={setFromChain}
            label="From Chain"
          />
          <ChainSelector 
            chainId={toChain}
            onSelect={setToChain}
            label="To Chain"
          />
        </div>

        {/* Token and Amount */}
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Amount</label>
            <input
              type="number"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="0.0"
              className="w-full p-3 bg-gray-700 text-white rounded-lg border-none focus:ring-2 focus:ring-blue-500 text-lg"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Destination Address</label>
            <input
              type="text"
              value={toAddress}
              onChange={(e) => setToAddress(e.target.value)}
              placeholder="0x..."
              className="w-full p-3 bg-gray-700 text-white rounded-lg border-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
            />
          </div>
        </div>

        {/* Bridge Routes */}
        {routes.length > 0 && (
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-gray-300">Available Routes</h3>
            <div className="space-y-2">
              {routes.slice(0, 3).map((route, index) => (
                <button
                  key={index}
                  onClick={() => setSelectedRoute(route)}
                  className={`w-full p-4 rounded-lg border transition-colors ${
                    selectedRoute === route
                      ? 'bg-blue-600/20 border-blue-500'
                      : 'bg-gray-700 border-gray-600 hover:bg-gray-600'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="text-left">
                        <p className="text-sm font-medium text-white">
                          {route.tool || 'Bridge Protocol'}
                        </p>
                        <div className="flex items-center space-x-4 text-xs text-gray-400">
                          <div className="flex items-center space-x-1">
                            <Clock className="w-3 h-3" />
                            <span>{formatTime(route.estimate?.executionDuration || 300)}</span>
                          </div>
                          <div className="flex items-center space-x-1">
                            <DollarSign className="w-3 h-3" />
                            <span>${route.estimate?.gasCosts?.[0]?.amount || 'N/A'}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium text-white">
                        {route.toAmount ? 
                          `${(parseFloat(route.toAmount) / Math.pow(10, 18)).toFixed(6)} ${toToken.symbol}` 
                          : 'Calculating...'
                        }
                      </p>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Quote Summary */}
        {quote && selectedRoute && (
          <div className="p-4 bg-gray-700 rounded-lg space-y-3">
            <h3 className="text-sm font-semibold text-white">Bridge Summary</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">You send</span>
                <span className="text-white">{amount} {fromToken.symbol}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">You receive</span>
                <span className="text-white">
                  {selectedRoute.toAmount ? 
                    `${(parseFloat(selectedRoute.toAmount) / Math.pow(10, 18)).toFixed(6)} ${toToken.symbol}` 
                    : 'Calculating...'
                  }
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Estimated time</span>
                <span className="text-white">
                  {formatTime(selectedRoute.estimate?.executionDuration || 300)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Bridge fee</span>
                <span className="text-white">
                  ${selectedRoute.estimate?.gasCosts?.[0]?.amount || 'N/A'}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Bridge Button */}
        <button
          onClick={handleBridge}
          disabled={!selectedRoute || !amount || parseFloat(amount) <= 0 || isGettingQuote || !toAddress}
          className="w-full py-4 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-colors flex items-center justify-center space-x-2"
        >
          {isGettingQuote ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Getting quote...</span>
            </>
          ) : !amount || parseFloat(amount) <= 0 ? (
            <span>Enter an amount</span>
          ) : !toAddress ? (
            <span>Enter destination address</span>
          ) : !selectedRoute ? (
            <span>Select a route</span>
          ) : (
            <>
              <Bridge className="w-5 h-5" />
              <span>Bridge Assets</span>
            </>
          )}
        </button>

        {/* Warning */}
        <div className="flex items-start space-x-2 p-3 bg-orange-900/20 border border-orange-700 rounded-lg">
          <AlertTriangle className="w-5 h-5 text-orange-400 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-orange-200">
            <p className="font-medium">Bridge Notice</p>
            <p>Cross-chain bridges may take several minutes to complete. Always verify the destination address.</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default BridgeInterface