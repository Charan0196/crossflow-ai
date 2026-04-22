import { Users, Activity, Award, Clock, Star, TrendingUp, Zap } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { GlassCard, MetricCard, StatusBadge, GlowButton } from '../components/common/UI';

const SolversPage = () => {
  const solvers = [
    { rank: 1, name: 'Alpha Solver', score: 98, volume: '$2.5M', latency: '12ms', trades: 1250, status: 'active', specialty: 'DEX Aggregation' },
    { rank: 2, name: 'Beta Network', score: 95, volume: '$1.8M', latency: '18ms', trades: 980, status: 'active', specialty: 'Cross-chain' },
    { rank: 3, name: 'Gamma Pool', score: 92, volume: '$1.2M', latency: '25ms', trades: 750, status: 'active', specialty: 'Limit Orders' },
    { rank: 4, name: 'Delta Hub', score: 89, volume: '$980K', latency: '32ms', trades: 620, status: 'warning', specialty: 'RFQ' },
    { rank: 5, name: 'Epsilon Node', score: 85, volume: '$750K', latency: '45ms', trades: 480, status: 'active', specialty: 'MEV Protection' }
  ];

  const volumeData = solvers.map(s => ({
    name: s.name.split(' ')[0],
    volume: parseFloat(s.volume.replace(/[$MK]/g, '')) * (s.volume.includes('M') ? 1000 : 1)
  }));

  const networkStats = [
    { label: 'Total Liquidity', value: '$125M' },
    { label: 'Avg Fill Rate', value: '99.2%' },
    { label: 'Network Uptime', value: '99.99%' },
    { label: 'Active Chains', value: '6' }
  ];

  return (
    <div className="space-y-6">
      {/* Metrics */}
      <div className="grid grid-cols-4 gap-5">
        <MetricCard icon={Users} label="Active Solvers" value="12" color="cyan" subtitle="Online now" />
        <MetricCard icon={Activity} label="Total Volume" value="$5.5M" change={18.3} color="emerald" subtitle="24h volume" />
        <MetricCard icon={Award} label="Avg Score" value="95.2" color="purple" subtitle="Network average" />
        <MetricCard icon={Clock} label="Avg Latency" value="18ms" color="amber" subtitle="Response time" />
      </div>

      {/* Leaderboard */}
      <GlassCard>
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-bold text-white">Solver Leaderboard</h3>
          <div className="flex gap-2">
            <GlowButton variant="ghost" size="sm">By Score</GlowButton>
            <GlowButton variant="ghost" size="sm">By Volume</GlowButton>
            <GlowButton variant="ghost" size="sm">By Latency</GlowButton>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-left text-slate-400 text-sm border-b border-slate-700/50">
                <th className="pb-4 font-medium">Rank</th>
                <th className="pb-4 font-medium">Solver</th>
                <th className="pb-4 font-medium">Score</th>
                <th className="pb-4 font-medium">Volume (24h)</th>
                <th className="pb-4 font-medium">Latency</th>
                <th className="pb-4 font-medium">Trades</th>
                <th className="pb-4 font-medium">Specialty</th>
                <th className="pb-4 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {solvers.map((solver) => (
                <tr key={solver.rank} className="border-b border-slate-800/50 hover:bg-slate-800/20 transition-colors">
                  <td className="py-4">
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold text-sm ${
                      solver.rank === 1 ? 'bg-gradient-to-br from-amber-400 to-amber-600 text-black' :
                      solver.rank === 2 ? 'bg-gradient-to-br from-slate-300 to-slate-500 text-black' :
                      solver.rank === 3 ? 'bg-gradient-to-br from-amber-600 to-amber-800 text-white' :
                      'bg-slate-700 text-slate-300'
                    }`}>
                      #{solver.rank}
                    </div>
                  </td>
                  <td className="py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-xl flex items-center justify-center text-sm font-bold">
                        {solver.name.slice(0, 2)}
                      </div>
                      <div>
                        <p className="font-semibold text-white">{solver.name}</p>
                        <div className="flex items-center gap-1">
                          {[...Array(5)].map((_, i) => (
                            <Star key={i} size={10} className={i < Math.floor(solver.score / 20) ? 'text-amber-400 fill-amber-400' : 'text-slate-600'} />
                          ))}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="py-4">
                    <div className="flex items-center gap-2">
                      <span className="text-cyan-400 font-bold">{solver.score}</span>
                      <div className="w-16 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                        <div className="h-full bg-cyan-500 rounded-full" style={{ width: `${solver.score}%` }}></div>
                      </div>
                    </div>
                  </td>
                  <td className="py-4 font-medium text-white">{solver.volume}</td>
                  <td className="py-4 text-emerald-400">{solver.latency}</td>
                  <td className="py-4 text-slate-400">{solver.trades.toLocaleString()}</td>
                  <td className="py-4">
                    <span className="px-2 py-1 bg-slate-700/50 text-slate-300 text-xs rounded-lg">{solver.specialty}</span>
                  </td>
                  <td className="py-4">
                    <StatusBadge status={solver.status} label={solver.status === 'active' ? 'Online' : 'Degraded'} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </GlassCard>

      <div className="grid grid-cols-3 gap-5">
        {/* Volume Chart */}
        <div className="col-span-2">
          <GlassCard>
            <h3 className="text-lg font-bold text-white mb-4">Solver Volume Distribution</h3>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={volumeData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                <XAxis dataKey="name" stroke="#64748b" axisLine={false} tickLine={false} />
                <YAxis stroke="#64748b" axisLine={false} tickLine={false} tickFormatter={(v) => `$${v}k`} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px' }}
                  formatter={(value) => [`$${value}K`, 'Volume']}
                />
                <Bar dataKey="volume" fill="#06b6d4" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </GlassCard>
        </div>

        {/* Network Stats */}
        <GlassCard>
          <h3 className="text-lg font-bold text-white mb-4">Network Statistics</h3>
          <div className="space-y-4">
            {networkStats.map((stat, i) => (
              <div key={i} className="flex items-center justify-between p-3 bg-slate-800/30 rounded-xl">
                <span className="text-slate-400 text-sm">{stat.label}</span>
                <span className="font-semibold text-white">{stat.value}</span>
              </div>
            ))}
          </div>
          <div className="mt-4 pt-4 border-t border-slate-700/50">
            <GlowButton variant="primary" size="md" className="w-full" icon={Zap}>
              Become a Solver
            </GlowButton>
          </div>
        </GlassCard>
      </div>
    </div>
  );
};

export default SolversPage;
