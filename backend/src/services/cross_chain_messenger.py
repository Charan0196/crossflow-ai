"""
Cross-Chain Messenger service with protocol selection logic
Integrates LayerZero V2 and Chainlink CCIP for secure cross-chain messaging
"""
import asyncio
import json
import logging
import time
from typing import Dict, Optional, List, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
from decimal import Decimal

from .layerzero_service import layerzero_service, LayerZeroService
from .ccip_service import ccip_service, CCIPService
from .retry_service import retry_service, RetryConfig, CircuitBreakerConfig
from .communication_logger import (
    communication_logger, 
    MessageType, 
    EventType,
    CommunicationLogger
)


logger = logging.getLogger(__name__)


class Protocol(Enum):
    """Supported cross-chain protocols"""
    LAYERZERO = "layerzero"
    CCIP = "ccip"


@dataclass
class MessageParams:
    """Parameters for cross-chain message"""
    source_chain: int
    destination_chain: int
    payload: bytes
    recipient: str
    gas_limit: int = 200000
    value_threshold: float = 10000.0  # USD threshold for protocol selection


@dataclass
class MessageResult:
    """Result of message sending operation"""
    message_id: str
    protocol: Protocol
    status: str
    estimated_fee: Dict
    transaction_hash: Optional[str] = None


@dataclass
class VerificationResult:
    """Result of message verification"""
    message_id: str
    verified: bool
    protocol: Protocol
    block_number: int
    timestamp: int


@dataclass
class MessageStatus:
    """Status of cross-chain message"""
    message_id: str
    status: str
    protocol: Protocol
    confirmations: int
    delivery_time: Optional[str] = None


