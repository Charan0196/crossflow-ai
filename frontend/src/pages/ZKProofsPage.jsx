import { CheckCircle, Lock, Zap, Shield, Eye, FileCheck, Clock, Hash } from 'lucide-react';
import { GlassCard, MetricCard, StatusBadge, GlowButton } from '../components/common/UI';

const ZKProofsPage = () => {
  const recentProofs = [
    { type: 'Strategy ROI', hash: '0x1a2b3c4d...5e6f7g8h', time: '2m ago', status: 'verified', prover: 'Groth16' },
    { type: 'Trade Execution', hash: '0x9i0j1k2l...3m4n5o6p', time: '15m ago', status: 'verified', prover: 'PLONK' },
    { type: 'Risk Assessment', hash: '0xqrst7u8v...wxyz1234', time: '1h ago', status: 'verified', prover: 'Groth16' },
    { type: 'Portfolio Balance', hash: '0x5678abcd...efgh9012', time: '3h ago', status: 'verified', prover: 'STARK' }
  ];

  const proofTypes = [
    { name: 'Performance Proofs', description: 'Verify strategy returns without revealing trades', count: 1247, icon: '📈' },
    { name: 'Balance Proofs', description: 'Prove solvency without exposing holdings', count: 856, icon: '💰' },
    { name: 'Compliance Proofs', description: 'Demonstrate regulatory compliance privately', count: 423, icon: '✅' },
    { name: 'Identity Proofs', description: 'KYC verification without data exposure', count: 312, icon: '🔐' }
  ];

  return (
    <div className="space-y-6">
      {/* Metrics */}
      <div className="grid grid-cols-4 gap-5">
        <MetricCard icon={CheckCircle} label="Verified Proofs" value="1,247" change={8.5} color="emerald" subtitle="Total generated" />
        <MetricCard icon={Lock} label="Privacy Score" value="100%" color="cyan" subtitle="Zero knowledge" />
        <MetricCard icon={Zap} label="Avg Proof Time" value="2.3s" color="purple" subtitle="Generation time" />
        <MetricCard icon={Shield} label="Security Level" value="High" color="amber" subtitle="256-bit security" />
      </div>

      <div className="grid grid-cols-3 gap-5">
        {/* ZK Proof Status */}
        <GlassCard glow className="col-span-1">
          <h3 className="text-lg font-bold text-white mb-6">Proof Status</h3>
          
          <div className="flex items-center justify-center py-6">
            <div className="relative">
              <div className="w-40 h-40 rounded-full border-4 border-emerald-500/20 flex items-center justify-center">
                <div className="w-32 h-32 rounded-full border-4 border-emerald-500/40 flex items-center justify-center animate-pulse">
                  <div className="w-24 h-24 rounded-full bg-emerald-500/20 flex items-center justify-center">
                    <CheckCircle size={48} className="text-emerald-400" />
                  </div>
                </div>
              </div>
              <div className="absolute -top-2 -right-2 px-3 py-1 bg-emerald-500 rounded-full text-sm font-bold text-black shadow-lg shadow-emerald-500/50">
                Verified
              </div>
            </div>
          </div>

          <div className="text-center mt-4">
            <p className="text-slate-400">All Proofs Valid</p>
            <p className="text-emerald-400 font-semibold mt-1">Zero-Knowledge Verified</p>
          </div>

          <div className="mt-6 space-y-2">
            <GlowButton variant="primary" size="md" className="w-full" icon={Zap}>Generate New Proof</GlowButton>
            <GlowButton variant="ghost" size="sm" className="w-full">Verify External Proof</GlowButton>
          </div>
        </GlassCard>

        {/* Proof Types */}
        <GlassCard className="col-span-2">
          <h3 className="text-lg font-bold text-white mb-4">Proof Types</h3>
          <div className="grid grid-cols-2 gap-4">
            {proofTypes.map((proof, i) => (
              <div key={i} className="p-4 bg-slate-800/30 rounded-xl border border-slate-700/30 hover:border-emerald-500/30 transition-all">
                <div className="flex items-center gap-3 mb-3">
                  <span className="text-2xl">{proof.icon}</span>
                  <div>
                    <p className="font-semibold text-white">{proof.name}</p>
                    <p className="text-xs text-slate-500">{proof.description}</p>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400 text-sm">{proof.count.toLocaleString()} proofs</span>
                  <GlowButton variant="ghost" size="sm">Generate</GlowButton>
                </div>
              </div>
            ))}
          </div>
        </GlassCard>
      </div>

      {/* Recent Verifications */}
      <GlassCard>
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-bold text-white">Recent Verifications</h3>
          <div className="flex items-center gap-2 text-sm text-slate-400">
            <Clock size={14} />
            <span>Auto-refreshing</span>
            <StatusBadge status="active" label="Live" />
          </div>
        </div>

        <div className="space-y-3">
          {recentProofs.map((proof, i) => (
            <div key={i} className="flex items-center justify-between p-4 bg-slate-800/30 rounded-xl border border-slate-700/30 hover:border-emerald-500/20 transition-all">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-emerald-500/20 rounded-xl flex items-center justify-center">
                  <CheckCircle size={24} className="text-emerald-400" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <p className="font-semibold text-white">{proof.type}</p>
                    <span className="px-2 py-0.5 bg-purple-500/20 text-purple-400 text-xs rounded font-medium">{proof.prover}</span>
                  </div>
                  <div className="flex items-center gap-2 mt-1">
                    <Hash size={12} className="text-slate-500" />
                    <span className="font-mono text-sm text-slate-500">{proof.hash}</span>
                  </div>
                </div>
              </div>
              <div className="text-right">
                <StatusBadge status="active" label="Verified" />
                <p className="text-xs text-slate-500 mt-1">{proof.time}</p>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-4 flex justify-center">
          <GlowButton variant="ghost" size="sm">View All Proofs</GlowButton>
        </div>
      </GlassCard>

      {/* How It Works */}
      <GlassCard>
        <h3 className="text-lg font-bold text-white mb-4">How ZK Proofs Work</h3>
        <div className="grid grid-cols-4 gap-4">
          {[
            { step: 1, title: 'Generate', desc: 'Create proof from private data', icon: FileCheck },
            { step: 2, title: 'Compute', desc: 'ZK circuit processes inputs', icon: Zap },
            { step: 3, title: 'Verify', desc: 'On-chain verification', icon: Shield },
            { step: 4, title: 'Confirm', desc: 'Proof validated publicly', icon: CheckCircle }
          ].map((item, i) => (
            <div key={i} className="text-center p-4">
              <div className="w-12 h-12 bg-gradient-to-br from-emerald-500/20 to-green-500/10 rounded-xl flex items-center justify-center mx-auto mb-3">
                <item.icon size={24} className="text-emerald-400" />
              </div>
              <div className="text-xs text-emerald-400 font-bold mb-1">Step {item.step}</div>
              <p className="font-semibold text-white text-sm">{item.title}</p>
              <p className="text-xs text-slate-500 mt-1">{item.desc}</p>
            </div>
          ))}
        </div>
      </GlassCard>
    </div>
  );
};

export default ZKProofsPage;
