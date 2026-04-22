"""
Compliance API Routes - Phase 4
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from datetime import datetime

router = APIRouter(prefix="/compliance", tags=["Compliance"])


class LogDecisionRequest(BaseModel):
    decision_type: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    reasoning_steps: List[Dict[str, Any]]
    model_version: str


class GenerateReportRequest(BaseModel):
    report_type: str  # daily, weekly, monthly
    period_start: str  # ISO date
    period_end: str  # ISO date


class OverrideConfigRequest(BaseModel):
    user_address: str
    amount_threshold: Optional[float] = None
    frequency_threshold: Optional[int] = None
    asset_types: List[str] = []
    always_ask_operations: List[str] = []
    enabled: bool = True


class OverrideResponseRequest(BaseModel):
    request_id: str
    approved: bool
    notes: Optional[str] = None


@router.post("/decision/log")
async def log_decision(request: LogDecisionRequest) -> Dict[str, Any]:
    """Log an AI decision for compliance."""
    from ...compliance import ComplianceEngine, AIDecision, ReasoningStep, DecisionType, RiskLevel
    import hashlib
    import time
    
    engine = ComplianceEngine()
    
    type_map = {
        "trade_execution": DecisionType.TRADE_EXECUTION,
        "portfolio_rebalance": DecisionType.PORTFOLIO_REBALANCE,
        "risk_assessment": DecisionType.RISK_ASSESSMENT,
        "strategy_selection": DecisionType.STRATEGY_SELECTION,
        "price_prediction": DecisionType.PRICE_PREDICTION,
    }
    
    decision_type = type_map.get(request.decision_type)
    if not decision_type:
        raise HTTPException(400, f"Invalid decision type: {request.decision_type}")
    
    reasoning_chain = [
        ReasoningStep(
            step_number=i + 1,
            description=step.get("description", ""),
            inputs=step.get("inputs", {}),
            outputs=step.get("outputs", {}),
            confidence=step.get("confidence", 0.5),
        )
        for i, step in enumerate(request.reasoning_steps)
    ]
    
    decision_id = f"decision_{hashlib.sha256(f'{time.time()}'.encode()).hexdigest()[:12]}"
    
    decision = AIDecision(
        decision_id=decision_id,
        decision_type=decision_type,
        risk_level=RiskLevel.MINIMAL,  # Will be classified
        reasoning_chain=reasoning_chain,
        explanation="",  # Will be generated
        inputs=request.inputs,
        outputs=request.outputs,
        timestamp=datetime.utcnow(),
        model_version=request.model_version,
    )
    
    # Classify and log
    decision.risk_level = await engine.classify_decision(decision)
    await engine.log_decision(decision)
    
    return {
        "decision_id": decision_id,
        "risk_level": decision.risk_level.value,
        "explanation": decision.explanation,
    }


@router.post("/report/generate")
async def generate_report(request: GenerateReportRequest) -> Dict[str, Any]:
    """Generate compliance report."""
    from ...compliance import ComplianceEngine, ReportType
    
    engine = ComplianceEngine()
    
    type_map = {
        "daily": ReportType.DAILY,
        "weekly": ReportType.WEEKLY,
        "monthly": ReportType.MONTHLY,
    }
    
    report_type = type_map.get(request.report_type)
    if not report_type:
        raise HTTPException(400, f"Invalid report type: {request.report_type}")
    
    report = await engine.generate_report(
        report_type,
        datetime.fromisoformat(request.period_start),
        datetime.fromisoformat(request.period_end),
    )
    
    return {
        "report_id": report.report_id,
        "report_type": report.report_type.value,
        "period_start": report.period_start.isoformat(),
        "period_end": report.period_end.isoformat(),
        "total_decisions": report.total_decisions,
        "decisions_by_risk": report.decisions_by_risk,
        "override_count": report.override_count,
        "anomalies_count": len(report.anomalies),
    }


@router.get("/report/{report_id}/export")
async def export_report(report_id: str, format: str = "json") -> Dict[str, Any]:
    """Export compliance report."""
    from ...compliance import ComplianceEngine, ExportFormat
    
    engine = ComplianceEngine()
    report = engine.reports.get(report_id)
    
    if not report:
        raise HTTPException(404, "Report not found")
    
    format_map = {
        "json": ExportFormat.JSON,
        "xml": ExportFormat.XML,
        "pdf": ExportFormat.PDF,
    }
    
    export_format = format_map.get(format)
    if not export_format:
        raise HTTPException(400, f"Invalid format: {format}")
    
    data = await engine.export_report(report, export_format)
    
    return {
        "report_id": report_id,
        "format": format,
        "data": data.decode(),
    }


@router.get("/dsar/{user_address}")
async def handle_dsar(user_address: str) -> Dict[str, Any]:
    """Handle Data Subject Access Request."""
    from ...compliance import ComplianceEngine
    
    engine = ComplianceEngine()
    response = await engine.handle_dsar(user_address)
    
    return {
        "user_address": response.user_address,
        "decisions_count": len(response.decisions),
        "data_categories": response.data_categories,
        "retention_period_years": response.retention_period_years,
        "generated_at": response.generated_at.isoformat(),
    }


@router.get("/audit")
async def get_audit_trail(
    user_address: Optional[str] = None,
    decision_type: Optional[str] = None,
    risk_level: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Get audit trail."""
    from ...compliance import ComplianceEngine, AuditFilters, DecisionType, RiskLevel
    
    engine = ComplianceEngine()
    
    type_map = {
        "trade_execution": DecisionType.TRADE_EXECUTION,
        "portfolio_rebalance": DecisionType.PORTFOLIO_REBALANCE,
        "risk_assessment": DecisionType.RISK_ASSESSMENT,
    }
    
    risk_map = {
        "minimal": RiskLevel.MINIMAL,
        "limited": RiskLevel.LIMITED,
        "high": RiskLevel.HIGH,
    }
    
    filters = AuditFilters(
        user_address=user_address,
        decision_type=type_map.get(decision_type) if decision_type else None,
        risk_level=risk_map.get(risk_level) if risk_level else None,
    )
    
    decisions = await engine.get_audit_trail(filters)
    
    return [
        {
            "decision_id": d.decision_id,
            "decision_type": d.decision_type.value,
            "risk_level": d.risk_level.value,
            "timestamp": d.timestamp.isoformat(),
        }
        for d in decisions[:limit]
    ]


