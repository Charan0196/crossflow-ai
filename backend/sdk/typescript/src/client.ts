/**
 * Main CrossFlow AI SDK Client
 */

import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import { IntentManager } from './intent-manager';
import { WebSocketClient } from './websocket';
import { CrossFlowError, AuthenticationError, RateLimitError } from './errors';
import { ClientConfig, AuthResponse, LoginRequest } from './types';

export class CrossFlowClient {
  private http: AxiosInstance;
  private _token?: string;
  private _intentManager?: IntentManager;
  private _websocket?: WebSocketClient;

  constructor(private config: ClientConfig) {
    this.http = axios.create({
      baseURL: config.apiUrl,
      timeout: config.timeout || 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this._token = config.token;
    this.setupInterceptors();
  }

  private setupInterceptors(): void {
    // Request interceptor to add auth token
    this.http.interceptors.request.use((config) => {
      if (this._token) {
        config.headers.Authorization = `Bearer ${this._token}`;
      }
      return config;
    });

    // Response interceptor for error handling
    this.http.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response) {
          const status = error.response.status;
          const data = error.response.data;

          switch (status) {
            case 401:
              throw new AuthenticationError('Authentication failed');
            case 429:
              throw new RateLimitError('Rate limit exceeded');
            case 422:
              throw new CrossFlowError(`Validation error: ${JSON.stringify(data.detail)}`);
            default:
              throw new CrossFlowError(`API error: ${data.detail || error.message}`);
          }
        }
        throw new CrossFlowError(`Network error: ${error.message}`);
      }
    );
  }

  /**
   * Authenticate with username and password
   */
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    try {
      const response = await this.http.post('/api/auth/login', credentials);
      const authResponse: AuthResponse = response.data;
      
      this._token = authResponse.accessToken;
      return authResponse;
    } catch (error) {
      throw new AuthenticationError('Login failed');
    }
  }

  /**
   * Set authentication token
   */
  setToken(token: string): void {
    this._token = token;
  }

  /**
   * Get current authentication token
   */
  getToken(): string | undefined {
    return this._token;
  }

  /**
   * Check API health
   */
  async health(): Promise<{ status: string }> {
    const response = await this.http.get('/health');
    return response.data;
  }

  /**
   * Get intent manager instance
   */
  get intents(): IntentManager {
    if (!this._intentManager) {
      this._intentManager = new IntentManager(this.http);
    }
    return this._intentManager;
  }

  /**
   * Get WebSocket client instance
   */
  get websocket(): WebSocketClient {
    if (!this._websocket) {
      if (!this._token) {
        throw new AuthenticationError('Token required for WebSocket connection');
      }
      
      const wsUrl = this.config.apiUrl.replace(/^http/, 'ws');
      this._websocket = new WebSocketClient(wsUrl, this._token);
    }
    return this._websocket;
  }

  /**
   * Make a custom API request
   */
  async request<T = any>(config: AxiosRequestConfig): Promise<T> {
    const response = await this.http.request(config);
    return response.data;
  }
}