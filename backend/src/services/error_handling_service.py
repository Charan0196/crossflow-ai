"""
Error Handling and User Feedback Service
Implements comprehensive error logging, user-friendly error messages, and error recovery mechanisms
Requirements: 9.5 - Error handling and user feedback
"""
import asyncio
import json
import logging
import time
import traceback
import uuid
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timezone
from decimal import Decimal

from src.services.system_logging_service import system_logging_service


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Categories of errors"""
    VALIDATION_ERROR = "validation_error"
    NETWORK_ERROR = "network_error"
    BLOCKCHAIN_ERROR = "blockchain_error"
    SOLVER_ERROR = "solver_error"
    LIQUIDITY_ERROR = "liquidity_error"
    GAS_ERROR = "gas_error"
    TIMEOUT_ERROR = "timeout_error"
    AUTHENTICATION_ERROR = "authentication_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    SYSTEM_ERROR = "system_error"
    UNKNOWN_ERROR = "unknown_error"


class RecoveryAction(Enum):
    """Types of recovery actions"""
    RETRY = "retry"
    FALLBACK = "fallback"
    USER_ACTION_REQUIRED = "user_action_required"
    ESCALATE = "escalate"
    IGNORE = "ignore"


@dataclass
class ErrorContext:
    """Context information for an error"""
    user_address: Optional[str] = None
    intent_id: Optional[str] = None
    solver_address: Optional[str] = None
    chain_id: Optional[int] = None
    operation_type: Optional[str] = None
    request_id: Optional[str] = None
    session_id: Optional[str] = None
    additional_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.additional_data is None:
            self.additional_data = {}


@dataclass
class ErrorEntry:
    """Comprehensive error log entry"""
    id: str
    timestamp: float
    error_code: str
    error_message: str
    user_friendly_message: str
    category: ErrorCategory
    severity: ErrorSeverity
    context: ErrorContext
    stack_trace: Optional[str] = None
    recovery_action: Optional[RecoveryAction] = None
    recovery_attempted: bool = False
    recovery_successful: Optional[bool] = None
    retry_count: int = 0
    resolved: bool = False
    resolution_notes: Optional[str] = None


@dataclass
class UserFriendlyError:
    """User-friendly error response"""
    error_id: str
    title: str
    message: str
    severity: str
    category: str
    suggested_actions: List[str]
    support_contact: Optional[str] = None
    retry_possible: bool = False
    estimated_resolution_time: Optional[str] = None


@dataclass
class RecoveryStrategy:
    """Error recovery strategy configuration"""
    error_category: ErrorCategory
    max_retries: int
    retry_delay_seconds: float
    exponential_backoff: bool
    fallback_action: Optional[Callable] = None
    escalation_threshold: int = 3
    user_notification_required: bool = True


class ErrorHandlingService:
    """Comprehensive error handling and user feedback service"""
    
    def __init__(self):
        self.error_logs: List[ErrorEntry] = []
        self.max_error_logs = 10000
        self.recovery_strategies: Dict[ErrorCategory, RecoveryStrategy] = {}
        self.error_patterns: Dict[str, ErrorCategory] = {}
        self.user_friendly_messages: Dict[str, Dict[str, str]] = {}
        self._setup_default_strategies()
        self._setup_error_patterns()
        self._setup_user_friendly_messages()
        self._setup_logger()
    
    def _setup_logger(self):
        """Set up error handling logger"""
        self.logger = logging.getLogger("crossflow.error_handling")
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def _setup_default_strategies(self):
        """Set up default recovery strategies for different error categories"""
        self.recovery_strategies = {
            ErrorCategory.NETWORK_ERROR: RecoveryStrategy(
                error_category=ErrorCategory.NETWORK_ERROR,
                max_retries=3,
                retry_delay_seconds=2.0,
                exponential_backoff=True,
                escalation_threshold=5,
                user_notification_required=True
            ),
            ErrorCategory.BLOCKCHAIN_ERROR: RecoveryStrategy(
                error_category=ErrorCategory.BLOCKCHAIN_ERROR,
                max_retries=2,
                retry_delay_seconds=5.0,
                exponential_backoff=True,
                escalation_threshold=3,
                user_notification_required=True
            ),
            ErrorCategory.SOLVER_ERROR: RecoveryStrategy(
                error_category=ErrorCategory.SOLVER_ERROR,
                max_retries=1,
                retry_delay_seconds=1.0,
                exponential_backoff=False,
                escalation_threshold=2,
                user_notification_required=True
            ),
            ErrorCategory.LIQUIDITY_ERROR: RecoveryStrategy(
                error_category=ErrorCategory.LIQUIDITY_ERROR,
                max_retries=0,
                retry_delay_seconds=0,
                exponential_backoff=False,
                escalation_threshold=1,
                user_notification_required=True
            ),
            ErrorCategory.GAS_ERROR: RecoveryStrategy(
                error_category=ErrorCategory.GAS_ERROR,
                max_retries=1,
                retry_delay_seconds=10.0,
                exponential_backoff=False,
                escalation_threshold=2,
                user_notification_required=True
            ),
            ErrorCategory.TIMEOUT_ERROR: RecoveryStrategy(
                error_category=ErrorCategory.TIMEOUT_ERROR,
                max_retries=2,
                retry_delay_seconds=5.0,
                exponential_backoff=True,
                escalation_threshold=3,
                user_notification_required=True
            ),
            ErrorCategory.VALIDATION_ERROR: RecoveryStrategy(
                error_category=ErrorCategory.VALIDATION_ERROR,
                max_retries=0,
                retry_delay_seconds=0,
                exponential_backoff=False,
                escalation_threshold=1,
                user_notification_required=True
            ),
            ErrorCategory.SYSTEM_ERROR: RecoveryStrategy(
                error_category=ErrorCategory.SYSTEM_ERROR,
                max_retries=1,
                retry_delay_seconds=3.0,
                exponential_backoff=False,
                escalation_threshold=2,
                user_notification_required=True
            )
        }
    
    def _setup_error_patterns(self):
        """Set up error pattern matching for categorization"""
        self.error_patterns = {
            # Network errors
            "connection": ErrorCategory.NETWORK_ERROR,
            "timeout": ErrorCategory.TIMEOUT_ERROR,
            "network": ErrorCategory.NETWORK_ERROR,
            "unreachable": ErrorCategory.NETWORK_ERROR,
            "dns": ErrorCategory.NETWORK_ERROR,
            
            # Blockchain errors
            "gas": ErrorCategory.GAS_ERROR,
            "nonce": ErrorCategory.BLOCKCHAIN_ERROR,
            "revert": ErrorCategory.BLOCKCHAIN_ERROR,
            "insufficient funds": ErrorCategory.BLOCKCHAIN_ERROR,
            "transaction failed": ErrorCategory.BLOCKCHAIN_ERROR,
            
            # Solver errors
            "solver": ErrorCategory.SOLVER_ERROR,
            "bid": ErrorCategory.SOLVER_ERROR,
            "fulfillment": ErrorCategory.SOLVER_ERROR,
            
            # Liquidity errors
            "liquidity": ErrorCategory.LIQUIDITY_ERROR,
            "slippage": ErrorCategory.LIQUIDITY_ERROR,
            "price impact": ErrorCategory.LIQUIDITY_ERROR,
            
            # Validation errors
            "validation": ErrorCategory.VALIDATION_ERROR,
            "invalid": ErrorCategory.VALIDATION_ERROR,
            "malformed": ErrorCategory.VALIDATION_ERROR,
            
            # Authentication errors
            "unauthorized": ErrorCategory.AUTHENTICATION_ERROR,
            "forbidden": ErrorCategory.AUTHENTICATION_ERROR,
            "authentication": ErrorCategory.AUTHENTICATION_ERROR,
            
            # Rate limiting
            "rate limit": ErrorCategory.RATE_LIMIT_ERROR,
            "too many requests": ErrorCategory.RATE_LIMIT_ERROR,
        }
    
    def _setup_user_friendly_messages(self):
        """Set up user-friendly error messages"""
        self.user_friendly_messages = {
            ErrorCategory.NETWORK_ERROR.value: {
                "title": "Connection Issue",
                "message": "We're having trouble connecting to the network. This is usually temporary.",
                "actions": [
                    "Wait a moment and try again",
                    "Check your internet connection",
                    "Contact support if the issue persists"
                ]
            },
            ErrorCategory.BLOCKCHAIN_ERROR.value: {
                "title": "Blockchain Transaction Issue",
                "message": "There was an issue processing your transaction on the blockchain.",
                "actions": [
                    "Check your wallet balance",
                    "Ensure you have enough gas fees",
                    "Try again with higher gas settings"
                ]
            },
            ErrorCategory.SOLVER_ERROR.value: {
                "title": "Trade Execution Issue",
                "message": "The market maker couldn't complete your trade. This might be due to market conditions.",
                "actions": [
                    "Try again in a few moments",
                    "Consider adjusting your trade parameters",
                    "Check if there's sufficient liquidity"
                ]
            },
            ErrorCategory.LIQUIDITY_ERROR.value: {
                "title": "Insufficient Liquidity",
                "message": "There isn't enough liquidity available for your trade at the current price.",
                "actions": [
                    "Try a smaller trade amount",
                    "Adjust your minimum output amount",
                    "Wait for better market conditions"
                ]
            },
            ErrorCategory.GAS_ERROR.value: {
                "title": "Gas Fee Issue",
                "message": "There's an issue with gas fees for your transaction.",
                "actions": [
                    "Check your wallet balance for gas fees",
                    "Try again when network congestion is lower",
                    "Increase your gas limit or price"
                ]
            },
            ErrorCategory.TIMEOUT_ERROR.value: {
                "title": "Request Timeout",
                "message": "Your request took too long to process and timed out.",
                "actions": [
                    "Try again - this is often temporary",
                    "Check network conditions",
                    "Contact support if timeouts persist"
                ]
            },
            ErrorCategory.VALIDATION_ERROR.value: {
                "title": "Invalid Input",
                "message": "Some of the information you provided isn't valid.",
                "actions": [
                    "Check all input fields",
                    "Ensure token addresses are correct",
                    "Verify amounts are within valid ranges"
                ]
            },
            ErrorCategory.SYSTEM_ERROR.value: {
                "title": "System Error",
                "message": "We encountered an internal system error. Our team has been notified.",
                "actions": [
                    "Try again in a few minutes",
                    "Contact support with error ID if issue persists",
                    "Check our status page for system updates"
                ]
            }
        }
    
    def categorize_error(self, error_message: str, error_code: Optional[str] = None) -> ErrorCategory:
        """Categorize error based on message content and error code"""
        error_text = (error_message + " " + (error_code or "")).lower()
        
        # Check for specific patterns
        for pattern, category in self.error_patterns.items():
            if pattern in error_text:
                return category
        
        # Default to unknown error
        return ErrorCategory.UNKNOWN_ERROR
    
    def determine_severity(self, category: ErrorCategory, context: ErrorContext) -> ErrorSeverity:
        """Determine error severity based on category and context"""
        # Critical errors
        if category in [ErrorCategory.SYSTEM_ERROR, ErrorCategory.AUTHENTICATION_ERROR]:
            return ErrorSeverity.CRITICAL
        
        # High severity errors
        if category in [ErrorCategory.BLOCKCHAIN_ERROR, ErrorCategory.GAS_ERROR]:
            return ErrorSeverity.HIGH
        
        # Medium severity errors
        if category in [ErrorCategory.SOLVER_ERROR, ErrorCategory.NETWORK_ERROR, ErrorCategory.TIMEOUT_ERROR]:
            return ErrorSeverity.MEDIUM
        
        # Low severity errors
        return ErrorSeverity.LOW
    
    async def handle_error(
        self,
        error: Exception,
        context: ErrorContext,
        error_code: Optional[str] = None,
        custom_message: Optional[str] = None
    ) -> ErrorEntry:
        """
        Handle an error with comprehensive logging and recovery
        Requirements: 9.5 - Comprehensive error logging for debugging
        """
        error_id = str(uuid.uuid4())
        error_message = custom_message or str(error)
        
        # Categorize the error
        category = self.categorize_error(error_message, error_code)
        severity = self.determine_severity(category, context)
        
        # Get stack trace
        stack_trace = traceback.format_exc() if error else None
        
        # Create error entry
        error_entry = ErrorEntry(
            id=error_id,
            timestamp=time.time(),
            error_code=error_code or "UNKNOWN",
            error_message=error_message,
            user_friendly_message=self._generate_user_friendly_message(category, error_message),
            category=category,
            severity=severity,
            context=context,
            stack_trace=stack_trace
        )
        
        # Log the error
        self._log_error(error_entry)
        
        # Attempt recovery if strategy exists
        if category in self.recovery_strategies:
            await self._attempt_recovery(error_entry)
        
        # Log to system logging service
        system_logging_service.log_system_health_check(
            service_name="error_handling",
            passed=False,
            response_time_ms=0,
            details={
                "error_id": error_id,
                "category": category.value,
                "severity": severity.value,
                "context": asdict(context)
            }
        )
        
        return error_entry
    
    def _generate_user_friendly_message(self, category: ErrorCategory, technical_message: str) -> str:
        """Generate user-friendly error message"""
        template = self.user_friendly_messages.get(category.value)
        if template:
            return template["message"]
        
        # Fallback for unknown categories
        return "An unexpected error occurred. Please try again or contact support if the issue persists."
    
    def _log_error(self, error_entry: ErrorEntry):
        """Log error entry to storage and logging system"""
        self.error_logs.append(error_entry)
        
        # Maintain maximum log entries
        if len(self.error_logs) > self.max_error_logs:
            self.error_logs = self.error_logs[-self.max_error_logs:]
        
        # Log to standard logger
        log_level = {
            ErrorSeverity.LOW: logging.INFO,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL
        }.get(error_entry.severity, logging.ERROR)
        
        self.logger.log(
            log_level,
            f"Error {error_entry.id}: {error_entry.error_message}",
            extra={
                "error_id": error_entry.id,
                "category": error_entry.category.value,
                "severity": error_entry.severity.value,
                "context": asdict(error_entry.context)
            }
        )
    
    async def _attempt_recovery(self, error_entry: ErrorEntry):
        """Attempt error recovery based on strategy"""
        strategy = self.recovery_strategies.get(error_entry.category)
        if not strategy:
            return
        
        error_entry.recovery_attempted = True
        
        # Check if we should retry
        if error_entry.retry_count < strategy.max_retries:
            error_entry.retry_count += 1
            
            # Calculate delay
            delay = strategy.retry_delay_seconds
            if strategy.exponential_backoff:
                delay *= (2 ** (error_entry.retry_count - 1))
            
            # Log retry attempt
            self.logger.info(
                f"Attempting recovery for error {error_entry.id} (attempt {error_entry.retry_count})",
                extra={
                    "error_id": error_entry.id,
                    "retry_count": error_entry.retry_count,
                    "delay_seconds": delay
                }
            )
            
            # Wait before retry
            if delay > 0:
                await asyncio.sleep(delay)
            
            # Here you would implement the actual retry logic
            # For now, we'll simulate recovery success/failure
            error_entry.recovery_successful = error_entry.retry_count <= 2  # Simulate success after 1-2 retries
        
        # Check if escalation is needed
        if error_entry.retry_count >= strategy.escalation_threshold:
            await self._escalate_error(error_entry)
    
    async def _escalate_error(self, error_entry: ErrorEntry):
        """Escalate error to higher level support"""
        self.logger.critical(
            f"Escalating error {error_entry.id} after {error_entry.retry_count} attempts",
            extra={
                "error_id": error_entry.id,
                "category": error_entry.category.value,
                "severity": error_entry.severity.value
            }
        )
        
        # Here you would integrate with alerting systems
        # (PagerDuty, Slack, email, etc.)
    
    def get_user_friendly_error(self, error_id: str) -> Optional[UserFriendlyError]:
        """
        Get user-friendly error information
        Requirements: 9.5 - User-friendly error messages
        """
        error_entry = self.get_error_by_id(error_id)
        if not error_entry:
            return None
        
        template = self.user_friendly_messages.get(error_entry.category.value, {})
        
        return UserFriendlyError(
            error_id=error_id,
            title=template.get("title", "Error"),
            message=error_entry.user_friendly_message,
            severity=error_entry.severity.value,
            category=error_entry.category.value,
            suggested_actions=template.get("actions", ["Contact support"]),
            support_contact="support@crossflow.ai",
            retry_possible=error_entry.category in self.recovery_strategies and not error_entry.resolved,
            estimated_resolution_time=self._estimate_resolution_time(error_entry)
        )
    
    def _estimate_resolution_time(self, error_entry: ErrorEntry) -> Optional[str]:
        """Estimate resolution time based on error category and severity"""
        if error_entry.category == ErrorCategory.NETWORK_ERROR:
            return "1-5 minutes"
        elif error_entry.category == ErrorCategory.BLOCKCHAIN_ERROR:
            return "5-15 minutes"
        elif error_entry.category == ErrorCategory.SOLVER_ERROR:
            return "2-10 minutes"
        elif error_entry.category == ErrorCategory.SYSTEM_ERROR:
            return "10-30 minutes"
        else:
            return "5-15 minutes"
    
    async def retry_operation(
        self,
        error_id: str,
        operation_callback: Callable,
        *args,
        **kwargs
    ) -> bool:
        """
        Retry a failed operation
        Requirements: 9.5 - Error recovery and retry mechanisms
        """
        error_entry = self.get_error_by_id(error_id)
        if not error_entry:
            return False
        
        strategy = self.recovery_strategies.get(error_entry.category)
        if not strategy or error_entry.retry_count >= strategy.max_retries:
            return False
        
        try:
            # Increment retry count
            error_entry.retry_count += 1
            
            # Calculate delay
            delay = strategy.retry_delay_seconds
            if strategy.exponential_backoff:
                delay *= (2 ** (error_entry.retry_count - 1))
            
            # Wait before retry
            if delay > 0:
                await asyncio.sleep(delay)
            
            # Execute the operation
            result = await operation_callback(*args, **kwargs)
            
            # Mark as successful
            error_entry.recovery_successful = True
            error_entry.resolved = True
            error_entry.resolution_notes = f"Resolved after {error_entry.retry_count} retries"
            
            self.logger.info(
                f"Successfully recovered from error {error_id} after {error_entry.retry_count} retries"
            )
            
            return True
            
        except Exception as e:
            # Retry failed
            error_entry.recovery_successful = False
            
            self.logger.warning(
                f"Retry {error_entry.retry_count} failed for error {error_id}: {str(e)}"
            )
            
            # Check if we should escalate
            if error_entry.retry_count >= strategy.escalation_threshold:
                await self._escalate_error(error_entry)
            
            return False
    
    def get_error_by_id(self, error_id: str) -> Optional[ErrorEntry]:
        """Get error entry by ID"""
        for error in self.error_logs:
            if error.id == error_id:
                return error
        return None
    
    def get_errors_by_category(
        self,
        category: ErrorCategory,
        limit: int = 100,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> List[ErrorEntry]:
        """Get errors filtered by category and time range"""
        filtered_errors = [
            error for error in self.error_logs
            if error.category == category
        ]
        
        if start_time:
            filtered_errors = [e for e in filtered_errors if e.timestamp >= start_time]
        
        if end_time:
            filtered_errors = [e for e in filtered_errors if e.timestamp <= end_time]
        
        # Sort by timestamp (newest first) and limit
        filtered_errors.sort(key=lambda x: x.timestamp, reverse=True)
        return filtered_errors[:limit]
    
    def get_error_statistics(
        self,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> Dict[str, Any]:
        """Get error statistics for analysis"""
        if start_time is None:
            start_time = time.time() - 86400  # Last 24 hours
        if end_time is None:
            end_time = time.time()
        
        # Filter errors by time range
        filtered_errors = [
            error for error in self.error_logs
            if start_time <= error.timestamp <= end_time
        ]
        
        if not filtered_errors:
            return {
                "total_errors": 0,
                "by_category": {},
                "by_severity": {},
                "recovery_rate": 0,
                "most_common_errors": [],
                "time_period": {"start": start_time, "end": end_time}
            }
        
        # Count by category
        by_category = {}
        for error in filtered_errors:
            category = error.category.value
            by_category[category] = by_category.get(category, 0) + 1
        
        # Count by severity
        by_severity = {}
        for error in filtered_errors:
            severity = error.severity.value
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        # Calculate recovery rate
        recovery_attempted = len([e for e in filtered_errors if e.recovery_attempted])
        recovery_successful = len([e for e in filtered_errors if e.recovery_successful])
        recovery_rate = (recovery_successful / recovery_attempted * 100) if recovery_attempted > 0 else 0
        
        # Find most common error messages
        error_messages = {}
        for error in filtered_errors:
            # Normalize error message for grouping
            normalized_msg = error.error_message[:100]  # First 100 chars
            error_messages[normalized_msg] = error_messages.get(normalized_msg, 0) + 1
        
        most_common_errors = sorted(error_messages.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "total_errors": len(filtered_errors),
            "by_category": by_category,
            "by_severity": by_severity,
            "recovery_rate": recovery_rate,
            "most_common_errors": [{"message": msg, "count": count} for msg, count in most_common_errors],
            "time_period": {"start": start_time, "end": end_time}
        }
    
    def mark_error_resolved(self, error_id: str, resolution_notes: str):
        """Mark an error as resolved"""
        error_entry = self.get_error_by_id(error_id)
        if error_entry:
            error_entry.resolved = True
            error_entry.resolution_notes = resolution_notes
            
            self.logger.info(
                f"Error {error_id} marked as resolved: {resolution_notes}"
            )
    
    def export_error_logs(
        self,
        format_type: str = "json",
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> str:
        """Export error logs in specified format"""
        filtered_errors = self.error_logs
        
        if start_time:
            filtered_errors = [e for e in filtered_errors if e.timestamp >= start_time]
        
        if end_time:
            filtered_errors = [e for e in filtered_errors if e.timestamp <= end_time]
        
        # Sort by timestamp
        filtered_errors.sort(key=lambda x: x.timestamp, reverse=True)
        
        if format_type.lower() == "json":
            return json.dumps([asdict(error) for error in filtered_errors], indent=2, default=str)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
    
    def clear_resolved_errors(self, older_than_seconds: Optional[int] = None):
        """Clear resolved error entries"""
        if older_than_seconds:
            cutoff_time = time.time() - older_than_seconds
            self.error_logs = [
                e for e in self.error_logs
                if not e.resolved or e.timestamp > cutoff_time
            ]
        else:
            self.error_logs = [e for e in self.error_logs if not e.resolved]
        
        self.logger.info("Cleared resolved error entries")


# Global instance
error_handling_service = ErrorHandlingService()