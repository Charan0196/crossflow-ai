"""
Slashing Module - Solver Accountability
Phase 3: Autonomy & MEV Protection

Enforces penalties for solver misbehavior and failed commitments.
"""

import hashlib
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class ViolationType(Enum):
    FAILED_FULFILLMENT = "failed_fulfillment"
    WORSE_THAN_PROMISED = "worse_than_promised"
    TIMEOUT = "timeout"
    INVALID_EXECUTION = "invalid_execution"
    REPEATED_FAILURES = "repeated_failures"


class Severity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AppealStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class Violation:
    violation_id: str
    solver_id: str
    violation_type: ViolationType
    severity: Severity
    auction_id: str
    evidence: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SlashingPenalty:
    penalty_id: str
    solver_id: str
    violation: Violation
    penalty_amount: float
    penalty_percentage: float
    description: str


@dataclass
class SlashingResult:
    success: bool
    penalty_id: str
    amount_slashed: float
    new_stake: float
    message: str


@dataclass
class SlashingAppeal:
    appeal_id: str
    slashing_id: str
    solver_id: str
    reason: str
    evidence: Dict[str, Any]
    submitted_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AppealResult:
    appeal_id: str
    status: AppealStatus
    decision_reason: str
    refund_amount: float


@dataclass
class SlashingEvent:
    slashing_id: str
    solver_id: str
    violation_type: ViolationType
    severity: Severity
    penalty_amount: float
    evidence: Dict[str, Any]
    appeal_status: Optional[AppealStatus]
    timestamp: datetime


