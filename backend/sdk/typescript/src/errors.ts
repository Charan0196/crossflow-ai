/**
 * Error classes for CrossFlow AI SDK
 */

export class CrossFlowError extends Error {
  constructor(message: string, public code?: string) {
    super(message);
    this.name = 'CrossFlowError';
  }
}

export class AuthenticationError extends CrossFlowError {
  constructor(message: string = 'Authentication failed') {
    super(message, 'AUTHENTICATION_ERROR');
    this.name = 'AuthenticationError';
  }
}

export class RateLimitError extends CrossFlowError {
  constructor(message: string = 'Rate limit exceeded') {
    super(message, 'RATE_LIMIT_ERROR');
    this.name = 'RateLimitError';
  }
}

export class ValidationError extends CrossFlowError {
  constructor(message: string, public details?: any) {
    super(message, 'VALIDATION_ERROR');
    this.name = 'ValidationError';
  }
}

export class NetworkError extends CrossFlowError {
  constructor(message: string = 'Network error') {
    super(message, 'NETWORK_ERROR');
    this.name = 'NetworkError';
  }
}

export class WebSocketError extends CrossFlowError {
  constructor(message: string = 'WebSocket error') {
    super(message, 'WEBSOCKET_ERROR');
    this.name = 'WebSocketError';
  }
}