# Human Override endpoints
@router.post("/override/config")
async def update_override_config(request: OverrideConfigRequest) -> Dict[str, Any]:
    """Update user's override configuration."""
    from ...compliance import HumanOverrideSystem, OverrideConfig
    
    system = HumanOverrideSystem()
    
    config = OverrideConfig(
        user_address=request.user_address,
        amount_threshold=request.amount_threshold,
        frequency_threshold=request.frequency_threshold,
        asset_types=request.asset_types,
        always_ask_operations=request.always_ask_operations,
        enabled=request.enabled,
    )
    
    await system.update_override_config(config)
    
    return {"success": True, "user_address": request.user_address}


@router.get("/override/config/{user_address}")
async def get_override_config(user_address: str) -> Dict[str, Any]:
    """Get user's override configuration."""
    from ...compliance import HumanOverrideSystem
    
    system = HumanOverrideSystem()
    config = await system.get_override_config(user_address)
    
    if not config:
        return {"user_address": user_address, "configured": False}
    
    return {
        "user_address": config.user_address,
        "configured": True,
        "amount_threshold": config.amount_threshold,
        "frequency_threshold": config.frequency_threshold,
        "asset_types": config.asset_types,
        "always_ask_operations": config.always_ask_operations,
        "enabled": config.enabled,
    }


@router.post("/override/pause/{user_address}")
async def pause_execution(user_address: str) -> Dict[str, Any]:
    """Pause AI execution for user."""
    from ...compliance import HumanOverrideSystem
    
    system = HumanOverrideSystem()
    success = await system.pause_execution(user_address)
    
    return {"paused": True, "within_timeout": success}


@router.post("/override/resume/{user_address}")
async def resume_execution(user_address: str) -> Dict[str, Any]:
    """Resume AI execution for user."""
    from ...compliance import HumanOverrideSystem
    
    system = HumanOverrideSystem()
    success = await system.resume_execution(user_address)
    
    return {"resumed": success}


@router.post("/override/respond")
async def respond_to_override(request: OverrideResponseRequest) -> Dict[str, Any]:
    """Respond to override request."""
    from ...compliance import HumanOverrideSystem, OverrideResponse
    
    system = HumanOverrideSystem()
    
    response = OverrideResponse(
        request_id=request.request_id,
        approved=request.approved,
        user_address="",  # Will be filled from request
        responded_at=datetime.utcnow(),
        notes=request.notes,
    )
    
    try:
        await system.process_response(response)
        return {"success": True, "approved": request.approved}
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.get("/override/history/{user_address}")
async def get_override_history(user_address: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Get override history for user."""
    from ...compliance import HumanOverrideSystem
    
    system = HumanOverrideSystem()
    history = await system.get_override_history(user_address, limit)
    
    return history
