"""
Market Intelligence Engine
Provides comprehensive market analysis including trend analysis, arbitrage detection,
volatility measurement, and market sentiment analysis.
"""
import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import redis

from ..config import AIConfig, AgentConfig, AgentType
from ..utils.model_manager import ModelManager


class TrendDirection(Enum):
    """Market trend directions"""
    BULLISH = "bullish"
    BEARISH = "bearish"
    SIDEWAYS = "sideways"
    UNKNOWN = "unknown"


class MarketRegime(Enum):
    """Market volatility regimes"""
    LOW_VOLATILITY = "low_vol"
    NORMAL_VOLATILITY = "normal_vol"
    HIGH_VOLATILITY = "high_vol"
    EXTREME_VOLATILITY = "extreme_vol"


@dataclass
class TechnicalIndicators:
    """Technical analysis indicators"""
    sma_20: float = 0.0
    sma_50: float = 0.0
    sma_200: float = 0.0
    ema_12: float = 0.0
    ema_26: float = 0.0
    rsi: float = 50.0
    macd: float = 0.0
    macd_signal: float = 0.0
    macd_histogram: float = 0.0
    bollinger_upper: float = 0.0
    bollinger_lower: float = 0.0
    bollinger_middle: float = 0.0
    atr: float = 0.0
    volume_sma: float = 0.0


@dataclass
class MarketAnalysis:
    """Comprehensive market analysis result"""
    asset: str
    chain: str
    timestamp: datetime
    price: float
    volume: float
    
    # Technical indicators
    indicators: TechnicalIndicators
    
    # Trend analysis
    trend_direction: TrendDirection
    trend_strength: float  # 0-1 scale
    trend_confidence: float  # 0-1 scale
    
    # Volatility analysis
    volatility: float
    volatility_regime: MarketRegime
    volatility_percentile: float  # Historical percentile
    
    # Volume analysis
    volume_profile: Dict[str, float]
    volume_trend: TrendDirection
    relative_volume: float  # Compared to average
    
    # Market sentiment
    sentiment_score: float  # -1 to 1 scale
    sentiment_confidence: float  # 0-1 scale
    
    # Overall confidence
    analysis_confidence: float = 0.0


@dataclass
class ArbitrageOpportunity:
    """Cross-chain arbitrage opportunity"""
    asset: str
    source_chain: str
    target_chain: str
    source_price: float
    target_price: float
    price_difference: float
    price_difference_pct: float
    estimated_profit: float
    estimated_costs: float
    net_profit: float
    profit_margin: float
    confidence_score: float
    timestamp: datetime
    expiry_estimate: datetime


@dataclass
class MarketAlert:
    """Market alert notification"""
    alert_id: str
    asset: str
    chain: str
    alert_type: str
    severity: str  # low, medium, high, critical
    message: str
    data: Dict[str, Any]
    timestamp: datetime
    expires_at: Optional[datetime] = None


