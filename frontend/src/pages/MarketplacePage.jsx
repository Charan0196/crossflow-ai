import { Briefcase, Users, Coins, Award, Star, TrendingUp, Shield, Copy } from 'lucide-react';
import { GlassCard, MetricCard, StatusBadge, GlowButton } from '../components/common/UI';

const MarketplacePage = () => {
  const strategies = [
    { 
      rank: 1, name: 'Alpha Hunter Pro', creator: '0x1a2b...3c4d', 
      roi: 45.2, sharpe: 2.1, followers: 1250, tvl: '$2.5M', fee: 15, 
      risk: 'Medium', tags: ['DeFi', 'Arbitrage'], verified: true 
    },
    { 
      rank: 2, name: 'DeFi Yield Master', creator: '0x5e6f...7g8h', 
      roi: 32.5, sharpe: 1.8, followers: 890, tvl: '$1.8M', fee: 10, 
      risk: 'Low', tags: ['Yield', 'Staking'], verified: true 
    },
    { 
      rank: 3, name: 'Cross-Chain Arb', creator: '0x9i0j...1k2l', 
      roi: 28.7, sharpe: 1.5, followers: 650, tvl: '$1.2M', fee: 12, 
      risk: 'High', tags: ['Cross-chain', 'MEV'], verified: false 
    },
    { 
      rank: 4, name: 'Momentum Trader', creator: '0xabcd...efgh', 
      roi: 24.3, sharpe: 1.3, followers: 420, tvl: '$850K', fee: 8, 
      risk: 'Medium', tags: ['Technical', 'Swing'], verified: true 
    }
  ];

  const featuredStrategy = strategies[0];

  return (
    <div className="space-y-6">
      {/* Metrics */}
      <div className="grid grid-cols-4 gap-5">
        <MetricCard icon={Briefcase} label="Total Strategies" value="156" color="purple" subtitle="Active strategies" />
        <MetricCard icon={Users} label="Total Followers" value="12.5K" change={8.2} color="cyan" subtitle="Unique users" />
        <MetricCard icon={Coins} label="Total TVL" value="$45.2M" change={15.3} color="emerald" subtitle="Locked value" />
        <MetricCard icon={Award} label="Avg ROI" value="32.5%" color="amber" subtitle="30-day average" />
      </div>

      {/* Featured Strategy */}
      <GlassCard glow className="relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-purple-500/20 to-pink-500/10 rounded-full blur-3xl"></div>
        <div className="relative">
          <div className="flex items-start justify-between mb-6">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-pink-600 rounded-2xl flex items-center justify-center shadow-lg shadow-purple-500/25">
                <Briefcase size={28} className="text-white" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-xl font-bold text-white">{featuredStrategy.name}</h3>
                  {featuredStrategy.verified && (
                    <span className="px-2 py-0.5 bg-emerald-500/20 text-emerald-400 text-xs rounded-full font-medium flex items-center gap-1">
                      <Shield size={10} /> Verified
                    </span>
                  )}
                </div>
                <p className="text-slate-400 text-sm">by {featuredStrategy.creator}</p>
                <div className="flex gap-2 mt-2">
                  {featuredStrategy.tags.map((tag, i) => (
                    <span key={i} className="px-2 py-0.5 bg-slate-700/50 text-slate-300 text-xs rounded">{tag}</span>
                  ))}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className="px-3 py-1 bg-amber-500/20 text-amber-400 rounded-full text-sm font-bold flex items-center gap-1">
                <Star size={14} className="fill-amber-400" /> Featured
              </span>
            </div>
          </div>

          <div className="grid grid-cols-5 gap-4 mb-6">
            <div className="p-4 bg-slate-800/30 rounded-xl text-center">
              <p className="text-2xl font-bold text-emerald-400">+{featuredStrategy.roi}%</p>
              <p className="text-xs text-slate-500">30d ROI</p>
            </div>
            <div className="p-4 bg-slate-800/30 rounded-xl text-center">
              <p className="text-2xl font-bold text-cyan-400">{featuredStrategy.sharpe}</p>
              <p className="text-xs text-slate-500">Sharpe Ratio</p>
            </div>
            <div className="p-4 bg-slate-800/30 rounded-xl text-center">
              <p className="text-2xl font-bold text-white">{featuredStrategy.tvl}</p>
              <p className="text-xs text-slate-500">TVL</p>
            </div>
            <div className="p-4 bg-slate-800/30 rounded-xl text-center">
              <p className="text-2xl font-bold text-purple-400">{featuredStrategy.followers.toLocaleString()}</p>
              <p className="text-xs text-slate-500">Followers</p>
            </div>
            <div className="p-4 bg-slate-800/30 rounded-xl text-center">
              <p className="text-2xl font-bold text-amber-400">{featuredStrategy.fee}%</p>
              <p className="text-xs text-slate-500">Fee</p>
            </div>
          </div>

          <div className="flex gap-3">
            <GlowButton variant="primary" size="lg" icon={TrendingUp}>Follow Strategy</GlowButton>
            <GlowButton variant="secondary" size="lg" icon={Copy}>Copy Trade</GlowButton>
          </div>
        </div>
      </GlassCard>

      {/* Strategy Leaderboard */}
      <GlassCard>
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-bold text-white">Strategy Leaderboard</h3>
          <div className="flex gap-2">
            {['Trending', 'Top ROI', 'Most Followed', 'New'].map((filter, i) => (
              <button key={i} className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                i === 0 ? 'bg-purple-500/20 text-purple-400' : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
              }`}>
                {filter}
              </button>
            ))}
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-left text-slate-400 text-sm border-b border-slate-700/50">
                <th className="pb-4 font-medium">Rank</th>
                <th className="pb-4 font-medium">Strategy</th>
                <th className="pb-4 font-medium">ROI (30d)</th>
                <th className="pb-4 font-medium">Sharpe</th>
                <th className="pb-4 font-medium">TVL</th>
                <th className="pb-4 font-medium">Followers</th>
                <th className="pb-4 font-medium">Risk</th>
                <th className="pb-4 font-medium">Fee</th>
                <th className="pb-4 font-medium">Action</th>
              </tr>
            </thead>
            <tbody>
              {strategies.map((s) => (
                <tr key={s.rank} className="border-b border-slate-800/50 hover:bg-slate-800/20 transition-colors">
                  <td className="py-4">
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold text-sm ${
                      s.rank === 1 ? 'bg-gradient-to-br from-amber-400 to-amber-600 text-black' :
                      s.rank === 2 ? 'bg-gradient-to-br from-slate-300 to-slate-500 text-black' :
                      s.rank === 3 ? 'bg-gradient-to-br from-amber-600 to-amber-800 text-white' :
                      'bg-slate-700 text-slate-300'
                    }`}>
                      #{s.rank}
                    </div>
                  </td>
                  <td className="py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-600 rounded-xl flex items-center justify-center">
                        <Briefcase size={18} className="text-white" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-white">{s.name}</span>
                          {s.verified && <Shield size={12} className="text-emerald-400" />}
                        </div>
                        <span className="text-xs text-slate-500">{s.creator}</span>
                      </div>
                    </div>
                  </td>
                  <td className="py-4 text-emerald-400 font-bold">+{s.roi}%</td>
                  <td className="py-4 text-cyan-400">{s.sharpe}</td>
                  <td className="py-4 text-white">{s.tvl}</td>
                  <td className="py-4 text-slate-400">{s.followers.toLocaleString()}</td>
                  <td className="py-4">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      s.risk === 'Low' ? 'bg-emerald-500/20 text-emerald-400' :
                      s.risk === 'Medium' ? 'bg-amber-500/20 text-amber-400' :
                      'bg-red-500/20 text-red-400'
                    }`}>
                      {s.risk}
                    </span>
                  </td>
                  <td className="py-4 text-purple-400">{s.fee}%</td>
                  <td className="py-4">
                    <GlowButton variant="outline" size="sm">Follow</GlowButton>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </GlassCard>
    </div>
  );
};

export default MarketplacePage;
