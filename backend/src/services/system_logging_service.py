"""
Comprehensive System Logging Service
Implements detailed intent processing logs, solver performance tracking, and system health monitoring
Requirements: 9.1, 9.3 - Intent processing logging and solver performance tracking
"""
import asyncio
import json
import logging
import time
import uuid
from typing import Dict, Optional, List, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import statistics

from src.services.communication_logger import communication_logger, LogLevel


class IntentEventType(Enum):
    """Types of intent processing events"""
    INTENT_CREATED = "intent_created"
    INTENT_VALIDATED = "intent_validated"
    INTENT_SUBMITTED = "intent_submitted"
    SOLVER_SELECTED = "solver_selected"
    FUNDS_LOCKED = "funds_locked"
    EXECUTION_STARTED = "execution_started"
    EXECUTION_COMPLETED = "execution_completed"
    EXECUTION_FAILED = "execution_failed"
    FUNDS_RELEASED = "funds_released"
    INTENT_CANCELLED = "intent_cancelled"
    INTENT_REFUNDED = "intent_refunded"


class SolverEventType(Enum):
    """Types of solver performance events"""
    SOLVER_REGISTERED = "solver_registered"
    SOLVER_DEREGISTERED = "solver_deregistered"
    BID_SUBMITTED = "bid_submitted"
    BID_SELECTED = "bid_selected"
    BID_REJECTED = "bid_rejected"
    FULFILLMENT_STARTED = "fulfillment_started"
    FULFILLMENT_COMPLETED = "fulfillment_completed"
    FULFILLMENT_FAILED = "fulfillment_failed"
    REPUTATION_UPDATED = "reputation_updated"
    SOLVER_SLASHED = "solver_slashed"


class SystemEventType(Enum):
    """Types of system health events"""
    SERVICE_STARTED = "service_started"
    SERVICE_STOPPED = "service_stopped"
    HEALTH_CHECK_PASSED = "health_check_passed"
    HEALTH_CHECK_FAILED = "health_check_failed"
    RESOURCE_THRESHOLD_EXCEEDED = "resource_threshold_exceeded"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    SCALING_EVENT = "scaling_event"
    ERROR_RATE_SPIKE = "error_rate_spike"


@dataclass
class IntentLogEntry:
    """Log entry for intent processing events"""
    id: str
    timestamp: float
    event_type: IntentEventType
    intent_id: str
    user_address: str
    source_chain: int
    destination_chain: int
    input_token: str
    output_token: str
    input_amount: str
    minimum_output_amount: str
    log_level: LogLevel = LogLevel.INFO
    execution_time_ms: Optional[float] = None
    gas_used: Optional[int] = None
    fees_paid: Optional[str] = None
    solver_address: Optional[str] = None
    error_message: Optional[str] = None
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}


@dataclass
class SolverLogEntry:
    """Log entry for solver performance events"""
    id: str
    timestamp: float
    event_type: SolverEventType
    solver_address: str
    intent_id: Optional[str] = None
    chain_id: Optional[int] = None
    log_level: LogLevel = LogLevel.INFO
    execution_time_ms: Optional[float] = None
    bid_amount: Optional[str] = None
    success: Optional[bool] = None
    reputation_score: Optional[float] = None
    stake_amount: Optional[str] = None
    error_message: Optional[str] = None
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}


@dataclass
class SystemLogEntry:
    """Log entry for system health events"""
    id: str
    timestamp: float
    event_type: SystemEventType
    service_name: str
    log_level: LogLevel = LogLevel.INFO
    metric_name: Optional[str] = None
    metric_value: Optional[float] = None
    threshold_value: Optional[float] = None
    error_message: Optional[str] = None
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}


@dataclass
class IntentProcessingStats:
    """Aggregated intent processing statistics"""
    total_intents: int
    successful_intents: int
    failed_intents: int
    cancelled_intents: int
    average_execution_time_ms: float
    average_gas_used: float
    total_volume_usd: Decimal
    success_rate: float
    popular_chains: Dict[str, int]
    popular_tokens: Dict[str, int]
    failure_reasons: Dict[str, int]
    time_period: Dict[str, float]


