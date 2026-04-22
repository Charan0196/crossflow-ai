import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, ArrowRight, Clock, DollarSign, Zap } from 'lucide-react';

const SUPPORTED_CHAINS = [
  { id: 1, name: 'Ethereum', symbol: 'ETH', color: 'bg-blue-500' },
  { id: 137, name: 'Polygon', symbol: 'MATIC', color: 'bg-purple-500' },
  { id: 42161, name: 'Arbitrum', symbol: 'ARB', color: 'bg-blue-600' },
  { id: 10, name: 'Optimism', symbol: 'OP', color: 'bg-red-500' },
  { id: 8453, name: 'Base', symbol: 'BASE', color: 'bg-blue-400' },
  { id: 56, name: 'BSC', symbol: 'BNB', color: 'bg-yellow-500' }
];

const POPULAR_TOKENS = {
  1: [
    { symbol: 'ETH', address: '0x0000000000000000000000000000000000000000', decimals: 18 },
    { symbol: 'USDC', address: '0xa0b86a33e6c6c9c6c6c6c6c6c6c6c6c6c6c6c6c6', decimals: 6 },
    { symbol: 'USDT', address: '0xdac17f958d2ee523a2206206994597c13d831ec7', decimals: 6 },
    { symbol: 'DAI', address: '0x6b175474e89094c44da98b954eedeac495271d0f', decimals: 18 }
  ],
  137: [
    { symbol: 'MATIC', address: '0x0000000000000000000000000000000000000000', decimals: 18 },
    { symbol: 'USDC', address: '0x2791bca1f2de4661ed88a30c99a7a9449aa84174', decimals: 6 },
    { symbol: 'WETH', address: '0x7ceb23fd6c0c6b4e2b8c3594c5c7f9b7c3c3c3c3', decimals: 18 }
  ]
};

