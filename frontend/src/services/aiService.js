/**
 * Phase 5: AI Service
 * 
 * API client for AI-powered features:
 * - Trading signals
 * - Portfolio analysis
 * - Rebalancing recommendations
 */

import { API_BASE_URL } from '../config/api';

const BASE_URL = API_BASE_URL || 'http://localhost:8000/api/v1';

/**
 * Get AI trading signals for a token
 */
export async function getSignals(token, options = {}) {
  const params = new URLSearchParams({
    token,
    ...(options.timeframe && { timeframe: options.timeframe }),
    ...(options.risk_tolerance && { risk_tolerance: options.risk_tolerance })
  });
  
  const response = await fetch(`${BASE_URL}/ai/signals?${params}`);
  
  if (!response.ok) {
    throw new Error('Failed to get AI signals');
  }
  
  return response.json();
}

/**
 * Get portfolio analysis
 */
export async function analyzePortfolio(holdings) {
  const response = await fetch(`${BASE_URL}/ai/portfolio/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ holdings })
  });
  
  if (!response.ok) {
    throw new Error('Failed to analyze portfolio');
  }
  
  return response.json();
}

/**
 * Get rebalancing recommendations
 */
export async function getRebalancingRecommendations(holdings, targetAllocations) {
  const response = await fetch(`${BASE_URL}/ai/portfolio/rebalance`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ holdings, target_allocations: targetAllocations })
  });
  
  if (!response.ok) {
    throw new Error('Failed to get rebalancing recommendations');
  }
  
  return response.json();
}

/**
 * Get chart data with indicators
 */
export async function getChartData(token, timeframe = '1h', indicators = []) {
  const params = new URLSearchParams({
    token,
    timeframe,
    ...(indicators.length && { indicators: indicators.join(',') })
  });
  
  const response = await fetch(`${BASE_URL}/charts/data?${params}`);
  
  if (!response.ok) {
    throw new Error('Failed to get chart data');
  }
  
  return response.json();
}

/**
 * Send a message to AI chat assistant
 */
export async function sendChatMessage(message, sessionId = 'default', includeMarketData = true) {
  const response = await fetch(`${API_BASE_URL}/ai-chat/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      session_id: sessionId,
      include_market_data: includeMarketData
    })
  });
  
  if (!response.ok) {
    throw new Error('Failed to send chat message');
  }
  
  return response.json();
}

/**
 * Clear chat history for a session
 */
export async function clearChatHistory(sessionId = 'default') {
  const response = await fetch(`${API_BASE_URL}/ai-chat/clear-history`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId })
  });
  
  if (!response.ok) {
    throw new Error('Failed to clear chat history');
  }
  
  return response.json();
}

export default {
  getSignals,
  analyzePortfolio,
  getRebalancingRecommendations,
  getChartData,
  sendChatMessage,
  clearChatHistory
};
