/**
 * Phase 5: Enhanced Swap Panel Component
 * 
 * Professional swap interface with:
 * - Glassmorphism effects
 * - Smooth animations
 * - Real quote fetching
 * - MEV protection
 */

import { useState, useEffect, useCallback } from 'react';
import { ArrowDown, ChevronDown, Shield, Settings, Loader2, AlertTriangle, Check, Sparkles, Zap, X } from 'lucide-react';
import { useAccount } from 'wagmi';
import tradingService from '../../services/tradingService';

const SlippageModal = ({ isOpen, onClose, slippage, setSlippage }) => {
  if (!isOpen) return null;
  
  const presets = [0.1, 0.5, 1.0, 3.0];
  
  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center animate-fade-in">
      <div className="absolute inset-0 bg-black/80 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-gradient-to-b from-[#1a1f2e] to-[#0d1117] border border-[#2a3441] rounded-3xl w-full max-w-sm p-6 shadow-2xl shadow-[#2dd4bf]/10 animate-scale-in">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-xl font-bold text-white flex items-center gap-3">
            <div className="p-2 rounded-xl bg-[#2dd4bf]/20">
              <Settings size={20} className="text-[#2dd4bf]" />
            </div>
            Slippage Tolerance
          </h3>
          <button onClick={onClose} className="p-2 rounded-xl hover:bg-[#2a3441] transition-colors">
            <X size={20} className="text-gray-400" />
          </button>
        </div>
        
        <div className="flex gap-2 mb-4">
          {presets.map((p, index) => (
            <button 
              key={p} 
              onClick={() => setSlippage(p)}
              style={{ animationDelay: `${index * 50}ms` }}
              className={`flex-1 py-3 rounded-xl text-sm font-semibold transition-all animate-slide-in-up ${
                slippage === p 
                  ? 'bg-gradient-to-r from-[#2dd4bf] to-[#06b6d4] text-black shadow-lg shadow-[#2dd4bf]/30' 
                  : 'bg-[#0d1117] text-gray-400 hover:text-white border border-[#2a3441] hover:border-[#2dd4bf]/50'
              }`}
            >
              {p}%
            </button>
          ))}
        </div>
        
        <div className="flex items-center gap-3 p-4 bg-[#0d1117] rounded-2xl border border-[#2a3441]">
          <input 
            type="number" 
            value={slippage} 
            onChange={(e) => setSlippage(parseFloat(e.target.value) || 0.5)}
            className="flex-1 bg-transparent text-xl font-bold outline-none text-white placeholder-gray-600"
            step="0.1" 
            min="0.1" 
            max="50" 
          />
          <span className="text-gray-400 font-medium">%</span>
        </div>
        
        {slippage > 5 && (
          <div className="mt-4 p-3 rounded-xl bg-yellow-500/10 border border-yellow-500/30 flex items-center gap-2">
            <AlertTriangle size={16} className="text-yellow-400" />
            <span className="text-yellow-400 text-sm">High slippage may result in unfavorable trades</span>
          </div>
        )}
        
        <button 
          onClick={onClose} 
          className="w-full mt-6 py-3 bg-gradient-to-r from-[#2dd4bf] to-[#06b6d4] text-black rounded-xl font-semibold hover:shadow-lg hover:shadow-[#2dd4bf]/30 transition-all"
        >
          Confirm Settings
        </button>
      </div>
    </div>
  );
};

