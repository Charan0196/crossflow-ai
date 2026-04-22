"""
Solver Coordination Network Agent for CrossFlow AI Phase 2
Implements intelligent multi-agent solver coordination, capability management,
workload distribution, and conflict resolution using AI-powered algorithms.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import numpy as np
from collections import defaultdict

from src.models.solver import Solver, SolverStatus, SolverTier
from src.services.solver_network_service import SolverNetworkService

logger = logging.getLogger(__name__)


class CapabilityType(Enum):
    """Types of solver capabilities"""
    DEX_TRADING = "dex_trading"
    BRIDGE_OPERATIONS = "bridge_operations"
    ARBITRAGE_EXECUTION = "arbitrage_execution"
    LIQUIDITY_PROVISION = "liquidity_provision"
    FLASH_LOANS = "flash_loans"
    MEV_PROTECTION = "mev_protection"
    CROSS_CHAIN_MESSAGING = "cross_chain_messaging"
    YIELD_FARMING = "yield_farming"
    OPTIONS_TRADING = "options_trading"
    DERIVATIVES_TRADING = "derivatives_trading"


class WorkloadPriority(Enum):
    """Workload priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ConflictType(Enum):
    """Types of coordination conflicts"""
    RESOURCE_CONTENTION = "resource_contention"
    CAPABILITY_OVERLAP = "capability_overlap"
    PRIORITY_DISPUTE = "priority_dispute"
    EXECUTION_CONFLICT = "execution_conflict"
    REPUTATION_DISPUTE = "reputation_dispute"


@dataclass
class SolverCapability:
    """Detailed solver capability information"""
    capability_type: CapabilityType
    proficiency_score: float  # 0.0 to 1.0
    supported_chains: List[int]
    supported_tokens: List[str]
    max_volume_capacity: Decimal
    average_execution_time: float  # seconds
    success_rate: float  # 0.0 to 1.0
    last_updated: datetime = field(default_factory=datetime.now)
    
    def is_compatible_with(self, other: 'SolverCapability') -> bool:
        """Check if this capability is compatible with another"""
        return (
            self.capability_type == other.capability_type and
            bool(set(self.supported_chains) & set(other.supported_chains)) and
            bool(set(self.supported_tokens) & set(other.supported_tokens))
        )


@dataclass
class WorkloadTask:
    """Individual workload task for distribution"""
    task_id: str
    intent_hash: str
    capability_required: CapabilityType
    priority: WorkloadPriority
    estimated_volume: Decimal
    estimated_execution_time: float
    target_chains: List[int]
    required_tokens: List[str]
    deadline: datetime
    created_at: datetime = field(default_factory=datetime.now)
    assigned_solver: Optional[str] = None
    status: str = "pending"


@dataclass
class SolverHealthStatus:
    """Solver health monitoring information"""
    solver_address: str
    last_heartbeat: datetime
    response_time: float  # milliseconds
    success_rate: float  # 0.0 to 1.0
    error_count: int
    consecutive_failures: int
    is_healthy: bool = True
    health_score: float = 1.0  # 0.0 to 1.0
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class CoordinationConflict:
    """Coordination conflict information"""
    conflict_id: str
    conflict_type: ConflictType
    involved_solvers: List[str]
    resource_contested: str
    priority_levels: Dict[str, int]
    created_at: datetime
    resolved_at: Optional[datetime] = None
    resolution_method: Optional[str] = None
    winner: Optional[str] = None


