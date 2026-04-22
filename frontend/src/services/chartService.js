// Live Chart Data Service with Real Candlestick Data
class ChartService {
  constructor() {
    this.baseUrl = 'https://api.coingecko.com/api/v3';
    this.binanceUrl = 'https://api.binance.com/api/v3';
    this.cache = new Map();
    this.cacheTimeout = 60000; // 1 minute cache
  }

  // Get live candlestick data for charts
  async getCandlestickData(symbol = 'bitcoin', vs_currency = 'usd', days = 1) {
    try {
      const cacheKey = `${symbol}_${vs_currency}_${days}`;
      const cached = this.cache.get(cacheKey);
      
      if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
        return cached.data;
      }

      // Get OHLC data from CoinGecko
      const response = await fetch(
        `${this.baseUrl}/coins/${symbol}/ohlc?vs_currency=${vs_currency}&days=${days}`
      );
      
      if (!response.ok) {
        throw new Error('Failed to fetch OHLC data');
      }

      const ohlcData = await response.json();
      
      // Transform data for chart consumption
      const chartData = ohlcData.map((item, index) => {
        const [timestamp, open, high, low, close] = item;
        return {
          time: timestamp,
          open: parseFloat(open.toFixed(2)),
          high: parseFloat(high.toFixed(2)),
          low: parseFloat(low.toFixed(2)),
          close: parseFloat(close.toFixed(2)),
          volume: Math.random() * 1000000 + 500000, // Mock volume data
          name: index.toString()
        };
      });

      // Cache the result
      this.cache.set(cacheKey, {
        data: chartData,
        timestamp: Date.now()
      });

      return chartData;
    } catch (error) {
      console.error('Error fetching candlestick data:', error);
      return this.generateMockCandlestickData(days);
    }
  }

  // Get real-time price data for multiple timeframes
  async getRealTimeData(symbol = 'BTCUSDT', interval = '1h', limit = 100) {
    try {
      // Use Binance API for real-time data (no API key required for public endpoints)
      const response = await fetch(
        `${this.binanceUrl}/klines?symbol=${symbol}&interval=${interval}&limit=${limit}`
      );

      if (!response.ok) {
        throw new Error('Failed to fetch real-time data');
      }

      const klineData = await response.json();
      
      return klineData.map((kline, index) => {
        const [
          openTime, open, high, low, close, volume,
          closeTime, quoteVolume, trades, buyBaseVolume, buyQuoteVolume
        ] = kline;

        return {
          time: parseInt(openTime),
          open: parseFloat(open),
          high: parseFloat(high),
          low: parseFloat(low),
          close: parseFloat(close),
          volume: parseFloat(volume),
          name: index.toString(),
          timestamp: new Date(parseInt(openTime)).toLocaleTimeString()
        };
      });
    } catch (error) {
      console.error('Error fetching real-time data:', error);
      return this.generateMockCandlestickData();
    }
  }

  // Generate realistic mock candlestick data
  generateMockCandlestickData(days = 1) {
    const dataPoints = days * 24; // Hourly data
    const basePrice = 67890; // Starting BTC price
    const data = [];
    let currentPrice = basePrice;

    for (let i = 0; i < dataPoints; i++) {
      const volatility = 0.02; // 2% volatility
      const change = (Math.random() - 0.5) * volatility;
      
      const open = currentPrice;
      const close = open * (1 + change);
      const high = Math.max(open, close) * (1 + Math.random() * 0.01);
      const low = Math.min(open, close) * (1 - Math.random() * 0.01);
      
      data.push({
        time: Date.now() - (dataPoints - i) * 3600000, // Hourly intervals
        open: parseFloat(open.toFixed(2)),
        high: parseFloat(high.toFixed(2)),
        low: parseFloat(low.toFixed(2)),
        close: parseFloat(close.toFixed(2)),
        volume: Math.random() * 1000000 + 500000,
        name: i.toString(),
        timestamp: new Date(Date.now() - (dataPoints - i) * 3600000).toLocaleTimeString()
      });

      currentPrice = close;
    }

    return data;
  }

  // Get market depth data
  async getMarketDepth(symbol = 'BTCUSDT') {
    try {
      const response = await fetch(
        `${this.binanceUrl}/depth?symbol=${symbol}&limit=20`
      );

      if (!response.ok) {
        throw new Error('Failed to fetch market depth');
      }

      const depthData = await response.json();
      
      return {
        bids: depthData.bids.map(([price, quantity]) => ({
          price: parseFloat(price),
          quantity: parseFloat(quantity),
          total: parseFloat(price) * parseFloat(quantity)
        })),
        asks: depthData.asks.map(([price, quantity]) => ({
          price: parseFloat(price),
          quantity: parseFloat(quantity),
          total: parseFloat(price) * parseFloat(quantity)
        }))
      };
    } catch (error) {
      console.error('Error fetching market depth:', error);
      return this.generateMockDepthData();
    }
  }

  generateMockDepthData() {
    const basePrice = 67890;
    const bids = [];
    const asks = [];

    // Generate bid orders (below current price)
    for (let i = 0; i < 10; i++) {
      const price = basePrice - (i + 1) * 50;
      const quantity = Math.random() * 5 + 0.1;
      bids.push({
        price: parseFloat(price.toFixed(2)),
        quantity: parseFloat(quantity.toFixed(4)),
        total: parseFloat((price * quantity).toFixed(2))
      });
    }

    // Generate ask orders (above current price)
    for (let i = 0; i < 10; i++) {
      const price = basePrice + (i + 1) * 50;
      const quantity = Math.random() * 5 + 0.1;
      asks.push({
        price: parseFloat(price.toFixed(2)),
        quantity: parseFloat(quantity.toFixed(4)),
        total: parseFloat((price * quantity).toFixed(2))
      });
    }

    return { bids, asks };
  }

  // Get trading volume data
  async getVolumeData(symbol = 'bitcoin', days = 7) {
    try {
      const response = await fetch(
        `${this.baseUrl}/coins/${symbol}/market_chart?vs_currency=usd&days=${days}`
      );

      if (!response.ok) {
        throw new Error('Failed to fetch volume data');
      }

      const data = await response.json();
      
      return data.total_volumes.map(([timestamp, volume]) => ({
        time: timestamp,
        volume: volume,
        date: new Date(timestamp).toLocaleDateString()
      }));
    } catch (error) {
      console.error('Error fetching volume data:', error);
      return this.generateMockVolumeData(days);
    }
  }

  generateMockVolumeData(days = 7) {
    const data = [];
    const baseVolume = 28500000000; // Base 24h volume

    for (let i = 0; i < days; i++) {
      const volume = baseVolume * (0.8 + Math.random() * 0.4); // ±20% variation
      data.push({
        time: Date.now() - (days - i) * 24 * 60 * 60 * 1000,
        volume: volume,
        date: new Date(Date.now() - (days - i) * 24 * 60 * 60 * 1000).toLocaleDateString()
      });
    }

    return data;
  }

  // Get technical indicators
  calculateTechnicalIndicators(data) {
    if (!data || data.length < 14) return null;

    const closes = data.map(d => d.close);
    
    return {
      sma20: this.calculateSMA(closes, 20),
      sma50: this.calculateSMA(closes, 50),
      rsi: this.calculateRSI(closes, 14),
      macd: this.calculateMACD(closes),
      bollinger: this.calculateBollingerBands(closes, 20, 2)
    };
  }

  calculateSMA(data, period) {
    if (data.length < period) return null;
    const sum = data.slice(-period).reduce((a, b) => a + b, 0);
    return sum / period;
  }

  calculateRSI(data, period = 14) {
    if (data.length < period + 1) return 50;

    let gains = 0;
    let losses = 0;

    for (let i = data.length - period; i < data.length; i++) {
      const change = data[i] - data[i - 1];
      if (change > 0) gains += change;
      else losses -= change;
    }

    const avgGain = gains / period;
    const avgLoss = losses / period;
    const rs = avgGain / avgLoss;
    
    return 100 - (100 / (1 + rs));
  }

  calculateMACD(data) {
    const ema12 = this.calculateEMA(data, 12);
    const ema26 = this.calculateEMA(data, 26);
    
    if (!ema12 || !ema26) return null;
    
    return {
      macd: ema12 - ema26,
      signal: this.calculateEMA([ema12 - ema26], 9),
      histogram: (ema12 - ema26) - this.calculateEMA([ema12 - ema26], 9)
    };
  }

  calculateEMA(data, period) {
    if (data.length < period) return null;
    
    const multiplier = 2 / (period + 1);
    let ema = data[0];
    
    for (let i = 1; i < data.length; i++) {
      ema = (data[i] * multiplier) + (ema * (1 - multiplier));
    }
    
    return ema;
  }

  calculateBollingerBands(data, period = 20, stdDev = 2) {
    if (data.length < period) return null;
    
    const sma = this.calculateSMA(data, period);
    const recentData = data.slice(-period);
    
    const variance = recentData.reduce((sum, price) => {
      return sum + Math.pow(price - sma, 2);
    }, 0) / period;
    
    const standardDeviation = Math.sqrt(variance);
    
    return {
      upper: sma + (standardDeviation * stdDev),
      middle: sma,
      lower: sma - (standardDeviation * stdDev)
    };
  }

  // Clear cache
  clearCache() {
    this.cache.clear();
  }
}

export const chartService = new ChartService();