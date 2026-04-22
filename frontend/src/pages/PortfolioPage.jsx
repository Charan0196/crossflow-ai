import { useState, useEffect } from 'react';
import { Wallet, TrendingUp, Activity, RefreshCw, ChevronDown, ExternalLink, Sparkles, Zap, Globe, Copy, Check, Coins } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { useAccount, useBalance, useNetwork, useContractRead } from 'wagmi';
import AISignalsPanel from '../components/ai/AISignalsPanel';
import PortfolioHoldings from '../components/portfolio/PortfolioHoldings';
import TradeHistoryTable from '../components/trading/TradeHistoryTable';
import PerformanceMetrics from '../components/dashboard/PerformanceMetrics';

// Demo wallet address
const DEMO_WALLET = '0x6739659248061A54E0f4de8f2cd60278B69468b3';

// Supported networks with their native tokens and explorers
const networks = [
  { id: 1, name: 'Ethereum', symbol: 'ETH', icon: '⟠', color: '#627EEA', gradient: 'from-blue-500 to-purple-600', explorer: 'https://etherscan.io' },
  { id: 137, name: 'Polygon', symbol: 'MATIC', icon: '⬡', color: '#8247E5', gradient: 'from-purple-500 to-pink-500', explorer: 'https://polygonscan.com' },
  { id: 42161, name: 'Arbitrum', symbol: 'ETH', icon: '🔵', color: '#28A0F0', gradient: 'from-blue-400 to-cyan-500', explorer: 'https://arbiscan.io' },
  { id: 10, name: 'Optimism', symbol: 'ETH', icon: '🔴', color: '#FF0420', gradient: 'from-red-500 to-orange-500', explorer: 'https://optimistic.etherscan.io' },
  { id: 56, name: 'BNB Chain', symbol: 'BNB', icon: '🟡', color: '#F3BA2F', gradient: 'from-yellow-400 to-orange-500', explorer: 'https://bscscan.com' },
  { id: 43114, name: 'Avalanche', symbol: 'AVAX', icon: '🔺', color: '#E84142', gradient: 'from-red-500 to-red-700', explorer: 'https://snowtrace.io' },
  { id: 8453, name: 'Base', symbol: 'ETH', icon: '🔵', color: '#0052FF', gradient: 'from-blue-600 to-blue-800', explorer: 'https://basescan.org' },
];

// Common ERC-20 tokens with contract addresses per network
const commonTokens = {
  1: [ // Ethereum
    { symbol: 'USDT', name: 'Tether USD', address: '0xdAC17F958D2ee523a2206206994597C13D831ec7', decimals: 6 },
    { symbol: 'USDC', name: 'USD Coin', address: '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48', decimals: 6 },
    { symbol: 'WETH', name: 'Wrapped Ether', address: '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2', decimals: 18 },
    { symbol: 'DAI', name: 'Dai Stablecoin', address: '0x6B175474E89094C44Da98b954EedeAC495271d0F', decimals: 18 },
    { symbol: 'LINK', name: 'Chainlink', address: '0x514910771AF9Ca656af840dff83E8264EcF986CA', decimals: 18 },
    { symbol: 'UNI', name: 'Uniswap', address: '0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984', decimals: 18 },
  ],
  137: [ // Polygon
    { symbol: 'USDT', name: 'Tether USD', address: '0xc2132D05D31c914a87C6611C10748AEb04B58e8F', decimals: 6 },
    { symbol: 'USDC', name: 'USD Coin', address: '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174', decimals: 6 },
    { symbol: 'WETH', name: 'Wrapped Ether', address: '0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619', decimals: 18 },
    { symbol: 'DAI', name: 'Dai Stablecoin', address: '0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063', decimals: 18 },
    { symbol: 'WMATIC', name: 'Wrapped Matic', address: '0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270', decimals: 18 },
  ],
  42161: [ // Arbitrum
    { symbol: 'USDT', name: 'Tether USD', address: '0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9', decimals: 6 },
    { symbol: 'USDC', name: 'USD Coin', address: '0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8', decimals: 6 },
    { symbol: 'WETH', name: 'Wrapped Ether', address: '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1', decimals: 18 },
    { symbol: 'DAI', name: 'Dai Stablecoin', address: '0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1', decimals: 18 },
  ],
  56: [ // BNB Chain
    { symbol: 'USDT', name: 'Tether USD', address: '0x55d398326f99059fF775485246999027B3197955', decimals: 18 },
    { symbol: 'USDC', name: 'USD Coin', address: '0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d', decimals: 18 },
    { symbol: 'WBNB', name: 'Wrapped BNB', address: '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c', decimals: 18 },
    { symbol: 'BUSD', name: 'Binance USD', address: '0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56', decimals: 18 },
  ],
};

