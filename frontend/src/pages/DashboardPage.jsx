import { useState, useEffect, useRef } from 'react';
import { 
  TrendingUp, TrendingDown, Zap, Activity, Wallet, ArrowUpRight, 
  ArrowDownRight, BarChart3, Clock, Shield, Brain, Sparkles
} from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import PerformanceMetrics from '../components/dashboard/PerformanceMetrics';
import AITradingControls from '../components/ai/AITradingControls';
import ProfitableSignals from '../components/trading/ProfitableSignals';
import PositionMonitor from '../components/trading/PositionMonitor';

// Demo wallet address
const DEMO_WALLET = '0x6739659248061A54E0f4de8f2cd60278B69468b3';

// Fetch real market data
const useMarketData = () => {
  const [tokens, setTokens] = useState([]);
  const [ethData, setEthData] = useState({ price: 0, change: 0, chartData: [] });
  const [loading, setLoading] = useState(true);
  const [tokenCharts, setTokenCharts] = useState({});
  const wsRef = useRef(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        // Fetch top 30 tokens
        const tickerRes = await fetch('https://api.binance.com/api/v3/ticker/24hr');
        const tickerData = await tickerRes.json();
        
        // Top 30 popular crypto tokens
        const symbols = [
          'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT', 'ADAUSDT',
          'DOGEUSDT', 'MATICUSDT', 'DOTUSDT', 'LTCUSDT', 'TRXUSDT', 'AVAXUSDT',
          'LINKUSDT', 'ATOMUSDT', 'UNIUSDT', 'ETCUSDT', 'XLMUSDT', 'NEARUSDT',
          'ALGOUSDT', 'VETUSDT', 'ICPUSDT', 'FILUSDT', 'APTUSDT', 'ARBUSDT',
          'OPUSDT', 'INJUSDT', 'SUIUSDT', 'STXUSDT', 'RNDRUSDT', 'TIAUSDT'
        ];
        
        const filtered = tickerData
          .filter(t => symbols.includes(t.symbol))
          .map(t => ({
            symbol: t.symbol.replace('USDT', ''),
            price: parseFloat(t.lastPrice),
            change: parseFloat(t.priceChangePercent),
            volume: parseFloat(t.quoteVolume)
          }))
          .sort((a, b) => symbols.indexOf(a.symbol + 'USDT') - symbols.indexOf(b.symbol + 'USDT'));
        setTokens(filtered);

        // Fetch mini charts for all tokens (last 12 hours)
        const chartPromises = symbols.map(async (symbol) => {
          try {
            const res = await fetch(`https://api.binance.com/api/v3/klines?symbol=${symbol}&interval=1h&limit=12`);
            const data = await res.json();
            return {
              symbol: symbol.replace('USDT', ''),
              data: data.map(k => parseFloat(k[4]))
            };
          } catch {
            return { symbol: symbol.replace('USDT', ''), data: [] };
          }
        });
        
        const charts = await Promise.all(chartPromises);
        const chartsMap = {};
        charts.forEach(c => { chartsMap[c.symbol] = c.data; });
        setTokenCharts(chartsMap);

        // Fetch ETH detailed chart data
        const klinesRes = await fetch('https://api.binance.com/api/v3/klines?symbol=ETHUSDT&interval=1h&limit=24');
        const klinesData = await klinesRes.json();
        const chartData = klinesData.map(k => ({
          time: new Date(k[0]).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
          price: parseFloat(k[4])
        }));
        
        const ethToken = filtered.find(t => t.symbol === 'ETH');
        setEthData({
          price: ethToken?.price || 0,
          change: ethToken?.change || 0,
          chartData
        });
        setLoading(false);
      } catch (e) {
        console.error('Market data error:', e);
        setLoading(false);
      }
    };

    fetchData();

    // WebSocket for real-time updates - subscribe to all 30 tokens
    const symbols = [
      'btcusdt', 'ethusdt', 'bnbusdt', 'solusdt', 'xrpusdt', 'adausdt',
      'dogeusdt', 'maticusdt', 'dotusdt', 'ltcusdt', 'trxusdt', 'avaxusdt',
      'linkusdt', 'atomusdt', 'uniusdt', 'etcusdt', 'xlmusdt', 'nearusdt',
      'algousdt', 'vetusdt', 'icpusdt', 'filusdt', 'aptusdt', 'arbusdt',
      'opusdt', 'injusdt', 'suiusdt', 'stxusdt', 'rndrusdt', 'tiausdt'
    ];
    const streams = symbols.map(s => `${s}@ticker`).join('/');
    wsRef.current = new WebSocket(`wss://stream.binance.com:9443/ws/${streams}`);
    
    wsRef.current.onopen = () => {
      console.log('Dashboard WebSocket connected - 30 tokens');
    };
    
    wsRef.current.onmessage = (e) => {
      const data = JSON.parse(e.data);
      const symbol = data.s.replace('USDT', '');
      
      setTokens(prev => prev.map(t => 
        t.symbol === symbol ? { 
          ...t, 
          price: parseFloat(data.c), 
          change: parseFloat(data.P),
          volume: parseFloat(data.q)
        } : t
      ));
      
      if (symbol === 'ETH') {
        setEthData(prev => ({ 
          ...prev, 
          price: parseFloat(data.c), 
          change: parseFloat(data.P) 
        }));
      }
    };
    
    wsRef.current.onerror = (error) => {
      console.error('Dashboard WebSocket error:', error);
    };

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        console.log('Dashboard WebSocket closed');
      }
    };
  }, []);

  return { tokens, ethData, loading, tokenCharts };
};

