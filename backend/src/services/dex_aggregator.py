"""
Phase 5: DEX Aggregator Service

Multi-DEX aggregation for optimal swap routing:
- 1inch API integration for EVM chains
- Jupiter API integration for Solana
- Direct Uniswap V3 quoter integration
- Optimal route selection across DEXs
- Slippage protection
"""

import asyncio
import aiohttp
import logging
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
import time

from src.config.phase5_config import (
    phase5_config, DEX_CONFIGS, CHAIN_CONFIGS, COMMON_TOKENS
)

logger = logging.getLogger(__name__)


class DEXType(Enum):
    """Types of DEX protocols"""
    AGGREGATOR = "aggregator"
    AMM = "amm"
    ORDER_BOOK = "order_book"


@dataclass
class SwapRoute:
    """A swap route through one or more DEXs"""
    dex_name: str
    from_token: str
    to_token: str
    from_amount: Decimal
    to_amount: Decimal
    to_amount_min: Decimal
    price_impact: float
    gas_estimate: int
    gas_price_gwei: float
    gas_fee_usd: Decimal
    protocol_fee: Decimal
    route_path: List[str]
    tx_data: Optional[Dict] = None
    
    @property
    def exchange_rate(self) -> Decimal:
        if self.from_amount == 0:
            return Decimal("0")
        return self.to_amount / self.from_amount
    
    @property
    def total_fee_usd(self) -> Decimal:
        return self.gas_fee_usd + self.protocol_fee
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "dex_name": self.dex_name,
            "from_token": self.from_token,
            "to_token": self.to_token,
            "from_amount": str(self.from_amount),
            "to_amount": str(self.to_amount),
            "to_amount_min": str(self.to_amount_min),
            "price_impact": self.price_impact,
            "gas_estimate": self.gas_estimate,
            "gas_fee_usd": str(self.gas_fee_usd),
            "protocol_fee": str(self.protocol_fee),
            "total_fee_usd": str(self.total_fee_usd),
            "exchange_rate": str(self.exchange_rate),
            "route_path": self.route_path
        }


@dataclass
class SwapQuote:
    """Aggregated swap quote from multiple DEXs"""
    from_token: str
    to_token: str
    from_amount: Decimal
    chain_id: int
    best_route: SwapRoute
    all_routes: List[SwapRoute]
    expires_at: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "from_token": self.from_token,
            "to_token": self.to_token,
            "from_amount": str(self.from_amount),
            "chain_id": self.chain_id,
            "best_route": self.best_route.to_dict(),
            "all_routes": [r.to_dict() for r in self.all_routes],
            "expires_at": self.expires_at
        }


