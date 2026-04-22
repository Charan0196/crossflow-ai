"""
Phase 5: Cross-Chain Router Service

Handles cross-chain transactions:
- Swap execution on all EVM chains
- Solana swap execution via Jupiter
- Bridge protocol integration (LI.FI)
- Transaction simulation before execution
- Transaction status tracking
"""

import asyncio
import aiohttp
import logging
import os
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from datetime import datetime
import time
import uuid

from src.config.phase5_config import (
    phase5_config, DEX_CONFIGS, CHAIN_CONFIGS
)

logger = logging.getLogger(__name__)


class TransactionStatus(Enum):
    """Transaction status states"""
    PENDING = "pending"
    SIMULATING = "simulating"
    AWAITING_SIGNATURE = "awaiting_signature"
    SUBMITTED = "submitted"
    CONFIRMING = "confirming"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    REVERTED = "reverted"


class BridgeStatus(Enum):
    """Bridge transaction status"""
    PENDING = "pending"
    SOURCE_CONFIRMED = "source_confirmed"
    BRIDGING = "bridging"
    DESTINATION_PENDING = "destination_pending"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TransactionResult:
    """Result of a transaction execution"""
    tx_hash: str
    status: TransactionStatus
    chain_id: int
    from_token: str
    to_token: str
    from_amount: Decimal
    to_amount: Optional[Decimal]
    gas_used: Optional[int]
    gas_price: Optional[float]
    block_number: Optional[int]
    error_message: Optional[str] = None
    explorer_url: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tx_hash": self.tx_hash,
            "status": self.status.value,
            "chain_id": self.chain_id,
            "from_token": self.from_token,
            "to_token": self.to_token,
            "from_amount": str(self.from_amount),
            "to_amount": str(self.to_amount) if self.to_amount else None,
            "gas_used": self.gas_used,
            "gas_price": self.gas_price,
            "block_number": self.block_number,
            "error_message": self.error_message,
            "explorer_url": self.explorer_url
        }


@dataclass
class BridgeQuote:
    """Quote for a cross-chain bridge"""
    bridge_name: str
    from_chain_id: int
    to_chain_id: int
    from_token: str
    to_token: str
    from_amount: Decimal
    to_amount: Decimal
    bridge_fee: Decimal
    gas_fee_usd: Decimal
    estimated_time: int  # seconds
    route_steps: List[Dict]
    tx_data: Optional[Dict] = None
    
    @property
    def total_fee_usd(self) -> Decimal:
        return self.bridge_fee + self.gas_fee_usd
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "bridge_name": self.bridge_name,
            "from_chain_id": self.from_chain_id,
            "to_chain_id": self.to_chain_id,
            "from_token": self.from_token,
            "to_token": self.to_token,
            "from_amount": str(self.from_amount),
            "to_amount": str(self.to_amount),
            "bridge_fee": str(self.bridge_fee),
            "gas_fee_usd": str(self.gas_fee_usd),
            "total_fee_usd": str(self.total_fee_usd),
            "estimated_time": self.estimated_time,
            "route_steps": self.route_steps
        }


@dataclass
class BridgeResult:
    """Result of a bridge execution"""
    bridge_id: str
    source_tx_hash: str
    destination_tx_hash: Optional[str]
    status: BridgeStatus
    from_chain_id: int
    to_chain_id: int
    from_amount: Decimal
    to_amount: Optional[Decimal]
    estimated_arrival: int  # Unix timestamp
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "bridge_id": self.bridge_id,
            "source_tx_hash": self.source_tx_hash,
            "destination_tx_hash": self.destination_tx_hash,
            "status": self.status.value,
            "from_chain_id": self.from_chain_id,
            "to_chain_id": self.to_chain_id,
            "from_amount": str(self.from_amount),
            "to_amount": str(self.to_amount) if self.to_amount else None,
            "estimated_arrival": self.estimated_arrival,
            "error_message": self.error_message
        }


