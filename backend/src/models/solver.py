"""
Solver model for CrossFlow AI solver network
Implements solver registration, reputation tracking, and performance metrics
"""
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
import json


class SolverStatus(Enum):
    """Solver status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    BLACKLISTED = "blacklisted"


class SolverTier(Enum):
    """Solver tier based on reputation and stake"""
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"


@dataclass
class SolverPerformanceMetrics:
    """Solver performance tracking metrics"""
    total_intents_received: int = 0
    total_bids_submitted: int = 0
    total_intents_won: int = 0
    total_intents_completed: int = 0
    total_intents_failed: int = 0
    total_volume_processed: Decimal = field(default_factory=lambda: Decimal('0'))
    average_execution_time: float = 0.0
    average_slippage: float = 0.0
    last_activity: Optional[datetime] = None
    
    @property
    def bid_win_rate(self) -> float:
        """Calculate bid win rate percentage"""
        if self.total_bids_submitted == 0:
            return 0.0
        return (self.total_intents_won / self.total_bids_submitted) * 100
    
    @property
    def completion_rate(self) -> float:
        """Calculate intent completion rate percentage"""
        if self.total_intents_won == 0:
            return 0.0
        return (self.total_intents_completed / self.total_intents_won) * 100
    
    @property
    def failure_rate(self) -> float:
        """Calculate intent failure rate percentage"""
        if self.total_intents_won == 0:
            return 0.0
        return (self.total_intents_failed / self.total_intents_won) * 100


@dataclass
class SolverReputationScore:
    """Solver reputation scoring system"""
    base_score: float = 1.0
    completion_bonus: float = 0.0
    speed_bonus: float = 0.0
    volume_bonus: float = 0.0
    reliability_penalty: float = 0.0
    slashing_penalty: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)
    
    @property
    def total_score(self) -> float:
        """Calculate total reputation score"""
        score = (
            self.base_score + 
            self.completion_bonus + 
            self.speed_bonus + 
            self.volume_bonus - 
            self.reliability_penalty - 
            self.slashing_penalty
        )
        return max(0.0, min(2.0, score))  # Clamp between 0 and 2
    
    def update_completion_bonus(self, completion_rate: float):
        """Update completion bonus based on completion rate"""
        if completion_rate >= 0.95:
            self.completion_bonus = 0.3
        elif completion_rate >= 0.90:
            self.completion_bonus = 0.2
        elif completion_rate >= 0.85:
            self.completion_bonus = 0.1
        else:
            self.completion_bonus = 0.0
    
    def update_speed_bonus(self, avg_execution_time: float):
        """Update speed bonus based on average execution time"""
        # Bonus for fast execution (under 5 minutes)
        if avg_execution_time <= 300:  # 5 minutes
            self.speed_bonus = 0.2
        elif avg_execution_time <= 600:  # 10 minutes
            self.speed_bonus = 0.1
        else:
            self.speed_bonus = 0.0
    
    def apply_slashing_penalty(self, penalty_amount: float):
        """Apply slashing penalty for malicious behavior"""
        self.slashing_penalty += penalty_amount
        self.last_updated = datetime.now()


@dataclass
class SolverStakeInfo:
    """Solver staking information"""
    stake_amount: Decimal
    stake_token: str  # Token contract address
    stake_timestamp: datetime
    minimum_stake_required: Decimal
    locked_until: Optional[datetime] = None
    slashed_amount: Decimal = field(default_factory=lambda: Decimal('0'))
    
    @property
    def effective_stake(self) -> Decimal:
        """Calculate effective stake after slashing"""
        return self.stake_amount - self.slashed_amount
    
    @property
    def is_sufficient(self) -> bool:
        """Check if stake meets minimum requirements"""
        return self.effective_stake >= self.minimum_stake_required
    
    @property
    def is_locked(self) -> bool:
        """Check if stake is currently locked"""
        if self.locked_until is None:
            return False
        return datetime.now() < self.locked_until
    
    def slash_stake(self, amount: Decimal) -> bool:
        """Slash stake for malicious behavior"""
        if amount <= 0 or amount > self.effective_stake:
            return False
        
        self.slashed_amount += amount
        return True


@dataclass
class Solver:
    """
    Solver model representing a market maker in the CrossFlow AI network
    Implements stake-based registration and reputation tracking
    """
    # Basic Information
    address: str  # Ethereum address
    name: str
    endpoint: str  # HTTP endpoint for communication
    
    # Network Configuration
    supported_chains: List[int]
    supported_tokens: List[str]
    
    # Status and Registration
    status: SolverStatus = SolverStatus.INACTIVE
    registration_timestamp: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)
    
    # Staking Information
    stake_info: SolverStakeInfo = None
    
    # Performance and Reputation
    performance_metrics: SolverPerformanceMetrics = field(default_factory=SolverPerformanceMetrics)
    reputation_score: SolverReputationScore = field(default_factory=SolverReputationScore)
    
    # Operational Limits
    max_concurrent_intents: int = 10
    current_concurrent_intents: int = 0
    
    # Additional Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-initialization validation and setup"""
        if not self.address or not self.address.startswith('0x') or len(self.address) != 42:
            raise ValueError(f"Invalid Ethereum address: {self.address}")
        
        if not self.endpoint or not self.endpoint.startswith(('http://', 'https://')):
            raise ValueError(f"Invalid endpoint URL: {self.endpoint}")
        
        if not self.supported_chains:
            raise ValueError("Solver must support at least one chain")
    
    @property
    def tier(self) -> SolverTier:
        """Determine solver tier based on reputation and stake"""
        reputation = self.reputation_score.total_score
        stake_amount = self.stake_info.effective_stake if self.stake_info else Decimal('0')
        
        # Tier calculation based on reputation and stake
        if reputation >= 1.8 and stake_amount >= Decimal('100'):  # 100 ETH equivalent
            return SolverTier.PLATINUM
        elif reputation >= 1.5 and stake_amount >= Decimal('50'):  # 50 ETH equivalent
            return SolverTier.GOLD
        elif reputation >= 1.2 and stake_amount >= Decimal('20'):  # 20 ETH equivalent
            return SolverTier.SILVER
        else:
            return SolverTier.BRONZE
    
    @property
    def is_eligible_for_intents(self) -> bool:
        """Check if solver is eligible to receive intents"""
        return (
            self.status == SolverStatus.ACTIVE and
            self.stake_info is not None and
            self.stake_info.is_sufficient and
            not self.stake_info.is_locked and
            self.current_concurrent_intents < self.max_concurrent_intents and
            self.reputation_score.total_score >= 0.7  # Minimum reputation threshold
        )
    
    def register_with_stake(
        self, 
        stake_amount: Decimal, 
        stake_token: str, 
        minimum_stake_required: Decimal
    ) -> bool:
        """Register solver with stake"""
        try:
            if stake_amount < minimum_stake_required:
                return False
            
            self.stake_info = SolverStakeInfo(
                stake_amount=stake_amount,
                stake_token=stake_token,
                stake_timestamp=datetime.now(),
                minimum_stake_required=minimum_stake_required
            )
            
            self.status = SolverStatus.ACTIVE
            self.registration_timestamp = datetime.now()
            return True
            
        except Exception:
            return False
    
    def update_performance_metrics(
        self,
        intent_received: bool = False,
        bid_submitted: bool = False,
        intent_won: bool = False,
        intent_completed: bool = False,
        intent_failed: bool = False,
        execution_time: Optional[float] = None,
        slippage: Optional[float] = None,
        volume_processed: Optional[Decimal] = None
    ):
        """Update solver performance metrics"""
        metrics = self.performance_metrics
        
        if intent_received:
            metrics.total_intents_received += 1
        
        if bid_submitted:
            metrics.total_bids_submitted += 1
        
        if intent_won:
            metrics.total_intents_won += 1
            self.current_concurrent_intents += 1
        
        if intent_completed:
            metrics.total_intents_completed += 1
            self.current_concurrent_intents = max(0, self.current_concurrent_intents - 1)
        
        if intent_failed:
            metrics.total_intents_failed += 1
            self.current_concurrent_intents = max(0, self.current_concurrent_intents - 1)
        
        if execution_time is not None:
            # Update average execution time using exponential moving average
            if metrics.average_execution_time == 0:
                metrics.average_execution_time = execution_time
            else:
                metrics.average_execution_time = (
                    0.8 * metrics.average_execution_time + 0.2 * execution_time
                )
        
        if slippage is not None:
            # Update average slippage using exponential moving average
            if metrics.average_slippage == 0:
                metrics.average_slippage = slippage
            else:
                metrics.average_slippage = (
                    0.8 * metrics.average_slippage + 0.2 * slippage
                )
        
        if volume_processed is not None:
            metrics.total_volume_processed += volume_processed
        
        metrics.last_activity = datetime.now()
        self.last_seen = datetime.now()
        
        # Update reputation score based on new metrics
        self._update_reputation_score()
    
    def _update_reputation_score(self):
        """Update reputation score based on current performance metrics"""
        metrics = self.performance_metrics
        reputation = self.reputation_score
        
        # Update completion bonus
        reputation.update_completion_bonus(metrics.completion_rate / 100)
        
        # Update speed bonus
        reputation.update_speed_bonus(metrics.average_execution_time)
        
        # Update volume bonus (higher volume = higher bonus)
        if metrics.total_volume_processed > Decimal('1000'):  # 1000 ETH equivalent
            reputation.volume_bonus = 0.2
        elif metrics.total_volume_processed > Decimal('500'):  # 500 ETH equivalent
            reputation.volume_bonus = 0.1
        else:
            reputation.volume_bonus = 0.0
        
        # Update reliability penalty based on failure rate
        failure_rate = metrics.failure_rate / 100
        if failure_rate > 0.15:  # More than 15% failure rate
            reputation.reliability_penalty = 0.3
        elif failure_rate > 0.10:  # More than 10% failure rate
            reputation.reliability_penalty = 0.2
        elif failure_rate > 0.05:  # More than 5% failure rate
            reputation.reliability_penalty = 0.1
        else:
            reputation.reliability_penalty = 0.0
        
        reputation.last_updated = datetime.now()
    
    def slash_for_malicious_behavior(self, slash_amount: Decimal, penalty_amount: float) -> bool:
        """Slash solver stake and reputation for malicious behavior"""
        if not self.stake_info:
            return False
        
        # Slash stake
        stake_slashed = self.stake_info.slash_stake(slash_amount)
        
        # Apply reputation penalty
        self.reputation_score.apply_slashing_penalty(penalty_amount)
        
        # Suspend solver if stake becomes insufficient
        if not self.stake_info.is_sufficient:
            self.status = SolverStatus.SUSPENDED
        
        return stake_slashed
    
    def suspend(self, duration_hours: int = 24):
        """Suspend solver for a specified duration"""
        self.status = SolverStatus.SUSPENDED
        if self.stake_info:
            self.stake_info.locked_until = datetime.now() + timedelta(hours=duration_hours)
    
    def reactivate(self) -> bool:
        """Reactivate suspended solver if conditions are met"""
        if self.status != SolverStatus.SUSPENDED:
            return False
        
        if not self.is_eligible_for_intents:
            return False
        
        self.status = SolverStatus.ACTIVE
        if self.stake_info:
            self.stake_info.locked_until = None
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert solver to dictionary representation"""
        return {
            "address": self.address,
            "name": self.name,
            "endpoint": self.endpoint,
            "supported_chains": self.supported_chains,
            "supported_tokens": self.supported_tokens,
            "status": self.status.value,
            "tier": self.tier.value,
            "registration_timestamp": self.registration_timestamp.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "stake_info": {
                "stake_amount": str(self.stake_info.stake_amount) if self.stake_info else "0",
                "effective_stake": str(self.stake_info.effective_stake) if self.stake_info else "0",
                "is_sufficient": self.stake_info.is_sufficient if self.stake_info else False,
                "is_locked": self.stake_info.is_locked if self.stake_info else False,
            } if self.stake_info else None,
            "performance_metrics": {
                "total_intents_received": self.performance_metrics.total_intents_received,
                "total_bids_submitted": self.performance_metrics.total_bids_submitted,
                "total_intents_won": self.performance_metrics.total_intents_won,
                "total_intents_completed": self.performance_metrics.total_intents_completed,
                "total_intents_failed": self.performance_metrics.total_intents_failed,
                "bid_win_rate": self.performance_metrics.bid_win_rate,
                "completion_rate": self.performance_metrics.completion_rate,
                "failure_rate": self.performance_metrics.failure_rate,
                "total_volume_processed": str(self.performance_metrics.total_volume_processed),
                "average_execution_time": self.performance_metrics.average_execution_time,
                "average_slippage": self.performance_metrics.average_slippage,
                "last_activity": self.performance_metrics.last_activity.isoformat() if self.performance_metrics.last_activity else None,
            },
            "reputation_score": {
                "total_score": self.reputation_score.total_score,
                "base_score": self.reputation_score.base_score,
                "completion_bonus": self.reputation_score.completion_bonus,
                "speed_bonus": self.reputation_score.speed_bonus,
                "volume_bonus": self.reputation_score.volume_bonus,
                "reliability_penalty": self.reputation_score.reliability_penalty,
                "slashing_penalty": self.reputation_score.slashing_penalty,
                "last_updated": self.reputation_score.last_updated.isoformat(),
            },
            "max_concurrent_intents": self.max_concurrent_intents,
            "current_concurrent_intents": self.current_concurrent_intents,
            "is_eligible_for_intents": self.is_eligible_for_intents,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Solver':
        """Create solver from dictionary representation"""
        # Parse basic fields
        solver = cls(
            address=data["address"],
            name=data["name"],
            endpoint=data["endpoint"],
            supported_chains=data["supported_chains"],
            supported_tokens=data["supported_tokens"],
            status=SolverStatus(data["status"]),
            registration_timestamp=datetime.fromisoformat(data["registration_timestamp"]),
            last_seen=datetime.fromisoformat(data["last_seen"]),
            max_concurrent_intents=data.get("max_concurrent_intents", 10),
            current_concurrent_intents=data.get("current_concurrent_intents", 0),
            metadata=data.get("metadata", {}),
        )
        
        # Parse stake info if present
        if data.get("stake_info"):
            stake_data = data["stake_info"]
            solver.stake_info = SolverStakeInfo(
                stake_amount=Decimal(stake_data["stake_amount"]),
                stake_token=stake_data["stake_token"],
                stake_timestamp=datetime.fromisoformat(stake_data["stake_timestamp"]),
                minimum_stake_required=Decimal(stake_data["minimum_stake_required"]),
                locked_until=datetime.fromisoformat(stake_data["locked_until"]) if stake_data.get("locked_until") else None,
                slashed_amount=Decimal(stake_data.get("slashed_amount", "0")),
            )
        
        # Parse performance metrics
        if data.get("performance_metrics"):
            perf_data = data["performance_metrics"]
            solver.performance_metrics = SolverPerformanceMetrics(
                total_intents_received=perf_data.get("total_intents_received", 0),
                total_bids_submitted=perf_data.get("total_bids_submitted", 0),
                total_intents_won=perf_data.get("total_intents_won", 0),
                total_intents_completed=perf_data.get("total_intents_completed", 0),
                total_intents_failed=perf_data.get("total_intents_failed", 0),
                total_volume_processed=Decimal(perf_data.get("total_volume_processed", "0")),
                average_execution_time=perf_data.get("average_execution_time", 0.0),
                average_slippage=perf_data.get("average_slippage", 0.0),
                last_activity=datetime.fromisoformat(perf_data["last_activity"]) if perf_data.get("last_activity") else None,
            )
        
        # Parse reputation score
        if data.get("reputation_score"):
            rep_data = data["reputation_score"]
            solver.reputation_score = SolverReputationScore(
                base_score=rep_data.get("base_score", 1.0),
                completion_bonus=rep_data.get("completion_bonus", 0.0),
                speed_bonus=rep_data.get("speed_bonus", 0.0),
                volume_bonus=rep_data.get("volume_bonus", 0.0),
                reliability_penalty=rep_data.get("reliability_penalty", 0.0),
                slashing_penalty=rep_data.get("slashing_penalty", 0.0),
                last_updated=datetime.fromisoformat(rep_data["last_updated"]),
            )
        
        return solver