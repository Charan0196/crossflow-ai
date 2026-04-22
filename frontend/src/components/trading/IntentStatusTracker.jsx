import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Clock, CheckCircle, XCircle, AlertCircle, 
  ArrowRight, Loader2, ExternalLink, Copy 
} from 'lucide-react';

const INTENT_STATUSES = {
  CREATED: { label: 'Created', color: 'bg-gray-500', step: 1 },
  VALIDATED: { label: 'Validated', color: 'bg-blue-500', step: 2 },
  SUBMITTED: { label: 'Submitted', color: 'bg-yellow-500', step: 3 },
  SOLVER_SELECTED: { label: 'Solver Selected', color: 'bg-purple-500', step: 4 },
  FUNDS_LOCKED: { label: 'Funds Locked', color: 'bg-orange-500', step: 5 },
  EXECUTING: { label: 'Executing', color: 'bg-blue-600', step: 6 },
  COMPLETED: { label: 'Completed', color: 'bg-green-500', step: 7 },
  FAILED: { label: 'Failed', color: 'bg-red-500', step: 0 },
  CANCELLED: { label: 'Cancelled', color: 'bg-gray-600', step: 0 },
  REFUNDED: { label: 'Refunded', color: 'bg-yellow-600', step: 0 }
};

const PROGRESS_STEPS = [
  { key: 'CREATED', label: 'Intent Created' },
  { key: 'VALIDATED', label: 'Validation Complete' },
  { key: 'SUBMITTED', label: 'Submitted to Network' },
  { key: 'SOLVER_SELECTED', label: 'Solver Selected' },
  { key: 'FUNDS_LOCKED', label: 'Funds Secured' },
  { key: 'EXECUTING', label: 'Cross-Chain Execution' },
  { key: 'COMPLETED', label: 'Trade Complete' }
];

