"""
Real-Time Decision Making System
High-performance decision engine for trading opportunities
"""
import asyncio
import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import uuid
import numpy as np

from ..config import AIConfig, AgentConfig, AgentType, get_agent_config
from ..utils.model_manager import ModelManager


class DecisionType(Enum):
    EXECUTE = "execute"
    HOLD = "hold"
    ESCALATE = "escalate"
    REJECT = "reject"


@dataclass
class Opportunity:
    opportunity_id: str
    asset: str
    chain: str
    expected_value: float
    risk_score: float
    time_sensitivity: float  # 0-1, higher = more urgent
    confidence: float
    timestamp: datetime


@dataclass
class Decision:
    decision_id: str
    opportunity_id: str
    decision_type: DecisionType
    rationale: str
    confidence: float
    latency_ms: float
    timestamp: datetime


@dataclass
class AuditTrail:
    trail_id: str
    decision_id: str
    inputs: Dict[str, Any]
    processing_steps: List[str]
    output: str
    timestamp: datetime


@dataclass
class EscalationRequest:
    escalation_id: str
    decision_id: str
    reason: str
    explanation: str
    urgency: str
    options: List[str]
    timestamp: datetime


class DecisionEngine:
    """High-performance decision making engine"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.decision_cache: Dict[str, Decision] = {}
    
    def make_decision(self, opportunity: Opportunity) -> Decision:
        """Make a decision on an opportunity"""
        start_time = time.time()
        
        # Decision logic
        ev_threshold = 0.05
        risk_threshold = 0.7
        
        if opportunity.expected_value > ev_threshold and opportunity.risk_score < risk_threshold:
            decision_type = DecisionType.EXECUTE
            rationale = f"Positive EV ({opportunity.expected_value:.2%}) with acceptable risk"
        elif opportunity.risk_score > 0.9:
            decision_type = DecisionType.REJECT
            rationale = f"Risk too high ({opportunity.risk_score:.2f})"
        elif opportunity.confidence < 0.5:
            decision_type = DecisionType.ESCALATE
            rationale = f"Low confidence ({opportunity.confidence:.2f}) - needs human review"
        else:
            decision_type = DecisionType.HOLD
            rationale = "Insufficient expected value"
        
        latency_ms = (time.time() - start_time) * 1000
        
        decision = Decision(
            decision_id=str(uuid.uuid4()),
            opportunity_id=opportunity.opportunity_id,
            decision_type=decision_type,
            rationale=rationale,
            confidence=opportunity.confidence,
            latency_ms=latency_ms,
            timestamp=datetime.now()
        )
        
        self.decision_cache[decision.decision_id] = decision
        return decision


class OpportunityPrioritizer:
    """Prioritizes opportunities by expected value and risk"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def prioritize(self, opportunities: List[Opportunity]) -> List[Opportunity]:
        """Prioritize opportunities by risk-adjusted expected value"""
        def score(opp: Opportunity) -> float:
            # Risk-adjusted score
            risk_adj = 1 - opp.risk_score
            time_adj = opp.time_sensitivity
            return opp.expected_value * risk_adj * opp.confidence * (1 + time_adj)
        
        return sorted(opportunities, key=score, reverse=True)


