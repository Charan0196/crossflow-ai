import { useState } from 'react';
import { Zap, Coins, Activity, Clock, Fuel, Key, CheckCircle } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { GlassCard, MetricCard, StatusBadge, GlowButton } from '../components/common/UI';

const GasPage = () => {
  const [sessionKeysEnabled, setSessionKeysEnabled] = useState(true);
  const [selectedToken, setSelectedToken] = useState('ETH');

  const gasTokens = [
    { token: 'ETH', rate: '1x', balance: '2.5', recommended: true },
    { token: 'USDC', rate: '1.02x', balance: '1,500', recommended: false },
    { token: 'USDT', rate: '1.02x', balance: '800', recommended: false },
    { token: 'DAI', rate: '1.03x', balance: '500', recommended: false }
  ];

  const gasHistory = Array.from({length: 24}, (_, i) => ({
    hour: `${i}:00`,
    gas: 20 + Math.random() * 30,
    optimized: 15 + Math.random() * 20
  }));

  const recentTx = [
    { type: 'Swap', gas: '$2.50', saved: '$1.20', token: 'ETH', time: '5m ago' },
    { type: 'Bridge', gas: '$4.80', saved: '$2.40', token: 'USDC', time: '15m ago' },
    { type: 'Approve', gas: '$0.80', saved: '$0.40', token: 'ETH', time: '1h ago' }
  ];

  return (
    <div className="space-y-6">
      {/* Metrics */}
      <div className="grid grid-cols-4 gap-5">
        <MetricCard icon={Zap} label="Gas Saved" value="$12.5K" change={25.4} color="amber" subtitle="This month" />
        <MetricCard icon={Coins} label="Sponsored Txs" value="2,450" color="cyan" subtitle="Total count" />
        <MetricCard icon={Activity} label="Avg Gas Price" value="25 gwei" color="purple" subtitle="Current" />
        <MetricCard icon={Clock} label="Optimization" value="35%" color="emerald" subtitle="Avg savings" />
      </div>

      <div className="grid grid-cols-3 gap-5">
        {/* Pay Gas With Any Token */}
        <GlassCard glow>
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 bg-gradient-to-br from-amber-500 to-orange-600 rounded-xl flex items-center justify-center shadow-lg shadow-amber-500/25">
              <Fuel size={20} className="text-white" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white">Pay Gas With Any Token</h3>
              <p className="text-slate-400 text-sm">Select your preferred gas token</p>
            </div>
          </div>

          <div className="space-y-3">
            {gasTokens.map((t, i) => (
              <button
                key={i}
                onClick={() => setSelectedToken(t.token)}
                className={`w-full flex items-center justify-between p-4 rounded-xl transition-all ${
                  selectedToken === t.token
                    ? 'bg-emerald-500/10 border-2 border-emerald-500/50'
                    : 'bg-slate-800/30 border border-slate-700/30 hover:border-slate-600/50'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold ${
                    t.token === 'ETH' ? 'bg-gradient-to-br from-blue-500 to-purple-600' :
                    t.token === 'USDC' ? 'bg-gradient-to-br from-cyan-500 to-blue-600' :
                    t.token === 'USDT' ? 'bg-gradient-to-br from-emerald-500 to-green-600' :
                    'bg-gradient-to-br from-amber-500 to-orange-600'
                  } text-white`}>
                    {t.token.slice(0, 2)}
                  </div>
                  <div className="text-left">
                    <p className="font-semibold text-white">{t.token}</p>
                    <p className="text-xs text-slate-500">Balance: {t.balance}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-slate-400 text-sm">{t.rate}</span>
                  {t.recommended && <StatusBadge status="active" label="Best" />}
                  {selectedToken === t.token && <CheckCircle size={18} className="text-emerald-400" />}
                </div>
              </button>
            ))}
          </div>
        </GlassCard>

        {/* Session Keys */}
        <GlassCard>
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-600 rounded-xl flex items-center justify-center shadow-lg shadow-purple-500/25">
              <Key size={20} className="text-white" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white">Session Keys</h3>
              <p className="text-slate-400 text-sm">Enable gasless transactions</p>
            </div>
          </div>

          <div className="p-4 bg-slate-800/30 rounded-xl border border-slate-700/30 mb-4">
            <div className="flex items-center justify-between mb-4">
              <div>
                <p className="font-semibold text-white">Auto-Sign Transactions</p>
                <p className="text-xs text-slate-500">No wallet popups for approved actions</p>
              </div>
              <button
                onClick={() => setSessionKeysEnabled(!sessionKeysEnabled)}
                className={`w-12 h-6 rounded-full transition-colors ${sessionKeysEnabled ? 'bg-emerald-500' : 'bg-slate-600'}`}
              >
                <div className={`w-5 h-5 bg-white rounded-full transition-transform shadow ${sessionKeysEnabled ? 'translate-x-6' : 'translate-x-0.5'}`}></div>
              </button>
            </div>
            {sessionKeysEnabled && (
              <div className="space-y-2 pt-4 border-t border-slate-700/50">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-400">Session Duration</span>
                  <span className="text-white">24 hours</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-400">Max Tx Value</span>
                  <span className="text-white">$10,000</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-400">Allowed Actions</span>
                  <span className="text-emerald-400">Swap, Bridge</span>
                </div>
              </div>
            )}
          </div>

          <div className="space-y-2">
            <GlowButton variant="secondary" size="sm" className="w-full">Configure Limits</GlowButton>
            <GlowButton variant="ghost" size="sm" className="w-full">Revoke Session</GlowButton>
          </div>
        </GlassCard>

        {/* Recent Transactions */}
        <GlassCard>
          <h3 className="text-lg font-bold text-white mb-4">Recent Gas Savings</h3>
          <div className="space-y-3">
            {recentTx.map((tx, i) => (
              <div key={i} className="flex items-center justify-between p-3 bg-slate-800/30 rounded-xl">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-amber-500/20 rounded-lg flex items-center justify-center">
                    <Zap size={16} className="text-amber-400" />
                  </div>
                  <div>
                    <p className="font-medium text-white text-sm">{tx.type}</p>
                    <p className="text-xs text-slate-500">Paid with {tx.token}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm text-white">{tx.gas}</p>
                  <p className="text-xs text-emerald-400">Saved {tx.saved}</p>
                </div>
              </div>
            ))}
          </div>
        </GlassCard>
      </div>

      {/* Gas Price Chart */}
      <GlassCard>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-white">Gas Price History (24h)</h3>
          <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-amber-500 rounded-full"></div>
              <span className="text-slate-400">Market Gas</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-emerald-500 rounded-full"></div>
              <span className="text-slate-400">Optimized</span>
            </div>
          </div>
        </div>
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={gasHistory}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
            <XAxis dataKey="hour" stroke="#64748b" axisLine={false} tickLine={false} />
            <YAxis stroke="#64748b" axisLine={false} tickLine={false} unit=" gwei" />
            <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px' }} />
            <Line type="monotone" dataKey="gas" stroke="#f59e0b" strokeWidth={2} dot={false} name="Market" />
            <Line type="monotone" dataKey="optimized" stroke="#10b981" strokeWidth={2} dot={false} name="Optimized" />
          </LineChart>
        </ResponsiveContainer>
      </GlassCard>
    </div>
  );
};

export default GasPage;
