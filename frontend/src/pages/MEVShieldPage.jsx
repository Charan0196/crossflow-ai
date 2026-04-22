import { Shield, Coins, Zap, Clock, Lock, AlertTriangle, CheckCircle } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { GlassCard, MetricCard, StatusBadge, GlowButton } from '../components/common/UI';

const MEVShieldPage = () => {
  const protectionStats = [
    { type: 'Sandwich Attack', blocked: 156, saved: '$12,450', icon: '🥪' },
    { type: 'Front-running', blocked: 89, saved: '$8,230', icon: '🏃' },
    { type: 'Back-running', blocked: 45, saved: '$5,120', icon: '🔙' },
    { type: 'JIT Liquidity', blocked: 23, saved: '$3,200', icon: '💧' }
  ];

  const timelineData = Array.from({length: 24}, (_, i) => ({
    hour: `${i}:00`,
    blocked: Math.floor(Math.random() * 15) + 2,
    saved: Math.floor(Math.random() * 500) + 100
  }));

  const recentBlocks = [
    { hash: '0x1a2b...3c4d', type: 'Sandwich', saved: '$245', time: '2m ago', tx: 'ETH → USDC' },
    { hash: '0x5e6f...7g8h', type: 'Front-run', saved: '$180', time: '8m ago', tx: 'BTC → ETH' },
    { hash: '0x9i0j...1k2l', type: 'Sandwich', saved: '$320', time: '15m ago', tx: 'SOL → USDC' }
  ];

  return (
    <div className="space-y-6">
      {/* Metrics */}
      <div className="grid grid-cols-4 gap-5">
        <MetricCard icon={Shield} label="Protected Trades" value="1,247" change={15.2} color="emerald" subtitle="This month" />
        <MetricCard icon={Coins} label="MEV Saved" value="$45.2K" change={22.1} color="cyan" subtitle="Total savings" />
        <MetricCard icon={Zap} label="Protection Rate" value="99.2%" color="purple" subtitle="Success rate" />
        <MetricCard icon={Clock} label="Avg Latency" value="12ms" color="amber" subtitle="Response time" />
      </div>

      <div className="grid grid-cols-3 gap-5">
        {/* Protection Status */}
        <div className="col-span-2">
          <GlassCard glow>
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-gradient-to-br from-emerald-500 to-green-600 rounded-xl flex items-center justify-center shadow-lg shadow-emerald-500/25">
                  <Shield size={24} className="text-white" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white">MEV Protection Status</h3>
                  <p className="text-slate-400 text-sm">Real-time protection active</p>
                </div>
              </div>
              <StatusBadge status="active" label="Active" />
            </div>

            <div className="grid grid-cols-2 gap-4">
              {protectionStats.map((stat, i) => (
                <div key={i} className="p-4 bg-slate-800/30 rounded-xl border border-slate-700/30 hover:border-emerald-500/30 transition-colors">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <span className="text-2xl">{stat.icon}</span>
                      <span className="font-medium text-white">{stat.type}</span>
                    </div>
                    <span className="text-emerald-400 font-bold">{stat.saved}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-500">{stat.blocked} blocked</span>
                    <div className="flex items-center gap-1 text-emerald-400">
                      <CheckCircle size={14} />
                      <span>Protected</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </GlassCard>
        </div>

        {/* Settings */}
        <GlassCard>
          <h3 className="text-lg font-bold text-white mb-4">Protection Settings</h3>
          <div className="space-y-4">
            {[
              { label: 'Sandwich Protection', enabled: true },
              { label: 'Front-run Protection', enabled: true },
              { label: 'Private Mempool', enabled: true },
              { label: 'Flashbots Integration', enabled: false }
            ].map((setting, i) => (
              <div key={i} className="flex items-center justify-between p-3 bg-slate-800/30 rounded-xl">
                <span className="text-slate-300 text-sm">{setting.label}</span>
                <button className={`w-10 h-5 rounded-full transition-colors ${setting.enabled ? 'bg-emerald-500' : 'bg-slate-600'}`}>
                  <div className={`w-4 h-4 bg-white rounded-full transition-transform shadow ${setting.enabled ? 'translate-x-5' : 'translate-x-0.5'}`}></div>
                </button>
              </div>
            ))}
          </div>
          <div className="mt-4 p-3 bg-amber-500/10 border border-amber-500/30 rounded-xl">
            <div className="flex items-center gap-2 text-amber-400 text-sm">
              <AlertTriangle size={16} />
              <span>Flashbots requires setup</span>
            </div>
          </div>
        </GlassCard>
      </div>

      <div className="grid grid-cols-2 gap-5">
        {/* Timeline Chart */}
        <GlassCard>
          <h3 className="text-lg font-bold text-white mb-4">Protection Timeline (24h)</h3>
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={timelineData}>
              <defs>
                <linearGradient id="blockedGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#10b981" stopOpacity={0.4}/>
                  <stop offset="100%" stopColor="#10b981" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
              <XAxis dataKey="hour" stroke="#64748b" axisLine={false} tickLine={false} />
              <YAxis stroke="#64748b" axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px' }} />
              <Area type="monotone" dataKey="blocked" stroke="#10b981" strokeWidth={2} fill="url(#blockedGradient)" name="Attacks Blocked" />
            </AreaChart>
          </ResponsiveContainer>
        </GlassCard>

        {/* Recent Blocks */}
        <GlassCard>
          <h3 className="text-lg font-bold text-white mb-4">Recent Blocked Attacks</h3>
          <div className="space-y-3">
            {recentBlocks.map((block, i) => (
              <div key={i} className="flex items-center justify-between p-4 bg-slate-800/30 rounded-xl border border-slate-700/30">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-emerald-500/20 rounded-xl flex items-center justify-center">
                    <Lock size={18} className="text-emerald-400" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm text-slate-400">{block.hash}</span>
                      <span className="px-2 py-0.5 bg-red-500/20 text-red-400 text-xs rounded font-medium">{block.type}</span>
                    </div>
                    <p className="text-xs text-slate-500">{block.tx}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-emerald-400 font-semibold">{block.saved}</p>
                  <p className="text-xs text-slate-500">{block.time}</p>
                </div>
              </div>
            ))}
          </div>
          <GlowButton variant="ghost" size="sm" className="w-full mt-4">
            View All History
          </GlowButton>
        </GlassCard>
      </div>
    </div>
  );
};

export default MEVShieldPage;