export default function IntentCreationInterface() {
  const [formData, setFormData] = useState({
    sourceChain: '',
    destinationChain: '',
    inputToken: '',
    outputToken: '',
    inputAmount: '',
    minimumOutputAmount: '',
    deadline: '30' // minutes
  });

  const [estimation, setEstimation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});
  const [livePrices, setLivePrices] = useState({});

  // Fetch live prices
  useEffect(() => {
    const fetchPrices = async () => {
      try {
        const response = await fetch('/api/prices/live');
        const prices = await response.json();
        setLivePrices(prices);
      } catch (error) {
        console.error('Failed to fetch live prices:', error);
      }
    };

    fetchPrices();
    const interval = setInterval(fetchPrices, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, []);

  // Calculate estimation when form changes
  useEffect(() => {
    if (formData.sourceChain && formData.destinationChain && 
        formData.inputToken && formData.outputToken && formData.inputAmount) {
      calculateEstimation();
    }
  }, [formData]);

  const calculateEstimation = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/intents/estimate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      
      const data = await response.json();
      setEstimation(data);
      
      // Auto-fill minimum output if not set
      if (!formData.minimumOutputAmount && data.estimatedOutput) {
        setFormData(prev => ({
          ...prev,
          minimumOutputAmount: (parseFloat(data.estimatedOutput) * 0.95).toFixed(6) // 5% slippage
        }));
      }
    } catch (error) {
      console.error('Estimation failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.sourceChain) newErrors.sourceChain = 'Source chain required';
    if (!formData.destinationChain) newErrors.destinationChain = 'Destination chain required';
    if (!formData.inputToken) newErrors.inputToken = 'Input token required';
    if (!formData.outputToken) newErrors.outputToken = 'Output token required';
    if (!formData.inputAmount || parseFloat(formData.inputAmount) <= 0) {
      newErrors.inputAmount = 'Valid input amount required';
    }
    if (!formData.minimumOutputAmount || parseFloat(formData.minimumOutputAmount) <= 0) {
      newErrors.minimumOutputAmount = 'Valid minimum output required';
    }
    if (formData.sourceChain === formData.destinationChain) {
      newErrors.destinationChain = 'Destination must differ from source';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) return;

    setLoading(true);
    try {
      const response = await fetch('/api/intents/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...formData,
          deadline: Date.now() + (parseInt(formData.deadline) * 60 * 1000) // Convert minutes to timestamp
        })
      });

      if (response.ok) {
        const intent = await response.json();
        // Redirect to intent tracking page
        window.location.href = `/intents/${intent.id}`;
      } else {
        const error = await response.json();
        setErrors({ submit: error.message });
      }
    } catch (error) {
      setErrors({ submit: 'Failed to create intent' });
    } finally {
      setLoading(false);
    }
  };

  const getTokensForChain = (chainId) => {
    return POPULAR_TOKENS[chainId] || [];
  };

  const formatEstimation = () => {
    if (!estimation) return null;

    return (
      <Card className="mt-4 border-green-200 bg-green-50">
        <CardContent className="pt-4">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="flex items-center gap-2">
              <DollarSign className="h-4 w-4 text-green-600" />
              <span>Estimated Output: <strong>{estimation.estimatedOutput}</strong></span>
            </div>
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-blue-600" />
              <span>Execution Time: <strong>{estimation.executionTime}</strong></span>
            </div>
            <div className="flex items-center gap-2">
              <Zap className="h-4 w-4 text-yellow-600" />
              <span>Gas Fees: <strong>{estimation.totalGasFees}</strong></span>
            </div>
            <div className="flex items-center gap-2">
              <ArrowRight className="h-4 w-4 text-purple-600" />
              <span>Price Impact: <strong>{estimation.priceImpact}%</strong></span>
            </div>
          </div>
          
          {estimation.warnings && estimation.warnings.length > 0 && (
            <Alert className="mt-3">
              <AlertDescription>
                {estimation.warnings.join(', ')}
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>
    );
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="h-5 w-5 text-blue-600" />
            Create Cross-Chain Intent
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Chain Selection */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Source Chain</label>
                <Select 
                  value={formData.sourceChain} 
                  onValueChange={(value) => setFormData(prev => ({ ...prev, sourceChain: value }))}
                >
                  <SelectTrigger className={errors.sourceChain ? 'border-red-500' : ''}>
                    <SelectValue placeholder="Select source chain" />
                  </SelectTrigger>
                  <SelectContent>
                    {SUPPORTED_CHAINS.map(chain => (
                      <SelectItem key={chain.id} value={chain.id.toString()}>
                        <div className="flex items-center gap-2">
                          <div className={`w-3 h-3 rounded-full ${chain.color}`} />
                          {chain.name}
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {errors.sourceChain && <p className="text-red-500 text-xs mt-1">{errors.sourceChain}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Destination Chain</label>
                <Select 
                  value={formData.destinationChain} 
                  onValueChange={(value) => setFormData(prev => ({ ...prev, destinationChain: value }))}
                >
                  <SelectTrigger className={errors.destinationChain ? 'border-red-500' : ''}>
                    <SelectValue placeholder="Select destination chain" />
                  </SelectTrigger>
                  <SelectContent>
                    {SUPPORTED_CHAINS.map(chain => (
                      <SelectItem key={chain.id} value={chain.id.toString()}>
                        <div className="flex items-center gap-2">
                          <div className={`w-3 h-3 rounded-full ${chain.color}`} />
                          {chain.name}
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {errors.destinationChain && <p className="text-red-500 text-xs mt-1">{errors.destinationChain}</p>}
              </div>
            </div>

            {/* Token Selection */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Input Token</label>
                <Select 
                  value={formData.inputToken} 
                  onValueChange={(value) => setFormData(prev => ({ ...prev, inputToken: value }))}
                  disabled={!formData.sourceChain}
                >
                  <SelectTrigger className={errors.inputToken ? 'border-red-500' : ''}>
                    <SelectValue placeholder="Select input token" />
                  </SelectTrigger>
                  <SelectContent>
                    {getTokensForChain(parseInt(formData.sourceChain)).map(token => (
                      <SelectItem key={token.address} value={token.address}>
                        <div className="flex items-center justify-between w-full">
                          <span>{token.symbol}</span>
                          {livePrices[token.symbol] && (
                            <Badge variant="secondary" className="ml-2">
                              ${livePrices[token.symbol]}
                            </Badge>
                          )}
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {errors.inputToken && <p className="text-red-500 text-xs mt-1">{errors.inputToken}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Output Token</label>
                <Select 
                  value={formData.outputToken} 
                  onValueChange={(value) => setFormData(prev => ({ ...prev, outputToken: value }))}
                  disabled={!formData.destinationChain}
                >
                  <SelectTrigger className={errors.outputToken ? 'border-red-500' : ''}>
                    <SelectValue placeholder="Select output token" />
                  </SelectTrigger>
                  <SelectContent>
                    {getTokensForChain(parseInt(formData.destinationChain)).map(token => (
                      <SelectItem key={token.address} value={token.address}>
                        <div className="flex items-center justify-between w-full">
                          <span>{token.symbol}</span>
                          {livePrices[token.symbol] && (
                            <Badge variant="secondary" className="ml-2">
                              ${livePrices[token.symbol]}
                            </Badge>
                          )}
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {errors.outputToken && <p className="text-red-500 text-xs mt-1">{errors.outputToken}</p>}
              </div>
            </div>

            {/* Amount Inputs */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-2">Input Amount</label>
                <Input
                  type="number"
                  step="0.000001"
                  placeholder="0.0"
                  value={formData.inputAmount}
                  onChange={(e) => setFormData(prev => ({ ...prev, inputAmount: e.target.value }))}
                  className={errors.inputAmount ? 'border-red-500' : ''}
                />
                {errors.inputAmount && <p className="text-red-500 text-xs mt-1">{errors.inputAmount}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Minimum Output</label>
                <Input
                  type="number"
                  step="0.000001"
                  placeholder="0.0"
                  value={formData.minimumOutputAmount}
                  onChange={(e) => setFormData(prev => ({ ...prev, minimumOutputAmount: e.target.value }))}
                  className={errors.minimumOutputAmount ? 'border-red-500' : ''}
                />
                {errors.minimumOutputAmount && <p className="text-red-500 text-xs mt-1">{errors.minimumOutputAmount}</p>}
              </div>
            </div>

            {/* Deadline */}
            <div>
              <label className="block text-sm font-medium mb-2">Deadline (minutes)</label>
              <Select 
                value={formData.deadline} 
                onValueChange={(value) => setFormData(prev => ({ ...prev, deadline: value }))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="15">15 minutes</SelectItem>
                  <SelectItem value="30">30 minutes</SelectItem>
                  <SelectItem value="60">1 hour</SelectItem>
                  <SelectItem value="120">2 hours</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Estimation Display */}
            {formatEstimation()}

            {/* Submit Button */}
            <Button 
              type="submit" 
              className="w-full" 
              disabled={loading}
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating Intent...
                </>
              ) : (
                'Create Intent'
              )}
            </Button>

            {errors.submit && (
              <Alert className="border-red-200 bg-red-50">
                <AlertDescription className="text-red-700">
                  {errors.submit}
                </AlertDescription>
              </Alert>
            )}
          </form>
        </CardContent>
      </Card>
    </div>
  );
}