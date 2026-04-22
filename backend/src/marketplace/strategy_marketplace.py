"""
Strategy Marketplace - Trading Strategy Listing and Following
Phase 4: Ecosystem & Compliance

Platform for traders to monetize agent configurations through performance fees.
"""

import hashlib
import math
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class StrategyCategory(Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class ListingStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REMOVED = "removed"


class SubscriptionStatus(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    CANCELLED = "cancelled"


@dataclass
class TrackRecord:
    start_date: datetime
    total_trades: int
    total_return_percent: float
    sharpe_ratio: float
    max_drawdown_percent: float
    win_rate: float


@dataclass
class RiskMetrics:
    volatility: float
    var_95: float  # Value at Risk 95%
    sortino_ratio: float
    beta: float
    max_leverage: float


@dataclass
class StrategyListing:
    strategy_id: str
    publisher_address: str
    name: str
    description: str
    category: StrategyCategory
    performance_fee_percent: float
    min_allocation: float
    track_record: TrackRecord
    risk_metrics: RiskMetrics
    status: ListingStatus
    created_at: datetime
    followers_count: int = 0


@dataclass
class StrategySubscription:
    subscription_id: str
    follower_address: str
    strategy_id: str
    allocation_amount: float
    high_water_mark: float
    pending_fees: float
    subscribed_at: datetime
    status: SubscriptionStatus
    current_value: float = 0.0


@dataclass
class FeeCalculation:
    subscription_id: str
    gross_profit: float
    fee_amount: float
    fee_percent: float
    high_water_mark: float
    new_high_water_mark: float


@dataclass
class ReplicatedTrade:
    original_trade_id: str
    follower_address: str
    amount: float
    proportion: float
    timestamp: datetime


@dataclass
class ValidationResult:
    valid: bool
    errors: List[str]
    warnings: List[str]


@dataclass
class FeeSettlement:
    subscription_id: str
    settled_amount: float
    settlement_time: datetime


@dataclass
class StrategyFilters:
    category: Optional[StrategyCategory] = None
    min_return: Optional[float] = None
    max_drawdown: Optional[float] = None
    min_sharpe: Optional[float] = None


class StrategyMarketplace:
    """
    Strategy Marketplace for listing and following trading strategies.
    
    Validates: Requirements 3.1-3.6, 4.1-4.6
    """
    
    MIN_TRACK_RECORD_DAYS = 30
    MIN_TRADES_FOR_LISTING = 10
    MAX_PERFORMANCE_FEE = 20.0
    
    def __init__(self):
        self.listings: Dict[str, StrategyListing] = {}
        self.subscriptions: Dict[str, StrategySubscription] = {}
        self.trades_by_strategy: Dict[str, List[Dict]] = {}

    async def validate_listing(self, listing: StrategyListing) -> ValidationResult:
        """
        Validate strategy listing requirements.
        
        Property 6: Strategy Listing Validation
        For any strategy submission, validates 30 days track record and 10+ trades.
        
        Property 7: Performance Fee Cap Enforcement
        For any strategy listing, performance fee SHALL NOT exceed 20%.
        """
        errors = []
        warnings = []
        
        # Check track record duration
        track_days = (datetime.utcnow() - listing.track_record.start_date).days
        if track_days < self.MIN_TRACK_RECORD_DAYS:
            errors.append(f"Track record {track_days} days, minimum {self.MIN_TRACK_RECORD_DAYS} required")
        
        # Check minimum trades
        if listing.track_record.total_trades < self.MIN_TRADES_FOR_LISTING:
            errors.append(f"Total trades {listing.track_record.total_trades}, minimum {self.MIN_TRADES_FOR_LISTING} required")
        
        # Check performance fee cap
        if listing.performance_fee_percent > self.MAX_PERFORMANCE_FEE:
            errors.append(f"Performance fee {listing.performance_fee_percent}% exceeds maximum {self.MAX_PERFORMANCE_FEE}%")
        
        # Warnings
        if listing.track_record.max_drawdown_percent > 30:
            warnings.append("High max drawdown may deter followers")
        
        if listing.track_record.sharpe_ratio < 1.0:
            warnings.append("Sharpe ratio below 1.0 indicates suboptimal risk-adjusted returns")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    async def list_strategy(self, listing: StrategyListing) -> str:
        """
        List a strategy on the marketplace.
        
        Property 12: Strategy Category Assignment
        For any strategy listing, assigns exactly one category based on risk metrics.
        """
        validation = await self.validate_listing(listing)
        if not validation.valid:
            raise ValueError(f"Listing validation failed: {validation.errors}")
        
        # Assign category based on risk metrics if not set
        if not listing.category:
            listing.category = self._determine_category(listing.risk_metrics)
        
        listing.status = ListingStatus.ACTIVE
        self.listings[listing.strategy_id] = listing
        self.trades_by_strategy[listing.strategy_id] = []
        
        logger.info(f"Listed strategy {listing.strategy_id}: {listing.name}")
        return listing.strategy_id

    def _determine_category(self, metrics: RiskMetrics) -> StrategyCategory:
        """Determine strategy category based on risk metrics."""
        if metrics.volatility < 0.1 and metrics.max_leverage <= 1.0:
            return StrategyCategory.CONSERVATIVE
        elif metrics.volatility > 0.3 or metrics.max_leverage > 3.0:
            return StrategyCategory.AGGRESSIVE
        return StrategyCategory.MODERATE

    async def follow_strategy(
        self,
        follower: str,
        strategy_id: str,
        allocation: float
    ) -> StrategySubscription:
        """
        Follow a strategy and start replicating trades.
        
        Property 9: Proportional Trade Replication
        For any strategy trade, follower trades replicated proportionally.
        """
        listing = self.listings.get(strategy_id)
        if not listing or listing.status != ListingStatus.ACTIVE:
            raise ValueError("Strategy not available")
        
        if allocation < listing.min_allocation:
            raise ValueError(f"Minimum allocation is {listing.min_allocation}")
        
        subscription_id = self._generate_id("sub")
        subscription = StrategySubscription(
            subscription_id=subscription_id,
            follower_address=follower,
            strategy_id=strategy_id,
            allocation_amount=allocation,
            high_water_mark=allocation,
            pending_fees=0.0,
            subscribed_at=datetime.utcnow(),
            status=SubscriptionStatus.ACTIVE,
            current_value=allocation,
        )
        
        self.subscriptions[subscription_id] = subscription
        listing.followers_count += 1
        
        logger.info(f"User {follower} followed strategy {strategy_id} with ${allocation}")
        return subscription

    async def unfollow_strategy(self, subscription_id: str) -> FeeSettlement:
        """
        Unfollow a strategy and settle pending fees.
        
        Property 10: Fee Settlement on Unfollow
        For any unfollow action, pending fees settled immediately.
        """
        subscription = self.subscriptions.get(subscription_id)
        if not subscription:
            raise ValueError("Subscription not found")
        
        # Calculate final fees
        fee_calc = await self.calculate_fees(subscription_id)
        
        # Settle fees
        settlement = FeeSettlement(
            subscription_id=subscription_id,
            settled_amount=fee_calc.fee_amount,
            settlement_time=datetime.utcnow(),
        )
        
        # Update subscription status
        subscription.status = SubscriptionStatus.CANCELLED
        subscription.pending_fees = 0.0
        
        # Update listing followers count
        listing = self.listings.get(subscription.strategy_id)
        if listing:
            listing.followers_count = max(0, listing.followers_count - 1)
        
        logger.info(f"Unfollowed subscription {subscription_id}, settled ${settlement.settled_amount}")
        return settlement

    async def calculate_fees(self, subscription_id: str) -> FeeCalculation:
        """
        Calculate performance fees using high-water mark.
        
        Property 8: High-Water Mark Fee Calculation
        Fees only charged on profits above previous high-water mark.
        """
        subscription = self.subscriptions.get(subscription_id)
        if not subscription:
            raise ValueError("Subscription not found")
        
        listing = self.listings.get(subscription.strategy_id)
        if not listing:
            raise ValueError("Strategy not found")
        
        current_value = subscription.current_value
        high_water_mark = subscription.high_water_mark
        
        # Only charge fees on profits above high-water mark
        if current_value <= high_water_mark:
            return FeeCalculation(
                subscription_id=subscription_id,
                gross_profit=0.0,
                fee_amount=0.0,
                fee_percent=listing.performance_fee_percent,
                high_water_mark=high_water_mark,
                new_high_water_mark=high_water_mark,
            )
        
        gross_profit = current_value - high_water_mark
        fee_amount = gross_profit * (listing.performance_fee_percent / 100)
        new_hwm = current_value
        
        return FeeCalculation(
            subscription_id=subscription_id,
            gross_profit=gross_profit,
            fee_amount=fee_amount,
            fee_percent=listing.performance_fee_percent,
            high_water_mark=high_water_mark,
            new_high_water_mark=new_hwm,
        )

    async def replicate_trade(
        self,
        strategy_id: str,
        trade: Dict[str, Any]
    ) -> List[ReplicatedTrade]:
        """
        Replicate a strategy trade to all followers.
        
        Property 9: Proportional Trade Replication
        For any strategy trade, follower trades replicated proportionally.
        """
        listing = self.listings.get(strategy_id)
        if not listing:
            return []
        
        # Get total strategy AUM for proportion calculation
        strategy_aum = trade.get("strategy_aum", 100000)
        trade_amount = trade.get("amount", 0)
        trade_proportion = trade_amount / strategy_aum if strategy_aum > 0 else 0
        
        replicated = []
        for sub in self.subscriptions.values():
            if sub.strategy_id == strategy_id and sub.status == SubscriptionStatus.ACTIVE:
                follower_amount = sub.allocation_amount * trade_proportion
                
                replicated_trade = ReplicatedTrade(
                    original_trade_id=trade.get("trade_id", ""),
                    follower_address=sub.follower_address,
                    amount=follower_amount,
                    proportion=trade_proportion,
                    timestamp=datetime.utcnow(),
                )
                replicated.append(replicated_trade)
        
        # Store trade for analytics
        if strategy_id in self.trades_by_strategy:
            self.trades_by_strategy[strategy_id].append(trade)
        
        return replicated

    def calculate_sharpe_ratio(
        self,
        returns: List[float],
        risk_free_rate: float = 0.02
    ) -> float:
        """
        Calculate Sharpe ratio for a strategy.
        
        Property 11: Sharpe Ratio Calculation
        For any strategy with sufficient history, calculates Sharpe ratio correctly.
        """
        if len(returns) < 2:
            return 0.0
        
        mean_return = sum(returns) / len(returns)
        excess_return = mean_return - (risk_free_rate / 252)  # Daily risk-free rate
        
        variance = sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)
        std_dev = math.sqrt(variance) if variance > 0 else 0.001
        
        sharpe = (excess_return / std_dev) * math.sqrt(252)  # Annualized
        return round(sharpe, 4)

    async def search_strategies(
        self,
        filters: Optional[StrategyFilters] = None
    ) -> List[StrategyListing]:
        """Search strategies with optional filters."""
        results = [l for l in self.listings.values() if l.status == ListingStatus.ACTIVE]
        
        if filters:
            if filters.category:
                results = [l for l in results if l.category == filters.category]
            if filters.min_return is not None:
                results = [l for l in results if l.track_record.total_return_percent >= filters.min_return]
            if filters.max_drawdown is not None:
                results = [l for l in results if l.track_record.max_drawdown_percent <= filters.max_drawdown]
            if filters.min_sharpe is not None:
                results = [l for l in results if l.track_record.sharpe_ratio >= filters.min_sharpe]
        
        return sorted(results, key=lambda x: x.track_record.sharpe_ratio, reverse=True)

    async def get_strategy(self, strategy_id: str) -> Optional[StrategyListing]:
        """Get strategy by ID."""
        return self.listings.get(strategy_id)

    async def suspend_strategy(self, strategy_id: str, reason: str) -> bool:
        """Suspend a strategy listing."""
        listing = self.listings.get(strategy_id)
        if not listing:
            return False
        
        listing.status = ListingStatus.SUSPENDED
        logger.warning(f"Suspended strategy {strategy_id}: {reason}")
        return True

    async def update_subscription_value(
        self,
        subscription_id: str,
        new_value: float
    ) -> None:
        """Update subscription current value for P&L tracking."""
        subscription = self.subscriptions.get(subscription_id)
        if subscription:
            subscription.current_value = new_value
            if new_value > subscription.high_water_mark:
                subscription.high_water_mark = new_value

    def _generate_id(self, prefix: str) -> str:
        """Generate unique ID."""
        return f"{prefix}_{hashlib.sha256(f'{time.time()}'.encode()).hexdigest()[:12]}"
