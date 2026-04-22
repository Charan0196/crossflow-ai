"""
Automated Signal Generation Scheduler

Generates trading signals regularly based on market conditions
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from src.ai.signal_generator import signal_generator, TradingSignal
from src.services.advanced_price_oracle import price_oracle

logger = logging.getLogger(__name__)


class SignalScheduler:
    """
    Automated signal generation scheduler
    Generates signals at regular intervals based on market conditions
    """
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.active_tokens = [
            "BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "DOGE", "MATIC",
            "DOT", "LTC", "TRX", "AVAX", "LINK", "ATOM", "UNI", "ETC"
        ]
        self.latest_signals: Dict[str, TradingSignal] = {}
        self.signal_history: List[Dict[str, Any]] = []
        self.is_running = False
    
    async def start(self):
        """Start the signal generation scheduler"""
        if self.is_running:
            logger.warning("Signal scheduler is already running")
            return
        
        logger.info("🚀 Starting automated signal generation scheduler...")
        
        # Schedule signal generation every 5 minutes
        self.scheduler.add_job(
            self.generate_all_signals,
            trigger=IntervalTrigger(minutes=5),
            id="generate_signals_5min",
            name="Generate Trading Signals (5min)",
            replace_existing=True
        )
        
        # Schedule hourly signal generation for longer timeframes
        self.scheduler.add_job(
            self.generate_hourly_signals,
            trigger=IntervalTrigger(hours=1),
            id="generate_signals_1h",
            name="Generate Trading Signals (1h)",
            replace_existing=True
        )
        
        # Schedule daily signal generation
        self.scheduler.add_job(
            self.generate_daily_signals,
            trigger=CronTrigger(hour=0, minute=0),
            id="generate_signals_daily",
            name="Generate Trading Signals (Daily)",
            replace_existing=True
        )
        
        # Schedule market analysis every 5 minutes
        self.scheduler.add_job(
            self.analyze_market_conditions,
            trigger=IntervalTrigger(minutes=5),
            id="analyze_market",
            name="Analyze Market Conditions",
            replace_existing=True
        )
        
        self.scheduler.start()
        self.is_running = True
        
        # Generate initial signals
        await self.generate_all_signals()
        
        logger.info("✅ Signal scheduler started successfully")
    
    async def stop(self):
        """Stop the signal generation scheduler"""
        if not self.is_running:
            return
        
        logger.info("Stopping signal scheduler...")
        self.scheduler.shutdown(wait=False)
        self.is_running = False
        logger.info("Signal scheduler stopped")
    
    async def generate_all_signals(self):
        """Generate signals for all active tokens"""
        try:
            logger.info(f"📊 Generating signals for {len(self.active_tokens)} tokens...")
            
            signals = await signal_generator.get_signals_for_tokens(
                tokens=self.active_tokens,
                timeframe="15m",
                risk_tolerance=0.5
            )
            
            # Update latest signals
            for signal in signals:
                self.latest_signals[signal.token] = signal
                
                # Add to history
                self.signal_history.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "token": signal.token,
                    "signal_type": signal.signal_type.value,
                    "confidence": signal.confidence,
                    "timeframe": "15m"
                })
            
            # Keep only last 1000 signals in history
            if len(self.signal_history) > 1000:
                self.signal_history = self.signal_history[-1000:]
            
            logger.info(f"✅ Generated {len(signals)} signals")
            
            # Log top signals
            top_signals = sorted(signals, key=lambda s: s.confidence, reverse=True)[:5]
            for signal in top_signals:
                logger.info(
                    f"  {signal.token}: {signal.signal_type.value.upper()} "
                    f"({signal.confidence:.0f}% confidence)"
                )
        
        except Exception as e:
            logger.error(f"Error generating signals: {e}", exc_info=True)
    
    async def generate_hourly_signals(self):
        """Generate signals for 1-hour timeframe"""
        try:
            logger.info("📊 Generating hourly signals...")
            
            signals = await signal_generator.get_signals_for_tokens(
                tokens=self.active_tokens,
                timeframe="1h",
                risk_tolerance=0.5
            )
            
            logger.info(f"✅ Generated {len(signals)} hourly signals")
        
        except Exception as e:
            logger.error(f"Error generating hourly signals: {e}", exc_info=True)
    
    async def generate_daily_signals(self):
        """Generate signals for daily timeframe"""
        try:
            logger.info("📊 Generating daily signals...")
            
            signals = await signal_generator.get_signals_for_tokens(
                tokens=self.active_tokens,
                timeframe="1d",
                risk_tolerance=0.5
            )
            
            logger.info(f"✅ Generated {len(signals)} daily signals")
        
        except Exception as e:
            logger.error(f"Error generating daily signals: {e}", exc_info=True)
    
    async def analyze_market_conditions(self):
        """Analyze overall market conditions"""
        try:
            # Get prices for major tokens
            major_tokens = ["BTC", "ETH", "BNB"]
            
            market_sentiment = {
                "bullish": 0,
                "bearish": 0,
                "neutral": 0
            }
            
            for token in major_tokens:
                if token in self.latest_signals:
                    signal = self.latest_signals[token]
                    if signal.signal_type.value in ["buy", "strong_buy"]:
                        market_sentiment["bullish"] += 1
                    elif signal.signal_type.value in ["sell", "strong_sell"]:
                        market_sentiment["bearish"] += 1
                    else:
                        market_sentiment["neutral"] += 1
            
            # Determine overall market sentiment
            if market_sentiment["bullish"] > market_sentiment["bearish"]:
                overall = "BULLISH"
            elif market_sentiment["bearish"] > market_sentiment["bullish"]:
                overall = "BEARISH"
            else:
                overall = "NEUTRAL"
            
            logger.debug(f"Market sentiment: {overall} (B:{market_sentiment['bullish']} N:{market_sentiment['neutral']} Be:{market_sentiment['bearish']})")
        
        except Exception as e:
            logger.error(f"Error analyzing market conditions: {e}")
    
    def get_latest_signals(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get latest generated signals"""
        signals = list(self.latest_signals.values())
        signals.sort(key=lambda s: s.confidence, reverse=True)
        return [s.to_dict() for s in signals[:limit]]
    
    def get_signal_for_token(self, token: str) -> Dict[str, Any]:
        """Get latest signal for a specific token"""
        if token in self.latest_signals:
            return self.latest_signals[token].to_dict()
        return None
    
    def get_signal_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get signal generation history"""
        return self.signal_history[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics"""
        return {
            "is_running": self.is_running,
            "active_tokens": len(self.active_tokens),
            "latest_signals_count": len(self.latest_signals),
            "total_signals_generated": len(self.signal_history),
            "next_run": self.scheduler.get_jobs()[0].next_run_time.isoformat() if self.scheduler.get_jobs() else None
        }


# Global scheduler instance
signal_scheduler = SignalScheduler()
