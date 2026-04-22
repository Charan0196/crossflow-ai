/**
 * WebSocket Client for Real-time Communication
 */

import WebSocket from 'ws';
import { EventEmitter } from 'eventemitter3';
import { WebSocketMessage, WebSocketConfig, WebSocketEventType, PriceData } from './types';

export class WebSocketClient extends EventEmitter {
  private ws?: WebSocket;
  private reconnectAttempts = 0;
  private isConnecting = false;
  private heartbeatInterval?: NodeJS.Timeout;
  private reconnectTimeout?: NodeJS.Timeout;

  constructor(
    private baseUrl: string,
    private token: string,
    private config: WebSocketConfig = {}
  ) {
    super();
    
    // Default configuration
    this.config = {
      reconnect: true,
      reconnectInterval: 5000,
      maxReconnectAttempts: 10,
      heartbeatInterval: 30000,
      ...config
    };
  }

  /**
   * Connect to WebSocket server
   */
  async connect(endpoint: string = '/api/ws/general'): Promise<void> {
    if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.OPEN)) {
      return;
    }

    this.isConnecting = true;
    const url = `${this.baseUrl}${endpoint}?token=${this.token}`;

    try {
      this.ws = new WebSocket(url);
      this.setupEventHandlers();
      
      return new Promise((resolve, reject) => {
        const onOpen = () => {
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          this.startHeartbeat();
          this.emit('connect');
          resolve();
        };

        const onError = (error: Error) => {
          this.isConnecting = false;
          this.emit('error', error);
          reject(error);
        };

        this.ws!.once('open', onOpen);
        this.ws!.once('error', onError);
      });
    } catch (error) {
      this.isConnecting = false;
      throw error;
    }
  }

  /**
   * Connect to intent updates WebSocket
   */
  async connectToIntentUpdates(): Promise<void> {
    return this.connect('/api/ws/intents');
  }

  /**
   * Connect to price feeds WebSocket
   */
  async connectToPriceFeeds(pairs?: string[]): Promise<void> {
    const endpoint = pairs 
      ? `/api/ws/prices?pairs=${pairs.join(',')}`
      : '/api/ws/prices';
    return this.connect(endpoint);
  }

  /**
   * Disconnect from WebSocket
   */
  disconnect(): void {
    this.stopHeartbeat();
    this.clearReconnectTimeout();
    
    if (this.ws) {
      this.ws.close();
      this.ws = undefined;
    }
  }

  /**
   * Send message to server
   */
  send(message: any): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket not connected');
    }

    this.ws.send(JSON.stringify(message));
  }

  /**
   * Subscribe to a topic
   */
  subscribeToTopic(topic: string): void {
    this.send({
      type: 'subscribe',
      data: { topic }
    });
  }

  /**
   * Unsubscribe from a topic
   */
  unsubscribeFromTopic(topic: string): void {
    this.send({
      type: 'unsubscribe',
      data: { topic }
    });
  }

  /**
   * Subscribe to intent updates for a specific intent
   */
  subscribeToIntentUpdates(intentId: string): void {
    this.send({
      type: 'intent_subscribe',
      data: { intent_id: intentId }
    });
  }

  /**
   * Subscribe to price updates for specific token pairs
   */
  subscribeToPriceFeeds(tokenPairs: string[]): void {
    tokenPairs.forEach(pair => {
      this.send({
        type: 'price_subscribe',
        data: { token_pair: pair }
      });
    });
  }

  /**
   * Check if WebSocket is connected
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  private setupEventHandlers(): void {
    if (!this.ws) return;

    this.ws.on('open', () => {
      this.emit('connect');
    });

    this.ws.on('close', (code, reason) => {
      this.stopHeartbeat();
      this.emit('disconnect', { code, reason: reason.toString() });
      
      if (this.config.reconnect && this.reconnectAttempts < this.config.maxReconnectAttempts!) {
        this.scheduleReconnect();
      }
    });

    this.ws.on('error', (error) => {
      this.emit('error', error);
    });

    this.ws.on('message', (data) => {
      try {
        const message: WebSocketMessage = JSON.parse(data.toString());
        this.handleMessage(message);
      } catch (error) {
        this.emit('error', new Error('Failed to parse WebSocket message'));
      }
    });
  }

  private handleMessage(message: WebSocketMessage): void {
    this.emit('message', message);

    // Emit specific event types
    switch (message.type) {
      case 'intent_status_update':
        this.emit('intentStatusUpdate', message.data);
        break;
      case 'price_update':
        this.emit('priceUpdate', message.data);
        break;
      case 'solver_bid_update':
        this.emit('solverBidUpdate', message.data);
        break;
      case 'system_notification':
        this.emit('systemNotification', message.data);
        break;
      case 'heartbeat':
        this.emit('heartbeat', message.data);
        // Respond to heartbeat
        this.send({ type: 'heartbeat', data: {} });
        break;
      case 'error':
        this.emit('error', new Error(message.data.error));
        break;
    }
  }

  private startHeartbeat(): void {
    if (this.config.heartbeatInterval) {
      this.heartbeatInterval = setInterval(() => {
        if (this.isConnected()) {
          this.send({ type: 'heartbeat', data: {} });
        }
      }, this.config.heartbeatInterval);
    }
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = undefined;
    }
  }

  private scheduleReconnect(): void {
    this.reconnectAttempts++;
    const delay = Math.min(
      this.config.reconnectInterval! * Math.pow(2, this.reconnectAttempts - 1),
      30000 // Max 30 seconds
    );

    this.reconnectTimeout = setTimeout(() => {
      this.connect().catch(() => {
        // Reconnection failed, will try again if under max attempts
      });
    }, delay);
  }

  private clearReconnectTimeout(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = undefined;
    }
  }
}