// Hook to fetch live prices for all tokens
const useLivePrices = () => {
  const [prices, setPrices] = useState({});

  useEffect(() => {
    const fetchPrices = async () => {
      try {
        const symbols = ['ETHUSDT', 'MATICUSDT', 'BNBUSDT', 'AVAXUSDT', 'LINKUSDT', 'UNIUSDT'];
        const res = await fetch(`https://api.binance.com/api/v3/ticker/price?symbols=${JSON.stringify(symbols)}`);
        const data = await res.json();
        const priceMap = { USDT: 1, USDC: 1, DAI: 1, BUSD: 1, WETH: 0, WMATIC: 0, WBNB: 0 };
        data.forEach(t => {
          const symbol = t.symbol.replace('USDT', '');
          priceMap[symbol] = parseFloat(t.price);
          // Set wrapped token prices equal to native
          if (symbol === 'ETH') priceMap['WETH'] = parseFloat(t.price);
          if (symbol === 'MATIC') priceMap['WMATIC'] = parseFloat(t.price);
          if (symbol === 'BNB') priceMap['WBNB'] = parseFloat(t.price);
        });
        setPrices(priceMap);
      } catch {
        setPrices({ ETH: 2650, MATIC: 0.85, BNB: 580, AVAX: 35, USDT: 1, USDC: 1, DAI: 1, WETH: 2650, LINK: 15, UNI: 8 });
      }
    };
    fetchPrices();
    const interval = setInterval(fetchPrices, 30000);
    return () => clearInterval(interval);
  }, []);

  return prices;
};

// Multi-chain balance hook using wagmi
const useMultiChainBalances = (address) => {
  const [balances, setBalances] = useState({});
  const [loading, setLoading] = useState(true);

  const { data: ethBalance } = useBalance({ address, chainId: 1, watch: true });
  const { data: polygonBalance } = useBalance({ address, chainId: 137, watch: true });
  const { data: arbitrumBalance } = useBalance({ address, chainId: 42161, watch: true });
  const { data: optimismBalance } = useBalance({ address, chainId: 10, watch: true });
  const { data: bnbBalance } = useBalance({ address, chainId: 56, watch: true });
  const { data: avalancheBalance } = useBalance({ address, chainId: 43114, watch: true });
  const { data: baseBalance } = useBalance({ address, chainId: 8453, watch: true });

  useEffect(() => {
    const newBalances = {
      1: ethBalance ? parseFloat(ethBalance.formatted) : 0,
      137: polygonBalance ? parseFloat(polygonBalance.formatted) : 0,
      42161: arbitrumBalance ? parseFloat(arbitrumBalance.formatted) : 0,
      10: optimismBalance ? parseFloat(optimismBalance.formatted) : 0,
      56: bnbBalance ? parseFloat(bnbBalance.formatted) : 0,
      43114: avalancheBalance ? parseFloat(avalancheBalance.formatted) : 0,
      8453: baseBalance ? parseFloat(baseBalance.formatted) : 0,
    };
    setBalances(newBalances);
    setLoading(false);
  }, [ethBalance, polygonBalance, arbitrumBalance, optimismBalance, bnbBalance, avalancheBalance, baseBalance]);

  return { balances, loading };
};