class SlashingModule:
    """
    Slashing Module enforces penalties for solver violations.
    
    Validates: Requirements 4.5, 5.5
    """
    
    # Penalty percentages by severity
    PENALTY_RATES = {
        Severity.LOW: 0.01,      # 1% of stake
        Severity.MEDIUM: 0.05,   # 5% of stake
        Severity.HIGH: 0.15,     # 15% of stake
        Severity.CRITICAL: 0.50  # 50% of stake
    }
    
    def __init__(self, solver_registry=None):
        self.violations: Dict[str, Violation] = {}
        self.slashing_events: Dict[str, SlashingEvent] = {}
        self.appeals: Dict[str, SlashingAppeal] = {}
        self.solver_stakes: Dict[str, float] = {}  # solver_id -> stake amount
        self.solver_registry = solver_registry

    async def detect_violation(
        self,
        solver_id: str,
        auction_id: str,
        commitment: Dict[str, Any],
        actual_result: Dict[str, Any]
    ) -> Optional[Violation]:
        """
        Detect violations from fulfillment results.
        
        Property 19: Slashing Mechanism Enforcement
        For any solver failing to fulfill or providing worse outcomes, applies slashing.
        """
        violation_type = None
        severity = Severity.LOW
        evidence = {
            "commitment": commitment,
            "actual_result": actual_result
        }
        
        # Check for failed fulfillment
        if not actual_result.get("success", False):
            violation_type = ViolationType.FAILED_FULFILLMENT
            severity = Severity.MEDIUM
        
        # Check for worse than promised output
        elif actual_result.get("output_amount", 0) < commitment.get("offered_output", 0) * 0.99:
            violation_type = ViolationType.WORSE_THAN_PROMISED
            severity = Severity.HIGH
            evidence["shortfall"] = commitment.get("offered_output", 0) - actual_result.get("output_amount", 0)
        
        # Check for timeout
        elif actual_result.get("execution_time_ms", 0) > commitment.get("execution_time_estimate", 0) * 2:
            violation_type = ViolationType.TIMEOUT
            severity = Severity.LOW
        
        if violation_type:
            violation = Violation(
                violation_id=self._generate_id("viol"),
                solver_id=solver_id,
                violation_type=violation_type,
                severity=severity,
                auction_id=auction_id,
                evidence=evidence
            )
            self.violations[violation.violation_id] = violation
            logger.warning(f"Violation detected: {violation_type.value} by {solver_id}")
            return violation
        
        return None
    
    async def calculate_penalty(self, violation: Violation) -> SlashingPenalty:
        """Calculate penalty for a violation."""
        stake = self.solver_stakes.get(violation.solver_id, 1000.0)
        penalty_rate = self.PENALTY_RATES.get(violation.severity, 0.01)
        penalty_amount = stake * penalty_rate
        
        return SlashingPenalty(
            penalty_id=self._generate_id("pen"),
            solver_id=violation.solver_id,
            violation=violation,
            penalty_amount=penalty_amount,
            penalty_percentage=penalty_rate * 100,
            description=f"{violation.violation_type.value} - {violation.severity.value} severity"
        )

    async def execute_slashing(
        self,
        solver_id: str,
        penalty: SlashingPenalty
    ) -> SlashingResult:
        """Execute slashing penalty on solver stake."""
        current_stake = self.solver_stakes.get(solver_id, 0)
        
        if current_stake < penalty.penalty_amount:
            # Slash entire remaining stake
            slashed = current_stake
            self.solver_stakes[solver_id] = 0
        else:
            slashed = penalty.penalty_amount
            self.solver_stakes[solver_id] = current_stake - slashed
        
        # Record slashing event
        event = SlashingEvent(
            slashing_id=self._generate_id("slash"),
            solver_id=solver_id,
            violation_type=penalty.violation.violation_type,
            severity=penalty.violation.severity,
            penalty_amount=slashed,
            evidence=penalty.violation.evidence,
            appeal_status=None,
            timestamp=datetime.utcnow()
        )
        self.slashing_events[event.slashing_id] = event
        
        logger.info(f"Slashed {slashed} from {solver_id}, new stake: {self.solver_stakes[solver_id]}")
        
        return SlashingResult(
            success=True,
            penalty_id=penalty.penalty_id,
            amount_slashed=slashed,
            new_stake=self.solver_stakes[solver_id],
            message=f"Slashed {slashed} for {penalty.violation.violation_type.value}"
        )
    
    async def submit_appeal(
        self,
        slashing_id: str,
        solver_id: str,
        reason: str,
        evidence: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Submit appeal for a slashing event."""
        event = self.slashing_events.get(slashing_id)
        if not event:
            return {"success": False, "message": "Slashing event not found"}
        
        if event.solver_id != solver_id:
            return {"success": False, "message": "Not authorized to appeal"}
        
        appeal = SlashingAppeal(
            appeal_id=self._generate_id("appeal"),
            slashing_id=slashing_id,
            solver_id=solver_id,
            reason=reason,
            evidence=evidence
        )
        
        self.appeals[appeal.appeal_id] = appeal
        event.appeal_status = AppealStatus.PENDING
        
        return {"success": True, "appeal_id": appeal.appeal_id}
    
    async def process_appeal(
        self,
        appeal_id: str,
        approved: bool,
        decision_reason: str
    ) -> AppealResult:
        """Process a slashing appeal."""
        appeal = self.appeals.get(appeal_id)
        if not appeal:
            raise ValueError(f"Appeal {appeal_id} not found")
        
        event = self.slashing_events.get(appeal.slashing_id)
        refund = 0.0
        
        if approved:
            event.appeal_status = AppealStatus.APPROVED
            # Refund the slashed amount
            refund = event.penalty_amount
            self.solver_stakes[appeal.solver_id] = self.solver_stakes.get(appeal.solver_id, 0) + refund
        else:
            event.appeal_status = AppealStatus.REJECTED
        
        return AppealResult(
            appeal_id=appeal_id,
            status=event.appeal_status,
            decision_reason=decision_reason,
            refund_amount=refund
        )

    async def get_slashing_history(
        self,
        solver_id: str
    ) -> List[SlashingEvent]:
        """Get slashing history for a solver."""
        return [
            event for event in self.slashing_events.values()
            if event.solver_id == solver_id
        ]
    
    def set_solver_stake(self, solver_id: str, amount: float):
        """Set solver stake amount."""
        self.solver_stakes[solver_id] = amount
    
    def get_solver_stake(self, solver_id: str) -> float:
        """Get current solver stake."""
        return self.solver_stakes.get(solver_id, 0)
    
    async def check_repeated_violations(
        self,
        solver_id: str,
        window_days: int = 7
    ) -> bool:
        """Check if solver has repeated violations."""
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=window_days)
        
        recent_violations = [
            v for v in self.violations.values()
            if v.solver_id == solver_id and v.timestamp >= cutoff
        ]
        
        return len(recent_violations) >= 3
    
    def _generate_id(self, prefix: str) -> str:
        """Generate unique ID."""
        return f"{prefix}_{hashlib.sha256(f'{time.time()}'.encode()).hexdigest()[:10]}"
