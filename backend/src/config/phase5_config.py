"""
Phase 5: Advanced Trading & AI Integration Configuration

This module contains all configuration settings for Phase 5 features including:
- Multi-chain support configuration
- DEX aggregator settings
- Price oracle configuration
- AI trading parameters
- WebSocket settings
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum
import os
from decimal import Decimal


class ChainId(Enum):
    """Supported blockchain network IDs"""
    ETHEREUM = 1
    POLYGON = 137
    ARBITRUM = 42161
    OPTIMISM = 10
    BSC = 56
    AVALANCHE = 43114
    BASE = 8453
    SOLANA = "solana"


@dataclass
class ChainConfig:
    """Configuration for a single blockchain network"""
    chain_id: int
    name: str
    symbol: str
    rpc_url: str
    explorer_url: str
    native_token: str
    wrapped_native: str
    supported_dexs: List[str]
    block_time: float  # seconds
    confirmation_blocks: int


@dataclass
class DEXConfig:
    """Configuration for a DEX protocol"""
    name: str
    router_address: Optional[str]
    factory_address: Optional[str]
    quoter_address: Optional[str]
    api_url: Optional[str]
    supported_chains: List[int]


@dataclass
class PriceSourceConfig:
    """Configuration for a price data source"""
    name: str
    priority: int
    api_url: str
    api_key_env: str
    rate_limit: int  # requests per minute
    supports_websocket: bool


# Chain configurations
CHAIN_CONFIGS: Dict[int, ChainConfig] = {
    ChainId.ETHEREUM.value: ChainConfig(
        chain_id=1,
        name="Ethereum",
        symbol="ETH",
        rpc_url=os.getenv("ETHEREUM_RPC", ""),
        explorer_url="https://etherscan.io",
        native_token="ETH",
        wrapped_native="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",  # WETH
        supported_dexs=["uniswap_v3", "uniswap_v2", "sushiswap", "curve", "balancer"],
        block_time=12.0,
        confirmation_blocks=2
    ),
    ChainId.POLYGON.value: ChainConfig(
        chain_id=137,
        name="Polygon",
        symbol="MATIC",
        rpc_url=os.getenv("POLYGON_RPC", ""),
        explorer_url="https://polygonscan.com",
        native_token="MATIC",
        wrapped_native="0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",  # WMATIC
        supported_dexs=["quickswap", "uniswap_v3", "sushiswap"],
        block_time=2.0,
        confirmation_blocks=5
    ),
    ChainId.ARBITRUM.value: ChainConfig(
        chain_id=42161,
        name="Arbitrum",
        symbol="ETH",
        rpc_url=os.getenv("ARBITRUM_RPC", ""),
        explorer_url="https://arbiscan.io",
        native_token="ETH",
        wrapped_native="0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",  # WETH
        supported_dexs=["uniswap_v3", "sushiswap", "camelot", "gmx"],
        block_time=0.25,
        confirmation_blocks=1
    ),
    ChainId.OPTIMISM.value: ChainConfig(
        chain_id=10,
        name="Optimism",
        symbol="ETH",
        rpc_url=os.getenv("OPTIMISM_RPC", ""),
        explorer_url="https://optimistic.etherscan.io",
        native_token="ETH",
        wrapped_native="0x4200000000000000000000000000000000000006",  # WETH
        supported_dexs=["velodrome", "uniswap_v3"],
        block_time=2.0,
        confirmation_blocks=1
    ),
    ChainId.BSC.value: ChainConfig(
        chain_id=56,
        name="BNB Chain",
        symbol="BNB",
        rpc_url=os.getenv("BSC_RPC", ""),
        explorer_url="https://bscscan.com",
        native_token="BNB",
        wrapped_native="0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",  # WBNB
        supported_dexs=["pancakeswap", "biswap"],
        block_time=3.0,
        confirmation_blocks=3
    ),
    ChainId.AVALANCHE.value: ChainConfig(
        chain_id=43114,
        name="Avalanche",
        symbol="AVAX",
        rpc_url=os.getenv("AVALANCHE_RPC", ""),
        explorer_url="https://snowtrace.io",
        native_token="AVAX",
        wrapped_native="0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7",  # WAVAX
        supported_dexs=["traderjoe", "pangolin"],
        block_time=2.0,
        confirmation_blocks=1
    ),
    ChainId.BASE.value: ChainConfig(
        chain_id=8453,
        name="Base",
        symbol="ETH",
        rpc_url=os.getenv("BASE_RPC", ""),
        explorer_url="https://basescan.org",
        native_token="ETH",
        wrapped_native="0x4200000000000000000000000000000000000006",  # WETH
        supported_dexs=["aerodrome", "uniswap_v3", "baseswap"],
        block_time=2.0,
        confirmation_blocks=1
    ),
}

# DEX configurations
DEX_CONFIGS: Dict[str, DEXConfig] = {
    "uniswap_v3": DEXConfig(
        name="Uniswap V3",
        router_address="0xE592427A0AEce92De3Edee1F18E0157C05861564",
        factory_address="0x1F98431c8aD98523631AE4a59f267346ea31F984",
        quoter_address="0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6",
        api_url=None,
        supported_chains=[1, 137, 42161, 10, 8453]
    ),
    "1inch": DEXConfig(
        name="1inch",
        router_address=None,
        factory_address=None,
        quoter_address=None,
        api_url=os.getenv("ONEINCH_BASE_URL", "https://api.1inch.dev/swap/v6.0"),
        supported_chains=[1, 137, 42161, 10, 56, 43114, 8453]
    ),
    "jupiter": DEXConfig(
        name="Jupiter",
        router_address=None,
        factory_address=None,
        quoter_address=None,
        api_url=os.getenv("JUPITER_BASE_URL", "https://quote-api.jup.ag/v6"),
        supported_chains=[]  # Solana only
    ),
    "lifi": DEXConfig(
        name="LI.FI",
        router_address=None,
        factory_address=None,
        quoter_address=None,
        api_url=os.getenv("LIFI_BASE_URL", "https://li.quest/v1"),
        supported_chains=[1, 137, 42161, 10, 56, 43114, 8453]
    ),
}

# Price source configurations
PRICE_SOURCES: List[PriceSourceConfig] = [
    PriceSourceConfig(
        name="binance",
        priority=1,
        api_url="https://api.binance.com/api/v3",
        api_key_env="BINANCE_API_KEY",
        rate_limit=1200,
        supports_websocket=True
    ),
    PriceSourceConfig(
        name="coingecko",
        priority=2,
        api_url="https://api.coingecko.com/api/v3",
        api_key_env="COINGECKO_API_KEY",
        rate_limit=50,
        supports_websocket=False
    ),
    PriceSourceConfig(
        name="chainlink",
        priority=3,
        api_url="",  # On-chain
        api_key_env="",
        rate_limit=0,
        supports_websocket=False
    ),
]


@dataclass
class TradingConfig:
    """Trading-related configuration"""
    default_slippage_tolerance: float = float(os.getenv("DEFAULT_SLIPPAGE_TOLERANCE", "0.5"))
    max_slippage_tolerance: float = float(os.getenv("MAX_SLIPPAGE_TOLERANCE", "5.0"))
    high_value_threshold: Decimal = Decimal(os.getenv("HIGH_VALUE_THRESHOLD", "10000"))
    daily_limit_default: Decimal = Decimal(os.getenv("DAILY_LIMIT_DEFAULT", "100000"))
    price_staleness_threshold: int = 30  # seconds
    gas_estimation_buffer: float = 1.2  # 20% buffer
    mev_protection_enabled: bool = True


@dataclass
class AIConfig:
    """AI trading configuration"""
    signal_confidence_threshold: float = float(os.getenv("SIGNAL_CONFIDENCE_THRESHOLD", "70"))
    concentration_risk_threshold: float = float(os.getenv("CONCENTRATION_RISK_THRESHOLD", "50"))
    min_signal_factors: int = 3
    signal_expiry_minutes: int = 60
    rebalance_threshold: float = 5.0  # % deviation to trigger rebalance


@dataclass
class WebSocketConfig:
    """WebSocket configuration"""
    heartbeat_interval: int = int(os.getenv("WS_HEARTBEAT_INTERVAL", "30"))
    max_connections: int = int(os.getenv("WS_MAX_CONNECTIONS", "1000"))
    price_update_interval: float = 1.0  # seconds
    reconnect_delay: int = 5  # seconds


@dataclass
class Phase5Config:
    """Main Phase 5 configuration container"""
    chains: Dict[int, ChainConfig] = field(default_factory=lambda: CHAIN_CONFIGS)
    dexs: Dict[str, DEXConfig] = field(default_factory=lambda: DEX_CONFIGS)
    price_sources: List[PriceSourceConfig] = field(default_factory=lambda: PRICE_SOURCES)
    trading: TradingConfig = field(default_factory=TradingConfig)
    ai: AIConfig = field(default_factory=AIConfig)
    websocket: WebSocketConfig = field(default_factory=WebSocketConfig)
    
    @property
    def supported_chain_ids(self) -> List[int]:
        """Get list of supported chain IDs"""
        return list(self.chains.keys())
    
    def get_chain_config(self, chain_id: int) -> Optional[ChainConfig]:
        """Get configuration for a specific chain"""
        return self.chains.get(chain_id)
    
    def get_explorer_url(self, chain_id: int, tx_hash: str) -> str:
        """Generate explorer URL for a transaction"""
        chain = self.chains.get(chain_id)
        if chain:
            return f"{chain.explorer_url}/tx/{tx_hash}"
        return ""


# Global configuration instance
phase5_config = Phase5Config()


# Technical indicator parameters
INDICATOR_PARAMS = {
    "MA": {"periods": [20, 50, 200]},
    "EMA": {"periods": [12, 26, 50]},
    "RSI": {"period": 14, "overbought": 70, "oversold": 30},
    "MACD": {"fast": 12, "slow": 26, "signal": 9},
    "BB": {"period": 20, "std_dev": 2},
    "VOLUME": {"ma_period": 20}
}

# Supported timeframes for charts
CHART_TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h", "1d", "1w"]

# Token lists per chain (common tokens)
COMMON_TOKENS = {
    1: {  # Ethereum
        "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "DAI": "0x6B175474E89094C44Da98b954EescdeCB5BE3830",
        "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
        "LINK": "0x514910771AF9Ca656af840dff83E8264EcF986CA",
    },
    137: {  # Polygon
        "WMATIC": "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
        "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
        "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
        "WETH": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
    },
    42161: {  # Arbitrum
        "WETH": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
        "USDC": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
        "USDT": "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",
        "ARB": "0x912CE59144191C1204E64559FE8253a0e49E6548",
    },
    56: {  # BSC
        "WBNB": "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",
        "USDT": "0x55d398326f99059fF775485246999027B3197955",
        "BUSD": "0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56",
    },
}
