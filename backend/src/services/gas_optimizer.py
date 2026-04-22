"""
Phase 5: Gas Optimization Service

Provides:
- Gas estimation for all chains
- Gas price monitoring
- Cost-effective routing
- Gas limit suggestions
"""

import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from decimal import Decimal
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class GasSpeed(str, Enum):
    SLOW = "slow"
    STANDARD = "standard"
    FAST = "fast"
    INSTANT = "instant"


@dataclass
class GasEstimate:
    chain_id: int
    gas_limit: int
    gas_price_gwei: Decimal
    max_fee_gwei: Decimal
    priority_fee_gwei: Decimal
    estimated_cost_native: Decimal
    estimated_cost_usd: Decimal
    speed: GasSpeed
    estimated_time_seconds: int


@dataclass
class ChainGasInfo:
    chain_id: int
    chain_name: str
    native_token: str
    native_price_usd: Decimal
    base_fee_gwei: Decimal
    slow_gwei: Decimal
    standard_gwei: Decimal
    fast_gwei: Decimal
    instant_gwei: Decimal
    is_congested: bool
    congestion_level: float  # 0-1
    last_updated: datetime


# Chain configurations
CHAIN_CONFIG = {
    1: {"name": "Ethereum", "native": "ETH", "avg_block_time": 12},
    137: {"name": "Polygon", "native": "MATIC", "avg_block_time": 2},
    42161: {"name": "Arbitrum", "native": "ETH", "avg_block_time": 0.25},
    10: {"name": "Optimism", "native": "ETH", "avg_block_time": 2},
    56: {"name": "BNB Chain", "native": "BNB", "avg_block_time": 3},
    43114: {"name": "Avalanche", "native": "AVAX", "avg_block_time": 2},
    8453: {"name": "Base", "native": "ETH", "avg_block_time": 2},
}

# Gas limits for common operations
GAS_LIMITS = {
    "transfer": 21000,
    "erc20_transfer": 65000,
    "swap_simple": 150000,
    "swap_complex": 300000,
    "bridge": 250000,
    "approve": 46000,
}


