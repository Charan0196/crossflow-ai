import { Shield, AlertCircle, Activity, Target, TrendingDown, CheckCircle } from 'lucide-react';
import { RadialBarChart, RadialBar, ResponsiveContainer, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';
import { GlassCard, MetricCard, StatusBadge, GlowButton } from '../components/common/UI';

const RiskPage = () => {
  const riskData = [
    { name: 'Market Risk', value: 65, fill: '#06b6d4' },
    { name: 'Liquidity Risk', value: 45, fill: '#8b5cf6' },
    { name: 'Smart Contract', value: 25, fill: '#10b981' },
    { name: 'Counterparty', value: 35, fill: '#f59e0b' }
  ];

  const exposureData = [
    { chain: 'Ethereum', exposure: 45000, limit: 60000 },
    { chain: 'Polygon', exposure: 15000, limit: 25000 },
    { chain: 'Arbitrum', exposure: 22000, limit: 30000 },
    { chain: 'Optimism', exposure: 8000, limit: 20000 }
  ];

  const alerts = [
    { level: 'low', message: 'Portfolio well diversified across 5 chains', time: '2m ago', action: null },
    { level: 'medium', message: 'ETH exposure above 40% threshold', time: '15m ago', action: 'Rebalance' },
    { level: 'low', message: 'All smart contracts audited', time: '1h ago', action: null }
  ];

  const riskMetrics = [
    { label: 'Value at Risk (95%)', value: '$2,340', status: 'normal' },
    { label: 'Max Drawdown', value: '-12.5%', status: 'warning' },
    { label: 'Sharpe Ratio', value: '1.85', status: 'good' },
    { label: 'Beta', value: '0.92', status: 'normal' }
  ];

  return (
    <div className="space-y-6">
      {/* Metrics */}
      <div className="grid grid-cols-4 gap-5">
        <MetricCard icon={Shield} label="Risk Score" value="32/100" color="emerald" subtitle="Low risk" />
        <MetricCard icon={AlertCircle} label="Total Exposure" value="$90.2K" change={-5.2} color="amber" subtitle="Across all chains" />
        <MetricCard icon={Activity} label="VaR (95%)" value="$2,340" color="purple" subtitle="Daily" />
        <MetricCard icon={Target} label="Sharpe Ratio" value="1.85" change={0.12} color="cyan" subtitle="30-day" />
      </div>

      <div className="grid grid-cols-2 gap-5">
        {/* Risk Distribution */}
        <GlassCard>
          <h3 className="text-lg font-bold text-white mb-4">Risk Distribution</h3>
          <div className="flex items-center">
            <ResponsiveContainer width="60%" height={280}>
              <RadialBarChart cx="50%" cy="50%" innerRadius="30%" outerRadius="100%" data={riskData} startAngle={180} endAngle={-180}>
                <RadialBar dataKey="value" cornerRadius={10} background={{ fill: '#1e293b' }} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px' }}
                  formatter={(value) => [`${value}%`, 'Risk Level']}
                />
              </RadialBarChart>
            </ResponsiveContainer>
            <div className="flex-1 space-y-3">
              {riskData.map((item, i) => (
                <div key={i} className="flex items-center gap-3">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.fill }}></div>
                  <div className="flex-1">
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-400">{item.name}</span>
                      <span className="text-white font-medium">{item.value}%</span>
                    </div>
                    <div className="h-1.5 bg-slate-700 rounded-full mt-1 overflow-hidden">
                      <div className="h-full rounded-full" style={{ width: `${item.value}%`, backgroundColor: item.fill }}></div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </GlassCard>

        {/* Chain Exposure */}
        <GlassCard>
          <h3 className="text-lg font-bold text-white mb-4">Chain Exposure</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={exposureData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" horizontal={false} />
              <XAxis type="number" stroke="#64748b" axisLine={false} tickLine={false} tickFormatter={(v) => `$${v/1000}k`} />
              <YAxis type="category" dataKey="chain" stroke="#64748b" axisLine={false} tickLine={false} width={80} />
              <Tooltip 
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '12px' }}
                formatter={(value) => [`$${value.toLocaleString()}`, '']}
              />
              <Bar dataKey="exposure" fill="#10b981" radius={[0, 4, 4, 0]} name="Current" />
              <Bar dataKey="limit" fill="#334155" radius={[0, 4, 4, 0]} name="Limit" />
            </BarChart>
          </ResponsiveContainer>
        </GlassCard>
      </div>

      <div className="grid grid-cols-3 gap-5">
        {/* Risk Alerts */}
        <div className="col-span-2">
          <GlassCard>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-white">Risk Alerts</h3>
              <StatusBadge status="active" label="Monitoring" />
            </div>
            <div className="space-y-3">
              {alerts.map((alert, i) => (
                <div key={i} className={`flex items-center gap-4 p-4 rounded-xl border ${
                  alert.level === 'low' ? 'bg-emerald-500/5 border-emerald-500/20' :
                  alert.level === 'medium' ? 'bg-amber-500/5 border-amber-500/20' :
                  'bg-red-500/5 border-red-500/20'
                }`}>
                  <div className={`p-2 rounded-lg ${
                    alert.level === 'low' ? 'bg-emerald-500/20' :
                    alert.level === 'medium' ? 'bg-amber-500/20' : 'bg-red-500/20'
                  }`}>
                    {alert.level === 'low' ? (
                      <CheckCircle size={20} className="text-emerald-400" />
                    ) : (
                      <AlertCircle size={20} className={alert.level === 'medium' ? 'text-amber-400' : 'text-red-400'} />
                    )}
                  </div>
                  <div className="flex-1">
                    <p className="font-medium text-white">{alert.message}</p>
                    <p className="text-sm text-slate-500">{alert.time}</p>
                  </div>
                  {alert.action && (
                    <GlowButton variant="outline" size="sm">{alert.action}</GlowButton>
                  )}
                </div>
              ))}
            </div>
          </GlassCard>
        </div>

        {/* Risk Metrics */}
        <GlassCard>
          <h3 className="text-lg font-bold text-white mb-4">Key Metrics</h3>
          <div className="space-y-4">
            {riskMetrics.map((metric, i) => (
              <div key={i} className="flex items-center justify-between p-3 bg-slate-800/30 rounded-xl">
                <span className="text-slate-400 text-sm">{metric.label}</span>
                <span className={`font-semibold ${
                  metric.status === 'good' ? 'text-emerald-400' :
                  metric.status === 'warning' ? 'text-amber-400' : 'text-white'
                }`}>
                  {metric.value}
                </span>
              </div>
            ))}
          </div>
          <div className="mt-4 pt-4 border-t border-slate-700/50">
            <GlowButton variant="secondary" size="md" className="w-full" icon={TrendingDown}>
              Run Stress Test
            </GlowButton>
          </div>
        </GlassCard>
      </div>
    </div>
  );
};

export default RiskPage;
