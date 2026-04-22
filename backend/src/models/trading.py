"""
Phase 5: Trading Data Models

Database models for:
- Orders (market, limit, stop-loss, take-profit)
- Transaction records
- Price alerts
- User trading preferences
"""

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, 
    ForeignKey, Enum as SQLEnum, Text, Numeric, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, Dict, Any
import uuid

from src.config.database import Base


class OrderType(str, Enum):
    """Order types"""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"


class OrderSide(str, Enum):
    """Order side (buy/sell)"""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(str, Enum):
    """Order status"""
    PENDING = "pending"
    OPEN = "open"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    FAILED = "failed"


class TransactionType(str, Enum):
    """Transaction types"""
    SWAP = "swap"
    BRIDGE = "bridge"
    APPROVE = "approve"
    TRANSFER = "transfer"


class TransactionStatus(str, Enum):
    """Transaction status"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"


class Order(Base):
    """Order model for all order types"""
    __tablename__ = "orders"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    # Order details
    order_type = Column(SQLEnum(OrderType), nullable=False)
    side = Column(SQLEnum(OrderSide), nullable=False)
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    
    # Token pair
    from_token = Column(String(42), nullable=False)
    to_token = Column(String(42), nullable=False)
    from_token_symbol = Column(String(20), nullable=False)
    to_token_symbol = Column(String(20), nullable=False)
    
    # Amounts
    amount = Column(Numeric(36, 18), nullable=False)
    filled_amount = Column(Numeric(36, 18), default=0)
    
    # Prices
    price = Column(Numeric(36, 18), nullable=True)  # For limit orders
    trigger_price = Column(Numeric(36, 18), nullable=True)  # For stop-loss/take-profit
    executed_price = Column(Numeric(36, 18), nullable=True)
    
    # Chain info
    chain_id = Column(Integer, nullable=False)
    
    # Execution details
    tx_hash = Column(String(66), nullable=True)
    gas_used = Column(Integer, nullable=True)
    gas_price = Column(Numeric(36, 18), nullable=True)
    
    # Fees
    protocol_fee = Column(Numeric(36, 18), default=0)
    gas_fee = Column(Numeric(36, 18), default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    filled_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="orders")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "order_type": self.order_type.value,
            "side": self.side.value,
            "status": self.status.value,
            "from_token": self.from_token,
            "to_token": self.to_token,
            "from_token_symbol": self.from_token_symbol,
            "to_token_symbol": self.to_token_symbol,
            "amount": str(self.amount),
            "filled_amount": str(self.filled_amount),
            "price": str(self.price) if self.price else None,
            "trigger_price": str(self.trigger_price) if self.trigger_price else None,
            "executed_price": str(self.executed_price) if self.executed_price else None,
            "chain_id": self.chain_id,
            "tx_hash": self.tx_hash,
            "gas_used": self.gas_used,
            "protocol_fee": str(self.protocol_fee),
            "gas_fee": str(self.gas_fee),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "filled_at": self.filled_at.isoformat() if self.filled_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }


class TransactionRecord(Base):
    """Transaction record for all blockchain transactions"""
    __tablename__ = "transaction_records"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    # Transaction details
    tx_hash = Column(String(66), nullable=False, unique=True, index=True)
    tx_type = Column(SQLEnum(TransactionType), nullable=False)
    status = Column(SQLEnum(TransactionStatus), default=TransactionStatus.PENDING)
    
    # Chain info
    chain_id = Column(Integer, nullable=False)
    block_number = Column(Integer, nullable=True)
    
    # Token details
    from_token = Column(String(42), nullable=False)
    to_token = Column(String(42), nullable=False)
    from_token_symbol = Column(String(20), nullable=False)
    to_token_symbol = Column(String(20), nullable=False)
    
    # Amounts
    from_amount = Column(Numeric(36, 18), nullable=False)
    to_amount = Column(Numeric(36, 18), nullable=True)
    
    # Prices at execution
    from_token_price_usd = Column(Numeric(36, 18), nullable=True)
    to_token_price_usd = Column(Numeric(36, 18), nullable=True)
    
    # Fees
    gas_used = Column(Integer, nullable=True)
    gas_price = Column(Numeric(36, 18), nullable=True)
    gas_fee_usd = Column(Numeric(36, 18), nullable=True)
    protocol_fee = Column(Numeric(36, 18), default=0)
    bridge_fee = Column(Numeric(36, 18), nullable=True)
    total_fee_usd = Column(Numeric(36, 18), nullable=True)
    
    # P&L tracking
    entry_price = Column(Numeric(36, 18), nullable=True)
    realized_pnl = Column(Numeric(36, 18), nullable=True)
    
    # Bridge-specific fields
    destination_chain_id = Column(Integer, nullable=True)
    destination_tx_hash = Column(String(66), nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    confirmed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="transaction_records")
    
    @property
    def explorer_url(self) -> str:
        """Generate block explorer URL"""
        from src.config.phase5_config import phase5_config
        return phase5_config.get_explorer_url(self.chain_id, self.tx_hash)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "tx_hash": self.tx_hash,
            "tx_type": self.tx_type.value,
            "status": self.status.value,
            "chain_id": self.chain_id,
            "block_number": self.block_number,
            "from_token": self.from_token,
            "to_token": self.to_token,
            "from_token_symbol": self.from_token_symbol,
            "to_token_symbol": self.to_token_symbol,
            "from_amount": str(self.from_amount),
            "to_amount": str(self.to_amount) if self.to_amount else None,
            "gas_fee_usd": str(self.gas_fee_usd) if self.gas_fee_usd else None,
            "protocol_fee": str(self.protocol_fee),
            "total_fee_usd": str(self.total_fee_usd) if self.total_fee_usd else None,
            "realized_pnl": str(self.realized_pnl) if self.realized_pnl else None,
            "explorer_url": self.explorer_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "confirmed_at": self.confirmed_at.isoformat() if self.confirmed_at else None,
            "error_message": self.error_message,
        }


class PriceAlert(Base):
    """Price alert configuration"""
    __tablename__ = "price_alerts"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    # Alert configuration
    token_symbol = Column(String(20), nullable=False)
    chain_id = Column(Integer, nullable=False)
    target_price = Column(Numeric(36, 18), nullable=False)
    condition = Column(String(10), nullable=False)  # "above" or "below"
    
    # Status
    is_active = Column(Boolean, default=True)
    triggered = Column(Boolean, default=False)
    triggered_at = Column(DateTime, nullable=True)
    triggered_price = Column(Numeric(36, 18), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="price_alerts")


class TradingPreferences(Base):
    """User trading preferences"""
    __tablename__ = "trading_preferences"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, unique=True)
    
    # Risk settings
    risk_tolerance = Column(Float, default=0.5)  # 0-1 scale
    default_slippage = Column(Float, default=0.5)  # percentage
    max_slippage = Column(Float, default=5.0)  # percentage
    
    # Limits
    daily_limit = Column(Numeric(36, 18), default=100000)
    single_trade_limit = Column(Numeric(36, 18), default=10000)
    
    # MEV protection
    mev_protection_enabled = Column(Boolean, default=True)
    
    # Notifications
    notify_on_fill = Column(Boolean, default=True)
    notify_on_signal = Column(Boolean, default=True)
    notify_on_price_alert = Column(Boolean, default=True)
    
    # Favorite tokens (JSON array)
    favorite_tokens = Column(JSON, default=list)
    
    # Chart preferences (JSON)
    chart_preferences = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="trading_preferences")


class ChartConfiguration(Base):
    """Saved chart configurations"""
    __tablename__ = "chart_configurations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    # Configuration
    name = Column(String(100), nullable=False)
    symbol = Column(String(20), nullable=False)
    timeframe = Column(String(10), nullable=False)
    
    # Indicators (JSON array)
    indicators = Column(JSON, default=list)
    
    # Drawing tools (JSON array)
    drawings = Column(JSON, default=list)
    
    # Layout settings (JSON)
    layout = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="chart_configs")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "indicators": self.indicators,
            "drawings": self.drawings,
            "layout": self.layout,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AutonomousTrade(Base):
    """Autonomous trade records for unified trading integration"""
    __tablename__ = "autonomous_trades"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    wallet_address = Column(String(42), nullable=False, index=True)
    tx_hash = Column(String(66), unique=True, nullable=False, index=True)
    timestamp = Column(Integer, nullable=False, index=True)
    
    # Token details
    from_token = Column(String(42), nullable=False)
    to_token = Column(String(42), nullable=False)
    from_token_symbol = Column(String(20), nullable=False)
    to_token_symbol = Column(String(20), nullable=False)
    
    # Amounts
    from_amount = Column(Numeric(36, 18), nullable=False)
    to_amount = Column(Numeric(36, 18), nullable=False)
    
    # Fees and slippage
    gas_fee = Column(Numeric(36, 18), nullable=False)
    slippage = Column(Numeric(5, 2), nullable=False)
    
    # Status and type
    status = Column(String(20), nullable=False, index=True)  # pending, confirmed, failed
    trade_type = Column(String(10), nullable=False, index=True)  # manual, ai_executed
    
    # Performance tracking
    profit_loss = Column(Numeric(36, 18), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "wallet_address": self.wallet_address,
            "tx_hash": self.tx_hash,
            "timestamp": self.timestamp,
            "from_token": self.from_token,
            "to_token": self.to_token,
            "from_token_symbol": self.from_token_symbol,
            "to_token_symbol": self.to_token_symbol,
            "from_amount": str(self.from_amount),
            "to_amount": str(self.to_amount),
            "gas_fee": str(self.gas_fee),
            "slippage": str(self.slippage),
            "status": self.status,
            "trade_type": self.trade_type,
            "profit_loss": str(self.profit_loss) if self.profit_loss else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class WalletSnapshot(Base):
    """Daily wallet snapshots for performance tracking"""
    __tablename__ = "wallet_snapshots"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    wallet_address = Column(String(42), nullable=False, index=True)
    timestamp = Column(Integer, nullable=False, index=True)
    
    # Portfolio value
    total_value_usd = Column(Numeric(36, 2), nullable=False)
    eth_balance = Column(Numeric(36, 18), nullable=False)
    
    # Token balances (JSON)
    token_balances = Column(JSON, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "wallet_address": self.wallet_address,
            "timestamp": self.timestamp,
            "total_value_usd": str(self.total_value_usd),
            "eth_balance": str(self.eth_balance),
            "token_balances": self.token_balances,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AISignal(Base):
    """AI trading signals"""
    __tablename__ = "ai_signals"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(Integer, nullable=False, index=True)
    
    # Signal details
    action = Column(String(10), nullable=False)  # buy, sell
    token = Column(String(42), nullable=False)
    token_symbol = Column(String(20), nullable=False)
    confidence = Column(Numeric(5, 2), nullable=False)
    reason = Column(Text, nullable=True)
    
    # Execution tracking
    executed = Column(Boolean, default=False, index=True)
    trade_id = Column(Integer, ForeignKey("autonomous_trades.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    trade = relationship("AutonomousTrade", foreign_keys=[trade_id])
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "action": self.action,
            "token": self.token,
            "token_symbol": self.token_symbol,
            "confidence": str(self.confidence),
            "reason": self.reason,
            "executed": self.executed,
            "trade_id": self.trade_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