class MarketIntelligenceEngine:
    """
    AI-powered market intelligence engine that provides comprehensive market analysis,
    arbitrage detection, and real-time market monitoring.
    """
    
    def __init__(self, config: AIConfig, agent_config: AgentConfig, model_manager: ModelManager):
        self.config = config
        self.agent_config = agent_config
        self.model_manager = model_manager
        self.logger = logging.getLogger(__name__)
        
        # Redis for caching and real-time data
        self.redis_client = redis.Redis(
            host=config.redis_host,
            port=config.redis_port,
            db=config.redis_db,
            decode_responses=True
        )
        
        # Thread pool for parallel processing
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Market data cache
        self.price_cache: Dict[str, List[Tuple[datetime, float]]] = {}
        self.volume_cache: Dict[str, List[Tuple[datetime, float]]] = {}
        
        # Alert system
        self.active_alerts: Dict[str, MarketAlert] = {}
        self.alert_thresholds: Dict[str, Dict[str, float]] = {}
        
        # Analysis cache
        self.analysis_cache: Dict[str, MarketAnalysis] = {}
        self.cache_ttl = agent_config.performance_config.get("cache_ttl", 60)
        
        self.logger.info("Market Intelligence Engine initialized")
    
    async def analyze_market(self, asset: str, chain: str, 
                           lookback_hours: int = 24) -> MarketAnalysis:
        """
        Perform comprehensive market analysis for an asset on a specific chain
        """
        cache_key = f"analysis:{asset}:{chain}"
        
        # Check cache first
        cached_analysis = self._get_cached_analysis(cache_key)
        if cached_analysis:
            return cached_analysis
        
        try:
            # Get market data
            price_data = await self._get_price_data(asset, chain, lookback_hours)
            volume_data = await self._get_volume_data(asset, chain, lookback_hours)
            
            if not price_data or not volume_data:
                raise ValueError(f"Insufficient data for {asset} on {chain}")
            
            # Calculate technical indicators
            indicators = self._calculate_technical_indicators(price_data, volume_data)
            
            # Analyze trend
            trend_direction, trend_strength, trend_confidence = self._analyze_trend(
                price_data, indicators
            )
            
            # Analyze volatility
            volatility, volatility_regime, volatility_percentile = self._analyze_volatility(
                price_data
            )
            
            # Analyze volume
            volume_profile, volume_trend, relative_volume = self._analyze_volume(
                volume_data, price_data
            )
            
            # Calculate market sentiment
            sentiment_score, sentiment_confidence = self._calculate_sentiment(
                price_data, volume_data, indicators
            )
            
            # Calculate overall confidence
            analysis_confidence = self._calculate_analysis_confidence(
                trend_confidence, sentiment_confidence, len(price_data)
            )
            
            # Create analysis result
            analysis = MarketAnalysis(
                asset=asset,
                chain=chain,
                timestamp=datetime.now(),
                price=price_data[-1][1],
                volume=volume_data[-1][1],
                indicators=indicators,
                trend_direction=trend_direction,
                trend_strength=trend_strength,
                trend_confidence=trend_confidence,
                volatility=volatility,
                volatility_regime=volatility_regime,
                volatility_percentile=volatility_percentile,
                volume_profile=volume_profile,
                volume_trend=volume_trend,
                relative_volume=relative_volume,
                sentiment_score=sentiment_score,
                sentiment_confidence=sentiment_confidence,
                analysis_confidence=analysis_confidence
            )
            
            # Cache the analysis
            self._cache_analysis(cache_key, analysis)
            
            self.logger.info(f"Completed market analysis for {asset} on {chain}")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Market analysis failed for {asset} on {chain}: {e}")
            raise
    
    def _calculate_technical_indicators(self, price_data: List[Tuple[datetime, float]], 
                                      volume_data: List[Tuple[datetime, float]]) -> TechnicalIndicators:
        """Calculate technical analysis indicators"""
        
        # Convert to pandas for easier calculation
        df = pd.DataFrame(price_data, columns=['timestamp', 'price'])
        df['volume'] = [v[1] for v in volume_data]
        df = df.set_index('timestamp')
        
        indicators = TechnicalIndicators()
        
        # Simple Moving Averages
        if len(df) >= 20:
            indicators.sma_20 = df['price'].rolling(20).mean().iloc[-1]
        if len(df) >= 50:
            indicators.sma_50 = df['price'].rolling(50).mean().iloc[-1]
        if len(df) >= 200:
            indicators.sma_200 = df['price'].rolling(200).mean().iloc[-1]
        
        # Exponential Moving Averages
        if len(df) >= 12:
            indicators.ema_12 = df['price'].ewm(span=12).mean().iloc[-1]
        if len(df) >= 26:
            indicators.ema_26 = df['price'].ewm(span=26).mean().iloc[-1]
        
        # RSI
        if len(df) >= 14:
            delta = df['price'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            indicators.rsi = 100 - (100 / (1 + rs)).iloc[-1]
        
        # MACD
        if len(df) >= 26:
            ema_12 = df['price'].ewm(span=12).mean()
            ema_26 = df['price'].ewm(span=26).mean()
            macd_line = ema_12 - ema_26
            signal_line = macd_line.ewm(span=9).mean()
            
            indicators.macd = macd_line.iloc[-1]
            indicators.macd_signal = signal_line.iloc[-1]
            indicators.macd_histogram = indicators.macd - indicators.macd_signal
        
        # Bollinger Bands
        if len(df) >= 20:
            sma_20 = df['price'].rolling(20).mean()
            std_20 = df['price'].rolling(20).std()
            indicators.bollinger_upper = (sma_20 + 2 * std_20).iloc[-1]
            indicators.bollinger_lower = (sma_20 - 2 * std_20).iloc[-1]
            indicators.bollinger_middle = sma_20.iloc[-1]
        
        # Average True Range (ATR)
        if len(df) >= 14:
            high = df['price'] * 1.001  # Approximate high
            low = df['price'] * 0.999   # Approximate low
            close = df['price']
            
            tr1 = high - low
            tr2 = abs(high - close.shift())
            tr3 = abs(low - close.shift())
            
            true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            indicators.atr = true_range.rolling(14).mean().iloc[-1]
        
        # Volume SMA
        if len(df) >= 20:
            indicators.volume_sma = df['volume'].rolling(20).mean().iloc[-1]
        
        return indicators
    
    def _analyze_trend(self, price_data: List[Tuple[datetime, float]], 
                      indicators: TechnicalIndicators) -> Tuple[TrendDirection, float, float]:
        """Analyze market trend direction and strength"""
        
        if len(price_data) < 2:
            return TrendDirection.SIDEWAYS, 0.0, 0.1  # Minimal confidence for insufficient data
        
        prices = [p[1] for p in price_data]
        
        # Calculate trend using multiple methods
        trend_signals = []
        
        # 1. Price momentum (use available data)
        lookback = min(len(prices) - 1, 20)  # Use up to 20 periods or available data
        if lookback > 0:
            price_change = (prices[-1] - prices[-lookback-1]) / prices[-lookback-1]
            if price_change > 0.02:  # 2% increase
                trend_signals.append(1)
            elif price_change < -0.02:  # 2% decrease
                trend_signals.append(-1)
            else:
                trend_signals.append(0)
        
        # 2. Moving average crossover (if available)
        if indicators.sma_20 > 0 and indicators.sma_50 > 0:
            if indicators.sma_20 > indicators.sma_50:
                trend_signals.append(1)
            elif indicators.sma_20 < indicators.sma_50:
                trend_signals.append(-1)
            else:
                trend_signals.append(0)
        
        # 3. MACD signal (if available)
        if indicators.macd != 0 and indicators.macd_signal != 0:
            if indicators.macd > indicators.macd_signal:
                trend_signals.append(1)
            elif indicators.macd < indicators.macd_signal:
                trend_signals.append(-1)
            else:
                trend_signals.append(0)
        
        # 4. RSI trend (if available)
        if indicators.rsi > 0:
            if indicators.rsi > 60:
                trend_signals.append(1)
            elif indicators.rsi < 40:
                trend_signals.append(-1)
            else:
                trend_signals.append(0)
        
        # 5. Simple linear trend for short data
        if len(prices) >= 3:
            # Calculate simple slope
            x = list(range(len(prices)))
            y = prices
            n = len(prices)
            
            sum_x = sum(x)
            sum_y = sum(y)
            sum_xy = sum(x[i] * y[i] for i in range(n))
            sum_x2 = sum(x[i] * x[i] for i in range(n))
            
            if n * sum_x2 - sum_x * sum_x != 0:  # Avoid division by zero
                slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
                avg_price = sum_y / n
                
                # Normalize slope by average price
                normalized_slope = slope / avg_price if avg_price > 0 else 0
                
                if normalized_slope > 0.001:  # 0.1% per period
                    trend_signals.append(1)
                elif normalized_slope < -0.001:
                    trend_signals.append(-1)
                else:
                    trend_signals.append(0)
        
        # Aggregate signals
        if not trend_signals:
            return TrendDirection.SIDEWAYS, 0.0, 0.1
        
        avg_signal = sum(trend_signals) / len(trend_signals)
        
        # Determine trend direction
        if avg_signal > 0.3:
            direction = TrendDirection.BULLISH
        elif avg_signal < -0.3:
            direction = TrendDirection.BEARISH
        else:
            direction = TrendDirection.SIDEWAYS
        
        # Calculate trend strength (0-1)
        strength = min(abs(avg_signal), 1.0)
        
        # Calculate confidence based on signal consistency and data availability
        if len(trend_signals) > 1:
            signal_consistency = 1.0 - (np.std(trend_signals) / 2.0)
        else:
            signal_consistency = 0.5
        
        # Adjust confidence based on data availability
        data_factor = min(len(price_data) / 20, 1.0)  # Full confidence with 20+ data points
        confidence = max(signal_consistency * data_factor, 0.1)  # Minimum 10% confidence
        
        return direction, strength, confidence
    
    def _analyze_volatility(self, price_data: List[Tuple[datetime, float]]) -> Tuple[float, MarketRegime, float]:
        """Analyze market volatility and regime"""
        
        if len(price_data) < 2:
            return 0.1, MarketRegime.NORMAL_VOLATILITY, 0.5  # Default minimal volatility
        
        prices = [p[1] for p in price_data]
        
        # Calculate returns
        returns = []
        for i in range(1, len(prices)):
            if prices[i-1] > 0:  # Avoid division by zero
                ret = (prices[i] - prices[i-1]) / prices[i-1]
                returns.append(ret)
        
        if not returns:
            return 0.1, MarketRegime.NORMAL_VOLATILITY, 0.5
        
        # Calculate volatility (annualized)
        if len(returns) == 1:
            volatility = abs(returns[0]) * np.sqrt(365 * 24)  # Single return case
        else:
            volatility = np.std(returns) * np.sqrt(365 * 24)  # Assuming hourly data
        
        # Ensure minimum volatility to avoid zero values
        volatility = max(volatility, 0.12)  # Minimum volatility in low range
        
        # Determine volatility regime with proper thresholds
        if volatility < 0.15:  # Adjusted threshold
            regime = MarketRegime.LOW_VOLATILITY
        elif volatility < 0.4:  # Adjusted threshold
            regime = MarketRegime.NORMAL_VOLATILITY
        elif volatility < 0.8:  # Adjusted threshold
            regime = MarketRegime.HIGH_VOLATILITY
        else:
            regime = MarketRegime.EXTREME_VOLATILITY
        
        # Calculate historical percentile (simplified)
        # In a real implementation, this would use historical volatility data
        if volatility < 0.1:
            percentile = 0.1
        elif volatility < 0.3:
            percentile = 0.4
        elif volatility < 0.6:
            percentile = 0.7
        elif volatility < 1.0:
            percentile = 0.9
        else:
            percentile = 0.95
        
        return volatility, regime, percentile
    
    def _analyze_volume(self, volume_data: List[Tuple[datetime, float]], 
                       price_data: List[Tuple[datetime, float]]) -> Tuple[Dict[str, float], TrendDirection, float]:
        """Analyze volume patterns and trends"""
        
        if len(volume_data) < 20:
            return {}, TrendDirection.UNKNOWN, 1.0
        
        volumes = [v[1] for v in volume_data]
        prices = [p[1] for p in price_data]
        
        # Volume profile (simplified)
        recent_volume = sum(volumes[-10:]) / 10
        historical_volume = sum(volumes[:-10]) / len(volumes[:-10]) if len(volumes) > 10 else recent_volume
        
        volume_profile = {
            "recent_avg": recent_volume,
            "historical_avg": historical_volume,
            "current": volumes[-1],
            "max_24h": max(volumes[-24:]) if len(volumes) >= 24 else max(volumes),
            "min_24h": min(volumes[-24:]) if len(volumes) >= 24 else min(volumes)
        }
        
        # Volume trend
        volume_change = (recent_volume - historical_volume) / historical_volume if historical_volume > 0 else 0
        
        if volume_change > 0.1:  # 10% increase
            volume_trend = TrendDirection.BULLISH
        elif volume_change < -0.1:  # 10% decrease
            volume_trend = TrendDirection.BEARISH
        else:
            volume_trend = TrendDirection.SIDEWAYS
        
        # Relative volume
        relative_volume = recent_volume / historical_volume if historical_volume > 0 else 1.0
        
        return volume_profile, volume_trend, relative_volume
    
    def _calculate_sentiment(self, price_data: List[Tuple[datetime, float]], 
                           volume_data: List[Tuple[datetime, float]], 
                           indicators: TechnicalIndicators) -> Tuple[float, float]:
        """Calculate market sentiment from price action"""
        
        if len(price_data) < 10:
            return 0.0, 0.0
        
        sentiment_factors = []
        
        # 1. Price momentum sentiment
        prices = [p[1] for p in price_data]
        short_momentum = (prices[-1] - prices[-5]) / prices[-5] if len(prices) >= 5 else 0
        long_momentum = (prices[-1] - prices[-20]) / prices[-20] if len(prices) >= 20 else 0
        
        momentum_sentiment = (short_momentum * 0.6 + long_momentum * 0.4) * 10  # Scale to -1 to 1
        sentiment_factors.append(np.clip(momentum_sentiment, -1, 1))
        
        # 2. RSI sentiment
        if indicators.rsi > 0:
            rsi_sentiment = (indicators.rsi - 50) / 50  # Convert to -1 to 1 scale
            sentiment_factors.append(np.clip(rsi_sentiment, -1, 1))
        
        # 3. MACD sentiment
        if indicators.macd_histogram != 0:
            # Normalize MACD histogram (simplified)
            macd_sentiment = np.tanh(indicators.macd_histogram * 100)  # Use tanh for bounded output
            sentiment_factors.append(macd_sentiment)
        
        # 4. Volume-price relationship
        volumes = [v[1] for v in volume_data]
        if len(volumes) >= 5:
            recent_vol_change = (volumes[-1] - sum(volumes[-5:-1])/4) / (sum(volumes[-5:-1])/4) if sum(volumes[-5:-1]) > 0 else 0
            recent_price_change = (prices[-1] - prices[-2]) / prices[-2] if len(prices) >= 2 else 0
            
            # Positive correlation between volume and price change is bullish
            if recent_price_change > 0 and recent_vol_change > 0:
                vp_sentiment = 0.5
            elif recent_price_change < 0 and recent_vol_change > 0:
                vp_sentiment = -0.5
            else:
                vp_sentiment = 0.0
            
            sentiment_factors.append(vp_sentiment)
        
        # Aggregate sentiment
        if not sentiment_factors:
            return 0.0, 0.0
        
        sentiment_score = sum(sentiment_factors) / len(sentiment_factors)
        sentiment_score = np.clip(sentiment_score, -1, 1)
        
        # Calculate confidence based on factor consistency
        if len(sentiment_factors) > 1:
            factor_std = np.std(sentiment_factors)
            confidence = max(0.0, 1.0 - factor_std)
        else:
            confidence = 0.5
        
        return sentiment_score, confidence
    
    def _calculate_analysis_confidence(self, trend_confidence: float, 
                                     sentiment_confidence: float, 
                                     data_points: int) -> float:
        """Calculate overall analysis confidence"""
        
        # Data sufficiency factor (more generous for smaller datasets)
        if data_points >= 50:
            data_factor = 1.0
        elif data_points >= 20:
            data_factor = 0.8
        elif data_points >= 10:
            data_factor = 0.6
        elif data_points >= 5:
            data_factor = 0.4
        else:
            data_factor = 0.2
        
        # Average of individual confidences
        avg_confidence = (trend_confidence + sentiment_confidence) / 2
        
        # Overall confidence with minimum threshold
        overall_confidence = max(avg_confidence * data_factor, 0.1)  # Minimum 10% confidence
        
        return min(overall_confidence, 1.0)
    
    async def _get_price_data(self, asset: str, chain: str, 
                            lookback_hours: int) -> List[Tuple[datetime, float]]:
        """Get historical price data for an asset"""
        
        # In a real implementation, this would fetch from price oracles or exchanges
        # For now, we'll generate mock data or use cached data
        
        cache_key = f"price:{asset}:{chain}"
        
        # Check if we have cached data
        if cache_key in self.price_cache:
            cached_data = self.price_cache[cache_key]
            # Filter for the requested timeframe
            cutoff_time = datetime.now() - timedelta(hours=lookback_hours)
            filtered_data = [(ts, price) for ts, price in cached_data if ts >= cutoff_time]
            if filtered_data:
                return filtered_data
        
        # Generate mock price data for testing
        # In production, replace with actual price feed integration
        base_price = 100.0  # Mock base price
        data = []
        
        for i in range(lookback_hours):
            timestamp = datetime.now() - timedelta(hours=lookback_hours - i)
            # Simple random walk for mock data
            price_change = np.random.normal(0, 0.02)  # 2% volatility
            if i == 0:
                price = base_price
            else:
                price = data[-1][1] * (1 + price_change)
            
            data.append((timestamp, price))
        
        # Cache the data
        self.price_cache[cache_key] = data
        
        return data
    
    async def _get_volume_data(self, asset: str, chain: str, 
                             lookback_hours: int) -> List[Tuple[datetime, float]]:
        """Get historical volume data for an asset"""
        
        cache_key = f"volume:{asset}:{chain}"
        
        # Check if we have cached data
        if cache_key in self.volume_cache:
            cached_data = self.volume_cache[cache_key]
            cutoff_time = datetime.now() - timedelta(hours=lookback_hours)
            filtered_data = [(ts, volume) for ts, volume in cached_data if ts >= cutoff_time]
            if filtered_data:
                return filtered_data
        
        # Generate mock volume data for testing
        base_volume = 1000000.0  # Mock base volume
        data = []
        
        for i in range(lookback_hours):
            timestamp = datetime.now() - timedelta(hours=lookback_hours - i)
            # Volume with some randomness
            volume_multiplier = np.random.lognormal(0, 0.5)  # Log-normal distribution
            volume = base_volume * volume_multiplier
            
            data.append((timestamp, volume))
        
        # Cache the data
        self.volume_cache[cache_key] = data
        
        return data
    
    def _get_cached_analysis(self, cache_key: str) -> Optional[MarketAnalysis]:
        """Get cached market analysis if still valid"""
        
        if cache_key in self.analysis_cache:
            analysis = self.analysis_cache[cache_key]
            # Check if cache is still valid
            if (datetime.now() - analysis.timestamp).total_seconds() < self.cache_ttl:
                return analysis
            else:
                # Remove expired cache
                del self.analysis_cache[cache_key]
        
        return None
    
    def _cache_analysis(self, cache_key: str, analysis: MarketAnalysis) -> None:
        """Cache market analysis result"""
        self.analysis_cache[cache_key] = analysis
        
        # Also cache in Redis for persistence
        try:
            import json
            analysis_dict = {
                "asset": analysis.asset,
                "chain": analysis.chain,
                "timestamp": analysis.timestamp.isoformat(),
                "price": analysis.price,
                "volume": analysis.volume,
                "trend_direction": analysis.trend_direction.value,
                "trend_strength": analysis.trend_strength,
                "trend_confidence": analysis.trend_confidence,
                "volatility": analysis.volatility,
                "volatility_regime": analysis.volatility_regime.value,
                "sentiment_score": analysis.sentiment_score,
                "analysis_confidence": analysis.analysis_confidence
            }
            
            self.redis_client.setex(
                cache_key, 
                self.cache_ttl, 
                json.dumps(analysis_dict)
            )
        except Exception as e:
            self.logger.warning(f"Failed to cache analysis in Redis: {e}")
    
    async def detect_arbitrage_opportunities(self, asset: str, 
                                           chains: List[str],
                                           min_profit_threshold: float = 0.01) -> List[ArbitrageOpportunity]:
        """
        Detect cross-chain arbitrage opportunities for an asset
        """
        
        if len(chains) < 2:
            return []
        
        opportunities = []
        
        try:
            # Get current prices on all chains
            chain_prices = {}
            for chain in chains:
                price_data = await self._get_price_data(asset, chain, 1)  # Last hour
                if price_data:
                    chain_prices[chain] = price_data[-1][1]
            
            if len(chain_prices) < 2:
                return []
            
            # Find arbitrage opportunities between all chain pairs
            for source_chain in chains:
                for target_chain in chains:
                    if source_chain == target_chain:
                        continue
                    
                    if source_chain not in chain_prices or target_chain not in chain_prices:
                        continue
                    
                    source_price = chain_prices[source_chain]
                    target_price = chain_prices[target_chain]
                    
                    # Calculate price difference
                    price_diff = target_price - source_price
                    price_diff_pct = price_diff / source_price
                    
                    # Only consider profitable opportunities
                    if price_diff_pct <= min_profit_threshold:
                        continue
                    
                    # Estimate costs (gas, bridge fees, etc.)
                    estimated_costs = await self._estimate_arbitrage_costs(
                        asset, source_chain, target_chain, source_price
                    )
                    
                    # Calculate net profit
                    gross_profit = price_diff
                    net_profit = gross_profit - estimated_costs
                    profit_margin = net_profit / source_price if source_price > 0 else 0
                    
                    # Only include if still profitable after costs
                    if profit_margin <= 0:
                        continue
                    
                    # Calculate confidence score
                    confidence = await self._calculate_arbitrage_confidence(
                        asset, source_chain, target_chain, price_diff_pct
                    )
                    
                    # Estimate opportunity expiry
                    expiry_estimate = datetime.now() + timedelta(minutes=5)  # Conservative estimate
                    
                    opportunity = ArbitrageOpportunity(
                        asset=asset,
                        source_chain=source_chain,
                        target_chain=target_chain,
                        source_price=source_price,
                        target_price=target_price,
                        price_difference=price_diff,
                        price_difference_pct=price_diff_pct,
                        estimated_profit=gross_profit,
                        estimated_costs=estimated_costs,
                        net_profit=net_profit,
                        profit_margin=profit_margin,
                        confidence_score=confidence,
                        timestamp=datetime.now(),
                        expiry_estimate=expiry_estimate
                    )
                    
                    opportunities.append(opportunity)
            
            # Sort by profit margin (descending)
            opportunities.sort(key=lambda x: x.profit_margin, reverse=True)
            
            self.logger.info(f"Found {len(opportunities)} arbitrage opportunities for {asset}")
            return opportunities
            
        except Exception as e:
            self.logger.error(f"Arbitrage detection failed for {asset}: {e}")
            return []
    
    async def _estimate_arbitrage_costs(self, asset: str, source_chain: str, 
                                      target_chain: str, amount: float) -> float:
        """Estimate total costs for arbitrage execution"""
        
        # Base costs (simplified estimates)
        costs = {
            "source_gas": 0.001 * amount,  # 0.1% for source chain gas
            "bridge_fee": 0.002 * amount,  # 0.2% for bridge fees
            "target_gas": 0.001 * amount,  # 0.1% for target chain gas
            "slippage": 0.003 * amount,    # 0.3% for slippage
            "protocol_fees": 0.001 * amount  # 0.1% for protocol fees
        }
        
        # Chain-specific adjustments
        chain_multipliers = {
            "ethereum": 2.0,    # Higher gas costs
            "polygon": 0.1,     # Lower gas costs
            "arbitrum": 0.3,    # Medium gas costs
            "optimism": 0.3,    # Medium gas costs
            "bsc": 0.2,         # Low gas costs
            "avalanche": 0.5    # Medium gas costs
        }
        
        source_multiplier = chain_multipliers.get(source_chain.lower(), 1.0)
        target_multiplier = chain_multipliers.get(target_chain.lower(), 1.0)
        
        # Adjust gas costs based on chain
        costs["source_gas"] *= source_multiplier
        costs["target_gas"] *= target_multiplier
        
        # Bridge-specific costs
        bridge_costs = {
            ("ethereum", "polygon"): 0.001,
            ("ethereum", "arbitrum"): 0.0005,
            ("ethereum", "optimism"): 0.0005,
            ("polygon", "bsc"): 0.002,
            ("arbitrum", "optimism"): 0.0003
        }
        
        bridge_key = (source_chain.lower(), target_chain.lower())
        if bridge_key in bridge_costs:
            costs["bridge_fee"] = bridge_costs[bridge_key] * amount
        
        return sum(costs.values())
    
    async def _calculate_arbitrage_confidence(self, asset: str, source_chain: str, 
                                            target_chain: str, price_diff_pct: float) -> float:
        """Calculate confidence score for arbitrage opportunity"""
        
        confidence_factors = []
        
        # 1. Price difference magnitude (higher difference = higher confidence)
        diff_confidence = min(price_diff_pct / 0.05, 1.0)  # Max confidence at 5% difference
        confidence_factors.append(diff_confidence)
        
        # 2. Market liquidity (simplified - would use real liquidity data)
        liquidity_confidence = 0.8  # Assume good liquidity for now
        confidence_factors.append(liquidity_confidence)
        
        # 3. Chain reliability
        chain_reliability = {
            "ethereum": 0.95,
            "polygon": 0.90,
            "arbitrum": 0.92,
            "optimism": 0.92,
            "bsc": 0.85,
            "avalanche": 0.88
        }
        
        source_reliability = chain_reliability.get(source_chain.lower(), 0.8)
        target_reliability = chain_reliability.get(target_chain.lower(), 0.8)
        avg_reliability = (source_reliability + target_reliability) / 2
        confidence_factors.append(avg_reliability)
        
        # 4. Historical success rate (would use real data)
        historical_confidence = 0.75  # Assume 75% historical success rate
        confidence_factors.append(historical_confidence)
        
        # Calculate overall confidence
        overall_confidence = sum(confidence_factors) / len(confidence_factors)
        return min(overall_confidence, 1.0)
    
    async def generate_market_alerts(self, assets: List[str], chains: List[str]) -> List[MarketAlert]:
        """Generate market alerts based on current conditions"""
        
        alerts = []
        
        try:
            for asset in assets:
                for chain in chains:
                    # Get market analysis
                    analysis = await self.analyze_market(asset, chain)
                    
                    # Check for alert conditions
                    asset_alerts = self._check_alert_conditions(analysis)
                    alerts.extend(asset_alerts)
            
            # Remove duplicate alerts
            unique_alerts = self._deduplicate_alerts(alerts)
            
            # Store active alerts
            for alert in unique_alerts:
                self.active_alerts[alert.alert_id] = alert
            
            self.logger.info(f"Generated {len(unique_alerts)} market alerts")
            return unique_alerts
            
        except Exception as e:
            self.logger.error(f"Alert generation failed: {e}")
            return []
    
    def _check_alert_conditions(self, analysis: MarketAnalysis) -> List[MarketAlert]:
        """Check for various alert conditions in market analysis"""
        
        alerts = []
        timestamp = datetime.now()
        
        # 1. High volatility alert
        if analysis.volatility_regime in [MarketRegime.HIGH_VOLATILITY, MarketRegime.EXTREME_VOLATILITY]:
            alert = MarketAlert(
                alert_id=f"volatility_{analysis.asset}_{analysis.chain}_{int(timestamp.timestamp())}",
                asset=analysis.asset,
                chain=analysis.chain,
                alert_type="high_volatility",
                severity="high" if analysis.volatility_regime == MarketRegime.EXTREME_VOLATILITY else "medium",
                message=f"High volatility detected for {analysis.asset} on {analysis.chain}: {analysis.volatility:.2%}",
                data={
                    "volatility": analysis.volatility,
                    "regime": analysis.volatility_regime.value,
                    "percentile": analysis.volatility_percentile
                },
                timestamp=timestamp,
                expires_at=timestamp + timedelta(hours=1)
            )
            alerts.append(alert)
        
        # 2. Strong trend alert
        if analysis.trend_strength > 0.8 and analysis.trend_confidence > 0.7:
            alert = MarketAlert(
                alert_id=f"trend_{analysis.asset}_{analysis.chain}_{int(timestamp.timestamp())}",
                asset=analysis.asset,
                chain=analysis.chain,
                alert_type="strong_trend",
                severity="medium",
                message=f"Strong {analysis.trend_direction.value} trend for {analysis.asset} on {analysis.chain}",
                data={
                    "trend_direction": analysis.trend_direction.value,
                    "trend_strength": analysis.trend_strength,
                    "trend_confidence": analysis.trend_confidence
                },
                timestamp=timestamp,
                expires_at=timestamp + timedelta(hours=2)
            )
            alerts.append(alert)
        
        # 3. Extreme sentiment alert
        if abs(analysis.sentiment_score) > 0.8 and analysis.sentiment_confidence > 0.6:
            sentiment_type = "bullish" if analysis.sentiment_score > 0 else "bearish"
            alert = MarketAlert(
                alert_id=f"sentiment_{analysis.asset}_{analysis.chain}_{int(timestamp.timestamp())}",
                asset=analysis.asset,
                chain=analysis.chain,
                alert_type="extreme_sentiment",
                severity="medium",
                message=f"Extreme {sentiment_type} sentiment for {analysis.asset} on {analysis.chain}",
                data={
                    "sentiment_score": analysis.sentiment_score,
                    "sentiment_confidence": analysis.sentiment_confidence
                },
                timestamp=timestamp,
                expires_at=timestamp + timedelta(hours=1)
            )
            alerts.append(alert)
        
        # 4. Volume spike alert
        if analysis.relative_volume > 3.0:  # 3x normal volume
            alert = MarketAlert(
                alert_id=f"volume_{analysis.asset}_{analysis.chain}_{int(timestamp.timestamp())}",
                asset=analysis.asset,
                chain=analysis.chain,
                alert_type="volume_spike",
                severity="high",
                message=f"Volume spike detected for {analysis.asset} on {analysis.chain}: {analysis.relative_volume:.1f}x normal",
                data={
                    "relative_volume": analysis.relative_volume,
                    "current_volume": analysis.volume,
                    "volume_profile": analysis.volume_profile
                },
                timestamp=timestamp,
                expires_at=timestamp + timedelta(minutes=30)
            )
            alerts.append(alert)
        
        # 5. Technical indicator alerts
        if analysis.indicators.rsi > 80:  # Overbought
            alert = MarketAlert(
                alert_id=f"rsi_overbought_{analysis.asset}_{analysis.chain}_{int(timestamp.timestamp())}",
                asset=analysis.asset,
                chain=analysis.chain,
                alert_type="overbought",
                severity="medium",
                message=f"RSI overbought for {analysis.asset} on {analysis.chain}: {analysis.indicators.rsi:.1f}",
                data={"rsi": analysis.indicators.rsi},
                timestamp=timestamp,
                expires_at=timestamp + timedelta(hours=1)
            )
            alerts.append(alert)
        elif analysis.indicators.rsi < 20:  # Oversold
            alert = MarketAlert(
                alert_id=f"rsi_oversold_{analysis.asset}_{analysis.chain}_{int(timestamp.timestamp())}",
                asset=analysis.asset,
                chain=analysis.chain,
                alert_type="oversold",
                severity="medium",
                message=f"RSI oversold for {analysis.asset} on {analysis.chain}: {analysis.indicators.rsi:.1f}",
                data={"rsi": analysis.indicators.rsi},
                timestamp=timestamp,
                expires_at=timestamp + timedelta(hours=1)
            )
            alerts.append(alert)
        
        return alerts
    
    def _deduplicate_alerts(self, alerts: List[MarketAlert]) -> List[MarketAlert]:
        """Remove duplicate alerts based on type, asset, and chain"""
        
        seen = set()
        unique_alerts = []
        
        for alert in alerts:
            key = (alert.alert_type, alert.asset, alert.chain)
            if key not in seen:
                seen.add(key)
                unique_alerts.append(alert)
        
        return unique_alerts
    
    def get_active_alerts(self, asset: Optional[str] = None, 
                         chain: Optional[str] = None) -> List[MarketAlert]:
        """Get currently active alerts, optionally filtered"""
        
        # Clean up expired alerts first
        current_time = datetime.now()
        expired_alerts = [
            alert_id for alert_id, alert in self.active_alerts.items()
            if alert.expires_at and alert.expires_at < current_time
        ]
        
        for alert_id in expired_alerts:
            del self.active_alerts[alert_id]
        
        # Filter alerts
        filtered_alerts = []
        for alert in self.active_alerts.values():
            if asset and alert.asset != asset:
                continue
            if chain and alert.chain != chain:
                continue
            filtered_alerts.append(alert)
        
        return filtered_alerts
    
    def dismiss_alert(self, alert_id: str) -> bool:
        """Dismiss an active alert"""
        
        if alert_id in self.active_alerts:
            del self.active_alerts[alert_id]
            self.logger.info(f"Dismissed alert {alert_id}")
            return True
        
        return False
    
    async def get_market_summary(self, assets: List[str], chains: List[str]) -> Dict[str, Any]:
        """Get comprehensive market summary for multiple assets and chains"""
        
        summary = {
            "timestamp": datetime.now().isoformat(),
            "assets": {},
            "overall_sentiment": 0.0,
            "market_regime": "normal",
            "active_alerts": len(self.active_alerts),
            "arbitrage_opportunities": 0
        }
        
        try:
            sentiment_scores = []
            volatility_scores = []
            
            # Analyze each asset on each chain
            for asset in assets:
                asset_data = {}
                
                for chain in chains:
                    try:
                        analysis = await self.analyze_market(asset, chain)
                        
                        asset_data[chain] = {
                            "price": analysis.price,
                            "trend": analysis.trend_direction.value,
                            "trend_strength": analysis.trend_strength,
                            "volatility": analysis.volatility,
                            "sentiment": analysis.sentiment_score,
                            "confidence": analysis.analysis_confidence
                        }
                        
                        sentiment_scores.append(analysis.sentiment_score)
                        volatility_scores.append(analysis.volatility)
                        
                    except Exception as e:
                        self.logger.warning(f"Failed to analyze {asset} on {chain}: {e}")
                        continue
                
                if asset_data:
                    summary["assets"][asset] = asset_data
            
            # Calculate overall metrics
            if sentiment_scores:
                summary["overall_sentiment"] = sum(sentiment_scores) / len(sentiment_scores)
            
            if volatility_scores:
                avg_volatility = sum(volatility_scores) / len(volatility_scores)
                if avg_volatility > 0.8:
                    summary["market_regime"] = "high_volatility"
                elif avg_volatility > 0.5:
                    summary["market_regime"] = "elevated_volatility"
                else:
                    summary["market_regime"] = "normal"
            
            # Count arbitrage opportunities
            total_opportunities = 0
            for asset in assets:
                opportunities = await self.detect_arbitrage_opportunities(asset, chains)
                total_opportunities += len(opportunities)
            
            summary["arbitrage_opportunities"] = total_opportunities
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Market summary generation failed: {e}")
            return summary
    
    async def shutdown(self):
        """Shutdown the market intelligence engine"""
        
        try:
            # Close Redis connection
            self.redis_client.close()
            
            # Shutdown thread pool
            self.executor.shutdown(wait=True)
            
            self.logger.info("Market Intelligence Engine shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")