class GasOptimizer:
    def __init__(self):
        self.gas_cache: Dict[int, ChainGasInfo] = {}
        self.native_prices: Dict[str, Decimal] = {}
        self.cache_ttl = 30  # seconds
    
    async def _fetch_native_prices(self) -> Dict[str, Decimal]:
        """Fetch native token prices from Binance."""
        try:
            async with aiohttp.ClientSession() as session:
                symbols = ["ETHUSDT", "MATICUSDT", "BNBUSDT", "AVAXUSDT"]
                url = f"https://api.binance.com/api/v3/ticker/price"
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        prices = {}
                        for item in data:
                            if item["symbol"] in symbols:
                                token = item["symbol"].replace("USDT", "")
                                prices[token] = Decimal(item["price"])
                        return prices
        except Exception as e:
            logger.error(f"Failed to fetch native prices: {e}")
        
        # Fallback prices
        return {
            "ETH": Decimal("2650"),
            "MATIC": Decimal("0.85"),
            "BNB": Decimal("580"),
            "AVAX": Decimal("35")
        }
    
    async def _fetch_gas_prices(self, chain_id: int) -> Optional[ChainGasInfo]:
        """Fetch current gas prices for a chain."""
        config = CHAIN_CONFIG.get(chain_id)
        if not config:
            return None
        
        # Simulated gas prices (in production, use chain RPC or gas APIs)
        base_fees = {
            1: Decimal("25"),      # Ethereum
            137: Decimal("50"),    # Polygon
            42161: Decimal("0.1"), # Arbitrum
            10: Decimal("0.001"),  # Optimism
            56: Decimal("3"),      # BNB
            43114: Decimal("25"),  # Avalanche
            8453: Decimal("0.01"), # Base
        }
        
        base_fee = base_fees.get(chain_id, Decimal("20"))
        
        # Calculate speed tiers
        slow = base_fee * Decimal("0.8")
        standard = base_fee
        fast = base_fee * Decimal("1.2")
        instant = base_fee * Decimal("1.5")
        
        # Determine congestion
        congestion = min(float(base_fee) / 100, 1.0) if chain_id == 1 else 0.3
        
        native_token = config["native"]
        native_price = self.native_prices.get(native_token, Decimal("2650"))
        
        return ChainGasInfo(
            chain_id=chain_id,
            chain_name=config["name"],
            native_token=native_token,
            native_price_usd=native_price,
            base_fee_gwei=base_fee,
            slow_gwei=slow,
            standard_gwei=standard,
            fast_gwei=fast,
            instant_gwei=instant,
            is_congested=congestion > 0.7,
            congestion_level=congestion,
            last_updated=datetime.utcnow()
        )
    
    async def get_gas_info(self, chain_id: int) -> Optional[ChainGasInfo]:
        """Get current gas info for a chain."""
        cached = self.gas_cache.get(chain_id)
        if cached and (datetime.utcnow() - cached.last_updated).seconds < self.cache_ttl:
            return cached
        
        # Refresh native prices
        self.native_prices = await self._fetch_native_prices()
        
        gas_info = await self._fetch_gas_prices(chain_id)
        if gas_info:
            self.gas_cache[chain_id] = gas_info
        
        return gas_info
    
    async def estimate_gas(
        self,
        chain_id: int,
        operation: str = "swap_simple",
        speed: GasSpeed = GasSpeed.STANDARD,
        custom_gas_limit: Optional[int] = None
    ) -> Optional[GasEstimate]:
        """Estimate gas cost for an operation."""
        gas_info = await self.get_gas_info(chain_id)
        if not gas_info:
            return None
        
        gas_limit = custom_gas_limit or GAS_LIMITS.get(operation, 150000)
        
        # Get gas price for speed
        gas_prices = {
            GasSpeed.SLOW: gas_info.slow_gwei,
            GasSpeed.STANDARD: gas_info.standard_gwei,
            GasSpeed.FAST: gas_info.fast_gwei,
            GasSpeed.INSTANT: gas_info.instant_gwei,
        }
        gas_price = gas_prices[speed]
        
        # Calculate costs
        cost_native = (Decimal(gas_limit) * gas_price) / Decimal("1e9")
        cost_usd = cost_native * gas_info.native_price_usd
        
        # Estimate time
        config = CHAIN_CONFIG.get(chain_id, {"avg_block_time": 12})
        blocks_to_confirm = {
            GasSpeed.SLOW: 10,
            GasSpeed.STANDARD: 3,
            GasSpeed.FAST: 1,
            GasSpeed.INSTANT: 1,
        }
        est_time = int(blocks_to_confirm[speed] * config["avg_block_time"])
        
        return GasEstimate(
            chain_id=chain_id,
            gas_limit=gas_limit,
            gas_price_gwei=gas_price,
            max_fee_gwei=gas_price * Decimal("1.2"),
            priority_fee_gwei=gas_price * Decimal("0.1"),
            estimated_cost_native=cost_native,
            estimated_cost_usd=cost_usd,
            speed=speed,
            estimated_time_seconds=est_time
        )
    
    async def find_optimal_route(
        self,
        routes: List[Dict[str, Any]],
        max_gas_usd: Optional[Decimal] = None
    ) -> Optional[Dict[str, Any]]:
        """Find the most cost-effective route considering gas costs."""
        if not routes:
            return None
        
        scored_routes = []
        for route in routes:
            chain_id = route.get("chain_id", 1)
            gas_estimate = await self.estimate_gas(chain_id, "swap_complex")
            
            if not gas_estimate:
                continue
            
            if max_gas_usd and gas_estimate.estimated_cost_usd > max_gas_usd:
                continue
            
            output_value = Decimal(str(route.get("output_amount_usd", 0)))
            gas_cost = gas_estimate.estimated_cost_usd
            net_value = output_value - gas_cost
            
            scored_routes.append({
                "route": route,
                "gas_estimate": gas_estimate,
                "net_value_usd": net_value,
                "gas_cost_usd": gas_cost
            })
        
        if not scored_routes:
            return None
        
        # Sort by net value (highest first)
        scored_routes.sort(key=lambda x: x["net_value_usd"], reverse=True)
        return scored_routes[0]
    
    async def should_wait_for_lower_gas(
        self,
        chain_id: int,
        threshold_gwei: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """Check if user should wait for lower gas prices."""
        gas_info = await self.get_gas_info(chain_id)
        if not gas_info:
            return {"should_wait": False, "reason": "Unable to fetch gas info"}
        
        # Default thresholds by chain
        default_thresholds = {
            1: Decimal("30"),   # Ethereum
            137: Decimal("100"), # Polygon
            56: Decimal("5"),   # BNB
        }
        
        threshold = threshold_gwei or default_thresholds.get(chain_id, Decimal("50"))
        
        should_wait = gas_info.base_fee_gwei > threshold
        
        return {
            "should_wait": should_wait,
            "current_gas_gwei": float(gas_info.base_fee_gwei),
            "threshold_gwei": float(threshold),
            "is_congested": gas_info.is_congested,
            "congestion_level": gas_info.congestion_level,
            "suggestion": "Consider waiting for lower gas prices" if should_wait else "Gas prices are reasonable",
            "estimated_savings_percent": max(0, float((gas_info.base_fee_gwei - threshold) / gas_info.base_fee_gwei * 100)) if should_wait else 0
        }
    
    async def get_all_chains_gas(self) -> List[ChainGasInfo]:
        """Get gas info for all supported chains."""
        results = []
        for chain_id in CHAIN_CONFIG.keys():
            gas_info = await self.get_gas_info(chain_id)
            if gas_info:
                results.append(gas_info)
        return results


# Singleton instance
gas_optimizer = GasOptimizer()