class CrossChainMessenger:
    """
    Main cross-chain messaging service with intelligent protocol selection
    """
    
    def __init__(self):
        self.layerzero = layerzero_service
        self.ccip = ccip_service
        self.retry_service = retry_service
        self.logger = communication_logger
        self.protocol_preferences = self._initialize_protocol_preferences()
        self._initialize_retry_configs()
    
    def _initialize_protocol_preferences(self) -> Dict[str, Protocol]:
        """Initialize protocol preferences for different scenarios"""
        return {
            "high_frequency": Protocol.LAYERZERO,  # Lower fees, faster
            "high_value": Protocol.CCIP,           # Higher security
            "default": Protocol.LAYERZERO          # Default choice
        }
    
    def _initialize_retry_configs(self):
        """Initialize retry configurations for different operations"""
        self.retry_configs = {
            "send_message": RetryConfig(
                max_attempts=5,
                base_delay=2.0,
                max_delay=30.0,
                backoff_multiplier=2.0,
                jitter=True
            ),
            "verify_message": RetryConfig(
                max_attempts=3,
                base_delay=1.0,
                max_delay=10.0,
                backoff_multiplier=1.5,
                jitter=True
            ),
            "get_status": RetryConfig(
                max_attempts=3,
                base_delay=0.5,
                max_delay=5.0,
                backoff_multiplier=2.0,
                jitter=True
            )
        }
        
        self.circuit_configs = {
            "layerzero_send": CircuitBreakerConfig(
                failure_threshold=5,
                recovery_timeout=60.0,
                half_open_max_calls=3
            ),
            "ccip_send": CircuitBreakerConfig(
                failure_threshold=5,
                recovery_timeout=60.0,
                half_open_max_calls=3
            ),
            "message_verification": CircuitBreakerConfig(
                failure_threshold=3,
                recovery_timeout=30.0,
                half_open_max_calls=2
            )
        }
    
    def select_protocol(
        self, 
        source_chain: int, 
        destination_chain: int, 
        value_usd: float = 0.0,
        message_type: str = "default"
    ) -> Protocol:
        """
        Select optimal protocol based on trade value and message type
        
        Selection Logic:
        - CCIP for high-value transactions (>$10,000) requiring maximum security
        - LayerZero for high-frequency, low-cost messaging
        - Fallback based on chain support
        """
        try:
            # Check chain support for both protocols
            lz_supported = (self.layerzero.is_chain_supported(source_chain) and 
                           self.layerzero.is_chain_supported(destination_chain))
            ccip_supported = (self.ccip.is_chain_supported(source_chain) and 
                             self.ccip.is_chain_supported(destination_chain))
            
            alternatives = []
            if lz_supported:
                alternatives.append("layerzero")
            if ccip_supported:
                alternatives.append("ccip")
            
            selected_protocol = None
            reason = ""
            
            # High-value transactions use CCIP for maximum security
            if value_usd > 10000.0 and ccip_supported:
                selected_protocol = Protocol.CCIP
                reason = f"High-value transaction (${value_usd}) requires maximum security"
                logger.info(f"Selected CCIP for high-value transaction: ${value_usd}")
            
            # High-frequency trading prefers LayerZero for lower costs
            elif message_type == "high_frequency" and lz_supported:
                selected_protocol = Protocol.LAYERZERO
                reason = "High-frequency trading optimized for lower costs"
                logger.info("Selected LayerZero for high-frequency trading")
            
            # Default preference is LayerZero if supported
            elif lz_supported:
                selected_protocol = Protocol.LAYERZERO
                reason = "Default protocol preference"
                logger.info("Selected LayerZero as default protocol")
            
            # Fallback to CCIP if LayerZero not supported
            elif ccip_supported:
                selected_protocol = Protocol.CCIP
                reason = "LayerZero not supported, using CCIP fallback"
                logger.info("Selected CCIP as fallback protocol")
            
            # No protocol supports this chain pair
            else:
                reason = f"No protocol supports chain pair: {source_chain} -> {destination_chain}"
                logger.error(reason)
                raise ValueError(reason)
            
            # Log protocol selection
            self.logger.log_protocol_selection(
                source_chain=source_chain,
                destination_chain=destination_chain,
                selected_protocol=selected_protocol.value,
                reason=reason,
                alternatives=alternatives,
                details={
                    "value_usd": value_usd,
                    "message_type": message_type,
                    "lz_supported": lz_supported,
                    "ccip_supported": ccip_supported
                }
            )
            
            return selected_protocol
            
        except Exception as e:
            logger.error(f"Error selecting protocol: {e}")
            # Log the error
            self.logger.log_message_failed(
                message_type=MessageType.STATUS_UPDATE,
                protocol="unknown",
                source_chain=source_chain,
                destination_chain=destination_chain,
                operation_id=f"protocol_selection_{source_chain}_{destination_chain}",
                error_message=str(e),
                details={
                    "value_usd": value_usd,
                    "message_type": message_type
                }
            )
            # Default fallback
            return Protocol.LAYERZERO
    
    async def send_message(self, params: MessageParams) -> Optional[MessageResult]:
        """Send cross-chain message using optimal protocol with retry logic"""
        start_time = time.time()
        operation_id = f"send_{params.source_chain}_{params.destination_chain}_{int(start_time)}"
        
        try:
            # Select protocol based on parameters
            protocol = self.select_protocol(
                params.source_chain,
                params.destination_chain,
                params.value_threshold
            )
            
            logger.info(f"Sending message via {protocol.value} with retry logic")
            
            # Define the actual send operation
            async def _send_operation():
                if protocol == Protocol.LAYERZERO:
                    return await self.layerzero.send_message(
                        params.source_chain,
                        params.destination_chain,
                        params.payload,
                        params.recipient,
                        params.gas_limit
                    )
                else:  # CCIP
                    return await self.ccip.send_message(
                        params.source_chain,
                        params.destination_chain,
                        params.recipient,
                        params.payload,
                        gas_limit=params.gas_limit
                    )
            
            # Execute with retry logic
            protocol_operation_id = f"{protocol.value}_send_{params.source_chain}_{params.destination_chain}"
            retry_result = await self.retry_service.retry_with_backoff(
                _send_operation,
                protocol_operation_id,
                self.retry_configs["send_message"],
                self.circuit_configs[f"{protocol.value}_send"]
            )
            
            execution_time_ms = (time.time() - start_time) * 1000
            
            if not retry_result.success:
                error_msg = f"Failed to send message after {retry_result.attempts} attempts: {retry_result.last_error}"
                logger.error(error_msg)
                
                # Log failure
                self.logger.log_message_failed(
                    message_type=MessageType.INTENT_BROADCAST,  # Default type
                    protocol=protocol.value,
                    source_chain=params.source_chain,
                    destination_chain=params.destination_chain,
                    operation_id=operation_id,
                    error_message=str(retry_result.last_error),
                    retry_attempt=retry_result.attempts,
                    details={
                        "payload_size": len(params.payload),
                        "gas_limit": params.gas_limit,
                        "recipient": params.recipient,
                        "execution_time_ms": execution_time_ms
                    }
                )
                
                return None
            
            result = retry_result.result
            if not result:
                logger.error(f"No result from {protocol.value} send operation")
                
                # Log failure
                self.logger.log_message_failed(
                    message_type=MessageType.INTENT_BROADCAST,
                    protocol=protocol.value,
                    source_chain=params.source_chain,
                    destination_chain=params.destination_chain,
                    operation_id=operation_id,
                    error_message="No result from send operation",
                    details={
                        "payload_size": len(params.payload),
                        "gas_limit": params.gas_limit
                    }
                )
                
                return None
            
            # Log successful message sending
            self.logger.log_message_sent(
                message_type=MessageType.INTENT_BROADCAST,
                protocol=protocol.value,
                source_chain=params.source_chain,
                destination_chain=params.destination_chain,
                message_id=result["message_id"],
                operation_id=operation_id,
                execution_time_ms=execution_time_ms,
                fee_paid=result["estimated_fee"].get("native_fee") or result["estimated_fee"].get("fee"),
                details={
                    "payload_size": len(params.payload),
                    "gas_limit": params.gas_limit,
                    "recipient": params.recipient,
                    "retry_attempts": retry_result.attempts,
                    "estimated_fee": result["estimated_fee"]
                }
            )
            
            return MessageResult(
                message_id=result["message_id"],
                protocol=protocol,
                status=result["status"],
                estimated_fee=result["estimated_fee"]
            )
            
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Error sending cross-chain message: {e}")
            
            # Log exception
            self.logger.log_message_failed(
                message_type=MessageType.INTENT_BROADCAST,
                protocol="unknown",
                source_chain=params.source_chain,
                destination_chain=params.destination_chain,
                operation_id=operation_id,
                error_message=str(e),
                details={
                    "payload_size": len(params.payload),
                    "gas_limit": params.gas_limit,
                    "execution_time_ms": execution_time_ms
                }
            )
            
            return None
    
    async def verify_message(self, message_id: str, source_chain: int, protocol: Protocol) -> Optional[VerificationResult]:
        """Verify message authenticity using specified protocol with retry logic"""
        start_time = time.time()
        
        try:
            # Define the verification operation
            async def _verify_operation():
                if protocol == Protocol.LAYERZERO:
                    return await self.layerzero.verify_message(message_id, source_chain)
                else:  # CCIP
                    return await self.ccip.verify_message(message_id, source_chain)
            
            # Execute with retry logic
            operation_id = f"verify_{protocol.value}_{source_chain}"
            retry_result = await self.retry_service.retry_with_backoff(
                _verify_operation,
                operation_id,
                self.retry_configs["verify_message"],
                self.circuit_configs["message_verification"]
            )
            
            execution_time_ms = (time.time() - start_time) * 1000
            
            if not retry_result.success:
                error_msg = f"Failed to verify message after {retry_result.attempts} attempts: {retry_result.last_error}"
                logger.error(error_msg)
                
                # Log verification failure
                self.logger.log_message_failed(
                    message_type=MessageType.VERIFICATION,
                    protocol=protocol.value,
                    source_chain=source_chain,
                    destination_chain=0,
                    operation_id=f"verify_{message_id}",
                    error_message=str(retry_result.last_error),
                    retry_attempt=retry_result.attempts,
                    details={
                        "message_id": message_id,
                        "execution_time_ms": execution_time_ms
                    }
                )
                
                return None
            
            result = retry_result.result
            if not result:
                # Log verification failure
                self.logger.log_message_failed(
                    message_type=MessageType.VERIFICATION,
                    protocol=protocol.value,
                    source_chain=source_chain,
                    destination_chain=0,
                    operation_id=f"verify_{message_id}",
                    error_message="No verification result returned",
                    details={
                        "message_id": message_id,
                        "execution_time_ms": execution_time_ms
                    }
                )
                return None
            
            # Log verification result
            self.logger.log_message_verified(
                message_type=MessageType.VERIFICATION,
                protocol=protocol.value,
                source_chain=source_chain,
                message_id=message_id,
                verified=result["verified"],
                details={
                    "block_number": result["block_number"],
                    "timestamp": result["timestamp"],
                    "execution_time_ms": execution_time_ms,
                    "retry_attempts": retry_result.attempts
                }
            )
            
            return VerificationResult(
                message_id=message_id,
                verified=result["verified"],
                protocol=protocol,
                block_number=result["block_number"],
                timestamp=result["timestamp"]
            )
            
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Error verifying message: {e}")
            
            # Log exception
            self.logger.log_message_failed(
                message_type=MessageType.VERIFICATION,
                protocol=protocol.value,
                source_chain=source_chain,
                destination_chain=0,
                operation_id=f"verify_{message_id}",
                error_message=str(e),
                details={
                    "message_id": message_id,
                    "execution_time_ms": execution_time_ms
                }
            )
            
            return None
    
    async def get_message_status(self, message_id: str, source_chain: int, protocol: Protocol) -> Optional[MessageStatus]:
        """Get message status using specified protocol with retry logic"""
        try:
            # Define the status operation
            async def _status_operation():
                if protocol == Protocol.LAYERZERO:
                    return await self.layerzero.get_message_status(message_id, source_chain)
                else:  # CCIP
                    return await self.ccip.get_message_status(message_id, source_chain)
            
            # Execute with retry logic
            operation_id = f"status_{protocol.value}_{source_chain}"
            retry_result = await self.retry_service.retry_with_backoff(
                _status_operation,
                operation_id,
                self.retry_configs["get_status"],
                self.circuit_configs["message_verification"]
            )
            
            if not retry_result.success:
                logger.error(f"Failed to get message status after {retry_result.attempts} attempts: {retry_result.last_error}")
                return None
            
            result = retry_result.result
            if not result:
                return None
            
            return MessageStatus(
                message_id=message_id,
                status=result["status"],
                protocol=protocol,
                confirmations=result["confirmations"],
                delivery_time=result.get("delivery_time")
            )
            
        except Exception as e:
            logger.error(f"Error getting message status: {e}")
            return None
    
    async def estimate_message_cost(self, params: MessageParams) -> Optional[Dict]:
        """Estimate costs for both protocols and return comparison"""
        try:
            costs = {}
            
            # Estimate LayerZero cost
            if (self.layerzero.is_chain_supported(params.source_chain) and 
                self.layerzero.is_chain_supported(params.destination_chain)):
                lz_cost = await self.layerzero.estimate_fees(
                    params.source_chain,
                    params.destination_chain,
                    params.payload,
                    params.gas_limit
                )
                if lz_cost:
                    costs["layerzero"] = lz_cost
            
            # Estimate CCIP cost
            if (self.ccip.is_chain_supported(params.source_chain) and 
                self.ccip.is_chain_supported(params.destination_chain)):
                ccip_cost = await self.ccip.estimate_fees(
                    params.source_chain,
                    params.destination_chain,
                    params.payload,
                    gas_limit=params.gas_limit
                )
                if ccip_cost:
                    costs["ccip"] = ccip_cost
            
            # Add recommended protocol
            recommended = self.select_protocol(
                params.source_chain,
                params.destination_chain,
                params.value_threshold
            )
            
            return {
                "costs": costs,
                "recommended_protocol": recommended.value,
                "comparison": self._compare_costs(costs)
            }
            
        except Exception as e:
            logger.error(f"Error estimating message costs: {e}")
            return None
    
    def _compare_costs(self, costs: Dict) -> Dict:
        """Compare costs between protocols"""
        if not costs:
            return {}
        
        comparison = {}
        
        if "layerzero" in costs and "ccip" in costs:
            lz_fee = float(costs["layerzero"]["native_fee"])
            ccip_fee = float(costs["ccip"]["fee"])
            
            if lz_fee < ccip_fee:
                comparison["cheaper"] = "layerzero"
                comparison["savings"] = f"{((ccip_fee - lz_fee) / ccip_fee * 100):.1f}%"
            else:
                comparison["cheaper"] = "ccip"
                comparison["savings"] = f"{((lz_fee - ccip_fee) / lz_fee * 100):.1f}%"
        
        return comparison
    
    def get_supported_chains(self) -> Dict[str, List[int]]:
        """Get supported chains for each protocol"""
        return {
            "layerzero": self.layerzero.get_supported_chains(),
            "ccip": self.ccip.get_supported_chains(),
            "common": list(set(self.layerzero.get_supported_chains()) & 
                          set(self.ccip.get_supported_chains()))
        }
    
    def is_route_supported(self, source_chain: int, destination_chain: int) -> Dict[str, bool]:
        """Check if a route is supported by each protocol"""
        return {
            "layerzero": (self.layerzero.is_chain_supported(source_chain) and 
                         self.layerzero.is_chain_supported(destination_chain)),
            "ccip": (self.ccip.is_chain_supported(source_chain) and 
                    self.ccip.is_chain_supported(destination_chain))
        }
    
    def get_retry_statistics(self) -> Dict[str, Any]:
        """Get comprehensive retry statistics for all operations"""
        stats = {}
        
        # Get stats for all tracked operations
        for operation_type in ["send_message", "verify_message", "get_status"]:
            # Get stats for both protocols
            for protocol in ["layerzero", "ccip"]:
                operation_id = f"{protocol}_{operation_type}"
                stats[operation_id] = self.retry_service.get_retry_stats(operation_id)
        
        # Add circuit breaker status
        stats["circuit_breakers"] = self.retry_service.get_all_circuit_breaker_status()
        
        return stats
    
    def reset_retry_statistics(self):
        """Reset all retry statistics and circuit breakers"""
        self.retry_service.retry_stats.clear()
        for operation_id in self.retry_service.circuit_breakers.keys():
            self.retry_service.reset_circuit_breaker(operation_id)
        logger.info("Reset all retry statistics and circuit breakers")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on cross-chain messaging infrastructure"""
        health_status = {
            "timestamp": time.time(),
            "overall_status": "healthy",
            "protocols": {},
            "retry_stats": self.get_retry_statistics()
        }
        
        # Check LayerZero health
        try:
            lz_chains = self.layerzero.get_supported_chains()
            health_status["protocols"]["layerzero"] = {
                "status": "healthy",
                "supported_chains": len(lz_chains),
                "chains": lz_chains
            }
        except Exception as e:
            health_status["protocols"]["layerzero"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["overall_status"] = "degraded"
        
        # Check CCIP health
        try:
            ccip_chains = self.ccip.get_supported_chains()
            health_status["protocols"]["ccip"] = {
                "status": "healthy",
                "supported_chains": len(ccip_chains),
                "chains": ccip_chains
            }
        except Exception as e:
            health_status["protocols"]["ccip"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            if health_status["overall_status"] == "degraded":
                health_status["overall_status"] = "unhealthy"
            else:
                health_status["overall_status"] = "degraded"
        
        return health_status
    
    def get_communication_logs(
        self,
        limit: int = 100,
        event_type: Optional[str] = None,
        protocol: Optional[str] = None,
        source_chain: Optional[int] = None,
        hours_back: int = 24
    ) -> List[Dict]:
        """Get communication logs with filtering"""
        start_time = time.time() - (hours_back * 3600)
        
        # Convert string event_type to EventType enum if provided
        event_type_enum = None
        if event_type:
            try:
                event_type_enum = EventType(event_type)
            except ValueError:
                logger.warning(f"Invalid event type: {event_type}")
        
        logs = self.logger.get_logs(
            limit=limit,
            event_type=event_type_enum,
            protocol=protocol,
            source_chain=source_chain,
            start_time=start_time
        )
        
        # Convert to dictionaries for JSON serialization
        return [asdict(log) for log in logs]
    
    def get_communication_stats(self, hours_back: int = 24) -> Dict[str, Any]:
        """Get communication statistics"""
        start_time = time.time() - (hours_back * 3600)
        stats = self.logger.get_aggregated_stats(start_time=start_time)
        return asdict(stats)
    
    def export_communication_logs(
        self,
        format_type: str = "json",
        hours_back: int = 24
    ) -> str:
        """Export communication logs"""
        start_time = time.time() - (hours_back * 3600)
        return self.logger.export_logs(
            format_type=format_type,
            start_time=start_time
        )
    
    def clear_old_logs(self, older_than_hours: int = 168):  # Default 7 days
        """Clear old communication logs"""
        older_than_seconds = older_than_hours * 3600
        self.logger.clear_logs(older_than_seconds=older_than_seconds)
        logger.info(f"Cleared communication logs older than {older_than_hours} hours")


# Global instance
cross_chain_messenger = CrossChainMessenger()