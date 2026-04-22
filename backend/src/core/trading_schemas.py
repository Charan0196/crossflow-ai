"""
Phase 5: Trading API Schemas

Pydantic models for API request/response validation
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime
from enum import Enum


# Enums
class OrderTypeEnum(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"


class OrderSideEnum(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderStatusEnum(str, Enum):
    PENDING = "pending"
    OPEN = "open"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    FAILED = "failed"


class SignalTypeEnum(str, Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


# Swap Schemas
class SwapQuoteRequest(BaseModel):
    """Request for swap quote"""
    from_token: str = Field(..., description="Source token address")
    to_token: str = Field(..., description="Destination token address")
    amount: str = Field(..., description="Amount to swap (in token units)")
    chain_id: int = Field(..., description="Chain ID")
    slippage_tolerance: float = Field(default=0.5, ge=0, le=50, description="Slippage tolerance %")
    user_address: str = Field(..., description="User wallet address")


class SwapQuoteResponse(BaseModel):
    """Response with swap quote"""
    from_token: str
    to_token: str
    from_amount: str
    to_amount: str
    to_amount_min: str
    price_impact: float
    route: List[str]
    gas_estimate: int
    gas_fee_usd: str
    protocol_fee: str
    total_fee_usd: str
    exchange_rate: str
    expires_at: int
    dex_name: str


class SwapExecuteRequest(BaseModel):
    """Request to execute swap"""
    from_token: str
    to_token: str
    amount: str
    chain_id: int
    slippage_tolerance: float = 0.5
    user_address: str
    deadline: Optional[int] = None  # Unix timestamp


class SwapExecuteResponse(BaseModel):
    """Response after swap execution"""
    tx_hash: str
    status: str
    from_amount: str
    to_amount: Optional[str]
    gas_used: Optional[int]
    explorer_url: str


# Bridge Schemas
class BridgeQuoteRequest(BaseModel):
    """Request for bridge quote"""
    from_token: str
    to_token: str
    amount: str
    from_chain_id: int
    to_chain_id: int
    user_address: str
    slippage_tolerance: float = 0.5


class BridgeQuoteResponse(BaseModel):
    """Response with bridge quote"""
    from_token: str
    to_token: str
    from_chain_id: int
    to_chain_id: int
    from_amount: str
    to_amount: str
    bridge_fee: str
    gas_fee_usd: str
    total_fee_usd: str
    estimated_time: int  # seconds
    bridge_name: str
    expires_at: int


class BridgeExecuteRequest(BaseModel):
    """Request to execute bridge"""
    from_token: str
    to_token: str
    amount: str
    from_chain_id: int
    to_chain_id: int
    user_address: str
    slippage_tolerance: float = 0.5


class BridgeExecuteResponse(BaseModel):
    """Response after bridge execution"""
    source_tx_hash: str
    status: str
    from_amount: str
    estimated_arrival: int  # Unix timestamp
    explorer_url: str


# Order Schemas
class CreateOrderRequest(BaseModel):
    """Request to create an order"""
    order_type: OrderTypeEnum
    side: OrderSideEnum
    from_token: str
    to_token: str
    amount: str
    chain_id: int
    price: Optional[str] = None  # For limit orders
    trigger_price: Optional[str] = None  # For stop-loss/take-profit
    expires_in: Optional[int] = None  # Seconds until expiry
    
    @validator('price')
    def validate_price(cls, v, values):
        if values.get('order_type') == OrderTypeEnum.LIMIT and not v:
            raise ValueError('Price required for limit orders')
        return v
    
    @validator('trigger_price')
    def validate_trigger_price(cls, v, values):
        if values.get('order_type') in [OrderTypeEnum.STOP_LOSS, OrderTypeEnum.TAKE_PROFIT] and not v:
            raise ValueError('Trigger price required for stop-loss/take-profit orders')
        return v


class OrderResponse(BaseModel):
    """Order response"""
    id: str
    order_type: str
    side: str
    status: str
    from_token: str
    to_token: str
    from_token_symbol: str
    to_token_symbol: str
    amount: str
    filled_amount: str
    price: Optional[str]
    trigger_price: Optional[str]
    executed_price: Optional[str]
    chain_id: int
    tx_hash: Optional[str]
    protocol_fee: str
    gas_fee: str
    created_at: str
    filled_at: Optional[str]
    expires_at: Optional[str]


class OrderListResponse(BaseModel):
    """List of orders"""
    orders: List[OrderResponse]
    total: int
    page: int
    page_size: int


# Transaction History Schemas
class TransactionRecordResponse(BaseModel):
    """Transaction record response"""
    id: str
    tx_hash: str
    tx_type: str
    status: str
    chain_id: int
    block_number: Optional[int]
    from_token: str
    to_token: str
    from_token_symbol: str
    to_token_symbol: str
    from_amount: str
    to_amount: Optional[str]
    gas_fee_usd: Optional[str]
    protocol_fee: str
    total_fee_usd: Optional[str]
    realized_pnl: Optional[str]
    explorer_url: str
    created_at: str
    confirmed_at: Optional[str]
    error_message: Optional[str]


class TransactionHistoryResponse(BaseModel):
    """Transaction history response"""
    transactions: List[TransactionRecordResponse]
    total: int
    page: int
    page_size: int
    total_volume_usd: str
    total_fees_usd: str
    total_pnl: str


# AI Signal Schemas
class SignalFactor(BaseModel):
    """Factor contributing to a signal"""
    name: str
    value: float
    weight: float
    description: str


class TradingSignalResponse(BaseModel):
    """AI trading signal response"""
    token: str
    signal_type: SignalTypeEnum
    confidence: float = Field(..., ge=0, le=100)
    target_price: str
    stop_loss: str
    take_profit: str
    timeframe: str
    explanation: str
    factors: List[SignalFactor]
    created_at: str
    expires_at: str


class SignalListResponse(BaseModel):
    """List of trading signals"""
    signals: List[TradingSignalResponse]
    accuracy_30d: float
    total_signals_30d: int


# Portfolio Schemas
class PortfolioMetricsResponse(BaseModel):
    """Portfolio metrics response"""
    total_value_usd: str
    allocations: Dict[str, float]  # token -> percentage
    chain_distribution: Dict[str, float]  # chain -> percentage
    risk_score: float
    sharpe_ratio: Optional[float]
    max_drawdown: Optional[float]
    concentration_risk: str  # LOW, MEDIUM, HIGH
    performance_24h: float
    performance_7d: float
    performance_30d: float


class RebalanceRecommendation(BaseModel):
    """Rebalancing recommendation"""
    action: str  # BUY or SELL
    token: str
    token_symbol: str
    amount: str
    amount_usd: str
    reason: str
    expected_improvement: float
    gas_cost_usd: str
    chain_id: int


class RebalanceResponse(BaseModel):
    """Rebalancing recommendations response"""
    recommendations: List[RebalanceRecommendation]
    current_risk_score: float
    projected_risk_score: float
    total_gas_cost_usd: str


# Chart Schemas
class ChartDataRequest(BaseModel):
    """Request for chart data"""
    symbol: str
    timeframe: str = "1h"
    limit: int = Field(default=100, ge=1, le=1000)
    indicators: List[str] = []


class OHLCV(BaseModel):
    """OHLCV candle data"""
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float


class ChartDataResponse(BaseModel):
    """Chart data response"""
    symbol: str
    timeframe: str
    candles: List[OHLCV]
    indicators: Dict[str, List[float]]


class ChartConfigRequest(BaseModel):
    """Request to save chart configuration"""
    name: str
    symbol: str
    timeframe: str
    indicators: List[Dict[str, Any]]
    drawings: List[Dict[str, Any]] = []
    layout: Dict[str, Any] = {}


class ChartConfigResponse(BaseModel):
    """Chart configuration response"""
    id: str
    name: str
    symbol: str
    timeframe: str
    indicators: List[Dict[str, Any]]
    drawings: List[Dict[str, Any]]
    layout: Dict[str, Any]
    created_at: str
    updated_at: str


# Price Alert Schemas
class CreatePriceAlertRequest(BaseModel):
    """Request to create price alert"""
    token_symbol: str
    chain_id: int
    target_price: str
    condition: str = Field(..., pattern="^(above|below)$")


class PriceAlertResponse(BaseModel):
    """Price alert response"""
    id: str
    token_symbol: str
    chain_id: int
    target_price: str
    condition: str
    is_active: bool
    triggered: bool
    triggered_at: Optional[str]
    triggered_price: Optional[str]
    created_at: str


# Notification Preferences
class NotificationPreferencesRequest(BaseModel):
    """Update notification preferences"""
    notify_on_fill: Optional[bool] = None
    notify_on_signal: Optional[bool] = None
    notify_on_price_alert: Optional[bool] = None


class TradingPreferencesRequest(BaseModel):
    """Update trading preferences"""
    risk_tolerance: Optional[float] = Field(None, ge=0, le=1)
    default_slippage: Optional[float] = Field(None, ge=0, le=50)
    max_slippage: Optional[float] = Field(None, ge=0, le=50)
    daily_limit: Optional[str] = None
    mev_protection_enabled: Optional[bool] = None
    favorite_tokens: Optional[List[str]] = None


class TradingPreferencesResponse(BaseModel):
    """Trading preferences response"""
    risk_tolerance: float
    default_slippage: float
    max_slippage: float
    daily_limit: str
    mev_protection_enabled: bool
    favorite_tokens: List[str]
    notify_on_fill: bool
    notify_on_signal: bool
    notify_on_price_alert: bool
