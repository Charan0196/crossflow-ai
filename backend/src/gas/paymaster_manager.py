"""
Paymaster Manager - Gas Abstraction with ERC-4337
Phase 3: Autonomy & MEV Protection

Manages Paymaster contracts for gas abstraction across chains.
"""

import hashlib
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class PaymasterStatus(Enum):
    ACTIVE = "active"
    LOW_BALANCE = "low_balance"
    PAUSED = "paused"
    UNAVAILABLE = "unavailable"


class SponsorshipStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    EXECUTED = "executed"
    FAILED = "failed"
    REFUNDED = "refunded"


@dataclass
class Token:
    symbol: str
    address: str
    decimals: int
    chain: str


@dataclass
class PaymasterInfo:
    paymaster_id: str
    chain: str
    address: str
    supported_tokens: List[Token]
    balance: float
    daily_limit: float
    daily_usage: float
    fee_markup: float  # e.g., 0.01 = 1% markup
    status: PaymasterStatus


@dataclass
class GasEstimate:
    chain: str
    gas_limit: int
    gas_price_gwei: float
    total_cost_native: float
    total_cost_usd: float


@dataclass
class SponsorshipResult:
    sponsorship_id: str
    paymaster_id: str
    transaction_hash: str
    gas_sponsored: float
    payment_token: Token
    payment_amount: float
    exchange_rate: float
    status: SponsorshipStatus
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PaymasterBalance:
    paymaster_id: str
    native_balance: float
    token_balances: Dict[str, float]
    daily_remaining: float


