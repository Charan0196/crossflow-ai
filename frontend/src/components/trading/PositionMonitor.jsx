import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, TrendingDown, Target, DollarSign, Clock, 
  AlertTriangle, CheckCircle, Loader2, ExternalLink, X, Eye
} from 'lucide-react';

const API_BASE = 'http://localhost:8000/api';

const PositionMonitor = () => {
  const [positions, setPositions] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showDetails, setShowDetails] = useState(null);

  // Fetch positions and summary
  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      // Fetch positions and summary in parallel
      const [positionsResponse, summaryResponse] = await Promise.all([
        fetch(`${API_BASE}/position-monitor/positions`),
        fetch(`${API_BASE}/position-monitor/summary`)
      ]);

      const positionsData = await positionsResponse.json();
      const summaryData = await summaryResponse.json();

      if (positionsData.success) {
        setPositions(positionsData.positions);
      }

      if (summaryData.success) {
        setSummary(summaryData.summary);
      }
    } catch (error) {
      console.error('Error fetching position data:', error);
    } finally {
      setLoading(false);
    }
  };

  const closePosition = async (positionId) => {
    try {
      const response = await fetch(`${API_BASE}/position-monitor/close`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ position_id: positionId })
      });

      const data = await response.json();
      
      if (data.success) {
        // Refresh data
        fetchData();
      } else {
        alert('Failed to close position: ' + data.error);
      }
    } catch (error) {
      console.error('Error closing position:', error);
      alert('Error closing position');
    }
  };

  const formatPrice = (price) => {
    return price >= 1000 ? 
      `${price.toLocaleString(undefined, {maximumFractionDigits: 2})}` : 
      `${price.toFixed(4)}`;
  };

  const formatPnL = (pnl, percentage) => {
    const isPositive = pnl >= 0;
    return {
      color: isPositive ? 'text-green-400' : 'text-red-400',
      usd: `${isPositive ? '+' : ''}$${Math.abs(pnl).toFixed(2)}`,
      percent: `${isPositive ? '+' : ''}${percentage.toFixed(2)}%`
    };
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'ACTIVE': return 'text-blue-400 bg-blue-500/10';
      case 'TARGET_HIT': return 'text-green-400 bg-green-500/10';
      case 'STOP_LOSS_HIT': return 'text-red-400 bg-red-500/10';
      case 'CLOSED': return 'text-gray-400 bg-gray-500/10';
      default: return 'text-gray-400 bg-gray-500/10';
    }
  };

  if (loading) {
    return (
      <div className="p-6 rounded-2xl border border-[#2a3441] bg-[#0d1117]">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 rounded-xl bg-gradient-to-r from-blue-500/20 to-purple-500/20">
            <Eye size={20} className="text-blue-400" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-white">Position Monitor</h3>
            <p className="text-sm text-gray-400">Track your active trading positions</p>
          </div>
        </div>
        
        <div className="flex items-center justify-center py-12">
          <Loader2 size={32} className="animate-spin text-blue-400" />
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 rounded-2xl border border-[#2a3441] bg-[#0d1117]">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-gradient-to-r from-blue-500/20 to-purple-500/20">
            <Eye size={20} className="text-blue-400" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-white">Position Monitor</h3>
            <p className="text-sm text-gray-400">Track your active trading positions</p>
          </div>
        </div>
        
        <button 
          onClick={fetchData}
          className="p-2 rounded-lg bg-[#1a1f2e] border border-[#2a3441] hover:border-blue-500/30 transition-all"
          title="Refresh positions"
        >
          <Target size={16} className="text-gray-400 hover:text-blue-400" />
        </button>
      </div>

      {/* Portfolio Summary */}
      {summary && (
        <div className="mb-6 p-4 rounded-xl bg-[#1a1f2e] border border-[#2a3441]">
          <h4 className="text-lg font-semibold text-white mb-3">Portfolio Summary</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <p className="text-xs text-gray-500">Total Positions</p>
              <p className="text-lg font-bold text-white">{summary.total_positions}</p>
            </div>
            <div className="text-center">
              <p className="text-xs text-gray-500">Total Invested</p>
              <p className="text-lg font-bold text-white">${summary.total_invested.toFixed(2)}</p>
            </div>
            <div className="text-center">
              <p className="text-xs text-gray-500">Total P&L</p>
              <p className={`text-lg font-bold ${summary.total_pnl_usd >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {summary.total_pnl_usd >= 0 ? '+' : ''}${summary.total_pnl_usd.toFixed(2)}
              </p>
            </div>
            <div className="text-center">
              <p className="text-xs text-gray-500">Win Rate</p>
              <p className="text-lg font-bold text-white">
                {summary.total_positions > 0 ? 
                  `${((summary.winning_positions / summary.total_positions) * 100).toFixed(1)}%` : 
                  '0%'
                }
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Positions List */}
      {positions.length === 0 ? (
        <div className="text-center py-12">
          <Eye size={48} className="mx-auto text-gray-600 mb-4" />
          <p className="text-gray-400">No active positions</p>
          <p className="text-sm text-gray-500 mt-2">Execute some signals to start monitoring positions</p>
        </div>
      ) : (
        <div className="space-y-4">
          {positions.map((position) => {
            const pnl = formatPnL(position.pnl_usd, position.pnl_percentage);
            
            return (
              <div key={position.id} className="p-4 rounded-xl bg-[#1a1f2e] border border-[#2a3441] hover:border-blue-500/30 transition-all">
                {/* Position Header */}
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center">
                      <TrendingUp size={18} className="text-blue-400" />
                    </div>
                    <div>
                      <h4 className="font-semibold text-white">{position.token_pair.replace('USDT', '')}</h4>
                      <p className="text-xs text-gray-500">
                        {new Date(position.created_at).toLocaleDateString()} • {position.network}
                      </p>
                    </div>
                  </div>
                  
                  <div className="text-right">
                    <span className={`px-2 py-1 rounded-lg text-xs font-medium ${getStatusColor(position.status)}`}>
                      {position.status}
                    </span>
                  </div>
                </div>

                {/* P&L Display */}
                <div className="mb-3">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm text-gray-500">Profit & Loss</span>
                    <div className="text-right">
                      <span className={`text-lg font-bold ${pnl.color}`}>{pnl.usd}</span>
                      <span className={`text-sm ml-2 ${pnl.color}`}>({pnl.percent})</span>
                    </div>
                  </div>
                </div>

                {/* Price Information */}
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <p className="text-xs text-gray-500">Entry Price</p>
                    <p className="text-sm font-mono text-white">${formatPrice(position.entry_price)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Current Price</p>
                    <p className="text-sm font-mono text-white">${formatPrice(position.current_price)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Target Price</p>
                    <p className="text-sm font-mono text-green-400">${formatPrice(position.target_price)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Stop Loss</p>
                    <p className="text-sm font-mono text-red-400">${formatPrice(position.stop_loss)}</p>
                  </div>
                </div>

                {/* Position Details */}
                <div className="flex items-center justify-between text-xs text-gray-400 mb-3">
                  <span>Amount: ${position.amount_usd.toFixed(2)}</span>
                  <span>Tokens: {position.tokens_bought.toFixed(4)}</span>
                </div>

                {/* Action Buttons */}
                <div className="flex gap-2">
                  <button
                    onClick={() => setShowDetails(position)}
                    className="flex-1 py-2 px-3 rounded-lg bg-blue-500/20 text-blue-400 hover:bg-blue-500/30 transition-all text-sm font-medium"
                  >
                    View Details
                  </button>
                  
                  {position.status === 'ACTIVE' && (
                    <button
                      onClick={() => closePosition(position.id)}
                      className="flex-1 py-2 px-3 rounded-lg bg-red-500/20 text-red-400 hover:bg-red-500/30 transition-all text-sm font-medium"
                    >
                      Close Position
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Position Details Modal */}
      {showDetails && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/80 backdrop-blur-sm" onClick={() => setShowDetails(null)} />
          <div className="relative bg-[#1a1f2e] border border-[#2a3441] rounded-2xl p-6 w-full max-w-md shadow-2xl">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-semibold text-white">Position Details</h3>
              <button 
                onClick={() => setShowDetails(null)}
                className="p-1 rounded-lg hover:bg-gray-800"
              >
                <X size={20} className="text-gray-400" />
              </button>
            </div>

            <div className="space-y-4">
              <div className="p-4 rounded-lg bg-[#0d1117] border border-[#2a3441]">
                <h4 className="font-semibold text-white mb-2">{showDetails.token_pair.replace('USDT', '')}</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Signal ID:</span>
                    <span className="text-white font-mono text-xs">{showDetails.signal_id}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Wallet:</span>
                    <span className="text-white font-mono text-xs">
                      {showDetails.wallet_address.slice(0, 6)}...{showDetails.wallet_address.slice(-4)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Network:</span>
                    <span className="text-white">{showDetails.network}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Created:</span>
                    <span className="text-white">{new Date(showDetails.created_at).toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Last Update:</span>
                    <span className="text-white">{new Date(showDetails.updated_at).toLocaleString()}</span>
                  </div>
                </div>
              </div>

              <a 
                href={`https://etherscan.io/tx/${showDetails.transaction_hash}`}
                target="_blank" 
                rel="noopener noreferrer"
                className="flex items-center justify-center gap-2 w-full py-3 px-4 rounded-lg bg-blue-500/20 text-blue-400 hover:bg-blue-500/30 transition-all font-medium"
              >
                View Transaction <ExternalLink size={16} />
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PositionMonitor;