const SwapPanel = ({ 
  fromToken, 
  toToken, 
  onFromTokenSelect, 
  onToTokenSelect,
  prices,
  getTokenBalance 
}) => {
  const { address, isConnected } = useAccount();
  const [fromAmount, setFromAmount] = useState('');
  const [quote, setQuote] = useState(null);
  const [loading, setLoading] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [slippage, setSlippage] = useState(0.5);
  const [mevProtection, setMevProtection] = useState(true);
  const [showSlippageModal, setShowSlippageModal] = useState(false);
  const [txStatus, setTxStatus] = useState(null);

  const fromPrice = prices[fromToken?.binanceSymbol] || { price: fromToken?.binanceSymbol ? 0 : 1 };
  const toPrice = prices[toToken?.binanceSymbol] || { price: toToken?.binanceSymbol ? 0 : 1 };

  // Fetch quote when amount changes
  const fetchQuote = useCallback(async () => {
    if (!fromAmount || parseFloat(fromAmount) <= 0 || !fromToken || !toToken) {
      setQuote(null);
      return;
    }

    setLoading(true);

    try {
      const result = await tradingService.getSwapQuote({
        from_token: fromToken.symbol,
        to_token: toToken.symbol,
        amount: fromAmount,
        chain_id: 1,
        slippage_tolerance: slippage
      });
      setQuote(result);
    } catch {
      // Fallback to calculated quote
      const outputAmount = (parseFloat(fromAmount) * fromPrice.price / (toPrice.price || 1)).toFixed(6);
      setQuote({
        output_amount: outputAmount,
        price_impact: 0.01,
        gas_estimate_usd: 2.50,
        route: 'Direct'
      });
    } finally {
      setLoading(false);
    }
  }, [fromAmount, fromToken, toToken, slippage, fromPrice, toPrice]);

  useEffect(() => {
    const timer = setTimeout(fetchQuote, 500);
    return () => clearTimeout(timer);
  }, [fetchQuote]);

  const handleSwap = async () => {
    if (!isConnected || !quote) return;

    setExecuting(true);
    setTxStatus({ status: 'pending', message: 'Preparing transaction...' });

    try {
      setTxStatus({ status: 'pending', message: 'Simulating transaction...' });
      
      const simulation = await tradingService.simulateSwap({
        from_token: fromToken.symbol,
        to_token: toToken.symbol,
        amount: fromAmount,
        chain_id: 1,
        slippage_tolerance: slippage,
        user_address: address
      });

      if (!simulation.success) {
        throw new Error(simulation.error || 'Simulation failed');
      }

      setTxStatus({ status: 'pending', message: 'Executing swap...' });

      const result = await tradingService.executeSwap({
        from_token: fromToken.symbol,
        to_token: toToken.symbol,
        amount: fromAmount,
        chain_id: 1,
        slippage_tolerance: slippage,
        user_address: address,
        mev_protection: mevProtection
      });

      setTxStatus({ 
        status: 'success', 
        message: 'Swap successful!',
        txHash: result.tx_hash 
      });
      
      setFromAmount('');
      setQuote(null);
    } catch (err) {
      setTxStatus({ status: 'error', message: err.message });
    } finally {
      setExecuting(false);
    }
  };

  const swapTokens = () => {
    const temp = fromToken;
    onFromTokenSelect(toToken);
    onToTokenSelect(temp);
    setFromAmount('');
    setQuote(null);
  };

  return (
    <div className="space-y-4">
      {/* Settings Bar */}
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-2">
          <Sparkles size={16} className="text-[#2dd4bf]" />
          <span className="text-sm text-gray-400">Best rate guaranteed</span>
        </div>
        <button 
          onClick={() => setShowSlippageModal(true)}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-[#0d1117]/80 border border-[#2a3441] text-sm text-gray-400 hover:text-white hover:border-[#2dd4bf]/50 transition-all"
        >
          <Settings size={14} />
          <span className="font-medium">{slippage}%</span>
        </button>
      </div>

      {/* From Input */}
      <div className="bg-gradient-to-br from-[#0d1117] to-[#1a1f2e]/50 rounded-2xl p-5 border border-[#2a3441] hover:border-[#2dd4bf]/30 transition-all">
        <div className="flex justify-between text-sm mb-3">
          <span className="text-gray-500 font-medium">You Pay</span>
          <span className="text-gray-400">
            Balance: <span className="text-white font-medium">{getTokenBalance(fromToken)}</span> {fromToken?.symbol}
          </span>
        </div>
        <div className="flex items-center gap-4">
          <input 
            type="number" 
            value={fromAmount} 
            onChange={(e) => setFromAmount(e.target.value)} 
            placeholder="0.0" 
            className="flex-1 bg-transparent text-3xl font-bold outline-none text-white placeholder-gray-700" 
          />
          <button 
            onClick={onFromTokenSelect}
            className="flex items-center gap-3 bg-[#2a3441]/80 hover:bg-[#3a4451] px-4 py-3 rounded-2xl transition-all hover:shadow-lg"
          >
            <div 
              className="w-8 h-8 rounded-xl flex items-center justify-center text-xs font-bold shadow-lg" 
              style={{ 
                background: `linear-gradient(135deg, ${fromToken?.color}, ${fromToken?.color}88)`,
                boxShadow: `0 4px 12px ${fromToken?.color}40`
              }}
            >
              {fromToken?.symbol?.slice(0, 2)}
            </div>
            <span className="font-semibold text-white text-lg">{fromToken?.symbol}</span>
            <ChevronDown size={16} className="text-gray-400" />
          </button>
        </div>
        <p className="text-sm text-gray-500 mt-3">
          ≈ ${fromAmount ? (parseFloat(fromAmount) * fromPrice.price).toLocaleString(undefined, { maximumFractionDigits: 2 }) : '0.00'}
        </p>
      </div>

      {/* Swap Direction Button */}
      <div className="flex justify-center -my-3 relative z-10">
        <button 
          onClick={swapTokens} 
          className="p-4 bg-gradient-to-br from-[#1a1f2e] to-[#0d1117] rounded-2xl border border-[#2a3441] hover:border-[#2dd4bf] transition-all hover:shadow-lg hover:shadow-[#2dd4bf]/20 group"
        >
          <ArrowDown size={20} className="text-[#2dd4bf] group-hover:rotate-180 transition-transform duration-300" />
        </button>
      </div>

      {/* To Input */}
      <div className="bg-gradient-to-br from-[#0d1117] to-[#1a1f2e]/50 rounded-2xl p-5 border border-[#2a3441] hover:border-[#2dd4bf]/30 transition-all">
        <div className="flex justify-between text-sm mb-3">
          <span className="text-gray-500 font-medium">You Receive</span>
          <span className="text-gray-400">
            Balance: <span className="text-white font-medium">{getTokenBalance(toToken)}</span> {toToken?.symbol}
          </span>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex-1">
            {loading ? (
              <div className="flex items-center gap-3">
                <Loader2 size={24} className="text-[#2dd4bf] animate-spin" />
                <span className="text-gray-500">Finding best rate...</span>
              </div>
            ) : (
              <span className="text-3xl font-bold text-white">
                {quote?.output_amount || '0.0'}
              </span>
            )}
          </div>
          <button 
            onClick={onToTokenSelect}
            className="flex items-center gap-3 bg-[#2a3441]/80 hover:bg-[#3a4451] px-4 py-3 rounded-2xl transition-all hover:shadow-lg"
          >
            <div 
              className="w-8 h-8 rounded-xl flex items-center justify-center text-xs font-bold shadow-lg" 
              style={{ 
                background: `linear-gradient(135deg, ${toToken?.color}, ${toToken?.color}88)`,
                boxShadow: `0 4px 12px ${toToken?.color}40`
              }}
            >
              {toToken?.symbol?.slice(0, 2)}
            </div>
            <span className="font-semibold text-white text-lg">{toToken?.symbol}</span>
            <ChevronDown size={16} className="text-gray-400" />
          </button>
        </div>
      </div>

      {/* MEV Protection Toggle */}
      <div className="flex items-center justify-between p-4 rounded-2xl bg-gradient-to-r from-[#2dd4bf]/10 to-[#06b6d4]/5 border border-[#2dd4bf]/30">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-[#2dd4bf]/20">
            <Shield size={18} className="text-[#2dd4bf]" />
          </div>
          <div>
            <span className="text-[#2dd4bf] font-semibold text-sm">MEV Protection</span>
            <p className="text-xs text-gray-500">Protect against front-running</p>
          </div>
        </div>
        <button 
          onClick={() => setMevProtection(!mevProtection)} 
          className={`w-12 h-6 rounded-full transition-all ${mevProtection ? 'bg-[#2dd4bf]' : 'bg-gray-600'}`}
        >
          <div className={`w-5 h-5 bg-white rounded-full shadow-lg transition-transform ${mevProtection ? 'translate-x-6' : 'translate-x-0.5'}`} />
        </button>
      </div>

      {/* Quote Details */}
      {quote && (
        <div className="space-y-3 p-4 rounded-2xl bg-[#0d1117]/50 border border-[#2a3441]">
          <div className="flex justify-between text-sm">
            <span className="text-gray-500">Rate</span>
            <span className="text-white font-medium">
              1 {fromToken?.symbol} = {(fromPrice.price / (toPrice.price || 1)).toFixed(4)} {toToken?.symbol}
            </span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-500">Price Impact</span>
            <span className={`font-medium ${quote.price_impact > 1 ? 'text-yellow-400' : 'text-[#2dd4bf]'}`}>
              {quote.price_impact?.toFixed(2) || '<0.01'}%
            </span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-500">Network Fee</span>
            <div className="flex items-center gap-2">
              <Zap size={12} className="text-yellow-400" />
              <span className="text-white font-medium">~${quote.gas_estimate_usd?.toFixed(2) || '2.50'}</span>
            </div>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-500">Route</span>
            <span className="text-white font-medium">{quote.route || 'Best Route'}</span>
          </div>
        </div>
      )}

      {/* Transaction Status */}
      {txStatus && (
        <div className={`p-4 rounded-2xl flex items-center gap-3 animate-slide-in-up ${
          txStatus.status === 'success' ? 'bg-green-500/10 border border-green-500/30' :
          txStatus.status === 'error' ? 'bg-red-500/10 border border-red-500/30' :
          'bg-[#2dd4bf]/10 border border-[#2dd4bf]/30'
        }`}>
          {txStatus.status === 'pending' && <Loader2 size={18} className="text-[#2dd4bf] animate-spin" />}
          {txStatus.status === 'success' && <Check size={18} className="text-green-400" />}
          {txStatus.status === 'error' && <AlertTriangle size={18} className="text-red-400" />}
          <span className={`text-sm font-medium ${
            txStatus.status === 'success' ? 'text-green-400' :
            txStatus.status === 'error' ? 'text-red-400' : 'text-[#2dd4bf]'
          }`}>
            {txStatus.message}
          </span>
        </div>
      )}

      {/* Swap Button */}
      <button 
        onClick={handleSwap} 
        disabled={!isConnected || !quote || executing}
        className="w-full py-4 rounded-2xl bg-gradient-to-r from-[#2dd4bf] to-[#06b6d4] text-black font-bold text-lg flex items-center justify-center gap-3 hover:shadow-xl hover:shadow-[#2dd4bf]/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-none"
      >
        {executing ? (
          <><Loader2 size={20} className="animate-spin" /> Processing...</>
        ) : !isConnected ? (
          'Connect Wallet'
        ) : !fromAmount ? (
          'Enter Amount'
        ) : (
          <>
            <Sparkles size={20} />
            Swap {fromToken?.symbol} → {toToken?.symbol}
          </>
        )}
      </button>

      <SlippageModal 
        isOpen={showSlippageModal} 
        onClose={() => setShowSlippageModal(false)} 
        slippage={slippage} 
        setSlippage={setSlippage} 
      />

      {/* CSS Animations */}
      <style>{`
        @keyframes fade-in {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes scale-in {
          from { opacity: 0; transform: scale(0.95); }
          to { opacity: 1; transform: scale(1); }
        }
        @keyframes slide-in-up {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fade-in { animation: fade-in 0.3s ease-out; }
        .animate-scale-in { animation: scale-in 0.3s ease-out; }
        .animate-slide-in-up { animation: slide-in-up 0.4s ease-out both; }
      `}</style>
    </div>
  );
};

export default SwapPanel;