const PortfolioPage = () => {
  const { address, isConnected } = useAccount();
  const { chain } = useNetwork();
  const prices = useLivePrices();
  const { balances, loading } = useMultiChainBalances(address);
  const [selectedNetwork, setSelectedNetwork] = useState('all');
  const [showNetworkDropdown, setShowNetworkDropdown] = useState(false);
  const [copied, setCopied] = useState(false);

  // Calculate USD values for each network
  const networkBalances = networks.map(network => {
    const balance = balances[network.id] || 0;
    const price = prices[network.symbol] || 0;
    const usdValue = balance * price;
    return { ...network, balance, usdValue };
  });

  // Total portfolio value
  const totalValue = networkBalances.reduce((sum, n) => sum + n.usdValue, 0);

  // Pie chart data
  const pieData = networkBalances
    .filter(n => n.usdValue > 0)
    .map(n => ({ name: n.name, value: n.usdValue, color: n.color }));

  // Performance data (simulated based on total value)
  const performanceData = Array.from({ length: 24 }, (_, i) => ({
    time: `${i}:00`,
    value: totalValue * (0.95 + Math.random() * 0.1)
  }));

  const copyAddress = () => {
    navigator.clipboard.writeText(address);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!isConnected) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] text-center animate-fade-in">
        <div className="w-24 h-24 rounded-3xl bg-gradient-to-br from-[#2dd4bf]/20 to-[#06b6d4]/10 flex items-center justify-center mb-8 shadow-xl shadow-[#2dd4bf]/20">
          <Wallet size={48} className="text-[#2dd4bf]" />
        </div>
        <h2 className="text-3xl font-bold text-white mb-3">Connect Your Wallet</h2>
        <p className="text-gray-400 mb-8 max-w-md">Connect your wallet to view your portfolio across all supported networks</p>
        <div className="flex items-center gap-3 text-sm text-gray-500">
          <Globe size={16} />
          <span>Supporting {networks.length} networks</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Total Balance Card */}
        <div className="p-6 rounded-3xl border border-[#2dd4bf]/30 bg-gradient-to-br from-[#2dd4bf]/10 via-[#1a1f2e] to-[#06b6d4]/5 backdrop-blur-xl shadow-xl shadow-[#2dd4bf]/10">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 rounded-xl bg-[#2dd4bf]/20">
              <Wallet size={18} className="text-[#2dd4bf]" />
            </div>
            <span className="text-gray-400 text-sm font-medium">Total Balance</span>
          </div>
          <p className="text-4xl font-bold text-white mb-2">${totalValue.toLocaleString(undefined, { maximumFractionDigits: 2 })}</p>
          <p className="text-[#2dd4bf] text-sm flex items-center gap-2">
            <Sparkles size={14} />
            Across {networkBalances.filter(n => n.balance > 0).length} networks
          </p>
        </div>

        {/* 24h Change Card */}
        <div className="p-6 rounded-3xl border border-[#2a3441] bg-gradient-to-br from-[#1a1f2e] to-[#0d1117] backdrop-blur-xl hover:border-[#2dd4bf]/30 transition-all">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 rounded-xl bg-green-500/20">
              <TrendingUp size={18} className="text-green-400" />
            </div>
            <span className="text-gray-400 text-sm font-medium">24h Change</span>
          </div>
          <p className="text-3xl font-bold text-green-400">+$124.50</p>
          <p className="text-gray-500 text-sm mt-1">+2.34%</p>
        </div>

        {/* Active Networks Card */}
        <div className="p-6 rounded-3xl border border-[#2a3441] bg-gradient-to-br from-[#1a1f2e] to-[#0d1117] backdrop-blur-xl hover:border-[#2dd4bf]/30 transition-all">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 rounded-xl bg-blue-500/20">
              <Activity size={18} className="text-blue-400" />
            </div>
            <span className="text-gray-400 text-sm font-medium">Active Networks</span>
          </div>
          <p className="text-3xl font-bold text-white">{networkBalances.filter(n => n.balance > 0).length}</p>
          <p className="text-gray-500 text-sm mt-1">of {networks.length} supported</p>
        </div>

        {/* Current Network Card */}
        <div className="p-6 rounded-3xl border border-[#2a3441] bg-gradient-to-br from-[#1a1f2e] to-[#0d1117] backdrop-blur-xl hover:border-[#2dd4bf]/30 transition-all">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 rounded-xl bg-purple-500/20">
              <Globe size={18} className="text-purple-400" />
            </div>
            <span className="text-gray-400 text-sm font-medium">Current Network</span>
          </div>
          <p className="text-xl font-bold text-white flex items-center gap-3">
            <span className="text-2xl">{networks.find(n => n.id === chain?.id)?.icon || '⟠'}</span>
            {chain?.name || 'Ethereum'}
          </p>
          <p className="text-gray-500 text-sm mt-1">Chain ID: {chain?.id || 1}</p>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Portfolio Chart */}
        <div className="lg:col-span-8 p-6 rounded-3xl border border-[#2a3441] bg-gradient-to-br from-[#1a1f2e] to-[#0d1117] backdrop-blur-xl">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                Portfolio Value
                <Sparkles size={16} className="text-[#2dd4bf]" />
              </h2>
              <p className="text-gray-500 text-sm">24 hour performance</p>
            </div>
            <button className="p-3 rounded-xl bg-[#0d1117] border border-[#2a3441] hover:border-[#2dd4bf] hover:shadow-lg hover:shadow-[#2dd4bf]/10 transition-all group">
              <RefreshCw size={18} className="text-gray-400 group-hover:text-[#2dd4bf] group-hover:rotate-180 transition-all duration-500" />
            </button>
          </div>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={performanceData}>
                <defs>
                  <linearGradient id="portfolioGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#2dd4bf" stopOpacity={0.4} />
                    <stop offset="50%" stopColor="#2dd4bf" stopOpacity={0.1} />
                    <stop offset="100%" stopColor="#2dd4bf" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="time" stroke="#4b5563" axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: '#6b7280' }} />
                <YAxis stroke="#4b5563" axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: '#6b7280' }} 
                  tickFormatter={v => `$${(v/1000).toFixed(1)}k`} width={70} domain={['auto', 'auto']} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1a1f2e', 
                    border: '1px solid #2a3441', 
                    borderRadius: '12px',
                    boxShadow: '0 10px 40px rgba(0,0,0,0.5)'
                  }}
                  formatter={(v) => [`$${Number(v).toLocaleString(undefined, { maximumFractionDigits: 2 })}`, 'Value']} 
                />
                <Area type="monotone" dataKey="value" stroke="#2dd4bf" strokeWidth={2.5} fill="url(#portfolioGradient)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Allocation Pie */}
        <div className="lg:col-span-4 p-6 rounded-3xl border border-[#2a3441] bg-gradient-to-br from-[#1a1f2e] to-[#0d1117] backdrop-blur-xl">
          <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
            Network Allocation
            <Zap size={16} className="text-yellow-400" />
          </h2>
          {pieData.length > 0 ? (
            <>
              <div className="h-[200px]">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={pieData} cx="50%" cy="50%" innerRadius={55} outerRadius={85} paddingAngle={4} dataKey="value">
                      {pieData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                    </Pie>
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: '#1a1f2e', 
                        border: '1px solid #2a3441', 
                        borderRadius: '12px' 
                      }}
                      formatter={(v) => [`$${Number(v).toLocaleString(undefined, { maximumFractionDigits: 2 })}`, 'Value']} 
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="space-y-3 mt-6">
                {pieData.map((item, i) => (
                  <div key={i} className="flex items-center justify-between p-3 rounded-xl bg-[#0d1117]/50 border border-[#2a3441]/50">
                    <div className="flex items-center gap-3">
                      <div className="w-4 h-4 rounded-full shadow-lg" style={{ backgroundColor: item.color, boxShadow: `0 2px 8px ${item.color}40` }} />
                      <span className="text-gray-400 font-medium">{item.name}</span>
                    </div>
                    <span className="text-white font-bold">{((item.value / totalValue) * 100).toFixed(1)}%</span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="h-[250px] flex flex-col items-center justify-center text-gray-500">
              <div className="w-16 h-16 rounded-2xl bg-[#2a3441]/50 flex items-center justify-center mb-4">
                <Wallet size={32} className="text-gray-600" />
              </div>
              <p className="font-medium">No assets found</p>
              <p className="text-xs text-gray-600 mt-1">Deposit assets to get started</p>
            </div>
          )}
        </div>
      </div>

      {/* Network Balances */}
      <div className="p-6 rounded-3xl border border-[#2a3441] bg-gradient-to-br from-[#1a1f2e] to-[#0d1117] backdrop-blur-xl">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            Native Token Balances
            <Globe size={18} className="text-[#2dd4bf]" />
          </h2>
          <div className="relative">
            <button 
              onClick={() => setShowNetworkDropdown(!showNetworkDropdown)}
              className="flex items-center gap-3 px-5 py-3 rounded-2xl bg-[#0d1117] border border-[#2a3441] hover:border-[#2dd4bf]/50 transition-all"
            >
              <span className="text-white font-medium">
                {selectedNetwork === 'all' ? 'All Networks' : networks.find(n => n.id === parseInt(selectedNetwork))?.name}
              </span>
              <ChevronDown size={16} className={`text-gray-400 transition-transform ${showNetworkDropdown ? 'rotate-180' : ''}`} />
            </button>
            {showNetworkDropdown && (
              <>
                <div className="fixed inset-0 z-40" onClick={() => setShowNetworkDropdown(false)} />
                <div className="absolute top-full right-0 mt-2 w-56 bg-gradient-to-b from-[#1a1f2e] to-[#0d1117] border border-[#2a3441] rounded-2xl py-2 z-50 shadow-2xl animate-scale-in">
                  <button 
                    onClick={() => { setSelectedNetwork('all'); setShowNetworkDropdown(false); }}
                    className="w-full px-4 py-3 text-left text-sm text-gray-300 hover:bg-[#2a3441]/50 transition-colors"
                  >
                    All Networks
                  </button>
                  {networks.map((n, index) => (
                    <button 
                      key={n.id} 
                      onClick={() => { setSelectedNetwork(n.id.toString()); setShowNetworkDropdown(false); }}
                      style={{ animationDelay: `${index * 30}ms` }}
                      className="w-full px-4 py-3 text-left text-sm text-gray-300 hover:bg-[#2a3441]/50 transition-colors flex items-center gap-3 animate-slide-in-up"
                    >
                      <span className="text-xl">{n.icon}</span> 
                      <span>{n.name}</span>
                    </button>
                  ))}
                </div>
              </>
            )}
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center h-48">
            <RefreshCw size={32} className="text-[#2dd4bf] animate-spin" />
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {networkBalances
              .filter(n => selectedNetwork === 'all' || n.id === parseInt(selectedNetwork))
              .map((network, index) => (
                <div 
                  key={network.id} 
                  style={{ animationDelay: `${index * 50}ms` }}
                  className={`p-5 rounded-2xl border transition-all duration-300 animate-slide-in-up hover:shadow-xl ${
                    network.balance > 0 
                      ? 'border-[#2dd4bf]/30 bg-gradient-to-br from-[#2dd4bf]/10 to-[#06b6d4]/5 hover:shadow-[#2dd4bf]/10' 
                      : 'border-[#2a3441] bg-[#0d1117]/80 hover:border-[#2a3441]'
                  }`}
                >
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <span className="text-3xl">{network.icon}</span>
                      <div>
                        <p className="font-semibold text-white">{network.name}</p>
                        <p className="text-xs text-gray-500">{network.symbol}</p>
                      </div>
                    </div>
                    <a 
                      href={`${network.explorer}/address/${address}`} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="p-2 rounded-xl hover:bg-[#2a3441] transition-colors"
                    >
                      <ExternalLink size={16} className="text-gray-500 hover:text-[#2dd4bf]" />
                    </a>
                  </div>
                  <div className="space-y-1">
                    <p className="text-2xl font-bold text-white">
                      {network.balance.toFixed(4)} <span className="text-sm text-gray-400">{network.symbol}</span>
                    </p>
                    <p className={`text-sm font-medium ${network.usdValue > 0 ? 'text-[#2dd4bf]' : 'text-gray-500'}`}>
                      ${network.usdValue.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                    </p>
                  </div>
                  {chain?.id === network.id && (
                    <div className="mt-3 px-3 py-1.5 rounded-lg bg-[#2dd4bf]/20 text-[#2dd4bf] text-xs font-semibold inline-flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-[#2dd4bf] animate-pulse" />
                      Connected
                    </div>
                  )}
                </div>
              ))}
          </div>
        )}
      </div>

      {/* ERC-20 Token Balances on Current Network */}
      {chain?.id && commonTokens[chain.id] && (
        <div className="p-6 rounded-3xl border border-[#2a3441] bg-gradient-to-br from-[#1a1f2e] to-[#0d1117] backdrop-blur-xl">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                ERC-20 Token Balances
                <Coins size={18} className="text-yellow-400" />
              </h2>
              <p className="text-sm text-gray-500 mt-1">
                On {networks.find(n => n.id === chain.id)?.name || 'current network'}
              </p>
            </div>
            <div className="flex items-center gap-2 px-4 py-2 bg-gray-800 rounded-lg">
              <span className="text-xl">{networks.find(n => n.id === chain.id)?.icon}</span>
              <span className="text-sm text-gray-400">{networks.find(n => n.id === chain.id)?.name}</span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {commonTokens[chain.id].map((token, index) => {
              // Simulated balance - in production, use useContractRead to fetch real balance
              const balance = 0; // Replace with actual contract read
              const usdValue = balance * (prices[token.symbol] || 0);
              
              return (
                <div 
                  key={token.address}
                  style={{ animationDelay: `${index * 50}ms` }}
                  className={`p-5 rounded-2xl border transition-all duration-300 animate-slide-in-up hover:shadow-xl ${
                    balance > 0 
                      ? 'border-yellow-500/30 bg-gradient-to-br from-yellow-500/10 to-orange-500/5 hover:shadow-yellow-500/10' 
                      : 'border-[#2a3441] bg-[#0d1117]/80 hover:border-[#2a3441]'
                  }`}
                >
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-yellow-400 to-orange-500 flex items-center justify-center text-sm font-bold text-black">
                        {token.symbol.slice(0, 2)}
                      </div>
                      <div>
                        <p className="font-semibold text-white">{token.symbol}</p>
                        <p className="text-xs text-gray-500">{token.name}</p>
                      </div>
                    </div>
                    <a 
                      href={`${networks.find(n => n.id === chain.id)?.explorer}/token/${token.address}?a=${address}`} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="p-2 rounded-xl hover:bg-[#2a3441] transition-colors"
                    >
                      <ExternalLink size={16} className="text-gray-500 hover:text-yellow-400" />
                    </a>
                  </div>
                  <div className="space-y-1">
                    <p className="text-2xl font-bold text-white">
                      {balance.toFixed(4)} <span className="text-sm text-gray-400">{token.symbol}</span>
                    </p>
                    <p className={`text-sm font-medium ${usdValue > 0 ? 'text-yellow-400' : 'text-gray-500'}`}>
                      ${usdValue.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                    </p>
                  </div>
                  {balance === 0 && (
                    <p className="text-xs text-gray-600 mt-3">No balance</p>
                  )}
                </div>
              );
            })}
          </div>

          <div className="mt-6 p-4 bg-gray-800/50 rounded-xl border border-gray-700">
            <p className="text-sm text-gray-400 flex items-center gap-2">
              <Sparkles size={14} className="text-yellow-400" />
              <span>Connect your wallet and switch to this network to see your token balances</span>
            </p>
          </div>
        </div>
      )}

      {/* AI Trading Signals */}
      <AISignalsPanel tokens={['BTC', 'ETH', 'SOL', 'ARB', 'MATIC']} />

      {/* Wallet Address */}
      <div className="p-5 rounded-2xl border border-[#2a3441] bg-gradient-to-br from-[#1a1f2e] to-[#0d1117] flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="p-3 rounded-xl bg-[#2dd4bf]/20">
            <Wallet size={22} className="text-[#2dd4bf]" />
          </div>
          <div>
            <p className="text-sm text-gray-400 font-medium">Connected Address</p>
            <p className="font-mono text-white text-lg">{address}</p>
          </div>
        </div>
        <button 
          onClick={copyAddress}
          className={`px-5 py-3 rounded-xl border text-sm font-medium transition-all flex items-center gap-2 ${
            copied 
              ? 'bg-[#2dd4bf]/20 border-[#2dd4bf]/50 text-[#2dd4bf]' 
              : 'bg-[#0d1117] border-[#2a3441] text-gray-400 hover:text-white hover:border-[#2dd4bf]/50'
          }`}
        >
          {copied ? <Check size={16} /> : <Copy size={16} />}
          {copied ? 'Copied!' : 'Copy'}
        </button>
      </div>

      {/* CSS Animations */}
      <style>{`
        @keyframes fade-in {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes scale-in {
          from { opacity: 0; transform: scale(0.95); }
          to { opacity: 1; transform: scale(1); }
        }
        @keyframes slide-in-up {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fade-in { animation: fade-in 0.3s ease-out; }
        .animate-scale-in { animation: scale-in 0.3s ease-out; }
        .animate-slide-in-up { animation: slide-in-up 0.4s ease-out both; }
      `}</style>

      {/* Autonomous Trading Portfolio Section */}
      <div className="space-y-6 mt-8">
        <h2 className="text-2xl font-bold text-white flex items-center gap-3">
          <Zap className="text-green-500" />
          Autonomous Trading Portfolio
        </h2>
        
        {/* Performance Metrics */}
        <PerformanceMetrics walletAddress={DEMO_WALLET} />
        
        {/* Portfolio Holdings */}
        <PortfolioHoldings walletAddress={DEMO_WALLET} />
        
        {/* Trade History */}
        <TradeHistoryTable walletAddress={DEMO_WALLET} />
      </div>
    </div>
  );
};

export default PortfolioPage;
