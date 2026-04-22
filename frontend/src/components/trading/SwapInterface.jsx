import React, { useState, useEffect } from 'react'
import { useAccount, useNetwork } from 'wagmi'
import { useQuery } from '@tanstack/react-query'
import { tradingAPI } from '../../config/api'
import { toast } from 'react-toastify'
import { 
  ArrowDownUp, 
  Settings, 
  Info, 
  Loader2,
  ChevronDown,
  AlertTriangle
} from 'lucide-react'

const SwapInterface = () => {
  const { address } = useAccount()
  const { chain } = useNetwork()
  
  const [fromToken, setFromToken] = useState({
    address: 'native',
    symbol: 'ETH',
    name: 'Ethereum',
    decimals: 18,
    logoURI: ''
  })
  
  const [toToken, setToToken] = useState({
    address: '0xa0b86a33e6c6c9c6c6c6c6c6c6c6c6c6c6c6c6c6',
    symbol: 'USDC',
    name: 'USD Coin',
    decimals: 6,
    logoURI: ''
  })
  
  const [fromAmount, setFromAmount] = useState('')
  const [toAmount, setToAmount] = useState('')
  const [slippage, setSlippage] = useState(1.0)
  const [showSettings, setShowSettings] = useState(false)
  const [isGettingQuote, setIsGettingQuote] = useState(false)
  const [quote, setQuote] = useState(null)

  // Fetch supported tokens
  const { data: tokensData } = useQuery({
    queryKey: ['tokens', chain?.id],
    queryFn: () => tradingAPI.getTokens(chain?.id),
    enabled: !!chain?.id,
  })

  const tokens = tokensData?.data?.tokens || {}

  // Get quote when amount changes
  useEffect(() => {
    if (fromAmount && parseFloat(fromAmount) > 0 && fromToken && toToken && chain?.id) {
      getQuote()
    }
  }, [fromAmount, fromToken, toToken, chain?.id])

  const getQuote = async () => {
    if (!fromAmount || parseFloat(fromAmount) <= 0) return
    
    setIsGettingQuote(true)
    try {
      const amount = (parseFloat(fromAmount) * Math.pow(10, fromToken.decimals)).toString()
      
      const response = await tradingAPI.getSwapQuote({
        chain_id: chain.id,
        from_token: fromToken.address,
        to_token: toToken.address,
        amount: amount,
        slippage: slippage
      })
      
      if (response.data) {
        setQuote(response.data)
        const toAmountFormatted = parseFloat(response.data.toAmount) / Math.pow(10, toToken.decimals)
        setToAmount(toAmountFormatted.toFixed(6))
      }
    } catch (error) {
      console.error('Error getting quote:', error)
      toast.error('Failed to get quote')
    } finally {
      setIsGettingQuote(false)
    }
  }

  const handleSwap = async () => {
    if (!quote || !address) return
    
    try {
      const amount = (parseFloat(fromAmount) * Math.pow(10, fromToken.decimals)).toString()
      
      const response = await tradingAPI.getSwapTransaction({
        chain_id: chain.id,
        from_token: fromToken.address,
        to_token: toToken.address,
        amount: amount,
        slippage: slippage
      }, address)
      
      if (response.data?.tx) {
        // Here you would send the transaction using wagmi
        console.log('Transaction data:', response.data.tx)
        toast.success('Swap transaction prepared! Please confirm in your wallet.')
      }
    } catch (error) {
      console.error('Error preparing swap:', error)
      toast.error('Failed to prepare swap transaction')
    }
  }

  const switchTokens = () => {
    const temp = fromToken
    setFromToken(toToken)
    setToToken(temp)
    setFromAmount(toAmount)
    setToAmount('')
    setQuote(null)
  }

  const TokenSelector = ({ token, onSelect, label }) => (
    <div className="space-y-2">
      <label className="text-sm font-medium text-gray-300">{label}</label>
      <button className="w-full flex items-center justify-between p-3 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center">
            <span className="text-xs font-medium text-gray-300">
              {token.symbol?.slice(0, 2)}
            </span>
          </div>
          <div className="text-left">
            <p className="text-sm font-medium text-white">{token.symbol}</p>
            <p className="text-xs text-gray-400">{token.name}</p>
          </div>
        </div>
        <ChevronDown className="w-4 h-4 text-gray-400" />
      </button>
    </div>
  )

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-white">Swap Tokens</h2>
        <button
          onClick={() => setShowSettings(!showSettings)}
          className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
        >
          <Settings className="w-5 h-5" />
        </button>
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <div className="mb-6 p-4 bg-gray-700 rounded-lg">
          <h3 className="text-sm font-semibold text-white mb-3">Swap Settings</h3>
          <div className="space-y-3">
            <div>
              <label className="block text-sm text-gray-300 mb-1">Slippage Tolerance</label>
              <div className="flex space-x-2">
                {[0.5, 1.0, 2.0].map((value) => (
                  <button
                    key={value}
                    onClick={() => setSlippage(value)}
                    className={`px-3 py-1 text-sm rounded ${
                      slippage === value
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-600 text-gray-300 hover:bg-gray-500'
                    }`}
                  >
                    {value}%
                  </button>
                ))}
                <input
                  type="number"
                  value={slippage}
                  onChange={(e) => setSlippage(parseFloat(e.target.value) || 0)}
                  className="w-20 px-2 py-1 text-sm bg-gray-600 text-white rounded border-none focus:ring-2 focus:ring-blue-500"
                  step="0.1"
                  min="0"
                  max="50"
                />
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="space-y-4">
        {/* From Token */}
        <div className="space-y-2">
          <TokenSelector 
            token={fromToken} 
            onSelect={setFromToken} 
            label="From" 
          />
          <input
            type="number"
            value={fromAmount}
            onChange={(e) => setFromAmount(e.target.value)}
            placeholder="0.0"
            className="w-full p-3 bg-gray-700 text-white rounded-lg border-none focus:ring-2 focus:ring-blue-500 text-right text-lg"
          />
        </div>

        {/* Switch Button */}
        <div className="flex justify-center">
          <button
            onClick={switchTokens}
            className="p-2 bg-gray-700 hover:bg-gray-600 rounded-full transition-colors"
          >
            <ArrowDownUp className="w-5 h-5 text-gray-300" />
          </button>
        </div>

        {/* To Token */}
        <div className="space-y-2">
          <TokenSelector 
            token={toToken} 
            onSelect={setToToken} 
            label="To" 
          />
          <div className="relative">
            <input
              type="number"
              value={toAmount}
              readOnly
              placeholder="0.0"
              className="w-full p-3 bg-gray-700 text-white rounded-lg border-none text-right text-lg"
            />
            {isGettingQuote && (
              <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                <Loader2 className="w-5 h-5 text-blue-400 animate-spin" />
              </div>
            )}
          </div>
        </div>

        {/* Quote Info */}
        {quote && (
          <div className="p-4 bg-gray-700 rounded-lg space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">Rate</span>
              <span className="text-white">
                1 {fromToken.symbol} = {(parseFloat(toAmount) / parseFloat(fromAmount)).toFixed(6)} {toToken.symbol}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">Price Impact</span>
              <span className="text-white">
                {quote.priceImpact ? `${parseFloat(quote.priceImpact).toFixed(2)}%` : 'N/A'}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">Estimated Gas</span>
              <span className="text-white">
                {quote.estimatedGas ? `${parseInt(quote.estimatedGas).toLocaleString()}` : 'N/A'}
              </span>
            </div>
          </div>
        )}

        {/* Swap Button */}
        <button
          onClick={handleSwap}
          disabled={!quote || !fromAmount || parseFloat(fromAmount) <= 0 || isGettingQuote}
          className="w-full py-4 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-colors"
        >
          {!fromAmount || parseFloat(fromAmount) <= 0
            ? 'Enter an amount'
            : !quote
            ? 'Getting quote...'
            : 'Swap'
          }
        </button>

        {/* Warning */}
        <div className="flex items-start space-x-2 p-3 bg-yellow-900/20 border border-yellow-700 rounded-lg">
          <AlertTriangle className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-yellow-200">
            <p className="font-medium">Important</p>
            <p>Always verify token addresses and amounts before confirming transactions.</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SwapInterface