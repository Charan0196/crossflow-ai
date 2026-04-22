/**
 * Phase 5: Enhanced Order Panel Component
 * 
 * Professional limit order interface with:
 * - Glassmorphism effects
 * - Smooth animations
 * - Multiple order types
 * - Open orders management
 */

import { useState, useEffect } from 'react';
import { ChevronDown, Loader2, X, Clock, TrendingUp, TrendingDown, Target, AlertTriangle, Sparkles, Zap } from 'lucide-react';
import { useAccount } from 'wagmi';
import tradingService from '../../services/tradingService';

const OrderPanel = ({ 
  fromToken, 
  toToken, 
  onFromTokenSelect, 
  onToTokenSelect,
  prices 
}) => {
  const { address, isConnected } = useAccount();
  const [orderType, setOrderType] = useState('limit');
  const [amount, setAmount] = useState('');
  const [limitPrice, setLimitPrice] = useState('');
  const [stopPrice, setStopPrice] = useState('');
  const [takeProfitPrice, setTakeProfitPrice] = useState('');
  const [loading, setLoading] = useState(false);
  const [openOrders, setOpenOrders] = useState([]);
  const [error, setError] = useState(null);

  const currentPrice = prices[fromToken?.binanceSymbol]?.price || 0;

  useEffect(() => {
    if (currentPrice && !limitPrice) {
      setLimitPrice(currentPrice.toFixed(2));
    }
  }, [currentPrice, limitPrice]);

  useEffect(() => {
    if (isConnected) {
      fetchOpenOrders();
    }
  }, [isConnected]);

  const fetchOpenOrders = async () => {
    try {
      const orders = await tradingService.getOpenOrders();
      setOpenOrders(orders.orders || []);
    } catch (err) {
      console.error('Failed to fetch orders:', err);
    }
  };

  const handleCreateOrder = async () => {
    if (!isConnected || !amount || !limitPrice) return;

    setLoading(true);
    setError(null);

    try {
      const orderData = {
        user_address: address,
        order_type: orderType,
        from_token: fromToken.symbol,
        to_token: toToken.symbol,
        amount: parseFloat(amount),
        chain_id: 1
      };

      if (orderType === 'limit') {
        orderData.limit_price = parseFloat(limitPrice);
      } else if (orderType === 'stop_loss') {
        orderData.stop_price = parseFloat(stopPrice);
      } else if (orderType === 'take_profit') {
        orderData.take_profit_price = parseFloat(takeProfitPrice);
      }

      await tradingService.createOrder(orderData);
      
      setAmount('');
      setLimitPrice('');
      setStopPrice('');
      setTakeProfitPrice('');
      fetchOpenOrders();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCancelOrder = async (orderId) => {
    try {
      await tradingService.cancelOrder(orderId);
      fetchOpenOrders();
    } catch (err) {
      console.error('Failed to cancel order:', err);
    }
  };

  const orderTypes = [
    { id: 'limit', label: 'Limit', icon: Target, color: 'from-blue-500 to-cyan-500' },
    { id: 'stop_loss', label: 'Stop Loss', icon: TrendingDown, color: 'from-red-500 to-orange-500' },
    { id: 'take_profit', label: 'Take Profit', icon: TrendingUp, color: 'from-green-500 to-emerald-500' }
  ];

  const selectedOrderType = orderTypes.find(t => t.id === orderType);

  return (
    <div className="space-y-5">
      {/* Order Type Tabs */}
      <div className="flex gap-2 p-1.5 bg-[#0d1117] rounded-2xl">
        {orderTypes.map((type, index) => {
          const Icon = type.icon;
          return (
            <button 
              key={type.id} 
              onClick={() => setOrderType(type.id)}
              style={{ animationDelay: `${index * 50}ms` }}
              className={`flex-1 py-3 rounded-xl text-xs font-semibold transition-all flex items-center justify-center gap-2 ${
                orderType === type.id 
                  ? `bg-gradient-to-r ${type.color} text-white shadow-lg` 
                  : 'text-gray-400 hover:text-white hover:bg-[#2a3441]/50'
              }`}
            >
              <Icon size={14} />
              {type.label}
            </button>
          );
        })}
      </div>

      {/* Token Pair Selector */}
      <div className="flex items-center justify-between p-4 bg-gradient-to-br from-[#0d1117] to-[#1a1f2e]/50 rounded-2xl border border-[#2a3441]">
        <button 
          onClick={onFromTokenSelect} 
          className="flex items-center gap-3 hover:bg-[#2a3441]/50 p-2 rounded-xl transition-all"
        >
          <div 
            className="w-10 h-10 rounded-xl flex items-center justify-center text-xs font-bold shadow-lg" 
            style={{ 
              background: `linear-gradient(135deg, ${fromToken?.color}, ${fromToken?.color}88)`,
              boxShadow: `0 4px 12px ${fromToken?.color}40`
            }}
          >
            {fromToken?.symbol?.slice(0, 2)}
          </div>
          <span className="font-semibold text-white">{fromToken?.symbol}</span>
          <ChevronDown size={14} className="text-gray-400" />
        </button>
        
        <div className="px-4">
          <div className="w-8 h-8 rounded-full bg-[#2a3441] flex items-center justify-center">
            <span className="text-gray-400">→</span>
          </div>
        </div>
        
        <button 
          onClick={onToTokenSelect} 
          className="flex items-center gap-3 hover:bg-[#2a3441]/50 p-2 rounded-xl transition-all"
        >
          <div 
            className="w-10 h-10 rounded-xl flex items-center justify-center text-xs font-bold shadow-lg" 
            style={{ 
              background: `linear-gradient(135deg, ${toToken?.color}, ${toToken?.color}88)`,
              boxShadow: `0 4px 12px ${toToken?.color}40`
            }}
          >
            {toToken?.symbol?.slice(0, 2)}
          </div>
          <span className="font-semibold text-white">{toToken?.symbol}</span>
          <ChevronDown size={14} className="text-gray-400" />
        </button>
      </div>

      {/* Current Price Display */}
      <div className="flex items-center justify-between p-4 rounded-2xl bg-[#2dd4bf]/5 border border-[#2dd4bf]/20">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-[#2dd4bf]/20">
            <Zap size={16} className="text-[#2dd4bf]" />
          </div>
          <span className="text-gray-400 text-sm font-medium">Current Price</span>
        </div>
        <span className="text-white font-bold text-lg">${currentPrice.toLocaleString()}</span>
      </div>

      {/* Amount Input */}
      <div className="space-y-2">
        <label className="text-sm text-gray-400 font-medium flex items-center gap-2">
          <Sparkles size={14} className="text-[#2dd4bf]" />
          Amount ({fromToken?.symbol})
        </label>
        <input 
          type="number" 
          value={amount} 
          onChange={(e) => setAmount(e.target.value)}
          placeholder="0.0" 
          className="w-full px-5 py-4 bg-[#0d1117] border border-[#2a3441] rounded-2xl text-xl font-bold text-white placeholder-gray-600 focus:border-[#2dd4bf] focus:ring-2 focus:ring-[#2dd4bf]/20 outline-none transition-all" 
        />
      </div>

      {/* Price Inputs based on order type */}
      {orderType === 'limit' && (
        <div className="space-y-2">
          <label className="text-sm text-gray-400 font-medium flex items-center gap-2">
            <Target size={14} className="text-blue-400" />
            Limit Price (USD)
          </label>
          <input 
            type="number" 
            value={limitPrice} 
            onChange={(e) => setLimitPrice(e.target.value)}
            placeholder="0.00" 
            className="w-full px-5 py-4 bg-[#0d1117] border border-[#2a3441] rounded-2xl text-xl font-bold text-white placeholder-gray-600 focus:border-blue-400 focus:ring-2 focus:ring-blue-400/20 outline-none transition-all" 
          />
          <p className="text-xs text-gray-500 flex items-center gap-1">
            <Clock size={12} />
            Order executes when price reaches this level
          </p>
        </div>
      )}

      {orderType === 'stop_loss' && (
        <div className="space-y-2">
          <label className="text-sm text-gray-400 font-medium flex items-center gap-2">
            <TrendingDown size={14} className="text-red-400" />
            Stop Price (USD)
          </label>
          <input 
            type="number" 
            value={stopPrice} 
            onChange={(e) => setStopPrice(e.target.value)}
            placeholder="0.00" 
            className="w-full px-5 py-4 bg-[#0d1117] border border-[#2a3441] rounded-2xl text-xl font-bold text-white placeholder-gray-600 focus:border-red-400 focus:ring-2 focus:ring-red-400/20 outline-none transition-all" 
          />
          <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/20">
            <p className="text-xs text-red-400 flex items-center gap-2">
              <AlertTriangle size={12} />
              Sell automatically when price drops to this level
            </p>
          </div>
        </div>
      )}

      {orderType === 'take_profit' && (
        <div className="space-y-2">
          <label className="text-sm text-gray-400 font-medium flex items-center gap-2">
            <TrendingUp size={14} className="text-green-400" />
            Take Profit Price (USD)
          </label>
          <input 
            type="number" 
            value={takeProfitPrice} 
            onChange={(e) => setTakeProfitPrice(e.target.value)}
            placeholder="0.00" 
            className="w-full px-5 py-4 bg-[#0d1117] border border-[#2a3441] rounded-2xl text-xl font-bold text-white placeholder-gray-600 focus:border-green-400 focus:ring-2 focus:ring-green-400/20 outline-none transition-all" 
          />
          <div className="p-3 rounded-xl bg-green-500/10 border border-green-500/20">
            <p className="text-xs text-green-400 flex items-center gap-2">
              <Sparkles size={12} />
              Lock in profits when price rises to this level
            </p>
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/30 flex items-center gap-3 animate-slide-in-up">
          <AlertTriangle size={18} className="text-red-400" />
          <span className="text-red-400 text-sm font-medium">{error}</span>
        </div>
      )}

      {/* Create Order Button */}
      <button 
        onClick={handleCreateOrder} 
        disabled={!isConnected || !amount || loading}
        className={`w-full py-4 rounded-2xl font-bold text-lg flex items-center justify-center gap-3 transition-all disabled:opacity-50 disabled:cursor-not-allowed ${
          orderType === 'limit' 
            ? 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white hover:shadow-xl hover:shadow-blue-500/30' 
            : orderType === 'stop_loss'
            ? 'bg-gradient-to-r from-red-500 to-orange-500 text-white hover:shadow-xl hover:shadow-red-500/30'
            : 'bg-gradient-to-r from-green-500 to-emerald-500 text-white hover:shadow-xl hover:shadow-green-500/30'
        }`}
      >
        {loading ? (
          <><Loader2 size={20} className="animate-spin" /> Creating Order...</>
        ) : !isConnected ? (
          'Connect Wallet'
        ) : (
          <>
            {selectedOrderType && <selectedOrderType.icon size={20} />}
            Create {selectedOrderType?.label} Order
          </>
        )}
      </button>

      {/* Open Orders */}
      {openOrders.length > 0 && (
        <div className="mt-6 pt-6 border-t border-[#2a3441]">
          <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <Clock size={16} className="text-[#2dd4bf]" />
            Open Orders ({openOrders.length})
          </h3>
          <div className="space-y-3">
            {openOrders.map((order, index) => (
              <div 
                key={order.id} 
                style={{ animationDelay: `${index * 50}ms` }}
                className="p-4 bg-gradient-to-br from-[#0d1117] to-[#1a1f2e]/50 rounded-2xl border border-[#2a3441] flex items-center justify-between animate-slide-in-up hover:border-[#2dd4bf]/30 transition-all"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className={`text-xs px-3 py-1 rounded-lg font-semibold ${
                      order.order_type === 'limit' ? 'bg-blue-500/20 text-blue-400' :
                      order.order_type === 'stop_loss' ? 'bg-red-500/20 text-red-400' :
                      'bg-green-500/20 text-green-400'
                    }`}>
                      {order.order_type.replace('_', ' ').toUpperCase()}
                    </span>
                    <span className="text-white font-medium">{order.from_token} → {order.to_token}</span>
                  </div>
                  <div className="flex items-center gap-4 text-sm text-gray-500">
                    <span className="flex items-center gap-1">
                      <Sparkles size={12} />
                      {order.amount} {order.from_token}
                    </span>
                    <span className="flex items-center gap-1">
                      <Target size={12} />
                      ${order.limit_price || order.stop_price || order.take_profit_price}
                    </span>
                  </div>
                </div>
                <button 
                  onClick={() => handleCancelOrder(order.id)}
                  className="p-3 rounded-xl hover:bg-red-500/20 text-gray-400 hover:text-red-400 transition-all"
                >
                  <X size={18} />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* CSS Animations */}
      <style>{`
        @keyframes slide-in-up {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-slide-in-up { animation: slide-in-up 0.4s ease-out both; }
      `}</style>
    </div>
  );
};

export default OrderPanel;
