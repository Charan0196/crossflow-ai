"""
Analytics and Reporting Service
Generates daily trading volume reports, system health reports, and popular trading pair analytics
Requirements: 9.4 - Daily reports on trading volume, popular trading pairs, and system health
"""
import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from enum import Enum
import statistics

from src.services.system_logging_service import system_logging_service, IntentEventType, SolverEventType
from src.services.communication_logger import communication_logger, EventType


class ReportType(Enum):
    """Types of reports that can be generated"""
    DAILY_TRADING_VOLUME = "daily_trading_volume"
    SYSTEM_HEALTH = "system_health"
    POPULAR_TRADING_PAIRS = "popular_trading_pairs"
    SOLVER_PERFORMANCE = "solver_performance"
    CROSS_CHAIN_ACTIVITY = "cross_chain_activity"
    ERROR_ANALYSIS = "error_analysis"
    PERFORMANCE_METRICS = "performance_metrics"


class ReportPeriod(Enum):
    """Report time periods"""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


@dataclass
class TradingVolumeReport:
    """Daily trading volume report"""
    report_date: str
    total_volume_usd: Decimal
    total_intents: int
    successful_intents: int
    failed_intents: int
    success_rate: float
    average_trade_size_usd: Decimal
    top_trading_pairs: List[Dict[str, Any]]
    chain_breakdown: Dict[str, Dict[str, Any]]
    hourly_breakdown: List[Dict[str, Any]]
    volume_trend: str  # "increasing", "decreasing", "stable"
    generated_at: datetime


@dataclass
class SystemHealthReport:
    """System health report"""
    report_date: str
    overall_health_score: float  # 0-100
    uptime_percentage: float
    average_response_time_ms: float
    error_rate: float
    service_status: Dict[str, str]
    resource_utilization: Dict[str, float]
    performance_alerts: List[Dict[str, Any]]
    critical_issues: List[Dict[str, Any]]
    recommendations: List[str]
    generated_at: datetime


@dataclass
class PopularTradingPairsReport:
    """Popular trading pairs analytics report"""
    report_date: str
    top_pairs_by_volume: List[Dict[str, Any]]
    top_pairs_by_count: List[Dict[str, Any]]
    emerging_pairs: List[Dict[str, Any]]
    declining_pairs: List[Dict[str, Any]]
    cross_chain_preferences: Dict[str, Any]
    token_popularity: Dict[str, Any]
    generated_at: datetime


@dataclass
class SolverPerformanceReport:
    """Solver network performance report"""
    report_date: str
    total_active_solvers: int
    top_performers: List[Dict[str, Any]]
    underperformers: List[Dict[str, Any]]
    average_success_rate: float
    average_execution_time_ms: float
    reputation_distribution: Dict[str, int]
    chain_coverage: Dict[str, List[str]]
    volume_distribution: Dict[str, Decimal]
    generated_at: datetime


@dataclass
class PerformanceDashboardData:
    """Performance dashboard data for operators"""
    timestamp: datetime
    system_overview: Dict[str, Any]
    real_time_metrics: Dict[str, Any]
    performance_trends: Dict[str, Any]
    alerts_and_warnings: List[Dict[str, Any]]
    resource_utilization: Dict[str, Any]
    network_status: Dict[str, Any]
    solver_network_health: Dict[str, Any]
    recent_activities: List[Dict[str, Any]]


