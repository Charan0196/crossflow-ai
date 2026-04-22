import { useState, useEffect, useRef } from 'react';
import { TrendingUp, TrendingDown, Search, Activity, BarChart3, Zap, ArrowLeftRight, Shield, ArrowDown, ChevronDown, Settings, Globe, Droplet, Wallet } from 'lucide-react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip } from 'recharts';
import { useAccount, useNetwork, useSwitchNetwork, usePublicClient, useWalletClient } from 'wagmi';
import { useWalletStore } from '../stores/walletStore';

// 30 popular tokens
const tokenSymbols = [
  'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT', 'ADAUSDT',
  'DOGEUSDT', 'MATICUSDT', 'DOTUSDT', 'LTCUSDT', 'TRXUSDT', 'AVAXUSDT',
  'LINKUSDT', 'ATOMUSDT', 'UNIUSDT', 'ETCUSDT', 'XLMUSDT', 'NEARUSDT',
  'ALGOUSDT', 'VETUSDT', 'ICPUSDT', 'FILUSDT', 'APTUSDT', 'ARBUSDT',
  'OPUSDT', 'INJUSDT', 'SUIUSDT', 'STXUSDT', 'RNDRUSDT', 'TIAUSDT'
];

// Supported networks
const networks = [
  { id: 1, name: 'Ethereum', symbol: 'ETH', icon: '⟠', color: '#627EEA' },
  { id: 137, name: 'Polygon', symbol: 'MATIC', icon: '⬡', color: '#8247E5' },
  { id: 42161, name: 'Arbitrum', symbol: 'ETH', icon: '🔵', color: '#28A0F0' },
  { id: 10, name: 'Optimism', symbol: 'ETH', icon: '🔴', color: '#FF0420' },
  { id: 56, name: 'BNB Chain', symbol: 'BNB', icon: '🟡', color: '#F3BA2F' },
  { id: 43114, name: 'Avalanche', symbol: 'AVAX', icon: '🔺', color: '#E84142' },
  { id: 8453, name: 'Base', symbol: 'ETH', icon: '🔵', color: '#0052FF' },
  { id: 11155111, name: 'Sepolia', symbol: 'ETH', icon: '🧪', color: '#CFB5F0' },
];

// Hook for market data
const useMarketData = () => {
  const [tokens, setTokens] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tokenCharts, setTokenCharts] = useState({});
  const wsRef = useRef(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const tickerRes = await fetch('https://api.binance.com/api/v3/ticker/24hr');
        const tickerData = await tickerRes.json();
        
        const filtered = tickerData
          .filter(t => tokenSymbols.includes(t.symbol))
          .map(t => ({
            symbol: t.symbol.replace('USDT', ''),
            price: parseFloat(t.lastPrice),
            change: parseFloat(t.priceChangePercent),
            volume: parseFloat(t.quoteVolume)
          }))
          .sort((a, b) => tokenSymbols.indexOf(a.symbol + 'USDT') - tokenSymbols.indexOf(b.symbol + 'USDT'));
        setTokens(filtered);

        // Fetch mini charts
        const chartPromises = tokenSymbols.map(async (symbol) => {
          try {
            const res = await fetch(`https://api.binance.com/api/v3/klines?symbol=${symbol}&interval=1h&limit=12`);
            const data = await res.json();
            return { symbol: symbol.replace('USDT', ''), data: data.map(k => parseFloat(k[4])) };
          } catch {
            return { symbol: symbol.replace('USDT', ''), data: [] };
          }
        });
        
        const charts = await Promise.all(chartPromises);
        const chartsMap = {};
        charts.forEach(c => { chartsMap[c.symbol] = c.data; });
        setTokenCharts(chartsMap);
        setLoading(false);
      } catch (e) {
        console.error('Market data error:', e);
        setLoading(false);
      }
    };

    fetchData();

    // WebSocket
    const streams = tokenSymbols.map(s => `${s.toLowerCase()}@ticker`).join('/');
    wsRef.current = new WebSocket(`wss://stream.binance.com:9443/ws/${streams}`);
    
    wsRef.current.onopen = () => console.log('Trading WebSocket connected');
    wsRef.current.onmessage = (e) => {
      const data = JSON.parse(e.data);
      const symbol = data.s.replace('USDT', '');
      setTokens(prev => prev.map(t => 
        t.symbol === symbol ? { ...t, price: parseFloat(data.c), change: parseFloat(data.P), volume: parseFloat(data.q) } : t
      ));
    };

    return () => wsRef.current?.close();
  }, []);

  return { tokens, loading, tokenCharts };
};

const formatPrice = (p) => p >= 1000 ? `${p.toLocaleString(undefined, {maximumFractionDigits: 2})}` : `${p.toFixed(2)}`;

// Helper function to get block explorer URL
const getExplorerUrl = (chainId) => {
  const explorers = {
    1: 'https://etherscan.io',
    11155111: 'https://sepolia.etherscan.io',
    137: 'https://polygonscan.com',
    42161: 'https://arbiscan.io',
    10: 'https://optimistic.etherscan.io',
    8453: 'https://basescan.org',
    56: 'https://bscscan.com',
    43114: 'https://snowtrace.io',
  };
  return explorers[chainId] || 'https://etherscan.io';
};

// Mini chart component
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
      <polyline points={points} fill="none" stroke={change >= 0 ? '#10b981' : '#ef4444'} strokeWidth="1.5" />
    </svg>
  );
};

