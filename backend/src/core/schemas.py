"""
Pydantic schemas for API request/response models
"""
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, List
from datetime import datetime
from decimal import Decimal


# Auth schemas
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: Optional[str]
    is_active: bool
    is_admin: bool
    created_at: datetime
    wallet_addresses: Optional[str]
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


# Trading schemas
class SwapRequest(BaseModel):
    chain_id: int
    from_token: str
    to_token: str
    amount: str
    slippage: Optional[float] = 1.0


class SwapResponse(BaseModel):
    quote: Dict
    transaction_data: Optional[Dict] = None
    estimated_gas: Optional[str] = None


class BridgeRequest(BaseModel):
    from_chain: int
    to_chain: int
    from_token: str
    to_token: str
    amount: str
    to_address: str
    slippage: Optional[float] = 0.03


class BridgeResponse(BaseModel):
    quote: Dict
    routes: Optional[List[Dict]] = None


# Portfolio schemas
class PortfolioItem(BaseModel):
    chain_id: int
    token_address: str
    token_symbol: str
    token_name: Optional[str]
    balance: Decimal
    usd_value: Decimal
    
    class Config:
        from_attributes = True


class PortfolioSummary(BaseModel):
    total_usd_value: Decimal
    chain_breakdown: Dict[str, Decimal]
    top_tokens: List[PortfolioItem]


class TransactionCreate(BaseModel):
    tx_hash: str
    chain_id: int
    type: str
    from_token_address: Optional[str] = None
    from_token_symbol: Optional[str] = None
    from_amount: Optional[Decimal] = None
    to_token_address: Optional[str] = None
    to_token_symbol: Optional[str] = None
    to_amount: Optional[Decimal] = None
    to_chain_id: Optional[int] = None


class TransactionResponse(BaseModel):
    id: int
    tx_hash: str
    chain_id: int
    type: str
    status: str
    from_token_symbol: Optional[str]
    to_token_symbol: Optional[str]
    from_amount: Optional[Decimal]
    to_amount: Optional[Decimal]
    usd_value: Optional[Decimal]
    created_at: datetime
    confirmed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# Price schemas
class TokenPrice(BaseModel):
    token_address: str
    token_symbol: str
    price_usd: Decimal
    last_updated: datetime


class PriceHistory(BaseModel):
    token_id: str
    prices: List[List[float]]  # [timestamp, price] pairs


# Intent validation schemas
class IntentValidationRequest(BaseModel):
    user: str
    source_chain: int
    destination_chain: int
    input_token: str
    output_token: str
    input_amount: str
    minimum_output_amount: str
    deadline: int
    nonce: int
    recipient: Optional[str] = None


class ValidationResponse(BaseModel):
    is_valid: bool
    result: str
    reason: str
    liquidity_info: Optional[Dict] = None
    price_impact: Optional[Decimal] = None
    estimated_output: Optional[str] = None
    gas_estimate: Optional[str] = None


class LiquidityCheckRequest(BaseModel):
    token_address: str
    amount: str


class LiquidityCheckResponse(BaseModel):
    token_address: str
    amount: str
    liquidity_by_chain: Dict[int, Dict]