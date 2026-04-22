"""
User model for authentication and profile management
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from src.config.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    # Profile info
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    
    # Wallet addresses (JSON stored as text)
    wallet_addresses = Column(Text)  # JSON string of {chain: address}
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    
    # Relationships
    portfolios = relationship("Portfolio", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")
    transaction_records = relationship("TransactionRecord", back_populates="user")
    
    # Phase 5 relationships
    orders = relationship("Order", back_populates="user")
    price_alerts = relationship("PriceAlert", back_populates="user")
    trading_preferences = relationship("TradingPreferences", back_populates="user", uselist=False)
    chart_configs = relationship("ChartConfiguration", back_populates="user")