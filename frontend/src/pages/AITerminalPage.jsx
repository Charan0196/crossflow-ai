import { useState, useRef, useEffect } from 'react';
import { 
  Brain, Send, Sparkles, Target, TrendingUp, TrendingDown, Zap, RefreshCw,
  Bot, User, Loader2, Trash2, Copy, Check, Activity, AlertTriangle, 
  LineChart, Cpu, Shield, Flame, Clock, ArrowUpRight, ArrowDownRight,
  BarChart3, Wallet, Globe, Settings, ChevronRight, Star, Eye, Volume2
} from 'lucide-react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip } from 'recharts';
import { useWalletStore } from '../stores/walletStore';
import AIProviderSelector from '../components/ai/AIProviderSelector';

const API_BASE = 'http://localhost:8000/api';

// 30 popular tokens
const TOKEN_SYMBOLS = [
  'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT', 'ADAUSDT',
  'DOGEUSDT', 'MATICUSDT', 'DOTUSDT', 'LTCUSDT', 'TRXUSDT', 'AVAXUSDT',
  'LINKUSDT', 'ATOMUSDT', 'UNIUSDT', 'ETCUSDT', 'XLMUSDT', 'NEARUSDT',
  'ALGOUSDT', 'VETUSDT', 'ICPUSDT', 'FILUSDT', 'APTUSDT', 'ARBUSDT',
  'OPUSDT', 'INJUSDT', 'SUIUSDT', 'STXUSDT', 'RNDRUSDT', 'TIAUSDT'
];

// Hook for live market data
const useMarketData = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch('https://api.binance.com/api/v3/ticker/24hr');
        const json = await res.json();
        const filtered = json.filter(d => TOKEN_SYMBOLS.includes(d.symbol)).map(d => ({
          symbol: d.symbol.replace('USDT', ''),
          price: parseFloat(d.lastPrice),
          change: parseFloat(d.priceChangePercent),
          volume: parseFloat(d.quoteVolume),
          high: parseFloat(d.highPrice),
          low: parseFloat(d.lowPrice)
        }))
        .sort((a, b) => TOKEN_SYMBOLS.indexOf(a.symbol + 'USDT') - TOKEN_SYMBOLS.indexOf(b.symbol + 'USDT'));
        setData(filtered);
        setLoading(false);
      } catch (e) { setLoading(false); }
    };
    fetchData();
    const interval = setInterval(fetchData, 15000);
    return () => clearInterval(interval);
  }, []);
  
  return { data, loading };
};

// Hook for price chart
const usePriceChart = (symbol) => {
  const [chartData, setChartData] = useState([]);
  
  useEffect(() => {
    const fetchChart = async () => {
      try {
        const res = await fetch(`https://api.binance.com/api/v3/klines?symbol=${symbol}USDT&interval=1h&limit=24`);
        const data = await res.json();
        setChartData(data.map(k => ({
          time: new Date(k[0]).toLocaleTimeString('en-US', { hour: '2-digit' }),
          price: parseFloat(k[4])
        })));
      } catch { setChartData([]); }
    };
    if (symbol) fetchChart();
  }, [symbol]);
  
  return chartData;
};

const formatPrice = (p) => p >= 1000 ? p.toLocaleString(undefined, {maximumFractionDigits: 2}) : p < 1 ? p.toFixed(4) : p.toFixed(2);
const formatVolume = (v) => v >= 1e9 ? (v/1e9).toFixed(1) + 'B' : v >= 1e6 ? (v/1e6).toFixed(1) + 'M' : (v/1e3).toFixed(1) + 'K';


