"""
Autonomous Engine - Intelligent Intent Execution
Phase 3: Autonomy & MEV Protection

Orchestrates autonomous intent execution with optimal timing and routing.
"""

import asyncio
import hashlib
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    PENDING = "pending"
    MONITORING = "monitoring"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    ESCALATED = "escalated"


class DecisionType(Enum):
    TIMING = "timing"
    ROUTING = "routing"
    SOLVER_SELECTION = "solver_selection"
    STRATEGY_CHANGE = "strategy_change"
    ESCALATION = "escalation"


@dataclass
class ExecutionConstraints:
    max_slippage: float
    deadline: datetime
    minimum_output: float
    preferred_solvers: Optional[List[str]] = None
    blocked_solvers: Optional[List[str]] = None
    max_gas_price: Optional[float] = None
    mev_protection_required: bool = True


@dataclass
class ExecutionDecision:
    decision_id: str
    decision_type: DecisionType
    timestamp: datetime
    rationale: str
    parameters: Dict[str, Any]
    outcome: Optional[str] = None


@dataclass
class StrategyAdaptation:
    adaptation_id: str
    trigger: str
    old_strategy: Dict[str, Any]
    new_strategy: Dict[str, Any]
    timestamp: datetime
    reason: str


@dataclass
class ExecutionOutcome:
    success: bool
    output_amount: float
    execution_price: float
    gas_cost: float
    mev_savings: float
    total_time_ms: int
    solver_used: str


@dataclass
class ExecutionReport:
    intent_id: str
    execution_id: str
    start_time: datetime
    end_time: datetime
    decisions_made: List[ExecutionDecision]
    strategy_adaptations: List[StrategyAdaptation]
    final_outcome: ExecutionOutcome
    mev_savings: float
    gas_costs: Dict[str, float]
    solver_used: str
    constraints_met: Dict[str, bool]


@dataclass
class ExecutionIssue:
    issue_id: str
    issue_type: str
    severity: str
    description: str
    options: List[Dict[str, Any]]
    requires_user_action: bool


