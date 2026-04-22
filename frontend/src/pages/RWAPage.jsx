import { Building, Coins, Activity, Globe, TrendingUp, ArrowUpRight, ExternalLink } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { GlassCard, MetricCard, GlowButton } from '../components/common/UI';

const RWAPage = () => {
  const rwaAssets = [
    { symbol: 'PAXG', name: 'Pax Gold', price: 2045.50, change: 0.82, apy: 0, type: 'Commodity', marketCap: '$450M', backed: 'Physical Gold' },
    { symbol: 'XAUT', name: 'Tether Gold', price: 2042.30, change: 0.75, apy: 0, type: 'Commodity', marketCap: '$520M', backed: 'Physical Gold' },
    { symbol: 'USDY', name: 'Ondo USD Yield', price: 1.05, change: 0.02, apy: 5.2, type: 'T-Bill', marketCap: '$180M', backed: 'US Treasuries' },
    { symbol: 'USDM', name: 'Mountain Protocol', price: 1.03, change: 0.01, apy: 4.8, type: 'T-Bill', marketCap: '$95M', backed: 'US Treasuries' },
    { symbol: 'EURE', name: 'Monerium EUR', price: 1.08, change: -0.15, apy: 0, type: 'Fiat', marketCap: '$45M', backed: 'EUR Reserves' }
  ];

  const goldPriceHistory = Array.from({length: 30}, (_, i) => ({
    day: i + 1,
    price: 2000 + Math.sin(i * 0.2) * 50 + i * 1.5
  }));

  const yieldComparison = [
    { name: 'USDY', apy: 5.2, color: '#10b981' },
    { name: 'USDM', apy: 4.8, color: '#06b6d4' },
    { name: 'sDAI', apy: 5.0, color: '#f59e0b' },
    { name: 'USDC', apy: 0.1, color: '#6b7280' }
  ];

  return (
    <div className="space-y-6">
      {/* Metrics */}
      <div className="grid grid-cols-4 gap-5">
        <MetricCard icon={Building} label="RWA TVL" value="$8.5M" change={12.4} color="amber" subtitle="Total locked" />
        <MetricCard icon={Coins} label="Gold Holdings" value="$2.1M" change={3.2} color="cyan" subtitle="PAXG + XAUT" />
        <MetricCard icon={Activity} label="Avg T-Bill Yield" value="5.0%" color="emerald" subtitle="Current APY" />
        <MetricCard icon={Globe} label="Supported Chains" value="5" color="purple" subtitle="Networks" />
      </div>

      {/* Featured Assets */}
      <div className="grid grid-cols-3 gap-5">
        {/* Gold Card */}
        <GlassCard glow className="relative overflow-hidden">
          <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-amber-500/20 to-yellow-500/10 rounded-full blur-2xl"></div>
          <div className="relative">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 bg-gradient-to-br from-amber-400 to-yellow-600 rounded-xl flex items-center justify-center shadow-lg shadow-amber-500/25">
                <Coins size={24} className="text-white" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white">Tokenized Gold</h3>
                <p className="text-slate-400 text-sm">Physical gold backed</p>
              </div>
            </div>
            <div className="text-3xl font-bold text-amber-400 mb-2">$2,045.50</div>
            <div className="flex items-center gap-2 text-emerald-400 text-sm mb-4">
              <ArrowUpRight size={16} /> +0.82% (24h)
            </div>
            <GlowButton variant="primary" size="md" className="w-full">Trade Gold</GlowButton>
          </div>
        </GlassCard>

        {/* T-Bill Yield Card */}
        <GlassCard className="relative overflow-hidden">
          <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-emerald-500/20 to-teal-500/10 rounded-full blur-2xl"></div>
          <div className="relative">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-xl flex items-center justify-center shadow-lg shadow-emerald-500/25">
                <Building size={24} className="text-white" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white">T-Bill Yields</h3>
                <p className="text-slate-400 text-sm">US Treasury backed</p>
              </div>
            </div>
            <div className="text-3xl font-bold text-emerald-400 mb-2">5.2% APY</div>
            <p className="text-slate-500 text-sm mb-4">Earn yield on stablecoins</p>
            <GlowButton variant="secondary" size="md" className="w-full">Earn Yield</GlowButton>
          </div>
        </GlassCard>

        {/* Yield Comparison */}
        <GlassCard>
          <h3 className="text-lg font-bold text-white mb-4">Yield Comparison</h3>
          <div className="space-y-3">
            {yieldComparison.map((item, i) => (
              <div key={i} className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg flex items-center justify-center text-xs font-bold text-white" style={{ backgroundColor: item.color }}>
                  {item.name.slice(0, 2)}
                </div>
                <div className="flex-1">
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-white font-medium">{item.name}</span>
                    <span className="text-emerald-400 font-bold">{item.apy}%</span>
                  </div>
                  <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                    <div className="h-full rounded-full" style={{ width: `${(item.apy / 6) * 100}%`, backgroundColor: item.color }}></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </GlassCard>
      </div>

      {/* Gold Price Chart */}
      <GlassCard>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-white">Gold Price (30 Days)</h3>
          <div className="flex gap-2">
            {['1W', '1M', '3M', '1Y'].map((period, i) => (
              <button key={i} className={`px-3 py-1.5 text-xs rounded-lg font-medium transition-all ${
                i === 1 ? 'bg-amber-500/20 text-amber-400' : 'text-slate-400 hover:text-white'
              }`}>
                {period}
              </button>
            ))}
          </div>
        </div>
        <ResponsiveContainer width="100%" height={280}>
          <AreaChart data={goldPriceHistory}>
            <defs>
              <linearGradient id="goldGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#f59e0b" stopOpacity={0.3}/>
                <stop offset="100%" stopColor="#f59e0b" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
            <XAxis dataKey="day" stroke="#64748b" axisLine={false} tickLine={false} />
            <YAxis stroke="#64748b" axisLine={false} tickLine={false} domain={['auto', 'auto']} tickFormatter={(v) => `$${v}`} />
            <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px' }} />
            <Area type="monotone" dataKey="price" stroke="#f59e0b" strokeWidth={2} fill="url(#goldGradient)" />
          </AreaChart>
        </ResponsiveContainer>
      </GlassCard>

      {/* All RWA Assets */}
      <GlassCard>
        <h3 className="text-lg font-bold text-white mb-4">All RWA Assets</h3>
        <div className="grid grid-cols-2 gap-4">
          {rwaAssets.map((asset, i) => (
            <div key={i} className="flex items-center justify-between p-5 bg-slate-800/30 rounded-xl border border-slate-700/30 hover:border-emerald-500/30 transition-all group">
              <div className="flex items-center gap-4">
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-sm font-bold text-white ${
                  asset.type === 'Commodity' ? 'bg-gradient-to-br from-amber-500 to-yellow-600' :
                  asset.type === 'T-Bill' ? 'bg-gradient-to-br from-emerald-500 to-teal-600' :
                  'bg-gradient-to-br from-blue-500 to-cyan-600'
                }`}>
                  {asset.symbol.slice(0, 2)}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <p className="font-bold text-white">{asset.symbol}</p>
                    <span className="px-2 py-0.5 bg-slate-700/50 text-slate-400 text-xs rounded">{asset.type}</span>
                  </div>
                  <p className="text-slate-500 text-sm">{asset.name}</p>
                  <p className="text-xs text-slate-600">Backed by: {asset.backed}</p>
                </div>
              </div>
              <div className="text-right">
                <p className="font-bold text-xl text-white">${asset.price.toLocaleString()}</p>
                <div className="flex items-center justify-end gap-2">
                  <span className={`text-sm ${asset.change >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                    {asset.change >= 0 ? '+' : ''}{asset.change}%
                  </span>
                  {asset.apy > 0 && (
                    <span className="text-cyan-400 text-sm">APY: {asset.apy}%</span>
                  )}
                </div>
                <p className="text-xs text-slate-600">MCap: {asset.marketCap}</p>
              </div>
            </div>
          ))}
        </div>
      </GlassCard>
    </div>
  );
};

export default RWAPage;