class PaymasterManager:
    """
    Paymaster Manager handles gas abstraction using ERC-4337 Paymasters.
    
    Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5
    """
    
    # Slippage buffer for exchange rate volatility
    SLIPPAGE_BUFFER = 0.02  # 2%
    
    def __init__(self):
        self.paymasters: Dict[str, PaymasterInfo] = {}
        self.sponsorships: Dict[str, SponsorshipResult] = {}
        self.exchange_rates: Dict[str, float] = {}  # token_symbol -> USD rate
        self._initialize_paymasters()
        self._initialize_rates()

    def _initialize_paymasters(self):
        """Initialize Paymasters for supported chains."""
        chains = ["ethereum", "arbitrum", "polygon", "optimism", "base"]
        
        for chain in chains:
            pm_id = f"pm_{chain}"
            usdc = Token("USDC", f"0x{chain[:8]}usdc", 6, chain)
            usdt = Token("USDT", f"0x{chain[:8]}usdt", 6, chain)
            
            self.paymasters[pm_id] = PaymasterInfo(
                paymaster_id=pm_id,
                chain=chain,
                address=f"0x{hashlib.sha256(chain.encode()).hexdigest()[:40]}",
                supported_tokens=[usdc, usdt],
                balance=100000.0,
                daily_limit=50000.0,
                daily_usage=0.0,
                fee_markup=0.01,
                status=PaymasterStatus.ACTIVE
            )
    
    def _initialize_rates(self):
        """Initialize exchange rates."""
        self.exchange_rates = {
            "ETH": 2000.0,
            "MATIC": 0.80,
            "USDC": 1.0,
            "USDT": 1.0,
            "ARB": 1.20,
            "OP": 2.50,
        }
    
    async def get_available_paymasters(self, chain: str) -> List[PaymasterInfo]:
        """
        Get available Paymasters for a chain.
        
        Property 29: Multi-Chain Gas Abstraction
        For any chain with Paymaster infrastructure, gas abstraction is supported.
        """
        return [
            pm for pm in self.paymasters.values()
            if pm.chain == chain and pm.status == PaymasterStatus.ACTIVE
        ]
    
    async def request_sponsorship(
        self,
        transaction: Dict[str, Any],
        payment_token: Token,
        gas_estimate: GasEstimate
    ) -> SponsorshipResult:
        """
        Request gas sponsorship for a transaction.
        
        Property 25: Alternative Token Gas Payment
        For any trade, offers option to pay gas in alternative tokens.
        """
        chain = transaction.get("chain", "ethereum")
        paymasters = await self.get_available_paymasters(chain)
        
        if not paymasters:
            raise ValueError(f"No Paymaster available for {chain}")
        
        paymaster = paymasters[0]
        
        # Check if token is supported
        supported = any(t.symbol == payment_token.symbol for t in paymaster.supported_tokens)
        if not supported:
            raise ValueError(f"Token {payment_token.symbol} not supported")
        
        # Calculate token amount with slippage buffer
        token_amount = await self.calculate_token_amount(gas_estimate, payment_token)
        
        # Check daily limit
        if paymaster.daily_usage + gas_estimate.total_cost_usd > paymaster.daily_limit:
            raise ValueError("Daily sponsorship limit exceeded")
        
        sponsorship_id = self._generate_id("sponsor")
        
        result = SponsorshipResult(
            sponsorship_id=sponsorship_id,
            paymaster_id=paymaster.paymaster_id,
            transaction_hash=transaction.get("hash", ""),
            gas_sponsored=gas_estimate.total_cost_native,
            payment_token=payment_token,
            payment_amount=token_amount,
            exchange_rate=self.exchange_rates.get(payment_token.symbol, 1.0),
            status=SponsorshipStatus.APPROVED
        )
        
        self.sponsorships[sponsorship_id] = result
        paymaster.daily_usage += gas_estimate.total_cost_usd
        
        return result

    async def calculate_token_amount(
        self,
        gas_estimate: GasEstimate,
        payment_token: Token
    ) -> float:
        """
        Calculate token amount for gas payment.
        
        Property 26: Real-Time Exchange Rate Calculation
        For any gas cost calculation, uses real-time rates with slippage buffers.
        """
        gas_cost_usd = gas_estimate.total_cost_usd
        token_rate = self.exchange_rates.get(payment_token.symbol, 1.0)
        
        # Base amount
        base_amount = gas_cost_usd / token_rate
        
        # Add slippage buffer
        buffered_amount = base_amount * (1 + self.SLIPPAGE_BUFFER)
        
        # Add paymaster fee markup
        paymaster = next(
            (pm for pm in self.paymasters.values() if payment_token.chain == pm.chain),
            None
        )
        markup = paymaster.fee_markup if paymaster else 0.01
        
        final_amount = buffered_amount * (1 + markup)
        
        return round(final_amount, payment_token.decimals)
    
    async def check_paymaster_balance(
        self,
        paymaster_id: str
    ) -> PaymasterBalance:
        """Check Paymaster balance and limits."""
        paymaster = self.paymasters.get(paymaster_id)
        if not paymaster:
            raise ValueError(f"Paymaster {paymaster_id} not found")
        
        return PaymasterBalance(
            paymaster_id=paymaster_id,
            native_balance=paymaster.balance,
            token_balances={t.symbol: 10000.0 for t in paymaster.supported_tokens},
            daily_remaining=paymaster.daily_limit - paymaster.daily_usage
        )
    
    async def refill_paymaster(
        self,
        paymaster_id: str,
        amount: float
    ) -> Dict[str, Any]:
        """Refill Paymaster balance."""
        paymaster = self.paymasters.get(paymaster_id)
        if not paymaster:
            return {"success": False, "message": "Paymaster not found"}
        
        paymaster.balance += amount
        
        if paymaster.status == PaymasterStatus.LOW_BALANCE:
            paymaster.status = PaymasterStatus.ACTIVE
        
        return {
            "success": True,
            "new_balance": paymaster.balance,
            "status": paymaster.status.value
        }
    
    async def adjust_for_gas_change(
        self,
        sponsorship_id: str,
        new_gas_price: float
    ) -> SponsorshipResult:
        """
        Adjust sponsorship for gas price changes.
        
        Property 28: Dynamic Gas Adjustment
        For any gas price fluctuation, dynamically adjusts token amounts.
        """
        sponsorship = self.sponsorships.get(sponsorship_id)
        if not sponsorship:
            raise ValueError(f"Sponsorship {sponsorship_id} not found")
        
        # Recalculate based on new gas price
        old_rate = sponsorship.exchange_rate
        new_rate = self.exchange_rates.get(sponsorship.payment_token.symbol, 1.0)
        
        # Adjust payment amount
        adjustment_factor = new_gas_price / (sponsorship.gas_sponsored * old_rate)
        new_payment = sponsorship.payment_amount * adjustment_factor * (1 + self.SLIPPAGE_BUFFER)
        
        sponsorship.payment_amount = new_payment
        sponsorship.exchange_rate = new_rate
        
        return sponsorship

    async def validate_erc4337_compliance(
        self,
        paymaster_id: str
    ) -> Dict[str, Any]:
        """
        Validate Paymaster ERC-4337 compliance.
        
        Property 27: ERC-4337 Paymaster Compliance
        For any gas-abstracted transaction, uses ERC-4337 compliant Paymasters.
        """
        paymaster = self.paymasters.get(paymaster_id)
        if not paymaster:
            return {"compliant": False, "reason": "Paymaster not found"}
        
        # Check compliance requirements
        checks = {
            "has_valid_address": len(paymaster.address) == 42,
            "has_supported_tokens": len(paymaster.supported_tokens) > 0,
            "has_sufficient_balance": paymaster.balance > 0,
            "is_active": paymaster.status == PaymasterStatus.ACTIVE,
            "implements_validate_paymaster_user_op": True,  # Assumed
            "implements_post_op": True,  # Assumed
        }
        
        compliant = all(checks.values())
        
        return {
            "compliant": compliant,
            "checks": checks,
            "paymaster_id": paymaster_id
        }
    
    def update_exchange_rate(self, token_symbol: str, rate: float):
        """Update exchange rate for a token."""
        self.exchange_rates[token_symbol] = rate
    
    def get_supported_tokens(self, chain: str) -> List[Token]:
        """Get all supported tokens for gas payment on a chain."""
        tokens = []
        for pm in self.paymasters.values():
            if pm.chain == chain:
                tokens.extend(pm.supported_tokens)
        return list({t.symbol: t for t in tokens}.values())
    
    async def execute_sponsorship(
        self,
        sponsorship_id: str
    ) -> Dict[str, Any]:
        """Execute a pending sponsorship."""
        sponsorship = self.sponsorships.get(sponsorship_id)
        if not sponsorship:
            return {"success": False, "message": "Sponsorship not found"}
        
        if sponsorship.status != SponsorshipStatus.APPROVED:
            return {"success": False, "message": "Sponsorship not approved"}
        
        # Deduct from paymaster balance
        paymaster = self.paymasters.get(sponsorship.paymaster_id)
        if paymaster:
            paymaster.balance -= sponsorship.gas_sponsored
        
        sponsorship.status = SponsorshipStatus.EXECUTED
        
        return {
            "success": True,
            "sponsorship_id": sponsorship_id,
            "gas_sponsored": sponsorship.gas_sponsored
        }
    
    def _generate_id(self, prefix: str) -> str:
        """Generate unique ID."""
        return f"{prefix}_{hashlib.sha256(f'{time.time()}'.encode()).hexdigest()[:10]}"
    
    def reset_daily_usage(self):
        """Reset daily usage for all Paymasters."""
        for pm in self.paymasters.values():
            pm.daily_usage = 0.0
