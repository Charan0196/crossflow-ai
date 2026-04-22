"""
Gas Calculator - Cross-Chain Gas Estimation
Phase 3: Autonomy & MEV Protection

Calculates gas costs across chains and converts to alternative payment tokens.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class GasEstimate:
    chain: str
    gas_limit: int
    gas_price_gwei: float
    total_cost_native: float
    total_cost_usd: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CrossChainGasEstimate:
    intent_id: str
    source_chain_gas: GasEstimate
    destination_chain_gas: GasEstimate
    bridge_gas: Optional[GasEstimate]
    total_gas_cost_usd: float
    total_in_tokens: Dict[str, float]
    optimal_payment_token: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class GasPriceForecast:
    chain: str
    current_price_gwei: float
    forecast_1h: float
    forecast_6h: float
    forecast_24h: float
    trend: str  # "rising", "falling", "stable"
    confidence: float


@dataclass
class TimingSuggestion:
    suggested_time: datetime
    expected_savings_percent: float
    reason: str
    alternative_chains: List[str]


@dataclass
class GasAlert:
    chain: str
    alert_type: str  # "spike", "drop", "congestion"
    current_price: float
    threshold_price: float
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


class GasCalculator:
    """
    Gas Calculator estimates gas costs across chains.
    
    Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5
    """
    
    # Base gas costs by operation type
    BASE_GAS = {
        "transfer": 21000,
        "swap": 150000,
        "bridge": 200000,
        "approve": 46000,
    }
    
    # Native token prices (USD)
    NATIVE_PRICES = {
        "ethereum": 2000.0,
        "arbitrum": 2000.0,  # Uses ETH
        "polygon": 0.80,
        "optimism": 2000.0,  # Uses ETH
        "base": 2000.0,      # Uses ETH
        "bsc": 300.0,
    }
    
    # Current gas prices (gwei)
    GAS_PRICES = {
        "ethereum": 30.0,
        "arbitrum": 0.1,
        "polygon": 50.0,
        "optimism": 0.001,
        "base": 0.001,
        "bsc": 5.0,
    }
    
    def __init__(self):
        self.gas_history: Dict[str, List[float]] = {chain: [] for chain in self.GAS_PRICES}
        self.alerts: List[GasAlert] = []
        self.gas_reserves: Dict[str, float] = {}  # chain -> reserve amount

    async def estimate_gas_cost(
        self,
        chain: str,
        operation: str = "swap"
    ) -> GasEstimate:
        """Estimate gas cost for an operation on a chain."""
        gas_limit = self.BASE_GAS.get(operation, 100000)
        gas_price = self.GAS_PRICES.get(chain, 30.0)
        native_price = self.NATIVE_PRICES.get(chain, 2000.0)
        
        # Calculate cost in native token
        cost_native = (gas_limit * gas_price) / 1e9  # Convert gwei to native
        cost_usd = cost_native * native_price
        
        return GasEstimate(
            chain=chain,
            gas_limit=gas_limit,
            gas_price_gwei=gas_price,
            total_cost_native=cost_native,
            total_cost_usd=cost_usd
        )
    
    async def estimate_cross_chain_gas(
        self,
        intent_id: str,
        source_chain: str,
        dest_chain: str,
        include_bridge: bool = True
    ) -> CrossChainGasEstimate:
        """
        Estimate total gas for cross-chain intent.
        
        Property 30: Cross-Chain Gas Calculation
        For any cross-chain trade, calculates total gas across all chains.
        """
        source_gas = await self.estimate_gas_cost(source_chain, "swap")
        dest_gas = await self.estimate_gas_cost(dest_chain, "swap")
        
        bridge_gas = None
        if include_bridge and source_chain != dest_chain:
            bridge_gas = await self.estimate_gas_cost(source_chain, "bridge")
        
        total_usd = source_gas.total_cost_usd + dest_gas.total_cost_usd
        if bridge_gas:
            total_usd += bridge_gas.total_cost_usd
        
        # Calculate in different tokens
        token_amounts = {
            "USDC": total_usd,
            "USDT": total_usd,
            "ETH": total_usd / 2000.0,
        }
        
        # Find optimal payment token (lowest effective cost)
        optimal = min(token_amounts.items(), key=lambda x: x[1])[0]
        
        return CrossChainGasEstimate(
            intent_id=intent_id,
            source_chain_gas=source_gas,
            destination_chain_gas=dest_gas,
            bridge_gas=bridge_gas,
            total_gas_cost_usd=total_usd,
            total_in_tokens=token_amounts,
            optimal_payment_token=optimal
        )

    async def convert_to_token(
        self,
        gas_cost_usd: float,
        token_symbol: str
    ) -> float:
        """Convert gas cost to token amount."""
        token_prices = {
            "USDC": 1.0,
            "USDT": 1.0,
            "ETH": 2000.0,
            "MATIC": 0.80,
            "ARB": 1.20,
        }
        
        price = token_prices.get(token_symbol, 1.0)
        return gas_cost_usd / price
    
    async def get_gas_price_forecast(
        self,
        chain: str,
        hours: int = 24
    ) -> GasPriceForecast:
        """
        Forecast gas prices for a chain.
        
        Property 33: Gas Spike Alerting
        For any gas price spike, alerts users with alternatives.
        """
        current = self.GAS_PRICES.get(chain, 30.0)
        history = self.gas_history.get(chain, [current])
        
        # Simple trend analysis
        if len(history) >= 2:
            recent_avg = sum(history[-5:]) / min(len(history), 5)
            if current > recent_avg * 1.1:
                trend = "rising"
            elif current < recent_avg * 0.9:
                trend = "falling"
            else:
                trend = "stable"
        else:
            trend = "stable"
        
        # Forecast (simplified)
        forecast_1h = current * (1.0 if trend == "stable" else 1.1 if trend == "rising" else 0.9)
        forecast_6h = current * (1.0 if trend == "stable" else 1.2 if trend == "rising" else 0.8)
        forecast_24h = current * (1.0 if trend == "stable" else 1.3 if trend == "rising" else 0.7)
        
        return GasPriceForecast(
            chain=chain,
            current_price_gwei=current,
            forecast_1h=forecast_1h,
            forecast_6h=forecast_6h,
            forecast_24h=forecast_24h,
            trend=trend,
            confidence=0.7
        )
    
    async def suggest_optimal_timing(
        self,
        source_chain: str,
        dest_chain: str,
        urgency: str = "normal"
    ) -> TimingSuggestion:
        """Suggest optimal timing for execution."""
        source_forecast = await self.get_gas_price_forecast(source_chain)
        dest_forecast = await self.get_gas_price_forecast(dest_chain)
        
        # Find cheaper alternatives
        alternatives = []
        for chain, price in self.GAS_PRICES.items():
            if chain not in [source_chain, dest_chain] and price < self.GAS_PRICES.get(source_chain, 100):
                alternatives.append(chain)
        
        # Determine suggestion
        if urgency == "high":
            suggested_time = datetime.utcnow()
            savings = 0.0
            reason = "Immediate execution due to high urgency"
        elif source_forecast.trend == "rising":
            suggested_time = datetime.utcnow()
            savings = 10.0
            reason = "Execute now before gas prices rise further"
        elif source_forecast.trend == "falling":
            suggested_time = datetime.utcnow() + timedelta(hours=2)
            savings = 15.0
            reason = "Wait for lower gas prices"
        else:
            suggested_time = datetime.utcnow() + timedelta(hours=1)
            savings = 5.0
            reason = "Stable gas prices, slight delay may help"
        
        return TimingSuggestion(
            suggested_time=suggested_time,
            expected_savings_percent=savings,
            reason=reason,
            alternative_chains=alternatives[:3]
        )

    async def check_gas_spike(
        self,
        chain: str,
        threshold_multiplier: float = 1.5
    ) -> Optional[GasAlert]:
        """
        Check for gas price spikes.
        
        Property 33: Gas Spike Alerting
        """
        current = self.GAS_PRICES.get(chain, 30.0)
        history = self.gas_history.get(chain, [])
        
        if not history:
            return None
        
        avg = sum(history) / len(history)
        threshold = avg * threshold_multiplier
        
        if current > threshold:
            alert = GasAlert(
                chain=chain,
                alert_type="spike",
                current_price=current,
                threshold_price=threshold,
                message=f"Gas price on {chain} is {current:.1f} gwei, {(current/avg - 1)*100:.0f}% above average"
            )
            self.alerts.append(alert)
            return alert
        
        return None
    
    async def handle_missing_native_token(
        self,
        user_address: str,
        chain: str,
        required_amount: float
    ) -> Dict[str, Any]:
        """
        Handle case where user lacks native tokens.
        
        Property 31: Automatic Gas Bridging
        For users lacking native tokens, automatically handles gas.
        """
        # Check gas reserves
        reserve = self.gas_reserves.get(chain, 0)
        
        if reserve >= required_amount:
            # Use reserve
            self.gas_reserves[chain] = reserve - required_amount
            return {
                "method": "reserve",
                "amount_provided": required_amount,
                "remaining_reserve": self.gas_reserves[chain]
            }
        
        # Suggest Paymaster
        return {
            "method": "paymaster",
            "message": "Use Paymaster to pay gas in alternative token",
            "suggested_tokens": ["USDC", "USDT"],
            "required_amount_usd": required_amount * self.NATIVE_PRICES.get(chain, 2000.0)
        }
    
    async def get_unified_cost_display(
        self,
        intent_id: str,
        source_chain: str,
        dest_chain: str,
        preferred_currency: str = "USD"
    ) -> Dict[str, Any]:
        """
        Get unified gas cost display.
        
        Property 32: Unified Gas Cost Display
        For any trade, shows unified gas cost breakdown.
        """
        estimate = await self.estimate_cross_chain_gas(intent_id, source_chain, dest_chain)
        
        breakdown = {
            "source_chain": {
                "chain": source_chain,
                "gas_cost": estimate.source_chain_gas.total_cost_usd,
                "gas_price_gwei": estimate.source_chain_gas.gas_price_gwei
            },
            "destination_chain": {
                "chain": dest_chain,
                "gas_cost": estimate.destination_chain_gas.total_cost_usd,
                "gas_price_gwei": estimate.destination_chain_gas.gas_price_gwei
            },
            "total_cost": estimate.total_gas_cost_usd,
            "currency": preferred_currency,
            "payment_options": estimate.total_in_tokens,
            "recommended_payment": estimate.optimal_payment_token
        }
        
        if estimate.bridge_gas:
            breakdown["bridge"] = {
                "gas_cost": estimate.bridge_gas.total_cost_usd,
                "gas_price_gwei": estimate.bridge_gas.gas_price_gwei
            }
        
        return breakdown
    
    def update_gas_price(self, chain: str, price_gwei: float):
        """Update gas price for a chain."""
        self.GAS_PRICES[chain] = price_gwei
        if chain not in self.gas_history:
            self.gas_history[chain] = []
        self.gas_history[chain].append(price_gwei)
        # Keep last 100 prices
        self.gas_history[chain] = self.gas_history[chain][-100:]
    
    def add_gas_reserve(self, chain: str, amount: float):
        """
        Add to gas reserves.
        
        Property 34: Gas Reserve Maintenance
        Maintains gas reserves for uninterrupted execution.
        """
        self.gas_reserves[chain] = self.gas_reserves.get(chain, 0) + amount
    
    def get_gas_reserve(self, chain: str) -> float:
        """Get current gas reserve for a chain."""
        return self.gas_reserves.get(chain, 0)
