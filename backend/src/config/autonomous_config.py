"""
Autonomous Trading Configuration

All configuration constants for autonomous trading features
"""

import os
from decimal import Decimal


# Demo Wallet Configuration
DEMO_WALLET_ADDRESS = os.getenv("DEMO_WALLET_ADDRESS", "0x6739659248061A54E0f4de8f2cd60278B69468b3")

# Risk Management Parameters
RISK_POSITION_SIZE_LIMIT = Decimal(os.getenv("RISK_POSITION_SIZE_LIMIT", "0.10"))  # 10% of portfolio
RISK_DRAWDOWN_LIMIT = Decimal(os.getenv("RISK_DRAWDOWN_LIMIT", "0.20"))  # 20% circuit breaker
RISK_DAILY_LOSS_LIMIT = Decimal(os.getenv("RISK_DAILY_LOSS_LIMIT", "0.05"))  # 5% daily loss limit
RISK_MIN_GAS_BALANCE = Decimal(os.getenv("RISK_MIN_GAS_BALANCE", "0.01"))  # 0.01 ETH minimum
RISK_STOP_LOSS_PCT = Decimal(os.getenv("RISK_STOP_LOSS_PCT", "0.05"))  # 5% below entry
RISK_TAKE_PROFIT_PCT = Decimal(os.getenv("RISK_TAKE_PROFIT_PCT", "0.10"))  # 10% above entry

# AI Trading Parameters
AI_CONFIDENCE_THRESHOLD = float(os.getenv("AI_CONFIDENCE_THRESHOLD", "75"))  # 75% minimum confidence
AI_SIGNAL_GENERATION_INTERVAL = int(os.getenv("AI_SIGNAL_GENERATION_INTERVAL", "60"))  # 60 seconds
AI_MAX_CONCURRENT_TRADES = int(os.getenv("AI_MAX_CONCURRENT_TRADES", "3"))  # Max 3 concurrent trades

# Wallet Service Configuration
WALLET_CACHE_TTL = int(os.getenv("WALLET_CACHE_TTL", "10"))  # 10 second cache
WALLET_BALANCE_REFRESH_INTERVAL = int(os.getenv("WALLET_BALANCE_REFRESH_INTERVAL", "30"))  # 30 seconds

# Trade History Configuration
TRADE_HISTORY_PAGE_SIZE = int(os.getenv("TRADE_HISTORY_PAGE_SIZE", "20"))  # 20 trades per page
TRADE_HISTORY_MAX_PAGES = int(os.getenv("TRADE_HISTORY_MAX_PAGES", "100"))  # Max 100 pages

# Performance Analytics Configuration
PERFORMANCE_TIME_RANGES = ["24h", "7d", "30d", "all"]
PERFORMANCE_SHARPE_RISK_FREE_RATE = Decimal(os.getenv("PERFORMANCE_SHARPE_RISK_FREE_RATE", "0.02"))  # 2% annual

# WebSocket Configuration
WS_RECONNECT_MAX_ATTEMPTS = int(os.getenv("WS_RECONNECT_MAX_ATTEMPTS", "10"))
WS_RECONNECT_BASE_DELAY = int(os.getenv("WS_RECONNECT_BASE_DELAY", "1000"))  # 1 second
WS_RECONNECT_MAX_DELAY = int(os.getenv("WS_RECONNECT_MAX_DELAY", "60000"))  # 60 seconds

# Database Configuration
DB_CONNECTION_POOL_SIZE = int(os.getenv("DB_CONNECTION_POOL_SIZE", "10"))
DB_CACHE_MAX_SIZE = int(os.getenv("DB_CACHE_MAX_SIZE", "1000"))

# RPC Configuration
RPC_ENDPOINTS = os.getenv("RPC_ENDPOINTS", "https://sepolia.infura.io/v3/YOUR_KEY").split(",")
RPC_TIMEOUT = int(os.getenv("RPC_TIMEOUT", "30"))  # 30 seconds
RPC_MAX_RETRIES = int(os.getenv("RPC_MAX_RETRIES", "3"))

# Network Configuration
NETWORK_CHAIN_ID = int(os.getenv("NETWORK_CHAIN_ID", "11155111"))  # Sepolia
NETWORK_NAME = os.getenv("NETWORK_NAME", "Sepolia")
NETWORK_EXPLORER_URL = os.getenv("NETWORK_EXPLORER_URL", "https://sepolia.etherscan.io")

# Portfolio Snapshot Configuration
SNAPSHOT_TIME_UTC = os.getenv("SNAPSHOT_TIME_UTC", "23:59")  # End of day
SNAPSHOT_RETENTION_DAYS = int(os.getenv("SNAPSHOT_RETENTION_DAYS", "365"))  # 1 year

# Notification Configuration
NOTIFICATION_MAX_QUEUE_SIZE = int(os.getenv("NOTIFICATION_MAX_QUEUE_SIZE", "100"))
NOTIFICATION_ADMIN_EMAIL = os.getenv("NOTIFICATION_ADMIN_EMAIL", "")

# Feature Flags
FEATURE_AI_TRADING_ENABLED = os.getenv("FEATURE_AI_TRADING_ENABLED", "true").lower() == "true"
FEATURE_RISK_MANAGEMENT_ENABLED = os.getenv("FEATURE_RISK_MANAGEMENT_ENABLED", "true").lower() == "true"
FEATURE_PORTFOLIO_SNAPSHOTS_ENABLED = os.getenv("FEATURE_PORTFOLIO_SNAPSHOTS_ENABLED", "true").lower() == "true"
FEATURE_WEBSOCKET_ENABLED = os.getenv("FEATURE_WEBSOCKET_ENABLED", "true").lower() == "true"

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")


def get_config_summary() -> dict:
    """Get a summary of all configuration values"""
    return {
        "demo_wallet": DEMO_WALLET_ADDRESS,
        "risk_management": {
            "position_size_limit": str(RISK_POSITION_SIZE_LIMIT),
            "drawdown_limit": str(RISK_DRAWDOWN_LIMIT),
            "daily_loss_limit": str(RISK_DAILY_LOSS_LIMIT),
            "min_gas_balance": str(RISK_MIN_GAS_BALANCE),
            "stop_loss_pct": str(RISK_STOP_LOSS_PCT),
            "take_profit_pct": str(RISK_TAKE_PROFIT_PCT),
        },
        "ai_trading": {
            "confidence_threshold": AI_CONFIDENCE_THRESHOLD,
            "signal_interval": AI_SIGNAL_GENERATION_INTERVAL,
            "max_concurrent_trades": AI_MAX_CONCURRENT_TRADES,
        },
        "performance": {
            "cache_ttl": WALLET_CACHE_TTL,
            "page_size": TRADE_HISTORY_PAGE_SIZE,
        },
        "network": {
            "chain_id": NETWORK_CHAIN_ID,
            "name": NETWORK_NAME,
            "explorer": NETWORK_EXPLORER_URL,
        },
        "features": {
            "ai_trading": FEATURE_AI_TRADING_ENABLED,
            "risk_management": FEATURE_RISK_MANAGEMENT_ENABLED,
            "portfolio_snapshots": FEATURE_PORTFOLIO_SNAPSHOTS_ENABLED,
            "websocket": FEATURE_WEBSOCKET_ENABLED,
        }
    }
