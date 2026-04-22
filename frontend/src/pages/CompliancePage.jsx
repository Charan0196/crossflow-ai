import { FileCheck, Shield, Clock, AlertCircle, CheckCircle, Play, Pause, RefreshCw, Eye, Lock } from 'lucide-react';
import { GlassCard, MetricCard, StatusBadge, GlowButton } from '../components/common/UI';

const CompliancePage = () => {
  const complianceItems = [
    { item: 'Transparency Requirements', score: 100, status: 'passed' },
    { item: 'Human Oversight', score: 98, status: 'passed' },
    { item: 'Risk Assessment', score: 95, status: 'passed' },
    { item: 'Data Governance', score: 97, status: 'passed' },
    { item: 'Algorithmic Accountability', score: 92, status: 'passed' },
    { item: 'User Rights Protection', score: 100, status: 'passed' }
  ];

  const auditHistory = [
    { date: '2024-01-15', type: 'Full Audit', result: 'Passed', auditor: 'CertiK', score: 98 },
    { date: '2024-01-01', type: 'Smart Contract', result: 'Passed', auditor: 'OpenZeppelin', score: 100 },
    { date: '2023-12-15', type: 'AI Model', result: 'Passed', auditor: 'Trail of Bits', score: 95 }
  ];

  const overrideControls = [
    { label: 'Auto-Trading', status: 'active', description: 'AI-powered automated trading' },
    { label: 'Emergency Stop', status: 'standby', description: 'Halt all trading immediately' },
    { label: 'Manual Review', status: 'inactive', description: 'Require human approval for trades' },
    { label: 'Position Limits', status: 'active', description: 'Enforce maximum position sizes' }
  ];

  return (
    <div className="space-y-6">
      {/* Metrics */}
      <div className="grid grid-cols-4 gap-5">
        <MetricCard icon={FileCheck} label="Compliance Score" value="98%" color="emerald" subtitle="Overall rating" />
        <MetricCard icon={Shield} label="Audit Status" value="Passed" color="cyan" subtitle="All checks passed" />
        <MetricCard icon={Clock} label="Last Audit" value="2h ago" color="purple" subtitle="Continuous monitoring" />
        <MetricCard icon={AlertCircle} label="Violations" value="0" color="amber" subtitle="No issues found" />
      </div>

      <div className="grid grid-cols-2 gap-5">
        {/* EU AI Act Compliance */}
        <GlassCard>
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 bg-gradient-to-br from-emerald-500 to-green-600 rounded-xl flex items-center justify-center shadow-lg shadow-emerald-500/25">
              <FileCheck size={20} className="text-white" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white">EU AI Act Compliance</h3>
              <p className="text-slate-400 text-sm">Regulatory requirements status</p>
            </div>
          </div>

          <div className="space-y-4">
            {complianceItems.map((item, i) => (
              <div key={i} className="flex items-center justify-between p-4 bg-slate-800/30 rounded-xl">
                <div className="flex items-center gap-3">
                  <CheckCircle size={18} className="text-emerald-400" />
                  <span className="text-white">{item.item}</span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-24 h-2 bg-slate-700 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-emerald-500 rounded-full transition-all" 
                      style={{ width: `${item.score}%` }}
                    ></div>
                  </div>
                  <span className="text-emerald-400 font-semibold w-12 text-right">{item.score}%</span>
                </div>
              </div>
            ))}
          </div>
        </GlassCard>

        {/* Human Override Controls */}
        <GlassCard>
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-600 rounded-xl flex items-center justify-center shadow-lg shadow-purple-500/25">
              <Eye size={20} className="text-white" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white">Human Override Controls</h3>
              <p className="text-slate-400 text-sm">Manual intervention options</p>
            </div>
          </div>

          <div className="space-y-4">
            {overrideControls.map((control, i) => (
              <div key={i} className="flex items-center justify-between p-4 bg-slate-800/30 rounded-xl">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${
                    control.status === 'active' ? 'bg-emerald-500/20' :
                    control.status === 'standby' ? 'bg-amber-500/20' : 'bg-slate-700/50'
                  }`}>
                    {control.label === 'Auto-Trading' ? <Play size={16} className={control.status === 'active' ? 'text-emerald-400' : 'text-slate-400'} /> :
                     control.label === 'Emergency Stop' ? <Pause size={16} className="text-amber-400" /> :
                     control.label === 'Manual Review' ? <Eye size={16} className="text-slate-400" /> :
                     <Lock size={16} className={control.status === 'active' ? 'text-emerald-400' : 'text-slate-400'} />}
                  </div>
                  <div>
                    <p className="font-medium text-white">{control.label}</p>
                    <p className="text-xs text-slate-500">{control.description}</p>
                  </div>
                </div>
                <GlowButton 
                  variant={control.status === 'active' ? 'ghost' : control.label === 'Emergency Stop' ? 'danger' : 'secondary'} 
                  size="sm"
                >
                  {control.status === 'active' ? 'Active' : control.label === 'Emergency Stop' ? 'Trigger' : 'Enable'}
                </GlowButton>
              </div>
            ))}
          </div>
        </GlassCard>
      </div>

      {/* Audit History */}
      <GlassCard>
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-bold text-white">Audit History</h3>
          <GlowButton variant="outline" size="sm" icon={RefreshCw}>Request Audit</GlowButton>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-left text-slate-400 text-sm border-b border-slate-700/50">
                <th className="pb-4 font-medium">Date</th>
                <th className="pb-4 font-medium">Type</th>
                <th className="pb-4 font-medium">Auditor</th>
                <th className="pb-4 font-medium">Score</th>
                <th className="pb-4 font-medium">Result</th>
                <th className="pb-4 font-medium">Report</th>
              </tr>
            </thead>
            <tbody>
              {auditHistory.map((audit, i) => (
                <tr key={i} className="border-b border-slate-800/50">
                  <td className="py-4 text-slate-400">{audit.date}</td>
                  <td className="py-4 text-white font-medium">{audit.type}</td>
                  <td className="py-4">
                    <span className="px-2 py-1 bg-slate-700/50 text-slate-300 text-xs rounded">{audit.auditor}</span>
                  </td>
                  <td className="py-4">
                    <div className="flex items-center gap-2">
                      <span className="text-emerald-400 font-bold">{audit.score}</span>
                      <div className="w-16 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                        <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${audit.score}%` }}></div>
                      </div>
                    </div>
                  </td>
                  <td className="py-4">
                    <StatusBadge status="active" label={audit.result} />
                  </td>
                  <td className="py-4">
                    <GlowButton variant="ghost" size="sm">View</GlowButton>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </GlassCard>

      {/* Compliance Notice */}
      <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl">
        <div className="flex items-center gap-3">
          <CheckCircle size={20} className="text-emerald-400" />
          <div>
            <p className="font-medium text-emerald-400">Fully Compliant</p>
            <p className="text-sm text-slate-400">CrossFlow AI meets all EU AI Act requirements for high-risk AI systems in financial services.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CompliancePage;
