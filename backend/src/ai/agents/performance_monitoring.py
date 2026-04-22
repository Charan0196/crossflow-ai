"""
Performance Monitoring and Analytics System
Comprehensive tracking and analysis of AI agent performance
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import uuid
import numpy as np
from collections import defaultdict

from ..config import AIConfig, AgentConfig, AgentType, get_agent_config
from ..utils.model_manager import ModelManager


class MetricType(Enum):
    ACCURACY = "accuracy"
    LATENCY = "latency"
    SUCCESS_RATE = "success_rate"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"


@dataclass
class DecisionMetrics:
    decision_id: str
    agent_id: str
    accuracy: float
    latency_ms: float
    success: bool
    timestamp: datetime


@dataclass
class PerformanceAlert:
    alert_id: str
    agent_id: str
    metric_type: MetricType
    current_value: float
    threshold: float
    severity: str
    diagnostic_info: str
    timestamp: datetime


@dataclass
class PerformanceAttribution:
    attribution_id: str
    strategy_a: str
    strategy_b: str
    performance_diff: float
    factors: Dict[str, float]
    confidence: float
    timestamp: datetime


@dataclass
class HistoricalData:
    data_id: str
    agent_id: str
    metric_type: MetricType
    values: List[float]
    timestamps: List[datetime]
    aggregation_period: str


@dataclass
class PerformanceReport:
    report_id: str
    period_start: datetime
    period_end: datetime
    technical_metrics: Dict[str, float]
    business_metrics: Dict[str, float]
    recommendations: List[str]
    timestamp: datetime


class DecisionTracker:
    """Tracks decision accuracy and success rates"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.metrics: List[DecisionMetrics] = []
        self.agent_metrics: Dict[str, List[DecisionMetrics]] = defaultdict(list)
    
    def track_decision(self, decision_id: str, agent_id: str,
                      accuracy: float, latency_ms: float, success: bool) -> DecisionMetrics:
        """Track a decision"""
        metric = DecisionMetrics(
            decision_id=decision_id,
            agent_id=agent_id,
            accuracy=accuracy,
            latency_ms=latency_ms,
            success=success,
            timestamp=datetime.now()
        )
        self.metrics.append(metric)
        self.agent_metrics[agent_id].append(metric)
        return metric
    
    def get_agent_stats(self, agent_id: str) -> Dict[str, float]:
        """Get statistics for an agent"""
        metrics = self.agent_metrics.get(agent_id, [])
        if not metrics:
            return {'accuracy': 0, 'success_rate': 0, 'avg_latency': 0}
        
        return {
            'accuracy': np.mean([m.accuracy for m in metrics]),
            'success_rate': sum(1 for m in metrics if m.success) / len(metrics),
            'avg_latency': np.mean([m.latency_ms for m in metrics])
        }


class DegradationDetector:
    """Detects performance degradation"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.thresholds = {
            MetricType.ACCURACY: 0.7,
            MetricType.SUCCESS_RATE: 0.8,
            MetricType.LATENCY: 100,  # ms
            MetricType.ERROR_RATE: 0.1
        }
        self.alerts: List[PerformanceAlert] = []
    
    def check_degradation(self, agent_id: str, metric_type: MetricType,
                         current_value: float) -> Optional[PerformanceAlert]:
        """Check for performance degradation"""
        threshold = self.thresholds.get(metric_type, 0.5)
        
        # For latency and error rate, higher is worse
        is_degraded = False
        if metric_type in [MetricType.LATENCY, MetricType.ERROR_RATE]:
            is_degraded = current_value > threshold
        else:
            is_degraded = current_value < threshold
        
        if is_degraded:
            severity = "critical" if abs(current_value - threshold) / threshold > 0.3 else "warning"
            
            alert = PerformanceAlert(
                alert_id=str(uuid.uuid4()),
                agent_id=agent_id,
                metric_type=metric_type,
                current_value=current_value,
                threshold=threshold,
                severity=severity,
                diagnostic_info=f"{metric_type.value} degraded: {current_value:.2f} vs threshold {threshold:.2f}",
                timestamp=datetime.now()
            )
            self.alerts.append(alert)
            return alert
        return None


class AttributionAnalyzer:
    """Analyzes performance attribution between strategies"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.attributions: List[PerformanceAttribution] = []
    
    def compare_strategies(self, strategy_a: str, perf_a: Dict[str, float],
                          strategy_b: str, perf_b: Dict[str, float]) -> PerformanceAttribution:
        """Compare two strategies"""
        # Calculate performance difference
        perf_diff = perf_a.get('return', 0) - perf_b.get('return', 0)
        
        # Attribute to factors
        factors = {
            'timing': (perf_a.get('timing_score', 0.5) - perf_b.get('timing_score', 0.5)) * 0.3,
            'risk_management': (perf_a.get('risk_score', 0.5) - perf_b.get('risk_score', 0.5)) * 0.3,
            'execution': (perf_a.get('execution_score', 0.5) - perf_b.get('execution_score', 0.5)) * 0.4
        }
        
        attribution = PerformanceAttribution(
            attribution_id=str(uuid.uuid4()),
            strategy_a=strategy_a,
            strategy_b=strategy_b,
            performance_diff=perf_diff,
            factors=factors,
            confidence=0.8,
            timestamp=datetime.now()
        )
        self.attributions.append(attribution)
        return attribution


