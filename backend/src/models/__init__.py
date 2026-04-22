"""
Models package initialization
"""
from .user import User
from .portfolio import Portfolio, PortfolioSnapshot
from .transaction import Transaction, TransactionType, TransactionStatus
from .solver import (
    Solver, 
    SolverStatus, 
    SolverTier, 
    SolverPerformanceMetrics, 
    SolverReputationScore, 
    SolverStakeInfo
)
from .trading import (
    Order,
    OrderType,
    OrderSide,
    OrderStatus,
    TransactionRecord,
    TransactionType as TxType,
    TransactionStatus as TxStatus,
    PriceAlert,
    TradingPreferences,
    ChartConfiguration,
    AutonomousTrade,
    WalletSnapshot,
    AISignal,
)
from .mock_trading import (
    MockTrade,
    MockTradeStatus,
    MockTradeType,
    MockPortfolioSnapshot,
)

__all__ = [
    "User",
    "Portfolio", 
    "PortfolioSnapshot",
    "Transaction",
    "TransactionType",
    "TransactionStatus",
    "Solver",
    "SolverStatus",
    "SolverTier",
    "SolverPerformanceMetrics",
    "SolverReputationScore",
    "SolverStakeInfo",
    # Phase 5 models
    "Order",
    "OrderType",
    "OrderSide",
    "OrderStatus",
    "TransactionRecord",
    "TxType",
    "TxStatus",
    "PriceAlert",
    "TradingPreferences",
    "ChartConfiguration",
    # Autonomous trading models
    "AutonomousTrade",
    "WalletSnapshot",
    "AISignal",
    # Mock trading models
    "MockTrade",
    "MockTradeStatus",
    "MockTradeType",
    "MockPortfolioSnapshot",
]