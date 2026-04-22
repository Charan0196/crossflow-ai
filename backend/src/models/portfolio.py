"""
Portfolio model for tracking user assets across chains
"""
from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from src.config.database import Base


class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Chain and token info
    chain_id = Column(Integer, nullable=False)  # 1=Ethereum, 137=Polygon, etc.
    token_address = Column(String, nullable=False)  # Contract address or "native"
    token_symbol = Column(String, nullable=False)
    token_name = Column(String)
    token_decimals = Column(Integer, default=18)
    
    # Balance info
    balance = Column(Numeric(precision=36, scale=18), default=0)
    usd_value = Column(Numeric(precision=20, scale=8), default=0)
    
    # Metadata
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="portfolios")


class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Snapshot data
    total_usd_value = Column(Numeric(precision=20, scale=8), nullable=False)
    chain_breakdown = Column(Text)  # JSON string of {chain_id: usd_value}
    token_breakdown = Column(Text)  # JSON string of token allocations
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())