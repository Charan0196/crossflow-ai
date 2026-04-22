/**
 * Type definitions for CrossFlow AI SDK
 */

export interface ClientConfig {
  apiUrl: string;
  token?: string;
  timeout?: number;
  retries?: number;
}

export interface IntentCreateRequest {
  sourceChain: number;
  destinationChain: number;
  inputToken: string;
  outputToken: string;
  inputAmount: string;
  minimumOutputAmount: string;
  deadline?: number;
  recipient?: string;
  maxGasPrice?: string;
  slippageTolerance?: number;
}

export interface Intent {
  intentId: string;
  status: string;
  userAddress: string;
  sourceChain: number;
  destinationChain: number;
  inputToken: string;
  outputToken: string;
  inputAmount: string;
  minimumOutputAmount: string;
  deadline: number;
  createdAt: string;
  updatedAt: string;
  estimatedExecutionTime?: number;
  estimatedGasCost?: string;
  solverAddress?: string;
  transactionHash?: string;
  errorMessage?: string;
}

export interface IntentStatus {
  intentId: string;
  status: string;
  progress: {
    created: boolean;
    validated: boolean;
    submitted: boolean;
    solverSelected: boolean;
    fundsLocked: boolean;
    executing: boolean;
    completed: boolean;
    failed: boolean;
  };
  executionDetails?: {
    executionTimeMs: number;
    gasUsed: string;
    feesPaid: string;
    solverAddress: string;
    outputAmount: string;
  };
  errorDetails?: {
    errorMessage: string;
    executionTimeMs: number;
    solverAddress: string;
  };
  estimatedCompletion?: string;
}

export interface IntentListResponse {
  intents: Intent[];
  totalCount: number;
  page: number;
  pageSize: number;
  hasNext: boolean;
}

export interface IntentListOptions {
  page?: number;
  pageSize?: number;
  status?: string;
  sourceChain?: number;
  destinationChain?: number;
}

export interface IntentEstimate {
  intentId: string;
  estimatedExecutionTimeSeconds: number;
  estimatedGasCostEth: string;
  estimatedGasCostUsd: string;
  estimatedOutputAmount: string;
  priceImpactPercentage: number;
  updatedAt: string;
}

export interface PriceData {
  tokenPair: string;
  price: string;
  volume24h: string;
  change24h: string;
  changePercent24h: string;
  high24h: string;
  low24h: string;
  timestamp: number;
  source: string;
}

export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: number;
  messageId: string;
}

export interface WebSocketConfig {
  reconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  heartbeatInterval?: number;
}

export type WebSocketEventType = 
  | 'connect'
  | 'disconnect'
  | 'error'
  | 'message'
  | 'intentStatusUpdate'
  | 'priceUpdate'
  | 'solverBidUpdate'
  | 'systemNotification'
  | 'heartbeat';

export interface AuthResponse {
  accessToken: string;
  tokenType: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface ApiError {
  detail: Array<{
    loc: string[];
    msg: string;
    type: string;
  }>;
}

export enum ChainId {
  ETHEREUM = 1,
  POLYGON = 137,
  ARBITRUM = 42161,
  OPTIMISM = 10,
  BSC = 56,
  BASE = 8453
}

export enum IntentStatusType {
  CREATED = 'created',
  VALIDATED = 'validated',
  SUBMITTED = 'submitted',
  SOLVER_SELECTED = 'solver_selected',
  FUNDS_LOCKED = 'funds_locked',
  EXECUTING = 'executing',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled'
}