class AnalyticsReportingService:
    """Service for generating analytics reports and insights"""
    
    def __init__(self):
        self.report_cache: Dict[str, Any] = {}
        self.cache_ttl_seconds = 3600  # 1 hour cache TTL
    
    def _get_cache_key(self, report_type: ReportType, period: ReportPeriod, date: str) -> str:
        """Generate cache key for report"""
        return f"{report_type.value}_{period.value}_{date}"
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached report is still valid"""
        if cache_key not in self.report_cache:
            return False
        
        cached_report = self.report_cache[cache_key]
        cache_time = cached_report.get("cached_at", 0)
        return (time.time() - cache_time) < self.cache_ttl_seconds
    
    async def generate_daily_trading_volume_report(
        self,
        target_date: Optional[str] = None
    ) -> TradingVolumeReport:
        """
        Generate daily trading volume report
        Requirements: 9.4 - Daily reports on trading volume
        """
        if target_date is None:
            target_date = datetime.now().strftime("%Y-%m-%d")
        
        cache_key = self._get_cache_key(ReportType.DAILY_TRADING_VOLUME, ReportPeriod.DAILY, target_date)
        
        if self._is_cache_valid(cache_key):
            return self.report_cache[cache_key]["report"]
        
        # Parse target date
        date_obj = datetime.strptime(target_date, "%Y-%m-%d")
        start_time = date_obj.timestamp()
        end_time = (date_obj + timedelta(days=1)).timestamp()
        
        # Get intent processing statistics
        intent_stats = system_logging_service.get_intent_processing_stats(start_time, end_time)
        
        # Calculate hourly breakdown
        hourly_breakdown = []
        for hour in range(24):
            hour_start = start_time + (hour * 3600)
            hour_end = hour_start + 3600
            hour_stats = system_logging_service.get_intent_processing_stats(hour_start, hour_end)
            
            hourly_breakdown.append({
                "hour": hour,
                "volume_usd": str(hour_stats.total_volume_usd),
                "intent_count": hour_stats.total_intents,
                "success_rate": hour_stats.success_rate
            })
        
        # Process top trading pairs
        top_trading_pairs = []
        for pair, count in list(intent_stats.popular_tokens.items())[:10]:
            # Parse token pair
            if "->" in pair:
                input_token, output_token = pair.split("->", 1)
                top_trading_pairs.append({
                    "input_token": input_token,
                    "output_token": output_token,
                    "trade_count": count,
                    "estimated_volume_usd": str(Decimal(count) * Decimal('100'))  # Simplified estimation
                })
        
        # Process chain breakdown
        chain_breakdown = {}
        for chain_pair, count in intent_stats.popular_chains.items():
            if "->" in chain_pair:
                source_chain, dest_chain = chain_pair.split("->", 1)
                chain_key = f"chain_{source_chain}_to_{dest_chain}"
                chain_breakdown[chain_key] = {
                    "source_chain": int(source_chain),
                    "destination_chain": int(dest_chain),
                    "trade_count": count,
                    "estimated_volume_usd": str(Decimal(count) * Decimal('100'))
                }
        
        # Determine volume trend (simplified)
        volume_trend = "stable"
        if len(hourly_breakdown) >= 12:
            first_half_volume = sum(Decimal(h["volume_usd"]) for h in hourly_breakdown[:12])
            second_half_volume = sum(Decimal(h["volume_usd"]) for h in hourly_breakdown[12:])
            
            if second_half_volume > first_half_volume * Decimal('1.1'):
                volume_trend = "increasing"
            elif second_half_volume < first_half_volume * Decimal('0.9'):
                volume_trend = "decreasing"
        
        # Calculate average trade size
        avg_trade_size = (intent_stats.total_volume_usd / intent_stats.total_intents) if intent_stats.total_intents > 0 else Decimal('0')
        
        report = TradingVolumeReport(
            report_date=target_date,
            total_volume_usd=intent_stats.total_volume_usd,
            total_intents=intent_stats.total_intents,
            successful_intents=intent_stats.successful_intents,
            failed_intents=intent_stats.failed_intents,
            success_rate=intent_stats.success_rate,
            average_trade_size_usd=avg_trade_size,
            top_trading_pairs=top_trading_pairs,
            chain_breakdown=chain_breakdown,
            hourly_breakdown=hourly_breakdown,
            volume_trend=volume_trend,
            generated_at=datetime.now()
        )
        
        # Cache the report
        self.report_cache[cache_key] = {
            "report": report,
            "cached_at": time.time()
        }
        
        return report
    
    async def generate_system_health_report(
        self,
        target_date: Optional[str] = None
    ) -> SystemHealthReport:
        """
        Generate system health report
        Requirements: 9.4 - System health reports
        """
        if target_date is None:
            target_date = datetime.now().strftime("%Y-%m-%d")
        
        cache_key = self._get_cache_key(ReportType.SYSTEM_HEALTH, ReportPeriod.DAILY, target_date)
        
        if self._is_cache_valid(cache_key):
            return self.report_cache[cache_key]["report"]
        
        # Parse target date
        date_obj = datetime.strptime(target_date, "%Y-%m-%d")
        start_time = date_obj.timestamp()
        end_time = (date_obj + timedelta(days=1)).timestamp()
        
        # Get system health statistics
        health_stats = system_logging_service.get_system_health_stats(start_time, end_time)
        
        # Get communication statistics
        comm_stats = communication_logger.get_aggregated_stats(start_time, end_time)
        
        # Calculate overall health score
        health_score = self._calculate_health_score(health_stats, comm_stats)
        
        # Analyze service status
        service_status = {}
        for service in health_stats.active_services:
            # Simplified service status determination
            if health_stats.failed_health_checks == 0:
                service_status[service] = "healthy"
            elif health_stats.failed_health_checks < 5:
                service_status[service] = "warning"
            else:
                service_status[service] = "critical"
        
        # Collect performance alerts
        performance_alerts = []
        if health_stats.performance_alerts > 0:
            performance_alerts.append({
                "type": "performance_degradation",
                "count": health_stats.performance_alerts,
                "severity": "warning",
                "description": f"{health_stats.performance_alerts} performance degradation events detected"
            })
        
        if health_stats.error_rate > 5:  # More than 5% error rate
            performance_alerts.append({
                "type": "high_error_rate",
                "value": health_stats.error_rate,
                "severity": "critical",
                "description": f"Error rate of {health_stats.error_rate:.1f}% exceeds threshold"
            })
        
        # Identify critical issues
        critical_issues = []
        if health_stats.uptime_percentage < 99:
            critical_issues.append({
                "type": "low_uptime",
                "value": health_stats.uptime_percentage,
                "description": f"System uptime of {health_stats.uptime_percentage:.2f}% below target",
                "impact": "high"
            })
        
        if health_stats.average_response_time_ms > 1000:
            critical_issues.append({
                "type": "slow_response",
                "value": health_stats.average_response_time_ms,
                "description": f"Average response time of {health_stats.average_response_time_ms:.0f}ms exceeds threshold",
                "impact": "medium"
            })
        
        # Generate recommendations
        recommendations = self._generate_health_recommendations(health_stats, comm_stats, critical_issues)
        
        report = SystemHealthReport(
            report_date=target_date,
            overall_health_score=health_score,
            uptime_percentage=health_stats.uptime_percentage,
            average_response_time_ms=health_stats.average_response_time_ms,
            error_rate=health_stats.error_rate,
            service_status=service_status,
            resource_utilization=health_stats.resource_utilization,
            performance_alerts=performance_alerts,
            critical_issues=critical_issues,
            recommendations=recommendations,
            generated_at=datetime.now()
        )
        
        # Cache the report
        self.report_cache[cache_key] = {
            "report": report,
            "cached_at": time.time()
        }
        
        return report
    
    async def generate_popular_trading_pairs_report(
        self,
        target_date: Optional[str] = None
    ) -> PopularTradingPairsReport:
        """
        Generate popular trading pairs analytics report
        Requirements: 9.4 - Popular trading pair analytics
        """
        if target_date is None:
            target_date = datetime.now().strftime("%Y-%m-%d")
        
        cache_key = self._get_cache_key(ReportType.POPULAR_TRADING_PAIRS, ReportPeriod.DAILY, target_date)
        
        if self._is_cache_valid(cache_key):
            return self.report_cache[cache_key]["report"]
        
        # Parse target date
        date_obj = datetime.strptime(target_date, "%Y-%m-%d")
        start_time = date_obj.timestamp()
        end_time = (date_obj + timedelta(days=1)).timestamp()
        
        # Get current day statistics
        current_stats = system_logging_service.get_intent_processing_stats(start_time, end_time)
        
        # Get previous day statistics for comparison
        prev_start = start_time - 86400
        prev_end = start_time
        previous_stats = system_logging_service.get_intent_processing_stats(prev_start, prev_end)
        
        # Process top pairs by volume (estimated)
        top_pairs_by_volume = []
        for pair, count in list(current_stats.popular_tokens.items())[:10]:
            if "->" in pair:
                input_token, output_token = pair.split("->", 1)
                estimated_volume = Decimal(count) * Decimal('100')  # Simplified estimation
                
                top_pairs_by_volume.append({
                    "input_token": input_token,
                    "output_token": output_token,
                    "trade_count": count,
                    "estimated_volume_usd": str(estimated_volume),
                    "volume_rank": len(top_pairs_by_volume) + 1
                })
        
        # Process top pairs by count
        top_pairs_by_count = []
        sorted_pairs = sorted(current_stats.popular_tokens.items(), key=lambda x: x[1], reverse=True)
        for i, (pair, count) in enumerate(sorted_pairs[:10]):
            if "->" in pair:
                input_token, output_token = pair.split("->", 1)
                top_pairs_by_count.append({
                    "input_token": input_token,
                    "output_token": output_token,
                    "trade_count": count,
                    "count_rank": i + 1,
                    "percentage_of_total": (count / current_stats.total_intents * 100) if current_stats.total_intents > 0 else 0
                })
        
        # Identify emerging pairs (new or significantly increased)
        emerging_pairs = []
        for pair, current_count in current_stats.popular_tokens.items():
            previous_count = previous_stats.popular_tokens.get(pair, 0)
            
            if previous_count == 0 and current_count >= 5:  # New pair with significant volume
                if "->" in pair:
                    input_token, output_token = pair.split("->", 1)
                    emerging_pairs.append({
                        "input_token": input_token,
                        "output_token": output_token,
                        "current_count": current_count,
                        "previous_count": previous_count,
                        "growth": "new",
                        "growth_percentage": float('inf')
                    })
            elif previous_count > 0 and current_count > previous_count * 2:  # 100%+ growth
                if "->" in pair:
                    input_token, output_token = pair.split("->", 1)
                    growth_percentage = ((current_count - previous_count) / previous_count) * 100
                    emerging_pairs.append({
                        "input_token": input_token,
                        "output_token": output_token,
                        "current_count": current_count,
                        "previous_count": previous_count,
                        "growth": "increased",
                        "growth_percentage": growth_percentage
                    })
        
        # Identify declining pairs
        declining_pairs = []
        for pair, previous_count in previous_stats.popular_tokens.items():
            current_count = current_stats.popular_tokens.get(pair, 0)
            
            if previous_count >= 5 and current_count < previous_count * 0.5:  # 50%+ decline
                if "->" in pair:
                    input_token, output_token = pair.split("->", 1)
                    decline_percentage = ((previous_count - current_count) / previous_count) * 100
                    declining_pairs.append({
                        "input_token": input_token,
                        "output_token": output_token,
                        "current_count": current_count,
                        "previous_count": previous_count,
                        "decline_percentage": decline_percentage
                    })
        
        # Analyze cross-chain preferences
        cross_chain_preferences = {}
        total_cross_chain = 0
        for chain_pair, count in current_stats.popular_chains.items():
            if "->" in chain_pair:
                source, dest = chain_pair.split("->", 1)
                if source != dest:  # Cross-chain trade
                    total_cross_chain += count
                    cross_chain_preferences[chain_pair] = {
                        "count": count,
                        "percentage": 0  # Will be calculated after total is known
                    }
        
        # Calculate percentages
        for chain_pair in cross_chain_preferences:
            cross_chain_preferences[chain_pair]["percentage"] = (
                cross_chain_preferences[chain_pair]["count"] / total_cross_chain * 100
            ) if total_cross_chain > 0 else 0
        
        # Analyze token popularity
        token_popularity = {}
        for pair in current_stats.popular_tokens:
            if "->" in pair:
                input_token, output_token = pair.split("->", 1)
                
                # Count input token appearances
                if input_token not in token_popularity:
                    token_popularity[input_token] = {"as_input": 0, "as_output": 0, "total": 0}
                token_popularity[input_token]["as_input"] += current_stats.popular_tokens[pair]
                
                # Count output token appearances
                if output_token not in token_popularity:
                    token_popularity[output_token] = {"as_input": 0, "as_output": 0, "total": 0}
                token_popularity[output_token]["as_output"] += current_stats.popular_tokens[pair]
        
        # Calculate totals
        for token in token_popularity:
            token_popularity[token]["total"] = (
                token_popularity[token]["as_input"] + token_popularity[token]["as_output"]
            )
        
        report = PopularTradingPairsReport(
            report_date=target_date,
            top_pairs_by_volume=top_pairs_by_volume,
            top_pairs_by_count=top_pairs_by_count,
            emerging_pairs=emerging_pairs,
            declining_pairs=declining_pairs,
            cross_chain_preferences=cross_chain_preferences,
            token_popularity=token_popularity,
            generated_at=datetime.now()
        )
        
        # Cache the report
        self.report_cache[cache_key] = {
            "report": report,
            "cached_at": time.time()
        }
        
        return report
    
    async def generate_solver_performance_report(
        self,
        target_date: Optional[str] = None
    ) -> SolverPerformanceReport:
        """Generate solver network performance report"""
        if target_date is None:
            target_date = datetime.now().strftime("%Y-%m-%d")
        
        cache_key = self._get_cache_key(ReportType.SOLVER_PERFORMANCE, ReportPeriod.DAILY, target_date)
        
        if self._is_cache_valid(cache_key):
            return self.report_cache[cache_key]["report"]
        
        # Parse target date
        date_obj = datetime.strptime(target_date, "%Y-%m-%d")
        start_time = date_obj.timestamp()
        end_time = (date_obj + timedelta(days=1)).timestamp()
        
        # Get all solver addresses from logs
        solver_addresses = set()
        for log in system_logging_service.solver_logs:
            if start_time <= log.timestamp <= end_time:
                solver_addresses.add(log.solver_address)
        
        # Collect performance stats for each solver
        solver_performances = []
        for solver_address in solver_addresses:
            stats = system_logging_service.get_solver_performance_stats(
                solver_address, start_time, end_time
            )
            solver_performances.append(stats)
        
        # Sort by success rate and volume
        top_performers = sorted(
            solver_performances,
            key=lambda x: (x.success_rate, x.total_volume_processed),
            reverse=True
        )[:10]
        
        # Identify underperformers
        underperformers = [
            solver for solver in solver_performances
            if solver.success_rate < 80 or solver.total_bids > 10  # Active but low success rate
        ][:10]
        
        # Calculate averages
        if solver_performances:
            avg_success_rate = statistics.mean([s.success_rate for s in solver_performances])
            avg_execution_time = statistics.mean([s.average_execution_time_ms for s in solver_performances if s.average_execution_time_ms > 0])
        else:
            avg_success_rate = 0
            avg_execution_time = 0
        
        # Reputation distribution
        reputation_distribution = {
            "excellent": 0,  # > 0.9
            "good": 0,       # 0.8 - 0.9
            "fair": 0,       # 0.7 - 0.8
            "poor": 0        # < 0.7
        }
        
        for solver in solver_performances:
            if solver.average_reputation_score > 0.9:
                reputation_distribution["excellent"] += 1
            elif solver.average_reputation_score > 0.8:
                reputation_distribution["good"] += 1
            elif solver.average_reputation_score > 0.7:
                reputation_distribution["fair"] += 1
            else:
                reputation_distribution["poor"] += 1
        
        # Chain coverage analysis
        chain_coverage = {}
        for solver in solver_performances:
            for chain_id in solver.chains_supported:
                chain_key = f"chain_{chain_id}"
                if chain_key not in chain_coverage:
                    chain_coverage[chain_key] = []
                chain_coverage[chain_key].append(solver.solver_address)
        
        # Volume distribution
        volume_distribution = {}
        for solver in solver_performances:
            volume_distribution[solver.solver_address] = solver.total_volume_processed
        
        report = SolverPerformanceReport(
            report_date=target_date,
            total_active_solvers=len(solver_addresses),
            top_performers=[{
                "solver_address": s.solver_address,
                "success_rate": s.success_rate,
                "total_volume": str(s.total_volume_processed),
                "average_execution_time_ms": s.average_execution_time_ms,
                "reputation_score": s.average_reputation_score,
                "trend": s.recent_performance_trend
            } for s in top_performers],
            underperformers=[{
                "solver_address": s.solver_address,
                "success_rate": s.success_rate,
                "total_bids": s.total_bids,
                "failed_bids": s.failed_bids,
                "issues": "Low success rate" if s.success_rate < 80 else "High failure count"
            } for s in underperformers],
            average_success_rate=avg_success_rate,
            average_execution_time_ms=avg_execution_time,
            reputation_distribution=reputation_distribution,
            chain_coverage=chain_coverage,
            volume_distribution=volume_distribution,
            generated_at=datetime.now()
        )
        
        # Cache the report
        self.report_cache[cache_key] = {
            "report": report,
            "cached_at": time.time()
        }
        
        return report
    
    async def generate_performance_dashboard_data(self) -> PerformanceDashboardData:
        """
        Generate real-time performance dashboard data for operators
        Requirements: 9.4 - Performance dashboards for operators
        """
        current_time = time.time()
        one_hour_ago = current_time - 3600
        one_day_ago = current_time - 86400
        
        # Get current system health
        health_stats = system_logging_service.get_system_health_stats(one_hour_ago, current_time)
        
        # Get intent processing stats
        intent_stats = system_logging_service.get_intent_processing_stats(one_hour_ago, current_time)
        daily_intent_stats = system_logging_service.get_intent_processing_stats(one_day_ago, current_time)
        
        # Get communication stats
        comm_stats = communication_logger.get_aggregated_stats(one_hour_ago, current_time)
        
        # System Overview
        system_overview = {
            "overall_health_score": self._calculate_health_score(health_stats, comm_stats),
            "uptime_percentage": health_stats.uptime_percentage,
            "total_intents_24h": daily_intent_stats.total_intents,
            "success_rate_24h": daily_intent_stats.success_rate,
            "total_volume_24h_usd": str(daily_intent_stats.total_volume_usd),
            "active_solvers": len(set(log.solver_address for log in system_logging_service.solver_logs 
                                   if one_hour_ago <= log.timestamp <= current_time)),
            "supported_chains": len(set(log.source_chain for log in system_logging_service.intent_logs 
                                      if one_hour_ago <= log.timestamp <= current_time))
        }
        
        # Real-time Metrics (last hour)
        real_time_metrics = {
            "intents_per_hour": intent_stats.total_intents,
            "success_rate_1h": intent_stats.success_rate,
            "average_execution_time_ms": intent_stats.average_execution_time_ms,
            "average_gas_used": intent_stats.average_gas_used,
            "error_rate": health_stats.error_rate,
            "average_response_time_ms": health_stats.average_response_time_ms,
            "cross_chain_messages_1h": comm_stats.total_messages,
            "message_success_rate": (comm_stats.successful_messages / comm_stats.total_messages * 100) if comm_stats.total_messages > 0 else 100
        }
        
        # Performance Trends (comparing last hour to previous hour)
        prev_hour_start = one_hour_ago - 3600
        prev_intent_stats = system_logging_service.get_intent_processing_stats(prev_hour_start, one_hour_ago)
        prev_health_stats = system_logging_service.get_system_health_stats(prev_hour_start, one_hour_ago)
        
        performance_trends = {
            "intent_volume_trend": self._calculate_trend(intent_stats.total_intents, prev_intent_stats.total_intents),
            "success_rate_trend": self._calculate_trend(intent_stats.success_rate, prev_intent_stats.success_rate),
            "execution_time_trend": self._calculate_trend(intent_stats.average_execution_time_ms, prev_intent_stats.average_execution_time_ms, inverse=True),
            "error_rate_trend": self._calculate_trend(health_stats.error_rate, prev_health_stats.error_rate, inverse=True),
            "response_time_trend": self._calculate_trend(health_stats.average_response_time_ms, prev_health_stats.average_response_time_ms, inverse=True)
        }
        
        # Alerts and Warnings
        alerts_and_warnings = []
        
        # High error rate alert
        if health_stats.error_rate > 5:
            alerts_and_warnings.append({
                "type": "error_rate",
                "severity": "high" if health_stats.error_rate > 10 else "medium",
                "message": f"Error rate is {health_stats.error_rate:.1f}% (threshold: 5%)",
                "timestamp": current_time,
                "action_required": True
            })
        
        # Low success rate alert
        if intent_stats.success_rate < 90:
            alerts_and_warnings.append({
                "type": "success_rate",
                "severity": "high" if intent_stats.success_rate < 80 else "medium",
                "message": f"Intent success rate is {intent_stats.success_rate:.1f}% (threshold: 90%)",
                "timestamp": current_time,
                "action_required": True
            })
        
        # Slow response time alert
        if health_stats.average_response_time_ms > 1000:
            alerts_and_warnings.append({
                "type": "response_time",
                "severity": "high" if health_stats.average_response_time_ms > 2000 else "medium",
                "message": f"Average response time is {health_stats.average_response_time_ms:.0f}ms (threshold: 1000ms)",
                "timestamp": current_time,
                "action_required": True
            })
        
        # Low uptime alert
        if health_stats.uptime_percentage < 99:
            alerts_and_warnings.append({
                "type": "uptime",
                "severity": "critical" if health_stats.uptime_percentage < 95 else "high",
                "message": f"System uptime is {health_stats.uptime_percentage:.2f}% (threshold: 99%)",
                "timestamp": current_time,
                "action_required": True
            })
        
        # Resource Utilization
        resource_utilization = {
            "cpu_usage": health_stats.resource_utilization.get("cpu_usage", 0),
            "memory_usage": health_stats.resource_utilization.get("memory_usage", 0),
            "disk_usage": health_stats.resource_utilization.get("disk_usage", 0),
            "network_io": health_stats.resource_utilization.get("network_io", 0),
            "database_connections": health_stats.resource_utilization.get("database_connections", 0),
            "active_websockets": health_stats.resource_utilization.get("active_websockets", 0)
        }
        
        # Network Status (cross-chain connectivity)
        network_status = {}
        chain_ids = [1, 137, 42161, 10, 56, 8453]  # Ethereum, Polygon, Arbitrum, Optimism, BSC, Base
        
        for chain_id in chain_ids:
            chain_messages = [log for log in communication_logger.log_entries 
                            if one_hour_ago <= log.timestamp <= current_time and 
                            (log.source_chain == chain_id or log.destination_chain == chain_id)]
            
            successful_messages = len([log for log in chain_messages if log.event_type in [EventType.MESSAGE_RECEIVED, EventType.MESSAGE_VERIFIED]])
            total_messages = len(chain_messages)
            
            network_status[f"chain_{chain_id}"] = {
                "status": "healthy" if total_messages == 0 or (successful_messages / total_messages) > 0.95 else "degraded",
                "success_rate": (successful_messages / total_messages * 100) if total_messages > 0 else 100,
                "message_count": total_messages,
                "last_successful_message": max([log.timestamp for log in chain_messages if log.event_type in [EventType.MESSAGE_RECEIVED, EventType.MESSAGE_VERIFIED]], default=0)
            }
        
        # Solver Network Health
        active_solver_addresses = set(log.solver_address for log in system_logging_service.solver_logs 
                                    if one_hour_ago <= log.timestamp <= current_time)
        
        solver_performances = []
        for solver_address in active_solver_addresses:
            stats = system_logging_service.get_solver_performance_stats(
                solver_address, one_hour_ago, current_time
            )
            solver_performances.append(stats)
        
        healthy_solvers = len([s for s in solver_performances if s.success_rate >= 90])
        total_active_solvers = len(solver_performances)
        
        solver_network_health = {
            "total_active_solvers": total_active_solvers,
            "healthy_solvers": healthy_solvers,
            "health_percentage": (healthy_solvers / total_active_solvers * 100) if total_active_solvers > 0 else 100,
            "average_success_rate": statistics.mean([s.success_rate for s in solver_performances]) if solver_performances else 0,
            "average_execution_time": statistics.mean([s.average_execution_time_ms for s in solver_performances if s.average_execution_time_ms > 0]) if solver_performances else 0,
            "top_performer": max(solver_performances, key=lambda x: x.success_rate).solver_address if solver_performances else None
        }
        
        # Recent Activities (last 10 significant events)
        recent_activities = []
        
        # Get recent intent completions
        recent_completions = [log for log in system_logging_service.intent_logs 
                            if log.event_type == IntentEventType.EXECUTION_COMPLETED and 
                            one_hour_ago <= log.timestamp <= current_time][-5:]
        
        for log in recent_completions:
            recent_activities.append({
                "type": "intent_completed",
                "timestamp": log.timestamp,
                "description": f"Intent {log.intent_id[:8]}... completed in {log.execution_time_ms:.0f}ms",
                "details": {
                    "intent_id": log.intent_id,
                    "execution_time_ms": log.execution_time_ms,
                    "solver_address": log.solver_address,
                    "gas_used": log.gas_used
                }
            })
        
        # Get recent failures
        recent_failures = [log for log in system_logging_service.intent_logs 
                         if log.event_type == IntentEventType.EXECUTION_FAILED and 
                         one_hour_ago <= log.timestamp <= current_time][-3:]
        
        for log in recent_failures:
            recent_activities.append({
                "type": "intent_failed",
                "timestamp": log.timestamp,
                "description": f"Intent {log.intent_id[:8]}... failed: {log.error_message[:50]}...",
                "details": {
                    "intent_id": log.intent_id,
                    "error_message": log.error_message,
                    "solver_address": log.solver_address
                }
            })
        
        # Get recent solver registrations
        recent_registrations = [log for log in system_logging_service.solver_logs 
                              if log.event_type == SolverEventType.SOLVER_REGISTERED and 
                              one_hour_ago <= log.timestamp <= current_time][-2:]
        
        for log in recent_registrations:
            recent_activities.append({
                "type": "solver_registered",
                "timestamp": log.timestamp,
                "description": f"New solver registered: {log.solver_address[:10]}...",
                "details": {
                    "solver_address": log.solver_address,
                    "stake_amount": log.stake_amount
                }
            })
        
        # Sort activities by timestamp (most recent first)
        recent_activities.sort(key=lambda x: x["timestamp"], reverse=True)
        recent_activities = recent_activities[:10]
        
        return PerformanceDashboardData(
            timestamp=datetime.now(),
            system_overview=system_overview,
            real_time_metrics=real_time_metrics,
            performance_trends=performance_trends,
            alerts_and_warnings=alerts_and_warnings,
            resource_utilization=resource_utilization,
            network_status=network_status,
            solver_network_health=solver_network_health,
            recent_activities=recent_activities
        )
    
    def _calculate_trend(self, current_value: float, previous_value: float, inverse: bool = False) -> Dict[str, Any]:
        """Calculate trend information between two values"""
        if previous_value == 0:
            if current_value == 0:
                return {"direction": "stable", "percentage": 0, "status": "neutral"}
            else:
                return {"direction": "up", "percentage": 100, "status": "positive" if not inverse else "negative"}
        
        percentage_change = ((current_value - previous_value) / previous_value) * 100
        
        if abs(percentage_change) < 5:  # Less than 5% change is considered stable
            direction = "stable"
            status = "neutral"
        elif percentage_change > 0:
            direction = "up"
            status = "positive" if not inverse else "negative"
        else:
            direction = "down"
            status = "negative" if not inverse else "positive"
        
        return {
            "direction": direction,
            "percentage": abs(percentage_change),
            "status": status
        }
    
    async def get_dashboard_api_data(self) -> Dict[str, Any]:
        """
        Get dashboard data in API-compatible format for frontend consumption
        Requirements: 9.4 - Performance dashboards for operators
        """
        dashboard_data = await self.generate_performance_dashboard_data()
        
        # Convert to API format
        return {
            "timestamp": dashboard_data.timestamp.isoformat(),
            "system_overview": dashboard_data.system_overview,
            "real_time_metrics": dashboard_data.real_time_metrics,
            "performance_trends": dashboard_data.performance_trends,
            "alerts": dashboard_data.alerts_and_warnings,
            "resource_utilization": dashboard_data.resource_utilization,
            "network_status": dashboard_data.network_status,
            "solver_network": dashboard_data.solver_network_health,
            "recent_activities": dashboard_data.recent_activities
        }
    
    def _calculate_health_score(self, health_stats, comm_stats) -> float:
        """Calculate overall system health score (0-100)"""
        score = 100.0
        
        # Uptime impact (40% of score)
        uptime_score = health_stats.uptime_percentage * 0.4
        
        # Error rate impact (30% of score)
        error_penalty = min(health_stats.error_rate * 3, 30)  # Max 30 point penalty
        error_score = max(0, 30 - error_penalty)
        
        # Response time impact (20% of score)
        response_penalty = min(health_stats.average_response_time_ms / 50, 20)  # 1 point per 50ms
        response_score = max(0, 20 - response_penalty)
        
        # Communication success impact (10% of score)
        comm_success_rate = (comm_stats.successful_messages / comm_stats.total_messages * 100) if comm_stats.total_messages > 0 else 100
        comm_score = comm_success_rate * 0.1
        
        total_score = uptime_score + error_score + response_score + comm_score
        return min(100.0, max(0.0, total_score))
        """Calculate overall system health score (0-100)"""
        score = 100.0
        
        # Uptime impact (40% of score)
        uptime_score = health_stats.uptime_percentage * 0.4
        
        # Error rate impact (30% of score)
        error_penalty = min(health_stats.error_rate * 3, 30)  # Max 30 point penalty
        error_score = max(0, 30 - error_penalty)
        
        # Response time impact (20% of score)
        response_penalty = min(health_stats.average_response_time_ms / 50, 20)  # 1 point per 50ms
        response_score = max(0, 20 - response_penalty)
        
        # Communication success impact (10% of score)
        comm_success_rate = (comm_stats.successful_messages / comm_stats.total_messages * 100) if comm_stats.total_messages > 0 else 100
        comm_score = comm_success_rate * 0.1
        
        total_score = uptime_score + error_score + response_score + comm_score
        return min(100.0, max(0.0, total_score))
    
    def _generate_health_recommendations(self, health_stats, comm_stats, critical_issues) -> List[str]:
        """Generate health improvement recommendations"""
        recommendations = []
        
        if health_stats.uptime_percentage < 99:
            recommendations.append("Investigate and resolve service availability issues to improve uptime")
        
        if health_stats.error_rate > 5:
            recommendations.append("Review error logs and implement fixes to reduce error rate")
        
        if health_stats.average_response_time_ms > 1000:
            recommendations.append("Optimize service performance to reduce response times")
        
        if health_stats.performance_alerts > 10:
            recommendations.append("Address performance degradation alerts to maintain service quality")
        
        if comm_stats.failed_messages > comm_stats.successful_messages * 0.1:
            recommendations.append("Improve cross-chain communication reliability")
        
        if len(critical_issues) == 0 and health_stats.uptime_percentage > 99.5:
            recommendations.append("System is performing well - maintain current monitoring and maintenance practices")
        
        return recommendations
    
    async def export_report(
        self,
        report: Any,
        format_type: str = "json"
    ) -> str:
        """Export report in specified format"""
        if format_type.lower() == "json":
            return json.dumps(asdict(report), indent=2, default=str)
        elif format_type.lower() == "csv":
            # Simplified CSV export for trading volume report
            if isinstance(report, TradingVolumeReport):
                lines = ["date,total_volume_usd,total_intents,success_rate,average_trade_size"]
                lines.append(f"{report.report_date},{report.total_volume_usd},{report.total_intents},{report.success_rate},{report.average_trade_size_usd}")
                return "\n".join(lines)
            else:
                raise ValueError("CSV export not supported for this report type")
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
    
    def clear_cache(self):
        """Clear report cache"""
        self.report_cache.clear()


# Global instance
analytics_reporting_service = AnalyticsReportingService()