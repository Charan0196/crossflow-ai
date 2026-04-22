"""
Automated Trading System with Mock USD

Executes trades automatically based on AI-generated signals using virtual funds
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from decimal import Decimal, ROUND_DOWN
from dataclasses import dataclass, field
from enum import Enum
import json

from src.services.signal_scheduler import signal_scheduler
from src.services.advanced_price_oracle import price_oracle
from src.config.database import get_db

logger = logging.getLogger(__name__)


class TradeStatus(Enum):
    """Trade execution status"""
    PENDING = "pending"
    EXECUTED = "executed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class TradeType(Enum):
    """Trade types"""
    BUY = "buy"
    SELL = "sell"


@dataclass
class MockPortfolio:
    """Mock trading portfolio"""
    usd_balance: Decimal = Decimal("10000.00")  # Starting with $10,000
    token_holdings: Dict[str, Decimal] = field(default_factory=dict)
    total_value: Decimal = Decimal("10000.00")
    profit_loss: Decimal = Decimal("0.00")
    trades_count: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    
    def get_win_rate(self) -> float:
        """Calculate win rate percentage"""
        if self.trades_count == 0:
            return 0.0
        return (self.winning_trades / self.trades_count) * 100
    
    def get_roi(self) -> float:
        """Calculate return on investment percentage"""
        initial_value = Decimal("10000.00")
        return float((self.total_value - initial_value) / initial_value * 100)


@dataclass
class MockTrade:
    """Mock trade execution"""
    id: str
    token: str
    trade_type: TradeType
    amount: Decimal
    price: Decimal
    total_value: Decimal
    signal_confidence: float
    status: TradeStatus
    created_at: datetime
    executed_at: Optional[datetime] = None
    stop_loss: Optional[Decimal] = None
    take_profit: Optional[Decimal] = None
    profit_loss: Optional[Decimal] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "token": self.token,
            "trade_type": self.trade_type.value,
            "amount": str(self.amount),
            "price": str(self.price),
            "total_value": str(self.total_value),
            "signal_confidence": self.signal_confidence,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "stop_loss": str(self.stop_loss) if self.stop_loss else None,
            "take_profit": str(self.take_profit) if self.take_profit else None,
            "profit_loss": str(self.profit_loss) if self.profit_loss else None
        }


class AutoTrader:
    """
    Automated trading system using mock USD
    Executes trades based on AI signals with virtual funds
    """
    
    def __init__(self):
        self.portfolio = MockPortfolio()
        self.active_trades: Dict[str, MockTrade] = {}
        self.trade_history: List[MockTrade] = []
        self.is_enabled = True
        self.min_confidence = 70.0  # Minimum signal confidence to trade
        self.max_position_size = 0.1  # Max 10% of portfolio per trade
        self.stop_loss_pct = 0.03  # 3% stop loss
        self.take_profit_pct = 0.06  # 6% take profit
        
        # Trading statistics
        self.stats = {
            "total_trades": 0,
            "profitable_trades": 0,
            "total_profit": Decimal("0.00"),
            "max_drawdown": Decimal("0.00"),
            "sharpe_ratio": 0.0,
            "started_at": datetime.utcnow()
        }
    
    async def start_auto_trading(self):
        """Start automated trading based on signals"""
        if not self.is_enabled:
            logger.info("Auto trading is disabled")
            return
        
        logger.info("🤖 Starting automated trading with mock USD...")
        logger.info(f"💰 Initial portfolio: ${self.portfolio.usd_balance}")
        
        # Start monitoring signals and executing trades
        while self.is_enabled:
            try:
                await self.process_signals()
                await self.monitor_active_trades()
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Error in auto trading loop: {e}", exc_info=True)
                await asyncio.sleep(60)  # Wait longer on error
    
    async def process_signals(self):
        """Process latest signals and execute trades"""
        try:
            # Get latest signals
            signals = signal_scheduler.get_latest_signals(limit=20)
            
            for signal_data in signals:
                await self.evaluate_signal(signal_data)
        
        except Exception as e:
            logger.error(f"Error processing signals: {e}")
    
    async def evaluate_signal(self, signal_data: Dict[str, Any]):
        """Evaluate a signal and decide whether to trade"""
        try:
            token = signal_data["token"]
            signal_type = signal_data["signal_type"]
            confidence = signal_data["confidence"]
            
            # Skip if confidence is too low
            if confidence < self.min_confidence:
                return
            
            # Skip if we already have an active position in this token
            if self.has_active_position(token):
                return
            
            # Get current price
            current_price = await self.get_current_price(token)
            if not current_price:
                return
            
            # Calculate position size based on confidence and portfolio
            position_size = self.calculate_position_size(confidence)
            
            if signal_type in ["buy", "strong_buy"]:
                await self.execute_buy_order(
                    token=token,
                    price=current_price,
                    position_size=position_size,
                    confidence=confidence,
                    signal_data=signal_data
                )
            elif signal_type in ["sell", "strong_sell"] and token in self.portfolio.token_holdings:
                await self.execute_sell_order(
                    token=token,
                    price=current_price,
                    confidence=confidence,
                    signal_data=signal_data
                )
        
        except Exception as e:
            logger.error(f"Error evaluating signal for {signal_data.get('token', 'unknown')}: {e}")
    
    async def execute_buy_order(
        self,
        token: str,
        price: Decimal,
        position_size: Decimal,
        confidence: float,
        signal_data: Dict[str, Any]
    ):
        """Execute a buy order with mock USD"""
        try:
            # Calculate trade amount
            trade_value = self.portfolio.usd_balance * position_size
            token_amount = trade_value / price
            
            # Check if we have enough USD
            if trade_value > self.portfolio.usd_balance:
                logger.warning(f"Insufficient USD balance for {token} trade")
                return
            
            # Create trade
            trade = MockTrade(
                id=f"trade_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{token}",
                token=token,
                trade_type=TradeType.BUY,
                amount=token_amount,
                price=price,
                total_value=trade_value,
                signal_confidence=confidence,
                status=TradeStatus.EXECUTED,
                created_at=datetime.utcnow(),
                executed_at=datetime.utcnow(),
                stop_loss=price * (1 - Decimal(str(self.stop_loss_pct))),
                take_profit=price * (1 + Decimal(str(self.take_profit_pct)))
            )
            
            # Update portfolio
            self.portfolio.usd_balance -= trade_value
            if token in self.portfolio.token_holdings:
                self.portfolio.token_holdings[token] += token_amount
            else:
                self.portfolio.token_holdings[token] = token_amount
            
            # Add to active trades and history
            self.active_trades[trade.id] = trade
            self.trade_history.append(trade)
            self.portfolio.trades_count += 1
            
            # Update stats
            self.stats["total_trades"] += 1
            
            # Store in database
            await self.store_trade(trade)
            
            logger.info(
                f"🟢 BUY {token}: {token_amount:.6f} @ ${price:.2f} "
                f"(${trade_value:.2f}, {confidence:.1f}% confidence)"
            )
            
            await self.update_portfolio_value()
        
        except Exception as e:
            logger.error(f"Error executing buy order for {token}: {e}")
    
    async def execute_sell_order(
        self,
        token: str,
        price: Decimal,
        confidence: float,
        signal_data: Dict[str, Any]
    ):
        """Execute a sell order"""
        try:
            if token not in self.portfolio.token_holdings:
                return
            
            token_amount = self.portfolio.token_holdings[token]
            trade_value = token_amount * price
            
            # Create trade
            trade = MockTrade(
                id=f"trade_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{token}",
                token=token,
                trade_type=TradeType.SELL,
                amount=token_amount,
                price=price,
                total_value=trade_value,
                signal_confidence=confidence,
                status=TradeStatus.EXECUTED,
                created_at=datetime.utcnow(),
                executed_at=datetime.utcnow()
            )
            
            # Update portfolio
            self.portfolio.usd_balance += trade_value
            del self.portfolio.token_holdings[token]
            
            # Calculate profit/loss from buy trades
            buy_trades = [t for t in self.trade_history if t.token == token and t.trade_type == TradeType.BUY]
            if buy_trades:
                avg_buy_price = sum(t.price for t in buy_trades) / len(buy_trades)
                profit_loss = (price - avg_buy_price) * token_amount
                trade.profit_loss = profit_loss
                self.portfolio.profit_loss += profit_loss
                
                if profit_loss > 0:
                    self.portfolio.winning_trades += 1
                    self.stats["profitable_trades"] += 1
                else:
                    self.portfolio.losing_trades += 1
                
                self.stats["total_profit"] += profit_loss
            
            # Add to history
            self.trade_history.append(trade)
            self.portfolio.trades_count += 1
            self.stats["total_trades"] += 1
            
            # Store in database
            await self.store_trade(trade)
            
            logger.info(
                f"🔴 SELL {token}: {token_amount:.6f} @ ${price:.2f} "
                f"(${trade_value:.2f}, {confidence:.1f}% confidence)"
            )
            
            await self.update_portfolio_value()
        
        except Exception as e:
            logger.error(f"Error executing sell order for {token}: {e}")
    
    async def monitor_active_trades(self):
        """Monitor active trades for stop-loss and take-profit"""
        try:
            for trade_id, trade in list(self.active_trades.items()):
                if trade.trade_type != TradeType.BUY:
                    continue
                
                current_price = await self.get_current_price(trade.token)
                if not current_price:
                    continue
                
                # Check stop-loss
                if trade.stop_loss and current_price <= trade.stop_loss:
                    await self.close_position(trade, current_price, "Stop Loss")
                    continue
                
                # Check take-profit
                if trade.take_profit and current_price >= trade.take_profit:
                    await self.close_position(trade, current_price, "Take Profit")
                    continue
        
        except Exception as e:
            logger.error(f"Error monitoring active trades: {e}")
    
    async def close_position(self, trade: MockTrade, current_price: Decimal, reason: str):
        """Close an active position"""
        try:
            # Execute sell order
            await self.execute_sell_order(
                token=trade.token,
                price=current_price,
                confidence=100.0,  # Automatic close
                signal_data={}
            )
            
            # Remove from active trades
            if trade.id in self.active_trades:
                del self.active_trades[trade.id]
            
            profit_pct = ((current_price - trade.price) / trade.price) * 100
            
            logger.info(
                f"🎯 {reason}: {trade.token} @ ${current_price:.2f} "
                f"({profit_pct:+.2f}% from ${trade.price:.2f})"
            )
        
        except Exception as e:
            logger.error(f"Error closing position for {trade.token}: {e}")
    
    async def get_current_price(self, token: str) -> Optional[Decimal]:
        """Get current price for a token"""
        try:
            # For demo purposes, use mock prices
            mock_prices = {
                "BTC": Decimal("67500.00"),
                "ETH": Decimal("3200.00"),
                "SOL": Decimal("180.00"),
                "BNB": Decimal("420.00"),
                "XRP": Decimal("2.10"),
                "ADA": Decimal("1.25"),
                "DOGE": Decimal("0.35"),
                "MATIC": Decimal("0.85"),
                "DOT": Decimal("18.50"),
                "LTC": Decimal("280.00"),
                "TRX": Decimal("0.22"),
                "AVAX": Decimal("45.00"),
                "LINK": Decimal("28.00"),
                "ATOM": Decimal("12.50"),
                "UNI": Decimal("15.00"),
                "ETC": Decimal("35.00")
            }
            
            if token in mock_prices:
                # Add some random variation (±2%)
                import random
                base_price = mock_prices[token]
                variation = random.uniform(-0.02, 0.02)
                return base_price * (1 + Decimal(str(variation)))
            
            # Fallback to price oracle
            candles = await price_oracle.get_historical_prices(token, "1m", limit=1)
            if candles:
                return Decimal(str(candles[0]["close"]))
            return None
        except Exception as e:
            logger.error(f"Error getting price for {token}: {e}")
            return None
    
    def calculate_position_size(self, confidence: float) -> Decimal:
        """Calculate position size based on confidence"""
        # Base position size: 2-10% based on confidence
        base_size = 0.02  # 2%
        confidence_multiplier = (confidence - 70) / 30  # 0-1 for confidence 70-100
        position_size = base_size + (self.max_position_size - base_size) * confidence_multiplier
        return Decimal(str(min(position_size, self.max_position_size)))
    
    def has_active_position(self, token: str) -> bool:
        """Check if we have an active position in a token"""
        return token in self.portfolio.token_holdings
    
    async def update_portfolio_value(self):
        """Update total portfolio value"""
        try:
            total_value = self.portfolio.usd_balance
            
            for token, amount in self.portfolio.token_holdings.items():
                current_price = await self.get_current_price(token)
                if current_price:
                    total_value += amount * current_price
            
            self.portfolio.total_value = total_value
        
        except Exception as e:
            logger.error(f"Error updating portfolio value: {e}")
    
    async def store_trade(self, trade: MockTrade):
        """Store trade in database"""
        try:
            from src.models.mock_trading import MockTrade as MockTradeModel
            from src.config.database import AsyncSessionLocal
            
            async with AsyncSessionLocal() as db:
                db_trade = MockTradeModel(
                    trade_id=trade.id,
                    token=trade.token,
                    trade_type=trade.trade_type.value,
                    amount=float(trade.amount),
                    price=float(trade.price),
                    total_value=float(trade.total_value),
                    signal_confidence=trade.signal_confidence,
                    status=trade.status.value,
                    created_at=trade.created_at,
                    executed_at=trade.executed_at,
                    stop_loss=float(trade.stop_loss) if trade.stop_loss else None,
                    take_profit=float(trade.take_profit) if trade.take_profit else None,
                    profit_loss=float(trade.profit_loss) if trade.profit_loss else None
                )
                db.add(db_trade)
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to store trade in database: {e}")
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get portfolio summary"""
        return {
            "usd_balance": str(self.portfolio.usd_balance),
            "token_holdings": {k: str(v) for k, v in self.portfolio.token_holdings.items()},
            "total_value": str(self.portfolio.total_value),
            "profit_loss": str(self.portfolio.profit_loss),
            "roi_percentage": self.portfolio.get_roi(),
            "trades_count": self.portfolio.trades_count,
            "win_rate": self.portfolio.get_win_rate(),
            "winning_trades": self.portfolio.winning_trades,
            "losing_trades": self.portfolio.losing_trades
        }
    
    def get_recent_trades(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent trades"""
        recent_trades = sorted(self.trade_history, key=lambda t: t.created_at, reverse=True)
        return [trade.to_dict() for trade in recent_trades[:limit]]
    
    def get_active_positions(self) -> List[Dict[str, Any]]:
        """Get active positions"""
        return [trade.to_dict() for trade in self.active_trades.values()]
    
    def get_trading_stats(self) -> Dict[str, Any]:
        """Get trading statistics"""
        return {
            "total_trades": self.stats["total_trades"],
            "profitable_trades": self.stats["profitable_trades"],
            "win_rate": (self.stats["profitable_trades"] / max(self.stats["total_trades"], 1)) * 100,
            "total_profit": str(self.stats["total_profit"]),
            "roi_percentage": self.portfolio.get_roi(),
            "started_at": self.stats["started_at"].isoformat(),
            "is_enabled": self.is_enabled,
            "min_confidence": self.min_confidence,
            "max_position_size": self.max_position_size
        }
    
    def enable_trading(self):
        """Enable automated trading"""
        self.is_enabled = True
        logger.info("🟢 Automated trading enabled")
    
    def disable_trading(self):
        """Disable automated trading"""
        self.is_enabled = False
        logger.info("🔴 Automated trading disabled")
    
    def update_settings(self, settings: Dict[str, Any]):
        """Update trading settings"""
        if "min_confidence" in settings:
            self.min_confidence = float(settings["min_confidence"])
        if "max_position_size" in settings:
            self.max_position_size = float(settings["max_position_size"])
        if "stop_loss_pct" in settings:
            self.stop_loss_pct = float(settings["stop_loss_pct"])
        if "take_profit_pct" in settings:
            self.take_profit_pct = float(settings["take_profit_pct"])
        
        logger.info(f"Trading settings updated: {settings}")


# Global auto trader instance
auto_trader = AutoTrader()