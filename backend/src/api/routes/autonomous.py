"""
Autonomous Execution API Routes - Phase 3
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from datetime import datetime

router = APIRouter(prefix="/autonomous", tags=["Autonomous Execution"])


class IntentSubmission(BaseModel):
    intent_id: str
    user_address: str
    source_chain: str
    dest_chain: str
    input_token: str
    output_token: str
    input_amount: float
    min_output_amount: float
    max_slippage: float
    deadline_minutes: int = 30
    mev_protection: bool = True
    preferred_solvers: Optional[List[str]] = None
    blocked_solvers: Optional[List[str]] = None
    max_gas_price: Optional[float] = None


class MarketChangeNotification(BaseModel):
    change_type: str
    details: Dict[str, Any]


@router.post("/submit")
async def submit_intent(request: IntentSubmission) -> Dict[str, Any]:
    """Submit intent for autonomous execution."""
    from ...execution import AutonomousEngine
    from ...execution.autonomous_engine import ExecutionConstraints
    from datetime import timedelta
    
    engine = AutonomousEngine()
    
    intent = {
        "intent_id": request.intent_id,
        "user_address": request.user_address,
        "source_chain": request.source_chain,
        "dest_chain": request.dest_chain,
        "input_token": request.input_token,
        "output_token": request.output_token,
        "input_amount": request.input_amount,
        "expected_price": 1.0  # Would be fetched
    }
    
    constraints = ExecutionConstraints(
        max_slippage=request.max_slippage,
        deadline=datetime.utcnow() + timedelta(minutes=request.deadline_minutes),
        minimum_output=request.min_output_amount,
        preferred_solvers=request.preferred_solvers,
        blocked_solvers=request.blocked_solvers,
        max_gas_price=request.max_gas_price,
        mev_protection_required=request.mev_protection
    )
    
    result = await engine.submit_intent(intent, constraints)
    
    return result


@router.get("/status/{intent_id}")
async def get_execution_status(intent_id: str) -> Dict[str, Any]:
    """Get execution status for an intent."""
    from ...execution import AutonomousEngine
    
    engine = AutonomousEngine()
    status = await engine.monitor_execution(intent_id)
    
    if "error" in status:
        raise HTTPException(404, status["error"])
    
    return status


@router.post("/adapt/{intent_id}")
async def adapt_strategy(
    intent_id: str,
    notification: MarketChangeNotification
) -> Dict[str, Any]:
    """Notify of market change to trigger strategy adaptation."""
    from ...execution import AutonomousEngine
    
    engine = AutonomousEngine()
    
    adaptation = await engine.adapt_strategy(intent_id, {
        "type": notification.change_type,
        **notification.details
    })
    
    if not adaptation:
        return {"adapted": False, "message": "No adaptation needed"}
    
    return {
        "adapted": True,
        "adaptation_id": adaptation.adaptation_id,
        "trigger": adaptation.trigger,
        "reason": adaptation.reason,
        "new_strategy": adaptation.new_strategy
    }


@router.get("/report/{intent_id}")
async def get_execution_report(intent_id: str) -> Dict[str, Any]:
    """Get detailed execution report."""
    from ...execution import AutonomousEngine
    
    engine = AutonomousEngine()
    
    if intent_id not in engine.execution_history:
        raise HTTPException(404, "Report not found")
    
    report = engine.execution_history[intent_id]
    
    return {
        "intent_id": report.intent_id,
        "execution_id": report.execution_id,
        "start_time": report.start_time.isoformat(),
        "end_time": report.end_time.isoformat(),
        "decisions_count": len(report.decisions_made),
        "adaptations_count": len(report.strategy_adaptations),
        "outcome": {
            "success": report.final_outcome.success,
            "output_amount": report.final_outcome.output_amount,
            "execution_price": report.final_outcome.execution_price,
            "gas_cost": report.final_outcome.gas_cost,
            "mev_savings": report.final_outcome.mev_savings,
            "total_time_ms": report.final_outcome.total_time_ms,
            "solver_used": report.final_outcome.solver_used
        },
        "constraints_met": report.constraints_met
    }


@router.delete("/cancel/{intent_id}")
async def cancel_intent(intent_id: str) -> Dict[str, Any]:
    """Cancel an active intent."""
    from ...execution import AutonomousEngine
    
    engine = AutonomousEngine()
    success = await engine.cancel_intent(intent_id)
    
    if not success:
        raise HTTPException(404, "Intent not found or already completed")
    
    return {"cancelled": True, "intent_id": intent_id}


@router.get("/decisions/{intent_id}")
async def get_decisions(intent_id: str) -> List[Dict[str, Any]]:
    """Get all decisions made for an intent."""
    from ...execution import AutonomousEngine
    
    engine = AutonomousEngine()
    decisions = engine.decisions.get(intent_id, [])
    
    return [
        {
            "decision_id": d.decision_id,
            "type": d.decision_type.value,
            "timestamp": d.timestamp.isoformat(),
            "rationale": d.rationale,
            "parameters": d.parameters
        }
        for d in decisions
    ]
