"""
Transaction model for tracking all trading activities
"""
from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, Text, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from src.config.database import Base


class TransactionType(enum.Enum):
    SWAP = "swap"
    BRIDGE = "bridge"
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"


class TransactionStatus(enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Transaction identifiers
    tx_hash = Column(String, index=True)
    chain_id = Column(Integer, nullable=False)
    block_number = Column(Integer)
    
    # Transaction details
    type = Column(Enum(TransactionType), nullable=False)
    status = Column(Enum(TransactionStatus), default=TransactionStatus.PENDING)
    
    # Token details
    from_token_address = Column(String)
    from_token_symbol = Column(String)
    from_amount = Column(Numeric(precision=36, scale=18))
    
    to_token_address = Column(String)
    to_token_symbol = Column(String)
    to_amount = Column(Numeric(precision=36, scale=18))
    
    # Cross-chain details (for bridges)
    to_chain_id = Column(Integer)
    bridge_provider = Column(String)
    
    # Financial details
    gas_used = Column(Numeric(precision=36, scale=18))
    gas_price = Column(Numeric(precision=36, scale=18))
    usd_value = Column(Numeric(precision=20, scale=8))
    
    # Metadata
    raw_data = Column(Text)  # JSON string of full transaction data
    error_message = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    confirmed_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="transactions")