class StrategyAdapter:
    """Adapts strategies in real-time"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.current_strategy: Dict[str, Any] = {'mode': 'balanced'}
    
    def adapt_strategy(self, market_conditions: Dict[str, float]) -> Dict[str, Any]:
        """Adapt strategy based on conditions"""
        volatility = market_conditions.get('volatility', 0.02)
        trend = market_conditions.get('trend', 0)
        
        if volatility > 0.05:
            self.current_strategy = {'mode': 'defensive', 'risk_multiplier': 0.5}
        elif trend > 0.01:
            self.current_strategy = {'mode': 'aggressive', 'risk_multiplier': 1.2}
        else:
            self.current_strategy = {'mode': 'balanced', 'risk_multiplier': 1.0}
        
        return self.current_strategy


class AuditTrailManager:
    """Manages decision audit trails"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.trails: List[AuditTrail] = []
    
    def create_trail(self, decision: Decision, inputs: Dict[str, Any],
                    steps: List[str]) -> AuditTrail:
        """Create audit trail for decision"""
        trail = AuditTrail(
            trail_id=str(uuid.uuid4()),
            decision_id=decision.decision_id,
            inputs=inputs,
            processing_steps=steps,
            output=decision.decision_type.value,
            timestamp=datetime.now()
        )
        self.trails.append(trail)
        return trail
    
    def get_trail(self, decision_id: str) -> Optional[AuditTrail]:
        """Get trail for decision"""
        for trail in self.trails:
            if trail.decision_id == decision_id:
                return trail
        return None


class EscalationManager:
    """Manages human escalation"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.escalations: List[EscalationRequest] = []
    
    def create_escalation(self, decision: Decision, reason: str) -> EscalationRequest:
        """Create escalation request"""
        explanation = self._generate_explanation(decision, reason)
        
        escalation = EscalationRequest(
            escalation_id=str(uuid.uuid4()),
            decision_id=decision.decision_id,
            reason=reason,
            explanation=explanation,
            urgency="high" if decision.confidence < 0.3 else "medium",
            options=["approve", "reject", "modify"],
            timestamp=datetime.now()
        )
        self.escalations.append(escalation)
        return escalation
    
    def _generate_explanation(self, decision: Decision, reason: str) -> str:
        """Generate human-readable explanation"""
        return f"Decision {decision.decision_id} requires review. Reason: {reason}. " \
               f"Original recommendation: {decision.decision_type.value}. " \
               f"Confidence: {decision.confidence:.1%}. Rationale: {decision.rationale}"


class RealTimeDecisionSystem:
    """Main real-time decision making system"""
    
    def __init__(self, config: AIConfig, agent_config: AgentConfig, model_manager: ModelManager):
        self.config = config
        self.agent_config = agent_config
        self.model_manager = model_manager
        self.logger = logging.getLogger(__name__)
        
        self.decision_engine = DecisionEngine()
        self.prioritizer = OpportunityPrioritizer()
        self.adapter = StrategyAdapter()
        self.audit_manager = AuditTrailManager()
        self.escalation_manager = EscalationManager()
        
        self.decision_history: List[Decision] = []
        self.logger.info("Real-Time Decision System initialized")
    
    async def make_millisecond_decision(self, opportunity: Opportunity) -> Decision:
        """Make decision within milliseconds - Requirements: 9.1"""
        decision = self.decision_engine.make_decision(opportunity)
        
        # Create audit trail
        self.audit_manager.create_trail(
            decision,
            {'opportunity': opportunity.__dict__},
            ['validate_input', 'calculate_ev', 'assess_risk', 'make_decision']
        )
        
        self.decision_history.append(decision)
        return decision
    
    async def prioritize_opportunities(self, 
                                       opportunities: List[Opportunity]) -> List[Opportunity]:
        """Prioritize opportunities - Requirements: 9.2"""
        return self.prioritizer.prioritize(opportunities)
    
    async def adapt_strategy_realtime(self, 
                                      market_conditions: Dict[str, float]) -> Dict[str, Any]:
        """Adapt strategy in real-time - Requirements: 9.3"""
        return self.adapter.adapt_strategy(market_conditions)
    
    async def get_decision_audit_trail(self, decision_id: str) -> Optional[AuditTrail]:
        """Get audit trail for decision - Requirements: 9.4"""
        return self.audit_manager.get_trail(decision_id)
    
    async def escalate_to_human(self, decision: Decision, reason: str) -> EscalationRequest:
        """Escalate decision to human - Requirements: 9.5"""
        return self.escalation_manager.create_escalation(decision, reason)