class HistoricalDataManager:
    """Manages historical performance data"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.data: Dict[str, List[HistoricalData]] = defaultdict(list)
    
    def store_data(self, agent_id: str, metric_type: MetricType,
                  values: List[float], timestamps: List[datetime],
                  period: str = "daily") -> HistoricalData:
        """Store historical data"""
        data = HistoricalData(
            data_id=str(uuid.uuid4()),
            agent_id=agent_id,
            metric_type=metric_type,
            values=values,
            timestamps=timestamps,
            aggregation_period=period
        )
        self.data[agent_id].append(data)
        return data
    
    def get_trend(self, agent_id: str, metric_type: MetricType,
                 periods: int = 10) -> Dict[str, Any]:
        """Get trend for metric"""
        agent_data = self.data.get(agent_id, [])
        relevant = [d for d in agent_data if d.metric_type == metric_type]
        
        if not relevant:
            return {'trend': 'unknown', 'change': 0}
        
        latest = relevant[-1]
        if len(latest.values) < 2:
            return {'trend': 'stable', 'change': 0}
        
        recent = latest.values[-periods:] if len(latest.values) >= periods else latest.values
        change = (recent[-1] - recent[0]) / (recent[0] + 0.001)
        
        if change > 0.05:
            trend = 'improving'
        elif change < -0.05:
            trend = 'declining'
        else:
            trend = 'stable'
        
        return {'trend': trend, 'change': change}


class ReportGenerator:
    """Generates performance reports"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.reports: List[PerformanceReport] = []
    
    def generate_report(self, tracker: DecisionTracker,
                       period_start: datetime, period_end: datetime) -> PerformanceReport:
        """Generate comprehensive report"""
        # Filter metrics in period
        period_metrics = [m for m in tracker.metrics 
                         if period_start <= m.timestamp <= period_end]
        
        # Technical metrics
        if period_metrics:
            technical = {
                'total_decisions': len(period_metrics),
                'avg_accuracy': np.mean([m.accuracy for m in period_metrics]),
                'success_rate': sum(1 for m in period_metrics if m.success) / len(period_metrics),
                'avg_latency_ms': np.mean([m.latency_ms for m in period_metrics])
            }
        else:
            technical = {'total_decisions': 0, 'avg_accuracy': 0, 'success_rate': 0, 'avg_latency_ms': 0}
        
        # Business metrics (simulated)
        business = {
            'estimated_value_added': technical['success_rate'] * 1000,
            'risk_adjusted_return': technical['avg_accuracy'] * 0.1,
            'operational_efficiency': 1 - (technical['avg_latency_ms'] / 1000)
        }
        
        # Recommendations
        recommendations = []
        if technical['avg_accuracy'] < 0.7:
            recommendations.append("Consider retraining models - accuracy below threshold")
        if technical['avg_latency_ms'] > 50:
            recommendations.append("Optimize decision pipeline - latency above target")
        if technical['success_rate'] < 0.8:
            recommendations.append("Review decision criteria - success rate needs improvement")
        if not recommendations:
            recommendations.append("Performance within acceptable bounds")
        
        report = PerformanceReport(
            report_id=str(uuid.uuid4()),
            period_start=period_start,
            period_end=period_end,
            technical_metrics=technical,
            business_metrics=business,
            recommendations=recommendations,
            timestamp=datetime.now()
        )
        self.reports.append(report)
        return report


class PerformanceMonitoringSystem:
    """Main performance monitoring system"""
    
    def __init__(self, config: AIConfig, agent_config: AgentConfig, model_manager: ModelManager):
        self.config = config
        self.agent_config = agent_config
        self.model_manager = model_manager
        self.logger = logging.getLogger(__name__)
        
        self.tracker = DecisionTracker()
        self.degradation_detector = DegradationDetector()
        self.attribution_analyzer = AttributionAnalyzer()
        self.historical_manager = HistoricalDataManager()
        self.report_generator = ReportGenerator()
        
        self.logger.info("Performance Monitoring System initialized")
    
    async def track_decision(self, decision_id: str, agent_id: str,
                            accuracy: float, latency_ms: float, 
                            success: bool) -> DecisionMetrics:
        """Track decision metrics - Requirements: 10.1"""
        return self.tracker.track_decision(decision_id, agent_id, accuracy, latency_ms, success)
    
    async def check_degradation(self, agent_id: str, metric_type: MetricType,
                               current_value: float) -> Optional[PerformanceAlert]:
        """Check for degradation - Requirements: 10.2"""
        return self.degradation_detector.check_degradation(agent_id, metric_type, current_value)
    
    async def analyze_attribution(self, strategy_a: str, perf_a: Dict[str, float],
                                  strategy_b: str, perf_b: Dict[str, float]) -> PerformanceAttribution:
        """Analyze performance attribution - Requirements: 10.3"""
        return self.attribution_analyzer.compare_strategies(strategy_a, perf_a, strategy_b, perf_b)
    
    async def store_historical_data(self, agent_id: str, metric_type: MetricType,
                                   values: List[float], timestamps: List[datetime]) -> HistoricalData:
        """Store historical data - Requirements: 10.4"""
        return self.historical_manager.store_data(agent_id, metric_type, values, timestamps)
    
    async def generate_report(self, period_start: datetime, 
                             period_end: datetime) -> PerformanceReport:
        """Generate performance report - Requirements: 10.5"""
        return self.report_generator.generate_report(self.tracker, period_start, period_end)