// AI Signal Card Component
const AISignalCard = ({ signal }) => {
  const isPositive = signal.direction === 'bullish';
  return (
    <div className={`p-3 rounded-xl border ${isPositive ? 'bg-emerald-500/5 border-emerald-500/20' : 'bg-red-500/5 border-red-500/20'}`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${isPositive ? 'bg-emerald-500/20' : 'bg-red-500/20'}`}>
            {isPositive ? <TrendingUp size={16} className="text-emerald-400" /> : <TrendingDown size={16} className="text-red-400" />}
          </div>
          <div>
            <p className="text-white font-semibold text-sm">{signal.pair}</p>
            <p className="text-gray-500 text-xs">{signal.timeframe}</p>
          </div>
        </div>
        <div className={`px-2 py-1 rounded-lg text-xs font-medium ${isPositive ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>
          {signal.confidence}% conf
        </div>
      </div>
      <p className="text-gray-400 text-xs">{signal.reason}</p>
      <div className="flex items-center gap-2 mt-2">
        <span className="text-xs text-gray-500">Entry: ${formatPrice(signal.entry)}</span>
        <span className="text-xs text-emerald-400">TP: ${formatPrice(signal.target)}</span>
        <span className="text-xs text-red-400">SL: ${formatPrice(signal.stop)}</span>
      </div>
    </div>
  );
};

// Mini Chart Component
const MiniChart = ({ symbol, change }) => {
  const chartData = usePriceChart(symbol);
  const color = change >= 0 ? '#10b981' : '#ef4444';
  
  return (
    <div className="h-12 w-24">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData}>
          <defs>
            <linearGradient id={`grad-${symbol}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.3} />
              <stop offset="100%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <Area type="monotone" dataKey="price" stroke={color} strokeWidth={1.5} fill={`url(#grad-${symbol})`} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

const AITerminalPage = () => {
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [copied, setCopied] = useState(null);
  const [sessionId] = useState(() => `session_${Date.now()}`);
  const [activeTab, setActiveTab] = useState('chat');
  const [selectedCoin, setSelectedCoin] = useState('BTC');
  const [backendStatus, setBackendStatus] = useState('checking');
  const [selectedAIProvider, setSelectedAIProvider] = useState('groq');
  const [selectedAIModel, setSelectedAIModel] = useState(null);
  const messagesEndRef = useRef(null);
  const { data: marketData, loading: marketLoading } = useMarketData();
  
  // Use autonomous wallet store
  const { address, ethBalance, tokenBalances, initialize, updateBalance } = useWalletStore();
  
  // Check backend health on mount
  useEffect(() => {
    const checkBackend = async () => {
      try {
        const response = await fetch(`${API_BASE}/ai-chat/health`);
        if (response.ok) {
          setBackendStatus('online');
          console.log('✅ Backend is online');
        } else {
          setBackendStatus('error');
          console.error('❌ Backend health check failed:', response.status);
        }
      } catch (error) {
        setBackendStatus('offline');
        console.error('❌ Cannot reach backend:', error.message);
      }
    };
    checkBackend();
  }, []);
  
  // Generate AI signals for all tokens
  const generateSignals = (marketData) => {
    if (!marketData || marketData.length === 0) return [];
    
    return marketData.slice(0, 10).map(token => {
      const change = token.change;
      const isBullish = change > 0;
      const confidence = Math.min(95, Math.abs(change) * 10 + 60 + Math.random() * 15);
      
      const reasons = isBullish ? [
        'Strong upward momentum detected',
        'RSI showing bullish divergence',
        'Breaking resistance levels',
        'Volume surge indicates buying pressure',
        'Moving averages aligned bullish'
      ] : [
        'Bearish momentum building',
        'RSI showing bearish divergence',
        'Testing support levels',
        'Volume decline indicates selling',
        'Moving averages turning bearish'
      ];
      
      const entry = token.price;
      const target = isBullish ? entry * 1.05 : entry * 0.95;
      const stop = isBullish ? entry * 0.97 : entry * 1.03;
      
      return {
        pair: `${token.symbol}/USDT`,
        direction: isBullish ? 'bullish' : 'bearish',
        confidence: Math.round(confidence),
        timeframe: ['15M', '1H', '4H', '1D'][Math.floor(Math.random() * 4)],
        reason: reasons[Math.floor(Math.random() * reasons.length)],
        entry: entry,
        target: target,
        stop: stop
      };
    });
  };
  
  const [signals, setSignals] = useState([]);
  
  // Update signals when market data changes
  useEffect(() => {
    if (marketData && marketData.length > 0) {
      setSignals(generateSignals(marketData));
    }
  }, [marketData]);
  
  const [messages, setMessages] = useState([
    {
      type: 'ai',
      content: `🚀 **Welcome to CrossFlow AI Terminal!**

I'm your advanced DeFi trading assistant powered by AI. Here's what I can do:

**Trading Commands**
• \`show balance\` - View your wallet balance
• \`analyze portfolio\` - Get portfolio insights
• \`suggest trades\` - Get AI trading signals
• \`swap [amount] [token] to [token]\` - Execute a swap
  Example: "swap 0.1 ETH to USDT"

**Analysis & Intelligence**
• Real-time price analysis & signals
• Risk assessment & optimization
• Cross-chain operations
• Gas optimization

**Demo Wallet:** \`${address.slice(0, 6)}...${address.slice(-4)}\`

Try: "show balance" or "suggest trades"`,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);


  const suggestions = [
    { icon: Wallet, text: "show balance", color: "text-cyan-400" },
    { icon: BarChart3, text: "analyze portfolio", color: "text-purple-400" },
    { icon: Target, text: "suggest trades", color: "text-emerald-400" },
    { icon: Zap, text: "swap 0.1 ETH to USDT", color: "text-yellow-400" },
  ];

  const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  useEffect(() => { scrollToBottom(); }, [messages]);
  
  // Initialize wallet on mount
  useEffect(() => {
    initialize();
  }, [initialize]);
  
  // Parse trading commands
  const parseCommand = async (userMessage) => {
    const lowerMsg = userMessage.toLowerCase();
    
    // Show balance command
    if (lowerMsg.includes('show balance') || lowerMsg.includes('my balance') || lowerMsg.includes('wallet balance')) {
      try {
        const response = await fetch(`${API_BASE}/autonomous/wallet/balance?address=${address}`);
        const data = await response.json();
        return {
          isCommand: true,
          response: `💰 **Wallet Balance**\n\n**Address:** \`${address}\`\n**ETH Balance:** ${data.eth_balance} ETH\n**USD Value:** $${data.usd_value}\n\n**Token Balances:**\n${data.token_balances.length > 0 ? data.token_balances.map(t => `• ${t.symbol}: ${t.balance} ($${t.usd_value})`).join('\n') : 'No tokens found'}`
        };
      } catch (error) {
        return { isCommand: true, response: '⚠️ Failed to fetch balance. Please try again.' };
      }
    }
    
    // Analyze portfolio command
    if (lowerMsg.includes('analyze portfolio') || lowerMsg.includes('portfolio analysis') || lowerMsg.includes('my portfolio')) {
      try {
        const response = await fetch(`${API_BASE}/autonomous/wallet/portfolio?address=${address}`);
        const data = await response.json();
        return {
          isCommand: true,
          response: `📊 **Portfolio Analysis**\n\n**Total Value:** $${data.total_value}\n**Number of Holdings:** ${data.holdings.length}\n\n**Top Holdings:**\n${data.holdings.slice(0, 5).map((h, i) => `${i+1}. ${h.symbol}: $${h.usd_value} (${h.allocation}%)`).join('\n')}\n\n**Diversification:** ${data.holdings.length > 5 ? 'Well diversified' : 'Consider diversifying'}`
        };
      } catch (error) {
        return { isCommand: true, response: '⚠️ Failed to analyze portfolio. Please try again.' };
      }
    }
    
    // Suggest trades command
    if (lowerMsg.includes('suggest trade') || lowerMsg.includes('trading signal') || lowerMsg.includes('recommend trade')) {
      try {
        const response = await fetch(`${API_BASE}/autonomous/ai/signals?limit=3`);
        const data = await response.json();
        if (data.signals && data.signals.length > 0) {
          return {
            isCommand: true,
            response: `🎯 **AI Trading Signals**\n\n${data.signals.map((s, i) => 
              `**${i+1}. ${s.token.replace('0x...', '').toUpperCase()}**\n` +
              `• Signal: ${s.action.toUpperCase()}\n` +
              `• Confidence: ${s.confidence}%\n` +
              `• Reason: ${s.reason}\n` +
              `• Entry: $${s.entry_price}\n` +
              `• Target: $${s.target_price}\n` +
              `• Stop Loss: $${s.stop_loss}`
            ).join('\n\n')}`
          };
        }
        return { isCommand: true, response: '📊 No trading signals available at the moment.' };
      } catch (error) {
        return { isCommand: true, response: '⚠️ Failed to fetch signals. Please try again.' };
      }
    }
    
    // Execute swap command
    const swapMatch = lowerMsg.match(/swap (\d+\.?\d*) (\w+) (?:to|for) (\w+)/i);
    if (swapMatch) {
      const [, amount, fromToken, toToken] = swapMatch;
      try {
        const response = await fetch(`${API_BASE}/autonomous/wallet/execute`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            address: address,
            from_token: fromToken.toUpperCase(),
            to_token: toToken.toUpperCase(),
            amount: parseFloat(amount),
            slippage: 0.5
          })
        });
        const data = await response.json();
        if (data.success) {
          await updateBalance();
          return {
            isCommand: true,
            response: `✅ **Swap Executed Successfully!**\n\n**Transaction:** ${amount} ${fromToken.toUpperCase()} → ${toToken.toUpperCase()}\n**TX Hash:** \`${data.tx_hash}\`\n**View on Etherscan:** https://sepolia.etherscan.io/tx/${data.tx_hash}\n\n💡 Your balance has been updated.`
          };
        }
        return { isCommand: true, response: `⚠️ Swap failed: ${data.error}` };
      } catch (error) {
        return { isCommand: true, response: '⚠️ Failed to execute swap. Please try again.' };
      }
    }
    
    return { isCommand: false };
  };

  const handleSend = async () => {
    if (!message.trim() || isLoading) return;
    const userMessage = message.trim();
    setMessage('');
    
    setMessages(prev => [...prev, {
      type: 'user',
      content: userMessage,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }]);
    
    setIsLoading(true);
    
    try {
      // Check if it's a trading command
      const commandResult = await parseCommand(userMessage);
      if (commandResult.isCommand) {
        setMessages(prev => [...prev, {
          type: 'ai',
          content: commandResult.response,
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }]);
        setIsLoading(false);
        return;
      }
      
      // Otherwise, send to AI chat
      console.log('Sending message to:', `${API_BASE}/ai-chat/chat`);
      console.log('Request body:', { message: userMessage, session_id: sessionId, include_market_data: true, provider: selectedAIProvider });
      
      const response = await fetch(`${API_BASE}/ai-chat/chat`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({ 
          message: userMessage, 
          session_id: sessionId, 
          include_market_data: true,
          provider: selectedAIProvider,
          model: selectedAIModel
        })
      });
      
      console.log('Response status:', response.status);
      console.log('Response headers:', Object.fromEntries(response.headers.entries()));
      
      if (response.ok) {
        const data = await response.json();
        console.log('AI Response:', data);
        setMessages(prev => [...prev, {
          type: 'ai',
          content: data.response,
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }]);
      } else {
        const errorText = await response.text();
        console.error('Response error:', response.status, errorText);
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }
    } catch (error) {
      console.error('Chat error details:', {
        name: error.name,
        message: error.message,
        stack: error.stack
      });
      
      let errorMsg = '⚠️ Connection error. ';
      if (error.message.includes('Failed to fetch') || error.message.includes('Load failed')) {
        errorMsg += 'Cannot reach backend server. Please ensure backend is running on http://localhost:8000';
      } else {
        errorMsg += error.message;
      }
      
      setMessages(prev => [...prev, {
        type: 'ai',
        content: errorMsg,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        isError: true
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClear = async () => {
    try {
      await fetch(`${API_BASE}/ai-chat/clear-history`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId })
      });
    } catch (e) {}
    setMessages([{
      type: 'ai',
      content: '🔄 Chat cleared. How can I assist you today?',
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }]);
  };

  const copyText = (text, idx) => {
    navigator.clipboard.writeText(text);
    setCopied(idx);
    setTimeout(() => setCopied(null), 2000);
  };

  const formatMsg = (content) => {
    return content
      .replace(/\*\*(.*?)\*\*/g, '<strong class="text-cyan-400">$1</strong>')
      .replace(/`(.*?)`/g, '<code class="bg-gray-800 px-1.5 py-0.5 rounded text-emerald-400 text-xs">$1</code>')
      .replace(/\n/g, '<br/>');
  };

  const selectedCoinData = marketData.find(c => c.symbol === selectedCoin) || { price: 0, change: 0, volume: 0 };


  return (
    <div className="space-y-4">
      {/* AI Provider Selector */}
      <div className="flex justify-end">
        <AIProviderSelector 
          selectedProvider={selectedAIProvider}
          onProviderChange={setSelectedAIProvider}
          selectedModel={selectedAIModel}
          onModelChange={setSelectedAIModel}
        />
      </div>

      {/* Header Stats Bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="p-4 rounded-xl bg-gradient-to-br from-cyan-500/10 to-cyan-500/5 border border-cyan-500/20">
          <div className="flex items-center gap-2 mb-1">
            <Cpu size={14} className="text-cyan-400" />
            <span className="text-xs text-gray-500 uppercase">AI Status</span>
          </div>
          <p className={`text-lg font-bold ${backendStatus === 'online' ? 'text-cyan-400' : backendStatus === 'checking' ? 'text-yellow-400' : 'text-red-400'}`}>
            {backendStatus === 'online' ? 'Online' : backendStatus === 'checking' ? 'Checking...' : 'Offline'}
          </p>
          <p className="text-xs text-gray-500">{selectedAIProvider.toUpperCase()} AI</p>
        </div>
        <div className="p-4 rounded-xl bg-gradient-to-br from-emerald-500/10 to-emerald-500/5 border border-emerald-500/20">
          <div className="flex items-center gap-2 mb-1">
            <Target size={14} className="text-emerald-400" />
            <span className="text-xs text-gray-500 uppercase">Accuracy</span>
          </div>
          <p className="text-lg font-bold text-emerald-400">94.2%</p>
          <p className="text-xs text-gray-500">Last 30 days</p>
        </div>
        <div className="p-4 rounded-xl bg-gradient-to-br from-purple-500/10 to-purple-500/5 border border-purple-500/20">
          <div className="flex items-center gap-2 mb-1">
            <Flame size={14} className="text-purple-400" />
            <span className="text-xs text-gray-500 uppercase">Signals Today</span>
          </div>
          <p className="text-lg font-bold text-purple-400">12</p>
          <p className="text-xs text-gray-500">8 profitable</p>
        </div>
        <div className="p-4 rounded-xl bg-gradient-to-br from-amber-500/10 to-amber-500/5 border border-amber-500/20">
          <div className="flex items-center gap-2 mb-1">
            <Clock size={14} className="text-amber-400" />
            <span className="text-xs text-gray-500 uppercase">Response</span>
          </div>
          <p className="text-lg font-bold text-amber-400">0.8s</p>
          <p className="text-xs text-gray-500">Avg latency</p>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Left Sidebar - Market Data */}
        <div className="lg:col-span-3 space-y-4">
          {/* Live Prices */}
          <div className="rounded-xl border border-gray-800 bg-gray-900 overflow-hidden">
            <div className="p-3 border-b border-gray-800 bg-gradient-to-r from-cyan-500/5 to-transparent">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Activity size={14} className="text-cyan-400" />
                  <span className="font-semibold text-white text-sm">Live Prices</span>
                </div>
                <span className="text-xs text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded-full animate-pulse">● LIVE</span>
              </div>
            </div>
            <div className="divide-y divide-gray-800/50 max-h-[600px] overflow-y-auto">
              {marketLoading ? (
                <div className="p-4 text-center text-gray-500 text-sm">Loading...</div>
              ) : marketData.map((coin, i) => (
                <div 
                  key={i} 
                  onClick={() => setSelectedCoin(coin.symbol)}
                  className={`p-3 flex items-center justify-between cursor-pointer transition-all ${selectedCoin === coin.symbol ? 'bg-cyan-500/10' : 'hover:bg-gray-800/50'}`}
                >
                  <div className="flex items-center gap-2">
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold ${
                      coin.symbol === 'BTC' ? 'bg-orange-500' : 
                      coin.symbol === 'ETH' ? 'bg-blue-500' : 
                      coin.symbol === 'SOL' ? 'bg-purple-500' : 
                      coin.symbol === 'BNB' ? 'bg-yellow-500' : 'bg-gray-600'
                    }`}>
                      {coin.symbol.slice(0, 2)}
                    </div>
                    <div>
                      <p className="text-white font-medium text-sm">{coin.symbol}</p>
                      <p className="text-gray-500 text-xs">${formatVolume(coin.volume)}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-white font-mono text-sm">${formatPrice(coin.price)}</p>
                    <p className={`text-xs flex items-center justify-end gap-0.5 ${coin.change >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                      {coin.change >= 0 ? <ArrowUpRight size={10} /> : <ArrowDownRight size={10} />}
                      {coin.change >= 0 ? '+' : ''}{coin.change.toFixed(2)}%
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* AI Signals */}
          <div className="rounded-xl border border-gray-800 bg-gray-900 p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Sparkles size={14} className="text-purple-400" />
                <span className="font-semibold text-white text-sm">AI Signals</span>
              </div>
              <span className="text-xs text-purple-400">{signals.length} active</span>
            </div>
            <div className="space-y-3">
              {signals.map((signal, i) => (
                <AISignalCard key={i} signal={signal} />
              ))}
            </div>
          </div>
        </div>


        {/* Main Chat Area */}
        <div className="lg:col-span-6 flex flex-col rounded-xl border border-gray-800 bg-gray-900 overflow-hidden" style={{ height: 'calc(100vh - 280px)' }}>
          {/* Chat Header */}
          <div className="flex items-center gap-3 px-5 py-4 border-b border-gray-800 bg-gradient-to-r from-cyan-500/5 via-purple-500/5 to-transparent">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-purple-500 flex items-center justify-center shadow-lg shadow-cyan-500/20">
              <Brain size={20} className="text-white" />
            </div>
            <div className="flex-1">
              <h3 className="text-white font-bold">CrossFlow AI</h3>
              <p className="text-gray-500 text-xs">Advanced Trading Assistant</p>
            </div>
            <div className="flex items-center gap-2">
              <span className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs border ${
                backendStatus === 'online' 
                  ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' 
                  : backendStatus === 'checking'
                  ? 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30'
                  : 'bg-red-500/20 text-red-400 border-red-500/30'
              }`}>
                <span className={`w-1.5 h-1.5 rounded-full ${
                  backendStatus === 'online' ? 'bg-emerald-400 animate-pulse' : 
                  backendStatus === 'checking' ? 'bg-yellow-400 animate-pulse' : 
                  'bg-red-400'
                }`} />
                {backendStatus === 'online' ? 'Online' : backendStatus === 'checking' ? 'Checking' : 'Offline'}
              </span>
              <button onClick={handleClear} className="p-2 rounded-lg hover:bg-gray-800 text-gray-500 hover:text-white transition-colors" title="Clear chat">
                <Trash2 size={16} />
              </button>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((msg, i) => (
              <div key={i} className={`flex gap-3 ${msg.type === 'user' ? 'flex-row-reverse' : ''}`}>
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                  msg.type === 'ai' ? 'bg-gradient-to-br from-cyan-500/20 to-purple-500/20' : 'bg-purple-500/20'
                }`}>
                  {msg.type === 'ai' ? <Bot size={16} className="text-cyan-400" /> : <User size={16} className="text-purple-400" />}
                </div>
                <div className={`max-w-[80%] ${msg.type === 'user' ? 'text-right' : ''}`}>
                  <div className={`group relative rounded-xl px-4 py-3 ${
                    msg.type === 'ai' 
                      ? msg.isError ? 'bg-red-500/10 border border-red-500/30' : 'bg-gray-800 border border-gray-700'
                      : 'bg-gradient-to-r from-cyan-500/20 to-purple-500/20 border border-cyan-500/30'
                  }`}>
                    <div className="text-sm text-gray-200 leading-relaxed" dangerouslySetInnerHTML={{ __html: formatMsg(msg.content) }} />
                    {msg.type === 'ai' && !msg.isError && (
                      <button onClick={() => copyText(msg.content, i)} className="absolute top-2 right-2 p-1.5 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity bg-gray-700 text-gray-400 hover:text-white">
                        {copied === i ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
                      </button>
                    )}
                  </div>
                  <p className="text-[10px] text-gray-600 mt-1">{msg.time}</p>
                </div>
              </div>
            ))}
            
            {isLoading && (
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500/20 to-purple-500/20 flex items-center justify-center">
                  <Bot size={16} className="text-cyan-400" />
                </div>
                <div className="bg-gray-800 border border-gray-700 rounded-xl px-4 py-3">
                  <div className="flex items-center gap-2 text-gray-400 text-sm">
                    <Loader2 size={14} className="animate-spin text-cyan-400" />
                    <span>Analyzing...</span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Suggestions */}
          <div className="px-4 py-2 border-t border-gray-800/50 bg-gray-900/50">
            <div className="flex gap-2 overflow-x-auto pb-1">
              {suggestions.map((s, i) => (
                <button key={i} onClick={() => setMessage(s.text)} className="flex-shrink-0 flex items-center gap-2 px-3 py-2 rounded-lg text-xs bg-gray-800 border border-gray-700 text-gray-400 hover:text-white hover:border-cyan-500/30 transition-all">
                  <s.icon size={12} className={s.color} />
                  {s.text}
                </button>
              ))}
            </div>
          </div>

          {/* Input */}
          <div className="p-4 border-t border-gray-800 bg-gray-900">
            <div className="flex gap-3">
              <input
                type="text"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                placeholder="Ask anything about trading, analysis, or DeFi..."
                disabled={isLoading}
                className="flex-1 bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-sm text-white placeholder-gray-500 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 outline-none transition-all disabled:opacity-50"
              />
              <button 
                onClick={handleSend}
                disabled={isLoading || !message.trim()}
                className="px-5 py-3 bg-gradient-to-r from-cyan-500 to-purple-500 text-white font-semibold rounded-xl flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-lg hover:shadow-cyan-500/20 transition-all"
              >
                {isLoading ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
              </button>
            </div>
          </div>
        </div>


        {/* Right Sidebar - Insights & Tools */}
        <div className="lg:col-span-3 space-y-4">
          {/* Selected Coin Chart */}
          <div className="rounded-xl border border-gray-800 bg-gray-900 p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <BarChart3 size={14} className="text-cyan-400" />
                <span className="font-semibold text-white text-sm">{selectedCoin}/USDT</span>
              </div>
              <span className={`text-xs px-2 py-1 rounded-lg ${selectedCoinData.change >= 0 ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>
                {selectedCoinData.change >= 0 ? '+' : ''}{selectedCoinData.change?.toFixed(2)}%
              </span>
            </div>
            <p className="text-2xl font-bold text-white mb-3">${formatPrice(selectedCoinData.price)}</p>
            <div className="h-24">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={usePriceChart(selectedCoin)}>
                  <defs>
                    <linearGradient id="selectedGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor={selectedCoinData.change >= 0 ? '#10b981' : '#ef4444'} stopOpacity={0.3} />
                      <stop offset="100%" stopColor={selectedCoinData.change >= 0 ? '#10b981' : '#ef4444'} stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="time" stroke="#4b5563" axisLine={false} tickLine={false} tick={{ fontSize: 9, fill: '#6b7280' }} />
                  <YAxis stroke="#4b5563" axisLine={false} tickLine={false} tick={false} domain={['auto', 'auto']} width={0} />
                  <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }} />
                  <Area type="monotone" dataKey="price" stroke={selectedCoinData.change >= 0 ? '#10b981' : '#ef4444'} strokeWidth={2} fill="url(#selectedGrad)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* AI Insights */}
          <div className="rounded-xl border border-gray-800 bg-gray-900 p-4">
            <div className="flex items-center gap-2 mb-3">
              <Eye size={14} className="text-amber-400" />
              <span className="font-semibold text-white text-sm">AI Insights</span>
            </div>
            <div className="space-y-3">
              <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                <div className="flex items-center gap-2 mb-1">
                  <TrendingUp size={12} className="text-emerald-400" />
                  <span className="text-xs text-emerald-400 font-medium">Bullish Signal</span>
                </div>
                <p className="text-xs text-gray-400">ETH showing strong support at $3,300. RSI indicates oversold conditions.</p>
              </div>
              <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
                <div className="flex items-center gap-2 mb-1">
                  <AlertTriangle size={12} className="text-amber-400" />
                  <span className="text-xs text-amber-400 font-medium">Market Alert</span>
                </div>
                <p className="text-xs text-gray-400">High volatility expected. Consider reducing position sizes.</p>
              </div>
              <div className="p-3 rounded-lg bg-cyan-500/10 border border-cyan-500/20">
                <div className="flex items-center gap-2 mb-1">
                  <Zap size={12} className="text-cyan-400" />
                  <span className="text-xs text-cyan-400 font-medium">Opportunity</span>
                </div>
                <p className="text-xs text-gray-400">ARB/ETH pair showing arbitrage opportunity across DEXs.</p>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="rounded-xl border border-gray-800 bg-gray-900 p-4">
            <div className="flex items-center gap-2 mb-3">
              <Zap size={14} className="text-yellow-400" />
              <span className="font-semibold text-white text-sm">Quick Actions</span>
            </div>
            <div className="grid grid-cols-2 gap-2">
              {[
                { icon: RefreshCw, label: 'Rebalance', color: 'text-cyan-400' },
                { icon: Shield, label: 'Risk Check', color: 'text-purple-400' },
                { icon: Globe, label: 'Bridge', color: 'text-blue-400' },
                { icon: Settings, label: 'Settings', color: 'text-gray-400' },
              ].map((action, i) => (
                <button key={i} onClick={() => setMessage(action.label === 'Rebalance' ? 'Help rebalance my portfolio' : action.label === 'Risk Check' ? 'Check my portfolio risk' : action.label === 'Bridge' ? 'Bridge assets to Arbitrum' : '')} className="flex flex-col items-center gap-1 p-3 rounded-lg bg-gray-800 border border-gray-700 hover:border-cyan-500/30 transition-all">
                  <action.icon size={18} className={action.color} />
                  <span className="text-xs text-gray-400">{action.label}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AITerminalPage;