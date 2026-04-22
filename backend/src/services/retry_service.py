"""
Retry service with exponential backoff and circuit breaker patterns
Implements Requirements 2.4 for cross-chain messaging reliability
"""
import asyncio
import logging
import time
import random
from typing import Callable, Any, Optional, Dict, List
from dataclasses import dataclass
from enum import Enum
from functools import wraps


logger = logging.getLogger(__name__)


class RetryStrategy(Enum):
    """Retry strategy types"""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_DELAY = "fixed_delay"


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_attempts: int = 5
    base_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    backoff_multiplier: float = 2.0
    jitter: bool = True
    jitter_range: float = 0.1  # 10% jitter
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF


@dataclass
class RetryResult:
    """Result of retry operation"""
    success: bool
    attempts: int
    total_time: float
    last_error: Optional[Exception] = None
    result: Any = None


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5
    recovery_timeout: float = 60.0  # seconds
    half_open_max_calls: int = 3


class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject calls
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreakerStatus:
    """Circuit breaker status tracking"""
    state: CircuitBreakerState = CircuitBreakerState.CLOSED
    failure_count: int = 0
    last_failure_time: float = 0
    half_open_calls: int = 0


class RetryService:
    """Service for handling retries with exponential backoff and circuit breakers"""
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreakerStatus] = {}
        self.retry_stats: Dict[str, List[RetryResult]] = {}
    
    def calculate_delay(self, attempt: int, config: RetryConfig) -> float:
        """Calculate delay for retry attempt"""
        if config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = config.base_delay * (config.backoff_multiplier ** (attempt - 1))
        elif config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = config.base_delay * attempt
        else:  # FIXED_DELAY
            delay = config.base_delay
        
        # Apply maximum delay limit
        delay = min(delay, config.max_delay)
        
        # Add jitter to prevent thundering herd
        if config.jitter:
            jitter_amount = delay * config.jitter_range
            jitter = random.uniform(-jitter_amount, jitter_amount)
            delay = max(0, delay + jitter)
        
        return delay
    
    def get_circuit_breaker(self, operation_id: str) -> CircuitBreakerStatus:
        """Get or create circuit breaker for operation"""
        if operation_id not in self.circuit_breakers:
            self.circuit_breakers[operation_id] = CircuitBreakerStatus()
        return self.circuit_breakers[operation_id]
    
    def should_allow_call(self, operation_id: str, config: CircuitBreakerConfig) -> bool:
        """Check if circuit breaker allows the call"""
        breaker = self.get_circuit_breaker(operation_id)
        current_time = time.time()
        
        if breaker.state == CircuitBreakerState.CLOSED:
            return True
        
        elif breaker.state == CircuitBreakerState.OPEN:
            # Check if recovery timeout has passed
            if current_time - breaker.last_failure_time >= config.recovery_timeout:
                breaker.state = CircuitBreakerState.HALF_OPEN
                breaker.half_open_calls = 0
                logger.info(f"Circuit breaker {operation_id} transitioning to HALF_OPEN")
                return True
            return False
        
        elif breaker.state == CircuitBreakerState.HALF_OPEN:
            # Allow limited calls in half-open state
            return breaker.half_open_calls < config.half_open_max_calls
        
        return False
    
    def record_success(self, operation_id: str):
        """Record successful operation"""
        breaker = self.get_circuit_breaker(operation_id)
        
        if breaker.state == CircuitBreakerState.HALF_OPEN:
            breaker.half_open_calls += 1
            # If enough successful calls, close the circuit
            if breaker.half_open_calls >= 3:  # Configurable threshold
                breaker.state = CircuitBreakerState.CLOSED
                breaker.failure_count = 0
                logger.info(f"Circuit breaker {operation_id} closed after recovery")
        else:
            breaker.failure_count = 0
    
    def record_failure(self, operation_id: str, config: CircuitBreakerConfig):
        """Record failed operation"""
        breaker = self.get_circuit_breaker(operation_id)
        breaker.failure_count += 1
        breaker.last_failure_time = time.time()
        
        if breaker.state == CircuitBreakerState.HALF_OPEN:
            # Failure in half-open state, go back to open
            breaker.state = CircuitBreakerState.OPEN
            logger.warning(f"Circuit breaker {operation_id} reopened after failure")
        
        elif breaker.failure_count >= config.failure_threshold:
            # Too many failures, open the circuit
            breaker.state = CircuitBreakerState.OPEN
            logger.warning(f"Circuit breaker {operation_id} opened after {breaker.failure_count} failures")
    
    async def retry_with_backoff(
        self,
        operation: Callable,
        operation_id: str,
        retry_config: Optional[RetryConfig] = None,
        circuit_config: Optional[CircuitBreakerConfig] = None,
        *args,
        **kwargs
    ) -> RetryResult:
        """
        Execute operation with retry logic and circuit breaker
        
        Args:
            operation: Async function to execute
            operation_id: Unique identifier for circuit breaker
            retry_config: Retry configuration
            circuit_config: Circuit breaker configuration
            *args, **kwargs: Arguments for the operation
        """
        if retry_config is None:
            retry_config = RetryConfig()
        
        if circuit_config is None:
            circuit_config = CircuitBreakerConfig()
        
        start_time = time.time()
        last_error = None
        
        for attempt in range(1, retry_config.max_attempts + 1):
            # Check circuit breaker
            if not self.should_allow_call(operation_id, circuit_config):
                logger.warning(f"Circuit breaker {operation_id} is OPEN, rejecting call")
                return RetryResult(
                    success=False,
                    attempts=attempt - 1,
                    total_time=time.time() - start_time,
                    last_error=Exception("Circuit breaker is OPEN")
                )
            
            try:
                logger.debug(f"Attempt {attempt}/{retry_config.max_attempts} for {operation_id}")
                
                # Execute the operation
                if asyncio.iscoroutinefunction(operation):
                    result = await operation(*args, **kwargs)
                else:
                    result = operation(*args, **kwargs)
                
                # Success - record and return
                self.record_success(operation_id)
                
                total_time = time.time() - start_time
                retry_result = RetryResult(
                    success=True,
                    attempts=attempt,
                    total_time=total_time,
                    result=result
                )
                
                # Store stats
                if operation_id not in self.retry_stats:
                    self.retry_stats[operation_id] = []
                self.retry_stats[operation_id].append(retry_result)
                
                logger.info(f"Operation {operation_id} succeeded on attempt {attempt}")
                return retry_result
                
            except Exception as e:
                last_error = e
                self.record_failure(operation_id, circuit_config)
                
                logger.warning(f"Attempt {attempt} failed for {operation_id}: {e}")
                
                # If this was the last attempt, don't wait
                if attempt == retry_config.max_attempts:
                    break
                
                # Calculate and apply delay
                delay = self.calculate_delay(attempt, retry_config)
                logger.debug(f"Waiting {delay:.2f}s before retry {attempt + 1}")
                await asyncio.sleep(delay)
        
        # All attempts failed
        total_time = time.time() - start_time
        retry_result = RetryResult(
            success=False,
            attempts=retry_config.max_attempts,
            total_time=total_time,
            last_error=last_error
        )
        
        # Store stats
        if operation_id not in self.retry_stats:
            self.retry_stats[operation_id] = []
        self.retry_stats[operation_id].append(retry_result)
        
        logger.error(f"Operation {operation_id} failed after {retry_config.max_attempts} attempts")
        return retry_result
    
    def get_retry_stats(self, operation_id: str) -> Dict[str, Any]:
        """Get retry statistics for an operation"""
        if operation_id not in self.retry_stats:
            return {"total_operations": 0}
        
        results = self.retry_stats[operation_id]
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        return {
            "total_operations": len(results),
            "successful_operations": len(successful),
            "failed_operations": len(failed),
            "success_rate": len(successful) / len(results) * 100 if results else 0,
            "average_attempts": sum(r.attempts for r in results) / len(results) if results else 0,
            "average_time": sum(r.total_time for r in results) / len(results) if results else 0,
            "circuit_breaker_state": self.circuit_breakers.get(operation_id, CircuitBreakerStatus()).state.value
        }
    
    def reset_circuit_breaker(self, operation_id: str):
        """Manually reset circuit breaker"""
        if operation_id in self.circuit_breakers:
            self.circuit_breakers[operation_id] = CircuitBreakerStatus()
            logger.info(f"Circuit breaker {operation_id} manually reset")
    
    def get_all_circuit_breaker_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all circuit breakers"""
        status = {}
        for operation_id, breaker in self.circuit_breakers.items():
            status[operation_id] = {
                "state": breaker.state.value,
                "failure_count": breaker.failure_count,
                "last_failure_time": breaker.last_failure_time,
                "half_open_calls": breaker.half_open_calls
            }
        return status


def retry_with_exponential_backoff(
    operation_id: str,
    max_attempts: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_multiplier: float = 2.0,
    jitter: bool = True
):
    """
    Decorator for automatic retry with exponential backoff
    
    Usage:
        @retry_with_exponential_backoff("send_message", max_attempts=3)
        async def send_cross_chain_message(params):
            # Implementation
            pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            retry_service = RetryService()
            config = RetryConfig(
                max_attempts=max_attempts,
                base_delay=base_delay,
                max_delay=max_delay,
                backoff_multiplier=backoff_multiplier,
                jitter=jitter
            )
            
            result = await retry_service.retry_with_backoff(
                func, operation_id, config, None, *args, **kwargs
            )
            
            if result.success:
                return result.result
            else:
                raise result.last_error or Exception("Operation failed after retries")
        
        return wrapper
    return decorator


# Global instance
retry_service = RetryService()