class SolverCoordinationNetwork:
    """
    AI-powered Solver Coordination Network for CrossFlow Phase 2
    Implements intelligent multi-agent solver coordination, capability management,
    workload distribution, and conflict resolution.
    """
    
    def __init__(self, solver_network_service: SolverNetworkService):
        self.solver_network_service = solver_network_service
        
        # Solver Registry and Capability Management
        self.solver_capabilities: Dict[str, List[SolverCapability]] = {}
        self.capability_index: Dict[CapabilityType, Set[str]] = defaultdict(set)
        self.solver_health_status: Dict[str, SolverHealthStatus] = {}
        
        # Workload Distribution
        self.pending_tasks: Dict[str, WorkloadTask] = {}
        self.active_tasks: Dict[str, WorkloadTask] = {}
        self.completed_tasks: Dict[str, WorkloadTask] = {}
        self.workload_distribution_history: List[Dict] = []
        
        # Multi-Solver Orchestration
        self.orchestration_sessions: Dict[str, Dict] = {}
        self.capability_combinations: Dict[str, List[str]] = {}
        
        # Reputation and Performance Tracking
        self.solver_performance_history: Dict[str, List[Dict]] = defaultdict(list)
        self.reputation_decay_rate = 0.01  # Daily decay
        
        # Conflict Resolution
        self.active_conflicts: Dict[str, Any] = {}
        self.resolved_conflicts: Dict[str, Any] = {}
        self.conflict_resolution_history: List[Any] = []
        self.dispute_arbitrations: Dict[str, Any] = {}
        self.early_warnings: Dict[str, Any] = {}
        
        # Task Assignments (for conflict detection)
        self.solver_task_assignments: Dict[str, List[Dict]] = defaultdict(list)
        self.solver_capacity: Dict[str, Dict] = {}
        
        # Configuration
        self.health_check_interval = 60  # seconds
        self.capability_refresh_interval = 300  # 5 minutes
        self.max_concurrent_tasks_per_solver = 5
        
        # Background tasks
        self._health_monitor_task = None
        self._capability_refresh_task = None
        self._conflict_resolution_task = None
        self._reputation_decay_task = None
        
        logger.info("Solver Coordination Network initialized")
    
    async def start_coordination_network(self):
        """Start the coordination network and background tasks"""
        try:
            # Start background monitoring tasks
            self._health_monitor_task = asyncio.create_task(self._monitor_solver_health())
            self._capability_refresh_task = asyncio.create_task(self._refresh_solver_capabilities())
            self._conflict_resolution_task = asyncio.create_task(self._monitor_conflicts())
            self._reputation_decay_task = asyncio.create_task(self._monitor_reputation_decay())
            
            logger.info("Solver Coordination Network started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start coordination network: {e}")
            return False
    
    async def stop_coordination_network(self):
        """Stop the coordination network and cleanup"""
        try:
            # Cancel background tasks
            if self._health_monitor_task:
                self._health_monitor_task.cancel()
            if self._capability_refresh_task:
                self._capability_refresh_task.cancel()
            if self._conflict_resolution_task:
                self._conflict_resolution_task.cancel()
            if self._reputation_decay_task:
                self._reputation_decay_task.cancel()
            
            logger.info("Solver Coordination Network stopped")
            
        except Exception as e:
            logger.error(f"Error stopping coordination network: {e}")
    
    async def _monitor_reputation_decay(self):
        """Background task to apply reputation decay"""
        while True:
            try:
                await self.implement_reputation_decay()
                await asyncio.sleep(86400)  # Run daily
                
            except Exception as e:
                logger.error(f"Error in reputation decay task: {e}")
                await asyncio.sleep(86400)
    
    # Solver Registry and Capability Management
    
    async def register_solver_capabilities(
        self, 
        solver_address: str, 
        capabilities: List[SolverCapability]
    ) -> bool:
        """
        Register solver capabilities in the coordination network
        Requirements: 3.1, 3.4 - Solver capability assessment and categorization
        """
        try:
            # Validate solver exists in network service
            solver = await self.solver_network_service.get_solver_by_address(solver_address)
            if not solver:
                logger.error(f"Solver {solver_address} not found in network service")
                return False
            
            # Validate capabilities
            for capability in capabilities:
                if not self._validate_capability(capability, solver):
                    logger.error(f"Invalid capability {capability.capability_type} for solver {solver_address}")
                    return False
            
            # Store capabilities
            self.solver_capabilities[solver_address] = capabilities
            
            # Update capability index
            for capability in capabilities:
                self.capability_index[capability.capability_type].add(solver_address)
            
            # Initialize health status
            if solver_address not in self.solver_health_status:
                self.solver_health_status[solver_address] = SolverHealthStatus(
                    solver_address=solver_address,
                    last_heartbeat=datetime.now(),
                    response_time=0.0,
                    success_rate=1.0,
                    error_count=0,
                    consecutive_failures=0
                )
            
            logger.info(f"Registered {len(capabilities)} capabilities for solver {solver_address}")
            return True
            
        except Exception as e:
            logger.error(f"Error registering solver capabilities: {e}")
            return False
    
    async def update_solver_capability(
        self, 
        solver_address: str, 
        capability_type: CapabilityType,
        proficiency_score: float,
        success_rate: float,
        average_execution_time: float
    ) -> bool:
        """
        Update solver capability metrics based on performance
        Requirements: 3.1, 3.4 - Capability assessment and tracking
        """
        try:
            if solver_address not in self.solver_capabilities:
                logger.error(f"Solver {solver_address} capabilities not found")
                return False
            
            # Find and update the capability
            capabilities = self.solver_capabilities[solver_address]
            for capability in capabilities:
                if capability.capability_type == capability_type:
                    # Update metrics using exponential moving average
                    capability.proficiency_score = (
                        0.8 * capability.proficiency_score + 0.2 * proficiency_score
                    )
                    capability.success_rate = (
                        0.8 * capability.success_rate + 0.2 * success_rate
                    )
                    capability.average_execution_time = (
                        0.8 * capability.average_execution_time + 0.2 * average_execution_time
                    )
                    capability.last_updated = datetime.now()
                    
                    logger.info(f"Updated capability {capability_type} for solver {solver_address}")
                    return True
            
            logger.warning(f"Capability {capability_type} not found for solver {solver_address}")
            return False
            
        except Exception as e:
            logger.error(f"Error updating solver capability: {e}")
            return False
    
    async def get_solvers_by_capability(
        self, 
        capability_type: CapabilityType,
        min_proficiency: float = 0.7,
        required_chains: Optional[List[int]] = None,
        required_tokens: Optional[List[str]] = None
    ) -> List[Tuple[str, SolverCapability]]:
        """
        Get solvers with specific capability and requirements
        Requirements: 3.1 - Solver discovery and capability matching
        """
        try:
            matching_solvers = []
            
            # Get solvers with the required capability
            candidate_solvers = self.capability_index.get(capability_type, set())
            
            for solver_address in candidate_solvers:
                # Check if solver is healthy and active
                if not await self._is_solver_healthy_and_active(solver_address):
                    continue
                
                # Find the specific capability
                capabilities = self.solver_capabilities.get(solver_address, [])
                for capability in capabilities:
                    if capability.capability_type != capability_type:
                        continue
                    
                    # Check proficiency threshold
                    if capability.proficiency_score < min_proficiency:
                        continue
                    
                    # Check chain support
                    if required_chains and not any(
                        chain in capability.supported_chains for chain in required_chains
                    ):
                        continue
                    
                    # Check token support
                    if required_tokens and not any(
                        token in capability.supported_tokens for token in required_tokens
                    ):
                        continue
                    
                    matching_solvers.append((solver_address, capability))
                    break
            
            # Sort by proficiency score and success rate
            matching_solvers.sort(
                key=lambda x: (x[1].proficiency_score * x[1].success_rate), 
                reverse=True
            )
            
            logger.info(f"Found {len(matching_solvers)} solvers for capability {capability_type}")
            return matching_solvers
            
        except Exception as e:
            logger.error(f"Error getting solvers by capability: {e}")
            return []
    
    async def assess_solver_capacity(self, solver_address: str) -> Dict[str, Any]:
        """
        Assess current solver capacity and availability
        Requirements: 3.1, 3.4 - Solver availability and capacity tracking
        """
        try:
            # Get solver from network service
            solver = await self.solver_network_service.get_solver_by_address(solver_address)
            if not solver:
                return {"available": False, "reason": "solver_not_found"}
            
            # Check basic eligibility
            if not solver.is_eligible_for_intents:
                return {
                    "available": False, 
                    "reason": "not_eligible",
                    "status": solver.status.value
                }
            
            # Get health status
            health_status = self.solver_health_status.get(solver_address)
            if not health_status or not health_status.is_healthy:
                return {
                    "available": False,
                    "reason": "unhealthy",
                    "health_score": health_status.health_score if health_status else 0.0
                }
            
            # Calculate current load
            current_load = solver.current_concurrent_intents / solver.max_concurrent_intents
            
            # Get active tasks in coordination network
            active_coordination_tasks = sum(
                1 for task in self.active_tasks.values()
                if task.assigned_solver == solver_address
            )
            
            coordination_load = active_coordination_tasks / self.max_concurrent_tasks_per_solver
            
            # Calculate overall capacity
            overall_load = max(current_load, coordination_load)
            available_capacity = max(0.0, 1.0 - overall_load)
            
            # Get capabilities summary
            capabilities = self.solver_capabilities.get(solver_address, [])
            capability_summary = {
                cap.capability_type.value: {
                    "proficiency": cap.proficiency_score,
                    "success_rate": cap.success_rate,
                    "avg_execution_time": cap.average_execution_time
                }
                for cap in capabilities
            }
            
            return {
                "available": available_capacity > 0.1,  # At least 10% capacity
                "available_capacity": available_capacity,
                "current_load": overall_load,
                "concurrent_intents": solver.current_concurrent_intents,
                "max_concurrent_intents": solver.max_concurrent_intents,
                "coordination_tasks": active_coordination_tasks,
                "max_coordination_tasks": self.max_concurrent_tasks_per_solver,
                "health_score": health_status.health_score if health_status else 0.0,
                "reputation_score": solver.reputation_score.total_score,
                "capabilities": capability_summary,
                "last_seen": solver.last_seen.isoformat(),
                "tier": solver.tier.value
            }
            
        except Exception as e:
            logger.error(f"Error assessing solver capacity: {e}")
            return {"available": False, "reason": "assessment_error"}
    
    async def update_solver_health_status(
        self, 
        solver_address: str,
        response_time: float,
        success: bool,
        error_details: Optional[str] = None
    ) -> bool:
        """
        Update solver health status based on monitoring data
        Requirements: 3.1, 3.4 - Solver health monitoring and status updates
        """
        try:
            # Get or create health status
            if solver_address not in self.solver_health_status:
                self.solver_health_status[solver_address] = SolverHealthStatus(
                    solver_address=solver_address,
                    last_heartbeat=datetime.now(),
                    response_time=response_time,
                    success_rate=1.0 if success else 0.0,
                    error_count=0 if success else 1,
                    consecutive_failures=0 if success else 1
                )
            else:
                health_status = self.solver_health_status[solver_address]
                
                # Update metrics
                health_status.last_heartbeat = datetime.now()
                health_status.response_time = (
                    0.8 * health_status.response_time + 0.2 * response_time
                )
                
                # Update success rate using exponential moving average
                current_success = 1.0 if success else 0.0
                health_status.success_rate = (
                    0.9 * health_status.success_rate + 0.1 * current_success
                )
                
                # Update error tracking
                if success:
                    health_status.consecutive_failures = 0
                else:
                    health_status.error_count += 1
                    health_status.consecutive_failures += 1
                
                # Calculate health score
                health_status.health_score = self._calculate_health_score(health_status)
                
                # Determine if solver is healthy
                health_status.is_healthy = (
                    health_status.health_score > 0.7 and
                    health_status.consecutive_failures < 3 and
                    health_status.response_time < 5000  # 5 seconds max
                )
                
                health_status.last_updated = datetime.now()
            
            logger.debug(f"Updated health status for solver {solver_address}: healthy={self.solver_health_status[solver_address].is_healthy}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating solver health status: {e}")
            return False
    
    def _calculate_health_score(self, health_status: SolverHealthStatus) -> float:
        """Calculate overall health score from various metrics"""
        try:
            # Base score from success rate
            success_score = health_status.success_rate
            
            # Response time score (penalize slow responses)
            max_acceptable_time = 2000  # 2 seconds
            time_score = max(0.0, 1.0 - (health_status.response_time / max_acceptable_time))
            
            # Consecutive failure penalty
            failure_penalty = min(0.5, health_status.consecutive_failures * 0.1)
            
            # Time since last heartbeat penalty
            time_since_heartbeat = (datetime.now() - health_status.last_heartbeat).total_seconds()
            heartbeat_penalty = min(0.3, time_since_heartbeat / 300)  # 5 minutes max
            
            # Calculate overall score
            health_score = (
                success_score * 0.4 +
                time_score * 0.3 +
                (1.0 - failure_penalty) * 0.2 +
                (1.0 - heartbeat_penalty) * 0.1
            )
            
            return max(0.0, min(1.0, health_score))
            
        except Exception as e:
            logger.error(f"Error calculating health score: {e}")
            return 0.0
    
    async def get_solver_health_report(self, solver_address: str) -> Optional[Dict]:
        """Get comprehensive health report for a solver"""
        try:
            if solver_address not in self.solver_health_status:
                return None
            
            health_status = self.solver_health_status[solver_address]
            
            return {
                "solver_address": solver_address,
                "is_healthy": health_status.is_healthy,
                "health_score": health_status.health_score,
                "last_heartbeat": health_status.last_heartbeat.isoformat(),
                "response_time": health_status.response_time,
                "success_rate": health_status.success_rate,
                "error_count": health_status.error_count,
                "consecutive_failures": health_status.consecutive_failures,
                "last_updated": health_status.last_updated.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting health report: {e}")
            return None
    
    def _validate_capability(self, capability: SolverCapability, solver: Solver) -> bool:
        """Validate solver capability against solver configuration"""
        try:
            # Check if capability chains are supported by solver
            if not all(chain in solver.supported_chains for chain in capability.supported_chains):
                return False
            
            # Check if capability tokens are supported by solver
            if not all(token in solver.supported_tokens for token in capability.supported_tokens):
                return False
            
            # Validate proficiency score range
            if not (0.0 <= capability.proficiency_score <= 1.0):
                return False
            
            # Validate success rate range
            if not (0.0 <= capability.success_rate <= 1.0):
                return False
            
            # Validate execution time is positive
            if capability.average_execution_time <= 0:
                return False
            
            # Validate volume capacity is positive
            if capability.max_volume_capacity <= 0:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating capability: {e}")
            return False
    
    async def _is_solver_healthy_and_active(self, solver_address: str) -> bool:
        """Check if solver is healthy and active"""
        try:
            # Check solver status in network service
            solver = await self.solver_network_service.get_solver_by_address(solver_address)
            if not solver or not solver.is_eligible_for_intents:
                return False
            
            # Check health status
            health_status = self.solver_health_status.get(solver_address)
            if not health_status or not health_status.is_healthy:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking solver health: {e}")
            return False
    
    async def _monitor_solver_health(self):
        """Background task to monitor solver health"""
        while True:
            try:
                current_time = datetime.now()
                
                # Check all registered solvers
                for solver_address in list(self.solver_health_status.keys()):
                    health_status = self.solver_health_status[solver_address]
                    
                    # Check for stale heartbeat
                    time_since_heartbeat = (current_time - health_status.last_heartbeat).total_seconds()
                    
                    if time_since_heartbeat > 300:  # 5 minutes
                        # Mark as unhealthy due to stale heartbeat
                        health_status.is_healthy = False
                        health_status.health_score = max(0.0, health_status.health_score - 0.1)
                        logger.warning(f"Solver {solver_address} marked unhealthy due to stale heartbeat")
                    
                    # Perform active health check
                    await self._perform_health_check(solver_address)
                
                await asyncio.sleep(self.health_check_interval)
                
            except Exception as e:
                logger.error(f"Error in health monitoring task: {e}")
                await asyncio.sleep(self.health_check_interval)
    
    async def _perform_health_check(self, solver_address: str):
        """Perform active health check on solver"""
        try:
            # Get solver info
            solver = await self.solver_network_service.get_solver_by_address(solver_address)
            if not solver:
                return
            
            # Simulate health check (in production, would make actual HTTP request)
            start_time = datetime.now()
            
            # In production: make HTTP request to solver's health endpoint
            # For now, simulate based on solver status
            success = solver.status.value == "active"
            response_time = 100.0 if success else 5000.0  # Simulate response time
            
            # Update health status
            await self.update_solver_health_status(
                solver_address, 
                response_time, 
                success
            )
            
        except Exception as e:
            logger.error(f"Error performing health check for {solver_address}: {e}")
    
    async def _refresh_solver_capabilities(self):
        """Background task to refresh solver capabilities"""
        while True:
            try:
                # Refresh capabilities for all registered solvers
                for solver_address in list(self.solver_capabilities.keys()):
                    await self._refresh_single_solver_capabilities(solver_address)
                
                await asyncio.sleep(self.capability_refresh_interval)
                
            except Exception as e:
                logger.error(f"Error in capability refresh task: {e}")
                await asyncio.sleep(self.capability_refresh_interval)
    
    async def _refresh_single_solver_capabilities(self, solver_address: str):
        """Refresh capabilities for a single solver"""
        try:
            # In production, would query solver for updated capabilities
            # For now, just update the last_updated timestamp
            capabilities = self.solver_capabilities.get(solver_address, [])
            for capability in capabilities:
                capability.last_updated = datetime.now()
            
            logger.debug(f"Refreshed capabilities for solver {solver_address}")
            
        except Exception as e:
            logger.error(f"Error refreshing capabilities for {solver_address}: {e}")
    
    # Workload Distribution Optimization
    
    async def distribute_workload(
        self, 
        tasks: List[WorkloadTask],
        optimization_strategy: str = "balanced"
    ) -> Dict[str, List[WorkloadTask]]:
        """
        Distribute workload across available solvers using optimization algorithms
        Requirements: 3.2 - Capacity-aware workload distribution and load balancing
        """
        try:
            distribution = {}
            
            # Get available solvers for each task
            task_solver_mapping = {}
            for task in tasks:
                eligible_solvers = await self.get_solvers_by_capability(
                    task.capability_required,
                    required_chains=task.target_chains,
                    required_tokens=task.required_tokens
                )
                task_solver_mapping[task.task_id] = eligible_solvers
            
            # Apply distribution strategy
            if optimization_strategy == "balanced":
                distribution = await self._balanced_distribution(tasks, task_solver_mapping)
            elif optimization_strategy == "priority_based":
                distribution = await self._priority_based_distribution(tasks, task_solver_mapping)
            elif optimization_strategy == "capacity_optimized":
                distribution = await self._capacity_optimized_distribution(tasks, task_solver_mapping)
            else:
                logger.error(f"Unknown optimization strategy: {optimization_strategy}")
                return {}
            
            # Assign tasks to solvers
            for solver_address, assigned_tasks in distribution.items():
                for task in assigned_tasks:
                    task.assigned_solver = solver_address
                    task.status = "assigned"
                    self.active_tasks[task.task_id] = task
            
            # Record distribution for analysis
            self.workload_distribution_history.append({
                "timestamp": datetime.now(),
                "strategy": optimization_strategy,
                "total_tasks": len(tasks),
                "distribution": {addr: len(tasks) for addr, tasks in distribution.items()},
                "efficiency_score": await self._calculate_distribution_efficiency(distribution)
            })
            
            logger.info(f"Distributed {len(tasks)} tasks across {len(distribution)} solvers using {optimization_strategy} strategy")
            return distribution
            
        except Exception as e:
            logger.error(f"Error distributing workload: {e}")
            return {}
    
    async def _balanced_distribution(
        self, 
        tasks: List[WorkloadTask], 
        task_solver_mapping: Dict[str, List[Tuple[str, SolverCapability]]]
    ) -> Dict[str, List[WorkloadTask]]:
        """Balanced workload distribution algorithm"""
        try:
            distribution = defaultdict(list)
            solver_loads = defaultdict(float)
            
            # Sort tasks by priority and deadline
            sorted_tasks = sorted(
                tasks, 
                key=lambda t: (t.priority.value, t.deadline, t.estimated_execution_time)
            )
            
            for task in sorted_tasks:
                eligible_solvers = task_solver_mapping.get(task.task_id, [])
                if not eligible_solvers:
                    logger.warning(f"No eligible solvers for task {task.task_id}")
                    continue
                
                # Find solver with lowest current load
                best_solver = None
                min_load = float('inf')
                
                for solver_address, capability in eligible_solvers:
                    # Calculate current load including estimated task time
                    current_load = solver_loads[solver_address]
                    estimated_load = current_load + task.estimated_execution_time
                    
                    # Consider solver capacity
                    capacity_info = await self.assess_solver_capacity(solver_address)
                    if not capacity_info.get("available", False):
                        continue
                    
                    # Adjust load based on capability proficiency
                    adjusted_load = estimated_load / capability.proficiency_score
                    
                    if adjusted_load < min_load:
                        min_load = adjusted_load
                        best_solver = solver_address
                
                if best_solver:
                    distribution[best_solver].append(task)
                    solver_loads[best_solver] += task.estimated_execution_time
            
            return dict(distribution)
            
        except Exception as e:
            logger.error(f"Error in balanced distribution: {e}")
            return {}
    
    async def _priority_based_distribution(
        self, 
        tasks: List[WorkloadTask], 
        task_solver_mapping: Dict[str, List[Tuple[str, SolverCapability]]]
    ) -> Dict[str, List[WorkloadTask]]:
        """Priority-based workload distribution algorithm"""
        try:
            distribution = defaultdict(list)
            
            # Group tasks by priority
            priority_groups = defaultdict(list)
            for task in tasks:
                priority_groups[task.priority].append(task)
            
            # Process high priority tasks first
            priority_order = [WorkloadPriority.CRITICAL, WorkloadPriority.HIGH, 
                            WorkloadPriority.MEDIUM, WorkloadPriority.LOW]
            
            for priority in priority_order:
                priority_tasks = priority_groups.get(priority, [])
                
                # Sort by deadline within priority group
                priority_tasks.sort(key=lambda t: t.deadline)
                
                for task in priority_tasks:
                    eligible_solvers = task_solver_mapping.get(task.task_id, [])
                    if not eligible_solvers:
                        continue
                    
                    # For high priority tasks, prefer high-tier solvers
                    if priority in [WorkloadPriority.CRITICAL, WorkloadPriority.HIGH]:
                        # Sort by solver tier and capability
                        eligible_solvers.sort(
                            key=lambda x: (
                                self._get_solver_tier_score(x[0]),
                                x[1].proficiency_score * x[1].success_rate
                            ),
                            reverse=True
                        )
                    
                    # Assign to best available solver
                    for solver_address, capability in eligible_solvers:
                        capacity_info = await self.assess_solver_capacity(solver_address)
                        if capacity_info.get("available", False):
                            distribution[solver_address].append(task)
                            break
            
            return dict(distribution)
            
        except Exception as e:
            logger.error(f"Error in priority-based distribution: {e}")
            return {}
    
    async def _capacity_optimized_distribution(
        self, 
        tasks: List[WorkloadTask], 
        task_solver_mapping: Dict[str, List[Tuple[str, SolverCapability]]]
    ) -> Dict[str, List[WorkloadTask]]:
        """Capacity-optimized workload distribution algorithm"""
        try:
            distribution = defaultdict(list)
            
            # Get capacity information for all solvers
            solver_capacities = {}
            for task in tasks:
                for solver_address, _ in task_solver_mapping.get(task.task_id, []):
                    if solver_address not in solver_capacities:
                        solver_capacities[solver_address] = await self.assess_solver_capacity(solver_address)
            
            # Sort tasks by execution time (longest first for better bin packing)
            sorted_tasks = sorted(tasks, key=lambda t: t.estimated_execution_time, reverse=True)
            
            for task in sorted_tasks:
                eligible_solvers = task_solver_mapping.get(task.task_id, [])
                if not eligible_solvers:
                    continue
                
                # Find solver with best capacity utilization
                best_solver = None
                best_score = -1
                
                for solver_address, capability in eligible_solvers:
                    capacity_info = solver_capacities.get(solver_address, {})
                    if not capacity_info.get("available", False):
                        continue
                    
                    # Calculate utilization score
                    available_capacity = capacity_info.get("available_capacity", 0)
                    current_tasks = len(distribution[solver_address])
                    
                    # Prefer solvers with good capacity but not overloaded
                    utilization_score = (
                        available_capacity * 0.4 +
                        capability.proficiency_score * 0.3 +
                        capability.success_rate * 0.2 +
                        (1.0 / (current_tasks + 1)) * 0.1  # Prefer less loaded solvers
                    )
                    
                    if utilization_score > best_score:
                        best_score = utilization_score
                        best_solver = solver_address
                
                if best_solver:
                    distribution[best_solver].append(task)
            
            return dict(distribution)
            
        except Exception as e:
            logger.error(f"Error in capacity-optimized distribution: {e}")
            return {}
    
    def _get_solver_tier_score(self, solver_address: str) -> float:
        """Get numerical score for solver tier"""
        try:
            # This would get the actual solver tier from the network service
            # For now, return a default score
            return 1.0
            
        except Exception as e:
            logger.error(f"Error getting solver tier score: {e}")
            return 0.0
    
    async def _calculate_distribution_efficiency(self, distribution: Dict[str, List[WorkloadTask]]) -> float:
        """Calculate efficiency score for workload distribution"""
        try:
            if not distribution:
                return 0.0
            
            # Calculate load balance (lower variance is better)
            task_counts = [len(tasks) for tasks in distribution.values()]
            if len(task_counts) <= 1:
                return 1.0
            
            mean_tasks = np.mean(task_counts)
            variance = np.var(task_counts)
            balance_score = 1.0 / (1.0 + variance / (mean_tasks + 1))
            
            # Calculate capability matching score
            capability_scores = []
            for solver_address, tasks in distribution.items():
                solver_capabilities = self.solver_capabilities.get(solver_address, [])
                for task in tasks:
                    # Find matching capability
                    matching_cap = next(
                        (cap for cap in solver_capabilities if cap.capability_type == task.capability_required),
                        None
                    )
                    if matching_cap:
                        capability_scores.append(matching_cap.proficiency_score)
            
            capability_score = np.mean(capability_scores) if capability_scores else 0.0
            
            # Overall efficiency score
            efficiency = balance_score * 0.6 + capability_score * 0.4
            return min(1.0, max(0.0, efficiency))
            
        except Exception as e:
            logger.error(f"Error calculating distribution efficiency: {e}")
            return 0.0
    
    async def rebalance_workload(self, trigger_threshold: float = 0.3) -> bool:
        """
        Dynamically rebalance workload when conditions change
        Requirements: 3.2 - Dynamic rebalancing for changing conditions
        """
        try:
            # Check if rebalancing is needed
            current_distribution = defaultdict(list)
            for task in self.active_tasks.values():
                if task.assigned_solver:
                    current_distribution[task.assigned_solver].append(task)
            
            if not current_distribution:
                return True
            
            # Calculate current efficiency
            current_efficiency = await self._calculate_distribution_efficiency(current_distribution)
            
            # Check if rebalancing threshold is met
            if current_efficiency > (1.0 - trigger_threshold):
                logger.debug(f"Rebalancing not needed, current efficiency: {current_efficiency}")
                return True
            
            logger.info(f"Triggering workload rebalancing, current efficiency: {current_efficiency}")
            
            # Get all active tasks
            active_tasks = list(self.active_tasks.values())
            
            # Clear current assignments
            for task in active_tasks:
                task.assigned_solver = None
                task.status = "pending"
            
            # Redistribute with balanced strategy
            new_distribution = await self.distribute_workload(active_tasks, "balanced")
            
            if new_distribution:
                new_efficiency = await self._calculate_distribution_efficiency(new_distribution)
                logger.info(f"Workload rebalanced, new efficiency: {new_efficiency}")
                return True
            else:
                logger.error("Failed to rebalance workload")
                return False
            
        except Exception as e:
            logger.error(f"Error rebalancing workload: {e}")
            return False
    
    # Multi-Solver Orchestration System
    
    async def orchestrate_multi_solver_execution(
        self, 
        intent_hash: str,
        required_capabilities: List[CapabilityType],
        execution_strategy: str = "parallel"
    ) -> Optional[str]:
        """
        Orchestrate multi-solver execution for complex intents
        Requirements: 3.3 - Complementary capability matching and coordination
        """
        try:
            # Find complementary solver combinations
            solver_combinations = await self._find_complementary_solvers(required_capabilities)
            
            if not solver_combinations:
                logger.error(f"No complementary solver combinations found for intent {intent_hash}")
                return None
            
            # Select best combination
            best_combination = await self._select_best_solver_combination(
                solver_combinations, 
                required_capabilities
            )
            
            if not best_combination:
                logger.error(f"Failed to select solver combination for intent {intent_hash}")
                return None
            
            # Create orchestration session
            session_id = f"orchestration_{intent_hash}_{datetime.now().timestamp()}"
            
            orchestration_session = {
                "session_id": session_id,
                "intent_hash": intent_hash,
                "required_capabilities": [cap.value for cap in required_capabilities],
                "selected_solvers": best_combination,
                "execution_strategy": execution_strategy,
                "status": "initializing",
                "created_at": datetime.now(),
                "execution_plan": await self._create_execution_plan(
                    best_combination, 
                    required_capabilities, 
                    execution_strategy
                ),
                "results": {},
                "errors": []
            }
            
            self.orchestration_sessions[session_id] = orchestration_session
            
            # Start orchestrated execution
            success = await self._execute_orchestrated_plan(session_id)
            
            if success:
                logger.info(f"Multi-solver orchestration started for intent {intent_hash}, session: {session_id}")
                return session_id
            else:
                logger.error(f"Failed to start orchestrated execution for intent {intent_hash}")
                return None
            
        except Exception as e:
            logger.error(f"Error orchestrating multi-solver execution: {e}")
            return None
    
    async def _find_complementary_solvers(
        self, 
        required_capabilities: List[CapabilityType]
    ) -> List[List[str]]:
        """Find solver combinations that cover all required capabilities"""
        try:
            combinations = []
            
            # Get solvers for each capability
            capability_solvers = {}
            for capability in required_capabilities:
                solvers = await self.get_solvers_by_capability(capability)
                capability_solvers[capability] = [solver_addr for solver_addr, _ in solvers]
            
            # Generate combinations using recursive approach
            def generate_combinations(caps_remaining, current_combination, used_solvers):
                if not caps_remaining:
                    combinations.append(current_combination.copy())
                    return
                
                capability = caps_remaining[0]
                available_solvers = capability_solvers.get(capability, [])
                
                for solver in available_solvers:
                    if solver not in used_solvers:
                        current_combination.append(solver)
                        used_solvers.add(solver)
                        generate_combinations(caps_remaining[1:], current_combination, used_solvers)
                        current_combination.pop()
                        used_solvers.remove(solver)
            
            generate_combinations(required_capabilities, [], set())
            
            # Limit to reasonable number of combinations
            return combinations[:10]
            
        except Exception as e:
            logger.error(f"Error finding complementary solvers: {e}")
            return []
    
    async def _select_best_solver_combination(
        self, 
        combinations: List[List[str]], 
        required_capabilities: List[CapabilityType]
    ) -> Optional[List[str]]:
        """Select the best solver combination based on multiple criteria"""
        try:
            if not combinations:
                return None
            
            scored_combinations = []
            
            for combination in combinations:
                score = await self._score_solver_combination(combination, required_capabilities)
                scored_combinations.append((score, combination))
            
            # Sort by score (descending)
            scored_combinations.sort(key=lambda x: x[0], reverse=True)
            
            return scored_combinations[0][1] if scored_combinations else None
            
        except Exception as e:
            logger.error(f"Error selecting best solver combination: {e}")
            return None
    
    async def _score_solver_combination(
        self, 
        combination: List[str], 
        required_capabilities: List[CapabilityType]
    ) -> float:
        """Score a solver combination based on various factors"""
        try:
            total_score = 0.0
            
            # Check each solver's capability for the required capabilities
            for i, solver_address in enumerate(combination):
                if i < len(required_capabilities):
                    capability_type = required_capabilities[i]
                    
                    # Get solver's capability score
                    capabilities = self.solver_capabilities.get(solver_address, [])
                    matching_cap = next(
                        (cap for cap in capabilities if cap.capability_type == capability_type),
                        None
                    )
                    
                    if matching_cap:
                        # Capability score
                        cap_score = matching_cap.proficiency_score * matching_cap.success_rate
                        
                        # Health score
                        health_status = self.solver_health_status.get(solver_address)
                        health_score = health_status.health_score if health_status else 0.0
                        
                        # Capacity score
                        capacity_info = await self.assess_solver_capacity(solver_address)
                        capacity_score = capacity_info.get("available_capacity", 0.0)
                        
                        # Combined score for this solver
                        solver_score = (
                            cap_score * 0.5 +
                            health_score * 0.3 +
                            capacity_score * 0.2
                        )
                        
                        total_score += solver_score
            
            # Average score across all solvers
            return total_score / len(combination) if combination else 0.0
            
        except Exception as e:
            logger.error(f"Error scoring solver combination: {e}")
            return 0.0
    
    async def _create_execution_plan(
        self, 
        solver_combination: List[str], 
        required_capabilities: List[CapabilityType],
        execution_strategy: str
    ) -> Dict:
        """Create detailed execution plan for multi-solver orchestration"""
        try:
            plan = {
                "strategy": execution_strategy,
                "steps": [],
                "dependencies": {},
                "timeouts": {},
                "fallback_options": {}
            }
            
            if execution_strategy == "parallel":
                # All solvers execute simultaneously
                for i, (solver_address, capability) in enumerate(zip(solver_combination, required_capabilities)):
                    step = {
                        "step_id": f"step_{i}",
                        "solver_address": solver_address,
                        "capability": capability.value,
                        "execution_order": 0,  # All parallel
                        "timeout": 300,  # 5 minutes default
                        "retry_count": 2
                    }
                    plan["steps"].append(step)
            
            elif execution_strategy == "sequential":
                # Solvers execute in sequence
                for i, (solver_address, capability) in enumerate(zip(solver_combination, required_capabilities)):
                    step = {
                        "step_id": f"step_{i}",
                        "solver_address": solver_address,
                        "capability": capability.value,
                        "execution_order": i,
                        "timeout": 300,
                        "retry_count": 2
                    }
                    plan["steps"].append(step)
                    
                    # Add dependency on previous step
                    if i > 0:
                        plan["dependencies"][f"step_{i}"] = [f"step_{i-1}"]
            
            elif execution_strategy == "pipeline":
                # Pipeline execution with data flow
                for i, (solver_address, capability) in enumerate(zip(solver_combination, required_capabilities)):
                    step = {
                        "step_id": f"step_{i}",
                        "solver_address": solver_address,
                        "capability": capability.value,
                        "execution_order": i,
                        "timeout": 300,
                        "retry_count": 2,
                        "data_input": f"step_{i-1}_output" if i > 0 else "initial_input",
                        "data_output": f"step_{i}_output"
                    }
                    plan["steps"].append(step)
                    
                    if i > 0:
                        plan["dependencies"][f"step_{i}"] = [f"step_{i-1}"]
            
            return plan
            
        except Exception as e:
            logger.error(f"Error creating execution plan: {e}")
            return {}
    
    async def _execute_orchestrated_plan(self, session_id: str) -> bool:
        """Execute the orchestrated multi-solver plan"""
        try:
            session = self.orchestration_sessions.get(session_id)
            if not session:
                return False
            
            session["status"] = "executing"
            execution_plan = session["execution_plan"]
            
            # Execute based on strategy
            if execution_plan["strategy"] == "parallel":
                return await self._execute_parallel_plan(session_id)
            elif execution_plan["strategy"] == "sequential":
                return await self._execute_sequential_plan(session_id)
            elif execution_plan["strategy"] == "pipeline":
                return await self._execute_pipeline_plan(session_id)
            else:
                logger.error(f"Unknown execution strategy: {execution_plan['strategy']}")
                return False
            
        except Exception as e:
            logger.error(f"Error executing orchestrated plan: {e}")
            return False
    
    async def _execute_parallel_plan(self, session_id: str) -> bool:
        """Execute parallel orchestration plan"""
        try:
            session = self.orchestration_sessions[session_id]
            execution_plan = session["execution_plan"]
            
            # Start all steps in parallel
            tasks = []
            for step in execution_plan["steps"]:
                task = asyncio.create_task(
                    self._execute_orchestration_step(session_id, step)
                )
                tasks.append(task)
            
            # Wait for all tasks to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check results
            success_count = sum(1 for result in results if result is True)
            total_steps = len(execution_plan["steps"])
            
            if success_count == total_steps:
                session["status"] = "completed"
                logger.info(f"Parallel orchestration completed successfully for session {session_id}")
                return True
            else:
                session["status"] = "failed"
                logger.error(f"Parallel orchestration failed for session {session_id}: {success_count}/{total_steps} steps succeeded")
                return False
            
        except Exception as e:
            logger.error(f"Error executing parallel plan: {e}")
            return False
    
    async def _execute_sequential_plan(self, session_id: str) -> bool:
        """Execute sequential orchestration plan"""
        try:
            session = self.orchestration_sessions[session_id]
            execution_plan = session["execution_plan"]
            
            # Sort steps by execution order
            sorted_steps = sorted(execution_plan["steps"], key=lambda s: s["execution_order"])
            
            # Execute steps in sequence
            for step in sorted_steps:
                success = await self._execute_orchestration_step(session_id, step)
                if not success:
                    session["status"] = "failed"
                    logger.error(f"Sequential orchestration failed at step {step['step_id']} for session {session_id}")
                    return False
            
            session["status"] = "completed"
            logger.info(f"Sequential orchestration completed successfully for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error executing sequential plan: {e}")
            return False
    
    async def _execute_pipeline_plan(self, session_id: str) -> bool:
        """Execute pipeline orchestration plan"""
        try:
            session = self.orchestration_sessions[session_id]
            execution_plan = session["execution_plan"]
            
            # Sort steps by execution order
            sorted_steps = sorted(execution_plan["steps"], key=lambda s: s["execution_order"])
            
            # Execute pipeline with data flow
            pipeline_data = {"initial_input": session.get("input_data", {})}
            
            for step in sorted_steps:
                # Get input data for this step
                input_key = step.get("data_input", "initial_input")
                step_input = pipeline_data.get(input_key, {})
                
                # Execute step with input data
                success, output_data = await self._execute_orchestration_step_with_data(
                    session_id, step, step_input
                )
                
                if not success:
                    session["status"] = "failed"
                    logger.error(f"Pipeline orchestration failed at step {step['step_id']} for session {session_id}")
                    return False
                
                # Store output data for next step
                output_key = step.get("data_output", f"{step['step_id']}_output")
                pipeline_data[output_key] = output_data
            
            # Store final results
            session["results"] = pipeline_data
            session["status"] = "completed"
            logger.info(f"Pipeline orchestration completed successfully for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error executing pipeline plan: {e}")
            return False
    
    async def _execute_orchestration_step(self, session_id: str, step: Dict) -> bool:
        """Execute a single orchestration step"""
        try:
            # In production, would make actual call to solver
            # For now, simulate execution based on solver health
            solver_address = step["solver_address"]
            
            # Check if solver is still healthy
            if not await self._is_solver_healthy_and_active(solver_address):
                logger.error(f"Solver {solver_address} not healthy for step {step['step_id']}")
                return False
            
            # Simulate execution time
            await asyncio.sleep(0.1)  # Simulate processing
            
            # Simulate success based on solver capability
            capabilities = self.solver_capabilities.get(solver_address, [])
            if capabilities:
                # Use average success rate of solver's capabilities
                avg_success_rate = np.mean([cap.success_rate for cap in capabilities])
                success = np.random.random() < avg_success_rate
            else:
                success = True  # Default success for testing
            
            logger.debug(f"Orchestration step {step['step_id']} for solver {solver_address}: {'success' if success else 'failed'}")
            return success
            
        except Exception as e:
            logger.error(f"Error executing orchestration step: {e}")
            return False
    
    async def _execute_orchestration_step_with_data(
        self, 
        session_id: str, 
        step: Dict, 
        input_data: Dict
    ) -> Tuple[bool, Dict]:
        """Execute orchestration step with data flow"""
        try:
            # Execute the step
            success = await self._execute_orchestration_step(session_id, step)
            
            # Generate output data (in production, would come from solver)
            output_data = {
                "step_id": step["step_id"],
                "solver_address": step["solver_address"],
                "capability": step["capability"],
                "input_processed": len(str(input_data)),
                "execution_time": 0.1,
                "success": success,
                "timestamp": datetime.now().isoformat()
            }
            
            return success, output_data
            
        except Exception as e:
            logger.error(f"Error executing orchestration step with data: {e}")
            return False, {}
    
    async def get_orchestration_status(self, session_id: str) -> Optional[Dict]:
        """Get status of orchestration session"""
        try:
            session = self.orchestration_sessions.get(session_id)
            if not session:
                return None
            
            return {
                "session_id": session_id,
                "intent_hash": session["intent_hash"],
                "status": session["status"],
                "created_at": session["created_at"].isoformat(),
                "selected_solvers": session["selected_solvers"],
                "execution_strategy": session["execution_strategy"],
                "required_capabilities": session["required_capabilities"],
                "results": session.get("results", {}),
                "errors": session.get("errors", [])
            }
            
        except Exception as e:
            logger.error(f"Error getting orchestration status: {e}")
            return None
    
    async def aggregate_orchestration_results(
        self, 
        session_id: str
    ) -> Optional[Dict]:
        """
        Aggregate and validate results from multi-solver orchestration
        Requirements: 3.3 - Result aggregation and validation
        """
        try:
            session = self.orchestration_sessions.get(session_id)
            if not session:
                logger.error(f"Orchestration session {session_id} not found")
                return None
            
            if session["status"] != "completed":
                logger.warning(f"Session {session_id} not completed, status: {session['status']}")
                return None
            
            execution_plan = session["execution_plan"]
            results = session.get("results", {})
            
            # Aggregate results based on execution strategy
            if execution_plan["strategy"] == "parallel":
                aggregated_results = await self._aggregate_parallel_results(session_id, results)
            elif execution_plan["strategy"] == "sequential":
                aggregated_results = await self._aggregate_sequential_results(session_id, results)
            elif execution_plan["strategy"] == "pipeline":
                aggregated_results = await self._aggregate_pipeline_results(session_id, results)
            else:
                logger.error(f"Unknown execution strategy: {execution_plan['strategy']}")
                return None
            
            # Validate aggregated results
            validation_result = await self._validate_orchestration_results(
                session_id, aggregated_results
            )
            
            # Create final result package
            final_results = {
                "session_id": session_id,
                "intent_hash": session["intent_hash"],
                "execution_strategy": execution_plan["strategy"],
                "aggregated_results": aggregated_results,
                "validation": validation_result,
                "solver_contributions": await self._analyze_solver_contributions(session_id),
                "performance_metrics": await self._calculate_orchestration_metrics(session_id),
                "aggregation_timestamp": datetime.now().isoformat()
            }
            
            # Store aggregated results in session
            session["final_results"] = final_results
            
            logger.info(f"Successfully aggregated results for orchestration session {session_id}")
            return final_results
            
        except Exception as e:
            logger.error(f"Error aggregating orchestration results: {e}")
            return None
    
    async def _aggregate_parallel_results(self, session_id: str, results: Dict) -> Dict:
        """Aggregate results from parallel execution"""
        try:
            session = self.orchestration_sessions[session_id]
            execution_plan = session["execution_plan"]
            
            aggregated = {
                "execution_mode": "parallel",
                "total_steps": len(execution_plan["steps"]),
                "successful_steps": 0,
                "failed_steps": 0,
                "step_results": {},
                "combined_output": {},
                "execution_summary": {}
            }
            
            # Process each step result
            for step in execution_plan["steps"]:
                step_id = step["step_id"]
                step_result = results.get(step_id, {})
                
                aggregated["step_results"][step_id] = {
                    "solver_address": step["solver_address"],
                    "capability": step["capability"],
                    "success": step_result.get("success", False),
                    "execution_time": step_result.get("execution_time", 0),
                    "output_data": step_result.get("output_data", {}),
                    "error_details": step_result.get("error_details")
                }
                
                if step_result.get("success", False):
                    aggregated["successful_steps"] += 1
                    # Merge successful outputs
                    output_data = step_result.get("output_data", {})
                    aggregated["combined_output"].update(output_data)
                else:
                    aggregated["failed_steps"] += 1
            
            # Calculate success rate
            aggregated["success_rate"] = (
                aggregated["successful_steps"] / aggregated["total_steps"]
                if aggregated["total_steps"] > 0 else 0.0
            )
            
            # Create execution summary
            aggregated["execution_summary"] = {
                "overall_success": aggregated["success_rate"] >= 0.8,  # 80% threshold
                "total_execution_time": max(
                    result.get("execution_time", 0) 
                    for result in aggregated["step_results"].values()
                ),
                "capabilities_executed": [
                    step["capability"] for step in execution_plan["steps"]
                ],
                "solvers_used": [
                    step["solver_address"] for step in execution_plan["steps"]
                ]
            }
            
            return aggregated
            
        except Exception as e:
            logger.error(f"Error aggregating parallel results: {e}")
            return {}
    
    async def _aggregate_sequential_results(self, session_id: str, results: Dict) -> Dict:
        """Aggregate results from sequential execution"""
        try:
            session = self.orchestration_sessions[session_id]
            execution_plan = session["execution_plan"]
            
            # Sort steps by execution order
            sorted_steps = sorted(execution_plan["steps"], key=lambda s: s["execution_order"])
            
            aggregated = {
                "execution_mode": "sequential",
                "total_steps": len(sorted_steps),
                "completed_steps": 0,
                "step_results": {},
                "execution_chain": [],
                "final_output": {},
                "execution_summary": {}
            }
            
            # Process steps in order
            for i, step in enumerate(sorted_steps):
                step_id = step["step_id"]
                step_result = results.get(step_id, {})
                
                step_info = {
                    "step_order": i,
                    "solver_address": step["solver_address"],
                    "capability": step["capability"],
                    "success": step_result.get("success", False),
                    "execution_time": step_result.get("execution_time", 0),
                    "output_data": step_result.get("output_data", {}),
                    "error_details": step_result.get("error_details")
                }
                
                aggregated["step_results"][step_id] = step_info
                aggregated["execution_chain"].append(step_info)
                
                if step_result.get("success", False):
                    aggregated["completed_steps"] += 1
                    # For sequential, final output is from last successful step
                    aggregated["final_output"] = step_result.get("output_data", {})
                else:
                    # Sequential execution stops on first failure
                    break
            
            # Calculate completion rate
            aggregated["completion_rate"] = (
                aggregated["completed_steps"] / aggregated["total_steps"]
                if aggregated["total_steps"] > 0 else 0.0
            )
            
            # Create execution summary
            aggregated["execution_summary"] = {
                "overall_success": aggregated["completion_rate"] == 1.0,
                "total_execution_time": sum(
                    result.get("execution_time", 0) 
                    for result in aggregated["step_results"].values()
                ),
                "execution_stopped_at_step": aggregated["completed_steps"],
                "capabilities_completed": [
                    step["capability"] for step in aggregated["execution_chain"]
                    if step["success"]
                ],
                "solvers_used": [
                    step["solver_address"] for step in aggregated["execution_chain"]
                ]
            }
            
            return aggregated
            
        except Exception as e:
            logger.error(f"Error aggregating sequential results: {e}")
            return {}
    
    async def _aggregate_pipeline_results(self, session_id: str, results: Dict) -> Dict:
        """Aggregate results from pipeline execution"""
        try:
            session = self.orchestration_sessions[session_id]
            execution_plan = session["execution_plan"]
            
            # Sort steps by execution order
            sorted_steps = sorted(execution_plan["steps"], key=lambda s: s["execution_order"])
            
            aggregated = {
                "execution_mode": "pipeline",
                "total_steps": len(sorted_steps),
                "completed_steps": 0,
                "step_results": {},
                "data_flow": {},
                "final_output": {},
                "execution_summary": {}
            }
            
            # Track data flow through pipeline
            current_data = session.get("input_data", {})
            
            for i, step in enumerate(sorted_steps):
                step_id = step["step_id"]
                step_result = results.get(step_id, {})
                
                step_info = {
                    "step_order": i,
                    "solver_address": step["solver_address"],
                    "capability": step["capability"],
                    "success": step_result.get("success", False),
                    "execution_time": step_result.get("execution_time", 0),
                    "input_data": current_data.copy(),
                    "output_data": step_result.get("output_data", {}),
                    "data_transformation": self._analyze_data_transformation(
                        current_data, step_result.get("output_data", {})
                    ),
                    "error_details": step_result.get("error_details")
                }
                
                aggregated["step_results"][step_id] = step_info
                
                if step_result.get("success", False):
                    aggregated["completed_steps"] += 1
                    # Update current data for next step
                    current_data = step_result.get("output_data", {})
                    aggregated["data_flow"][step_id] = current_data.copy()
                else:
                    # Pipeline execution stops on failure
                    break
            
            # Final output is the last successful step's output
            aggregated["final_output"] = current_data
            
            # Calculate completion rate
            aggregated["completion_rate"] = (
                aggregated["completed_steps"] / aggregated["total_steps"]
                if aggregated["total_steps"] > 0 else 0.0
            )
            
            # Create execution summary
            aggregated["execution_summary"] = {
                "overall_success": aggregated["completion_rate"] == 1.0,
                "total_execution_time": sum(
                    result.get("execution_time", 0) 
                    for result in aggregated["step_results"].values()
                ),
                "data_transformations": len(aggregated["data_flow"]),
                "pipeline_efficiency": self._calculate_pipeline_efficiency(aggregated),
                "capabilities_completed": [
                    step["capability"] for step in sorted_steps[:aggregated["completed_steps"]]
                ],
                "solvers_used": [
                    step["solver_address"] for step in sorted_steps[:aggregated["completed_steps"]]
                ]
            }
            
            return aggregated
            
        except Exception as e:
            logger.error(f"Error aggregating pipeline results: {e}")
            return {}
    
    def _analyze_data_transformation(self, input_data: Dict, output_data: Dict) -> Dict:
        """Analyze data transformation between pipeline steps"""
        try:
            return {
                "input_size": len(str(input_data)),
                "output_size": len(str(output_data)),
                "size_change": len(str(output_data)) - len(str(input_data)),
                "keys_added": list(set(output_data.keys()) - set(input_data.keys())),
                "keys_removed": list(set(input_data.keys()) - set(output_data.keys())),
                "keys_modified": [
                    key for key in input_data.keys() 
                    if key in output_data and input_data[key] != output_data[key]
                ]
            }
        except Exception as e:
            logger.error(f"Error analyzing data transformation: {e}")
            return {}
    
    def _calculate_pipeline_efficiency(self, aggregated_results: Dict) -> float:
        """Calculate pipeline execution efficiency"""
        try:
            if not aggregated_results.get("step_results"):
                return 0.0
            
            # Efficiency based on completion rate and data flow
            completion_rate = aggregated_results.get("completion_rate", 0.0)
            
            # Bonus for successful data transformations
            data_flow_bonus = len(aggregated_results.get("data_flow", {})) * 0.1
            
            # Penalty for execution time variance (prefer consistent timing)
            execution_times = [
                result.get("execution_time", 0) 
                for result in aggregated_results["step_results"].values()
            ]
            
            if len(execution_times) > 1:
                time_variance = np.var(execution_times)
                time_penalty = min(0.2, time_variance / 100.0)  # Max 20% penalty
            else:
                time_penalty = 0.0
            
            efficiency = completion_rate + data_flow_bonus - time_penalty
            return max(0.0, min(1.0, efficiency))
            
        except Exception as e:
            logger.error(f"Error calculating pipeline efficiency: {e}")
            return 0.0
    
    async def _validate_orchestration_results(
        self, 
        session_id: str, 
        aggregated_results: Dict
    ) -> Dict:
        """
        Validate orchestration results for consistency and completeness
        Requirements: 3.3 - Result aggregation and validation
        """
        try:
            session = self.orchestration_sessions[session_id]
            validation_result = {
                "is_valid": True,
                "validation_score": 1.0,
                "issues": [],
                "warnings": [],
                "recommendations": []
            }
            
            # Validate execution completeness
            required_capabilities = session["required_capabilities"]
            execution_mode = aggregated_results.get("execution_mode", "unknown")
            
            if execution_mode == "parallel":
                success_rate = aggregated_results.get("success_rate", 0.0)
                if success_rate < 0.8:
                    validation_result["issues"].append(
                        f"Low parallel execution success rate: {success_rate:.2f}"
                    )
                    validation_result["is_valid"] = False
                    validation_result["validation_score"] *= 0.5
            
            elif execution_mode == "sequential":
                completion_rate = aggregated_results.get("completion_rate", 0.0)
                if completion_rate < 1.0:
                    validation_result["issues"].append(
                        f"Incomplete sequential execution: {completion_rate:.2f}"
                    )
                    validation_result["is_valid"] = False
                    validation_result["validation_score"] *= 0.3
            
            elif execution_mode == "pipeline":
                completion_rate = aggregated_results.get("completion_rate", 0.0)
                if completion_rate < 1.0:
                    validation_result["issues"].append(
                        f"Incomplete pipeline execution: {completion_rate:.2f}"
                    )
                    validation_result["is_valid"] = False
                    validation_result["validation_score"] *= 0.3
                
                # Validate data flow continuity
                data_flow = aggregated_results.get("data_flow", {})
                if len(data_flow) < len(required_capabilities) - 1:
                    validation_result["warnings"].append(
                        "Incomplete data flow in pipeline execution"
                    )
                    validation_result["validation_score"] *= 0.8
            
            # Validate solver performance
            step_results = aggregated_results.get("step_results", {})
            for step_id, step_result in step_results.items():
                execution_time = step_result.get("execution_time", 0)
                if execution_time > 300:  # 5 minutes
                    validation_result["warnings"].append(
                        f"Step {step_id} took {execution_time:.1f}s (longer than expected)"
                    )
                    validation_result["validation_score"] *= 0.9
                
                if not step_result.get("success", False):
                    error_details = step_result.get("error_details", "Unknown error")
                    validation_result["issues"].append(
                        f"Step {step_id} failed: {error_details}"
                    )
            
            # Validate result consistency
            consistency_score = await self._validate_result_consistency(aggregated_results)
            validation_result["consistency_score"] = consistency_score
            validation_result["validation_score"] *= consistency_score
            
            if consistency_score < 0.8:
                validation_result["warnings"].append(
                    f"Low result consistency score: {consistency_score:.2f}"
                )
            
            # Generate recommendations
            if not validation_result["is_valid"]:
                validation_result["recommendations"].extend([
                    "Consider retry with different solver combination",
                    "Review solver health and capacity before retry",
                    "Analyze failure patterns for systematic issues"
                ])
            
            if validation_result["validation_score"] < 0.9:
                validation_result["recommendations"].append(
                    "Monitor solver performance for optimization opportunities"
                )
            
            logger.info(f"Validation completed for session {session_id}: valid={validation_result['is_valid']}, score={validation_result['validation_score']:.3f}")
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating orchestration results: {e}")
            return {
                "is_valid": False,
                "validation_score": 0.0,
                "issues": [f"Validation error: {str(e)}"],
                "warnings": [],
                "recommendations": ["Manual review required due to validation error"]
            }
    
    async def _validate_result_consistency(self, aggregated_results: Dict) -> float:
        """Validate consistency of results across solvers"""
        try:
            step_results = aggregated_results.get("step_results", {})
            if len(step_results) <= 1:
                return 1.0  # Single result is always consistent
            
            consistency_score = 1.0
            
            # Check execution time consistency
            execution_times = [
                result.get("execution_time", 0) 
                for result in step_results.values()
                if result.get("success", False)
            ]
            
            if len(execution_times) > 1:
                time_variance = np.var(execution_times)
                mean_time = np.mean(execution_times)
                if mean_time > 0:
                    time_consistency = 1.0 - min(0.5, time_variance / (mean_time ** 2))
                    consistency_score *= time_consistency
            
            # Check output data consistency (for parallel execution)
            if aggregated_results.get("execution_mode") == "parallel":
                output_sizes = [
                    len(str(result.get("output_data", {})))
                    for result in step_results.values()
                    if result.get("success", False)
                ]
                
                if len(output_sizes) > 1:
                    size_variance = np.var(output_sizes)
                    mean_size = np.mean(output_sizes)
                    if mean_size > 0:
                        size_consistency = 1.0 - min(0.3, size_variance / (mean_size ** 2))
                        consistency_score *= size_consistency
            
            return max(0.0, min(1.0, consistency_score))
            
        except Exception as e:
            logger.error(f"Error validating result consistency: {e}")
            return 0.0
    
    async def _analyze_solver_contributions(self, session_id: str) -> Dict:
        """Analyze individual solver contributions to orchestration"""
        try:
            session = self.orchestration_sessions[session_id]
            execution_plan = session["execution_plan"]
            results = session.get("results", {})
            
            contributions = {}
            
            for step in execution_plan["steps"]:
                solver_address = step["solver_address"]
                step_result = results.get(step["step_id"], {})
                
                contribution = {
                    "solver_address": solver_address,
                    "capability_provided": step["capability"],
                    "execution_success": step_result.get("success", False),
                    "execution_time": step_result.get("execution_time", 0),
                    "output_quality": self._assess_output_quality(step_result.get("output_data", {})),
                    "reliability_score": await self._calculate_solver_reliability_score(solver_address),
                    "contribution_score": 0.0
                }
                
                # Calculate contribution score
                if contribution["execution_success"]:
                    base_score = 1.0
                    time_bonus = max(0.0, 1.0 - contribution["execution_time"] / 300.0)  # Bonus for fast execution
                    quality_bonus = contribution["output_quality"]
                    reliability_bonus = contribution["reliability_score"] * 0.5
                    
                    contribution["contribution_score"] = (
                        base_score * 0.4 +
                        time_bonus * 0.2 +
                        quality_bonus * 0.2 +
                        reliability_bonus * 0.2
                    )
                
                contributions[solver_address] = contribution
            
            return contributions
            
        except Exception as e:
            logger.error(f"Error analyzing solver contributions: {e}")
            return {}
    
    def _assess_output_quality(self, output_data: Dict) -> float:
        """Assess quality of solver output data"""
        try:
            if not output_data:
                return 0.0
            
            # Basic quality metrics
            completeness = 1.0 if output_data else 0.0
            
            # Check for required fields
            required_fields = ["step_id", "solver_address", "success", "timestamp"]
            field_score = sum(1 for field in required_fields if field in output_data) / len(required_fields)
            
            # Check data richness
            data_richness = min(1.0, len(str(output_data)) / 100.0)  # Normalize by expected size
            
            quality_score = (
                completeness * 0.4 +
                field_score * 0.4 +
                data_richness * 0.2
            )
            
            return max(0.0, min(1.0, quality_score))
            
        except Exception as e:
            logger.error(f"Error assessing output quality: {e}")
            return 0.0
    
    async def _calculate_solver_reliability_score(self, solver_address: str) -> float:
        """Calculate solver reliability score"""
        try:
            # Get health status
            health_status = self.solver_health_status.get(solver_address)
            health_score = health_status.health_score if health_status else 0.0
            
            # Get solver from network service
            solver = await self.solver_network_service.get_solver_by_address(solver_address)
            reputation_score = solver.reputation_score.total_score if solver else 0.0
            
            # Combine scores
            reliability_score = health_score * 0.6 + reputation_score * 0.4
            return max(0.0, min(1.0, reliability_score))
            
        except Exception as e:
            logger.error(f"Error calculating solver reliability score: {e}")
            return 0.0
    
    async def _calculate_orchestration_metrics(self, session_id: str) -> Dict:
        """Calculate performance metrics for orchestration session"""
        try:
            session = self.orchestration_sessions[session_id]
            execution_plan = session["execution_plan"]
            results = session.get("results", {})
            
            metrics = {
                "total_execution_time": 0.0,
                "average_step_time": 0.0,
                "success_rate": 0.0,
                "solver_utilization": 0.0,
                "coordination_overhead": 0.0,
                "efficiency_score": 0.0
            }
            
            # Calculate timing metrics
            execution_times = []
            successful_steps = 0
            
            for step in execution_plan["steps"]:
                step_result = results.get(step["step_id"], {})
                execution_time = step_result.get("execution_time", 0)
                execution_times.append(execution_time)
                
                if step_result.get("success", False):
                    successful_steps += 1
            
            if execution_times:
                if execution_plan["strategy"] == "parallel":
                    metrics["total_execution_time"] = max(execution_times)
                else:
                    metrics["total_execution_time"] = sum(execution_times)
                
                metrics["average_step_time"] = np.mean(execution_times)
            
            # Calculate success rate
            total_steps = len(execution_plan["steps"])
            metrics["success_rate"] = successful_steps / total_steps if total_steps > 0 else 0.0
            
            # Calculate solver utilization
            unique_solvers = len(set(step["solver_address"] for step in execution_plan["steps"]))
            total_available_solvers = len(self.solver_capabilities)
            metrics["solver_utilization"] = unique_solvers / total_available_solvers if total_available_solvers > 0 else 0.0
            
            # Estimate coordination overhead
            session_duration = (datetime.now() - session["created_at"]).total_seconds()
            pure_execution_time = metrics["total_execution_time"]
            metrics["coordination_overhead"] = max(0.0, session_duration - pure_execution_time)
            
            # Calculate overall efficiency score
            metrics["efficiency_score"] = (
                metrics["success_rate"] * 0.4 +
                (1.0 - min(1.0, metrics["coordination_overhead"] / 60.0)) * 0.3 +  # Penalty for overhead > 1 min
                metrics["solver_utilization"] * 0.2 +
                (1.0 - min(1.0, metrics["average_step_time"] / 300.0)) * 0.1  # Bonus for fast steps
            )
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating orchestration metrics: {e}")
            return {}
    
    async def handle_orchestration_failure(
        self, 
        session_id: str,
        failure_type: str = "execution_failure",
        retry_strategy: str = "smart_retry"
    ) -> bool:
        """
        Handle orchestration failures with recovery mechanisms
        Requirements: 3.3 - Orchestration failure handling and recovery
        """
        try:
            session = self.orchestration_sessions.get(session_id)
            if not session:
                logger.error(f"Session {session_id} not found for failure handling")
                return False
            
            logger.info(f"Handling orchestration failure for session {session_id}, type: {failure_type}")
            
            # Analyze failure
            failure_analysis = await self._analyze_orchestration_failure(session_id, failure_type)
            
            # Determine recovery strategy
            recovery_strategy = await self._determine_recovery_strategy(
                session_id, failure_analysis, retry_strategy
            )
            
            # Execute recovery
            recovery_success = False
            
            if recovery_strategy["type"] == "retry_with_same_solvers":
                recovery_success = await self._retry_with_same_solvers(session_id)
            elif recovery_strategy["type"] == "retry_with_different_solvers":
                recovery_success = await self._retry_with_different_solvers(session_id)
            elif recovery_strategy["type"] == "partial_recovery":
                recovery_success = await self._attempt_partial_recovery(session_id)
            elif recovery_strategy["type"] == "fallback_to_single_solver":
                recovery_success = await self._fallback_to_single_solver(session_id)
            else:
                logger.error(f"Unknown recovery strategy: {recovery_strategy['type']}")
                return False
            
            # Update session with recovery information
            if "recovery_attempts" not in session:
                session["recovery_attempts"] = []
            
            session["recovery_attempts"].append({
                "timestamp": datetime.now(),
                "failure_type": failure_type,
                "failure_analysis": failure_analysis,
                "recovery_strategy": recovery_strategy,
                "recovery_success": recovery_success
            })
            
            if recovery_success:
                logger.info(f"Successfully recovered orchestration session {session_id}")
                session["status"] = "recovered"
            else:
                logger.error(f"Failed to recover orchestration session {session_id}")
                session["status"] = "failed_recovery"
            
            return recovery_success
            
        except Exception as e:
            logger.error(f"Error handling orchestration failure: {e}")
            return False
    
    async def _analyze_orchestration_failure(self, session_id: str, failure_type: str) -> Dict:
        """Analyze orchestration failure to determine root cause"""
        try:
            session = self.orchestration_sessions[session_id]
            execution_plan = session["execution_plan"]
            results = session.get("results", {})
            
            analysis = {
                "failure_type": failure_type,
                "failed_steps": [],
                "healthy_solvers": [],
                "unhealthy_solvers": [],
                "capability_issues": [],
                "timing_issues": [],
                "root_cause": "unknown"
            }
            
            # Analyze step failures
            for step in execution_plan["steps"]:
                step_result = results.get(step["step_id"], {})
                solver_address = step["solver_address"]
                
                if not step_result.get("success", False):
                    analysis["failed_steps"].append({
                        "step_id": step["step_id"],
                        "solver_address": solver_address,
                        "capability": step["capability"],
                        "error_details": step_result.get("error_details", "Unknown error")
                    })
                
                # Check solver health
                if await self._is_solver_healthy_and_active(solver_address):
                    analysis["healthy_solvers"].append(solver_address)
                else:
                    analysis["unhealthy_solvers"].append(solver_address)
            
            # Determine root cause
            if len(analysis["unhealthy_solvers"]) > 0:
                analysis["root_cause"] = "solver_health_issues"
            elif len(analysis["failed_steps"]) == len(execution_plan["steps"]):
                analysis["root_cause"] = "complete_execution_failure"
            elif len(analysis["failed_steps"]) > len(execution_plan["steps"]) / 2:
                analysis["root_cause"] = "majority_step_failure"
            else:
                analysis["root_cause"] = "partial_step_failure"
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing orchestration failure: {e}")
            return {"failure_type": failure_type, "root_cause": "analysis_error"}
    
    async def _determine_recovery_strategy(
        self, 
        session_id: str, 
        failure_analysis: Dict, 
        retry_strategy: str
    ) -> Dict:
        """Determine the best recovery strategy based on failure analysis"""
        try:
            root_cause = failure_analysis.get("root_cause", "unknown")
            failed_steps = failure_analysis.get("failed_steps", [])
            unhealthy_solvers = failure_analysis.get("unhealthy_solvers", [])
            
            strategy = {
                "type": "retry_with_same_solvers",
                "confidence": 0.5,
                "estimated_success_rate": 0.5,
                "reasoning": "Default retry strategy"
            }
            
            if retry_strategy == "smart_retry":
                if root_cause == "solver_health_issues":
                    if len(unhealthy_solvers) < len(failed_steps):
                        strategy = {
                            "type": "retry_with_different_solvers",
                            "confidence": 0.8,
                            "estimated_success_rate": 0.7,
                            "reasoning": "Replace unhealthy solvers with healthy alternatives"
                        }
                    else:
                        strategy = {
                            "type": "fallback_to_single_solver",
                            "confidence": 0.6,
                            "estimated_success_rate": 0.6,
                            "reasoning": "Too many unhealthy solvers, fallback to single solver"
                        }
                
                elif root_cause == "partial_step_failure":
                    strategy = {
                        "type": "partial_recovery",
                        "confidence": 0.7,
                        "estimated_success_rate": 0.8,
                        "reasoning": "Retry only failed steps with successful steps intact"
                    }
                
                elif root_cause == "complete_execution_failure":
                    strategy = {
                        "type": "retry_with_different_solvers",
                        "confidence": 0.6,
                        "estimated_success_rate": 0.5,
                        "reasoning": "Complete failure suggests solver selection issues"
                    }
            
            elif retry_strategy == "conservative_retry":
                strategy = {
                    "type": "fallback_to_single_solver",
                    "confidence": 0.8,
                    "estimated_success_rate": 0.7,
                    "reasoning": "Conservative approach using single best solver"
                }
            
            elif retry_strategy == "aggressive_retry":
                strategy = {
                    "type": "retry_with_different_solvers",
                    "confidence": 0.6,
                    "estimated_success_rate": 0.6,
                    "reasoning": "Aggressive retry with completely different solver set"
                }
            
            return strategy
            
        except Exception as e:
            logger.error(f"Error determining recovery strategy: {e}")
            return {
                "type": "retry_with_same_solvers",
                "confidence": 0.3,
                "estimated_success_rate": 0.3,
                "reasoning": "Error in strategy determination, using default"
            }
    
    async def _retry_with_same_solvers(self, session_id: str) -> bool:
        """Retry orchestration with the same solvers"""
        try:
            session = self.orchestration_sessions[session_id]
            
            # Reset session status
            session["status"] = "retrying"
            session["results"] = {}
            session["errors"] = []
            
            # Re-execute the orchestration plan
            success = await self._execute_orchestrated_plan(session_id)
            
            if success:
                logger.info(f"Successfully retried orchestration with same solvers for session {session_id}")
            else:
                logger.warning(f"Retry with same solvers failed for session {session_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error retrying with same solvers: {e}")
            return False
    
    async def _retry_with_different_solvers(self, session_id: str) -> bool:
        """Retry orchestration with different solvers"""
        try:
            session = self.orchestration_sessions[session_id]
            required_capabilities = [
                CapabilityType(cap) for cap in session["required_capabilities"]
            ]
            
            # Find new solver combinations
            new_combinations = await self._find_complementary_solvers(required_capabilities)
            
            # Filter out previously used solvers
            old_solvers = set(session["selected_solvers"])
            new_combinations = [
                combo for combo in new_combinations
                if not any(solver in old_solvers for solver in combo)
            ]
            
            if not new_combinations:
                logger.warning(f"No alternative solver combinations found for session {session_id}")
                return False
            
            # Select best new combination
            best_combination = await self._select_best_solver_combination(
                new_combinations, required_capabilities
            )
            
            if not best_combination:
                logger.error(f"Failed to select new solver combination for session {session_id}")
                return False
            
            # Update session with new solvers
            session["selected_solvers"] = best_combination
            session["status"] = "retrying"
            session["results"] = {}
            session["errors"] = []
            
            # Create new execution plan
            session["execution_plan"] = await self._create_execution_plan(
                best_combination, required_capabilities, session["execution_strategy"]
            )
            
            # Execute with new plan
            success = await self._execute_orchestrated_plan(session_id)
            
            if success:
                logger.info(f"Successfully retried orchestration with different solvers for session {session_id}")
            else:
                logger.warning(f"Retry with different solvers failed for session {session_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error retrying with different solvers: {e}")
            return False
    
    async def _attempt_partial_recovery(self, session_id: str) -> bool:
        """Attempt partial recovery by retrying only failed steps"""
        try:
            session = self.orchestration_sessions[session_id]
            execution_plan = session["execution_plan"]
            results = session.get("results", {})
            
            # Identify failed steps
            failed_steps = []
            for step in execution_plan["steps"]:
                step_result = results.get(step["step_id"], {})
                if not step_result.get("success", False):
                    failed_steps.append(step)
            
            if not failed_steps:
                logger.info(f"No failed steps found for partial recovery in session {session_id}")
                return True
            
            logger.info(f"Attempting partial recovery for {len(failed_steps)} failed steps in session {session_id}")
            
            # Retry failed steps
            recovery_success = True
            for step in failed_steps:
                step_success = await self._execute_orchestration_step(session_id, step)
                if not step_success:
                    recovery_success = False
                    logger.warning(f"Failed to recover step {step['step_id']} in session {session_id}")
            
            if recovery_success:
                session["status"] = "completed"
                logger.info(f"Partial recovery successful for session {session_id}")
            else:
                logger.warning(f"Partial recovery incomplete for session {session_id}")
            
            return recovery_success
            
        except Exception as e:
            logger.error(f"Error in partial recovery: {e}")
            return False
    
    async def _fallback_to_single_solver(self, session_id: str) -> bool:
        """Fallback to single solver execution"""
        try:
            session = self.orchestration_sessions[session_id]
            required_capabilities = [
                CapabilityType(cap) for cap in session["required_capabilities"]
            ]
            
            # Find a single solver that can handle multiple capabilities
            best_solver = None
            best_score = 0.0
            
            for solver_address in self.solver_capabilities.keys():
                if not await self._is_solver_healthy_and_active(solver_address):
                    continue
                
                solver_capabilities = self.solver_capabilities[solver_address]
                capability_matches = 0
                total_score = 0.0
                
                for required_cap in required_capabilities:
                    for solver_cap in solver_capabilities:
                        if solver_cap.capability_type == required_cap:
                            capability_matches += 1
                            total_score += solver_cap.proficiency_score * solver_cap.success_rate
                            break
                
                if capability_matches > 0:
                    average_score = total_score / capability_matches
                    coverage_bonus = capability_matches / len(required_capabilities)
                    combined_score = average_score * coverage_bonus
                    
                    if combined_score > best_score:
                        best_score = combined_score
                        best_solver = solver_address
            
            if not best_solver:
                logger.error(f"No suitable single solver found for fallback in session {session_id}")
                return False
            
            logger.info(f"Falling back to single solver {best_solver} for session {session_id}")
            
            # Update session for single solver execution
            session["selected_solvers"] = [best_solver]
            session["execution_strategy"] = "sequential"  # Single solver executes sequentially
            session["status"] = "retrying"
            session["results"] = {}
            session["errors"] = []
            
            # Create simplified execution plan
            simplified_steps = []
            for i, capability in enumerate(required_capabilities):
                step = {
                    "step_id": f"fallback_step_{i}",
                    "solver_address": best_solver,
                    "capability": capability.value,
                    "execution_order": i,
                    "timeout": 300,
                    "retry_count": 2
                }
                simplified_steps.append(step)
            
            session["execution_plan"] = {
                "strategy": "sequential",
                "steps": simplified_steps,
                "dependencies": {},
                "timeouts": {},
                "fallback_options": {}
            }
            
            # Execute simplified plan
            success = await self._execute_orchestrated_plan(session_id)
            
            if success:
                logger.info(f"Single solver fallback successful for session {session_id}")
            else:
                logger.error(f"Single solver fallback failed for session {session_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error in single solver fallback: {e}")
            return False
    
    async def _monitor_conflicts(self):
        """Background task to monitor and resolve conflicts"""
        while True:
            try:
                # Check for resource contention conflicts
                await self._detect_resource_conflicts()
                
                # Check for capability overlap conflicts
                await self._detect_capability_conflicts()
                
                # Process active conflicts
                for conflict_id in list(self.active_conflicts.keys()):
                    await self._attempt_conflict_resolution(conflict_id)
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in conflict monitoring task: {e}")
                await asyncio.sleep(30)
    
    async def _detect_resource_conflicts(self):
        """Detect resource contention conflicts"""
        try:
            # Check for solvers with overlapping task assignments
            solver_tasks = defaultdict(list)
            for task in self.active_tasks.values():
                if task.assigned_solver:
                    solver_tasks[task.assigned_solver].append(task)
            
            # Look for overloaded solvers
            for solver_address, tasks in solver_tasks.items():
                capacity_info = await self.assess_solver_capacity(solver_address)
                available_capacity = capacity_info.get("available_capacity", 0)
                
                if available_capacity < 0.1 and len(tasks) > 1:  # Overloaded
                    # Create conflict for resource contention
                    conflict_id = f"resource_conflict_{solver_address}_{datetime.now().timestamp()}"
                    
                    if conflict_id not in self.active_conflicts:
                        conflict = CoordinationConflict(
                            conflict_id=conflict_id,
                            conflict_type=ConflictType.RESOURCE_CONTENTION,
                            involved_solvers=[solver_address],
                            resource_contested=f"solver_capacity_{solver_address}",
                            priority_levels={task.task_id: task.priority.value for task in tasks},
                            created_at=datetime.now()
                        )
                        
                        self.active_conflicts[conflict_id] = conflict
                        logger.warning(f"Resource contention conflict detected: {conflict_id}")
            
        except Exception as e:
            logger.error(f"Error detecting resource conflicts: {e}")
    
    async def _detect_capability_conflicts(self):
        """Detect capability overlap conflicts"""
        try:
            # Check for multiple solvers claiming same capability for same task
            capability_assignments = defaultdict(list)
            
            for task in self.active_tasks.values():
                if task.assigned_solver:
                    key = (task.capability_required, tuple(task.target_chains))
                    capability_assignments[key].append((task, task.assigned_solver))
            
            # Look for potential conflicts
            for (capability, chains), assignments in capability_assignments.items():
                if len(assignments) > 1:
                    # Multiple tasks with same capability - check for conflicts
                    solvers_involved = list(set(solver for _, solver in assignments))
                    
                    if len(solvers_involved) > 1:
                        conflict_id = f"capability_conflict_{capability.value}_{datetime.now().timestamp()}"
                        
                        if conflict_id not in self.active_conflicts:
                            conflict = CoordinationConflict(
                                conflict_id=conflict_id,
                                conflict_type=ConflictType.CAPABILITY_OVERLAP,
                                involved_solvers=solvers_involved,
                                resource_contested=f"capability_{capability.value}",
                                priority_levels={
                                    task.task_id: task.priority.value 
                                    for task, _ in assignments
                                },
                                created_at=datetime.now()
                            )
                            
                            self.active_conflicts[conflict_id] = conflict
                            logger.warning(f"Capability overlap conflict detected: {conflict_id}")
            
        except Exception as e:
            logger.error(f"Error detecting capability conflicts: {e}")
    
    async def _attempt_conflict_resolution(self, conflict_id: str):
        """Attempt to resolve a specific conflict"""
        try:
            conflict = self.active_conflicts.get(conflict_id)
            if not conflict:
                return
            
            resolution_success = False
            
            if conflict.conflict_type == ConflictType.RESOURCE_CONTENTION:
                resolution_success = await self._resolve_resource_contention(conflict)
            elif conflict.conflict_type == ConflictType.CAPABILITY_OVERLAP:
                resolution_success = await self._resolve_capability_overlap(conflict)
            elif conflict.conflict_type == ConflictType.PRIORITY_DISPUTE:
                resolution_success = await self._resolve_priority_dispute(conflict)
            
            if resolution_success:
                conflict.resolved_at = datetime.now()
                conflict.resolution_method = f"auto_resolution_{conflict.conflict_type.value}"
                
                # Move to history
                self.conflict_resolution_history.append(conflict)
                del self.active_conflicts[conflict_id]
                
                logger.info(f"Conflict {conflict_id} resolved successfully")
            
        except Exception as e:
            logger.error(f"Error resolving conflict {conflict_id}: {e}")
    
    async def _resolve_resource_contention(self, conflict: CoordinationConflict) -> bool:
        """Resolve resource contention conflict"""
        try:
            # Get tasks for the overloaded solver
            solver_address = conflict.involved_solvers[0]
            solver_tasks = [
                task for task in self.active_tasks.values()
                if task.assigned_solver == solver_address
            ]
            
            if len(solver_tasks) <= 1:
                return True  # No longer a conflict
            
            # Sort tasks by priority
            solver_tasks.sort(key=lambda t: (t.priority.value, t.deadline))
            
            # Keep highest priority task, reassign others
            keep_task = solver_tasks[0]
            reassign_tasks = solver_tasks[1:]
            
            # Try to reassign lower priority tasks
            reassigned_count = 0
            for task in reassign_tasks:
                # Find alternative solvers
                eligible_solvers = await self.get_solvers_by_capability(
                    task.capability_required,
                    required_chains=task.target_chains,
                    required_tokens=task.required_tokens
                )
                
                # Find available alternative
                for alt_solver_addr, _ in eligible_solvers:
                    if alt_solver_addr != solver_address:
                        alt_capacity = await self.assess_solver_capacity(alt_solver_addr)
                        if alt_capacity.get("available", False):
                            # Reassign task
                            task.assigned_solver = alt_solver_addr
                            reassigned_count += 1
                            logger.info(f"Reassigned task {task.task_id} from {solver_address} to {alt_solver_addr}")
                            break
            
            return reassigned_count > 0
            
        except Exception as e:
            logger.error(f"Error resolving resource contention: {e}")
            return False
    
    async def _resolve_capability_overlap(self, conflict: CoordinationConflict) -> bool:
        """Resolve capability overlap conflict"""
        try:
            # For capability overlap, prefer solver with better performance
            involved_solvers = conflict.involved_solvers
            
            # Score each solver
            solver_scores = {}
            for solver_address in involved_solvers:
                solver = await self.solver_network_service.get_solver_by_address(solver_address)
                if solver:
                    # Calculate combined score
                    reputation_score = solver.reputation_score.total_score
                    health_status = self.solver_health_status.get(solver_address)
                    health_score = health_status.health_score if health_status else 0.0
                    
                    combined_score = reputation_score * 0.7 + health_score * 0.3
                    solver_scores[solver_address] = combined_score
            
            if not solver_scores:
                return False
            
            # Select winner (highest score)
            winner = max(solver_scores.items(), key=lambda x: x[1])[0]
            conflict.winner = winner
            
            # Reassign tasks from losing solvers to winner or alternatives
            for solver_address in involved_solvers:
                if solver_address != winner:
                    # Find tasks assigned to this solver
                    solver_tasks = [
                        task for task in self.active_tasks.values()
                        if task.assigned_solver == solver_address
                    ]
                    
                    # Try to reassign to winner or find alternatives
                    for task in solver_tasks:
                        winner_capacity = await self.assess_solver_capacity(winner)
                        if winner_capacity.get("available", False):
                            task.assigned_solver = winner
                        else:
                            # Find alternative solver
                            eligible_solvers = await self.get_solvers_by_capability(
                                task.capability_required,
                                required_chains=task.target_chains,
                                required_tokens=task.required_tokens
                            )
                            
                            for alt_solver_addr, _ in eligible_solvers:
                                if alt_solver_addr not in involved_solvers:
                                    alt_capacity = await self.assess_solver_capacity(alt_solver_addr)
                                    if alt_capacity.get("available", False):
                                        task.assigned_solver = alt_solver_addr
                                        break
            
            return True
            
        except Exception as e:
            logger.error(f"Error resolving capability overlap: {e}")
            return False
    
    async def _resolve_priority_dispute(self, conflict: CoordinationConflict) -> bool:
        """Resolve priority dispute conflict"""
        try:
            # Sort by priority levels and assign accordingly
            priority_items = list(conflict.priority_levels.items())
            priority_items.sort(key=lambda x: x[1])  # Sort by priority value
            
            # Highest priority wins
            if priority_items:
                highest_priority_task = priority_items[0][0]
                
                # Find the task and ensure it gets the best solver
                for task in self.active_tasks.values():
                    if task.task_id == highest_priority_task:
                        # Get best available solver for this task
                        eligible_solvers = await self.get_solvers_by_capability(
                            task.capability_required,
                            required_chains=task.target_chains,
                            required_tokens=task.required_tokens
                        )
                        
                        if eligible_solvers:
                            best_solver = eligible_solvers[0][0]  # First is best scored
                            task.assigned_solver = best_solver
                            conflict.winner = best_solver
                            return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error resolving priority dispute: {e}")
            return False
    
    async def get_conflict_resolution_report(self) -> Dict:
        """Get comprehensive conflict resolution report"""
        try:
            active_conflicts = len(self.active_conflicts)
            resolved_conflicts = len(self.conflict_resolution_history)
            
            # Calculate resolution statistics
            resolution_stats = defaultdict(int)
            for conflict in self.conflict_resolution_history:
                resolution_stats[conflict.conflict_type.value] += 1
            
            # Calculate average resolution time
            resolution_times = []
            for conflict in self.conflict_resolution_history:
                if conflict.resolved_at and conflict.created_at:
                    resolution_time = (conflict.resolved_at - conflict.created_at).total_seconds()
                    resolution_times.append(resolution_time)
            
            avg_resolution_time = np.mean(resolution_times) if resolution_times else 0.0
            
            return {
                "active_conflicts": active_conflicts,
                "resolved_conflicts": resolved_conflicts,
                "total_conflicts": active_conflicts + resolved_conflicts,
                "resolution_rate": resolved_conflicts / (active_conflicts + resolved_conflicts) if (active_conflicts + resolved_conflicts) > 0 else 0.0,
                "average_resolution_time_seconds": avg_resolution_time,
                "conflicts_by_type": dict(resolution_stats),
                "active_conflict_details": [
                    {
                        "conflict_id": conflict.conflict_id,
                        "type": conflict.conflict_type.value,
                        "involved_solvers": conflict.involved_solvers,
                        "created_at": conflict.created_at.isoformat(),
                        "age_seconds": (datetime.now() - conflict.created_at).total_seconds()
                    }
                    for conflict in self.active_conflicts.values()
                ]
            }
            
        except Exception as e:
            logger.error(f"Error generating conflict resolution report: {e}")
            return {}
    
    # Advanced Workload Distribution Optimization
    
    async def optimize_workload_distribution_advanced(
        self,
        tasks: List[WorkloadTask],
        optimization_objectives: Dict[str, float] = None
    ) -> Dict[str, List[WorkloadTask]]:
        """
        Advanced workload distribution with multi-objective optimization
        Requirements: 3.2 - Advanced capacity-aware workload distribution algorithms
        """
        try:
            if optimization_objectives is None:
                optimization_objectives = {
                    "load_balance": 0.4,
                    "capability_match": 0.3,
                    "execution_time": 0.2,
                    "cost_efficiency": 0.1
                }
            
            # Get all available solvers and their capabilities
            available_solvers = {}
            for solver_address in self.solver_capabilities.keys():
                if await self._is_solver_healthy_and_active(solver_address):
                    capacity_info = await self.assess_solver_capacity(solver_address)
                    if capacity_info.get("available", False):
                        available_solvers[solver_address] = capacity_info
            
            if not available_solvers:
                logger.warning("No available solvers for workload distribution")
                return {}
            
            # Use genetic algorithm for multi-objective optimization
            best_distribution = await self._genetic_algorithm_optimization(
                tasks, available_solvers, optimization_objectives
            )
            
            if not best_distribution:
                # Fallback to balanced distribution
                logger.info("Genetic algorithm failed, falling back to balanced distribution")
                return await self.distribute_workload(tasks, "balanced")
            
            # Apply the optimized distribution
            for solver_address, assigned_tasks in best_distribution.items():
                for task in assigned_tasks:
                    task.assigned_solver = solver_address
                    task.status = "assigned"
                    self.active_tasks[task.task_id] = task
            
            # Record optimization results
            efficiency_score = await self._calculate_distribution_efficiency(best_distribution)
            self.workload_distribution_history.append({
                "timestamp": datetime.now(),
                "strategy": "genetic_algorithm",
                "total_tasks": len(tasks),
                "distribution": {addr: len(tasks) for addr, tasks in best_distribution.items()},
                "efficiency_score": efficiency_score,
                "objectives": optimization_objectives
            })
            
            logger.info(f"Advanced optimization distributed {len(tasks)} tasks with efficiency {efficiency_score:.3f}")
            return best_distribution
            
        except Exception as e:
            logger.error(f"Error in advanced workload optimization: {e}")
            return {}
    
    async def _genetic_algorithm_optimization(
        self,
        tasks: List[WorkloadTask],
        available_solvers: Dict[str, Dict],
        objectives: Dict[str, float],
        population_size: int = 20,
        generations: int = 50
    ) -> Optional[Dict[str, List[WorkloadTask]]]:
        """
        Genetic algorithm for multi-objective workload optimization
        """
        try:
            solver_addresses = list(available_solvers.keys())
            
            if not solver_addresses or not tasks:
                return None
            
            # Initialize population
            population = []
            for _ in range(population_size):
                individual = await self._create_random_distribution(tasks, solver_addresses)
                population.append(individual)
            
            # Evolution loop
            for generation in range(generations):
                # Evaluate fitness
                fitness_scores = []
                for individual in population:
                    fitness = await self._evaluate_distribution_fitness(individual, objectives)
                    fitness_scores.append(fitness)
                
                # Selection (tournament selection)
                new_population = []
                for _ in range(population_size):
                    parent1 = await self._tournament_selection(population, fitness_scores)
                    parent2 = await self._tournament_selection(population, fitness_scores)
                    
                    # Crossover
                    child = await self._crossover_distributions(parent1, parent2, tasks)
                    
                    # Mutation
                    child = await self._mutate_distribution(child, solver_addresses, tasks)
                    
                    new_population.append(child)
                
                population = new_population
            
            # Return best individual
            final_fitness_scores = []
            for individual in population:
                fitness = await self._evaluate_distribution_fitness(individual, objectives)
                final_fitness_scores.append(fitness)
            
            best_index = final_fitness_scores.index(max(final_fitness_scores))
            return population[best_index]
            
        except Exception as e:
            logger.error(f"Error in genetic algorithm optimization: {e}")
            return None
    
    async def _create_random_distribution(
        self, 
        tasks: List[WorkloadTask], 
        solver_addresses: List[str]
    ) -> Dict[str, List[WorkloadTask]]:
        """Create a random task distribution"""
        try:
            distribution = defaultdict(list)
            
            for task in tasks:
                # Find capable solvers for this task
                capable_solvers = []
                for solver_address in solver_addresses:
                    solver_capabilities = self.solver_capabilities.get(solver_address, [])
                    if any(cap.capability_type == task.capability_required for cap in solver_capabilities):
                        # Check chain and token compatibility
                        for cap in solver_capabilities:
                            if (cap.capability_type == task.capability_required and
                                any(chain in cap.supported_chains for chain in task.target_chains) and
                                any(token in cap.supported_tokens for token in task.required_tokens)):
                                capable_solvers.append(solver_address)
                                break
                
                if capable_solvers:
                    # Randomly assign to a capable solver
                    chosen_solver = np.random.choice(capable_solvers)
                    distribution[chosen_solver].append(task)
            
            return dict(distribution)
            
        except Exception as e:
            logger.error(f"Error creating random distribution: {e}")
            return {}
    
    async def _evaluate_distribution_fitness(
        self, 
        distribution: Dict[str, List[WorkloadTask]], 
        objectives: Dict[str, float]
    ) -> float:
        """Evaluate fitness of a distribution based on multiple objectives"""
        try:
            fitness = 0.0
            
            # Load balance score
            if "load_balance" in objectives:
                load_balance_score = await self._calculate_load_balance_score(distribution)
                fitness += objectives["load_balance"] * load_balance_score
            
            # Capability match score
            if "capability_match" in objectives:
                capability_score = await self._calculate_capability_match_score(distribution)
                fitness += objectives["capability_match"] * capability_score
            
            # Execution time score
            if "execution_time" in objectives:
                time_score = await self._calculate_execution_time_score(distribution)
                fitness += objectives["execution_time"] * time_score
            
            # Cost efficiency score
            if "cost_efficiency" in objectives:
                cost_score = await self._calculate_cost_efficiency_score(distribution)
                fitness += objectives["cost_efficiency"] * cost_score
            
            return fitness
            
        except Exception as e:
            logger.error(f"Error evaluating distribution fitness: {e}")
            return 0.0
    
    async def _calculate_load_balance_score(self, distribution: Dict[str, List[WorkloadTask]]) -> float:
        """Calculate load balance score (higher is better)"""
        try:
            if not distribution:
                return 0.0
            
            task_counts = [len(tasks) for tasks in distribution.values()]
            if len(task_counts) <= 1:
                return 1.0
            
            mean_tasks = np.mean(task_counts)
            variance = np.var(task_counts)
            
            # Lower variance is better
            balance_score = 1.0 / (1.0 + variance / (mean_tasks + 1))
            return balance_score
            
        except Exception as e:
            logger.error(f"Error calculating load balance score: {e}")
            return 0.0
    
    async def _calculate_capability_match_score(self, distribution: Dict[str, List[WorkloadTask]]) -> float:
        """Calculate capability matching score (higher is better)"""
        try:
            total_score = 0.0
            total_tasks = 0
            
            for solver_address, tasks in distribution.items():
                solver_capabilities = self.solver_capabilities.get(solver_address, [])
                
                for task in tasks:
                    # Find matching capability
                    best_match_score = 0.0
                    for cap in solver_capabilities:
                        if cap.capability_type == task.capability_required:
                            # Score based on proficiency and success rate
                            match_score = cap.proficiency_score * cap.success_rate
                            best_match_score = max(best_match_score, match_score)
                    
                    total_score += best_match_score
                    total_tasks += 1
            
            return total_score / total_tasks if total_tasks > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating capability match score: {e}")
            return 0.0
    
    async def _calculate_execution_time_score(self, distribution: Dict[str, List[WorkloadTask]]) -> float:
        """Calculate execution time score (lower total time is better)"""
        try:
            total_time = 0.0
            max_solver_time = 0.0
            
            for solver_address, tasks in distribution.items():
                solver_time = sum(task.estimated_execution_time for task in tasks)
                total_time += solver_time
                max_solver_time = max(max_solver_time, solver_time)
            
            if max_solver_time == 0:
                return 1.0
            
            # Score based on parallel execution time (bottleneck solver)
            # Lower max time is better
            time_score = 1.0 / (1.0 + max_solver_time / 300.0)  # Normalize by 5 minutes
            return time_score
            
        except Exception as e:
            logger.error(f"Error calculating execution time score: {e}")
            return 0.0
    
    async def _calculate_cost_efficiency_score(self, distribution: Dict[str, List[WorkloadTask]]) -> float:
        """Calculate cost efficiency score"""
        try:
            total_cost = 0.0
            total_value = 0.0
            
            for solver_address, tasks in distribution.items():
                solver = await self.solver_network_service.get_solver_by_address(solver_address)
                if not solver:
                    continue
                
                # Estimate cost based on solver tier and reputation
                base_cost = 1.0
                if solver.tier.value == "platinum":
                    base_cost = 1.5
                elif solver.tier.value == "gold":
                    base_cost = 1.2
                elif solver.tier.value == "silver":
                    base_cost = 1.1
                
                for task in tasks:
                    task_cost = base_cost * task.estimated_execution_time / 60.0  # Cost per minute
                    task_value = float(task.estimated_volume)
                    
                    total_cost += task_cost
                    total_value += task_value
            
            if total_cost == 0:
                return 1.0
            
            # Higher value-to-cost ratio is better
            efficiency = total_value / total_cost
            return min(1.0, efficiency / 100.0)  # Normalize
            
        except Exception as e:
            logger.error(f"Error calculating cost efficiency score: {e}")
            return 0.0
    
    async def _tournament_selection(
        self, 
        population: List[Dict], 
        fitness_scores: List[float], 
        tournament_size: int = 3
    ) -> Dict:
        """Tournament selection for genetic algorithm"""
        try:
            tournament_indices = np.random.choice(len(population), tournament_size, replace=False)
            tournament_fitness = [fitness_scores[i] for i in tournament_indices]
            
            winner_index = tournament_indices[tournament_fitness.index(max(tournament_fitness))]
            return population[winner_index]
            
        except Exception as e:
            logger.error(f"Error in tournament selection: {e}")
            return population[0] if population else {}
    
    async def _crossover_distributions(
        self, 
        parent1: Dict[str, List[WorkloadTask]], 
        parent2: Dict[str, List[WorkloadTask]], 
        tasks: List[WorkloadTask]
    ) -> Dict[str, List[WorkloadTask]]:
        """Crossover operation for genetic algorithm"""
        try:
            child = defaultdict(list)
            
            # For each task, randomly choose assignment from parent1 or parent2
            for task in tasks:
                # Find which solver has this task in each parent
                parent1_solver = None
                parent2_solver = None
                
                for solver, solver_tasks in parent1.items():
                    if task in solver_tasks:
                        parent1_solver = solver
                        break
                
                for solver, solver_tasks in parent2.items():
                    if task in solver_tasks:
                        parent2_solver = solver
                        break
                
                # Choose assignment
                if parent1_solver and parent2_solver:
                    chosen_solver = np.random.choice([parent1_solver, parent2_solver])
                elif parent1_solver:
                    chosen_solver = parent1_solver
                elif parent2_solver:
                    chosen_solver = parent2_solver
                else:
                    continue  # Skip unassigned tasks
                
                child[chosen_solver].append(task)
            
            return dict(child)
            
        except Exception as e:
            logger.error(f"Error in crossover: {e}")
            return parent1
    
    async def _mutate_distribution(
        self, 
        distribution: Dict[str, List[WorkloadTask]], 
        solver_addresses: List[str], 
        tasks: List[WorkloadTask],
        mutation_rate: float = 0.1
    ) -> Dict[str, List[WorkloadTask]]:
        """Mutation operation for genetic algorithm"""
        try:
            mutated = defaultdict(list)
            
            # Copy current distribution
            for solver, solver_tasks in distribution.items():
                mutated[solver] = solver_tasks.copy()
            
            # Mutate some task assignments
            for task in tasks:
                if np.random.random() < mutation_rate:
                    # Find current assignment
                    current_solver = None
                    for solver, solver_tasks in mutated.items():
                        if task in solver_tasks:
                            current_solver = solver
                            solver_tasks.remove(task)
                            break
                    
                    # Find capable solvers for reassignment
                    capable_solvers = []
                    for solver_address in solver_addresses:
                        solver_capabilities = self.solver_capabilities.get(solver_address, [])
                        if any(cap.capability_type == task.capability_required for cap in solver_capabilities):
                            capable_solvers.append(solver_address)
                    
                    if capable_solvers:
                        new_solver = np.random.choice(capable_solvers)
                        mutated[new_solver].append(task)
            
            return dict(mutated)
            
        except Exception as e:
            logger.error(f"Error in mutation: {e}")
            return distribution
    
    async def implement_dynamic_load_balancing(self) -> bool:
        """
        Implement dynamic load balancing based on real-time solver performance
        Requirements: 3.2 - Dynamic rebalancing for changing conditions
        """
        try:
            # Get current load distribution
            current_loads = {}
            overloaded_solvers = []
            underloaded_solvers = []
            
            for solver_address in self.solver_capabilities.keys():
                capacity_info = await self.assess_solver_capacity(solver_address)
                if capacity_info.get("available", False):
                    load = 1.0 - capacity_info.get("available_capacity", 0.0)
                    current_loads[solver_address] = load
                    
                    if load > 0.8:  # Overloaded threshold
                        overloaded_solvers.append(solver_address)
                    elif load < 0.3:  # Underloaded threshold
                        underloaded_solvers.append(solver_address)
            
            if not overloaded_solvers or not underloaded_solvers:
                logger.debug("No load balancing needed")
                return True
            
            # Redistribute tasks from overloaded to underloaded solvers
            rebalanced_tasks = 0
            
            for overloaded_solver in overloaded_solvers:
                # Get tasks assigned to overloaded solver
                solver_tasks = [
                    task for task in self.active_tasks.values()
                    if task.assigned_solver == overloaded_solver and task.status == "assigned"
                ]
                
                # Sort by priority (move lower priority tasks first)
                solver_tasks.sort(key=lambda t: t.priority.value, reverse=True)
                
                # Try to move some tasks to underloaded solvers
                for task in solver_tasks[:len(solver_tasks)//2]:  # Move up to half
                    # Find compatible underloaded solver
                    for underloaded_solver in underloaded_solvers:
                        capable_solvers = await self.get_solvers_by_capability(
                            task.capability_required,
                            required_chains=task.target_chains,
                            required_tokens=task.required_tokens
                        )
                        
                        if any(solver_addr == underloaded_solver for solver_addr, _ in capable_solvers):
                            # Check if underloaded solver still has capacity
                            capacity_info = await self.assess_solver_capacity(underloaded_solver)
                            if capacity_info.get("available_capacity", 0) > 0.2:
                                # Move the task
                                task.assigned_solver = underloaded_solver
                                rebalanced_tasks += 1
                                logger.info(f"Rebalanced task {task.task_id} from {overloaded_solver} to {underloaded_solver}")
                                break
                
                if rebalanced_tasks >= 5:  # Limit rebalancing per cycle
                    break
            
            if rebalanced_tasks > 0:
                logger.info(f"Dynamic load balancing completed: {rebalanced_tasks} tasks rebalanced")
            
            return True
            
        except Exception as e:
            logger.error(f"Error in dynamic load balancing: {e}")
            return False
    
    async def predict_solver_performance(
        self, 
        solver_address: str, 
        task: WorkloadTask
    ) -> Dict[str, float]:
        """
        Predict solver performance for a specific task
        Requirements: 3.2 - Performance prediction for optimal assignment
        """
        try:
            solver = await self.solver_network_service.get_solver_by_address(solver_address)
            if not solver:
                return {"success_probability": 0.0, "estimated_time": float('inf'), "confidence": 0.0}
            
            # Get solver capabilities
            solver_capabilities = self.solver_capabilities.get(solver_address, [])
            matching_capability = None
            
            for cap in solver_capabilities:
                if cap.capability_type == task.capability_required:
                    matching_capability = cap
                    break
            
            if not matching_capability:
                return {"success_probability": 0.0, "estimated_time": float('inf'), "confidence": 0.0}
            
            # Base predictions from capability
            base_success_rate = matching_capability.success_rate
            base_execution_time = matching_capability.average_execution_time
            
            # Adjust based on solver health
            health_status = self.solver_health_status.get(solver_address)
            health_multiplier = health_status.health_score if health_status else 0.5
            
            # Adjust based on current load
            capacity_info = await self.assess_solver_capacity(solver_address)
            load_factor = 1.0 - capacity_info.get("available_capacity", 0.0)
            
            # Performance degradation under load
            load_multiplier = 1.0 + (load_factor * 0.5)  # Up to 50% slower under full load
            
            # Adjust based on task complexity
            complexity_factor = 1.0
            if task.estimated_volume > Decimal('500'):
                complexity_factor = 1.2  # Large volume tasks are more complex
            
            if len(task.target_chains) > 1:
                complexity_factor *= 1.1  # Multi-chain tasks are more complex
            
            # Calculate predictions
            predicted_success_rate = base_success_rate * health_multiplier
            predicted_execution_time = base_execution_time * load_multiplier * complexity_factor
            
            # Calculate confidence based on historical data
            historical_tasks = solver.performance_metrics.total_intents_completed
            confidence = min(1.0, historical_tasks / 10.0)  # Full confidence after 10 tasks
            
            # Adjust for solver tier
            tier_bonus = {
                "bronze": 0.0,
                "silver": 0.05,
                "gold": 0.10,
                "platinum": 0.15
            }.get(solver.tier.value, 0.0)
            
            predicted_success_rate = min(1.0, predicted_success_rate + tier_bonus)
            
            return {
                "success_probability": predicted_success_rate,
                "estimated_time": predicted_execution_time,
                "confidence": confidence,
                "health_score": health_multiplier,
                "load_factor": load_factor,
                "complexity_factor": complexity_factor
            }
            
        except Exception as e:
            logger.error(f"Error predicting solver performance: {e}")
            return {"success_probability": 0.0, "estimated_time": float('inf'), "confidence": 0.0}
    
    async def optimize_task_assignment_ml(
        self, 
        tasks: List[WorkloadTask]
    ) -> Dict[str, List[WorkloadTask]]:
        """
        Machine learning-based task assignment optimization
        Requirements: 3.2 - ML-based optimization for task assignment
        """
        try:
            # Collect features for each task-solver pair
            assignment_scores = {}
            
            for task in tasks:
                task_scores = {}
                
                # Get all capable solvers
                capable_solvers = await self.get_solvers_by_capability(
                    task.capability_required,
                    required_chains=task.target_chains,
                    required_tokens=task.required_tokens
                )
                
                for solver_address, capability in capable_solvers:
                    # Predict performance
                    performance_pred = await self.predict_solver_performance(solver_address, task)
                    
                    # Calculate composite score
                    success_weight = 0.4
                    time_weight = 0.3
                    confidence_weight = 0.2
                    health_weight = 0.1
                    
                    # Normalize time score (lower is better)
                    max_time = 300.0  # 5 minutes max
                    time_score = max(0.0, 1.0 - (performance_pred["estimated_time"] / max_time))
                    
                    composite_score = (
                        performance_pred["success_probability"] * success_weight +
                        time_score * time_weight +
                        performance_pred["confidence"] * confidence_weight +
                        performance_pred["health_score"] * health_weight
                    )
                    
                    task_scores[solver_address] = composite_score
                
                assignment_scores[task.task_id] = task_scores
            
            # Use Hungarian algorithm for optimal assignment
            optimal_assignment = await self._hungarian_assignment(tasks, assignment_scores)
            
            # Convert to distribution format
            distribution = defaultdict(list)
            for task_id, solver_address in optimal_assignment.items():
                task = next(t for t in tasks if t.task_id == task_id)
                distribution[solver_address].append(task)
            
            logger.info(f"ML-based optimization assigned {len(tasks)} tasks optimally")
            return dict(distribution)
            
        except Exception as e:
            logger.error(f"Error in ML-based task assignment: {e}")
            return {}
    
    async def _hungarian_assignment(
        self, 
        tasks: List[WorkloadTask], 
        assignment_scores: Dict[str, Dict[str, float]]
    ) -> Dict[str, str]:
        """
        Simplified Hungarian algorithm for optimal task assignment
        """
        try:
            # For simplicity, use greedy assignment with conflict resolution
            assignment = {}
            solver_loads = defaultdict(int)
            
            # Sort tasks by priority
            sorted_tasks = sorted(tasks, key=lambda t: t.priority.value)
            
            for task in sorted_tasks:
                task_scores = assignment_scores.get(task.task_id, {})
                
                if not task_scores:
                    continue
                
                # Sort solvers by score (descending)
                sorted_solvers = sorted(
                    task_scores.items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )
                
                # Assign to best available solver
                for solver_address, score in sorted_solvers:
                    # Check solver capacity
                    if solver_loads[solver_address] < self.max_concurrent_tasks_per_solver:
                        assignment[task.task_id] = solver_address
                        solver_loads[solver_address] += 1
                        break
            
            return assignment
            
        except Exception as e:
            logger.error(f"Error in Hungarian assignment: {e}")
            return {}
    
    async def get_workload_optimization_report(self) -> Dict:
        """Get comprehensive workload optimization performance report"""
        try:
            if not self.workload_distribution_history:
                return {"message": "No workload distribution history available"}
            
            # Calculate statistics from history
            recent_distributions = self.workload_distribution_history[-10:]  # Last 10 distributions
            
            efficiency_scores = [dist["efficiency_score"] for dist in recent_distributions]
            avg_efficiency = np.mean(efficiency_scores) if efficiency_scores else 0.0
            
            strategies_used = [dist["strategy"] for dist in recent_distributions]
            strategy_counts = {}
            for strategy in strategies_used:
                strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
            
            # Calculate load balance metrics
            load_balances = []
            for dist in recent_distributions:
                task_counts = list(dist["distribution"].values())
                if len(task_counts) > 1:
                    variance = np.var(task_counts)
                    mean_tasks = np.mean(task_counts)
                    balance_score = 1.0 / (1.0 + variance / (mean_tasks + 1))
                    load_balances.append(balance_score)
            
            avg_load_balance = np.mean(load_balances) if load_balances else 0.0
            
            # Current system status
            active_tasks_count = len(self.active_tasks)
            solver_utilization = {}
            
            for solver_address in self.solver_capabilities.keys():
                capacity_info = await self.assess_solver_capacity(solver_address)
                if capacity_info.get("available", False):
                    utilization = 1.0 - capacity_info.get("available_capacity", 0.0)
                    solver_utilization[solver_address] = utilization
            
            avg_utilization = np.mean(list(solver_utilization.values())) if solver_utilization else 0.0
            
            return {
                "optimization_performance": {
                    "average_efficiency": avg_efficiency,
                    "average_load_balance": avg_load_balance,
                    "total_distributions": len(self.workload_distribution_history),
                    "recent_distributions": len(recent_distributions)
                },
                "strategy_usage": strategy_counts,
                "current_status": {
                    "active_tasks": active_tasks_count,
                    "available_solvers": len(solver_utilization),
                    "average_utilization": avg_utilization,
                    "solver_utilization": solver_utilization
                },
                "performance_trends": {
                    "efficiency_trend": efficiency_scores[-5:] if len(efficiency_scores) >= 5 else efficiency_scores,
                    "load_balance_trend": load_balances[-5:] if len(load_balances) >= 5 else load_balances
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating workload optimization report: {e}")
            return {"error": str(e)}
    
    # Reputation and Performance Tracking System
    
    async def track_solver_performance(
        self,
        solver_address: str,
        task_id: str,
        execution_result: Dict[str, Any]
    ) -> bool:
        """
        Track solver performance for reputation scoring
        Requirements: 3.4 - Comprehensive solver performance metrics
        """
        try:
            # Create performance record
            performance_record = {
                "timestamp": datetime.now(),
                "task_id": task_id,
                "solver_address": solver_address,
                "success": execution_result.get("success", False),
                "execution_time": execution_result.get("execution_time", 0.0),
                "gas_used": execution_result.get("gas_used", 0),
                "slippage": execution_result.get("slippage", 0.0),
                "error_type": execution_result.get("error_type"),
                "error_message": execution_result.get("error_message"),
                "volume_handled": execution_result.get("volume_handled", Decimal('0')),
                "profit_generated": execution_result.get("profit_generated", Decimal('0')),
                "user_satisfaction": execution_result.get("user_satisfaction", 0.0)
            }
            
            # Add to performance history
            self.solver_performance_history[solver_address].append(performance_record)
            
            # Limit history size (keep last 100 records per solver)
            if len(self.solver_performance_history[solver_address]) > 100:
                self.solver_performance_history[solver_address] = \
                    self.solver_performance_history[solver_address][-100:]
            
            # Update solver capability metrics
            if performance_record["success"]:
                # Find the capability used for this task
                task = self.active_tasks.get(task_id) or self.completed_tasks.get(task_id)
                if task:
                    await self.update_solver_capability(
                        solver_address,
                        task.capability_required,
                        1.0,  # Full proficiency for successful execution
                        1.0,  # Full success rate
                        performance_record["execution_time"]
                    )
            
            # Update reputation score
            await self._update_solver_reputation(solver_address, performance_record)
            
            logger.info(f"Tracked performance for solver {solver_address}, task {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error tracking solver performance: {e}")
            return False
    
    async def _update_solver_reputation(
        self,
        solver_address: str,
        performance_record: Dict[str, Any]
    ) -> None:
        """
        Update solver reputation based on performance record
        Requirements: 3.4 - Reputation scoring algorithms
        """
        try:
            solver = await self.solver_network_service.get_solver_by_address(solver_address)
            if not solver:
                return
            
            # Calculate performance impact on reputation
            performance_impact = 0.0
            
            if performance_record["success"]:
                # Positive impact for successful execution
                base_impact = 1.0
                
                # Bonus for fast execution
                execution_time = performance_record["execution_time"]
                if execution_time < 30.0:  # Under 30 seconds
                    base_impact += 0.2
                elif execution_time < 60.0:  # Under 1 minute
                    base_impact += 0.1
                
                # Bonus for high volume
                volume = float(performance_record["volume_handled"])
                if volume > 1000:
                    base_impact += 0.1
                
                # Bonus for profit generation
                profit = float(performance_record["profit_generated"])
                if profit > 0:
                    base_impact += 0.1
                
                # Bonus for user satisfaction
                satisfaction = performance_record["user_satisfaction"]
                if satisfaction > 0.8:
                    base_impact += 0.1
                
                performance_impact = base_impact
            else:
                # Negative impact for failed execution
                base_impact = -2.0
                
                # More severe penalty for certain error types
                error_type = performance_record.get("error_type", "")
                if error_type in ["timeout", "insufficient_funds", "slippage_exceeded"]:
                    base_impact -= 1.0
                elif error_type in ["fraud", "malicious_behavior"]:
                    base_impact -= 5.0
                
                performance_impact = base_impact
            
            # Apply reputation decay (daily)
            current_time = datetime.now()
            last_update = getattr(solver.reputation_score, 'last_updated', current_time)
            days_since_update = (current_time - last_update).days
            
            if days_since_update > 0:
                decay_factor = (1.0 - self.reputation_decay_rate) ** days_since_update
                solver.reputation_score.total_score *= decay_factor
            
            # Update reputation score
            solver.reputation_score.total_score += performance_impact
            solver.reputation_score.total_score = max(0.0, min(100.0, solver.reputation_score.total_score))
            solver.reputation_score.last_updated = current_time
            
            logger.debug(f"Updated reputation for solver {solver_address}: {solver.reputation_score.total_score}")
            
        except Exception as e:
            logger.error(f"Error updating solver reputation: {e}")
    
    async def calculate_solver_reputation_score(self, solver_address: str) -> Dict[str, float]:
        """
        Calculate comprehensive reputation score for a solver
        Requirements: 3.4 - Performance-based solver ranking
        """
        try:
            performance_history = self.solver_performance_history.get(solver_address, [])
            
            if not performance_history:
                return {
                    "overall_score": 0.0,
                    "success_rate": 0.0,
                    "average_execution_time": 0.0,
                    "reliability_score": 0.0,
                    "efficiency_score": 0.0,
                    "user_satisfaction": 0.0,
                    "volume_score": 0.0,
                    "consistency_score": 0.0
                }
            
            # Calculate success rate
            successful_tasks = sum(1 for record in performance_history if record["success"])
            success_rate = successful_tasks / len(performance_history)
            
            # Calculate average execution time
            execution_times = [record["execution_time"] for record in performance_history if record["success"]]
            avg_execution_time = np.mean(execution_times) if execution_times else 0.0
            
            # Calculate reliability score (consistency of success)
            recent_records = performance_history[-20:]  # Last 20 tasks
            recent_successes = sum(1 for record in recent_records if record["success"])
            reliability_score = recent_successes / len(recent_records) if recent_records else 0.0
            
            # Calculate efficiency score (speed and resource usage)
            if execution_times:
                # Normalize execution times (lower is better)
                max_reasonable_time = 300.0  # 5 minutes
                normalized_times = [min(1.0, time / max_reasonable_time) for time in execution_times]
                efficiency_score = 1.0 - np.mean(normalized_times)
            else:
                efficiency_score = 0.0
            
            # Calculate user satisfaction score
            satisfaction_scores = [
                record["user_satisfaction"] for record in performance_history 
                if record["user_satisfaction"] > 0
            ]
            user_satisfaction = np.mean(satisfaction_scores) if satisfaction_scores else 0.0
            
            # Calculate volume handling score
            volumes = [float(record["volume_handled"]) for record in performance_history]
            total_volume = sum(volumes)
            volume_score = min(1.0, total_volume / 10000.0)  # Normalize by 10k volume
            
            # Calculate consistency score (variance in performance)
            if len(execution_times) > 1:
                time_variance = np.var(execution_times)
                mean_time = np.mean(execution_times)
                consistency_score = 1.0 / (1.0 + time_variance / (mean_time + 1))
            else:
                consistency_score = 1.0
            
            # Calculate overall score (weighted combination)
            overall_score = (
                success_rate * 0.25 +
                reliability_score * 0.20 +
                efficiency_score * 0.15 +
                user_satisfaction * 0.15 +
                volume_score * 0.10 +
                consistency_score * 0.15
            )
            
            return {
                "overall_score": overall_score,
                "success_rate": success_rate,
                "average_execution_time": avg_execution_time,
                "reliability_score": reliability_score,
                "efficiency_score": efficiency_score,
                "user_satisfaction": user_satisfaction,
                "volume_score": volume_score,
                "consistency_score": consistency_score
            }
            
        except Exception as e:
            logger.error(f"Error calculating reputation score: {e}")
            return {"overall_score": 0.0}
    
    async def get_solver_performance_ranking(
        self,
        capability_type: Optional[CapabilityType] = None,
        min_tasks: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get performance-based ranking of solvers
        Requirements: 3.4 - Performance-based solver ranking
        """
        try:
            solver_rankings = []
            
            for solver_address in self.solver_capabilities.keys():
                # Filter by capability if specified
                if capability_type:
                    solver_capabilities = self.solver_capabilities.get(solver_address, [])
                    if not any(cap.capability_type == capability_type for cap in solver_capabilities):
                        continue
                
                # Check minimum task requirement
                performance_history = self.solver_performance_history.get(solver_address, [])
                if len(performance_history) < min_tasks:
                    continue
                
                # Calculate reputation scores
                reputation_scores = await self.calculate_solver_reputation_score(solver_address)
                
                # Get solver info
                solver = await self.solver_network_service.get_solver_by_address(solver_address)
                if not solver:
                    continue
                
                # Get health status
                health_status = self.solver_health_status.get(solver_address)
                
                ranking_entry = {
                    "solver_address": solver_address,
                    "solver_name": solver.name,
                    "tier": solver.tier.value,
                    "reputation_scores": reputation_scores,
                    "health_score": health_status.health_score if health_status else 0.0,
                    "total_tasks": len(performance_history),
                    "recent_activity": performance_history[-1]["timestamp"].isoformat() if performance_history else None,
                    "capabilities": [cap.capability_type.value for cap in self.solver_capabilities.get(solver_address, [])]
                }
                
                solver_rankings.append(ranking_entry)
            
            # Sort by overall reputation score (descending)
            solver_rankings.sort(
                key=lambda x: x["reputation_scores"]["overall_score"], 
                reverse=True
            )
            
            return solver_rankings
            
        except Exception as e:
            logger.error(f"Error getting solver performance ranking: {e}")
            return []
    
    async def implement_reputation_decay(self) -> bool:
        """
        Implement reputation decay mechanism
        Requirements: 3.4 - Reputation decay and recovery mechanisms
        """
        try:
            current_time = datetime.now()
            updated_count = 0
            
            for solver_address in self.solver_capabilities.keys():
                solver = await self.solver_network_service.get_solver_by_address(solver_address)
                if not solver:
                    continue
                
                # Check if decay is needed
                last_update = getattr(solver.reputation_score, 'last_updated', current_time)
                days_since_update = (current_time - last_update).days
                
                if days_since_update > 0:
                    # Apply exponential decay
                    decay_factor = (1.0 - self.reputation_decay_rate) ** days_since_update
                    old_score = solver.reputation_score.total_score
                    solver.reputation_score.total_score *= decay_factor
                    solver.reputation_score.last_updated = current_time
                    
                    updated_count += 1
                    logger.debug(f"Applied reputation decay to solver {solver_address}: {old_score:.2f} -> {solver.reputation_score.total_score:.2f}")
            
            if updated_count > 0:
                logger.info(f"Applied reputation decay to {updated_count} solvers")
            
            return True
            
        except Exception as e:
            logger.error(f"Error implementing reputation decay: {e}")
            return False
    
    async def detect_performance_anomalies(self, solver_address: str) -> List[Dict[str, Any]]:
        """
        Detect performance anomalies for a solver
        Requirements: 3.4 - Performance monitoring and anomaly detection
        """
        try:
            performance_history = self.solver_performance_history.get(solver_address, [])
            
            if len(performance_history) < 10:  # Need minimum history for anomaly detection
                return []
            
            anomalies = []
            
            # Calculate baseline metrics
            recent_records = performance_history[-30:]  # Last 30 tasks
            success_rates = []
            execution_times = []
            
            # Calculate rolling metrics
            window_size = 10
            for i in range(len(recent_records) - window_size + 1):
                window = recent_records[i:i + window_size]
                
                # Success rate in window
                window_successes = sum(1 for record in window if record["success"])
                window_success_rate = window_successes / len(window)
                success_rates.append(window_success_rate)
                
                # Average execution time in window
                window_times = [record["execution_time"] for record in window if record["success"]]
                if window_times:
                    execution_times.append(np.mean(window_times))
            
            # Detect success rate anomalies
            if len(success_rates) > 5:
                mean_success_rate = np.mean(success_rates[:-1])  # Exclude current window
                std_success_rate = np.std(success_rates[:-1])
                current_success_rate = success_rates[-1]
                
                if current_success_rate < mean_success_rate - 2 * std_success_rate:
                    anomalies.append({
                        "type": "low_success_rate",
                        "severity": "high",
                        "current_value": current_success_rate,
                        "expected_range": [mean_success_rate - std_success_rate, mean_success_rate + std_success_rate],
                        "description": f"Success rate dropped to {current_success_rate:.2f}, expected around {mean_success_rate:.2f}"
                    })
            
            # Detect execution time anomalies
            if len(execution_times) > 5:
                mean_execution_time = np.mean(execution_times[:-1])
                std_execution_time = np.std(execution_times[:-1])
                current_execution_time = execution_times[-1]
                
                if current_execution_time > mean_execution_time + 2 * std_execution_time:
                    anomalies.append({
                        "type": "slow_execution",
                        "severity": "medium",
                        "current_value": current_execution_time,
                        "expected_range": [mean_execution_time - std_execution_time, mean_execution_time + std_execution_time],
                        "description": f"Execution time increased to {current_execution_time:.1f}s, expected around {mean_execution_time:.1f}s"
                    })
            
            # Detect consecutive failures
            recent_failures = 0
            for record in reversed(recent_records):
                if not record["success"]:
                    recent_failures += 1
                else:
                    break
            
            if recent_failures >= 3:
                anomalies.append({
                    "type": "consecutive_failures",
                    "severity": "high",
                    "current_value": recent_failures,
                    "expected_range": [0, 1],
                    "description": f"{recent_failures} consecutive failures detected"
                })
            
            # Detect unusual error patterns
            recent_errors = [
                record.get("error_type", "") for record in recent_records[-10:]
                if not record["success"] and record.get("error_type")
            ]
            
            if recent_errors:
                error_counts = {}
                for error in recent_errors:
                    error_counts[error] = error_counts.get(error, 0) + 1
                
                for error_type, count in error_counts.items():
                    if count >= 3:  # Same error type 3+ times
                        anomalies.append({
                            "type": "recurring_error",
                            "severity": "medium",
                            "current_value": count,
                            "expected_range": [0, 1],
                            "description": f"Recurring error '{error_type}' occurred {count} times recently",
                            "error_type": error_type
                        })
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error detecting performance anomalies: {e}")
            return []
    
    async def generate_performance_report(self, solver_address: str) -> Dict[str, Any]:
        """
        Generate comprehensive performance report for a solver
        Requirements: 3.4 - Comprehensive solver performance metrics
        """
        try:
            solver = await self.solver_network_service.get_solver_by_address(solver_address)
            if not solver:
                return {"error": "Solver not found"}
            
            performance_history = self.solver_performance_history.get(solver_address, [])
            reputation_scores = await self.calculate_solver_reputation_score(solver_address)
            health_status = self.solver_health_status.get(solver_address)
            anomalies = await self.detect_performance_anomalies(solver_address)
            
            # Calculate time-based metrics
            now = datetime.now()
            last_24h = [r for r in performance_history if (now - r["timestamp"]).total_seconds() < 86400]
            last_7d = [r for r in performance_history if (now - r["timestamp"]).days < 7]
            last_30d = [r for r in performance_history if (now - r["timestamp"]).days < 30]
            
            def calculate_period_metrics(records):
                if not records:
                    return {"tasks": 0, "success_rate": 0.0, "avg_time": 0.0, "total_volume": 0.0}
                
                successful = [r for r in records if r["success"]]
                return {
                    "tasks": len(records),
                    "success_rate": len(successful) / len(records),
                    "avg_time": np.mean([r["execution_time"] for r in successful]) if successful else 0.0,
                    "total_volume": sum(float(r["volume_handled"]) for r in records)
                }
            
            report = {
                "solver_info": {
                    "address": solver_address,
                    "name": solver.name,
                    "tier": solver.tier.value,
                    "status": solver.status.value,
                    "supported_chains": solver.supported_chains,
                    "supported_tokens": solver.supported_tokens
                },
                "reputation_scores": reputation_scores,
                "health_status": {
                    "is_healthy": health_status.is_healthy if health_status else False,
                    "health_score": health_status.health_score if health_status else 0.0,
                    "last_heartbeat": health_status.last_heartbeat.isoformat() if health_status else None,
                    "response_time": health_status.response_time if health_status else 0.0,
                    "consecutive_failures": health_status.consecutive_failures if health_status else 0
                },
                "performance_metrics": {
                    "total_tasks": len(performance_history),
                    "last_24h": calculate_period_metrics(last_24h),
                    "last_7d": calculate_period_metrics(last_7d),
                    "last_30d": calculate_period_metrics(last_30d),
                    "all_time": calculate_period_metrics(performance_history)
                },
                "capabilities": [
                    {
                        "type": cap.capability_type.value,
                        "proficiency": cap.proficiency_score,
                        "success_rate": cap.success_rate,
                        "avg_execution_time": cap.average_execution_time,
                        "supported_chains": cap.supported_chains,
                        "supported_tokens": cap.supported_tokens
                    }
                    for cap in self.solver_capabilities.get(solver_address, [])
                ],
                "anomalies": anomalies,
                "recent_activity": [
                    {
                        "timestamp": record["timestamp"].isoformat(),
                        "task_id": record["task_id"],
                        "success": record["success"],
                        "execution_time": record["execution_time"],
                        "volume": float(record["volume_handled"]),
                        "error_type": record.get("error_type")
                    }
                    for record in performance_history[-10:]  # Last 10 tasks
                ],
                "report_generated": now.isoformat()
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
            return {"error": str(e)}


    # ==================== CONFLICT RESOLUTION SYSTEM ====================
    # Task 4.9: Create conflict resolution system
    # Requirements: 3.5
    
    async def detect_conflicts(self, task_id: str = None) -> List[Dict[str, Any]]:
        """
        Detect and classify conflicts in the solver network.
        
        Conflict types:
        - RESOURCE_CONFLICT: Multiple solvers competing for same resource
        - TASK_CONFLICT: Conflicting task assignments
        - CAPABILITY_CONFLICT: Overlapping capability claims
        - PRIORITY_CONFLICT: Conflicting priority assignments
        - EXECUTION_CONFLICT: Conflicting execution states
        """
        try:
            conflicts = []
            now = datetime.now()
            
            # Check for resource conflicts
            resource_usage = {}
            for solver_address, tasks in self.solver_task_assignments.items():
                for task in tasks:
                    if task_id and task.get("task_id") != task_id:
                        continue
                    
                    resources = task.get("required_resources", [])
                    for resource in resources:
                        if resource not in resource_usage:
                            resource_usage[resource] = []
                        resource_usage[resource].append({
                            "solver": solver_address,
                            "task_id": task.get("task_id"),
                            "priority": task.get("priority", 0)
                        })
            
            # Detect resource conflicts
            for resource, users in resource_usage.items():
                if len(users) > 1:
                    conflicts.append({
                        "conflict_id": f"resource_{resource}_{now.timestamp()}",
                        "type": "RESOURCE_CONFLICT",
                        "severity": "HIGH" if len(users) > 2 else "MEDIUM",
                        "resource": resource,
                        "involved_parties": users,
                        "detected_at": now,
                        "status": "DETECTED",
                        "description": f"Resource '{resource}' is being used by {len(users)} solvers"
                    })
            
            # Check for task conflicts (same task assigned to multiple solvers)
            task_assignments = {}
            for solver_address, tasks in self.solver_task_assignments.items():
                for task in tasks:
                    tid = task.get("task_id")
                    if tid:
                        if tid not in task_assignments:
                            task_assignments[tid] = []
                        task_assignments[tid].append(solver_address)
            
            for tid, solvers in task_assignments.items():
                if len(solvers) > 1:
                    conflicts.append({
                        "conflict_id": f"task_{tid}_{now.timestamp()}",
                        "type": "TASK_CONFLICT",
                        "severity": "HIGH",
                        "task_id": tid,
                        "involved_parties": [{"solver": s} for s in solvers],
                        "detected_at": now,
                        "status": "DETECTED",
                        "description": f"Task '{tid}' is assigned to {len(solvers)} solvers"
                    })
            
            # Check for capability conflicts
            capability_claims = {}
            for solver_address, capabilities in self.solver_capabilities.items():
                for cap in capabilities:
                    cap_key = f"{cap.capability_type.value}_{','.join(map(str, cap.supported_chains))}"
                    if cap_key not in capability_claims:
                        capability_claims[cap_key] = []
                    capability_claims[cap_key].append({
                        "solver": solver_address,
                        "proficiency": cap.proficiency_score,
                        "success_rate": cap.success_rate
                    })
            
            # Detect capability conflicts (overlapping claims with significant proficiency difference)
            for cap_key, claims in capability_claims.items():
                if len(claims) > 1:
                    proficiencies = [c["proficiency"] for c in claims]
                    if max(proficiencies) - min(proficiencies) > 0.3:
                        conflicts.append({
                            "conflict_id": f"capability_{cap_key}_{now.timestamp()}",
                            "type": "CAPABILITY_CONFLICT",
                            "severity": "LOW",
                            "capability": cap_key,
                            "involved_parties": claims,
                            "detected_at": now,
                            "status": "DETECTED",
                            "description": f"Significant proficiency variance for capability '{cap_key}'"
                        })
            
            # Check for priority conflicts in orchestration sessions
            for session_id, session in self.orchestration_sessions.items():
                if session.get("status") == "active":
                    solvers = session.get("selected_solvers", [])
                    priorities = [s.get("priority", 0) for s in solvers]
                    if len(set(priorities)) < len(priorities) and len(priorities) > 1:
                        conflicts.append({
                            "conflict_id": f"priority_{session_id}_{now.timestamp()}",
                            "type": "PRIORITY_CONFLICT",
                            "severity": "MEDIUM",
                            "session_id": session_id,
                            "involved_parties": solvers,
                            "detected_at": now,
                            "status": "DETECTED",
                            "description": f"Priority conflict in orchestration session '{session_id}'"
                        })
            
            # Store detected conflicts
            for conflict in conflicts:
                self.active_conflicts[conflict["conflict_id"]] = conflict
            
            logger.info(f"Detected {len(conflicts)} conflicts")
            return conflicts
            
        except Exception as e:
            logger.error(f"Error detecting conflicts: {e}")
            return []
    
    async def classify_conflict(self, conflict_id: str) -> Dict[str, Any]:
        """
        Classify a conflict and determine resolution approach.
        """
        try:
            conflict = self.active_conflicts.get(conflict_id)
            if not conflict:
                return {"error": "Conflict not found"}
            
            classification = {
                "conflict_id": conflict_id,
                "type": conflict["type"],
                "severity": conflict["severity"],
                "urgency": "IMMEDIATE" if conflict["severity"] == "HIGH" else "NORMAL",
                "resolution_approaches": [],
                "recommended_approach": None,
                "estimated_resolution_time": 0
            }
            
            # Determine resolution approaches based on conflict type
            if conflict["type"] == "RESOURCE_CONFLICT":
                classification["resolution_approaches"] = [
                    {"approach": "PRIORITY_BASED", "description": "Assign resource to highest priority task"},
                    {"approach": "TIME_SHARING", "description": "Share resource across tasks with time slots"},
                    {"approach": "ALTERNATIVE_RESOURCE", "description": "Find alternative resource for lower priority tasks"},
                    {"approach": "QUEUE_BASED", "description": "Queue tasks for sequential resource access"}
                ]
                classification["recommended_approach"] = "PRIORITY_BASED"
                classification["estimated_resolution_time"] = 5  # seconds
                
            elif conflict["type"] == "TASK_CONFLICT":
                classification["resolution_approaches"] = [
                    {"approach": "SINGLE_ASSIGNMENT", "description": "Assign task to best-suited solver"},
                    {"approach": "COLLABORATIVE", "description": "Allow multiple solvers to collaborate"},
                    {"approach": "SPLIT_TASK", "description": "Split task into subtasks for different solvers"},
                    {"approach": "CANCEL_DUPLICATES", "description": "Cancel duplicate assignments"}
                ]
                classification["recommended_approach"] = "SINGLE_ASSIGNMENT"
                classification["estimated_resolution_time"] = 3
                
            elif conflict["type"] == "CAPABILITY_CONFLICT":
                classification["resolution_approaches"] = [
                    {"approach": "BENCHMARK", "description": "Run benchmark to verify capabilities"},
                    {"approach": "HISTORICAL_PERFORMANCE", "description": "Use historical performance data"},
                    {"approach": "ACCEPT_VARIANCE", "description": "Accept variance as normal"},
                    {"approach": "RECALIBRATE", "description": "Recalibrate capability scores"}
                ]
                classification["recommended_approach"] = "HISTORICAL_PERFORMANCE"
                classification["estimated_resolution_time"] = 10
                
            elif conflict["type"] == "PRIORITY_CONFLICT":
                classification["resolution_approaches"] = [
                    {"approach": "REPUTATION_BASED", "description": "Use reputation scores to break ties"},
                    {"approach": "RANDOM", "description": "Random selection among equal priorities"},
                    {"approach": "ROUND_ROBIN", "description": "Rotate priority among solvers"},
                    {"approach": "CAPACITY_BASED", "description": "Assign based on available capacity"}
                ]
                classification["recommended_approach"] = "REPUTATION_BASED"
                classification["estimated_resolution_time"] = 2
                
            elif conflict["type"] == "EXECUTION_CONFLICT":
                classification["resolution_approaches"] = [
                    {"approach": "ROLLBACK", "description": "Rollback conflicting executions"},
                    {"approach": "MERGE", "description": "Merge execution results"},
                    {"approach": "OVERRIDE", "description": "Override with authoritative result"},
                    {"approach": "RETRY", "description": "Retry with single executor"}
                ]
                classification["recommended_approach"] = "ROLLBACK"
                classification["estimated_resolution_time"] = 15
            
            # Update conflict with classification
            conflict["classification"] = classification
            conflict["status"] = "CLASSIFIED"
            
            return classification
            
        except Exception as e:
            logger.error(f"Error classifying conflict: {e}")
            return {"error": str(e)}
    
    async def resolve_conflict(self, conflict_id: str, approach: str = None) -> Dict[str, Any]:
        """
        Resolve a conflict using the specified or recommended approach.
        """
        try:
            conflict = self.active_conflicts.get(conflict_id)
            if not conflict:
                return {"success": False, "error": "Conflict not found"}
            
            # Get classification if not already done
            if "classification" not in conflict:
                await self.classify_conflict(conflict_id)
            
            classification = conflict.get("classification", {})
            resolution_approach = approach or classification.get("recommended_approach")
            
            if not resolution_approach:
                return {"success": False, "error": "No resolution approach specified"}
            
            resolution_result = {
                "conflict_id": conflict_id,
                "approach_used": resolution_approach,
                "success": False,
                "actions_taken": [],
                "resolution_time": 0,
                "resolved_at": None
            }
            
            start_time = datetime.now()
            
            # Execute resolution based on conflict type and approach
            if conflict["type"] == "RESOURCE_CONFLICT":
                result = await self._resolve_resource_conflict(conflict, resolution_approach)
            elif conflict["type"] == "TASK_CONFLICT":
                result = await self._resolve_task_conflict(conflict, resolution_approach)
            elif conflict["type"] == "CAPABILITY_CONFLICT":
                result = await self._resolve_capability_conflict(conflict, resolution_approach)
            elif conflict["type"] == "PRIORITY_CONFLICT":
                result = await self._resolve_priority_conflict(conflict, resolution_approach)
            elif conflict["type"] == "EXECUTION_CONFLICT":
                result = await self._resolve_execution_conflict(conflict, resolution_approach)
            else:
                result = {"success": False, "actions": [], "error": "Unknown conflict type"}
            
            resolution_result["success"] = result.get("success", False)
            resolution_result["actions_taken"] = result.get("actions", [])
            resolution_result["resolution_time"] = (datetime.now() - start_time).total_seconds()
            resolution_result["resolved_at"] = datetime.now()
            
            if resolution_result["success"]:
                conflict["status"] = "RESOLVED"
                conflict["resolution"] = resolution_result
                
                # Move to resolved conflicts
                self.resolved_conflicts[conflict_id] = conflict
                del self.active_conflicts[conflict_id]
                
                logger.info(f"Conflict {conflict_id} resolved using {resolution_approach}")
            else:
                conflict["status"] = "RESOLUTION_FAILED"
                conflict["failed_resolution"] = resolution_result
                logger.warning(f"Failed to resolve conflict {conflict_id}: {result.get('error')}")
            
            return resolution_result
            
        except Exception as e:
            logger.error(f"Error resolving conflict: {e}")
            return {"success": False, "error": str(e)}
    
    async def _resolve_resource_conflict(self, conflict: Dict, approach: str) -> Dict[str, Any]:
        """Resolve resource conflicts"""
        actions = []
        
        if approach == "PRIORITY_BASED":
            # Assign resource to highest priority task
            parties = conflict.get("involved_parties", [])
            if parties:
                sorted_parties = sorted(parties, key=lambda x: x.get("priority", 0), reverse=True)
                winner = sorted_parties[0]
                losers = sorted_parties[1:]
                
                actions.append({
                    "action": "ASSIGN_RESOURCE",
                    "resource": conflict.get("resource"),
                    "assigned_to": winner["solver"],
                    "task_id": winner.get("task_id")
                })
                
                for loser in losers:
                    actions.append({
                        "action": "QUEUE_TASK",
                        "solver": loser["solver"],
                        "task_id": loser.get("task_id"),
                        "reason": "Resource assigned to higher priority task"
                    })
                
                return {"success": True, "actions": actions}
                
        elif approach == "QUEUE_BASED":
            parties = conflict.get("involved_parties", [])
            for i, party in enumerate(parties):
                actions.append({
                    "action": "QUEUE_POSITION",
                    "solver": party["solver"],
                    "task_id": party.get("task_id"),
                    "position": i + 1
                })
            return {"success": True, "actions": actions}
        
        return {"success": False, "actions": actions, "error": f"Approach {approach} not implemented"}
    
    async def _resolve_task_conflict(self, conflict: Dict, approach: str) -> Dict[str, Any]:
        """Resolve task conflicts"""
        actions = []
        
        if approach == "SINGLE_ASSIGNMENT":
            parties = conflict.get("involved_parties", [])
            task_id = conflict.get("task_id")
            
            if parties:
                # Select best solver based on reputation
                best_solver = None
                best_score = -1
                
                for party in parties:
                    solver_address = party.get("solver")
                    reputation = await self.calculate_solver_reputation_score(solver_address)
                    score = reputation.get("overall_score", 0)
                    if score > best_score:
                        best_score = score
                        best_solver = solver_address
                
                if best_solver:
                    actions.append({
                        "action": "ASSIGN_TASK",
                        "task_id": task_id,
                        "assigned_to": best_solver,
                        "reason": "Highest reputation score"
                    })
                    
                    for party in parties:
                        if party.get("solver") != best_solver:
                            actions.append({
                                "action": "UNASSIGN_TASK",
                                "task_id": task_id,
                                "solver": party.get("solver"),
                                "reason": "Task assigned to better-suited solver"
                            })
                    
                    return {"success": True, "actions": actions}
        
        elif approach == "CANCEL_DUPLICATES":
            parties = conflict.get("involved_parties", [])
            task_id = conflict.get("task_id")
            
            if parties:
                # Keep first assignment, cancel others
                keeper = parties[0]
                actions.append({
                    "action": "KEEP_ASSIGNMENT",
                    "task_id": task_id,
                    "solver": keeper.get("solver")
                })
                
                for party in parties[1:]:
                    actions.append({
                        "action": "CANCEL_ASSIGNMENT",
                        "task_id": task_id,
                        "solver": party.get("solver"),
                        "reason": "Duplicate assignment cancelled"
                    })
                
                return {"success": True, "actions": actions}
        
        return {"success": False, "actions": actions, "error": f"Approach {approach} not implemented"}
    
    async def _resolve_capability_conflict(self, conflict: Dict, approach: str) -> Dict[str, Any]:
        """Resolve capability conflicts"""
        actions = []
        
        if approach == "HISTORICAL_PERFORMANCE":
            parties = conflict.get("involved_parties", [])
            capability = conflict.get("capability")
            
            for party in parties:
                solver_address = party.get("solver")
                history = self.solver_performance_history.get(solver_address, [])
                
                if history:
                    success_rate = sum(1 for r in history if r.get("success")) / len(history)
                    actions.append({
                        "action": "UPDATE_PROFICIENCY",
                        "solver": solver_address,
                        "capability": capability,
                        "new_proficiency": success_rate,
                        "based_on": f"{len(history)} historical records"
                    })
            
            return {"success": True, "actions": actions}
        
        elif approach == "ACCEPT_VARIANCE":
            actions.append({
                "action": "ACCEPT_VARIANCE",
                "capability": conflict.get("capability"),
                "reason": "Variance within acceptable limits"
            })
            return {"success": True, "actions": actions}
        
        return {"success": False, "actions": actions, "error": f"Approach {approach} not implemented"}
    
    async def _resolve_priority_conflict(self, conflict: Dict, approach: str) -> Dict[str, Any]:
        """Resolve priority conflicts"""
        actions = []
        
        if approach == "REPUTATION_BASED":
            parties = conflict.get("involved_parties", [])
            
            # Sort by reputation
            scored_parties = []
            for party in parties:
                solver_address = party.get("solver") if isinstance(party, dict) else party
                reputation = await self.calculate_solver_reputation_score(solver_address)
                scored_parties.append({
                    "solver": solver_address,
                    "reputation": reputation.get("overall_score", 0),
                    "original_priority": party.get("priority", 0) if isinstance(party, dict) else 0
                })
            
            scored_parties.sort(key=lambda x: x["reputation"], reverse=True)
            
            for i, party in enumerate(scored_parties):
                new_priority = len(scored_parties) - i
                actions.append({
                    "action": "UPDATE_PRIORITY",
                    "solver": party["solver"],
                    "old_priority": party["original_priority"],
                    "new_priority": new_priority,
                    "based_on": f"Reputation score: {party['reputation']:.3f}"
                })
            
            return {"success": True, "actions": actions}
        
        elif approach == "CAPACITY_BASED":
            parties = conflict.get("involved_parties", [])
            
            for party in parties:
                solver_address = party.get("solver") if isinstance(party, dict) else party
                capacity = self.solver_capacity.get(solver_address, {})
                available = capacity.get("available_capacity", 0)
                
                actions.append({
                    "action": "UPDATE_PRIORITY",
                    "solver": solver_address,
                    "new_priority": int(available * 10),
                    "based_on": f"Available capacity: {available}"
                })
            
            return {"success": True, "actions": actions}
        
        return {"success": False, "actions": actions, "error": f"Approach {approach} not implemented"}
    
    async def _resolve_execution_conflict(self, conflict: Dict, approach: str) -> Dict[str, Any]:
        """Resolve execution conflicts"""
        actions = []
        
        if approach == "ROLLBACK":
            parties = conflict.get("involved_parties", [])
            
            for party in parties:
                actions.append({
                    "action": "ROLLBACK_EXECUTION",
                    "solver": party.get("solver"),
                    "task_id": party.get("task_id"),
                    "reason": "Execution conflict detected"
                })
            
            actions.append({
                "action": "SCHEDULE_RETRY",
                "task_id": conflict.get("task_id"),
                "delay_seconds": 5
            })
            
            return {"success": True, "actions": actions}
        
        elif approach == "RETRY":
            parties = conflict.get("involved_parties", [])
            
            if parties:
                # Select single executor
                best_solver = parties[0].get("solver")
                
                actions.append({
                    "action": "CANCEL_ALL_EXECUTIONS",
                    "task_id": conflict.get("task_id")
                })
                
                actions.append({
                    "action": "RETRY_WITH_SINGLE_EXECUTOR",
                    "task_id": conflict.get("task_id"),
                    "executor": best_solver
                })
                
                return {"success": True, "actions": actions}
        
        return {"success": False, "actions": actions, "error": f"Approach {approach} not implemented"}
    
    async def arbitrate_dispute(self, dispute: Dict[str, Any]) -> Dict[str, Any]:
        """
        Arbitrate a dispute between solvers.
        """
        try:
            dispute_id = f"dispute_{datetime.now().timestamp()}"
            
            arbitration = {
                "dispute_id": dispute_id,
                "parties": dispute.get("parties", []),
                "subject": dispute.get("subject"),
                "evidence": dispute.get("evidence", []),
                "status": "UNDER_REVIEW",
                "created_at": datetime.now(),
                "ruling": None
            }
            
            # Gather evidence
            evidence_scores = {}
            for party in arbitration["parties"]:
                solver_address = party.get("solver")
                
                # Get reputation
                reputation = await self.calculate_solver_reputation_score(solver_address)
                
                # Get performance history
                history = self.solver_performance_history.get(solver_address, [])
                success_rate = sum(1 for r in history if r.get("success")) / len(history) if history else 0
                
                evidence_scores[solver_address] = {
                    "reputation": reputation.get("overall_score", 0),
                    "success_rate": success_rate,
                    "history_length": len(history),
                    "claim_validity": party.get("claim_validity", 0.5)
                }
            
            # Make ruling based on evidence
            if evidence_scores:
                # Calculate weighted scores
                weighted_scores = {}
                for solver, scores in evidence_scores.items():
                    weighted_scores[solver] = (
                        scores["reputation"] * 0.4 +
                        scores["success_rate"] * 0.3 +
                        min(scores["history_length"] / 100, 1.0) * 0.1 +
                        scores["claim_validity"] * 0.2
                    )
                
                # Determine winner
                winner = max(weighted_scores, key=weighted_scores.get)
                
                arbitration["ruling"] = {
                    "decision": "FAVOR_PARTY",
                    "favored_party": winner,
                    "reasoning": "Based on reputation, performance history, and claim validity",
                    "scores": weighted_scores,
                    "ruled_at": datetime.now()
                }
                arbitration["status"] = "RULED"
            else:
                arbitration["ruling"] = {
                    "decision": "INSUFFICIENT_EVIDENCE",
                    "reasoning": "Not enough evidence to make a ruling",
                    "ruled_at": datetime.now()
                }
                arbitration["status"] = "DISMISSED"
            
            # Store arbitration
            self.dispute_arbitrations[dispute_id] = arbitration
            
            logger.info(f"Dispute {dispute_id} arbitrated: {arbitration['ruling']['decision']}")
            return arbitration
            
        except Exception as e:
            logger.error(f"Error arbitrating dispute: {e}")
            return {"error": str(e)}
    
    async def implement_early_warning_system(self) -> Dict[str, Any]:
        """
        Implement early warning system for conflict prevention.
        """
        try:
            warnings = []
            now = datetime.now()
            
            # Check for potential resource contention
            resource_demand = {}
            for solver_address, tasks in self.solver_task_assignments.items():
                for task in tasks:
                    resources = task.get("required_resources", [])
                    for resource in resources:
                        if resource not in resource_demand:
                            resource_demand[resource] = {"count": 0, "solvers": []}
                        resource_demand[resource]["count"] += 1
                        resource_demand[resource]["solvers"].append(solver_address)
            
            for resource, demand in resource_demand.items():
                if demand["count"] > 1:
                    warnings.append({
                        "warning_id": f"resource_contention_{resource}_{now.timestamp()}",
                        "type": "POTENTIAL_RESOURCE_CONFLICT",
                        "severity": "WARNING",
                        "resource": resource,
                        "demand_count": demand["count"],
                        "involved_solvers": demand["solvers"],
                        "recommendation": "Consider load balancing or resource allocation",
                        "detected_at": now
                    })
            
            # Check for capacity warnings
            for solver_address, capacity in self.solver_capacity.items():
                utilization = capacity.get("current_load", 0) / max(capacity.get("max_capacity", 1), 1)
                if utilization > 0.8:
                    warnings.append({
                        "warning_id": f"capacity_warning_{solver_address}_{now.timestamp()}",
                        "type": "HIGH_CAPACITY_UTILIZATION",
                        "severity": "WARNING" if utilization < 0.95 else "CRITICAL",
                        "solver": solver_address,
                        "utilization": utilization,
                        "recommendation": "Consider redistributing workload",
                        "detected_at": now
                    })
            
            # Check for reputation degradation
            for solver_address in self.solver_capabilities.keys():
                history = self.solver_performance_history.get(solver_address, [])
                if len(history) >= 10:
                    recent = history[-10:]
                    recent_success_rate = sum(1 for r in recent if r.get("success")) / len(recent)
                    
                    older = history[-20:-10] if len(history) >= 20 else history[:-10]
                    if older:
                        older_success_rate = sum(1 for r in older if r.get("success")) / len(older)
                        
                        if recent_success_rate < older_success_rate - 0.2:
                            warnings.append({
                                "warning_id": f"reputation_degradation_{solver_address}_{now.timestamp()}",
                                "type": "REPUTATION_DEGRADATION",
                                "severity": "WARNING",
                                "solver": solver_address,
                                "recent_success_rate": recent_success_rate,
                                "previous_success_rate": older_success_rate,
                                "recommendation": "Investigate solver performance issues",
                                "detected_at": now
                            })
            
            # Check for orchestration session conflicts
            active_sessions = [s for s in self.orchestration_sessions.values() if s.get("status") == "active"]
            if len(active_sessions) > 5:
                warnings.append({
                    "warning_id": f"session_overload_{now.timestamp()}",
                    "type": "ORCHESTRATION_OVERLOAD",
                    "severity": "WARNING",
                    "active_sessions": len(active_sessions),
                    "recommendation": "Consider completing or cancelling some sessions",
                    "detected_at": now
                })
            
            # Store warnings
            for warning in warnings:
                self.early_warnings[warning["warning_id"]] = warning
            
            logger.info(f"Early warning system detected {len(warnings)} potential issues")
            return {
                "warnings": warnings,
                "total_warnings": len(warnings),
                "critical_count": sum(1 for w in warnings if w["severity"] == "CRITICAL"),
                "warning_count": sum(1 for w in warnings if w["severity"] == "WARNING"),
                "checked_at": now
            }
            
        except Exception as e:
            logger.error(f"Error in early warning system: {e}")
            return {"error": str(e)}
    
    async def get_conflict_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about conflicts and resolutions.
        """
        try:
            now = datetime.now()
            
            # Count conflicts by type
            active_by_type = {}
            for conflict in self.active_conflicts.values():
                ctype = conflict.get("type", "UNKNOWN")
                active_by_type[ctype] = active_by_type.get(ctype, 0) + 1
            
            resolved_by_type = {}
            for conflict in self.resolved_conflicts.values():
                ctype = conflict.get("type", "UNKNOWN")
                resolved_by_type[ctype] = resolved_by_type.get(ctype, 0) + 1
            
            # Calculate resolution times
            resolution_times = []
            for conflict in self.resolved_conflicts.values():
                resolution = conflict.get("resolution", {})
                if resolution.get("resolution_time"):
                    resolution_times.append(resolution["resolution_time"])
            
            avg_resolution_time = sum(resolution_times) / len(resolution_times) if resolution_times else 0
            
            # Calculate success rate
            total_resolved = len(self.resolved_conflicts)
            successful_resolutions = sum(
                1 for c in self.resolved_conflicts.values()
                if c.get("resolution", {}).get("success", False)
            )
            success_rate = successful_resolutions / total_resolved if total_resolved > 0 else 0
            
            return {
                "active_conflicts": len(self.active_conflicts),
                "resolved_conflicts": len(self.resolved_conflicts),
                "active_by_type": active_by_type,
                "resolved_by_type": resolved_by_type,
                "resolution_success_rate": success_rate,
                "avg_resolution_time": avg_resolution_time,
                "total_warnings": len(self.early_warnings),
                "total_arbitrations": len(self.dispute_arbitrations),
                "statistics_generated_at": now.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting conflict statistics: {e}")
            return {"error": str(e)}