export default function IntentStatusTracker({ intentId }) {
  const [intentData, setIntentData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [wsConnection, setWsConnection] = useState(null);

  useEffect(() => {
    if (!intentId) return;

    // Fetch initial intent data
    fetchIntentData();

    // Establish WebSocket connection for real-time updates
    const ws = new WebSocket(`ws://localhost:8000/ws/intents/${intentId}`);
    
    ws.onopen = () => {
      console.log('WebSocket connected');
      setWsConnection(ws);
    };

    ws.onmessage = (event) => {
      const update = JSON.parse(event.data);
      setIntentData(prev => ({ ...prev, ...update }));
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setError('Real-time updates unavailable');
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setWsConnection(null);
    };

    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, [intentId]);

  const fetchIntentData = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/intents/${intentId}`);
      if (response.ok) {
        const data = await response.json();
        setIntentData(data);
      } else {
        setError('Intent not found');
      }
    } catch (err) {
      setError('Failed to fetch intent data');
    } finally {
      setLoading(false);
    }
  };

  const getProgressPercentage = () => {
    if (!intentData) return 0;
    
    const currentStatus = INTENT_STATUSES[intentData.status];
    if (!currentStatus || currentStatus.step === 0) return 0;
    
    return (currentStatus.step / PROGRESS_STEPS.length) * 100;
  };

  const getEstimatedCompletion = () => {
    if (!intentData || !intentData.estimatedCompletionTime) return null;
    
    const completionTime = new Date(intentData.estimatedCompletionTime);
    const now = new Date();
    const diffMs = completionTime - now;
    
    if (diffMs <= 0) return 'Overdue';
    
    const diffMinutes = Math.ceil(diffMs / (1000 * 60));
    if (diffMinutes < 60) return `~${diffMinutes}m remaining`;
    
    const diffHours = Math.ceil(diffMinutes / 60);
    return `~${diffHours}h remaining`;
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'COMPLETED':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'FAILED':
      case 'CANCELLED':
        return <XCircle className="h-5 w-5 text-red-500" />;
      case 'EXECUTING':
        return <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />;
      default:
        return <Clock className="h-5 w-5 text-yellow-500" />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-8 w-8 animate-spin" />
        <span className="ml-2">Loading intent status...</span>
      </div>
    );
  }

  if (error) {
    return (
      <Alert className="border-red-200 bg-red-50">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  if (!intentData) return null;

  const currentStatus = INTENT_STATUSES[intentData.status];
  const progressPercentage = getProgressPercentage();
  const estimatedCompletion = getEstimatedCompletion();

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              {getStatusIcon(intentData.status)}
              Intent Status: {currentStatus.label}
            </CardTitle>
            <div className="flex items-center gap-2">
              <Badge className={`${currentStatus.color} text-white`}>
                {currentStatus.label}
              </Badge>
              {wsConnection && (
                <Badge variant="outline" className="text-green-600 border-green-600">
                  Live Updates
                </Badge>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <p className="text-gray-500">Intent ID</p>
              <div className="flex items-center gap-1">
                <code className="font-mono">{intentData.id.slice(0, 8)}...</code>
                <Copy 
                  className="h-3 w-3 cursor-pointer text-gray-400 hover:text-gray-600" 
                  onClick={() => copyToClipboard(intentData.id)}
                />
              </div>
            </div>
            <div>
              <p className="text-gray-500">Created</p>
              <p className="font-medium">{new Date(intentData.createdAt).toLocaleString()}</p>
            </div>
            <div>
              <p className="text-gray-500">Trade Route</p>
              <p className="font-medium">{intentData.sourceChain} → {intentData.destinationChain}</p>
            </div>
            <div>
              <p className="text-gray-500">Estimated Completion</p>
              <p className="font-medium">{estimatedCompletion || 'Calculating...'}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Progress Tracker */}
      <Card>
        <CardHeader>
          <CardTitle>Execution Progress</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between text-sm">
              <span>Progress</span>
              <span>{Math.round(progressPercentage)}% Complete</span>
            </div>
            <Progress value={progressPercentage} className="h-2" />
            
            {/* Step-by-step progress */}
            <div className="space-y-3 mt-6">
              {PROGRESS_STEPS.map((step, index) => {
                const isCompleted = currentStatus.step > index + 1;
                const isCurrent = currentStatus.step === index + 1;
                const isPending = currentStatus.step < index + 1;

                return (
                  <div key={step.key} className="flex items-center gap-3">
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium ${
                      isCompleted ? 'bg-green-500 text-white' :
                      isCurrent ? 'bg-blue-500 text-white' :
                      'bg-gray-200 text-gray-500'
                    }`}>
                      {isCompleted ? '✓' : index + 1}
                    </div>
                    <div className="flex-1">
                      <p className={`font-medium ${
                        isCompleted ? 'text-green-700' :
                        isCurrent ? 'text-blue-700' :
                        'text-gray-500'
                      }`}>
                        {step.label}
                      </p>
                      {isCurrent && intentData.currentStepDetails && (
                        <p className="text-sm text-gray-600">{intentData.currentStepDetails}</p>
                      )}
                    </div>
                    {isCurrent && (
                      <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Trade Details */}
      <Card>
        <CardHeader>
          <CardTitle>Trade Details</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-3">
              <h4 className="font-medium text-gray-700">Input</h4>
              <div className="bg-gray-50 p-3 rounded-lg">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Amount</span>
                  <span className="font-medium">{intentData.inputAmount} {intentData.inputToken}</span>
                </div>
                <div className="flex items-center justify-between mt-1">
                  <span className="text-sm text-gray-600">Chain</span>
                  <span className="font-medium">{intentData.sourceChain}</span>
                </div>
              </div>
            </div>

            <div className="space-y-3">
              <h4 className="font-medium text-gray-700">Output</h4>
              <div className="bg-gray-50 p-3 rounded-lg">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Expected</span>
                  <span className="font-medium">{intentData.expectedOutput} {intentData.outputToken}</span>
                </div>
                <div className="flex items-center justify-between mt-1">
                  <span className="text-sm text-gray-600">Chain</span>
                  <span className="font-medium">{intentData.destinationChain}</span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Solver Information */}
      {intentData.selectedSolver && (
        <Card>
          <CardHeader>
            <CardTitle>Solver Information</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <p className="text-sm text-gray-600">Solver</p>
                <p className="font-medium">{intentData.selectedSolver.name}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Reputation</p>
                <div className="flex items-center gap-2">
                  <div className="flex">
                    {[...Array(5)].map((_, i) => (
                      <span key={i} className={`text-sm ${
                        i < intentData.selectedSolver.reputation ? 'text-yellow-400' : 'text-gray-300'
                      }`}>
                        ★
                      </span>
                    ))}
                  </div>
                  <span className="text-sm text-gray-600">
                    ({intentData.selectedSolver.successRate}% success)
                  </span>
                </div>
              </div>
              <div>
                <p className="text-sm text-gray-600">Execution Fee</p>
                <p className="font-medium">{intentData.selectedSolver.fee}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Transaction Hashes */}
      {intentData.transactionHashes && intentData.transactionHashes.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Transaction Hashes</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {intentData.transactionHashes.map((tx, index) => (
                <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                  <div>
                    <p className="font-mono text-sm">{tx.hash}</p>
                    <p className="text-xs text-gray-600">{tx.chain} - {tx.type}</p>
                  </div>
                  <ExternalLink 
                    className="h-4 w-4 cursor-pointer text-blue-500 hover:text-blue-700"
                    onClick={() => window.open(tx.explorerUrl, '_blank')}
                  />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Error Information */}
      {intentData.status === 'FAILED' && intentData.errorMessage && (
        <Alert className="border-red-200 bg-red-50">
          <XCircle className="h-4 w-4" />
          <AlertDescription>
            <strong>Execution Failed:</strong> {intentData.errorMessage}
            {intentData.canRetry && (
              <div className="mt-2">
                <button className="text-blue-600 hover:text-blue-800 underline">
                  Retry Intent
                </button>
              </div>
            )}
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}