@dataclass
class SolverPerformanceStats:
    """Aggregated solver performance statistics"""
    solver_address: str
    total_bids: int
    successful_bids: int
    failed_bids: int
    average_execution_time_ms: float
    total_volume_processed: Decimal
    success_rate: float
    average_reputation_score: float
    chains_supported: List[int]
    recent_performance_trend: str  # "improving", "stable", "declining"
    time_period: Dict[str, float]


@dataclass
class SystemHealthStats:
    """System health statistics"""
    uptime_percentage: float
    average_response_time_ms: float
    error_rate: float
    resource_utilization: Dict[str, float]
    active_services: List[str]
    failed_health_checks: int
    performance_alerts: int
    time_period: Dict[str, float]


class SystemLoggingService:
    """Comprehensive system logging service"""
    
    def __init__(self, max_log_entries: int = 50000):
        self.intent_logs: List[IntentLogEntry] = []
        self.solver_logs: List[SolverLogEntry] = []
        self.system_logs: List[SystemLogEntry] = []
        self.max_log_entries = max_log_entries
        self._setup_loggers()
    
    def _setup_loggers(self):
        """Set up specialized loggers for different event types"""
        # Intent processing logger
        self.intent_logger = logging.getLogger("crossflow.intents")
        self.intent_logger.setLevel(logging.INFO)
        
        # Solver performance logger
        self.solver_logger = logging.getLogger("crossflow.solvers")
        self.solver_logger.setLevel(logging.INFO)
        
        # System health logger
        self.system_logger = logging.getLogger("crossflow.system")
        self.system_logger.setLevel(logging.INFO)
        
        # Set up formatters
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Add handlers if not present
        for logger in [self.intent_logger, self.solver_logger, self.system_logger]:
            if not logger.handlers:
                handler = logging.StreamHandler()
                handler.setFormatter(formatter)
                logger.addHandler(handler)
    
    def generate_log_id(self) -> str:
        """Generate unique log entry ID"""
        return str(uuid.uuid4())
    
    # Intent Processing Logging Methods
    
    def log_intent_created(
        self,
        intent_id: str,
        user_address: str,
        source_chain: int,
        destination_chain: int,
        input_token: str,
        output_token: str,
        input_amount: str,
        minimum_output_amount: str,
        details: Optional[Dict] = None
    ):
        """Log intent creation event"""
        entry = IntentLogEntry(
            id=self.generate_log_id(),
            timestamp=time.time(),
            event_type=IntentEventType.INTENT_CREATED,
            intent_id=intent_id,
            user_address=user_address,
            source_chain=source_chain,
            destination_chain=destination_chain,
            input_token=input_token,
            output_token=output_token,
            input_amount=input_amount,
            minimum_output_amount=minimum_output_amount,
            details=details or {}
        )
        
        self._add_intent_log(entry)
        
        self.intent_logger.info(
            f"Intent created: {intent_id} - {input_amount} {input_token} -> {output_token}",
            extra={
                "intent_id": intent_id,
                "user_address": user_address,
                "source_chain": source_chain,
                "destination_chain": destination_chain,
                "input_amount": input_amount,
                "minimum_output_amount": minimum_output_amount
            }
        )
    
    def log_intent_execution_completed(
        self,
        intent_id: str,
        execution_time_ms: float,
        gas_used: int,
        fees_paid: str,
        solver_address: str,
        output_amount: str,
        details: Optional[Dict] = None
    ):
        """Log successful intent execution completion"""
        entry = IntentLogEntry(
            id=self.generate_log_id(),
            timestamp=time.time(),
            event_type=IntentEventType.EXECUTION_COMPLETED,
            intent_id=intent_id,
            user_address="",  # Will be filled from intent lookup
            source_chain=0,   # Will be filled from intent lookup
            destination_chain=0,  # Will be filled from intent lookup
            input_token="",   # Will be filled from intent lookup
            output_token="",  # Will be filled from intent lookup
            input_amount="",  # Will be filled from intent lookup
            minimum_output_amount="",  # Will be filled from intent lookup
            execution_time_ms=execution_time_ms,
            gas_used=gas_used,
            fees_paid=fees_paid,
            solver_address=solver_address,
            details={**(details or {}), "output_amount": output_amount}
        )
        
        self._add_intent_log(entry)
        
        self.intent_logger.info(
            f"Intent execution completed: {intent_id} in {execution_time_ms:.2f}ms",
            extra={
                "intent_id": intent_id,
                "execution_time_ms": execution_time_ms,
                "gas_used": gas_used,
                "fees_paid": fees_paid,
                "solver_address": solver_address,
                "output_amount": output_amount
            }
        )
    
    def log_intent_execution_failed(
        self,
        intent_id: str,
        error_message: str,
        execution_time_ms: Optional[float] = None,
        solver_address: Optional[str] = None,
        details: Optional[Dict] = None
    ):
        """Log failed intent execution"""
        entry = IntentLogEntry(
            id=self.generate_log_id(),
            timestamp=time.time(),
            event_type=IntentEventType.EXECUTION_FAILED,
            intent_id=intent_id,
            user_address="",  # Will be filled from intent lookup
            source_chain=0,   # Will be filled from intent lookup
            destination_chain=0,  # Will be filled from intent lookup
            input_token="",   # Will be filled from intent lookup
            output_token="",  # Will be filled from intent lookup
            input_amount="",  # Will be filled from intent lookup
            minimum_output_amount="",  # Will be filled from intent lookup
            log_level=LogLevel.ERROR,
            execution_time_ms=execution_time_ms,
            solver_address=solver_address,
            error_message=error_message,
            details=details or {}
        )
        
        self._add_intent_log(entry)
        
        self.intent_logger.error(
            f"Intent execution failed: {intent_id} - {error_message}",
            extra={
                "intent_id": intent_id,
                "error_message": error_message,
                "execution_time_ms": execution_time_ms,
                "solver_address": solver_address
            }
        )
    
    # Solver Performance Logging Methods
    
    def log_solver_bid_submitted(
        self,
        solver_address: str,
        intent_id: str,
        bid_amount: str,
        chain_id: int,
        details: Optional[Dict] = None
    ):
        """Log solver bid submission"""
        entry = SolverLogEntry(
            id=self.generate_log_id(),
            timestamp=time.time(),
            event_type=SolverEventType.BID_SUBMITTED,
            solver_address=solver_address,
            intent_id=intent_id,
            chain_id=chain_id,
            bid_amount=bid_amount,
            details=details or {}
        )
        
        self._add_solver_log(entry)
        
        self.solver_logger.info(
            f"Solver bid submitted: {solver_address} bid {bid_amount} for {intent_id}",
            extra={
                "solver_address": solver_address,
                "intent_id": intent_id,
                "bid_amount": bid_amount,
                "chain_id": chain_id
            }
        )
    
    def log_solver_fulfillment_completed(
        self,
        solver_address: str,
        intent_id: str,
        execution_time_ms: float,
        success: bool,
        details: Optional[Dict] = None
    ):
        """Log solver fulfillment completion"""
        entry = SolverLogEntry(
            id=self.generate_log_id(),
            timestamp=time.time(),
            event_type=SolverEventType.FULFILLMENT_COMPLETED if success else SolverEventType.FULFILLMENT_FAILED,
            solver_address=solver_address,
            intent_id=intent_id,
            log_level=LogLevel.INFO if success else LogLevel.ERROR,
            execution_time_ms=execution_time_ms,
            success=success,
            details=details or {}
        )
        
        self._add_solver_log(entry)
        
        log_method = self.solver_logger.info if success else self.solver_logger.error
        status = "completed" if success else "failed"
        log_method(
            f"Solver fulfillment {status}: {solver_address} - {intent_id} in {execution_time_ms:.2f}ms",
            extra={
                "solver_address": solver_address,
                "intent_id": intent_id,
                "execution_time_ms": execution_time_ms,
                "success": success
            }
        )
    
    def log_solver_reputation_updated(
        self,
        solver_address: str,
        old_reputation: float,
        new_reputation: float,
        reason: str,
        details: Optional[Dict] = None
    ):
        """Log solver reputation update"""
        entry = SolverLogEntry(
            id=self.generate_log_id(),
            timestamp=time.time(),
            event_type=SolverEventType.REPUTATION_UPDATED,
            solver_address=solver_address,
            reputation_score=new_reputation,
            details={
                **(details or {}),
                "old_reputation": old_reputation,
                "reason": reason
            }
        )
        
        self._add_solver_log(entry)
        
        self.solver_logger.info(
            f"Solver reputation updated: {solver_address} {old_reputation:.3f} -> {new_reputation:.3f} ({reason})",
            extra={
                "solver_address": solver_address,
                "old_reputation": old_reputation,
                "new_reputation": new_reputation,
                "reason": reason
            }
        )
    
    # System Health Logging Methods
    
    def log_system_health_check(
        self,
        service_name: str,
        passed: bool,
        response_time_ms: float,
        details: Optional[Dict] = None
    ):
        """Log service health check result"""
        entry = SystemLogEntry(
            id=self.generate_log_id(),
            timestamp=time.time(),
            event_type=SystemEventType.HEALTH_CHECK_PASSED if passed else SystemEventType.HEALTH_CHECK_FAILED,
            service_name=service_name,
            log_level=LogLevel.INFO if passed else LogLevel.WARNING,
            metric_name="response_time_ms",
            metric_value=response_time_ms,
            details=details or {}
        )
        
        self._add_system_log(entry)
        
        log_method = self.system_logger.info if passed else self.system_logger.warning
        status = "passed" if passed else "failed"
        log_method(
            f"Health check {status}: {service_name} - {response_time_ms:.2f}ms",
            extra={
                "service_name": service_name,
                "health_check_passed": passed,
                "response_time_ms": response_time_ms
            }
        )
    
    def log_resource_threshold_exceeded(
        self,
        service_name: str,
        metric_name: str,
        current_value: float,
        threshold_value: float,
        details: Optional[Dict] = None
    ):
        """Log resource threshold exceeded event"""
        entry = SystemLogEntry(
            id=self.generate_log_id(),
            timestamp=time.time(),
            event_type=SystemEventType.RESOURCE_THRESHOLD_EXCEEDED,
            service_name=service_name,
            log_level=LogLevel.WARNING,
            metric_name=metric_name,
            metric_value=current_value,
            threshold_value=threshold_value,
            details=details or {}
        )
        
        self._add_system_log(entry)
        
        self.system_logger.warning(
            f"Resource threshold exceeded: {service_name} {metric_name} = {current_value} > {threshold_value}",
            extra={
                "service_name": service_name,
                "metric_name": metric_name,
                "current_value": current_value,
                "threshold_value": threshold_value
            }
        )
    
    def log_performance_degradation(
        self,
        service_name: str,
        metric_name: str,
        current_value: float,
        baseline_value: float,
        degradation_percentage: float,
        details: Optional[Dict] = None
    ):
        """Log performance degradation event"""
        entry = SystemLogEntry(
            id=self.generate_log_id(),
            timestamp=time.time(),
            event_type=SystemEventType.PERFORMANCE_DEGRADATION,
            service_name=service_name,
            log_level=LogLevel.WARNING,
            metric_name=metric_name,
            metric_value=current_value,
            details={
                **(details or {}),
                "baseline_value": baseline_value,
                "degradation_percentage": degradation_percentage
            }
        )
        
        self._add_system_log(entry)
        
        self.system_logger.warning(
            f"Performance degradation: {service_name} {metric_name} degraded by {degradation_percentage:.1f}%",
            extra={
                "service_name": service_name,
                "metric_name": metric_name,
                "current_value": current_value,
                "baseline_value": baseline_value,
                "degradation_percentage": degradation_percentage
            }
        )
    
    # Log Management Methods
    
    def _add_intent_log(self, entry: IntentLogEntry):
        """Add intent log entry to storage"""
        self.intent_logs.append(entry)
        if len(self.intent_logs) > self.max_log_entries:
            self.intent_logs = self.intent_logs[-self.max_log_entries:]
    
    def _add_solver_log(self, entry: SolverLogEntry):
        """Add solver log entry to storage"""
        self.solver_logs.append(entry)
        if len(self.solver_logs) > self.max_log_entries:
            self.solver_logs = self.solver_logs[-self.max_log_entries:]
    
    def _add_system_log(self, entry: SystemLogEntry):
        """Add system log entry to storage"""
        self.system_logs.append(entry)
        if len(self.system_logs) > self.max_log_entries:
            self.system_logs = self.system_logs[-self.max_log_entries:]
    
    # Analytics and Reporting Methods
    
    def get_intent_processing_stats(
        self,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> IntentProcessingStats:
        """Get aggregated intent processing statistics"""
        if start_time is None:
            start_time = time.time() - 3600  # Last hour
        if end_time is None:
            end_time = time.time()
        
        # Filter logs by time range
        logs = [
            e for e in self.intent_logs
            if start_time <= e.timestamp <= end_time
        ]
        
        if not logs:
            return IntentProcessingStats(
                total_intents=0,
                successful_intents=0,
                failed_intents=0,
                cancelled_intents=0,
                average_execution_time_ms=0,
                average_gas_used=0,
                total_volume_usd=Decimal('0'),
                success_rate=0,
                popular_chains={},
                popular_tokens={},
                failure_reasons={},
                time_period={"start": start_time, "end": end_time}
            )
        
        # Calculate statistics
        created_intents = [e for e in logs if e.event_type == IntentEventType.INTENT_CREATED]
        completed_intents = [e for e in logs if e.event_type == IntentEventType.EXECUTION_COMPLETED]
        failed_intents = [e for e in logs if e.event_type == IntentEventType.EXECUTION_FAILED]
        cancelled_intents = [e for e in logs if e.event_type == IntentEventType.INTENT_CANCELLED]
        
        total_intents = len(created_intents)
        successful_intents = len(completed_intents)
        failed_intents_count = len(failed_intents)
        cancelled_intents_count = len(cancelled_intents)
        
        # Execution times
        execution_times = [e.execution_time_ms for e in completed_intents if e.execution_time_ms is not None]
        avg_execution_time = statistics.mean(execution_times) if execution_times else 0
        
        # Gas usage
        gas_usage = [e.gas_used for e in completed_intents if e.gas_used is not None]
        avg_gas_used = statistics.mean(gas_usage) if gas_usage else 0
        
        # Volume calculation (simplified - would need price data in production)
        total_volume = Decimal('0')
        for intent in created_intents:
            try:
                amount = Decimal(intent.input_amount)
                # Assume $1 per token for simplification
                total_volume += amount
            except:
                continue
        
        # Success rate
        success_rate = (successful_intents / total_intents * 100) if total_intents > 0 else 0
        
        # Popular chains
        popular_chains = {}
        for intent in created_intents:
            chain_pair = f"{intent.source_chain}->{intent.destination_chain}"
            popular_chains[chain_pair] = popular_chains.get(chain_pair, 0) + 1
        
        # Popular tokens
        popular_tokens = {}
        for intent in created_intents:
            token_pair = f"{intent.input_token}->{intent.output_token}"
            popular_tokens[token_pair] = popular_tokens.get(token_pair, 0) + 1
        
        # Failure reasons
        failure_reasons = {}
        for intent in failed_intents:
            if intent.error_message:
                # Categorize errors
                if "timeout" in intent.error_message.lower():
                    reason = "timeout"
                elif "liquidity" in intent.error_message.lower():
                    reason = "insufficient_liquidity"
                elif "gas" in intent.error_message.lower():
                    reason = "gas_issues"
                elif "slippage" in intent.error_message.lower():
                    reason = "slippage"
                else:
                    reason = "other"
                
                failure_reasons[reason] = failure_reasons.get(reason, 0) + 1
        
        return IntentProcessingStats(
            total_intents=total_intents,
            successful_intents=successful_intents,
            failed_intents=failed_intents_count,
            cancelled_intents=cancelled_intents_count,
            average_execution_time_ms=avg_execution_time,
            average_gas_used=avg_gas_used,
            total_volume_usd=total_volume,
            success_rate=success_rate,
            popular_chains=popular_chains,
            popular_tokens=popular_tokens,
            failure_reasons=failure_reasons,
            time_period={"start": start_time, "end": end_time}
        )
    
    def get_solver_performance_stats(
        self,
        solver_address: str,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> SolverPerformanceStats:
        """Get performance statistics for a specific solver"""
        if start_time is None:
            start_time = time.time() - 86400  # Last 24 hours
        if end_time is None:
            end_time = time.time()
        
        # Filter logs for this solver and time range
        logs = [
            e for e in self.solver_logs
            if (e.solver_address == solver_address and
                start_time <= e.timestamp <= end_time)
        ]
        
        if not logs:
            return SolverPerformanceStats(
                solver_address=solver_address,
                total_bids=0,
                successful_bids=0,
                failed_bids=0,
                average_execution_time_ms=0,
                total_volume_processed=Decimal('0'),
                success_rate=0,
                average_reputation_score=0,
                chains_supported=[],
                recent_performance_trend="stable",
                time_period={"start": start_time, "end": end_time}
            )
        
        # Calculate statistics
        bid_logs = [e for e in logs if e.event_type == SolverEventType.BID_SUBMITTED]
        completed_logs = [e for e in logs if e.event_type == SolverEventType.FULFILLMENT_COMPLETED]
        failed_logs = [e for e in logs if e.event_type == SolverEventType.FULFILLMENT_FAILED]
        
        total_bids = len(bid_logs)
        successful_bids = len(completed_logs)
        failed_bids = len(failed_logs)
        
        # Execution times
        execution_times = [e.execution_time_ms for e in completed_logs if e.execution_time_ms is not None]
        avg_execution_time = statistics.mean(execution_times) if execution_times else 0
        
        # Volume processed (simplified)
        total_volume = Decimal('0')
        for log in bid_logs:
            if log.bid_amount:
                try:
                    total_volume += Decimal(log.bid_amount)
                except:
                    continue
        
        # Success rate
        total_fulfillments = successful_bids + failed_bids
        success_rate = (successful_bids / total_fulfillments * 100) if total_fulfillments > 0 else 0
        
        # Average reputation
        reputation_logs = [e for e in logs if e.event_type == SolverEventType.REPUTATION_UPDATED]
        if reputation_logs:
            avg_reputation = statistics.mean([e.reputation_score for e in reputation_logs if e.reputation_score is not None])
        else:
            avg_reputation = 0
        
        # Chains supported
        chains_supported = list(set([e.chain_id for e in logs if e.chain_id is not None]))
        
        # Performance trend (simplified analysis)
        if len(completed_logs) >= 10:
            # Split into two halves and compare success rates
            mid_point = len(completed_logs) // 2
            first_half_success = len([e for e in completed_logs[:mid_point] if e.success])
            second_half_success = len([e for e in completed_logs[mid_point:] if e.success])
            
            first_half_rate = first_half_success / mid_point if mid_point > 0 else 0
            second_half_rate = second_half_success / (len(completed_logs) - mid_point) if (len(completed_logs) - mid_point) > 0 else 0
            
            if second_half_rate > first_half_rate + 0.1:
                trend = "improving"
            elif second_half_rate < first_half_rate - 0.1:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "stable"
        
        return SolverPerformanceStats(
            solver_address=solver_address,
            total_bids=total_bids,
            successful_bids=successful_bids,
            failed_bids=failed_bids,
            average_execution_time_ms=avg_execution_time,
            total_volume_processed=total_volume,
            success_rate=success_rate,
            average_reputation_score=avg_reputation,
            chains_supported=chains_supported,
            recent_performance_trend=trend,
            time_period={"start": start_time, "end": end_time}
        )
    
    def get_system_health_stats(
        self,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> SystemHealthStats:
        """Get system health statistics"""
        if start_time is None:
            start_time = time.time() - 3600  # Last hour
        if end_time is None:
            end_time = time.time()
        
        # Filter logs by time range
        logs = [
            e for e in self.system_logs
            if start_time <= e.timestamp <= end_time
        ]
        
        if not logs:
            return SystemHealthStats(
                uptime_percentage=100.0,
                average_response_time_ms=0,
                error_rate=0,
                resource_utilization={},
                active_services=[],
                failed_health_checks=0,
                performance_alerts=0,
                time_period={"start": start_time, "end": end_time}
            )
        
        # Calculate statistics
        health_check_logs = [e for e in logs if e.event_type in [SystemEventType.HEALTH_CHECK_PASSED, SystemEventType.HEALTH_CHECK_FAILED]]
        passed_checks = [e for e in health_check_logs if e.event_type == SystemEventType.HEALTH_CHECK_PASSED]
        failed_checks = [e for e in health_check_logs if e.event_type == SystemEventType.HEALTH_CHECK_FAILED]
        
        # Uptime percentage
        total_checks = len(health_check_logs)
        uptime_percentage = (len(passed_checks) / total_checks * 100) if total_checks > 0 else 100.0
        
        # Average response time
        response_times = [e.metric_value for e in passed_checks if e.metric_value is not None]
        avg_response_time = statistics.mean(response_times) if response_times else 0
        
        # Error rate
        error_logs = [e for e in logs if e.log_level in [LogLevel.ERROR, LogLevel.CRITICAL]]
        error_rate = (len(error_logs) / len(logs) * 100) if logs else 0
        
        # Resource utilization (simplified)
        resource_logs = [e for e in logs if e.event_type == SystemEventType.RESOURCE_THRESHOLD_EXCEEDED]
        resource_utilization = {}
        for log in resource_logs:
            if log.metric_name and log.metric_value is not None:
                resource_utilization[log.metric_name] = log.metric_value
        
        # Active services
        active_services = list(set([e.service_name for e in logs]))
        
        # Performance alerts
        performance_alerts = len([e for e in logs if e.event_type == SystemEventType.PERFORMANCE_DEGRADATION])
        
        return SystemHealthStats(
            uptime_percentage=uptime_percentage,
            average_response_time_ms=avg_response_time,
            error_rate=error_rate,
            resource_utilization=resource_utilization,
            active_services=active_services,
            failed_health_checks=len(failed_checks),
            performance_alerts=performance_alerts,
            time_period={"start": start_time, "end": end_time}
        )
    
    def export_logs(
        self,
        log_type: str = "all",
        format_type: str = "json",
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> str:
        """Export logs in specified format"""
        logs_to_export = []
        
        if log_type in ["all", "intents"]:
            filtered_intent_logs = [
                e for e in self.intent_logs
                if (start_time is None or e.timestamp >= start_time) and
                   (end_time is None or e.timestamp <= end_time)
            ]
            logs_to_export.extend([{"type": "intent", **asdict(log)} for log in filtered_intent_logs])
        
        if log_type in ["all", "solvers"]:
            filtered_solver_logs = [
                e for e in self.solver_logs
                if (start_time is None or e.timestamp >= start_time) and
                   (end_time is None or e.timestamp <= end_time)
            ]
            logs_to_export.extend([{"type": "solver", **asdict(log)} for log in filtered_solver_logs])
        
        if log_type in ["all", "system"]:
            filtered_system_logs = [
                e for e in self.system_logs
                if (start_time is None or e.timestamp >= start_time) and
                   (end_time is None or e.timestamp <= end_time)
            ]
            logs_to_export.extend([{"type": "system", **asdict(log)} for log in filtered_system_logs])
        
        # Sort by timestamp
        logs_to_export.sort(key=lambda x: x["timestamp"])
        
        if format_type.lower() == "json":
            return json.dumps(logs_to_export, indent=2, default=str)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
    
    def clear_logs(self, log_type: str = "all", older_than_seconds: Optional[int] = None):
        """Clear log entries"""
        cutoff_time = time.time() - older_than_seconds if older_than_seconds else 0
        
        if log_type in ["all", "intents"]:
            if older_than_seconds:
                self.intent_logs = [e for e in self.intent_logs if e.timestamp > cutoff_time]
            else:
                self.intent_logs.clear()
        
        if log_type in ["all", "solvers"]:
            if older_than_seconds:
                self.solver_logs = [e for e in self.solver_logs if e.timestamp > cutoff_time]
            else:
                self.solver_logs.clear()
        
        if log_type in ["all", "system"]:
            if older_than_seconds:
                self.system_logs = [e for e in self.system_logs if e.timestamp > cutoff_time]
            else:
                self.system_logs.clear()


# Global instance
system_logging_service = SystemLoggingService()