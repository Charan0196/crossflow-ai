"""
Type definitions for CrossFlow AI Python SDK
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
from datetime import datetime


@dataclass
class ClientConfig:
    api_url: str
    token: Optional[str] = None
    timeout: int = 30
    retries: int = 3


@dataclass
class IntentCreateRequest:
    source_chain: int
    destination_chain: int
    input_token: str
    output_token: str
    input_amount: str
    minimum_output_amount: str
    deadline: Optional[int] = None
    recipient: Optional[str] = None
    max_gas_price: Optional[str] = None
    slippage_tolerance: Optional[float] = 0.5


@dataclass
class Intent:
    intent_id: str
    status: str
    user_address: str
    source_chain: int
    destination_chain: int
    input_token: str
    output_token: str
    input_amount: str
    minimum_output_amount: str
    deadline: int
    created_at: str
    updated_at: str
    estimated_execution_time: Optional[int] = None
    estimated_gas_cost: Optional[str] = None
    solver_address: Optional[str] = None
    transaction_hash: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class IntentProgress:
    created: bool
    validated: bool
    submitted: bool
    solver_selected: bool
    funds_locked: bool
    executing: bool
    completed: bool
    failed: bool


@dataclass
class ExecutionDetails:
    execution_time_ms: int
    gas_used: str
    fees_paid: str
    solver_address: str
    output_amount: str


@dataclass
class ErrorDetails:
    error_message: str
    execution_time_ms: int
    solver_address: str


@dataclass
class IntentStatus:
    intent_id: str
    status: str
    progress: IntentProgress
    execution_details: Optional[ExecutionDetails] = None
    error_details: Optional[ErrorDetails] = None
    estimated_completion: Optional[str] = None


@dataclass
class IntentListResponse:
    intents: List[Intent]
    total_count: int
    page: int
    page_size: int
    has_next: bool


@dataclass
class IntentListOptions:
    page: Optional[int] = None
    page_size: Optional[int] = None
    status: Optional[str] = None
    source_chain: Optional[int] = None
    destination_chain: Optional[int] = None


@dataclass
class IntentEstimate:
    intent_id: str
    estimated_execution_time_seconds: int
    estimated_gas_cost_eth: str
    estimated_gas_cost_usd: str
    estimated_output_amount: str
    price_impact_percentage: float
    updated_at: str


@dataclass
class PriceData:
    token_pair: str
    price: str
    volume_24h: str
    change_24h: str
    change_percent_24h: str
    high_24h: str
    low_24h: str
    timestamp: float
    source: str


@dataclass
class WebSocketMessage:
    type: str
    data: Dict[str, Any]
    timestamp: float
    message_id: str


@dataclass
class WebSocketConfig:
    reconnect: bool = True
    reconnect_interval: int = 5
    max_reconnect_attempts: int = 10
    heartbeat_interval: int = 30


@dataclass
class AuthResponse:
    access_token: str
    token_type: str


@dataclass
class LoginRequest:
    username: str
    password: str


class ChainId(Enum):
    ETHEREUM = 1
    POLYGON = 137
    ARBITRUM = 42161
    OPTIMISM = 10
    BSC = 56
    BASE = 8453


class IntentStatusType(Enum):
    CREATED = "created"
    VALIDATED = "validated"
    SUBMITTED = "submitted"
    SOLVER_SELECTED = "solver_selected"
    FUNDS_LOCKED = "funds_locked"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WebSocketEventType(Enum):
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    ERROR = "error"
    MESSAGE = "message"
    INTENT_STATUS_UPDATE = "intent_status_update"
    PRICE_UPDATE = "price_update"
    SOLVER_BID_UPDATE = "solver_bid_update"
    SYSTEM_NOTIFICATION = "system_notification"
    HEARTBEAT = "heartbeat"