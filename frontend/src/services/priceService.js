import axios from 'axios'

class PriceService {
  constructor() {
    this.coingeckoAPI = axios.create({
      baseURL: 'https://api.coingecko.com/api/v3',
      headers: {
        'x-cg-demo-api-key': import.meta.env.VITE_COINGECKO_API_KEY
      }
    })

    this.binanceAPI = axios.create({
      baseURL: 'https://api.binance.com/api/v3'
    })

    // Token mappings for popular cryptocurrencies
    this.tokenMappings = {
      'ethereum': { symbol: 'ETH', binanceSymbol: 'ETHUSDT' },
      'bitcoin': { symbol: 'BTC', binanceSymbol: 'BTCUSDT' },
      'binancecoin': { symbol: 'BNB', binanceSymbol: 'BNBUSDT' },
      'solana': { symbol: 'SOL', binanceSymbol: 'SOLUSDT' },
      'cardano': { symbol: 'ADA', binanceSymbol: 'ADAUSDT' },
      'polygon': { symbol: 'MATIC', binanceSymbol: 'MATICUSDT' },
      'chainlink': { symbol: 'LINK', binanceSymbol: 'LINKUSDT' },
      'uniswap': { symbol: 'UNI', binanceSymbol: 'UNIUSDT' },
      'avalanche-2': { symbol: 'AVAX', binanceSymbol: 'AVAXUSDT' },
      'polkadot': { symbol: 'DOT', binanceSymbol: 'DOTUSDT' }
    }
  }

  // Get live prices from CoinGecko
  async getLivePrices(tokenIds = ['ethereum', 'bitcoin', 'binancecoin', 'solana', 'cardano', 'polygon']) {
    try {
      const response = await this.coingeckoAPI.get('/simple/price', {
        params: {
          ids: tokenIds.join(','),
          vs_currencies: 'usd',
          include_24hr_change: true,
          include_24hr_vol: true,
          include_market_cap: true
        }
      })
      return response.data
    } catch (error) {
      console.error('Error fetching CoinGecko prices:', error)
      return null
    }
  }

  // Get trending coins
  async getTrendingCoins() {
    try {
      const response = await this.coingeckoAPI.get('/search/trending')
      return response.data.coins
    } catch (error) {
      console.error('Error fetching trending coins:', error)
      return []
    }
  }

  // Get market data from CoinGecko
  async getMarketData(page = 1, perPage = 50) {
    try {
      const response = await this.coingeckoAPI.get('/coins/markets', {
        params: {
          vs_currency: 'usd',
          order: 'market_cap_desc',
          per_page: perPage,
          page: page,
          sparkline: true,
          price_change_percentage: '1h,24h,7d'
        }
      })
      return response.data
    } catch (error) {
      console.error('Error fetching market data:', error)
      return []
    }
  }

  // Get historical data for charts
  async getHistoricalData(coinId, days = 7) {
    try {
      const response = await this.coingeckoAPI.get(`/coins/${coinId}/market_chart`, {
        params: {
          vs_currency: 'usd',
          days: days,
          interval: days <= 1 ? 'hourly' : 'daily'
        }
      })
      return response.data
    } catch (error) {
      console.error('Error fetching historical data:', error)
      return null
    }
  }

  // Get Binance ticker data for real-time updates
  async getBinanceTickers() {
    try {
      const response = await this.binanceAPI.get('/ticker/24hr')
      return response.data
    } catch (error) {
      console.error('Error fetching Binance tickers:', error)
      return []
    }
  }

  // Get specific token price from Binance
  async getBinancePrice(symbol) {
    try {
      const response = await this.binanceAPI.get('/ticker/price', {
        params: { symbol }
      })
      return parseFloat(response.data.price)
    } catch (error) {
      console.error(`Error fetching Binance price for ${symbol}:`, error)
      return null
    }
  }

  // Get DeFi protocols data
  async getDeFiProtocols() {
    try {
      const response = await this.coingeckoAPI.get('/coins/markets', {
        params: {
          vs_currency: 'usd',
          category: 'decentralized-finance-defi',
          order: 'market_cap_desc',
          per_page: 20,
          page: 1,
          sparkline: false,
          price_change_percentage: '24h'
        }
      })
      return response.data
    } catch (error) {
      console.error('Error fetching DeFi protocols:', error)
      return []
    }
  }

  // Format price with appropriate decimals
  formatPrice(price) {
    if (price >= 1000) {
      return `$${price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
    } else if (price >= 1) {
      return `$${price.toFixed(4)}`
    } else {
      return `$${price.toFixed(6)}`
    }
  }

  // Format market cap
  formatMarketCap(marketCap) {
    if (marketCap >= 1e12) {
      return `$${(marketCap / 1e12).toFixed(2)}T`
    } else if (marketCap >= 1e9) {
      return `$${(marketCap / 1e9).toFixed(2)}B`
    } else if (marketCap >= 1e6) {
      return `$${(marketCap / 1e6).toFixed(2)}M`
    } else {
      return `$${marketCap.toLocaleString()}`
    }
  }

  // Format volume
  formatVolume(volume) {
    return this.formatMarketCap(volume)
  }

  // Format percentage change
  formatPercentChange(change) {
    const formatted = Math.abs(change).toFixed(2)
    return change >= 0 ? `+${formatted}%` : `-${formatted}%`
  }
}

export const priceService = new PriceService()
export default priceService