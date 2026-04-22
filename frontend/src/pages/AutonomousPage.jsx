import { useState, useEffect } from 'react';
import { Bot, Plus, Play, Square, Trash2, AlertTriangle, TrendingUp, Droplet, ExternalLink, Zap } from 'lucide-react';

const API_BASE = 'http://localhost:8000/api';

const AutonomousPage = () => {
  const [wallets, setWallets] = useState([]);
  const [showAddWallet, setShowAddWallet] = useState(false);
  const [faucets, setFaucets] = useState({});
  const [testnets, setTestnets] = useState({});
  const [selectedNetwork, setSelectedNetwork] = useState('sepolia');
  const [balances, setBalances] = useState({});
  
  const [newWallet, setNewWallet] = useState({
    wallet_id: '',
    input_type: 'private_key', // 'private_key' or 'seed_phrase'
    private_key: '',
    seed_phrase: '',
    account_index: 0,
    max_trade_amount: 0.01,
    risk_level: 'low',
    allowed_tokens: ['ETH', 'USDC'],
    stop_loss_percent: 5.0,
    take_profit_percent: 10.0
  });

  useEffect(() => {
    fetchWallets();
    fetchFaucets();
    fetchTestnets();
    
    // Refresh balances every 10 seconds
    const interval = setInterval(() => {
      fetchBalances();
    }, 10000);
    
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (wallets.length > 0) {
      fetchBalances();
    }
  }, [wallets]);

  const fetchWallets = async () => {
    try {
      const res = await fetch(`${API_BASE}/autonomous/wallets`);
      const data = await res.json();
      setWallets(data.wallets || []);
    } catch (e) {
      console.error('Failed to fetch wallets:', e);
    }
  };

  const fetchFaucets = async () => {
    try {
      const res = await fetch(`${API_BASE}/faucet/list`);
      const data = await res.json();
      setFaucets(data.faucets || {});
    } catch (e) {
      console.error('Failed to fetch faucets:', e);
    }
  };

  const fetchTestnets = async () => {
    try {
      const res = await fetch(`${API_BASE}/faucet/networks`);
      const data = await res.json();
      setTestnets(data || {});
    } catch (e) {
      console.error('Failed to fetch testnets:', e);
    }
  };

  const fetchBalances = async () => {
    // Fetch balances for all wallets
    const newBalances = {};
    for (const wallet of wallets) {
      try {
        const response = await fetch(`https://rpc.sepolia.org`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            jsonrpc: '2.0',
            method: 'eth_getBalance',
            params: [wallet.address, 'latest'],
            id: 1
          })
        });
        const data = await response.json();
        if (data.result) {
          const balanceWei = parseInt(data.result, 16);
          const balanceEth = balanceWei / 1e18;
          newBalances[wallet.wallet_id] = balanceEth;
        }
      } catch (e) {
        console.error(`Failed to fetch balance for ${wallet.wallet_id}:`, e);
      }
    }
    setBalances(newBalances);
  };

  const addWallet = async () => {
    try {
      // Validation
      if (!newWallet.wallet_id.trim()) {
        alert('Please enter a Wallet ID');
        return;
      }

      if (newWallet.input_type === 'private_key' && !newWallet.private_key.trim()) {
        alert('Please enter a Private Key');
        return;
      }

      if (newWallet.input_type === 'seed_phrase' && !newWallet.seed_phrase.trim()) {
        alert('Please enter a Seed Phrase');
        return;
      }

      const payload = {
        wallet_id: newWallet.wallet_id,
        max_trade_amount: newWallet.max_trade_amount,
        risk_level: newWallet.risk_level,
        allowed_tokens: newWallet.allowed_tokens,
        stop_loss_percent: newWallet.stop_loss_percent,
        take_profit_percent: newWallet.take_profit_percent
      };

      // Add either private_key or seed_phrase based on input_type
      if (newWallet.input_type === 'private_key') {
        payload.private_key = newWallet.private_key;
      } else {
        payload.seed_phrase = newWallet.seed_phrase;
        payload.account_index = newWallet.account_index;
      }

      const res = await fetch(`${API_BASE}/autonomous/wallet/add`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      
      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || `HTTP ${res.status}`);
      }
      
      const data = await res.json();
      
      if (data.success) {
        alert('Wallet added successfully!');
        fetchWallets();
        setShowAddWallet(false);
        setNewWallet({
          wallet_id: '',
          input_type: 'private_key',
          private_key: '',
          seed_phrase: '',
          account_index: 0,
          max_trade_amount: 0.01,
          risk_level: 'low',
          allowed_tokens: ['ETH', 'USDC'],
          stop_loss_percent: 5.0,
          take_profit_percent: 10.0
        });
      } else {
        alert('Failed to add wallet: ' + (data.error || 'Unknown error'));
      }
    } catch (e) {
      console.error('Failed to add wallet:', e);
      alert('Failed to add wallet: ' + e.message);
    }
  };

  const startTrading = async (walletId) => {
    try {
      await fetch(`${API_BASE}/autonomous/trading/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ wallet_id: walletId })
      });
      fetchWallets();
    } catch (e) {
      console.error('Failed to start trading:', e);
    }
  };

  const stopTrading = async (walletId) => {
    try {
      await fetch(`${API_BASE}/autonomous/trading/stop`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ wallet_id: walletId })
      });
      fetchWallets();
    } catch (e) {
      console.error('Failed to stop trading:', e);
    }
  };

  const removeWallet = async (walletId) => {
    try {
      await fetch(`${API_BASE}/autonomous/wallet/remove`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ wallet_id: walletId })
      });
      fetchWallets();
    } catch (e) {
      console.error('Failed to remove wallet:', e);
    }
  };

  const executeManualTrade = async (walletId) => {
    const amount = prompt('Enter amount in ETH (e.g., 0.001):');
    if (!amount) return;
    
    const action = confirm('Buy USDC? (Cancel for Sell)') ? 'buy' : 'sell';
    
    try {
      const res = await fetch(`${API_BASE}/autonomous/trade/manual`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          wallet_id: walletId,
          action: action,
          token: 'USDC',
          amount: parseFloat(amount)
        })
      });
      const data = await res.json();
      if (data.success) {
        alert('Trade executed! Check wallet trades.');
        fetchWallets();
      } else {
        alert('Trade failed: ' + (data.error || 'Unknown error'));
      }
    } catch (e) {
      console.error('Failed to execute trade:', e);
      alert('Trade failed: ' + e.message);
    }
  };

  const autoFundWallet = async (walletId) => {
    try {
      const res = await fetch(`${API_BASE}/autonomous/wallet/${walletId}/auto-fund`, {
        method: 'POST'
      });
      const data = await res.json();
      
      if (data.success && data.drip_needed === false) {
        alert(`Balance sufficient: ${data.balance} ETH`);
      } else if (data.success) {
        alert('Tokens requested! Wait 1-5 minutes.');
      } else {
        // Show manual faucet instructions
        const faucets = data.manual_faucets || [];
        let msg = data.message + '\n\nManual Faucets:\n';
        faucets.forEach(f => {
          msg += `\n${f.name}: ${f.url}\nAmount: ${f.amount}, Cooldown: ${f.cooldown}\n`;
        });
        alert(msg);
      }
      fetchWallets();
    } catch (e) {
      console.error('Failed to auto-fund:', e);
      alert('Auto-fund failed: ' + e.message);
    }
  };

  const fundAndTrade = async (walletId) => {
    if (!confirm('This will request faucet tokens and start trading. Continue?')) return;
    
    try {
      const res = await fetch(`${API_BASE}/autonomous/wallet/${walletId}/fund-and-trade`, {
        method: 'POST'
      });
      const data = await res.json();
      
      if (data.success) {
        alert('Wallet funded and trading started!');
      } else {
        const faucets = data.manual_faucets || [];
        let msg = data.message + '\n\nPlease use manual faucets:\n';
        faucets.forEach(f => {
          msg += `\n${f.name}: ${f.url}\n`;
        });
        alert(msg);
      }
      fetchWallets();
    } catch (e) {
      console.error('Failed to fund and trade:', e);
      alert('Failed: ' + e.message);
    }
  };

  return (
    <div className="space-y-6">
      {/* Warning Banner */}
      <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4">
        <div className="flex items-start gap-3">
          <AlertTriangle className="text-amber-400 flex-shrink-0 mt-0.5" size={20} />
          <div>
            <h3 className="text-amber-400 font-semibold mb-1">Testnet Only Warning</h3>
            <p className="text-gray-400 text-sm">
              This autonomous trading feature is for TESTNET ONLY. Never use mainnet private keys. 
              Always test with testnet tokens first.
            </p>
          </div>
        </div>
      </div>

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white mb-2">Autonomous Trading</h1>
          <p className="text-gray-400">AI-powered automated trading on testnets</p>
        </div>
        <button
          onClick={() => setShowAddWallet(true)}
          className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-cyan-500 to-purple-500 text-white rounded-lg hover:shadow-lg transition-all"
        >
          <Plus size={18} />
          Add Wallet
        </button>
      </div>

      {/* Wallets Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {wallets.map((wallet) => (
          <div key={wallet.wallet_id} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Bot className="text-cyan-400" size={20} />
                <h3 className="text-white font-semibold">{wallet.wallet_id}</h3>
              </div>
              <span className={`px-2 py-1 rounded-lg text-xs ${wallet.active ? 'bg-emerald-500/20 text-emerald-400' : 'bg-gray-700 text-gray-400'}`}>
                {wallet.active ? 'Active' : 'Inactive'}
              </span>
            </div>
            
            <div className="space-y-2 mb-4">
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Address:</span>
                <span className="text-gray-300 font-mono text-xs">{wallet.address.slice(0, 10)}...{wallet.address.slice(-8)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Balance:</span>
                <span className="text-emerald-400 font-semibold">
                  {balances[wallet.wallet_id] !== undefined 
                    ? `${balances[wallet.wallet_id].toFixed(4)} ETH` 
                    : 'Loading...'}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Total Trades:</span>
                <span className="text-white">{wallet.total_trades}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Risk Level:</span>
                <span className="text-white capitalize">{wallet.config.risk_level}</span>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="grid grid-cols-2 gap-2 mb-3">
              <button
                onClick={() => autoFundWallet(wallet.wallet_id)}
                className="flex items-center justify-center gap-2 px-3 py-2 bg-blue-500/20 text-blue-400 rounded-lg hover:bg-blue-500/30 transition-all text-sm"
                title="Request faucet tokens"
              >
                <Droplet size={14} />
                Fund
              </button>
              <button
                onClick={() => fundAndTrade(wallet.wallet_id)}
                className="flex items-center justify-center gap-2 px-3 py-2 bg-purple-500/20 text-purple-400 rounded-lg hover:bg-purple-500/30 transition-all text-sm"
                title="Auto-fund and start trading"
              >
                <Zap size={14} />
                Fund & Trade
              </button>
            </div>

            <div className="flex gap-2">
              {!wallet.active ? (
                <button
                  onClick={() => startTrading(wallet.wallet_id)}
                  className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-emerald-500/20 text-emerald-400 rounded-lg hover:bg-emerald-500/30 transition-all"
                >
                  <Play size={16} />
                  Start
                </button>
              ) : (
                <button
                  onClick={() => stopTrading(wallet.wallet_id)}
                  className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition-all"
                >
                  <Square size={16} />
                  Stop
                </button>
              )}
              <button
                onClick={() => executeManualTrade(wallet.wallet_id)}
                className="px-3 py-2 bg-cyan-500/20 text-cyan-400 rounded-lg hover:bg-cyan-500/30 transition-all"
                title="Execute test trade"
              >
                <TrendingUp size={16} />
              </button>
              <button
                onClick={() => removeWallet(wallet.wallet_id)}
                className="px-3 py-2 bg-gray-800 text-gray-400 rounded-lg hover:bg-gray-700 transition-all"
              >
                <Trash2 size={16} />
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Testnet Faucets Section */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <div className="flex items-center gap-2 mb-4">
          <Droplet className="text-blue-400" size={20} />
          <h2 className="text-xl font-bold text-white">Testnet Faucets</h2>
        </div>

        <div className="mb-4">
          <select
            value={selectedNetwork}
            onChange={(e) => setSelectedNetwork(e.target.value)}
            className="bg-gray-800 border border-gray-700 text-white rounded-lg px-4 py-2"
          >
            {Object.keys(testnets).map((network) => (
              <option key={network} value={network}>
                {testnets[network].name}
              </option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {faucets[selectedNetwork]?.map((faucet, i) => (
            <div key={i} className="bg-gray-800 border border-gray-700 rounded-lg p-4">
              <h3 className="text-white font-semibold mb-2">{faucet.name}</h3>
              <p className="text-gray-400 text-sm mb-3">
                Tokens: {faucet.tokens.join(', ')}
              </p>
              <a
                href={faucet.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 text-cyan-400 hover:text-cyan-300 text-sm"
              >
                Visit Faucet <ExternalLink size={14} />
              </a>
            </div>
          ))}
        </div>
      </div>

      {/* Add Wallet Modal */}
      {showAddWallet && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 max-w-md w-full mx-4">
            <h2 className="text-xl font-bold text-white mb-4">Add Wallet for Autonomous Trading</h2>
            
            <div className="space-y-4">
              <div>
                <label className="text-sm text-gray-400 mb-1 block">Wallet ID</label>
                <input
                  type="text"
                  value={newWallet.wallet_id}
                  onChange={(e) => setNewWallet({...newWallet, wallet_id: e.target.value})}
                  className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-4 py-2"
                  placeholder="my-testnet-wallet"
                />
              </div>

              <div>
                <label className="text-sm text-gray-400 mb-2 block">Input Type</label>
                <div className="flex gap-2">
                  <button
                    onClick={() => setNewWallet({...newWallet, input_type: 'private_key'})}
                    className={`flex-1 px-4 py-2 rounded-lg text-sm transition-all ${
                      newWallet.input_type === 'private_key'
                        ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30'
                        : 'bg-gray-800 text-gray-400 border border-gray-700'
                    }`}
                  >
                    Private Key
                  </button>
                  <button
                    onClick={() => setNewWallet({...newWallet, input_type: 'seed_phrase'})}
                    className={`flex-1 px-4 py-2 rounded-lg text-sm transition-all ${
                      newWallet.input_type === 'seed_phrase'
                        ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30'
                        : 'bg-gray-800 text-gray-400 border border-gray-700'
                    }`}
                  >
                    Seed Phrase
                  </button>
                </div>
              </div>

              {newWallet.input_type === 'private_key' ? (
                <div>
                  <label className="text-sm text-gray-400 mb-1 block">Private Key (Testnet Only!)</label>
                  <input
                    type="password"
                    value={newWallet.private_key}
                    onChange={(e) => setNewWallet({...newWallet, private_key: e.target.value})}
                    className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-4 py-2"
                    placeholder="0x..."
                  />
                </div>
              ) : (
                <>
                  <div>
                    <label className="text-sm text-gray-400 mb-1 block">Seed Phrase (Testnet Only!)</label>
                    <textarea
                      value={newWallet.seed_phrase}
                      onChange={(e) => setNewWallet({...newWallet, seed_phrase: e.target.value})}
                      className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-4 py-2 h-24"
                      placeholder="word1 word2 word3 ... (12 or 24 words)"
                    />
                    <p className="text-xs text-gray-500 mt-1">Enter your 12 or 24 word recovery phrase</p>
                  </div>
                  <div>
                    <label className="text-sm text-gray-400 mb-1 block">Account Index</label>
                    <input
                      type="number"
                      min="0"
                      value={newWallet.account_index}
                      onChange={(e) => setNewWallet({...newWallet, account_index: parseInt(e.target.value)})}
                      className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-4 py-2"
                    />
                    <p className="text-xs text-gray-500 mt-1">Derivation path: m/44'/60'/0'/0/{newWallet.account_index}</p>
                  </div>
                </>
              )}

              <div>
                <label className="text-sm text-gray-400 mb-1 block">Max Trade Amount</label>
                <input
                  type="number"
                  step="0.001"
                  value={newWallet.max_trade_amount}
                  onChange={(e) => setNewWallet({...newWallet, max_trade_amount: parseFloat(e.target.value)})}
                  className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-4 py-2"
                />
              </div>

              <div>
                <label className="text-sm text-gray-400 mb-1 block">Risk Level</label>
                <select
                  value={newWallet.risk_level}
                  onChange={(e) => setNewWallet({...newWallet, risk_level: e.target.value})}
                  className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-4 py-2"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowAddWallet(false)}
                className="flex-1 px-4 py-2 bg-gray-800 text-gray-400 rounded-lg hover:bg-gray-700 transition-all"
              >
                Cancel
              </button>
              <button
                onClick={addWallet}
                className="flex-1 px-4 py-2 bg-gradient-to-r from-cyan-500 to-purple-500 text-white rounded-lg hover:shadow-lg transition-all"
              >
                Add Wallet
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AutonomousPage;
