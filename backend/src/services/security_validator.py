"""
Phase 5: Security Validation Service

Provides:
- High-value transaction detection
- Risk warnings
- MEV protection routing
- Transaction simulation
- Daily limits
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Set
from decimal import Decimal
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskWarning:
    level: RiskLevel
    code: str
    message: str
    details: Dict[str, Any]


@dataclass
class SecurityCheck:
    passed: bool
    requires_confirmation: bool
    warnings: List[RiskWarning]
    mev_protection_recommended: bool
    simulation_result: Optional[Dict[str, Any]]


# Known scam tokens (simplified - in production use external API)
KNOWN_SCAM_TOKENS: Set[str] = set()

# MEV-vulnerable transaction types
MEV_VULNERABLE_OPERATIONS = ["swap", "limit_order", "arbitrage"]


class SecurityValidator:
    def __init__(self):
        self.daily_volumes: Dict[str, Dict[str, Decimal]] = {}
        self.user_limits: Dict[str, Decimal] = {}
        self.default_daily_limit = Decimal("50000")  # USD
        self.high_value_threshold = Decimal("10000")  # USD
    
    def _get_today_key(self) -> str:
        return datetime.utcnow().strftime("%Y-%m-%d")
    
    async def check_high_value_transaction(
        self,
        user_address: str,
        value_usd: Decimal
    ) -> RiskWarning:
        """Check if transaction is high value and needs confirmation."""
        if value_usd >= self.high_value_threshold:
            return RiskWarning(
                level=RiskLevel.HIGH if value_usd >= self.high_value_threshold * 5 else RiskLevel.MEDIUM,
                code="HIGH_VALUE",
                message=f"High value transaction: ${value_usd:,.2f}",
                details={
                    "value_usd": float(value_usd),
                    "threshold_usd": float(self.high_value_threshold),
                    "requires_confirmation": True
                }
            )
        return None
    
    async def check_slippage_risk(
        self,
        expected_output: Decimal,
        minimum_output: Decimal,
        slippage_tolerance: Decimal
    ) -> Optional[RiskWarning]:
        """Check for high slippage scenarios."""
        actual_slippage = (expected_output - minimum_output) / expected_output * 100
        
        if actual_slippage > Decimal("5"):
            return RiskWarning(
                level=RiskLevel.HIGH,
                code="HIGH_SLIPPAGE",
                message=f"High slippage detected: {actual_slippage:.2f}%",
                details={
                    "expected_slippage": float(slippage_tolerance),
                    "actual_slippage": float(actual_slippage),
                    "potential_loss_percent": float(actual_slippage)
                }
            )
        elif actual_slippage > Decimal("2"):
            return RiskWarning(
                level=RiskLevel.MEDIUM,
                code="MODERATE_SLIPPAGE",
                message=f"Moderate slippage: {actual_slippage:.2f}%",
                details={"actual_slippage": float(actual_slippage)}
            )
        return None

    async def check_liquidity(
        self,
        pool_liquidity_usd: Decimal,
        trade_value_usd: Decimal
    ) -> Optional[RiskWarning]:
        """Check for low liquidity warnings."""
        impact_ratio = trade_value_usd / pool_liquidity_usd if pool_liquidity_usd > 0 else Decimal("1")
        
        if impact_ratio > Decimal("0.1"):
            return RiskWarning(
                level=RiskLevel.HIGH,
                code="LOW_LIQUIDITY",
                message="Low liquidity - trade may significantly impact price",
                details={
                    "pool_liquidity_usd": float(pool_liquidity_usd),
                    "trade_value_usd": float(trade_value_usd),
                    "impact_ratio": float(impact_ratio)
                }
            )
        elif impact_ratio > Decimal("0.05"):
            return RiskWarning(
                level=RiskLevel.MEDIUM,
                code="MODERATE_LIQUIDITY",
                message="Moderate liquidity impact expected",
                details={"impact_ratio": float(impact_ratio)}
            )
        return None
    
    async def check_token_safety(self, token_address: str) -> Optional[RiskWarning]:
        """Check token against scam databases."""
        if token_address.lower() in KNOWN_SCAM_TOKENS:
            return RiskWarning(
                level=RiskLevel.CRITICAL,
                code="SCAM_TOKEN",
                message="This token has been flagged as potentially malicious",
                details={"token_address": token_address, "action": "BLOCK"}
            )
        return None
    
    async def check_mev_vulnerability(
        self,
        operation_type: str,
        value_usd: Decimal,
        chain_id: int
    ) -> Dict[str, Any]:
        """Check if transaction is vulnerable to MEV attacks."""
        is_vulnerable = (
            operation_type in MEV_VULNERABLE_OPERATIONS and
            value_usd > Decimal("1000") and
            chain_id == 1  # Ethereum mainnet
        )
        
        return {
            "is_vulnerable": is_vulnerable,
            "recommended_protection": is_vulnerable,
            "protection_methods": ["flashbots", "mev_blocker"] if is_vulnerable else [],
            "reason": "Large swap on Ethereum mainnet" if is_vulnerable else None
        }

    async def check_daily_limit(
        self,
        user_address: str,
        value_usd: Decimal
    ) -> Optional[RiskWarning]:
        """Check if transaction exceeds daily limit."""
        user_key = user_address.lower()
        today = self._get_today_key()
        
        if user_key not in self.daily_volumes:
            self.daily_volumes[user_key] = {}
        
        current_volume = self.daily_volumes[user_key].get(today, Decimal("0"))
        limit = self.user_limits.get(user_key, self.default_daily_limit)
        
        if current_volume + value_usd > limit:
            return RiskWarning(
                level=RiskLevel.HIGH,
                code="DAILY_LIMIT_EXCEEDED",
                message=f"Transaction would exceed daily limit of ${limit:,.2f}",
                details={
                    "current_volume_usd": float(current_volume),
                    "transaction_value_usd": float(value_usd),
                    "daily_limit_usd": float(limit),
                    "remaining_usd": float(max(Decimal("0"), limit - current_volume))
                }
            )
        return None
    
    async def record_transaction_volume(
        self,
        user_address: str,
        value_usd: Decimal
    ):
        """Record transaction volume for daily limit tracking."""
        user_key = user_address.lower()
        today = self._get_today_key()
        
        if user_key not in self.daily_volumes:
            self.daily_volumes[user_key] = {}
        
        current = self.daily_volumes[user_key].get(today, Decimal("0"))
        self.daily_volumes[user_key][today] = current + value_usd
    
    async def set_user_daily_limit(self, user_address: str, limit_usd: Decimal):
        """Set custom daily limit for a user."""
        self.user_limits[user_address.lower()] = limit_usd
    
    async def simulate_transaction(
        self,
        chain_id: int,
        from_address: str,
        to_address: str,
        data: str,
        value: int = 0
    ) -> Dict[str, Any]:
        """Simulate transaction before execution."""
        # In production, use Tenderly or similar service
        return {
            "success": True,
            "gas_used": 150000,
            "state_changes": [],
            "logs": [],
            "error": None
        }

    async def validate_transaction(
        self,
        user_address: str,
        operation_type: str,
        chain_id: int,
        value_usd: Decimal,
        from_token: str,
        to_token: str,
        expected_output: Optional[Decimal] = None,
        minimum_output: Optional[Decimal] = None,
        slippage_tolerance: Decimal = Decimal("0.5"),
        pool_liquidity_usd: Optional[Decimal] = None
    ) -> SecurityCheck:
        """Comprehensive security validation for a transaction."""
        warnings = []
        requires_confirmation = False
        
        # High value check
        high_value_warning = await self.check_high_value_transaction(user_address, value_usd)
        if high_value_warning:
            warnings.append(high_value_warning)
            requires_confirmation = True
        
        # Slippage check
        if expected_output and minimum_output:
            slippage_warning = await self.check_slippage_risk(
                expected_output, minimum_output, slippage_tolerance
            )
            if slippage_warning:
                warnings.append(slippage_warning)
        
        # Liquidity check
        if pool_liquidity_usd:
            liquidity_warning = await self.check_liquidity(pool_liquidity_usd, value_usd)
            if liquidity_warning:
                warnings.append(liquidity_warning)
        
        # Token safety
        for token in [from_token, to_token]:
            if token and token.startswith("0x"):
                token_warning = await self.check_token_safety(token)
                if token_warning:
                    warnings.append(token_warning)
        
        # Daily limit
        limit_warning = await self.check_daily_limit(user_address, value_usd)
        if limit_warning:
            warnings.append(limit_warning)
            requires_confirmation = True
        
        # MEV check
        mev_check = await self.check_mev_vulnerability(operation_type, value_usd, chain_id)
        
        # Determine if passed
        critical_warnings = [w for w in warnings if w.level == RiskLevel.CRITICAL]
        passed = len(critical_warnings) == 0
        
        return SecurityCheck(
            passed=passed,
            requires_confirmation=requires_confirmation,
            warnings=warnings,
            mev_protection_recommended=mev_check["recommended_protection"],
            simulation_result=None
        )


# Singleton instance
security_validator = SecurityValidator()
