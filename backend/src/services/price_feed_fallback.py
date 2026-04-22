"""
Price feed fallback system with automatic failover mechanisms
"""
import asyncio
from typing import Dict, List, Optional, Tuple, Callable, Any
from decimal import Decimal
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging
from collections import defaultdict

from src.services.price_freshness_validator import (
    PriceDataPoint, 
    PriceDataSource, 
    price_freshness_validator
)


class FallbackStrategy(Enum):
    """Fallback strategy types"""
    SEQUENTIAL = "sequential"  # Try sources in order
    PARALLEL = "parallel"      # Try all sources simultaneously
    WEIGHTED = "weighted"      # Use weighted selection based on reliability


@dataclass
class PriceSourceConfig:
    """Configuration for a price data source"""
    source: PriceDataSource
    priority: int  # Lower number = higher priority
    weight: float  # Weight for weighted strategy (0.0 - 1.0)
    timeout_seconds: int = 10
    max_retries: int = 3
    circuit_breaker_threshold: float = 0.5  # Failure rate threshold
    circuit_breaker_window: int = 300  # Time window in seconds
    enabled: bool = True


@dataclass
class FallbackResult:
    """Result from fallback system"""
    price_data: Optional[PriceDataPoint]
    source_used: Optional[PriceDataSource]
    sources_tried: List[PriceDataSource]
    sources_failed: List[Tuple[PriceDataSource, str]]
    execution_time_ms: int
    fallback_triggered: bool


class CircuitBreaker:
    """Circuit breaker for price sources"""
    
    def __init__(self, failure_threshold: float, time_window: int):
        self.failure_threshold = failure_threshold
        self.time_window = time_window
        self.failures = []
        self.is_open = False
        self.last_failure_time = None
        self.recovery_timeout = 60  # 1 minute recovery timeout
    
    def record_success(self):
        """Record successful operation"""
        self.is_open = False
        # Keep only recent failures
        cutoff_time = datetime.now() - timedelta(seconds=self.time_window)
        self.failures = [f for f in self.failures if f > cutoff_time]
    
    def record_failure(self):
        """Record failed operation"""
        now = datetime.now()
        self.failures.append(now)
        self.last_failure_time = now
        
        # Clean old failures
        cutoff_time = now - timedelta(seconds=self.time_window)
        self.failures = [f for f in self.failures if f > cutoff_time]
        
        # Check if we should open the circuit
        if len(self.failures) > 0:
            failure_rate = len(self.failures) / max(1, self.time_window / 60)  # failures per minute
            if failure_rate >= self.failure_threshold:
                self.is_open = True
    
    def can_execute(self) -> bool:
        """Check if operation can be executed"""
        if not self.is_open:
            return True
        
        # Check if recovery timeout has passed
        if self.last_failure_time:
            time_since_failure = (datetime.now() - self.last_failure_time).total_seconds()
            if time_since_failure >= self.recovery_timeout:
                self.is_open = False
                return True
        
        return False