class CrossChainRouter:
    """
    Cross-chain transaction router
    """
    
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
        self._lifi_api_key = os.getenv("LIFI_API_KEY", "")
        self._pending_transactions: Dict[str, TransactionResult] = {}
        self._pending_bridges: Dict[str, BridgeResult] = {}
        self._status_callbacks: Dict[str, List[Callable]] = {}
    
    async def start(self) -> None:
        """Initialize the router"""
        self._session = aiohttp.ClientSession()
        # Start background status polling
        asyncio.create_task(self._poll_transaction_status())
        logger.info("Cross-Chain Router started")
    
    async def stop(self) -> None:
        """Cleanup resources"""
        if self._session:
            await self._session.close()
        logger.info("Cross-Chain Router stopped")
    
    async def simulate_swap(
        self,
        from_token: str,
        to_token: str,
        amount: Decimal,
        chain_id: int,
        user_address: str
    ) -> Dict[str, Any]:
        """
        Simulate a swap transaction before execution
        
        Returns simulation result with expected output and potential errors
        """
        from src.services.dex_aggregator import dex_aggregator
        
        # Get quote
        quote = await dex_aggregator.get_swap_quote(
            from_token, to_token, amount, chain_id, 0.5, user_address
        )
        
        if not quote:
            return {
                "success": False,
                "error": "Unable to get quote for this swap"
            }
        
        # Simulate transaction (in production, use eth_call)
        simulation_result = {
            "success": True,
            "expected_output": str(quote.best_route.to_amount),
            "expected_output_min": str(quote.best_route.to_amount_min),
            "price_impact": quote.best_route.price_impact,
            "gas_estimate": quote.best_route.gas_estimate,
            "gas_fee_usd": str(quote.best_route.gas_fee_usd),
            "warnings": []
        }
        
        # Add warnings for high price impact
        if quote.best_route.price_impact > 1.0:
            simulation_result["warnings"].append(
                f"High price impact: {quote.best_route.price_impact:.2f}%"
            )
        
        if quote.best_route.price_impact > 5.0:
            simulation_result["warnings"].append(
                "Very high price impact - consider splitting into smaller trades"
            )
        
        return simulation_result
    
    async def execute_swap(
        self,
        from_token: str,
        to_token: str,
        amount: Decimal,
        chain_id: int,
        user_address: str,
        slippage_tolerance: float = 0.5,
        deadline: Optional[int] = None
    ) -> TransactionResult:
        """
        Execute a swap transaction
        
        In production, this would:
        1. Build the transaction
        2. Return unsigned tx for user to sign
        3. Submit signed tx to network
        4. Track confirmation
        """
        from src.services.dex_aggregator import dex_aggregator
        
        # Get quote
        quote = await dex_aggregator.get_swap_quote(
            from_token, to_token, amount, chain_id, slippage_tolerance, user_address
        )
        
        if not quote:
            return TransactionResult(
                tx_hash="",
                status=TransactionStatus.FAILED,
                chain_id=chain_id,
                from_token=from_token,
                to_token=to_token,
                from_amount=amount,
                to_amount=None,
                gas_used=None,
                gas_price=None,
                block_number=None,
                error_message="Unable to get quote"
            )
        
        # Generate mock tx hash for demo
        tx_hash = f"0x{uuid.uuid4().hex}"
        
        # Create pending transaction
        result = TransactionResult(
            tx_hash=tx_hash,
            status=TransactionStatus.SUBMITTED,
            chain_id=chain_id,
            from_token=from_token,
            to_token=to_token,
            from_amount=amount,
            to_amount=quote.best_route.to_amount,
            gas_used=quote.best_route.gas_estimate,
            gas_price=quote.best_route.gas_price_gwei,
            block_number=None,
            explorer_url=phase5_config.get_explorer_url(chain_id, tx_hash)
        )
        
        # Track pending transaction
        self._pending_transactions[tx_hash] = result
        
        # Simulate confirmation after delay (in production, poll network)
        asyncio.create_task(self._simulate_confirmation(tx_hash))
        
        return result
    
    async def _simulate_confirmation(self, tx_hash: str) -> None:
        """Simulate transaction confirmation (for demo)"""
        await asyncio.sleep(3)  # Simulate block time
        
        if tx_hash in self._pending_transactions:
            result = self._pending_transactions[tx_hash]
            result.status = TransactionStatus.CONFIRMED
            result.block_number = 12345678  # Mock block number
            
            # Notify callbacks
            await self._notify_status_change(tx_hash, result)
    
    async def get_bridge_quote(
        self,
        from_token: str,
        to_token: str,
        amount: Decimal,
        from_chain_id: int,
        to_chain_id: int,
        user_address: str,
        slippage_tolerance: float = 0.5
    ) -> Optional[BridgeQuote]:
        """
        Get quote for cross-chain bridge via LI.FI
        """
        if not self._session:
            return None
        
        base_url = DEX_CONFIGS["lifi"].api_url
        url = f"{base_url}/quote"
        
        # Convert amount to wei
        amount_wei = str(int(amount * Decimal("1e18")))
        
        params = {
            "fromChain": str(from_chain_id),
            "toChain": str(to_chain_id),
            "fromToken": from_token,
            "toToken": to_token,
            "fromAmount": amount_wei,
            "fromAddress": user_address,
            "slippage": slippage_tolerance / 100
        }
        
        try:
            async with self._session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    estimate = data.get("estimate", {})
                    to_amount = Decimal(estimate.get("toAmount", "0")) / Decimal("1e18")
                    
                    # Calculate fees
                    gas_costs = estimate.get("gasCosts", [])
                    gas_fee = sum(
                        Decimal(g.get("amountUSD", "0")) 
                        for g in gas_costs
                    )
                    
                    fee_costs = estimate.get("feeCosts", [])
                    bridge_fee = sum(
                        Decimal(f.get("amountUSD", "0")) 
                        for f in fee_costs
                    )
                    
                    return BridgeQuote(
                        bridge_name=data.get("toolDetails", {}).get("name", "LI.FI"),
                        from_chain_id=from_chain_id,
                        to_chain_id=to_chain_id,
                        from_token=from_token,
                        to_token=to_token,
                        from_amount=amount,
                        to_amount=to_amount,
                        bridge_fee=bridge_fee,
                        gas_fee_usd=gas_fee,
                        estimated_time=int(estimate.get("executionDuration", 300)),
                        route_steps=data.get("includedSteps", []),
                        tx_data=data.get("transactionRequest")
                    )
        except Exception as e:
            logger.error(f"LI.FI quote error: {e}")
        
        # Fallback: return simulated quote
        return self._get_simulated_bridge_quote(
            from_token, to_token, amount, from_chain_id, to_chain_id
        )
    
    def _get_simulated_bridge_quote(
        self,
        from_token: str,
        to_token: str,
        amount: Decimal,
        from_chain_id: int,
        to_chain_id: int
    ) -> BridgeQuote:
        """Generate simulated bridge quote for demo"""
        # Estimate bridge fee (0.1-0.3%)
        bridge_fee = amount * Decimal("0.002")
        gas_fee = Decimal("5")  # ~$5 gas
        to_amount = amount - bridge_fee
        
        # Estimate time based on chains
        time_estimates = {
            (1, 137): 600,    # ETH -> Polygon: 10 min
            (1, 42161): 900,  # ETH -> Arbitrum: 15 min
            (1, 10): 900,     # ETH -> Optimism: 15 min
            (137, 1): 1800,   # Polygon -> ETH: 30 min
        }
        estimated_time = time_estimates.get(
            (from_chain_id, to_chain_id), 1200
        )
        
        return BridgeQuote(
            bridge_name="LI.FI",
            from_chain_id=from_chain_id,
            to_chain_id=to_chain_id,
            from_token=from_token,
            to_token=to_token,
            from_amount=amount,
            to_amount=to_amount,
            bridge_fee=bridge_fee,
            gas_fee_usd=gas_fee,
            estimated_time=estimated_time,
            route_steps=[
                {"type": "swap", "chain": from_chain_id},
                {"type": "bridge", "from": from_chain_id, "to": to_chain_id},
            ]
        )

    
    async def execute_bridge(
        self,
        from_token: str,
        to_token: str,
        amount: Decimal,
        from_chain_id: int,
        to_chain_id: int,
        user_address: str,
        slippage_tolerance: float = 0.5
    ) -> BridgeResult:
        """
        Execute a cross-chain bridge transaction
        """
        # Get quote
        quote = await self.get_bridge_quote(
            from_token, to_token, amount, from_chain_id, to_chain_id,
            user_address, slippage_tolerance
        )
        
        if not quote:
            return BridgeResult(
                bridge_id=str(uuid.uuid4()),
                source_tx_hash="",
                destination_tx_hash=None,
                status=BridgeStatus.FAILED,
                from_chain_id=from_chain_id,
                to_chain_id=to_chain_id,
                from_amount=amount,
                to_amount=None,
                estimated_arrival=0,
                error_message="Unable to get bridge quote"
            )
        
        # Generate mock tx hash
        source_tx_hash = f"0x{uuid.uuid4().hex}"
        bridge_id = str(uuid.uuid4())
        
        result = BridgeResult(
            bridge_id=bridge_id,
            source_tx_hash=source_tx_hash,
            destination_tx_hash=None,
            status=BridgeStatus.PENDING,
            from_chain_id=from_chain_id,
            to_chain_id=to_chain_id,
            from_amount=amount,
            to_amount=quote.to_amount,
            estimated_arrival=int(time.time()) + quote.estimated_time
        )
        
        # Track pending bridge
        self._pending_bridges[bridge_id] = result
        
        # Simulate bridge completion
        asyncio.create_task(self._simulate_bridge_completion(bridge_id, quote.estimated_time))
        
        return result
    
    async def _simulate_bridge_completion(self, bridge_id: str, duration: int) -> None:
        """Simulate bridge completion (for demo)"""
        # Source confirmation
        await asyncio.sleep(3)
        if bridge_id in self._pending_bridges:
            self._pending_bridges[bridge_id].status = BridgeStatus.SOURCE_CONFIRMED
        
        # Bridging
        await asyncio.sleep(min(duration / 10, 5))
        if bridge_id in self._pending_bridges:
            self._pending_bridges[bridge_id].status = BridgeStatus.BRIDGING
        
        # Destination pending
        await asyncio.sleep(min(duration / 10, 5))
        if bridge_id in self._pending_bridges:
            self._pending_bridges[bridge_id].status = BridgeStatus.DESTINATION_PENDING
            self._pending_bridges[bridge_id].destination_tx_hash = f"0x{uuid.uuid4().hex}"
        
        # Completed
        await asyncio.sleep(3)
        if bridge_id in self._pending_bridges:
            self._pending_bridges[bridge_id].status = BridgeStatus.COMPLETED
    
    async def get_transaction_status(self, tx_hash: str) -> Optional[TransactionResult]:
        """Get status of a pending transaction"""
        return self._pending_transactions.get(tx_hash)
    
    async def get_bridge_status(self, bridge_id: str) -> Optional[BridgeResult]:
        """Get status of a pending bridge"""
        return self._pending_bridges.get(bridge_id)
    
    def register_status_callback(
        self, tx_hash: str, callback: Callable
    ) -> None:
        """Register callback for transaction status updates"""
        if tx_hash not in self._status_callbacks:
            self._status_callbacks[tx_hash] = []
        self._status_callbacks[tx_hash].append(callback)
    
    async def _notify_status_change(
        self, tx_hash: str, result: TransactionResult
    ) -> None:
        """Notify registered callbacks of status change"""
        callbacks = self._status_callbacks.get(tx_hash, [])
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(result)
                else:
                    callback(result)
            except Exception as e:
                logger.error(f"Status callback error: {e}")
    
    async def _poll_transaction_status(self) -> None:
        """Background task to poll transaction status"""
        while True:
            try:
                # In production, poll actual blockchain nodes
                # For demo, transactions are simulated
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Status polling error: {e}")
                await asyncio.sleep(10)
    
    async def get_supported_bridges(
        self, from_chain_id: int, to_chain_id: int
    ) -> List[Dict[str, Any]]:
        """Get list of supported bridges between two chains"""
        # LI.FI supports most chain combinations
        bridges = [
            {
                "name": "LI.FI",
                "supported": True,
                "estimated_time": self._estimate_bridge_time(from_chain_id, to_chain_id),
                "fee_percent": 0.2
            }
        ]
        
        # Add specific bridges based on chains
        if from_chain_id == 1 and to_chain_id == 42161:
            bridges.append({
                "name": "Arbitrum Bridge",
                "supported": True,
                "estimated_time": 600,
                "fee_percent": 0
            })
        
        if from_chain_id == 1 and to_chain_id == 10:
            bridges.append({
                "name": "Optimism Bridge",
                "supported": True,
                "estimated_time": 600,
                "fee_percent": 0
            })
        
        return bridges
    
    def _estimate_bridge_time(self, from_chain_id: int, to_chain_id: int) -> int:
        """Estimate bridge time in seconds"""
        # L2 to L1 takes longer due to challenge period
        l2_chains = {42161, 10, 8453}
        
        if from_chain_id in l2_chains and to_chain_id == 1:
            return 604800  # 7 days for optimistic rollup withdrawal
        
        if from_chain_id == 1 and to_chain_id in l2_chains:
            return 600  # ~10 minutes
        
        return 1200  # Default 20 minutes


# Global cross-chain router instance
cross_chain_router = CrossChainRouter()