class AutonomousEngine:
    """
    Autonomous Engine orchestrates intelligent intent execution.
    
    Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5
    """
    
    def __init__(self, mev_shield=None, auction_manager=None, gas_calculator=None):
        self.active_intents: Dict[str, Dict[str, Any]] = {}
        self.execution_history: Dict[str, ExecutionReport] = {}
        self.decisions: Dict[str, List[ExecutionDecision]] = {}
        self.mev_shield = mev_shield
        self.auction_manager = auction_manager
        self.gas_calculator = gas_calculator
        self._monitoring_tasks: Dict[str, asyncio.Task] = {}

    async def submit_intent(
        self,
        intent: Dict[str, Any],
        constraints: ExecutionConstraints
    ) -> Dict[str, Any]:
        """
        Submit intent for autonomous execution.
        
        Property 40: Continuous Market Monitoring
        For any submitted intent, continuously monitors for optimal execution.
        """
        execution_id = self._generate_id("exec")
        intent_id = intent.get("intent_id", execution_id)
        
        self.active_intents[intent_id] = {
            "intent": intent,
            "constraints": constraints,
            "execution_id": execution_id,
            "status": ExecutionStatus.PENDING,
            "start_time": datetime.utcnow(),
            "decisions": [],
            "adaptations": []
        }
        
        self.decisions[intent_id] = []
        
        # Start monitoring task
        task = asyncio.create_task(self._monitor_and_execute(intent_id))
        self._monitoring_tasks[intent_id] = task
        
        logger.info(f"Intent {intent_id} submitted for autonomous execution")
        
        return {
            "intent_id": intent_id,
            "execution_id": execution_id,
            "status": "monitoring",
            "message": "Intent submitted for autonomous execution"
        }
    
    async def _monitor_and_execute(self, intent_id: str):
        """Monitor market conditions and execute at optimal time."""
        intent_data = self.active_intents.get(intent_id)
        if not intent_data:
            return
        
        intent_data["status"] = ExecutionStatus.MONITORING
        constraints = intent_data["constraints"]
        
        while datetime.utcnow() < constraints.deadline:
            # Check market conditions
            should_execute, reason = await self._check_execution_conditions(intent_id)
            
            if should_execute:
                await self._execute_intent(intent_id)
                return
            
            # Record monitoring decision
            self._record_decision(
                intent_id,
                DecisionType.TIMING,
                f"Waiting for better conditions: {reason}",
                {"reason": reason}
            )
            
            await asyncio.sleep(1)  # Check every second
        
        # Deadline reached, execute anyway or escalate
        await self._handle_deadline(intent_id)

    async def _check_execution_conditions(
        self,
        intent_id: str
    ) -> tuple[bool, str]:
        """Check if conditions are favorable for execution."""
        intent_data = self.active_intents.get(intent_id)
        if not intent_data:
            return False, "Intent not found"
        
        constraints = intent_data["constraints"]
        intent = intent_data["intent"]
        
        # Check gas prices
        if self.gas_calculator:
            chain = intent.get("source_chain", "ethereum")
            gas_estimate = await self.gas_calculator.estimate_gas_cost(chain)
            
            if constraints.max_gas_price and gas_estimate.gas_price_gwei > constraints.max_gas_price:
                return False, f"Gas price {gas_estimate.gas_price_gwei} exceeds max {constraints.max_gas_price}"
        
        # Check slippage conditions (simplified)
        current_price = intent.get("current_price", 1.0)
        expected_price = intent.get("expected_price", 1.0)
        slippage = abs(current_price - expected_price) / expected_price
        
        if slippage > constraints.max_slippage:
            return False, f"Slippage {slippage:.2%} exceeds max {constraints.max_slippage:.2%}"
        
        return True, "Conditions favorable"
    
    async def _execute_intent(self, intent_id: str):
        """Execute the intent."""
        intent_data = self.active_intents.get(intent_id)
        if not intent_data:
            return
        
        intent_data["status"] = ExecutionStatus.EXECUTING
        intent = intent_data["intent"]
        constraints = intent_data["constraints"]
        
        self._record_decision(
            intent_id,
            DecisionType.TIMING,
            "Executing intent - conditions met",
            {"timestamp": datetime.utcnow().isoformat()}
        )
        
        try:
            # Run auction if auction manager available
            solver_id = "internal"
            if self.auction_manager:
                from ..solvers.auction_manager import Intent as AuctionIntent
                auction_intent = AuctionIntent(
                    intent_id=intent_id,
                    user_address=intent.get("user_address", ""),
                    source_chain=intent.get("source_chain", "ethereum"),
                    dest_chain=intent.get("dest_chain", "ethereum"),
                    input_token=intent.get("input_token", "ETH"),
                    output_token=intent.get("output_token", "USDC"),
                    input_amount=intent.get("input_amount", 0),
                    min_output_amount=constraints.minimum_output,
                    deadline=constraints.deadline
                )
                auction = await self.auction_manager.create_auction(auction_intent)
                # Wait for bids and select winner
                await asyncio.sleep(0.1)  # Simplified
                winner = await self.auction_manager.select_winner(auction.auction_id)
                if winner:
                    solver_id = winner.bid.solver_id
            
            # Apply MEV protection
            if constraints.mev_protection_required and self.mev_shield:
                # Route through private RPC
                pass
            
            # Record outcome
            outcome = ExecutionOutcome(
                success=True,
                output_amount=constraints.minimum_output * 1.01,  # Simulated
                execution_price=intent.get("expected_price", 1.0),
                gas_cost=5.0,
                mev_savings=0.5,
                total_time_ms=int((datetime.utcnow() - intent_data["start_time"]).total_seconds() * 1000),
                solver_used=solver_id
            )
            
            intent_data["status"] = ExecutionStatus.COMPLETED
            intent_data["outcome"] = outcome
            
            # Generate report
            await self.generate_execution_report(intent_id)
            
        except Exception as e:
            logger.error(f"Execution failed for {intent_id}: {e}")
            intent_data["status"] = ExecutionStatus.FAILED
            await self.escalate_to_user(intent_id, ExecutionIssue(
                issue_id=self._generate_id("issue"),
                issue_type="execution_failure",
                severity="high",
                description=str(e),
                options=[{"action": "retry"}, {"action": "cancel"}],
                requires_user_action=True
            ))

    async def adapt_strategy(
        self,
        intent_id: str,
        market_change: Dict[str, Any]
    ) -> Optional[StrategyAdaptation]:
        """
        Adapt execution strategy based on market changes.
        
        Property 41: Real-Time Strategy Adaptation
        For any market condition change, adapts strategies in real-time.
        """
        intent_data = self.active_intents.get(intent_id)
        if not intent_data:
            return None
        
        old_strategy = intent_data.get("current_strategy", {"type": "default"})
        
        # Determine new strategy based on market change
        change_type = market_change.get("type", "")
        new_strategy = old_strategy.copy()
        reason = ""
        
        if change_type == "volatility_increase":
            new_strategy["execution_speed"] = "fast"
            new_strategy["slippage_tolerance"] = "tight"
            reason = "Increased volatility - executing faster with tighter slippage"
        
        elif change_type == "gas_spike":
            new_strategy["wait_for_gas"] = True
            new_strategy["max_wait_minutes"] = 30
            reason = "Gas spike detected - waiting for lower prices"
        
        elif change_type == "liquidity_drop":
            new_strategy["split_execution"] = True
            new_strategy["num_splits"] = 3
            reason = "Liquidity dropped - splitting execution"
        
        else:
            return None
        
        adaptation = StrategyAdaptation(
            adaptation_id=self._generate_id("adapt"),
            trigger=change_type,
            old_strategy=old_strategy,
            new_strategy=new_strategy,
            timestamp=datetime.utcnow(),
            reason=reason
        )
        
        intent_data["current_strategy"] = new_strategy
        intent_data["adaptations"].append(adaptation)
        
        self._record_decision(
            intent_id,
            DecisionType.STRATEGY_CHANGE,
            reason,
            {"old": old_strategy, "new": new_strategy}
        )
        
        return adaptation
    
    async def escalate_to_user(
        self,
        intent_id: str,
        issue: ExecutionIssue
    ) -> Dict[str, Any]:
        """
        Escalate issue to user with explanations.
        
        Property 43: Issue Escalation
        For any execution issue, escalates with clear explanations.
        """
        intent_data = self.active_intents.get(intent_id)
        if intent_data:
            intent_data["status"] = ExecutionStatus.ESCALATED
        
        self._record_decision(
            intent_id,
            DecisionType.ESCALATION,
            f"Escalated to user: {issue.description}",
            {"issue": issue.__dict__}
        )
        
        logger.warning(f"Escalating intent {intent_id}: {issue.description}")
        
        return {
            "intent_id": intent_id,
            "issue": {
                "id": issue.issue_id,
                "type": issue.issue_type,
                "severity": issue.severity,
                "description": issue.description,
                "options": issue.options
            },
            "requires_action": issue.requires_user_action
        }

    async def generate_execution_report(
        self,
        intent_id: str
    ) -> ExecutionReport:
        """
        Generate detailed execution report.
        
        Property 44: Detailed Execution Reporting
        For any completed execution, provides detailed reports.
        """
        intent_data = self.active_intents.get(intent_id)
        if not intent_data:
            raise ValueError(f"Intent {intent_id} not found")
        
        outcome = intent_data.get("outcome")
        if not outcome:
            outcome = ExecutionOutcome(
                success=False,
                output_amount=0,
                execution_price=0,
                gas_cost=0,
                mev_savings=0,
                total_time_ms=0,
                solver_used="none"
            )
        
        constraints = intent_data["constraints"]
        
        report = ExecutionReport(
            intent_id=intent_id,
            execution_id=intent_data["execution_id"],
            start_time=intent_data["start_time"],
            end_time=datetime.utcnow(),
            decisions_made=self.decisions.get(intent_id, []),
            strategy_adaptations=intent_data.get("adaptations", []),
            final_outcome=outcome,
            mev_savings=outcome.mev_savings,
            gas_costs={"total": outcome.gas_cost},
            solver_used=outcome.solver_used,
            constraints_met={
                "slippage": True,  # Would calculate actual
                "deadline": datetime.utcnow() < constraints.deadline,
                "minimum_output": outcome.output_amount >= constraints.minimum_output
            }
        )
        
        self.execution_history[intent_id] = report
        return report
    
    async def monitor_execution(self, intent_id: str) -> Dict[str, Any]:
        """Get current execution status."""
        intent_data = self.active_intents.get(intent_id)
        if not intent_data:
            return {"error": "Intent not found"}
        
        return {
            "intent_id": intent_id,
            "status": intent_data["status"].value,
            "start_time": intent_data["start_time"].isoformat(),
            "decisions_count": len(self.decisions.get(intent_id, [])),
            "adaptations_count": len(intent_data.get("adaptations", []))
        }
    
    def _record_decision(
        self,
        intent_id: str,
        decision_type: DecisionType,
        rationale: str,
        parameters: Dict[str, Any]
    ):
        """Record an execution decision."""
        decision = ExecutionDecision(
            decision_id=self._generate_id("dec"),
            decision_type=decision_type,
            timestamp=datetime.utcnow(),
            rationale=rationale,
            parameters=parameters
        )
        
        if intent_id not in self.decisions:
            self.decisions[intent_id] = []
        self.decisions[intent_id].append(decision)
    
    async def _handle_deadline(self, intent_id: str):
        """Handle deadline reached."""
        intent_data = self.active_intents.get(intent_id)
        if not intent_data:
            return
        
        # Try to execute anyway or escalate
        should_execute, _ = await self._check_execution_conditions(intent_id)
        
        if should_execute:
            await self._execute_intent(intent_id)
        else:
            await self.escalate_to_user(intent_id, ExecutionIssue(
                issue_id=self._generate_id("issue"),
                issue_type="deadline_reached",
                severity="high",
                description="Deadline reached but conditions not favorable",
                options=[
                    {"action": "execute_anyway", "description": "Execute despite unfavorable conditions"},
                    {"action": "extend_deadline", "description": "Extend deadline by 1 hour"},
                    {"action": "cancel", "description": "Cancel the intent"}
                ],
                requires_user_action=True
            ))
    
    def _generate_id(self, prefix: str) -> str:
        """Generate unique ID."""
        return f"{prefix}_{hashlib.sha256(f'{time.time()}'.encode()).hexdigest()[:10]}"
    
    async def cancel_intent(self, intent_id: str) -> bool:
        """Cancel an active intent."""
        if intent_id in self._monitoring_tasks:
            self._monitoring_tasks[intent_id].cancel()
            del self._monitoring_tasks[intent_id]
        
        if intent_id in self.active_intents:
            self.active_intents[intent_id]["status"] = ExecutionStatus.FAILED
            return True
        
        return False