class PriceFeedFallbackSystem:
    """Comprehensive price feed fallback system"""
    
    def __init__(self, strategy: FallbackStrategy = FallbackStrategy.SEQUENTIAL):
        self.strategy = strategy
        self.logger = logging.getLogger(__name__)
        
        # Source configurations
        self.source_configs: Dict[PriceDataSource, PriceSourceConfig] = {
            PriceDataSource.UNISWAP_V3: PriceSourceConfig(
                source=PriceDataSource.UNISWAP_V3,
                priority=1,
                weight=0.4,
                timeout_seconds=10,
                max_retries=2
            ),
            PriceDataSource.JUPITER: PriceSourceConfig(
                source=PriceDataSource.JUPITER,
                priority=2,
                weight=0.35,
                timeout_seconds=8,
                max_retries=2
            ),
            PriceDataSource.COINGECKO: PriceSourceConfig(
                source=PriceDataSource.COINGECKO,
                priority=3,
                weight=0.25,
                timeout_seconds=15,
                max_retries=3
            )
        }
        
        # Circuit breakers for each source
        self.circuit_breakers: Dict[PriceDataSource, CircuitBreaker] = {}
        for source, config in self.source_configs.items():
            self.circuit_breakers[source] = CircuitBreaker(
                config.circuit_breaker_threshold,
                config.circuit_breaker_window
            )
        
        # Source reliability monitoring
        self.source_metrics: Dict[PriceDataSource, Dict[str, Any]] = defaultdict(lambda: {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "avg_response_time": 0.0,
            "last_success": None,
            "last_failure": None
        })
    
    async def get_price_with_fallback(self, token_a: str, token_b: str, chain_id: Optional[int] = None) -> FallbackResult:
        """Get price with automatic fallback"""
        start_time = datetime.now()
        sources_tried = []
        sources_failed = []
        
        if self.strategy == FallbackStrategy.SEQUENTIAL:
            result = await self._sequential_fallback(token_a, token_b, chain_id, sources_tried, sources_failed)
        elif self.strategy == FallbackStrategy.PARALLEL:
            result = await self._parallel_fallback(token_a, token_b, chain_id, sources_tried, sources_failed)
        elif self.strategy == FallbackStrategy.WEIGHTED:
            result = await self._weighted_fallback(token_a, token_b, chain_id, sources_tried, sources_failed)
        else:
            result = None
        
        execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return FallbackResult(
            price_data=result[0] if result else None,
            source_used=result[1] if result else None,
            sources_tried=sources_tried,
            sources_failed=sources_failed,
            execution_time_ms=execution_time,
            fallback_triggered=len(sources_tried) > 1
        )
    
    async def _sequential_fallback(self, token_a: str, token_b: str, chain_id: Optional[int], 
                                 sources_tried: List, sources_failed: List) -> Optional[Tuple[PriceDataPoint, PriceDataSource]]:
        """Try sources sequentially in priority order"""
        # Sort sources by priority
        sorted_sources = sorted(
            [(source, config) for source, config in self.source_configs.items() if config.enabled],
            key=lambda x: x[1].priority
        )
        
        for source, config in sorted_sources:
            if not self.circuit_breakers[source].can_execute():
                self.logger.warning(f"Circuit breaker open for {source.value}, skipping")
                continue
            
            sources_tried.append(source)
            
            try:
                price_data = await self._fetch_from_source(source, token_a, token_b, chain_id, config)
                if price_data:
                    self._record_success(source)
                    return price_data, source
                else:
                    self._record_failure(source, "No data returned")
                    sources_failed.append((source, "No data returned"))
            
            except Exception as e:
                error_msg = str(e)
                self._record_failure(source, error_msg)
                sources_failed.append((source, error_msg))
                self.logger.error(f"Error fetching from {source.value}: {error_msg}")
        
        return None
    
    async def _parallel_fallback(self, token_a: str, token_b: str, chain_id: Optional[int],
                               sources_tried: List, sources_failed: List) -> Optional[Tuple[PriceDataPoint, PriceDataSource]]:
        """Try all sources in parallel and return first successful result"""
        enabled_sources = [(source, config) for source, config in self.source_configs.items() 
                          if config.enabled and self.circuit_breakers[source].can_execute()]
        
        if not enabled_sources:
            return None
        
        # Create tasks for all sources
        tasks = []
        source_map = {}
        
        for source, config in enabled_sources:
            sources_tried.append(source)
            task = asyncio.create_task(self._fetch_from_source_with_timeout(source, token_a, token_b, chain_id, config))
            tasks.append(task)
            source_map[task] = source
        
        # Wait for first successful result
        try:
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            
            # Cancel pending tasks
            for task in pending:
                task.cancel()
            
            # Check completed tasks
            for task in done:
                source = source_map[task]
                try:
                    result = await task
                    if result:
                        self._record_success(source)
                        return result, source
                    else:
                        self._record_failure(source, "No data returned")
                        sources_failed.append((source, "No data returned"))
                except Exception as e:
                    error_msg = str(e)
                    self._record_failure(source, error_msg)
                    sources_failed.append((source, error_msg))
            
            # If no successful results, wait for all to complete to collect errors
            if pending:
                await asyncio.gather(*pending, return_exceptions=True)
        
        except Exception as e:
            self.logger.error(f"Error in parallel fallback: {e}")
        
        return None
    
    async def _weighted_fallback(self, token_a: str, token_b: str, chain_id: Optional[int],
                               sources_tried: List, sources_failed: List) -> Optional[Tuple[PriceDataPoint, PriceDataSource]]:
        """Use weighted selection based on reliability"""
        # Calculate dynamic weights based on reliability
        weights = self._calculate_dynamic_weights()
        
        # Sort sources by dynamic weight
        sorted_sources = sorted(
            [(source, config, weights.get(source, 0)) for source, config in self.source_configs.items() 
             if config.enabled and self.circuit_breakers[source].can_execute()],
            key=lambda x: x[2],
            reverse=True
        )
        
        # Try sources in weighted order
        for source, config, weight in sorted_sources:
            sources_tried.append(source)
            
            try:
                price_data = await self._fetch_from_source(source, token_a, token_b, chain_id, config)
                if price_data:
                    self._record_success(source)
                    return price_data, source
                else:
                    self._record_failure(source, "No data returned")
                    sources_failed.append((source, "No data returned"))
            
            except Exception as e:
                error_msg = str(e)
                self._record_failure(source, error_msg)
                sources_failed.append((source, error_msg))
        
        return None
    
    async def _fetch_from_source_with_timeout(self, source: PriceDataSource, token_a: str, token_b: str, 
                                            chain_id: Optional[int], config: PriceSourceConfig) -> Optional[PriceDataPoint]:
        """Fetch from source with timeout"""
        try:
            return await asyncio.wait_for(
                self._fetch_from_source(source, token_a, token_b, chain_id, config),
                timeout=config.timeout_seconds
            )
        except asyncio.TimeoutError:
            raise Exception(f"Timeout after {config.timeout_seconds}s")
    
    async def _fetch_from_source(self, source: PriceDataSource, token_a: str, token_b: str, 
                               chain_id: Optional[int], config: PriceSourceConfig) -> Optional[PriceDataPoint]:
        """Fetch price data from specific source with retries"""
        last_exception = None
        
        for attempt in range(config.max_retries + 1):
            try:
                if source == PriceDataSource.UNISWAP_V3 and chain_id:
                    from src.services.uniswap_v3_service import uniswap_v3_service
                    quote = await uniswap_v3_service.get_quote(token_a, token_b, 10**18, chain_id)
                    if quote:
                        return PriceDataPoint(
                            price=quote.price,
                            timestamp=quote.timestamp,
                            source=source,
                            token_pair=f"{token_a}/{token_b}",
                            chain_id=chain_id,
                            is_fresh=True,
                            staleness_seconds=0
                        )
                
                elif source == PriceDataSource.JUPITER:
                    from src.services.jupiter_service import jupiter_service
                    quote = await jupiter_service.get_quote(token_a, token_b, 10**6)
                    if quote:
                        price = Decimal(quote.out_amount) / Decimal(quote.in_amount)
                        return PriceDataPoint(
                            price=price,
                            timestamp=quote.timestamp,
                            source=source,
                            token_pair=f"{token_a}/{token_b}",
                            is_fresh=True,
                            staleness_seconds=0
                        )
                
                elif source == PriceDataSource.COINGECKO:
                    from src.services.price_service import price_service
                    coingecko_id = price_service.get_coingecko_id(token_a, chain_id or 1)
                    if coingecko_id:
                        price = await price_service.get_token_price(coingecko_id)
                        if price:
                            return PriceDataPoint(
                                price=price,
                                timestamp=datetime.now(),
                                source=source,
                                token_pair=f"{coingecko_id}/USD",
                                chain_id=chain_id,
                                is_fresh=True,
                                staleness_seconds=0
                            )
                
                return None
            
            except Exception as e:
                last_exception = e
                if attempt < config.max_retries:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                continue
        
        if last_exception:
            raise last_exception
        return None
    
    def _calculate_dynamic_weights(self) -> Dict[PriceDataSource, float]:
        """Calculate dynamic weights based on source reliability"""
        weights = {}
        
        for source, config in self.source_configs.items():
            metrics = self.source_metrics[source]
            base_weight = config.weight
            
            # Adjust weight based on success rate
            total_requests = metrics["total_requests"]
            if total_requests > 0:
                success_rate = metrics["successful_requests"] / total_requests
                reliability_multiplier = success_rate
            else:
                reliability_multiplier = 1.0
            
            # Adjust weight based on response time
            avg_response_time = metrics["avg_response_time"]
            if avg_response_time > 0:
                # Penalize slow sources
                time_multiplier = max(0.1, 1.0 - (avg_response_time / 10.0))
            else:
                time_multiplier = 1.0
            
            # Calculate final weight
            final_weight = base_weight * reliability_multiplier * time_multiplier
            weights[source] = final_weight
        
        return weights
    
    def _record_success(self, source: PriceDataSource):
        """Record successful operation"""
        self.circuit_breakers[source].record_success()
        metrics = self.source_metrics[source]
        metrics["total_requests"] += 1
        metrics["successful_requests"] += 1
        metrics["last_success"] = datetime.now()
    
    def _record_failure(self, source: PriceDataSource, error: str):
        """Record failed operation"""
        self.circuit_breakers[source].record_failure()
        metrics = self.source_metrics[source]
        metrics["total_requests"] += 1
        metrics["failed_requests"] += 1
        metrics["last_failure"] = datetime.now()
        self.logger.warning(f"Source {source.value} failed: {error}")
    
    def get_source_health_status(self) -> Dict[str, Any]:
        """Get health status of all price sources"""
        status = {
            "overall_health": "healthy",
            "sources": {},
            "strategy": self.strategy.value,
            "timestamp": datetime.now().isoformat()
        }
        
        unhealthy_count = 0
        
        for source, config in self.source_configs.items():
            metrics = self.source_metrics[source]
            circuit_breaker = self.circuit_breakers[source]
            
            # Calculate success rate
            total_requests = metrics["total_requests"]
            success_rate = (metrics["successful_requests"] / total_requests) if total_requests > 0 else 1.0
            
            # Determine health status
            if not config.enabled:
                health = "disabled"
            elif circuit_breaker.is_open:
                health = "circuit_open"
                unhealthy_count += 1
            elif success_rate < 0.5:
                health = "unhealthy"
                unhealthy_count += 1
            elif success_rate < 0.8:
                health = "degraded"
            else:
                health = "healthy"
            
            source_status = {
                "health": health,
                "enabled": config.enabled,
                "circuit_breaker_open": circuit_breaker.is_open,
                "success_rate": success_rate,
                "total_requests": total_requests,
                "avg_response_time": metrics["avg_response_time"],
                "last_success": metrics["last_success"].isoformat() if metrics["last_success"] else None,
                "last_failure": metrics["last_failure"].isoformat() if metrics["last_failure"] else None,
                "priority": config.priority,
                "weight": config.weight
            }
            
            status["sources"][source.value] = source_status
        
        # Determine overall health
        total_sources = len([c for c in self.source_configs.values() if c.enabled])
        if unhealthy_count >= total_sources:
            status["overall_health"] = "critical"
        elif unhealthy_count > 0:
            status["overall_health"] = "degraded"
        
        return status
    
    def configure_source(self, source: PriceDataSource, **kwargs):
        """Configure a price source"""
        if source in self.source_configs:
            config = self.source_configs[source]
            for key, value in kwargs.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            
            # Update circuit breaker if thresholds changed
            if 'circuit_breaker_threshold' in kwargs or 'circuit_breaker_window' in kwargs:
                self.circuit_breakers[source] = CircuitBreaker(
                    config.circuit_breaker_threshold,
                    config.circuit_breaker_window
                )
    
    def enable_source(self, source: PriceDataSource):
        """Enable a price source"""
        if source in self.source_configs:
            self.source_configs[source].enabled = True
    
    def disable_source(self, source: PriceDataSource):
        """Disable a price source"""
        if source in self.source_configs:
            self.source_configs[source].enabled = False
    
    def reset_circuit_breaker(self, source: PriceDataSource):
        """Reset circuit breaker for a source"""
        if source in self.circuit_breakers:
            self.circuit_breakers[source].is_open = False
            self.circuit_breakers[source].failures = []


# Global instance
price_feed_fallback = PriceFeedFallbackSystem()