const formatPrice = (p) => p >= 1000 ? `${p.toLocaleString(undefined, {maximumFractionDigits: 2})}` : `${p.toFixed(2)}`;

// Mini sparkline chart component
const MiniChart = ({ data, change }) => {
  if (!data || data.length === 0) return null;
  
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;
  const width = 60;
  const height = 24;
  
  const points = data.map((val, i) => {
    const x = (i / (data.length - 1)) * width;
    const y = height - ((val - min) / range) * height;
    return `${x},${y}`;
  }).join(' ');
  
  return (
    <svg width={width} height={height} className="opacity-70">
      <polyline
        points={points}
        fill="none"
        stroke={change >= 0 ? '#10b981' : '#ef4444'}
        strokeWidth="1.5"
      />
    </svg>
  );
};

const DashboardPage = () => {
  const { tokens, ethData, loading, tokenCharts } = useMarketData();
  const [selectedChartToken, setSelectedChartToken] = useState('ETH');
  const [chartData, setChartData] = useState([]);

  // Fetch chart data for selected token
  useEffect(() => {
    const fetchChartData = async () => {
      if (!selectedChartToken) return;
      try {
        const res = await fetch(`https://api.binance.com/api/v3/klines?symbol=${selectedChartToken}USDT&interval=1h&limit=24`);
        const data = await res.json();
        const formatted = data.map(k => ({
          time: new Date(k[0]).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
          price: parseFloat(k[4])
        }));
        setChartData(formatted);
      } catch (e) {
        console.error('Chart fetch error:', e);
      }
    };
    fetchChartData();
  }, [selectedChartToken]);

  // Calculate real portfolio allocation from tokens
  const totalVolume = tokens.reduce((sum, t) => sum + t.volume, 0);
  const portfolioData = tokens.slice(0, 4).map(t => ({
    name: t.symbol,
    value: totalVolume > 0 ? Math.round((t.volume / totalVolume) * 100) : 0,
    color: t.symbol === 'BTC' ? '#F7931A' : t.symbol === 'ETH' ? '#627EEA' : t.symbol === 'SOL' ? '#14F195' : t.symbol === 'BNB' ? '#F3BA2F' : '#6b7280'
  }));

  // Calculate real stats from market data
  const avgChange = tokens.length > 0 ? tokens.reduce((sum, t) => sum + t.change, 0) / tokens.length : 0;
  
  // Get selected token data
  const selectedTokenData = tokens.find(t => t.symbol === selectedChartToken) || { price: 0, change: 0 };

  return (
    <div className="space-y-5">
      {/* Top Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { icon: Wallet, label: 'ETH Price', value: `$${formatPrice(ethData.price)}`, change: ethData.change, color: 'cyan' },
          { icon: Activity, label: 'BTC Price', value: `$${formatPrice(tokens.find(t => t.symbol === 'BTC')?.price || 0)}`, change: tokens.find(t => t.symbol === 'BTC')?.change || 0, color: 'green' },
          { icon: Zap, label: 'Tracked Tokens', value: tokens.length.toString(), change: null, color: 'purple' },
          { icon: Shield, label: 'Market Trend', value: avgChange >= 0 ? 'Bullish' : 'Bearish', change: avgChange, color: 'amber' }
        ].map((stat, i) => (
          <div key={i} className="p-4 rounded-2xl border border-[#2a3441] bg-[#0d1117] hover:border-[#2dd4bf]/30 transition-all">
            <div className="flex items-center justify-between mb-3">
              <div className={`p-2 rounded-xl ${
                stat.color === 'cyan' ? 'bg-[#2dd4bf]/10' :
                stat.color === 'green' ? 'bg-[#10b981]/10' :
                stat.color === 'purple' ? 'bg-purple-500/10' : 'bg-amber-500/10'
              }`}>
                <stat.icon size={18} className={
                  stat.color === 'cyan' ? 'text-[#2dd4bf]' :
                  stat.color === 'green' ? 'text-[#10b981]' :
                  stat.color === 'purple' ? 'text-purple-400' : 'text-amber-400'
                } />
              </div>
              {stat.change !== null && (
                <span className={`flex items-center gap-0.5 text-xs font-medium ${stat.change >= 0 ? 'text-[#10b981]' : 'text-red-400'}`}>
                  {stat.change >= 0 ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}
                  {Math.abs(stat.change).toFixed(2)}%
                </span>
              )}
            </div>
            <p className="text-xs text-gray-500 mb-1">{stat.label}</p>
            <p className="text-xl font-bold text-white">{stat.value}</p>
          </div>
        ))}
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* AI Agent Status */}
        <div className="lg:col-span-3 p-5 rounded-2xl border border-[#2a3441] bg-[#0d1117]">
          <div className="flex items-center gap-2 mb-4">
            <Brain size={18} className="text-[#2dd4bf]" />
            <h3 className="font-semibold text-white">AI Agent</h3>
          </div>
          
          <div className="flex items-center gap-3 mb-5">
            <div className="relative">
              <div className="w-12 h-12 rounded-full border-2 border-[#2dd4bf] flex items-center justify-center">
                <div className="w-4 h-4 rounded-full bg-[#2dd4bf] animate-pulse" />
              </div>
            </div>
            <div>
              <span className="text-[#2dd4bf] font-semibold">ACTIVE</span>
              <p className="text-xs text-gray-500">Monitoring markets</p>
            </div>
          </div>

          <div className="space-y-3">
            <div className="p-3 rounded-xl bg-[#1a1f2e]">
              <p className="text-xs text-gray-500 mb-1">Top Gainer</p>
              <p className="text-sm text-white font-medium">
                {tokens.length > 0 && tokens.reduce((max, t) => t.change > max.change ? t : max, tokens[0]).symbol}
                <span className="text-[#10b981] ml-2">
                  +{tokens.length > 0 && tokens.reduce((max, t) => t.change > max.change ? t : max, tokens[0]).change.toFixed(2)}%
                </span>
              </p>
            </div>
            <div className="p-3 rounded-xl bg-[#1a1f2e]">
              <p className="text-xs text-gray-500 mb-1">BTC Price</p>
              <p className="text-2xl font-bold text-[#2dd4bf]">
                ${tokens.find(t => t.symbol === 'BTC')?.price.toLocaleString() || '0'}
              </p>
            </div>
            <div className="p-3 rounded-xl bg-[#1a1f2e]">
              <p className="text-xs text-gray-500 mb-1">Market Trend</p>
              <p className="text-lg font-bold text-[#10b981]">
                {avgChange >= 0 ? 'Bullish' : 'Bearish'} {Math.abs(avgChange).toFixed(1)}%
              </p>
            </div>
          </div>
        </div>

        {/* Market Chart */}
        <div className="lg:col-span-6 p-5 rounded-2xl border border-[#2a3441] bg-[#0d1117]">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-semibold text-white">{selectedChartToken}/USDT</h3>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-2xl font-bold text-white">${formatPrice(selectedTokenData.price)}</span>
                <span className={`flex items-center gap-0.5 text-sm font-medium px-2 py-0.5 rounded-lg ${
                  selectedTokenData.change >= 0 ? 'bg-[#10b981]/10 text-[#10b981]' : 'bg-red-500/10 text-red-400'
                }`}>
                  {selectedTokenData.change >= 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                  {selectedTokenData.change >= 0 ? '+' : ''}{selectedTokenData.change.toFixed(2)}%
                </span>
              </div>
            </div>
            <div className="flex gap-1">
              {['1H', '24H', '7D', '1M'].map((tf, i) => (
                <button key={tf} className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${
                  i === 1 ? 'bg-[#2dd4bf] text-black' : 'bg-[#1a1f2e] text-gray-400 hover:text-white'
                }`}>{tf}</button>
              ))}
            </div>
          </div>

          <div className="h-[220px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={selectedTokenData.change >= 0 ? '#2dd4bf' : '#ef4444'} stopOpacity={0.3} />
                    <stop offset="100%" stopColor={selectedTokenData.change >= 0 ? '#2dd4bf' : '#ef4444'} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="time" stroke="#4b5563" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: '#6b7280' }} />
                <YAxis stroke="#4b5563" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: '#6b7280' }} domain={['auto', 'auto']} width={60} tickFormatter={v => `$${v.toLocaleString()}`} />
                <Tooltip contentStyle={{ backgroundColor: '#1a1f2e', border: '1px solid #2a3441', borderRadius: '8px' }} formatter={(v) => [`$${Number(v).toLocaleString()}`, 'Price']} />
                <Area type="monotone" dataKey="price" stroke={selectedTokenData.change >= 0 ? '#2dd4bf' : '#ef4444'} strokeWidth={2} fill="url(#chartGradient)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="grid grid-cols-3 gap-3 mt-4 pt-4 border-t border-[#2a3441]">
            {[
              { label: 'BTC Change', value: `${tokens.find(t => t.symbol === 'BTC')?.change >= 0 ? '+' : ''}${tokens.find(t => t.symbol === 'BTC')?.change.toFixed(2) || '0'}%`, icon: Clock },
              { label: 'SOL Price', value: `$${tokens.find(t => t.symbol === 'SOL')?.price.toFixed(2) || '0'}`, icon: BarChart3 },
              { label: 'Tokens', value: tokens.length.toString(), icon: Sparkles }
            ].map((s, i) => (
              <div key={i} className="text-center p-2 rounded-lg bg-[#1a1f2e]">
                <s.icon size={14} className="mx-auto text-gray-500 mb-1" />
                <p className="text-xs text-gray-500">{s.label}</p>
                <p className="text-sm font-bold text-white">{s.value}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Portfolio Allocation */}
        <div className="lg:col-span-3 p-5 rounded-2xl border border-[#2a3441] bg-[#0d1117]">
          <div className="flex items-center gap-2 mb-4">
            <BarChart3 size={18} className="text-purple-400" />
            <h3 className="font-semibold text-white">Allocation</h3>
          </div>

          <div className="h-[140px] mb-4">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={portfolioData} cx="50%" cy="50%" innerRadius={40} outerRadius={60} dataKey="value" stroke="none">
                  {portfolioData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="space-y-2">
            {portfolioData.map((item, i) => (
              <div key={i} className="flex items-center justify-between p-2 rounded-lg bg-[#1a1f2e]">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                  <span className="text-sm text-white">{item.name}</span>
                </div>
                <span className="text-sm text-gray-400">{item.value}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Profitable Signals */}
      <ProfitableSignals />

      {/* Position Monitor */}
      <PositionMonitor />

      {/* Performance Metrics */}
      <PerformanceMetrics walletAddress={DEMO_WALLET} />

      {/* AI Trading Controls */}
      <AITradingControls />

      {/* Market Overview */}
      <div className="p-5 rounded-2xl border border-[#2a3441] bg-[#0d1117]">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <Activity size={18} className="text-[#2dd4bf]" />
            <h3 className="font-semibold text-white">Market Overview - 30 Tokens</h3>
            <span className="flex items-center gap-1.5 text-xs text-[#2dd4bf] bg-[#2dd4bf]/10 px-2 py-1 rounded-full">
              <span className="w-1.5 h-1.5 rounded-full bg-[#2dd4bf] animate-pulse" />
              LIVE
            </span>
          </div>
          <span className="text-xs text-gray-500">Real-time from Binance</span>
        </div>

        {loading ? (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            {[...Array(30)].map((_, i) => (
              <div key={i} className="p-3 rounded-xl bg-[#1a1f2e] animate-pulse">
                <div className="h-4 bg-gray-700 rounded mb-2" />
                <div className="h-6 bg-gray-700 rounded mb-1" />
                <div className="h-5 bg-gray-700 rounded w-3/4" />
              </div>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            {tokens.map((token, i) => (
              <div 
                key={i} 
                onClick={() => setSelectedChartToken(token.symbol)}
                className={`p-3 rounded-xl transition-all cursor-pointer border ${
                  selectedChartToken === token.symbol 
                    ? 'bg-[#2dd4bf]/10 border-[#2dd4bf]/50' 
                    : 'bg-[#1a1f2e] hover:bg-[#1a1f2e]/80 border-transparent hover:border-[#2dd4bf]/20'
                } group`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-semibold text-white">{token.symbol}</span>
                  <span className={`flex items-center gap-0.5 text-xs font-medium ${token.change >= 0 ? 'text-[#10b981]' : 'text-red-400'}`}>
                    {token.change >= 0 ? <TrendingUp size={10} /> : <TrendingDown size={10} />}
                    {token.change >= 0 ? '+' : ''}{token.change.toFixed(2)}%
                  </span>
                </div>
                <p className="text-lg font-bold text-white mb-2">${formatPrice(token.price)}</p>
                <div className="flex justify-center">
                  <MiniChart data={tokenCharts[token.symbol]} change={token.change} />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default DashboardPage;