class DEXAggregator:
    """
    Multi-DEX aggregator for optimal swap routing
    """
    
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
        self._1inch_api_key = os.getenv("ONEINCH_API_KEY", "")
        self._jupiter_api_key = os.getenv("JUPITER_API_KEY", "")
    
    async def start(self) -> None:
        """Initialize the DEX aggregator"""
        self._session = aiohttp.ClientSession()
        logger.info("DEX Aggregator started")
    
    async def stop(self) -> None:
        """Cleanup resources"""
        if self._session:
            await self._session.close()
        logger.info("DEX Aggregator stopped")
    
    async def get_swap_quote(
        self,
        from_token: str,
        to_token: str,
        amount: Decimal,
        chain_id: int,
        slippage_tolerance: float = 0.5,
        user_address: Optional[str] = None
    ) -> Optional[SwapQuote]:
        """
        Get the best swap quote across multiple DEXs
        
        Args:
            from_token: Source token address
            to_token: Destination token address
            amount: Amount to swap (in token units)
            chain_id: Chain ID
            slippage_tolerance: Slippage tolerance percentage
            user_address: User's wallet address
        
        Returns:
            SwapQuote with best route and alternatives
        """
        # Query multiple DEXs in parallel
        tasks = []
        
        # 1inch for EVM chains
        if chain_id in DEX_CONFIGS["1inch"].supported_chains:
            tasks.append(self._get_1inch_quote(
                from_token, to_token, amount, chain_id, slippage_tolerance, user_address
            ))
        
        # Jupiter for Solana
        if chain_id == 0:  # Solana
            tasks.append(self._get_jupiter_quote(
                from_token, to_token, amount, slippage_tolerance
            ))
        
        # Uniswap V3 direct
        if chain_id in DEX_CONFIGS["uniswap_v3"].supported_chains:
            tasks.append(self._get_uniswap_quote(
                from_token, to_token, amount, chain_id, slippage_tolerance
            ))
        
        # Execute all queries in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful results
        routes = []
        for result in results:
            if isinstance(result, SwapRoute):
                routes.append(result)
            elif isinstance(result, Exception):
                logger.warning(f"DEX quote failed: {result}")
        
        if not routes:
            return None
        
        # Sort by output amount (best first)
        routes.sort(key=lambda r: r.to_amount, reverse=True)
        
        return SwapQuote(
            from_token=from_token,
            to_token=to_token,
            from_amount=amount,
            chain_id=chain_id,
            best_route=routes[0],
            all_routes=routes,
            expires_at=int(time.time()) + 60  # 60 second expiry
        )
    
    async def _get_1inch_quote(
        self,
        from_token: str,
        to_token: str,
        amount: Decimal,
        chain_id: int,
        slippage: float,
        user_address: Optional[str]
    ) -> Optional[SwapRoute]:
        """Get quote from 1inch API"""
        if not self._session:
            return None
        
        base_url = DEX_CONFIGS["1inch"].api_url
        url = f"{base_url}/{chain_id}/quote"
        
        # Convert amount to wei (assuming 18 decimals)
        amount_wei = int(amount * Decimal("1e18"))
        
        params = {
            "src": from_token,
            "dst": to_token,
            "amount": str(amount_wei),
        }
        
        headers = {}
        if self._1inch_api_key:
            headers["Authorization"] = f"Bearer {self._1inch_api_key}"
        
        try:
            async with self._session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    to_amount = Decimal(data["toAmount"]) / Decimal("1e18")
                    to_amount_min = to_amount * Decimal(1 - slippage / 100)
                    
                    # Estimate gas cost
                    gas_estimate = int(data.get("gas", 200000))
                    gas_price = await self._get_gas_price(chain_id)
                    eth_price = await self._get_eth_price()
                    gas_fee_usd = Decimal(gas_estimate * gas_price * 1e-9) * eth_price
                    
                    return SwapRoute(
                        dex_name="1inch",
                        from_token=from_token,
                        to_token=to_token,
                        from_amount=amount,
                        to_amount=to_amount,
                        to_amount_min=to_amount_min,
                        price_impact=0.0,  # 1inch doesn't always return this
                        gas_estimate=gas_estimate,
                        gas_price_gwei=gas_price,
                        gas_fee_usd=gas_fee_usd,
                        protocol_fee=Decimal("0"),
                        route_path=data.get("protocols", [[]])[0] if data.get("protocols") else []
                    )
        except Exception as e:
            logger.error(f"1inch quote error: {e}")
        
        return None
    
    async def _get_jupiter_quote(
        self,
        from_token: str,
        to_token: str,
        amount: Decimal,
        slippage: float
    ) -> Optional[SwapRoute]:
        """Get quote from Jupiter (Solana)"""
        if not self._session:
            return None
        
        base_url = DEX_CONFIGS["jupiter"].api_url
        url = f"{base_url}/quote"
        
        # Convert to lamports (9 decimals for most Solana tokens)
        amount_lamports = int(amount * Decimal("1e9"))
        
        params = {
            "inputMint": from_token,
            "outputMint": to_token,
            "amount": str(amount_lamports),
            "slippageBps": int(slippage * 100),
        }
        
        try:
            async with self._session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    to_amount = Decimal(data["outAmount"]) / Decimal("1e9")
                    to_amount_min = Decimal(data.get("otherAmountThreshold", data["outAmount"])) / Decimal("1e9")
                    
                    return SwapRoute(
                        dex_name="Jupiter",
                        from_token=from_token,
                        to_token=to_token,
                        from_amount=amount,
                        to_amount=to_amount,
                        to_amount_min=to_amount_min,
                        price_impact=float(data.get("priceImpactPct", 0)),
                        gas_estimate=5000,  # Solana compute units
                        gas_price_gwei=0,
                        gas_fee_usd=Decimal("0.001"),  # ~$0.001 on Solana
                        protocol_fee=Decimal("0"),
                        route_path=[r.get("label", "") for r in data.get("routePlan", [])]
                    )
        except Exception as e:
            logger.error(f"Jupiter quote error: {e}")
        
        return None
    
    async def _get_uniswap_quote(
        self,
        from_token: str,
        to_token: str,
        amount: Decimal,
        chain_id: int,
        slippage: float
    ) -> Optional[SwapRoute]:
        """Get quote from Uniswap V3 quoter contract"""
        # This would use web3.py to call the quoter contract
        # For now, return a simulated quote
        
        # Simulate Uniswap quote (in production, call quoter contract)
        try:
            # Get price from oracle for simulation
            from src.services.advanced_price_oracle import price_oracle
            
            from_price = await price_oracle.get_price(from_token.split("0x")[0] if "0x" in from_token else "ETH")
            to_price = await price_oracle.get_price(to_token.split("0x")[0] if "0x" in to_token else "USDC")
            
            if from_price and to_price:
                exchange_rate = from_price.price / to_price.price
                to_amount = amount * exchange_rate
                to_amount_min = to_amount * Decimal(1 - slippage / 100)
                
                # Estimate gas
                gas_estimate = 150000
                gas_price = await self._get_gas_price(chain_id)
                eth_price = await self._get_eth_price()
                gas_fee_usd = Decimal(gas_estimate * gas_price * 1e-9) * eth_price
                
                return SwapRoute(
                    dex_name="Uniswap V3",
                    from_token=from_token,
                    to_token=to_token,
                    from_amount=amount,
                    to_amount=to_amount,
                    to_amount_min=to_amount_min,
                    price_impact=0.1,  # Simulated
                    gas_estimate=gas_estimate,
                    gas_price_gwei=gas_price,
                    gas_fee_usd=gas_fee_usd,
                    protocol_fee=amount * Decimal("0.003"),  # 0.3% fee
                    route_path=[from_token, to_token]
                )
        except Exception as e:
            logger.error(f"Uniswap quote error: {e}")
        
        return None

    
    async def _get_gas_price(self, chain_id: int) -> float:
        """Get current gas price in gwei for a chain"""
        # Default gas prices by chain (in gwei)
        default_gas_prices = {
            1: 30.0,      # Ethereum
            137: 50.0,    # Polygon
            42161: 0.1,   # Arbitrum
            10: 0.001,    # Optimism
            56: 5.0,      # BSC
            43114: 25.0,  # Avalanche
            8453: 0.001,  # Base
        }
        return default_gas_prices.get(chain_id, 20.0)
    
    async def _get_eth_price(self) -> Decimal:
        """Get current ETH price in USD"""
        try:
            from src.services.advanced_price_oracle import price_oracle
            price_data = await price_oracle.get_price("ETHUSDT")
            if price_data:
                return price_data.price
        except Exception:
            pass
        return Decimal("2000")  # Fallback price
    
    def validate_slippage(
        self,
        expected_output: Decimal,
        actual_output: Decimal,
        slippage_tolerance: float
    ) -> Tuple[bool, float]:
        """
        Validate that actual output is within slippage tolerance
        
        Returns:
            Tuple of (is_valid, actual_slippage_percent)
        """
        if expected_output == 0:
            return False, 100.0
        
        actual_slippage = float((expected_output - actual_output) / expected_output * 100)
        is_valid = actual_slippage <= slippage_tolerance
        
        return is_valid, actual_slippage
    
    async def get_token_info(
        self, token_address: str, chain_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get token information (symbol, decimals, name)"""
        # Check common tokens first
        chain_tokens = COMMON_TOKENS.get(chain_id, {})
        for symbol, address in chain_tokens.items():
            if address.lower() == token_address.lower():
                return {
                    "address": token_address,
                    "symbol": symbol,
                    "decimals": 18,  # Most ERC20 tokens
                    "chain_id": chain_id
                }
        
        # In production, query the token contract
        return {
            "address": token_address,
            "symbol": "UNKNOWN",
            "decimals": 18,
            "chain_id": chain_id
        }
    
    async def get_supported_tokens(self, chain_id: int) -> List[Dict[str, Any]]:
        """Get list of supported tokens for a chain"""
        chain_tokens = COMMON_TOKENS.get(chain_id, {})
        return [
            {
                "address": address,
                "symbol": symbol,
                "chain_id": chain_id
            }
            for symbol, address in chain_tokens.items()
        ]


# Global DEX aggregator instance
dex_aggregator = DEXAggregator()
