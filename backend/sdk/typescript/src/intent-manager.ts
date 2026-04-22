/**
 * Intent Management Module
 */

import { AxiosInstance } from 'axios';
import {
  Intent,
  IntentCreateRequest,
  IntentStatus,
  IntentListResponse,
  IntentListOptions,
  IntentEstimate
} from './types';

export class IntentManager {
  constructor(private http: AxiosInstance) {}

  /**
   * Create a new trading intent
   */
  async create(request: IntentCreateRequest): Promise<Intent> {
    const response = await this.http.post('/api/intents', request);
    return response.data;
  }

  /**
   * Get intent by ID
   */
  async get(intentId: string): Promise<Intent> {
    const response = await this.http.get(`/api/intents/${intentId}`);
    return response.data;
  }

  /**
   * Get intent status and progress
   */
  async getStatus(intentId: string): Promise<IntentStatus> {
    const response = await this.http.get(`/api/intents/${intentId}/status`);
    return response.data;
  }

  /**
   * List user's intents with optional filtering
   */
  async list(options: IntentListOptions = {}): Promise<IntentListResponse> {
    const params = new URLSearchParams();
    
    if (options.page) params.append('page', options.page.toString());
    if (options.pageSize) params.append('page_size', options.pageSize.toString());
    if (options.status) params.append('status', options.status);
    if (options.sourceChain) params.append('source_chain', options.sourceChain.toString());
    if (options.destinationChain) params.append('destination_chain', options.destinationChain.toString());

    const response = await this.http.get(`/api/intents?${params.toString()}`);
    return response.data;
  }

  /**
   * Cancel a pending intent
   */
  async cancel(intentId: string): Promise<{ message: string; intentId: string }> {
    const response = await this.http.delete(`/api/intents/${intentId}`);
    return response.data;
  }

  /**
   * Get updated cost and time estimates for an intent
   */
  async getEstimate(intentId: string): Promise<IntentEstimate> {
    const response = await this.http.get(`/api/intents/${intentId}/estimate`);
    return response.data;
  }

  /**
   * Wait for intent completion with polling
   */
  async waitForCompletion(
    intentId: string,
    options: {
      pollInterval?: number;
      timeout?: number;
      onStatusUpdate?: (status: IntentStatus) => void;
    } = {}
  ): Promise<IntentStatus> {
    const pollInterval = options.pollInterval || 5000; // 5 seconds
    const timeout = options.timeout || 300000; // 5 minutes
    const startTime = Date.now();

    return new Promise((resolve, reject) => {
      const poll = async () => {
        try {
          if (Date.now() - startTime > timeout) {
            reject(new Error('Timeout waiting for intent completion'));
            return;
          }

          const status = await this.getStatus(intentId);
          
          if (options.onStatusUpdate) {
            options.onStatusUpdate(status);
          }

          if (status.status === 'completed' || status.status === 'failed') {
            resolve(status);
            return;
          }

          setTimeout(poll, pollInterval);
        } catch (error) {
          reject(error);
        }
      };

      poll();
    });
  }
}