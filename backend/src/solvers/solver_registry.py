"""
Solver Registry - Third-Party Solver Management
Phase 3: Autonomy & MEV Protection

Manages registration, verification, and lifecycle of third-party solvers.
"""

import hashlib
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
import logging

logger = logging.getLogger(__name__)


class SolverStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    BANNED = "banned"


@dataclass
class SolverCapabilities:
    supported_chains: List[str]
    supported_tokens: List[str]
    max_volume_per_trade: float
    min_volume_per_trade: float
    supported_intent_types: List[str]
    average_execution_time_ms: int = 1000


@dataclass
class SolverInfo:
    solver_id: str
    name: str
    registration_date: datetime
    status: SolverStatus
    capabilities: SolverCapabilities
    reputation_score: float
    total_volume: float
    fulfillment_rate: float
    average_execution_time: float
    stake_amount: float
    wallet_address: str
    api_endpoint: str
    last_active: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SolverApplication:
    name: str
    wallet_address: str
    api_endpoint: str
    capabilities: SolverCapabilities
    stake_amount: float
    contact_email: str
    company_name: Optional[str] = None


@dataclass
class RegistrationResult:
    success: bool
    solver_id: Optional[str]
    message: str
    requirements_met: Dict[str, bool]


@dataclass
class SolverFilters:
    chains: Optional[List[str]] = None
    min_reputation: Optional[float] = None
    min_volume: Optional[float] = None
    status: Optional[SolverStatus] = None


@dataclass
class NetworkStatistics:
    total_solvers: int
    active_solvers: int
    total_volume_24h: float
    total_intents_fulfilled_24h: int
    average_fulfillment_rate: float
    average_execution_time_ms: float


