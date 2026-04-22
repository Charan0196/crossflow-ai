"""
Mock Trading Models

Database models for automated mock trading system
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum

from src.config.database import Base


class MockTradeStatus(Enum):
    """Mock trade status enumeration"""
    PENDING = "pending"
    EXECUTED = "executed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class MockTradeType(Enum):
    """Mock trade type enumeration"""
    BUY = "buy"
    SELL = "sell"


class MockTrade(Base):
    """Mock trade execution record"""
    __tablename__ = "mock_trades"
    
    id = Column(Integer, primary_key=True, index=True)
    trade_id = Column(String(100), unique=True, index=True, nullable=False)
    token = Column(String(20), nullable=False, index=True)
    trade_type = Column(String(10), nullable=False)  # buy/sell
    amount = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    total_value = Column(Float, nullable=False)
    signal_confidence = Column(Float, nullable=False)
    status = Column(String(20), nullable=False, default="executed")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    executed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Risk management
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    profit_loss = Column(Float, nullable=True)
    
    # Additional metadata
    signal_data = Column(Text, nullable=True)  # JSON string of signal data
    notes = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<MockTrade {self.trade_id}: {self.trade_type} {self.amount} {self.token} @ ${self.price}>"


class MockPortfolioSnapshot(Base):
    """Portfolio snapshot for tracking performance over time"""
    __tablename__ = "mock_portfolio_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Portfolio values
    usd_balance = Column(Float, nullable=False)
    total_value = Column(Float, nullable=False)
    profit_loss = Column(Float, nullable=False)
    
    # Performance metrics
    trades_count = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    roi_percentage = Column(Float, default=0.0)
    
    # Token holdings (JSON string)
    token_holdings = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<MockPortfolioSnapshot {self.timestamp}: ${self.total_value:.2f} ({self.roi_percentage:+.2f}%)>"