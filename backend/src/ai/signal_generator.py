"""
Phase 5: AI Signal Generator

Generates trading signals based on:
- Technical indicators (RSI, MACD, MA, Bollinger Bands)
- Price momentum analysis
- Volume analysis
- Market sentiment
- User risk tolerance personalization
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime, timedelta
from enum import Enum
import numpy as np

from src.config.phase5_config import INDICATOR_PARAMS
from src.services.advanced_price_oracle import price_oracle
from src.config.database import get_db

logger = logging.getLogger(__name__)


class SignalType(Enum):
    """Trading signal types"""
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


class SignalStrength(Enum):
    """Signal strength levels"""
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"


@dataclass
class SignalFactor:
    """A factor contributing to the signal"""
    name: str
    value: float
    weight: float
    signal_contribution: float  # -1 to 1 (bearish to bullish)
    description: str


@dataclass
class TradingSignal:
    """AI-generated trading signal"""
    token: str
    signal_type: SignalType
    confidence: float  # 0-100
    strength: SignalStrength
    target_price: Decimal
    stop_loss: Decimal
    take_profit: Decimal
    timeframe: str
    explanation: str
    factors: List[SignalFactor]
    created_at: datetime
    expires_at: datetime
    risk_adjusted: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "token": self.token,
            "signal_type": self.signal_type.value,
            "confidence": self.confidence,
            "strength": self.strength.value,
            "target_price": str(self.target_price),
            "stop_loss": str(self.stop_loss),
            "take_profit": str(self.take_profit),
            "timeframe": self.timeframe,
            "explanation": self.explanation,
            "factors": [
                {
                    "name": f.name,
                    "value": f.value,
                    "weight": f.weight,
                    "signal_contribution": f.signal_contribution,
                    "description": f.description
                }
                for f in self.factors
            ],
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "risk_adjusted": self.risk_adjusted
        }


@dataclass
class SignalAccuracy:
    """Historical signal accuracy tracking"""
    total_signals: int = 0
    correct_signals: int = 0
    accuracy_rate: float = 0.0
    avg_return: float = 0.0
    
    def update(self, was_correct: bool, return_pct: float) -> None:
        self.total_signals += 1
        if was_correct:
            self.correct_signals += 1
        self.accuracy_rate = self.correct_signals / self.total_signals * 100
        # Running average
        self.avg_return = (
            (self.avg_return * (self.total_signals - 1) + return_pct) 
            / self.total_signals
        )


class TechnicalIndicators:
    """Calculate technical indicators from price data"""
    
    @staticmethod
    def calculate_sma(prices: List[float], period: int) -> List[float]:
        """Simple Moving Average"""
        if len(prices) < period:
            return []
        
        sma = []
        for i in range(period - 1, len(prices)):
            avg = sum(prices[i - period + 1:i + 1]) / period
            sma.append(avg)
        return sma
    
    @staticmethod
    def calculate_ema(prices: List[float], period: int) -> List[float]:
        """Exponential Moving Average"""
        if len(prices) < period:
            return []
        
        multiplier = 2 / (period + 1)
        ema = [sum(prices[:period]) / period]  # Start with SMA
        
        for price in prices[period:]:
            ema.append((price - ema[-1]) * multiplier + ema[-1])
        
        return ema
    
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> List[float]:
        """Relative Strength Index"""
        if len(prices) < period + 1:
            return []
        
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        
        rsi = []
        for i in range(period, len(deltas)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            
            if avg_loss == 0:
                rsi.append(100)
            else:
                rs = avg_gain / avg_loss
                rsi.append(100 - (100 / (1 + rs)))
        
        return rsi
    
    @staticmethod
    def calculate_macd(
        prices: List[float],
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> Tuple[List[float], List[float], List[float]]:
        """MACD (Moving Average Convergence Divergence)"""
        if len(prices) < slow:
            return [], [], []
        
        ema_fast = TechnicalIndicators.calculate_ema(prices, fast)
        ema_slow = TechnicalIndicators.calculate_ema(prices, slow)
        
        # Align EMAs
        offset = slow - fast
        macd_line = [
            ema_fast[i + offset] - ema_slow[i] 
            for i in range(len(ema_slow))
        ]
        
        signal_line = TechnicalIndicators.calculate_ema(macd_line, signal)
        
        # Histogram
        offset = len(macd_line) - len(signal_line)
        histogram = [
            macd_line[i + offset] - signal_line[i] 
            for i in range(len(signal_line))
        ]
        
        return macd_line, signal_line, histogram
    
    @staticmethod
    def calculate_bollinger_bands(
        prices: List[float],
        period: int = 20,
        std_dev: float = 2.0
    ) -> Tuple[List[float], List[float], List[float]]:
        """Bollinger Bands"""
        if len(prices) < period:
            return [], [], []
        
        sma = TechnicalIndicators.calculate_sma(prices, period)
        
        upper = []
        lower = []
        
        for i in range(len(sma)):
            window = prices[i:i + period]
            std = np.std(window)
            upper.append(sma[i] + std_dev * std)
            lower.append(sma[i] - std_dev * std)
        
        return upper, sma, lower


class SignalGenerator:
    """
    AI-powered trading signal generator
    """
    
    def __init__(self):
        self.indicators = TechnicalIndicators()
        self.signal_history: Dict[str, List[TradingSignal]] = {}
        self.accuracy_tracking: Dict[str, SignalAccuracy] = {}
    
    async def generate_signal(
        self,
        token: str,
        timeframe: str = "1h",
        risk_tolerance: float = 0.5
    ) -> Optional[TradingSignal]:
        """
        Generate a trading signal for a token
        
        Args:
            token: Token symbol (e.g., "BTC", "ETH")
            timeframe: Chart timeframe
            risk_tolerance: User's risk tolerance (0-1)
        
        Returns:
            TradingSignal with recommendation
        """
        # Get historical price data
        candles = await price_oracle.get_historical_prices(
            token, timeframe, limit=200
        )
        
        if len(candles) < 50:
            return None
        
        prices = [c["close"] for c in candles]
        volumes = [c["volume"] for c in candles]
        current_price = Decimal(str(prices[-1]))
        
        # Calculate all indicators
        factors = []
        
        # RSI Analysis
        rsi_factor = self._analyze_rsi(prices)
        if rsi_factor:
            factors.append(rsi_factor)
        
        # MACD Analysis
        macd_factor = self._analyze_macd(prices)
        if macd_factor:
            factors.append(macd_factor)
        
        # Moving Average Analysis
        ma_factor = self._analyze_moving_averages(prices)
        if ma_factor:
            factors.append(ma_factor)
        
        # Bollinger Bands Analysis
        bb_factor = self._analyze_bollinger_bands(prices)
        if bb_factor:
            factors.append(bb_factor)
        
        # Volume Analysis
        vol_factor = self._analyze_volume(prices, volumes)
        if vol_factor:
            factors.append(vol_factor)
        
        # Momentum Analysis
        momentum_factor = self._analyze_momentum(prices)
        if momentum_factor:
            factors.append(momentum_factor)
        
        if len(factors) < 3:
            return None
        
        # Calculate overall signal
        signal_score = self._calculate_signal_score(factors)
        signal_type = self._score_to_signal_type(signal_score)
        confidence = self._calculate_confidence(factors, signal_score)
        strength = self._calculate_strength(confidence)
        
        # Adjust for risk tolerance
        if risk_tolerance < 0.3:
            # Conservative: require higher confidence
            if confidence < 70:
                signal_type = SignalType.HOLD
        elif risk_tolerance > 0.7:
            # Aggressive: lower threshold
            pass
        
        # Calculate price targets
        stop_loss, take_profit = self._calculate_targets(
            current_price, signal_type, risk_tolerance
        )
        
        # Generate explanation
        explanation = self._generate_explanation(factors, signal_type, confidence)
        
        signal = TradingSignal(
            token=token,
            signal_type=signal_type,
            confidence=confidence,
            strength=strength,
            target_price=current_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            timeframe=timeframe,
            explanation=explanation,
            factors=factors,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=1),
            risk_adjusted=risk_tolerance != 0.5
        )
        
        # Store in history
        if token not in self.signal_history:
            self.signal_history[token] = []
        self.signal_history[token].append(signal)
        
        # Store in database
        try:
            db = next(get_db())
            db.execute("""
                INSERT INTO ai_signals (
                    token, signal_type, confidence, timeframe, reason,
                    entry_price, target_price, stop_loss, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                token,
                signal_type.value,
                confidence,
                timeframe,
                explanation,
                float(current_price),
                float(take_profit),
                float(stop_loss),
                datetime.utcnow().isoformat()
            ))
            db.commit()
        except Exception as e:
            logger.error(f"Failed to store signal in database: {e}")
        
        return signal

    
    def _analyze_rsi(self, prices: List[float]) -> Optional[SignalFactor]:
        """Analyze RSI indicator"""
        rsi_values = self.indicators.calculate_rsi(prices, 14)
        if not rsi_values:
            return None
        
        current_rsi = rsi_values[-1]
        
        # Determine signal contribution
        if current_rsi < 30:
            contribution = 0.8  # Oversold - bullish
            description = f"RSI at {current_rsi:.1f} indicates oversold conditions"
        elif current_rsi > 70:
            contribution = -0.8  # Overbought - bearish
            description = f"RSI at {current_rsi:.1f} indicates overbought conditions"
        elif current_rsi < 40:
            contribution = 0.3
            description = f"RSI at {current_rsi:.1f} suggests mild bullish momentum"
        elif current_rsi > 60:
            contribution = -0.3
            description = f"RSI at {current_rsi:.1f} suggests mild bearish momentum"
        else:
            contribution = 0
            description = f"RSI at {current_rsi:.1f} is neutral"
        
        return SignalFactor(
            name="RSI",
            value=current_rsi,
            weight=0.2,
            signal_contribution=contribution,
            description=description
        )
    
    def _analyze_macd(self, prices: List[float]) -> Optional[SignalFactor]:
        """Analyze MACD indicator"""
        macd_line, signal_line, histogram = self.indicators.calculate_macd(prices)
        if not histogram:
            return None
        
        current_hist = histogram[-1]
        prev_hist = histogram[-2] if len(histogram) > 1 else 0
        
        # Determine signal contribution
        if current_hist > 0 and current_hist > prev_hist:
            contribution = 0.7  # Bullish momentum increasing
            description = "MACD histogram positive and increasing - bullish momentum"
        elif current_hist > 0:
            contribution = 0.3
            description = "MACD histogram positive - mild bullish"
        elif current_hist < 0 and current_hist < prev_hist:
            contribution = -0.7  # Bearish momentum increasing
            description = "MACD histogram negative and decreasing - bearish momentum"
        elif current_hist < 0:
            contribution = -0.3
            description = "MACD histogram negative - mild bearish"
        else:
            contribution = 0
            description = "MACD is neutral"
        
        return SignalFactor(
            name="MACD",
            value=current_hist,
            weight=0.2,
            signal_contribution=contribution,
            description=description
        )
    
    def _analyze_moving_averages(self, prices: List[float]) -> Optional[SignalFactor]:
        """Analyze moving average crossovers"""
        ma_20 = self.indicators.calculate_sma(prices, 20)
        ma_50 = self.indicators.calculate_sma(prices, 50)
        
        if not ma_20 or not ma_50:
            return None
        
        current_price = prices[-1]
        current_ma20 = ma_20[-1]
        current_ma50 = ma_50[-1] if len(ma_50) > 0 else ma_20[-1]
        
        # Price vs MAs
        above_ma20 = current_price > current_ma20
        above_ma50 = current_price > current_ma50
        ma20_above_ma50 = current_ma20 > current_ma50
        
        if above_ma20 and above_ma50 and ma20_above_ma50:
            contribution = 0.6
            description = "Price above both MAs with bullish crossover"
        elif above_ma20 and above_ma50:
            contribution = 0.4
            description = "Price above both moving averages"
        elif not above_ma20 and not above_ma50 and not ma20_above_ma50:
            contribution = -0.6
            description = "Price below both MAs with bearish crossover"
        elif not above_ma20 and not above_ma50:
            contribution = -0.4
            description = "Price below both moving averages"
        else:
            contribution = 0
            description = "Mixed moving average signals"
        
        return SignalFactor(
            name="Moving Averages",
            value=current_price / current_ma20 - 1,
            weight=0.2,
            signal_contribution=contribution,
            description=description
        )
    
    def _analyze_bollinger_bands(self, prices: List[float]) -> Optional[SignalFactor]:
        """Analyze Bollinger Bands"""
        upper, middle, lower = self.indicators.calculate_bollinger_bands(prices)
        if not upper:
            return None
        
        current_price = prices[-1]
        current_upper = upper[-1]
        current_lower = lower[-1]
        current_middle = middle[-1]
        
        # Calculate position within bands
        band_width = current_upper - current_lower
        position = (current_price - current_lower) / band_width if band_width > 0 else 0.5
        
        if position < 0.1:
            contribution = 0.7  # Near lower band - potential bounce
            description = "Price near lower Bollinger Band - potential reversal"
        elif position > 0.9:
            contribution = -0.7  # Near upper band - potential pullback
            description = "Price near upper Bollinger Band - potential pullback"
        elif position < 0.3:
            contribution = 0.3
            description = "Price in lower half of Bollinger Bands"
        elif position > 0.7:
            contribution = -0.3
            description = "Price in upper half of Bollinger Bands"
        else:
            contribution = 0
            description = "Price in middle of Bollinger Bands"
        
        return SignalFactor(
            name="Bollinger Bands",
            value=position,
            weight=0.15,
            signal_contribution=contribution,
            description=description
        )
    
    def _analyze_volume(
        self, prices: List[float], volumes: List[float]
    ) -> Optional[SignalFactor]:
        """Analyze volume patterns"""
        if len(volumes) < 20:
            return None
        
        avg_volume = sum(volumes[-20:]) / 20
        current_volume = volumes[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
        
        price_change = (prices[-1] - prices[-2]) / prices[-2] if prices[-2] > 0 else 0
        
        # High volume with price increase is bullish
        # High volume with price decrease is bearish
        if volume_ratio > 1.5 and price_change > 0:
            contribution = 0.5
            description = f"High volume ({volume_ratio:.1f}x avg) with price increase"
        elif volume_ratio > 1.5 and price_change < 0:
            contribution = -0.5
            description = f"High volume ({volume_ratio:.1f}x avg) with price decrease"
        elif volume_ratio < 0.5:
            contribution = 0
            description = "Low volume - weak conviction"
        else:
            contribution = 0.1 if price_change > 0 else -0.1
            description = "Normal volume"
        
        return SignalFactor(
            name="Volume",
            value=volume_ratio,
            weight=0.1,
            signal_contribution=contribution,
            description=description
        )
    
    def _analyze_momentum(self, prices: List[float]) -> Optional[SignalFactor]:
        """Analyze price momentum"""
        if len(prices) < 14:
            return None
        
        # Calculate momentum (rate of change)
        momentum_7d = (prices[-1] - prices[-7]) / prices[-7] * 100 if prices[-7] > 0 else 0
        momentum_14d = (prices[-1] - prices[-14]) / prices[-14] * 100 if prices[-14] > 0 else 0
        
        avg_momentum = (momentum_7d + momentum_14d) / 2
        
        if avg_momentum > 10:
            contribution = 0.5
            description = f"Strong upward momentum ({avg_momentum:.1f}%)"
        elif avg_momentum > 3:
            contribution = 0.3
            description = f"Positive momentum ({avg_momentum:.1f}%)"
        elif avg_momentum < -10:
            contribution = -0.5
            description = f"Strong downward momentum ({avg_momentum:.1f}%)"
        elif avg_momentum < -3:
            contribution = -0.3
            description = f"Negative momentum ({avg_momentum:.1f}%)"
        else:
            contribution = 0
            description = f"Neutral momentum ({avg_momentum:.1f}%)"
        
        return SignalFactor(
            name="Momentum",
            value=avg_momentum,
            weight=0.15,
            signal_contribution=contribution,
            description=description
        )
    
    def _calculate_signal_score(self, factors: List[SignalFactor]) -> float:
        """Calculate weighted signal score from factors"""
        total_weight = sum(f.weight for f in factors)
        if total_weight == 0:
            return 0
        
        weighted_sum = sum(f.signal_contribution * f.weight for f in factors)
        return weighted_sum / total_weight
    
    def _score_to_signal_type(self, score: float) -> SignalType:
        """Convert signal score to signal type"""
        if score > 0.5:
            return SignalType.STRONG_BUY
        elif score > 0.2:
            return SignalType.BUY
        elif score < -0.5:
            return SignalType.STRONG_SELL
        elif score < -0.2:
            return SignalType.SELL
        else:
            return SignalType.HOLD
    
    def _calculate_confidence(
        self, factors: List[SignalFactor], score: float
    ) -> float:
        """Calculate confidence level (0-100)"""
        # Base confidence from score magnitude
        base_confidence = min(abs(score) * 100, 80)
        
        # Bonus for factor agreement
        bullish_factors = sum(1 for f in factors if f.signal_contribution > 0)
        bearish_factors = sum(1 for f in factors if f.signal_contribution < 0)
        
        agreement_ratio = max(bullish_factors, bearish_factors) / len(factors)
        agreement_bonus = agreement_ratio * 20
        
        return min(base_confidence + agreement_bonus, 95)
    
    def _calculate_strength(self, confidence: float) -> SignalStrength:
        """Determine signal strength from confidence"""
        if confidence >= 75:
            return SignalStrength.STRONG
        elif confidence >= 50:
            return SignalStrength.MODERATE
        else:
            return SignalStrength.WEAK
    
    def _calculate_targets(
        self,
        current_price: Decimal,
        signal_type: SignalType,
        risk_tolerance: float
    ) -> Tuple[Decimal, Decimal]:
        """Calculate stop-loss and take-profit targets"""
        # Base percentages
        base_stop = Decimal("0.03")  # 3%
        base_profit = Decimal("0.06")  # 6%
        
        # Adjust for risk tolerance
        risk_multiplier = Decimal(str(0.5 + risk_tolerance))
        
        stop_pct = base_stop * risk_multiplier
        profit_pct = base_profit * risk_multiplier
        
        if signal_type in [SignalType.BUY, SignalType.STRONG_BUY]:
            stop_loss = current_price * (1 - stop_pct)
            take_profit = current_price * (1 + profit_pct)
        else:
            stop_loss = current_price * (1 + stop_pct)
            take_profit = current_price * (1 - profit_pct)
        
        return stop_loss, take_profit
    
    def _generate_explanation(
        self,
        factors: List[SignalFactor],
        signal_type: SignalType,
        confidence: float
    ) -> str:
        """Generate human-readable explanation"""
        signal_word = signal_type.value.replace("_", " ").title()
        
        # Get top contributing factors
        sorted_factors = sorted(
            factors, 
            key=lambda f: abs(f.signal_contribution * f.weight),
            reverse=True
        )[:3]
        
        factor_descriptions = [f.description for f in sorted_factors]
        
        explanation = (
            f"{signal_word} signal with {confidence:.0f}% confidence. "
            f"Key factors: {'; '.join(factor_descriptions)}."
        )
        
        return explanation
    
    def get_signal_accuracy(self, token: str) -> SignalAccuracy:
        """Get historical accuracy for a token"""
        return self.accuracy_tracking.get(token, SignalAccuracy())
    
    async def get_signals_for_tokens(
        self,
        tokens: List[str],
        timeframe: str = "1h",
        risk_tolerance: float = 0.5
    ) -> List[TradingSignal]:
        """Generate signals for multiple tokens"""
        tasks = [
            self.generate_signal(token, timeframe, risk_tolerance)
            for token in tokens
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        signals = []
        for result in results:
            if isinstance(result, TradingSignal):
                signals.append(result)
        
        # Sort by confidence
        signals.sort(key=lambda s: s.confidence, reverse=True)
        return signals


# Global signal generator instance
signal_generator = SignalGenerator()
