"""
Cross-chain communication logging service
Implements comprehensive audit logging for Requirements 2.5
"""
import asyncio
import json
import logging
import time
from typing import Dict, Optional, List, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timezone
import uuid


logger = logging.getLogger(__name__)


class LogLevel(Enum):
    """Log levels for communication events"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MessageType(Enum):
    """Types of cross-chain messages"""
    INTENT_BROADCAST = "intent_broadcast"
    SOLVER_BID = "solver_bid"
    EXECUTION_PROOF = "execution_proof"
    FUND_RELEASE = "fund_release"
    STATUS_UPDATE = "status_update"
    VERIFICATION = "verification"


class EventType(Enum):
    """Types of communication events"""
    MESSAGE_SENT = "message_sent"
    MESSAGE_RECEIVED = "message_received"
    MESSAGE_VERIFIED = "message_verified"
    MESSAGE_FAILED = "message_failed"
    RETRY_ATTEMPTED = "retry_attempted"
    CIRCUIT_BREAKER_OPENED = "circuit_breaker_opened"
    CIRCUIT_BREAKER_CLOSED = "circuit_breaker_closed"
    PROTOCOL_SELECTED = "protocol_selected"


@dataclass
class CommunicationLogEntry:
    """Structured log entry for cross-chain communication"""
    id: str
    timestamp: float
    event_type: EventType
    message_type: MessageType
    protocol: str
    source_chain: int
    destination_chain: int
    message_id: Optional[str] = None
    operation_id: Optional[str] = None
    log_level: LogLevel = LogLevel.INFO
    details: Dict[str, Any] = None
    error_message: Optional[str] = None
    execution_time_ms: Optional[float] = None
    retry_attempt: Optional[int] = None
    gas_used: Optional[int] = None
    fee_paid: Optional[str] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}


@dataclass
class AlertConfig:
    """Configuration for alerting on communication events"""
    event_types: List[EventType]
    threshold_count: int
    time_window_seconds: int
    alert_channels: List[str]  # email, slack, webhook, etc.


@dataclass
class LogAggregation:
    """Aggregated log statistics"""
    total_messages: int
    successful_messages: int
    failed_messages: int
    average_execution_time: float
    protocols_used: Dict[str, int]
    chains_used: Dict[str, int]
    error_types: Dict[str, int]
    time_period: Dict[str, float]


class CommunicationLogger:
    """Service for logging cross-chain communication events"""
    
    def __init__(self, max_log_entries: int = 10000):
        self.log_entries: List[CommunicationLogEntry] = []
        self.max_log_entries = max_log_entries
        self.alert_configs: List[AlertConfig] = []
        self.alert_history: List[Dict] = []
        self._setup_structured_logging()
    
    def _setup_structured_logging(self):
        """Set up structured logging configuration"""
        # Configure structured logger for cross-chain communications
        self.structured_logger = logging.getLogger("crosschain.communication")
        self.structured_logger.setLevel(logging.INFO)
        
        # Create formatter for structured logs
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Add handler if not already present
        if not self.structured_logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            self.structured_logger.addHandler(handler)
    
    def generate_log_id(self) -> str:
        """Generate unique log entry ID"""
        return str(uuid.uuid4())
    
    def log_message_sent(
        self,
        message_type: MessageType,
        protocol: str,
        source_chain: int,
        destination_chain: int,
        message_id: str,
        operation_id: str,
        details: Optional[Dict] = None,
        execution_time_ms: Optional[float] = None,
        fee_paid: Optional[str] = None
    ):
        """Log a message being sent"""
        entry = CommunicationLogEntry(
            id=self.generate_log_id(),
            timestamp=time.time(),
            event_type=EventType.MESSAGE_SENT,
            message_type=message_type,
            protocol=protocol,
            source_chain=source_chain,
            destination_chain=destination_chain,
            message_id=message_id,
            operation_id=operation_id,
            log_level=LogLevel.INFO,
            details=details or {},
            execution_time_ms=execution_time_ms,
            fee_paid=fee_paid
        )
        
        self._add_log_entry(entry)
        
        # Structured logging
        self.structured_logger.info(
            f"Message sent: {message_type.value} via {protocol} "
            f"from chain {source_chain} to {destination_chain}",
            extra={
                "event_type": "message_sent",
                "message_id": message_id,
                "protocol": protocol,
                "source_chain": source_chain,
                "destination_chain": destination_chain,
                "execution_time_ms": execution_time_ms,
                "fee_paid": fee_paid
            }
        )
    
    def log_message_received(
        self,
        message_type: MessageType,
        protocol: str,
        source_chain: int,
        destination_chain: int,
        message_id: str,
        details: Optional[Dict] = None
    ):
        """Log a message being received"""
        entry = CommunicationLogEntry(
            id=self.generate_log_id(),
            timestamp=time.time(),
            event_type=EventType.MESSAGE_RECEIVED,
            message_type=message_type,
            protocol=protocol,
            source_chain=source_chain,
            destination_chain=destination_chain,
            message_id=message_id,
            log_level=LogLevel.INFO,
            details=details or {}
        )
        
        self._add_log_entry(entry)
        
        self.structured_logger.info(
            f"Message received: {message_type.value} via {protocol} "
            f"from chain {source_chain} to {destination_chain}",
            extra={
                "event_type": "message_received",
                "message_id": message_id,
                "protocol": protocol,
                "source_chain": source_chain,
                "destination_chain": destination_chain
            }
        )
    
    def log_message_verified(
        self,
        message_type: MessageType,
        protocol: str,
        source_chain: int,
        message_id: str,
        verified: bool,
        details: Optional[Dict] = None
    ):
        """Log message verification result"""
        entry = CommunicationLogEntry(
            id=self.generate_log_id(),
            timestamp=time.time(),
            event_type=EventType.MESSAGE_VERIFIED,
            message_type=message_type,
            protocol=protocol,
            source_chain=source_chain,
            destination_chain=0,  # Not applicable for verification
            message_id=message_id,
            log_level=LogLevel.INFO if verified else LogLevel.WARNING,
            details=details or {}
        )
        
        self._add_log_entry(entry)
        
        log_method = self.structured_logger.info if verified else self.structured_logger.warning
        log_method(
            f"Message verification: {message_id} - {'VERIFIED' if verified else 'FAILED'}",
            extra={
                "event_type": "message_verified",
                "message_id": message_id,
                "protocol": protocol,
                "verified": verified
            }
        )
    
    def log_message_failed(
        self,
        message_type: MessageType,
        protocol: str,
        source_chain: int,
        destination_chain: int,
        operation_id: str,
        error_message: str,
        retry_attempt: Optional[int] = None,
        details: Optional[Dict] = None
    ):
        """Log a failed message"""
        entry = CommunicationLogEntry(
            id=self.generate_log_id(),
            timestamp=time.time(),
            event_type=EventType.MESSAGE_FAILED,
            message_type=message_type,
            protocol=protocol,
            source_chain=source_chain,
            destination_chain=destination_chain,
            operation_id=operation_id,
            log_level=LogLevel.ERROR,
            error_message=error_message,
            retry_attempt=retry_attempt,
            details=details or {}
        )
        
        self._add_log_entry(entry)
        
        self.structured_logger.error(
            f"Message failed: {message_type.value} via {protocol} - {error_message}",
            extra={
                "event_type": "message_failed",
                "operation_id": operation_id,
                "protocol": protocol,
                "source_chain": source_chain,
                "destination_chain": destination_chain,
                "error_message": error_message,
                "retry_attempt": retry_attempt
            }
        )
        
        # Check for alert conditions
        self._check_alert_conditions(entry)
    
    def log_retry_attempted(
        self,
        operation_id: str,
        protocol: str,
        retry_attempt: int,
        delay_seconds: float,
        reason: str
    ):
        """Log a retry attempt"""
        entry = CommunicationLogEntry(
            id=self.generate_log_id(),
            timestamp=time.time(),
            event_type=EventType.RETRY_ATTEMPTED,
            message_type=MessageType.STATUS_UPDATE,
            protocol=protocol,
            source_chain=0,
            destination_chain=0,
            operation_id=operation_id,
            log_level=LogLevel.WARNING,
            retry_attempt=retry_attempt,
            details={"delay_seconds": delay_seconds, "reason": reason}
        )
        
        self._add_log_entry(entry)
        
        self.structured_logger.warning(
            f"Retry attempt #{retry_attempt} for {operation_id} - {reason}",
            extra={
                "event_type": "retry_attempted",
                "operation_id": operation_id,
                "retry_attempt": retry_attempt,
                "delay_seconds": delay_seconds,
                "reason": reason
            }
        )
    
    def log_circuit_breaker_event(
        self,
        operation_id: str,
        protocol: str,
        event_type: EventType,
        failure_count: int,
        details: Optional[Dict] = None
    ):
        """Log circuit breaker state changes"""
        entry = CommunicationLogEntry(
            id=self.generate_log_id(),
            timestamp=time.time(),
            event_type=event_type,
            message_type=MessageType.STATUS_UPDATE,
            protocol=protocol,
            source_chain=0,
            destination_chain=0,
            operation_id=operation_id,
            log_level=LogLevel.CRITICAL if event_type == EventType.CIRCUIT_BREAKER_OPENED else LogLevel.INFO,
            details={**(details or {}), "failure_count": failure_count}
        )
        
        self._add_log_entry(entry)
        
        log_method = self.structured_logger.critical if event_type == EventType.CIRCUIT_BREAKER_OPENED else self.structured_logger.info
        log_method(
            f"Circuit breaker {event_type.value} for {operation_id} - {failure_count} failures",
            extra={
                "event_type": event_type.value,
                "operation_id": operation_id,
                "failure_count": failure_count
            }
        )
        
        # Alert on circuit breaker opening
        if event_type == EventType.CIRCUIT_BREAKER_OPENED:
            self._check_alert_conditions(entry)
    
    def log_protocol_selection(
        self,
        source_chain: int,
        destination_chain: int,
        selected_protocol: str,
        reason: str,
        alternatives: List[str],
        details: Optional[Dict] = None
    ):
        """Log protocol selection decision"""
        entry = CommunicationLogEntry(
            id=self.generate_log_id(),
            timestamp=time.time(),
            event_type=EventType.PROTOCOL_SELECTED,
            message_type=MessageType.STATUS_UPDATE,
            protocol=selected_protocol,
            source_chain=source_chain,
            destination_chain=destination_chain,
            log_level=LogLevel.INFO,
            details={
                **(details or {}),
                "reason": reason,
                "alternatives": alternatives
            }
        )
        
        self._add_log_entry(entry)
        
        self.structured_logger.info(
            f"Protocol selected: {selected_protocol} for {source_chain}->{destination_chain} - {reason}",
            extra={
                "event_type": "protocol_selected",
                "selected_protocol": selected_protocol,
                "source_chain": source_chain,
                "destination_chain": destination_chain,
                "reason": reason,
                "alternatives": alternatives
            }
        )
    
    def _add_log_entry(self, entry: CommunicationLogEntry):
        """Add log entry to in-memory storage"""
        self.log_entries.append(entry)
        
        # Maintain maximum log entries
        if len(self.log_entries) > self.max_log_entries:
            self.log_entries = self.log_entries[-self.max_log_entries:]
    
    def _check_alert_conditions(self, entry: CommunicationLogEntry):
        """Check if entry triggers any alert conditions"""
        current_time = time.time()
        
        for alert_config in self.alert_configs:
            if entry.event_type in alert_config.event_types:
                # Count recent events of this type
                recent_events = [
                    e for e in self.log_entries
                    if (e.event_type in alert_config.event_types and
                        current_time - e.timestamp <= alert_config.time_window_seconds)
                ]
                
                if len(recent_events) >= alert_config.threshold_count:
                    self._trigger_alert(alert_config, recent_events)
    
    def _trigger_alert(self, config: AlertConfig, events: List[CommunicationLogEntry]):
        """Trigger alert for matching events"""
        alert = {
            "id": self.generate_log_id(),
            "timestamp": time.time(),
            "config": asdict(config),
            "event_count": len(events),
            "events": [asdict(e) for e in events[-5:]],  # Last 5 events
            "message": f"Alert: {len(events)} {config.event_types} events in {config.time_window_seconds}s"
        }
        
        self.alert_history.append(alert)
        
        # Log the alert
        self.structured_logger.critical(
            f"ALERT TRIGGERED: {alert['message']}",
            extra={
                "alert_id": alert["id"],
                "event_count": len(events),
                "time_window": config.time_window_seconds
            }
        )
        
        # Here you would integrate with actual alerting systems
        # (email, Slack, PagerDuty, etc.)
    
    def add_alert_config(self, config: AlertConfig):
        """Add alert configuration"""
        self.alert_configs.append(config)
        logger.info(f"Added alert config for {config.event_types}")
    
    def get_logs(
        self,
        limit: int = 100,
        event_type: Optional[EventType] = None,
        protocol: Optional[str] = None,
        source_chain: Optional[int] = None,
        destination_chain: Optional[int] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> List[CommunicationLogEntry]:
        """Get filtered log entries"""
        filtered_logs = self.log_entries
        
        # Apply filters
        if event_type:
            filtered_logs = [e for e in filtered_logs if e.event_type == event_type]
        
        if protocol:
            filtered_logs = [e for e in filtered_logs if e.protocol == protocol]
        
        if source_chain is not None:
            filtered_logs = [e for e in filtered_logs if e.source_chain == source_chain]
        
        if destination_chain is not None:
            filtered_logs = [e for e in filtered_logs if e.destination_chain == destination_chain]
        
        if start_time:
            filtered_logs = [e for e in filtered_logs if e.timestamp >= start_time]
        
        if end_time:
            filtered_logs = [e for e in filtered_logs if e.timestamp <= end_time]
        
        # Sort by timestamp (newest first) and limit
        filtered_logs.sort(key=lambda x: x.timestamp, reverse=True)
        return filtered_logs[:limit]
    
    def get_aggregated_stats(
        self,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> LogAggregation:
        """Get aggregated statistics for log entries"""
        if start_time is None:
            start_time = time.time() - 3600  # Last hour
        if end_time is None:
            end_time = time.time()
        
        # Filter logs by time range
        logs = [
            e for e in self.log_entries
            if start_time <= e.timestamp <= end_time
        ]
        
        if not logs:
            return LogAggregation(
                total_messages=0,
                successful_messages=0,
                failed_messages=0,
                average_execution_time=0,
                protocols_used={},
                chains_used={},
                error_types={},
                time_period={"start": start_time, "end": end_time}
            )
        
        # Calculate statistics
        total_messages = len([e for e in logs if e.event_type == EventType.MESSAGE_SENT])
        successful_messages = len([e for e in logs if e.event_type == EventType.MESSAGE_RECEIVED])
        failed_messages = len([e for e in logs if e.event_type == EventType.MESSAGE_FAILED])
        
        # Execution times
        execution_times = [e.execution_time_ms for e in logs if e.execution_time_ms is not None]
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
        
        # Protocol usage
        protocols_used = {}
        for log in logs:
            protocols_used[log.protocol] = protocols_used.get(log.protocol, 0) + 1
        
        # Chain usage
        chains_used = {}
        for log in logs:
            if log.source_chain > 0:
                chain_key = f"chain_{log.source_chain}"
                chains_used[chain_key] = chains_used.get(chain_key, 0) + 1
        
        # Error types
        error_types = {}
        for log in logs:
            if log.error_message:
                # Categorize errors (simplified)
                if "timeout" in log.error_message.lower():
                    error_type = "timeout"
                elif "network" in log.error_message.lower():
                    error_type = "network"
                elif "gas" in log.error_message.lower():
                    error_type = "gas"
                else:
                    error_type = "other"
                
                error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return LogAggregation(
            total_messages=total_messages,
            successful_messages=successful_messages,
            failed_messages=failed_messages,
            average_execution_time=avg_execution_time,
            protocols_used=protocols_used,
            chains_used=chains_used,
            error_types=error_types,
            time_period={"start": start_time, "end": end_time}
        )
    
    def export_logs(
        self,
        format_type: str = "json",
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> str:
        """Export logs in specified format"""
        logs = self.get_logs(
            limit=10000,  # Large limit for export
            start_time=start_time,
            end_time=end_time
        )
        
        if format_type.lower() == "json":
            return json.dumps([asdict(log) for log in logs], indent=2)
        elif format_type.lower() == "csv":
            # Simple CSV export (would need proper CSV library in production)
            lines = ["timestamp,event_type,protocol,source_chain,destination_chain,message_id,error_message"]
            for log in logs:
                lines.append(f"{log.timestamp},{log.event_type.value},{log.protocol},{log.source_chain},{log.destination_chain},{log.message_id or ''},{log.error_message or ''}")
            return "\n".join(lines)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
    
    def clear_logs(self, older_than_seconds: Optional[int] = None):
        """Clear log entries"""
        if older_than_seconds:
            cutoff_time = time.time() - older_than_seconds
            self.log_entries = [e for e in self.log_entries if e.timestamp > cutoff_time]
            logger.info(f"Cleared logs older than {older_than_seconds} seconds")
        else:
            self.log_entries.clear()
            logger.info("Cleared all log entries")


# Global instance
communication_logger = CommunicationLogger()

# Set up default alert configurations
default_alerts = [
    AlertConfig(
        event_types=[EventType.MESSAGE_FAILED],
        threshold_count=5,
        time_window_seconds=300,  # 5 minutes
        alert_channels=["log"]
    ),
    AlertConfig(
        event_types=[EventType.CIRCUIT_BREAKER_OPENED],
        threshold_count=1,
        time_window_seconds=60,
        alert_channels=["log", "critical"]
    )
]

for alert in default_alerts:
    communication_logger.add_alert_config(alert)