class SolverRegistry:
    """
    Solver Registry manages third-party solver registration and lifecycle.
    
    Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5
    """
    
    # Minimum requirements for solver registration
    MIN_STAKE_AMOUNT = 1000.0  # Minimum stake in USD
    MIN_FULFILLMENT_RATE = 0.95  # 95% minimum fulfillment rate
    
    def __init__(self):
        self.solvers: Dict[str, SolverInfo] = {}
        self.pending_applications: Dict[str, SolverApplication] = {}
        self.suspension_history: Dict[str, List[Dict]] = {}

    async def register_solver(
        self,
        application: SolverApplication
    ) -> RegistrationResult:
        """
        Register a new solver with verification.
        
        Property 10: Solver Registration Process
        For any market maker application, provides clear registration process.
        """
        requirements = self._check_requirements(application)
        
        if not all(requirements.values()):
            return RegistrationResult(
                success=False,
                solver_id=None,
                message="Registration requirements not met",
                requirements_met=requirements
            )
        
        solver_id = self._generate_solver_id(application)
        
        solver = SolverInfo(
            solver_id=solver_id,
            name=application.name,
            registration_date=datetime.utcnow(),
            status=SolverStatus.ACTIVE,
            capabilities=application.capabilities,
            reputation_score=0.5,  # Start with neutral reputation
            total_volume=0.0,
            fulfillment_rate=1.0,
            average_execution_time=application.capabilities.average_execution_time_ms,
            stake_amount=application.stake_amount,
            wallet_address=application.wallet_address,
            api_endpoint=application.api_endpoint
        )
        
        self.solvers[solver_id] = solver
        logger.info(f"Registered new solver: {solver_id} ({application.name})")
        
        return RegistrationResult(
            success=True,
            solver_id=solver_id,
            message="Solver registered successfully",
            requirements_met=requirements
        )
    
    def _check_requirements(self, app: SolverApplication) -> Dict[str, bool]:
        """Check if application meets requirements."""
        return {
            "stake_amount": app.stake_amount >= self.MIN_STAKE_AMOUNT,
            "valid_wallet": len(app.wallet_address) == 42,
            "valid_endpoint": app.api_endpoint.startswith("https://"),
            "has_capabilities": len(app.capabilities.supported_chains) > 0,
            "contact_provided": "@" in app.contact_email
        }
    
    async def get_solver_info(self, solver_id: str) -> Optional[SolverInfo]:
        """
        Get solver information.
        
        Property 11: Public Solver Registry
        For any registered solver, provides public information.
        """
        return self.solvers.get(solver_id)

    async def list_active_solvers(
        self,
        filters: Optional[SolverFilters] = None
    ) -> List[SolverInfo]:
        """
        List active solvers with optional filtering.
        
        Property 12: Open Bid Submission
        For any broadcast intent, all registered solvers can participate.
        """
        solvers = list(self.solvers.values())
        
        if filters:
            if filters.status:
                solvers = [s for s in solvers if s.status == filters.status]
            else:
                solvers = [s for s in solvers if s.status == SolverStatus.ACTIVE]
            
            if filters.chains:
                solvers = [
                    s for s in solvers
                    if any(c in s.capabilities.supported_chains for c in filters.chains)
                ]
            
            if filters.min_reputation:
                solvers = [s for s in solvers if s.reputation_score >= filters.min_reputation]
            
            if filters.min_volume:
                solvers = [s for s in solvers if s.total_volume >= filters.min_volume]
        else:
            solvers = [s for s in solvers if s.status == SolverStatus.ACTIVE]
        
        return solvers
    
    async def update_solver_capabilities(
        self,
        solver_id: str,
        capabilities: SolverCapabilities
    ) -> bool:
        """Update solver capabilities."""
        solver = self.solvers.get(solver_id)
        if not solver:
            return False
        
        solver.capabilities = capabilities
        solver.last_active = datetime.utcnow()
        return True
    
    async def suspend_solver(
        self,
        solver_id: str,
        reason: str
    ) -> Dict[str, Any]:
        """
        Suspend a solver for violations.
        
        Property 14: Performance Standards Enforcement
        For any solver failing standards, triggers automatic suspension.
        """
        solver = self.solvers.get(solver_id)
        if not solver:
            return {"success": False, "message": "Solver not found"}
        
        solver.status = SolverStatus.SUSPENDED
        
        if solver_id not in self.suspension_history:
            self.suspension_history[solver_id] = []
        
        self.suspension_history[solver_id].append({
            "timestamp": datetime.utcnow(),
            "reason": reason,
            "previous_status": SolverStatus.ACTIVE.value
        })
        
        logger.warning(f"Suspended solver {solver_id}: {reason}")
        
        return {
            "success": True,
            "message": f"Solver suspended: {reason}",
            "suspension_count": len(self.suspension_history[solver_id])
        }

    async def check_performance_standards(
        self,
        solver_id: str
    ) -> Dict[str, Any]:
        """Check if solver meets minimum performance standards."""
        solver = self.solvers.get(solver_id)
        if not solver:
            return {"meets_standards": False, "reason": "Solver not found"}
        
        issues = []
        
        if solver.fulfillment_rate < self.MIN_FULFILLMENT_RATE:
            issues.append(f"Fulfillment rate {solver.fulfillment_rate:.2%} below minimum {self.MIN_FULFILLMENT_RATE:.2%}")
        
        if solver.stake_amount < self.MIN_STAKE_AMOUNT:
            issues.append(f"Stake amount ${solver.stake_amount} below minimum ${self.MIN_STAKE_AMOUNT}")
        
        if issues:
            return {
                "meets_standards": False,
                "issues": issues,
                "action_required": "suspend" if len(issues) > 1 else "warning"
            }
        
        return {"meets_standards": True, "issues": []}
    
    async def get_network_statistics(self) -> NetworkStatistics:
        """
        Get aggregate network statistics.
        
        Property 24: Network Statistics Publication
        For any reporting period, publishes aggregate statistics.
        """
        active = [s for s in self.solvers.values() if s.status == SolverStatus.ACTIVE]
        
        total_volume = sum(s.total_volume for s in active)
        avg_fulfillment = sum(s.fulfillment_rate for s in active) / max(len(active), 1)
        avg_execution = sum(s.average_execution_time for s in active) / max(len(active), 1)
        
        return NetworkStatistics(
            total_solvers=len(self.solvers),
            active_solvers=len(active),
            total_volume_24h=total_volume * 0.1,  # Estimate 24h as 10% of total
            total_intents_fulfilled_24h=int(len(active) * 50),  # Estimate
            average_fulfillment_rate=avg_fulfillment,
            average_execution_time_ms=avg_execution
        )
    
    async def reinstate_solver(self, solver_id: str) -> bool:
        """Reinstate a suspended solver."""
        solver = self.solvers.get(solver_id)
        if not solver or solver.status != SolverStatus.SUSPENDED:
            return False
        
        solver.status = SolverStatus.ACTIVE
        solver.last_active = datetime.utcnow()
        return True
    
    def _generate_solver_id(self, app: SolverApplication) -> str:
        """Generate unique solver ID."""
        data = f"{app.wallet_address}{app.name}{time.time()}"
        return f"solver_{hashlib.sha256(data.encode()).hexdigest()[:12]}"
    
    def get_solvers_for_intent(
        self,
        chains: List[str],
        tokens: List[str],
        volume: float
    ) -> List[SolverInfo]:
        """Get solvers capable of fulfilling an intent."""
        eligible = []
        for solver in self.solvers.values():
            if solver.status != SolverStatus.ACTIVE:
                continue
            
            caps = solver.capabilities
            chain_match = any(c in caps.supported_chains for c in chains)
            token_match = any(t in caps.supported_tokens for t in tokens)
            volume_ok = caps.min_volume_per_trade <= volume <= caps.max_volume_per_trade
            
            if chain_match and token_match and volume_ok:
                eligible.append(solver)
        
        return eligible
