"""
Compliance Engine - EU AI Act Compliance
Phase 4: Ecosystem & Compliance

Provides EU AI Act compliance monitoring, audit trails, and reporting.
"""

import hashlib
import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    MINIMAL = "minimal"
    LIMITED = "limited"
    HIGH = "high"


class DecisionType(Enum):
    TRADE_EXECUTION = "trade_execution"
    PORTFOLIO_REBALANCE = "portfolio_rebalance"
    RISK_ASSESSMENT = "risk_assessment"
    STRATEGY_SELECTION = "strategy_selection"
    PRICE_PREDICTION = "price_prediction"


class ReportType(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class ExportFormat(Enum):
    JSON = "json"
    XML = "xml"
    PDF = "pdf"


@dataclass
class ReasoningStep:
    step_number: int
    description: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    confidence: float


@dataclass
class AIDecision:
    decision_id: str
    decision_type: DecisionType
    risk_level: RiskLevel
    reasoning_chain: List[ReasoningStep]
    explanation: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    timestamp: datetime
    model_version: str


@dataclass
class Anomaly:
    anomaly_id: str
    decision_id: str
    anomaly_type: str
    description: str
    severity: str
    detected_at: datetime


@dataclass
class ComplianceReport:
    report_id: str
    report_type: ReportType
    period_start: datetime
    period_end: datetime
    total_decisions: int
    decisions_by_risk: Dict[str, int]
    override_count: int
    anomalies: List[Anomaly]
    generated_at: datetime


@dataclass
class DSARResponse:
    user_address: str
    decisions: List[AIDecision]
    data_categories: List[str]
    retention_period_years: int
    generated_at: datetime


@dataclass
class AuditFilters:
    user_address: Optional[str] = None
    decision_type: Optional[DecisionType] = None
    risk_level: Optional[RiskLevel] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class ComplianceEngine:
    """
    Compliance Engine for EU AI Act compliance.
    
    Validates: Requirements 5.1-5.6, 9.1-9.6
    """
    
    RETENTION_YEARS = 5
    HIGH_RISK_THRESHOLD_AMOUNT = 10000
    
    def __init__(self):
        self.decisions: Dict[str, AIDecision] = {}
        self.anomalies: List[Anomaly] = []
        self.reports: Dict[str, ComplianceReport] = {}
        self.override_log: List[Dict[str, Any]] = []

    async def classify_decision(self, decision: AIDecision) -> RiskLevel:
        """
        Classify AI decision by risk level.
        
        Property 13: Decision Risk Classification
        For any AI decision, assigns exactly one risk level.
        """
        # High risk: large amounts, portfolio changes, automated execution
        if decision.decision_type in [DecisionType.PORTFOLIO_REBALANCE, DecisionType.TRADE_EXECUTION]:
            amount = decision.inputs.get("amount", 0)
            if amount > self.HIGH_RISK_THRESHOLD_AMOUNT:
                return RiskLevel.HIGH
        
        # High risk: low confidence decisions
        if decision.reasoning_chain:
            avg_confidence = sum(s.confidence for s in decision.reasoning_chain) / len(decision.reasoning_chain)
            if avg_confidence < 0.7:
                return RiskLevel.HIGH
        
        # Limited risk: predictions and assessments
        if decision.decision_type in [DecisionType.PRICE_PREDICTION, DecisionType.RISK_ASSESSMENT]:
            return RiskLevel.LIMITED
        
        # Minimal risk: strategy selection with user confirmation
        return RiskLevel.MINIMAL

    async def log_decision(self, decision: AIDecision) -> str:
        """
        Log AI decision with complete audit trail.
        
        Property 14: High-Risk Decision Logging
        For any high-risk decision, logs complete reasoning chain.
        """
        # Classify if not already classified
        if not decision.risk_level:
            decision.risk_level = await self.classify_decision(decision)
        
        # Generate explanation if not provided
        if not decision.explanation:
            decision.explanation = await self.generate_explanation(decision)
        
        self.decisions[decision.decision_id] = decision
        
        logger.info(f"Logged decision {decision.decision_id} [{decision.risk_level.value}]")
        return decision.decision_id

    async def generate_explanation(self, decision: AIDecision) -> str:
        """
        Generate human-readable explanation for AI decision.
        
        Property 15: Human-Readable Explanations
        For any AI decision, generates human-readable explanation.
        """
        explanation_parts = []
        
        # Decision type context
        type_descriptions = {
            DecisionType.TRADE_EXECUTION: "executed a trade",
            DecisionType.PORTFOLIO_REBALANCE: "rebalanced the portfolio",
            DecisionType.RISK_ASSESSMENT: "assessed risk levels",
            DecisionType.STRATEGY_SELECTION: "selected a trading strategy",
            DecisionType.PRICE_PREDICTION: "predicted price movement",
        }
        
        explanation_parts.append(f"The AI system {type_descriptions.get(decision.decision_type, 'made a decision')}")
        
        # Add reasoning steps
        if decision.reasoning_chain:
            explanation_parts.append("based on the following analysis:")
            for step in decision.reasoning_chain:
                explanation_parts.append(f"  {step.step_number}. {step.description} (confidence: {step.confidence:.0%})")
        
        # Add input summary
        if decision.inputs:
            key_inputs = list(decision.inputs.keys())[:3]
            explanation_parts.append(f"Key inputs considered: {', '.join(key_inputs)}")
        
        # Add risk level context
        explanation_parts.append(f"This decision was classified as {decision.risk_level.value} risk.")
        
        return "\n".join(explanation_parts)

    async def generate_report(
        self,
        report_type: ReportType,
        period_start: datetime,
        period_end: datetime
    ) -> ComplianceReport:
        """
        Generate compliance report for period.
        
        Property 16: Compliance Report Generation
        For any reporting period, generates complete compliance report.
        """
        # Filter decisions in period
        period_decisions = [
            d for d in self.decisions.values()
            if period_start <= d.timestamp <= period_end
        ]
        
        # Count by risk level
        decisions_by_risk = {
            RiskLevel.MINIMAL.value: 0,
            RiskLevel.LIMITED.value: 0,
            RiskLevel.HIGH.value: 0,
        }
        for d in period_decisions:
            decisions_by_risk[d.risk_level.value] += 1
        
        # Count overrides in period
        override_count = len([
            o for o in self.override_log
            if period_start <= o.get("timestamp", datetime.min) <= period_end
        ])
        
        # Get anomalies in period
        period_anomalies = [
            a for a in self.anomalies
            if period_start <= a.detected_at <= period_end
        ]
        
        report = ComplianceReport(
            report_id=self._generate_id("report"),
            report_type=report_type,
            period_start=period_start,
            period_end=period_end,
            total_decisions=len(period_decisions),
            decisions_by_risk=decisions_by_risk,
            override_count=override_count,
            anomalies=period_anomalies,
            generated_at=datetime.utcnow(),
        )
        
        self.reports[report.report_id] = report
        logger.info(f"Generated {report_type.value} compliance report: {report.report_id}")
        return report

    async def export_report(
        self,
        report: ComplianceReport,
        format: ExportFormat
    ) -> bytes:
        """
        Export compliance report in specified format.
        
        Property 17: Export Format Support
        For any compliance report, supports XML, JSON, and PDF export.
        """
        if format == ExportFormat.JSON:
            return self._export_json(report)
        elif format == ExportFormat.XML:
            return self._export_xml(report)
        elif format == ExportFormat.PDF:
            return self._export_pdf(report)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _export_json(self, report: ComplianceReport) -> bytes:
        """Export report as JSON."""
        data = {
            "report_id": report.report_id,
            "report_type": report.report_type.value,
            "period_start": report.period_start.isoformat(),
            "period_end": report.period_end.isoformat(),
            "total_decisions": report.total_decisions,
            "decisions_by_risk": report.decisions_by_risk,
            "override_count": report.override_count,
            "anomalies_count": len(report.anomalies),
            "generated_at": report.generated_at.isoformat(),
        }
        return json.dumps(data, indent=2).encode()

    def _export_xml(self, report: ComplianceReport) -> bytes:
        """Export report as XML."""
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<ComplianceReport>
    <ReportId>{report.report_id}</ReportId>
    <ReportType>{report.report_type.value}</ReportType>
    <PeriodStart>{report.period_start.isoformat()}</PeriodStart>
    <PeriodEnd>{report.period_end.isoformat()}</PeriodEnd>
    <TotalDecisions>{report.total_decisions}</TotalDecisions>
    <DecisionsByRisk>
        <Minimal>{report.decisions_by_risk.get('minimal', 0)}</Minimal>
        <Limited>{report.decisions_by_risk.get('limited', 0)}</Limited>
        <High>{report.decisions_by_risk.get('high', 0)}</High>
    </DecisionsByRisk>
    <OverrideCount>{report.override_count}</OverrideCount>
    <AnomaliesCount>{len(report.anomalies)}</AnomaliesCount>
    <GeneratedAt>{report.generated_at.isoformat()}</GeneratedAt>
</ComplianceReport>"""
        return xml.encode()

    def _export_pdf(self, report: ComplianceReport) -> bytes:
        """Export report as PDF (simplified text representation)."""
        content = f"""COMPLIANCE REPORT
================
Report ID: {report.report_id}
Type: {report.report_type.value.upper()}
Period: {report.period_start.date()} to {report.period_end.date()}

SUMMARY
-------
Total Decisions: {report.total_decisions}
- Minimal Risk: {report.decisions_by_risk.get('minimal', 0)}
- Limited Risk: {report.decisions_by_risk.get('limited', 0)}
- High Risk: {report.decisions_by_risk.get('high', 0)}

Human Overrides: {report.override_count}
Anomalies Detected: {len(report.anomalies)}

Generated: {report.generated_at.isoformat()}
"""
        return content.encode()

    async def handle_dsar(self, user_address: str) -> DSARResponse:
        """
        Handle Data Subject Access Request.
        
        Property 18: DSAR Request Handling
        For any DSAR, retrieves all user-related AI decisions and data.
        """
        # Find all decisions related to user
        user_decisions = [
            d for d in self.decisions.values()
            if d.inputs.get("user_address") == user_address
            or d.outputs.get("user_address") == user_address
        ]
        
        # Determine data categories
        data_categories = set()
        for d in user_decisions:
            data_categories.add(d.decision_type.value)
            if "portfolio" in str(d.inputs).lower():
                data_categories.add("portfolio_data")
            if "trade" in str(d.inputs).lower():
                data_categories.add("trading_data")
        
        return DSARResponse(
            user_address=user_address,
            decisions=user_decisions,
            data_categories=list(data_categories),
            retention_period_years=self.RETENTION_YEARS,
            generated_at=datetime.utcnow(),
        )

    async def get_audit_trail(self, filters: AuditFilters) -> List[AIDecision]:
        """Get audit trail with filtering."""
        results = list(self.decisions.values())
        
        if filters.user_address:
            results = [
                d for d in results
                if d.inputs.get("user_address") == filters.user_address
            ]
        
        if filters.decision_type:
            results = [d for d in results if d.decision_type == filters.decision_type]
        
        if filters.risk_level:
            results = [d for d in results if d.risk_level == filters.risk_level]
        
        if filters.start_date:
            results = [d for d in results if d.timestamp >= filters.start_date]
        
        if filters.end_date:
            results = [d for d in results if d.timestamp <= filters.end_date]
        
        return sorted(results, key=lambda x: x.timestamp, reverse=True)

    def log_override(self, override_data: Dict[str, Any]) -> None:
        """Log human override event."""
        override_data["timestamp"] = datetime.utcnow()
        self.override_log.append(override_data)

    def detect_anomaly(
        self,
        decision: AIDecision,
        anomaly_type: str,
        description: str
    ) -> Anomaly:
        """Detect and record an anomaly."""
        anomaly = Anomaly(
            anomaly_id=self._generate_id("anomaly"),
            decision_id=decision.decision_id,
            anomaly_type=anomaly_type,
            description=description,
            severity="high" if decision.risk_level == RiskLevel.HIGH else "medium",
            detected_at=datetime.utcnow(),
        )
        self.anomalies.append(anomaly)
        logger.warning(f"Anomaly detected: {anomaly_type} - {description}")
        return anomaly

    def _generate_id(self, prefix: str) -> str:
        """Generate unique ID."""
        return f"{prefix}_{hashlib.sha256(f'{time.time()}'.encode()).hexdigest()[:12]}"
