/**
 * Phase 5: WebSocket Client Service
 * 
 * Handles real-time connections for:
 * - Price updates
 * - Transaction status
 * - Order updates
 * - AI signal notifications
 */

import { API_BASE_URL } from '../config/api';

class WebSocketService {
  constructor() {
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 10;
    this.baseReconnectDelay = 1000; // Start at 1 second
    this.maxReconnectDelay = 60000; // Max 60 seconds
    this.listeners = new Map();
    this.subscriptions = new Set();
    this.isConnected = false;
    this.connectionStatus = 'disconnected'; // disconnected, connecting, connected, reconnecting
    this.statusListeners = [];
    this.userId = 'anonymous';
  }

  /**
   * Connect to the WebSocket server
   */
  connect(userId = 'anonymous') {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      return Promise.resolve();
    }

    this.userId = userId;
    this.setConnectionStatus('connecting');

    return new Promise((resolve, reject) => {
      const wsUrl = API_BASE_URL.replace('http', 'ws') + `/ws/${userId}`;
      
      try {
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.isConnected = true;
          this.reconnectAttempts = 0;
          this.setConnectionStatus('connected');
          
          // Resubscribe to previous subscriptions
          this.subscriptions.forEach(topic => {
            this.subscribe(topic);
          });
          
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (err) {
            console.error('Failed to parse WebSocket message:', err);
          }
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          reject(error);
        };

        this.ws.onclose = () => {
          console.log('WebSocket disconnected');
          this.isConnected = false;
          this.setConnectionStatus('disconnected');
          this.attemptReconnect();
        };
      } catch (err) {
        this.setConnectionStatus('disconnected');
        reject(err);
      }
    });
  }

  /**
   * Disconnect from WebSocket
   */
  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.isConnected = false;
  }

  /**
   * Attempt to reconnect with exponential backoff
   */
  attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('Max reconnect attempts reached');
      this.setConnectionStatus('disconnected');
      return;
    }

    this.reconnectAttempts++;
    this.setConnectionStatus('reconnecting');
    
    // Exponential backoff: 1s, 2s, 4s, 8s, 16s, max 60s
    const delay = Math.min(
      this.baseReconnectDelay * Math.pow(2, this.reconnectAttempts - 1),
      this.maxReconnectDelay
    );
    
    console.log(`Reconnecting in ${delay/1000}s... Attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
    
    setTimeout(() => {
      this.connect(this.userId).catch(err => {
        console.error('Reconnection failed:', err);
      });
    }, delay);
  }

  /**
   * Set connection status and notify listeners
   */
  setConnectionStatus(status) {
    this.connectionStatus = status;
    this.statusListeners.forEach(callback => {
      try {
        callback(status);
      } catch (err) {
        console.error('Status listener error:', err);
      }
    });
  }

  /**
   * Listen to connection status changes
   */
  onStatusChange(callback) {
    this.statusListeners.push(callback);
    // Immediately call with current status
    callback(this.connectionStatus);
    
    // Return unsubscribe function
    return () => {
      const index = this.statusListeners.indexOf(callback);
      if (index > -1) {
        this.statusListeners.splice(index, 1);
      }
    };
  }

  /**
   * Get current connection status
   */
  getStatus() {
    return this.connectionStatus;
  }

  /**
   * Handle incoming messages
   */
  handleMessage(message) {
    const { type, data, timestamp } = message;
    
    // Notify all listeners for this message type
    const typeListeners = this.listeners.get(type) || [];
    typeListeners.forEach(callback => {
      try {
        callback(data, timestamp);
      } catch (err) {
        console.error('Listener error:', err);
      }
    });

    // Notify wildcard listeners
    const wildcardListeners = this.listeners.get('*') || [];
    wildcardListeners.forEach(callback => {
      try {
        callback(message);
      } catch (err) {
        console.error('Wildcard listener error:', err);
      }
    });
  }

  /**
   * Subscribe to a topic
   */
  subscribe(topic) {
    this.subscriptions.add(topic);
    
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'subscribe',
        topic: topic
      }));
    }
  }

  /**
   * Unsubscribe from a topic
   */
  unsubscribe(topic) {
    this.subscriptions.delete(topic);
    
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'unsubscribe',
        topic: topic
      }));
    }
  }

  /**
   * Add event listener
   */
  on(type, callback) {
    if (!this.listeners.has(type)) {
      this.listeners.set(type, []);
    }
    this.listeners.get(type).push(callback);
    
    // Return unsubscribe function
    return () => {
      const listeners = this.listeners.get(type);
      const index = listeners.indexOf(callback);
      if (index > -1) {
        listeners.splice(index, 1);
      }
    };
  }

  /**
   * Remove event listener
   */
  off(type, callback) {
    const listeners = this.listeners.get(type);
    if (listeners) {
      const index = listeners.indexOf(callback);
      if (index > -1) {
        listeners.splice(index, 1);
      }
    }
  }

  /**
   * Send a message
   */
  send(type, data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, data }));
    }
  }
}

// Singleton instance
export const wsService = new WebSocketService();

// Message types
export const MessageTypes = {
  PRICE_UPDATE: 'price_update',
  TRANSACTION_STATUS: 'transaction_status',
  ORDER_UPDATE: 'order_update',
  AI_SIGNAL: 'ai_signal',
  PORTFOLIO_UPDATE: 'portfolio_update',
  NOTIFICATION: 'notification',
  ERROR: 'error',
  HEARTBEAT: 'heartbeat'
};

export default wsService;
