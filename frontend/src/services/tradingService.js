/**
 * Phase 5: Trading Service
 * 
 * API client for trading operations:
 * - Swap quotes and execution
 * - Bridge quotes and execution
 * - Order management
 * - Transaction tracking
 */

import { API_BASE_URL } from '../config/api';

const BASE_URL = API_BASE_URL || 'http://localhost:8000/api/v1';

/**
 * Get swap quote from multiple DEXs
 */
export async function getSwapQuote(params) {
  const response = await fetch(`${BASE_URL}/trading/v2/swap/quote`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params)
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to get swap quote');
  }
  
  return response.json();
}

/**
 * Execute a swap transaction
 */
export async function executeSwap(params) {
  const response = await fetch(`${BASE_URL}/trading/v2/swap/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params)
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to execute swap');
  }
  
  return response.json();
}

/**
 * Simulate a swap before execution
 */
export async function simulateSwap(params) {
  const response = await fetch(`${BASE_URL}/trading/v2/swap/simulate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params)
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to simulate swap');
  }
  
  return response.json();
}

/**
 * Get bridge quote for cross-chain transfer
 */
export async function getBridgeQuote(params) {
  const response = await fetch(`${BASE_URL}/trading/v2/bridge/quote`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params)
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to get bridge quote');
  }
  
  return response.json();
}

/**
 * Execute a bridge transaction
 */
export async function executeBridge(params) {
  const response = await fetch(`${BASE_URL}/trading/v2/bridge/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params)
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to execute bridge');
  }
  
  return response.json();
}

/**
 * Get transaction status
 */
export async function getTransactionStatus(txHash) {
  const response = await fetch(`${BASE_URL}/trading/v2/transaction/${txHash}`);
  
  if (!response.ok) {
    if (response.status === 404) return null;
    throw new Error('Failed to get transaction status');
  }
  
  return response.json();
}

/**
 * Get bridge status
 */
export async function getBridgeStatus(bridgeId) {
  const response = await fetch(`${BASE_URL}/trading/v2/bridge/${bridgeId}`);
  
  if (!response.ok) {
    if (response.status === 404) return null;
    throw new Error('Failed to get bridge status');
  }
  
  return response.json();
}

/**
 * Get supported chains
 */
export async function getSupportedChains() {
  const response = await fetch(`${BASE_URL}/trading/v2/supported-chains`);
  return response.json();
}

/**
 * Get supported tokens for a chain
 */
export async function getSupportedTokens(chainId) {
  const response = await fetch(`${BASE_URL}/trading/v2/supported-tokens/${chainId}`);
  return response.json();
}

/**
 * Get token price
 */
export async function getTokenPrice(symbol) {
  const response = await fetch(`${BASE_URL}/trading/v2/price/${symbol}`);
  
  if (!response.ok) {
    if (response.status === 404) return null;
    throw new Error('Failed to get price');
  }
  
  return response.json();
}

/**
 * Get multiple token prices
 */
export async function getTokenPrices(symbols) {
  const response = await fetch(`${BASE_URL}/trading/v2/prices?symbols=${symbols.join(',')}`);
  return response.json();
}

/**
 * Get arbitrage opportunities
 */
export async function getArbitrageOpportunities(token, amountUsd = 1000) {
  const response = await fetch(`${BASE_URL}/trading/v2/arbitrage/${token}?amount_usd=${amountUsd}`);
  return response.json();
}

// Order Management

/**
 * Create a new order
 */
export async function createOrder(params) {
  const response = await fetch(`${BASE_URL}/orders/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params)
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create order');
  }
  
  return response.json();
}

/**
 * Get user orders
 */
export async function getOrders(params = {}) {
  const queryParams = new URLSearchParams(params);
  const response = await fetch(`${BASE_URL}/orders/?${queryParams}`);
  return response.json();
}

/**
 * Get open orders
 */
export async function getOpenOrders() {
  const response = await fetch(`${BASE_URL}/orders/open`);
  return response.json();
}

/**
 * Get order history
 */
export async function getOrderHistory(page = 1, pageSize = 50) {
  const response = await fetch(`${BASE_URL}/orders/history?page=${page}&page_size=${pageSize}`);
  return response.json();
}

/**
 * Cancel an order
 */
export async function cancelOrder(orderId) {
  const response = await fetch(`${BASE_URL}/orders/${orderId}`, {
    method: 'DELETE'
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to cancel order');
  }
  
  return response.json();
}

/**
 * Get order estimate
 */
export async function getOrderEstimate(orderId) {
  const response = await fetch(`${BASE_URL}/orders/${orderId}/estimate`, {
    method: 'POST'
  });
  return response.json();
}

export default {
  getSwapQuote,
  executeSwap,
  simulateSwap,
  getBridgeQuote,
  executeBridge,
  getTransactionStatus,
  getBridgeStatus,
  getSupportedChains,
  getSupportedTokens,
  getTokenPrice,
  getTokenPrices,
  getArbitrageOpportunities,
  createOrder,
  getOrders,
  getOpenOrders,
  getOrderHistory,
  cancelOrder,
  getOrderEstimate
};