const TradingPage = () => {
  const { tokens, tokenCharts } = useMarketData();
  const { address: connectedAddress, isConnected: walletConnected } = useAccount();
  const { chain } = useNetwork();
  const { switchNetwork } = useSwitchNetwork();
  const publicClient = usePublicClient();
  const { data: walletClient } = useWalletClient();
  
  // Use autonomous wallet store
  const { 
    address, 
    ethBalance, 
    tokenBalances, 
    isConnected, 
    initialize, 
    updateBalance, 
    useConnectedWallet, 
    setUseConnectedWallet 
  } = useWalletStore();
  
  // Automatically use connected wallet when available
  useEffect(() => {
    if (walletConnected && connectedAddress) {
      console.log('Connected wallet detected, switching from demo mode');
      setUseConnectedWallet(true, connectedAddress);
      initialize(connectedAddress);
    } else if (!walletConnected) {
      console.log('No wallet connected, using demo mode');
      setUseConnectedWallet(false);
      initialize();
    }
  }, [walletConnected, connectedAddress, setUseConnectedWallet, initialize]);
  
  const [selectedToken, setSelectedToken] = useState('ETH');
  const [chartData, setChartData] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  
  // Swap state
  const [fromToken, setFromToken] = useState({ symbol: 'ETH', name: 'Ethereum' });
  const [toToken, setToToken] = useState({ symbol: 'USDT', name: 'Tether USD' });
  const [fromAmount, setFromAmount] = useState('');
  const [toAmount, setToAmount] = useState('');
  const [slippage] = useState('0.5');
  const [showFromTokens, setShowFromTokens] = useState(false);
  const [showToTokens, setShowToTokens] = useState(false);
  const [showNetworks, setShowNetworks] = useState(false);
  const [swapping, setSwapping] = useState(false);
  const [txHash, setTxHash] = useState('');
  const [txStatus, setTxStatus] = useState(''); // 'pending', 'success', 'failed'
  const [error, setError] = useState('');
  const [requestingFaucet, setRequestingFaucet] = useState(false);
  const [faucetMessage, setFaucetMessage] = useState('');
  
  // Wallet selection for swap - automatically use connected wallet when available
  const [selectedWallet, setSelectedWallet] = useState('autonomous'); // Will be updated based on connection
  const [showWalletSelector, setShowWalletSelector] = useState(false);
  
  // Auto-select connected wallet when available
  useEffect(() => {
    if (walletConnected && connectedAddress) {
      setSelectedWallet('connected'); // Default to real transactions when wallet is connected
    } else {
      setSelectedWallet('autonomous'); // Fall back to demo mode
    }
  }, [walletConnected, connectedAddress]);
  
  // Real swap state
  const [swapQuote, setSwapQuote] = useState(null);
  const [fetchingQuote, setFetchingQuote] = useState(false);
  
  // Initialize wallet on mount
  useEffect(() => {
    initialize();
  }, [initialize]);

  // Fetch chart for selected token
  useEffect(() => {
    const fetchChart = async () => {
      if (!selectedToken) return;
      try {
        const res = await fetch(`https://api.binance.com/api/v3/klines?symbol=${selectedToken}USDT&interval=1h&limit=24`);
        const data = await res.json();
        setChartData(data.map(k => ({
          time: new Date(k[0]).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
          price: parseFloat(k[4])
        })));
      } catch (e) {
        console.error('Chart error:', e);
      }
    };
    fetchChart();
  }, [selectedToken]);

  // Calculate swap output with simple calculation
  useEffect(() => {
    if (fromAmount && fromToken && toToken) {
      setFetchingQuote(true);
      
      // Simple calculation based on market prices
      const fromPrice = tokens.find(t => t.symbol === fromToken.symbol)?.price || 0;
      const toPrice = tokens.find(t => t.symbol === toToken.symbol)?.price || 1;
      const output = (parseFloat(fromAmount) * fromPrice) / toPrice;
      
      // Simulate quote fetching delay
      setTimeout(() => {
        setToAmount(output.toFixed(6));
        
        if (selectedWallet === 'connected') {
          setSwapQuote({
            inputAmount: parseFloat(fromAmount),
            outputAmount: output,
            rate: fromPrice / toPrice,
            priceImpact: 0.1,
            fee: parseFloat(fromAmount) * 0.003,
          });
        } else {
          setSwapQuote(null);
        }
        
        setFetchingQuote(false);
      }, 500);
    }
  }, [fromAmount, fromToken, toToken, tokens, selectedWallet]);

  const handleSwapTokens = () => {
    const temp = fromToken;
    setFromToken(toToken);
    setToToken(temp);
    setFromAmount(toAmount);
    setToAmount(fromAmount);
  };

  // Function to verify transaction status
  const verifyTransactionStatus = async (hash) => {
    if (!publicClient || !hash) return;
    
    try {
      console.log('Verifying transaction status for:', hash);
      const receipt = await publicClient.getTransactionReceipt({ hash });
      
      console.log('Transaction receipt:', receipt);
      
      if (receipt.status === 'success') {
        setTxStatus('success');
        console.log('✅ Transaction verified as successful');
      } else {
        setTxStatus('failed');
        console.log('❌ Transaction verified as failed');
      }
    } catch (error) {
      console.log('⏳ Transaction still pending or not found:', error.message);
      setTxStatus('pending');
    }
  };

  // Auto-verify transaction status when txHash changes
  useEffect(() => {
    if (txHash && selectedWallet === 'connected' && publicClient) {
      // Initial verification
      verifyTransactionStatus(txHash);
      
      // Set up polling to check status every 5 seconds
      const interval = setInterval(() => {
        if (txStatus !== 'success' && txStatus !== 'failed') {
          verifyTransactionStatus(txHash);
        } else {
          clearInterval(interval);
        }
      }, 5000);
      
      return () => clearInterval(interval);
    }
  }, [txHash, selectedWallet, publicClient, txStatus]);

  const handleSwap = async () => {
    console.log('=== SWAP STARTED ===');
    
    // Get the selected wallet address
    const swapWalletAddress = selectedWallet === 'connected' ? connectedAddress : address;
    
    // Debug logging
    console.log('Swap Debug Info:', {
      selectedWallet,
      connectedAddress,
      autonomousAddress: address,
      swapWalletAddress,
      fromAmount,
      fromToken: fromToken.symbol,
      toToken: toToken.symbol,
      hasWalletClient: !!walletClient,
      hasPublicClient: !!publicClient,
      chainId: chain?.id
    });
    
    if (!swapWalletAddress) {
      const errorMsg = selectedWallet === 'connected' 
        ? 'Please connect your MetaMask wallet first'
        : 'Autonomous wallet not available';
      setError(errorMsg);
      console.log('Error: No wallet address');
      return;
    }
    if (!fromAmount || parseFloat(fromAmount) <= 0) {
      setError('Please enter a valid amount');
      console.log('Error: Invalid amount');
      return;
    }
    
    console.log('Starting swap process...');
    setSwapping(true);
    setError('');
    setTxHash('');
    setTxStatus('');
    
    try {
      if (selectedWallet === 'connected' && connectedAddress) {
        console.log('Executing REAL swap for connected wallet');
        await handleRealSwap();
      } else {
        console.log('Executing MOCK swap for autonomous wallet');
        await handleMockSwap(swapWalletAddress);
      }
      console.log('=== SWAP COMPLETED SUCCESSFULLY ===');
    } catch (err) {
      console.error('=== SWAP FAILED ===', err);
      setTxStatus('failed');
      setError(err.message || 'Network error');
    } finally {
      console.log('=== SWAP PROCESS ENDED ===');
      setSwapping(false);
    }
  };

  const handleRealSwap = async () => {
    console.log('=== REAL SWAP STARTED ===');
    
    try {
      if (!walletClient || !publicClient || !chain?.id) {
        throw new Error('Wallet not properly connected')
      }

      console.log('Wallet and client available:', {
        hasWalletClient: !!walletClient,
        hasPublicClient: !!publicClient,
        chainId: chain?.id,
        connectedAddress
      });

      // Show user confirmation
      const confirmed = window.confirm(
        `Real Uniswap Swap:\n\n` +
        `From: ${fromAmount} ${fromToken.symbol}\n` +
        `To: ~${toAmount} ${toToken.symbol}\n` +
        `Network: ${currentNetwork.name}\n` +
        `Slippage: ${slippage}%\n` +
        `Estimated Gas: ~$5-15\n\n` +
        `This will execute a REAL swap on Uniswap V3.\n` +
        `Click OK to proceed with MetaMask.`
      );
      
      if (!confirmed) {
        throw new Error('Transaction cancelled by user');
      }
      
      console.log('User confirmed transaction, executing real Uniswap swap...');
      
      // Import viem functions
      const { parseEther, parseUnits, formatUnits } = await import('viem');
      
      // Uniswap V3 Router address (same on most networks)
      const UNISWAP_V3_ROUTER = '0xE592427A0AEce92De3Edee1F18E0157C05861564';
      
      // Token addresses for Sepolia testnet
      const TOKEN_ADDRESSES = {
        ETH: '0x0000000000000000000000000000000000000000', // Native ETH
        WETH: '0x7b79995e5f793A07Bc00c21412e50Ecae098E7f9',
        USDC: '0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238',
        USDT: '0x7169D38820dfd117C3FA1f22a697dBA58d90BA06',
        DAI: '0x3e622317f8C93f7328350cF0B56d9eD4C620C5d6'
      };
      
      // Get token addresses
      const fromTokenAddress = fromToken.symbol === 'ETH' ? TOKEN_ADDRESSES.WETH : TOKEN_ADDRESSES[fromToken.symbol];
      const toTokenAddress = toToken.symbol === 'ETH' ? TOKEN_ADDRESSES.WETH : TOKEN_ADDRESSES[toToken.symbol];
      
      if (!fromTokenAddress || !toTokenAddress) {
        throw new Error(`Token not supported: ${fromToken.symbol} or ${toToken.symbol}`);
      }
      
      console.log('Token addresses:', { fromTokenAddress, toTokenAddress });
      
      // Convert amount to proper units (assuming 18 decimals for simplicity)
      const amountIn = parseUnits(fromAmount.toString(), 18);
      const amountOutMin = parseUnits((parseFloat(toAmount) * (1 - parseFloat(slippage) / 100)).toString(), 18);
      
      console.log('Swap amounts:', {
        amountIn: amountIn.toString(),
        amountOutMin: amountOutMin.toString()
      });
      
      // Uniswap V3 Router ABI for exactInputSingle
      const UNISWAP_V3_ROUTER_ABI = [
        {
          name: 'exactInputSingle',
          type: 'function',
          stateMutability: 'payable',
          inputs: [
            {
              name: 'params',
              type: 'tuple',
              components: [
                { name: 'tokenIn', type: 'address' },
                { name: 'tokenOut', type: 'address' },
                { name: 'fee', type: 'uint24' },
                { name: 'recipient', type: 'address' },
                { name: 'deadline', type: 'uint256' },
                { name: 'amountIn', type: 'uint256' },
                { name: 'amountOutMinimum', type: 'uint256' },
                { name: 'sqrtPriceLimitX96', type: 'uint160' },
              ],
            },
          ],
          outputs: [{ name: 'amountOut', type: 'uint256' }],
        },
      ];
      
      // ERC-20 ABI for approval
      const ERC20_ABI = [
        {
          name: 'approve',
          type: 'function',
          stateMutability: 'nonpayable',
          inputs: [
            { name: 'spender', type: 'address' },
            { name: 'amount', type: 'uint256' },
          ],
          outputs: [{ name: '', type: 'bool' }],
        },
        {
          name: 'allowance',
          type: 'function',
          stateMutability: 'view',
          inputs: [
            { name: 'owner', type: 'address' },
            { name: 'spender', type: 'address' },
          ],
          outputs: [{ name: '', type: 'uint256' }],
        },
      ];
      
      // Step 1: Handle token approval (if not ETH)
      if (fromToken.symbol !== 'ETH') {
        console.log('Checking token allowance...');
        
        // Check current allowance
        const currentAllowance = await publicClient.readContract({
          address: fromTokenAddress,
          abi: ERC20_ABI,
          functionName: 'allowance',
          args: [connectedAddress, UNISWAP_V3_ROUTER],
        });
        
        console.log('Current allowance:', currentAllowance.toString());
        
        if (currentAllowance < amountIn) {
          console.log('Approval needed, requesting approval...');
          
          const approvalHash = await walletClient.writeContract({
            address: fromTokenAddress,
            abi: ERC20_ABI,
            functionName: 'approve',
            args: [UNISWAP_V3_ROUTER, amountIn],
          });
          
          console.log('Approval transaction sent:', approvalHash);
          
          // Wait for approval confirmation
          await publicClient.waitForTransactionReceipt({ 
            hash: approvalHash,
            timeout: 60000 
          });
          
          console.log('Token approval confirmed');
        } else {
          console.log('Sufficient allowance already exists');
        }
      }
      
      // Step 2: Execute the swap
      console.log('Executing Uniswap V3 swap...');
      
      const deadline = BigInt(Math.floor(Date.now() / 1000) + 1800); // 30 minutes
      const fee = 3000; // 0.3% fee tier
      
      const swapParams = {
        tokenIn: fromTokenAddress,
        tokenOut: toTokenAddress,
        fee,
        recipient: connectedAddress,
        deadline,
        amountIn,
        amountOutMinimum: amountOutMin,
        sqrtPriceLimitX96: 0n,
      };
      
      console.log('Swap parameters:', swapParams);
      
      const swapHash = await walletClient.writeContract({
        address: UNISWAP_V3_ROUTER,
        abi: UNISWAP_V3_ROUTER_ABI,
        functionName: 'exactInputSingle',
        args: [swapParams],
        value: fromToken.symbol === 'ETH' ? amountIn : 0n,
      });
      
      console.log('Swap transaction sent:', swapHash);
      setTxHash(swapHash);
      setTxStatus('pending');
      
      // Wait for swap confirmation
      const receipt = await publicClient.waitForTransactionReceipt({ 
        hash: swapHash,
        timeout: 120000 // 2 minutes timeout
      });
      
      console.log('Swap transaction confirmed:', receipt);
      
      // Check if transaction was successful
      if (receipt.status === 'success') {
        setTxStatus('success');
        setFromAmount('');
        setToAmount('');
        console.log('Real Uniswap swap completed successfully!');
      } else {
        setTxStatus('failed');
        throw new Error('Transaction failed on blockchain');
      }
      
    } catch (error) {
      console.error('Real swap error:', error);
      
      // Handle specific error types
      if (error.message.includes('User rejected') || error.message.includes('user rejected')) {
        throw new Error('Transaction was rejected in MetaMask');
      } else if (error.message.includes('insufficient funds')) {
        throw new Error('Insufficient funds for transaction');
      } else if (error.message.includes('cancelled')) {
        throw new Error('Transaction cancelled by user');
      } else if (error.message.includes('Token not supported')) {
        throw new Error(error.message);
      } else if (error.message.includes('slippage')) {
        throw new Error('Transaction failed due to slippage. Try increasing slippage tolerance.');
      } else {
        throw new Error(`Uniswap swap failed: ${error.message}`);
      }
    }
  };

  const handleMockSwap = async (walletAddress) => {
    console.log('=== MOCK SWAP STARTED ===');
    console.log('Wallet address:', walletAddress);
    console.log('From token:', fromToken.symbol);
    console.log('To token:', toToken.symbol);
    console.log('Amount:', fromAmount);
    
    try {
      // Execute mock swap using backend API (for autonomous wallet)
      const requestBody = {
        address: walletAddress,
        from_token: fromToken.symbol,
        to_token: toToken.symbol,
        amount: parseFloat(fromAmount),
        slippage: parseFloat(slippage)
      };
      
      console.log('Sending request to backend:', requestBody);
      
      const response = await fetch('http://localhost:8000/api/autonomous/wallet/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      });
      
      console.log('Mock Swap Response Status:', response.status);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('Mock Swap Response Data:', data);
      
      if (data.success) {
        setTxHash(data.tx_hash);
        setTxStatus('success');
        setFromAmount('');
        setToAmount('');
        // Update balance after successful swap
        if (updateBalance) {
          await updateBalance();
        }
        console.log('Mock swap completed successfully');
      } else {
        setTxStatus('failed');
        throw new Error(data.error || 'Swap failed');
      }
    } catch (error) {
      console.error('Mock swap error:', error);
      throw error;
    }
  };

  const handleRequestFaucet = async () => {
    if (!connectedAddress && !address) {
      setFaucetMessage('Please connect your wallet first');
      return;
    }
    
    setRequestingFaucet(true);
    setFaucetMessage('');
    
    try {
      const targetAddress = connectedAddress || address;
      const response = await fetch('http://localhost:8000/api/testnet-faucet/request', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          address: targetAddress,
          network: 'sepolia'
        })
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setFaucetMessage(`Success! ${data.amount} ETH sent to your wallet. TX: ${data.tx_hash?.slice(0, 10)}...`);
        // Update balance after receiving tokens
        if (updateBalance) await updateBalance();
      } else {
        setFaucetMessage(data.error || 'Faucet request failed');
      }
    } catch (err) {
      setFaucetMessage(err.message || 'Network error');
    } finally {
      setRequestingFaucet(false);
    }
  };

  const selectedTokenData = tokens.find(t => t.symbol === selectedToken) || { price: 0, change: 0 };
  const filteredTokens = tokens.filter(t => t.symbol.toLowerCase().includes(searchTerm.toLowerCase()));
  const currentNetwork = networks.find(n => n.id === chain?.id) || networks[0];

  return (
    <div className="space-y-6">
      {/* Wallet Status Banner */}
      {walletConnected && connectedAddress ? (
        <div className="bg-gradient-to-r from-blue-500/10 to-cyan-500/10 border border-blue-500/30 rounded-2xl p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 rounded-full bg-blue-400 animate-pulse" />
              <div>
                <p className="text-blue-400 font-semibold">Real Wallet Connected</p>
                <p className="text-sm text-gray-300">
                  Address: <span className="font-mono">{connectedAddress.slice(0, 6)}...{connectedAddress.slice(-4)}</span>
                  {selectedWallet === 'connected' ? ' • Real transactions enabled' : ' • Demo mode active'}
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-xs text-gray-400">Network</p>
              <p className="text-sm font-semibold text-white">{currentNetwork.name}</p>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-gradient-to-r from-yellow-500/10 to-orange-500/10 border border-yellow-500/30 rounded-2xl p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 rounded-full bg-yellow-400 animate-pulse" />
              <div>
                <p className="text-yellow-400 font-semibold">Demo Mode</p>
                <p className="text-sm text-gray-300">
                  Using demo wallet • Connect your wallet for real transactions
                </p>
              </div>
            </div>
            <button
              onClick={() => {
                // Trigger wallet connection modal
                const connectButton = document.querySelector('[data-wallet-connect]');
                if (connectButton) connectButton.click();
              }}
              className="px-4 py-2 bg-blue-500/20 border border-blue-500/30 rounded-lg text-blue-400 hover:bg-blue-500/30 transition-colors text-sm font-medium"
            >
              Connect Wallet
            </button>
          </div>
        </div>
      )}

      {/* Header Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { icon: Activity, label: 'BTC Price', value: `${formatPrice(tokens.find(t => t.symbol === 'BTC')?.price || 0)}`, change: tokens.find(t => t.symbol === 'BTC')?.change || 0, color: 'cyan' },
          { icon: BarChart3, label: 'ETH Price', value: `${formatPrice(tokens.find(t => t.symbol === 'ETH')?.price || 0)}`, change: tokens.find(t => t.symbol === 'ETH')?.change || 0, color: 'green' },
          { icon: Zap, label: 'Tracked Tokens', value: tokens.length.toString(), change: null, color: 'purple' },
          { icon: Shield, label: 'Selected', value: selectedToken, change: selectedTokenData.change, color: 'amber' }
        ].map((stat, i) => (
          <div key={i} className="p-4 rounded-2xl border border-gray-800 bg-[#0d1117]">
            <div className="flex items-center justify-between mb-2">
              <stat.icon size={18} className={`text-${stat.color}-400`} />
              {stat.change !== null && (
                <span className={`text-xs font-medium ${stat.change >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                  {stat.change >= 0 ? '+' : ''}{stat.change.toFixed(2)}%
                </span>
              )}
            </div>
            <p className="text-xs text-gray-500 mb-1">{stat.label}</p>
            <p className="text-xl font-bold text-white">{stat.value}</p>
          </div>
        ))}
      </div>

      {/* Network Selector Bar */}
      <div className="bg-gray-900 rounded-2xl border border-gray-800 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Globe size={18} className="text-[#2dd4bf]" />
            <span className="text-sm text-gray-400">Current Network:</span>
            <div className="flex items-center gap-2 px-3 py-2 bg-gray-800 rounded-lg">
              <span className="text-xl">{currentNetwork.icon}</span>
              <span className="font-semibold text-white">{currentNetwork.name}</span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {/* Testnet Faucet Button */}
            {chain?.id === 11155111 && (
              <button
                onClick={handleRequestFaucet}
                disabled={requestingFaucet}
                className="flex items-center gap-2 px-4 py-2 bg-blue-500/10 border border-blue-500/30 rounded-lg hover:bg-blue-500/20 transition-colors disabled:opacity-50"
              >
                <Droplet size={16} className="text-blue-400" />
                <span className="text-white font-medium">
                  {requestingFaucet ? 'Requesting...' : 'Get Test ETH'}
                </span>
              </button>
            )}
            
            {/* Network Switcher */}
            <div className="relative">
              <button
                onClick={() => setShowNetworks(!showNetworks)}
                className="flex items-center gap-2 px-4 py-2 bg-[#2dd4bf]/10 border border-[#2dd4bf]/30 rounded-lg hover:bg-[#2dd4bf]/20 transition-colors"
              >
                <span className="text-white font-medium">Switch Network</span>
                <ChevronDown size={16} className={`text-[#2dd4bf] transition-transform ${showNetworks ? 'rotate-180' : ''}`} />
              </button>
              {showNetworks && (
                <>
                  <div className="fixed inset-0 z-40" onClick={() => setShowNetworks(false)} />
                  <div className="absolute top-full right-0 mt-2 w-64 bg-gray-800 border border-gray-700 rounded-xl py-2 z-50 shadow-2xl">
                    {networks.map((network) => (
                      <button
                        key={network.id}
                        onClick={() => {
                          if (switchNetwork) {
                            switchNetwork(network.id);
                          }
                          setShowNetworks(false);
                        }}
                        className={`w-full px-4 py-3 text-left hover:bg-gray-700 transition-colors flex items-center gap-3 ${
                          chain?.id === network.id ? 'bg-gray-700/50' : ''
                        }`}
                      >
                        <span className="text-2xl">{network.icon}</span>
                        <div className="flex-1">
                          <p className="text-sm font-semibold text-white">{network.name}</p>
                          <p className="text-xs text-gray-400">{network.symbol}</p>
                        </div>
                        {chain?.id === network.id && (
                          <div className="w-2 h-2 rounded-full bg-[#2dd4bf] animate-pulse" />
                        )}
                      </button>
                    ))}
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
        
        {/* Faucet Message */}
        {faucetMessage && (
          <div className={`mt-3 p-3 rounded-lg text-sm ${
            faucetMessage.includes('Success') 
              ? 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-400'
              : 'bg-red-500/10 border border-red-500/30 text-red-400'
          }`}>
            {faucetMessage}
          </div>
        )}
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Token List */}
        <div className="lg:col-span-3">
          <div className="bg-gray-900 rounded-2xl border border-gray-800 p-4">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Activity size={18} className="text-cyan-400" />
                <h3 className="font-semibold text-white">Markets</h3>
              </div>
              <span className="text-xs text-cyan-400 bg-cyan-500/10 px-2 py-1 rounded-full animate-pulse">● LIVE</span>
            </div>
            
            <div className="relative mb-4">
              <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
              <input
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search tokens..."
                className="w-full pl-9 pr-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-white focus:border-cyan-500 outline-none"
              />
            </div>

            <div className="space-y-1 max-h-[600px] overflow-y-auto">
              {filteredTokens.map((token, i) => (
                <div
                  key={i}
                  onClick={() => setSelectedToken(token.symbol)}
                  className={`p-3 rounded-xl cursor-pointer transition-all border ${
                    selectedToken === token.symbol
                      ? 'bg-cyan-500/10 border-cyan-500/50'
                      : 'bg-gray-800/50 border-transparent hover:bg-gray-800 hover:border-cyan-500/20'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-white">{token.symbol}</span>
                    <span className={`text-xs font-medium ${token.change >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                      {token.change >= 0 ? '+' : ''}{token.change.toFixed(2)}%
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-lg font-bold text-white">${formatPrice(token.price)}</span>
                    <MiniChart data={tokenCharts[token.symbol]} change={token.change} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Chart */}
        <div className="lg:col-span-6">
          <div className="bg-gray-900 rounded-2xl border border-gray-800 p-5">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="font-semibold text-white text-xl">{selectedToken}/USDT</h3>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-3xl font-bold text-white">${formatPrice(selectedTokenData.price)}</span>
                  <span className={`flex items-center gap-0.5 text-sm font-medium px-2 py-1 rounded-lg ${
                    selectedTokenData.change >= 0 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'
                  }`}>
                    {selectedTokenData.change >= 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                    {selectedTokenData.change >= 0 ? '+' : ''}{selectedTokenData.change.toFixed(2)}%
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <ArrowLeftRight size={18} className="text-cyan-400" />
                <span className="text-sm text-gray-400">24H Chart</span>
              </div>
            </div>

            <div className="h-[400px]">
              {chartData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chartData}>
                    <defs>
                      <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor={selectedTokenData.change >= 0 ? '#10b981' : '#ef4444'} stopOpacity={0.4} />
                        <stop offset="100%" stopColor={selectedTokenData.change >= 0 ? '#10b981' : '#ef4444'} stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <XAxis dataKey="time" stroke="#4b5563" axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: '#6b7280' }} />
                    <YAxis stroke="#4b5563" axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: '#6b7280' }} domain={['auto', 'auto']} width={70} tickFormatter={v => `${v.toLocaleString()}`} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '12px' }}
                      formatter={(v) => [`${Number(v).toLocaleString()}`, 'Price']}
                    />
                    <Area type="monotone" dataKey="price" stroke={selectedTokenData.change >= 0 ? '#10b981' : '#ef4444'} strokeWidth={2} fill="url(#chartGradient)" />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-gray-500">
                  <div className="text-center">
                    <BarChart3 size={48} className="mx-auto mb-2 opacity-50" />
                    <p>Loading chart data...</p>
                  </div>
                </div>
              )}
            </div>

            <div className="grid grid-cols-3 gap-4 mt-6 pt-6 border-t border-gray-800">
              <div className="text-center p-3 rounded-xl bg-gray-800">
                <p className="text-xs text-gray-500 mb-1">24h High</p>
                <p className="text-lg font-bold text-emerald-400">${formatPrice(Math.max(...chartData.map(d => d.price)))}</p>
              </div>
              <div className="text-center p-3 rounded-xl bg-gray-800">
                <p className="text-xs text-gray-500 mb-1">24h Low</p>
                <p className="text-lg font-bold text-red-400">${formatPrice(Math.min(...chartData.map(d => d.price)))}</p>
              </div>
              <div className="text-center p-3 rounded-xl bg-gray-800">
                <p className="text-xs text-gray-500 mb-1">24h Change</p>
                <p className={`text-lg font-bold ${selectedTokenData.change >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                  {selectedTokenData.change >= 0 ? '+' : ''}{selectedTokenData.change.toFixed(2)}%
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Swap Panel */}
        <div className="lg:col-span-3">
          <div className="bg-gradient-to-br from-[#2dd4bf]/10 via-gray-900 to-gray-900 rounded-2xl border border-[#2dd4bf]/30 p-5">
            <div className="flex items-center justify-between mb-5">
              <div className="flex items-center gap-2">
                <ArrowLeftRight size={18} className="text-[#2dd4bf]" />
                <h3 className="font-semibold text-white">Swap</h3>
              </div>
              <button className="p-2 rounded-lg hover:bg-gray-800 transition-colors">
                <Settings size={16} className="text-gray-400" />
              </button>
            </div>

            {/* From Token */}
            <div className="mb-2">
              <label className="text-xs text-gray-400 mb-2 block">From</label>
              <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
                <div className="flex items-center justify-between mb-3">
                  <input
                    type="number"
                    value={fromAmount}
                    onChange={(e) => setFromAmount(e.target.value)}
                    placeholder="0.0"
                    className="bg-transparent text-2xl font-bold text-white outline-none w-full"
                  />
                </div>
                <div className="flex items-center justify-between">
                  <div className="relative">
                    <button
                      onClick={() => setShowFromTokens(!showFromTokens)}
                      className="flex items-center gap-2 px-3 py-2 bg-gray-700 rounded-lg hover:bg-gray-600 transition-colors"
                    >
                      <div className="w-6 h-6 rounded-full bg-gradient-to-br from-cyan-400 to-blue-500 flex items-center justify-center text-xs font-bold">
                        {fromToken.symbol.slice(0, 1)}
                      </div>
                      <span className="font-semibold text-white">{fromToken.symbol}</span>
                      <ChevronDown size={14} className="text-gray-400" />
                    </button>
                    {showFromTokens && (
                      <>
                        <div className="fixed inset-0 z-40" onClick={() => setShowFromTokens(false)} />
                        <div className="absolute top-full left-0 mt-2 w-56 bg-gray-800 border border-gray-700 rounded-xl py-2 z-50 max-h-80 overflow-y-auto">
                          {tokens.map((token, i) => (
                            <button
                              key={i}
                              onClick={() => {
                                setFromToken({ symbol: token.symbol, name: token.symbol });
                                setShowFromTokens(false);
                              }}
                              className="w-full px-4 py-2 text-left hover:bg-gray-700 transition-colors flex items-center gap-3"
                            >
                              <div className="w-6 h-6 rounded-full bg-gradient-to-br from-cyan-400 to-blue-500 flex items-center justify-center text-xs font-bold">
                                {token.symbol.slice(0, 1)}
                              </div>
                              <div>
                                <p className="text-sm font-semibold text-white">{token.symbol}</p>
                                <p className="text-xs text-gray-400">${formatPrice(token.price)}</p>
                              </div>
                            </button>
                          ))}
                        </div>
                      </>
                    )}
                  </div>
                  <span className="text-sm text-gray-400">Balance: {ethBalance}</span>
                </div>
              </div>
            </div>

            {/* Swap Button */}
            <div className="flex justify-center -my-2 relative z-10">
              <button
                onClick={handleSwapTokens}
                className="p-2 bg-gray-800 border-4 border-gray-900 rounded-xl hover:bg-gray-700 transition-all hover:rotate-180 duration-300"
              >
                <ArrowDown size={20} className="text-[#2dd4bf]" />
              </button>
            </div>

            {/* To Token */}
            <div className="mb-4">
              <label className="text-xs text-gray-400 mb-2 block">To</label>
              <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
                <div className="flex items-center justify-between mb-3">
                  <input
                    type="number"
                    value={toAmount}
                    readOnly
                    placeholder="0.0"
                    className="bg-transparent text-2xl font-bold text-white outline-none w-full"
                  />
                </div>
                <div className="flex items-center justify-between">
                  <div className="relative">
                    <button
                      onClick={() => setShowToTokens(!showToTokens)}
                      className="flex items-center gap-2 px-3 py-2 bg-gray-700 rounded-lg hover:bg-gray-600 transition-colors"
                    >
                      <div className="w-6 h-6 rounded-full bg-gradient-to-br from-green-400 to-emerald-500 flex items-center justify-center text-xs font-bold">
                        {toToken.symbol.slice(0, 1)}
                      </div>
                      <span className="font-semibold text-white">{toToken.symbol}</span>
                      <ChevronDown size={14} className="text-gray-400" />
                    </button>
                    {showToTokens && (
                      <>
                        <div className="fixed inset-0 z-40" onClick={() => setShowToTokens(false)} />
                        <div className="absolute top-full left-0 mt-2 w-56 bg-gray-800 border border-gray-700 rounded-xl py-2 z-50 max-h-80 overflow-y-auto">
                          <button
                            onClick={() => {
                              setToToken({ symbol: 'USDT', name: 'Tether USD' });
                              setShowToTokens(false);
                            }}
                            className="w-full px-4 py-2 text-left hover:bg-gray-700 transition-colors flex items-center gap-3"
                          >
                            <div className="w-6 h-6 rounded-full bg-gradient-to-br from-green-400 to-emerald-500 flex items-center justify-center text-xs font-bold">
                              U
                            </div>
                            <div>
                              <p className="text-sm font-semibold text-white">USDT</p>
                              <p className="text-xs text-gray-400">$1.00</p>
                            </div>
                          </button>
                          {tokens.map((token, i) => (
                            <button
                              key={i}
                              onClick={() => {
                                setToToken({ symbol: token.symbol, name: token.symbol });
                                setShowToTokens(false);
                              }}
                              className="w-full px-4 py-2 text-left hover:bg-gray-700 transition-colors flex items-center gap-3"
                            >
                              <div className="w-6 h-6 rounded-full bg-gradient-to-br from-green-400 to-emerald-500 flex items-center justify-center text-xs font-bold">
                                {token.symbol.slice(0, 1)}
                              </div>
                              <div>
                                <p className="text-sm font-semibold text-white">{token.symbol}</p>
                                <p className="text-xs text-gray-400">${formatPrice(token.price)}</p>
                              </div>
                            </button>
                          ))}
                        </div>
                      </>
                    )}
                  </div>
                  <span className="text-sm text-gray-400">Balance: 0.00</span>
                </div>
              </div>
            </div>

            {/* Swap Details */}
            {fromAmount && toAmount && (
              <div className="mb-4 p-3 bg-gray-800/50 rounded-xl space-y-2 text-sm">
                <div className="flex justify-between text-gray-400">
                  <span>Rate</span>
                  <span className="text-white">
                    1 {fromToken.symbol} = {(parseFloat(toAmount) / parseFloat(fromAmount)).toFixed(4)} {toToken.symbol}
                    {fetchingQuote && <span className="ml-2 text-cyan-400">Updating...</span>}
                  </span>
                </div>
                <div className="flex justify-between text-gray-400">
                  <span>Slippage</span>
                  <span className="text-white">{slippage}%</span>
                </div>
                {selectedWallet === 'connected' && swapQuote && (
                  <>
                    <div className="flex justify-between text-gray-400">
                      <span>Price Impact</span>
                      <span className="text-white">{swapQuote.priceImpact?.toFixed(2)}%</span>
                    </div>
                    <div className="flex justify-between text-gray-400">
                      <span>Uniswap Fee</span>
                      <span className="text-white">{swapQuote.fee?.toFixed(6)} {fromToken.symbol}</span>
                    </div>
                  </>
                )}
                <div className="flex justify-between text-gray-400">
                  <span>Network Fee</span>
                  <span className="text-white">
                    {selectedWallet === 'connected' ? '~$5-15' : 'Free (Mock)'}
                  </span>
                </div>
                {selectedWallet === 'connected' && (
                  <div className="flex justify-between text-gray-400">
                    <span>Network</span>
                    <span className="text-white">{currentNetwork.name}</span>
                  </div>
                )}
              </div>
            )}

            {/* Wallet Selector */}
            <div className="mb-4">
              <div className="flex items-center gap-2 mb-2">
                <Wallet size={14} className="text-gray-400" />
                <label className="text-xs text-gray-400">Using Wallet</label>
              </div>
              <div className="relative">
                <button
                  onClick={() => setShowWalletSelector(!showWalletSelector)}
                  className="w-full flex items-center justify-between px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl hover:bg-gray-700 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-3 h-3 rounded-full ${
                      (selectedWallet === 'connected' && connectedAddress) ? 'bg-blue-400' : 'bg-green-400'
                    }`} />
                    <div className="text-left">
                      <p className="text-sm font-semibold text-white">
                        {(selectedWallet === 'connected' && connectedAddress) ? 'Connected Wallet (Real)' : 
                         (connectedAddress && useConnectedWallet) ? 'Connected Wallet (Demo Mode)' : 'Demo Wallet'}
                      </p>
                      <p className="text-xs text-gray-400 font-mono">
                        {(selectedWallet === 'connected' && connectedAddress) 
                          ? `${connectedAddress.slice(0, 6)}...${connectedAddress.slice(-4)}`
                          : connectedAddress && useConnectedWallet
                          ? `${connectedAddress.slice(0, 6)}...${connectedAddress.slice(-4)}`
                          : `${address.slice(0, 6)}...${address.slice(-4)}`
                        }
                      </p>
                    </div>
                  </div>
                  <ChevronDown size={16} className={`text-gray-400 transition-transform ${showWalletSelector ? 'rotate-180' : ''}`} />
                </button>
                
                {showWalletSelector && (
                  <>
                    <div className="fixed inset-0 z-40" onClick={() => setShowWalletSelector(false)} />
                    <div className="absolute top-full left-0 right-0 mt-2 bg-gray-800 border border-gray-700 rounded-xl py-2 z-50 shadow-2xl">
                      {/* Connected Wallet - Real Transactions */}
                      {connectedAddress && (
                        <button
                          onClick={() => {
                            setSelectedWallet('connected');
                            setShowWalletSelector(false);
                          }}
                          className={`w-full px-4 py-3 text-left hover:bg-gray-700 transition-colors flex items-center gap-3 ${
                            selectedWallet === 'connected' ? 'bg-gray-700/50' : ''
                          }`}
                        >
                          <div className="w-3 h-3 rounded-full bg-blue-400" />
                          <div className="flex-1">
                            <p className="text-sm font-semibold text-white">Connected Wallet (Real)</p>
                            <p className="text-xs text-gray-400 font-mono">{connectedAddress.slice(0, 6)}...{connectedAddress.slice(-4)}</p>
                            <p className="text-xs text-blue-400">MetaMask • Real Uniswap Transactions</p>
                          </div>
                          {selectedWallet === 'connected' && (
                            <div className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
                          )}
                        </button>
                      )}
                      
                      {/* Connected Wallet - Demo Mode */}
                      {connectedAddress && (
                        <button
                          onClick={() => {
                            setSelectedWallet('autonomous');
                            setShowWalletSelector(false);
                          }}
                          className={`w-full px-4 py-3 text-left hover:bg-gray-700 transition-colors flex items-center gap-3 ${
                            selectedWallet === 'autonomous' && useConnectedWallet ? 'bg-gray-700/50' : ''
                          }`}
                        >
                          <div className="w-3 h-3 rounded-full bg-green-400" />
                          <div className="flex-1">
                            <p className="text-sm font-semibold text-white">Connected Wallet (Demo)</p>
                            <p className="text-xs text-gray-400 font-mono">{connectedAddress.slice(0, 6)}...{connectedAddress.slice(-4)}</p>
                            <p className="text-xs text-green-400">Your Address • Mock Transactions</p>
                          </div>
                          {selectedWallet === 'autonomous' && useConnectedWallet && (
                            <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                          )}
                        </button>
                      )}
                      
                      {/* Demo Wallet Option (only if no connected wallet) */}
                      {!connectedAddress && (
                        <button
                          onClick={() => {
                            setSelectedWallet('autonomous');
                            setShowWalletSelector(false);
                          }}
                          className={`w-full px-4 py-3 text-left hover:bg-gray-700 transition-colors flex items-center gap-3 ${
                            selectedWallet === 'autonomous' ? 'bg-gray-700/50' : ''
                          }`}
                        >
                          <div className="w-3 h-3 rounded-full bg-green-400" />
                          <div className="flex-1">
                            <p className="text-sm font-semibold text-white">Demo Wallet</p>
                            <p className="text-xs text-gray-400 font-mono">{address.slice(0, 6)}...{address.slice(-4)}</p>
                            <p className="text-xs text-green-400">Demo Address • Mock Transactions</p>
                          </div>
                          {selectedWallet === 'autonomous' && (
                            <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                          )}
                        </button>
                      )}
                    </div>
                  </>
                )}
              </div>
            </div>
            
            {/* Error Message */}
            {error && (
              <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-xl text-sm text-red-400">
                {error}
              </div>
            )}
            
            {/* Success/Pending/Failed Message */}
            {txHash && (
              <div className={`mb-4 p-3 rounded-xl text-sm ${
                txStatus === 'success' 
                  ? 'bg-emerald-500/10 border border-emerald-500/30'
                  : txStatus === 'pending'
                  ? 'bg-yellow-500/10 border border-yellow-500/30'
                  : txStatus === 'failed'
                  ? 'bg-red-500/10 border border-red-500/30'
                  : 'bg-blue-500/10 border border-blue-500/30'
              }`}>
                <div className="flex items-center gap-2 mb-2">
                  {txStatus === 'success' && (
                    <>
                      <div className="w-2 h-2 rounded-full bg-emerald-400" />
                      <p className="text-emerald-400 font-medium">
                        {selectedWallet === 'connected' ? 'Real swap successful!' : 'Mock swap successful!'}
                      </p>
                    </>
                  )}
                  {txStatus === 'pending' && (
                    <>
                      <div className="w-2 h-2 rounded-full bg-yellow-400 animate-pulse" />
                      <p className="text-yellow-400 font-medium">
                        Transaction pending confirmation...
                      </p>
                    </>
                  )}
                  {txStatus === 'failed' && (
                    <>
                      <div className="w-2 h-2 rounded-full bg-red-400" />
                      <p className="text-red-400 font-medium">
                        Transaction failed
                      </p>
                    </>
                  )}
                  {!txStatus && (
                    <>
                      <div className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
                      <p className="text-blue-400 font-medium">
                        Transaction submitted
                      </p>
                    </>
                  )}
                </div>
                <a 
                  href={
                    selectedWallet === 'connected' && chain?.id 
                      ? `${getExplorerUrl(chain.id)}/tx/${txHash}`
                      : `https://sepolia.etherscan.io/tx/${txHash}`
                  }
                  target="_blank"
                  rel="noopener noreferrer"
                  className={`font-mono text-xs break-all hover:underline ${
                    txStatus === 'success' ? 'text-emerald-400' :
                    txStatus === 'pending' ? 'text-yellow-400' :
                    txStatus === 'failed' ? 'text-red-400' : 'text-blue-400'
                  }`}
                >
                  {txHash}
                </a>
                {selectedWallet === 'connected' && txStatus === 'success' && (
                  <p className="text-xs text-gray-400 mt-2">
                    Transaction confirmed on {currentNetwork.name}
                  </p>
                )}
                {txStatus === 'pending' && (
                  <div className="mt-3">
                    <p className="text-xs text-gray-400 mb-2">
                      Waiting for blockchain confirmation...
                    </p>
                    <button
                      onClick={() => verifyTransactionStatus(txHash)}
                      className="text-xs px-3 py-1 bg-yellow-500/20 border border-yellow-500/30 rounded-lg text-yellow-400 hover:bg-yellow-500/30 transition-colors"
                    >
                      Check Status
                    </button>
                  </div>
                )}
                {txStatus === 'failed' && (
                  <p className="text-xs text-red-400 mt-2">
                    Transaction failed on blockchain. Check the transaction link above for details.
                  </p>
                )}
              </div>
            )}

            {/* Swap Button */}
            <button
              onClick={handleSwap}
              disabled={
                (selectedWallet === 'connected' && !connectedAddress) || 
                (selectedWallet === 'autonomous' && !address) || 
                !fromAmount || 
                swapping ||
                fetchingQuote
              }
              className={`w-full py-4 rounded-xl font-bold text-lg transition-all ${
                (selectedWallet === 'connected' && !connectedAddress) || 
                (selectedWallet === 'autonomous' && !address) || 
                !fromAmount || 
                swapping ||
                fetchingQuote
                  ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                  : 'bg-gradient-to-r from-[#2dd4bf] to-cyan-500 text-black hover:shadow-lg hover:shadow-[#2dd4bf]/50'
              }`}
            >
              {selectedWallet === 'connected' && !connectedAddress 
                ? 'Connect Wallet' 
                : selectedWallet === 'autonomous' && !address
                ? 'Autonomous Wallet Unavailable'
                : fetchingQuote
                ? 'Getting Quote...'
                : swapping 
                ? (selectedWallet === 'connected' ? 'Processing Transaction...' : 'Swapping...') 
                : 'Swap'
              }
            </button>

            {/* Info */}
            <p className="text-xs text-gray-500 text-center mt-3">
              Powered by DEX Aggregator
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TradingPage;
