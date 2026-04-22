"""
Solver Network Service for Intent Broadcasting and Management
Implements solver network communication, intent submission tracking, and status management
Enhanced with stake-based registration and reputation tracking system
"""
import asyncio
import json
import time
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
from decimal import Decimal
import logging

from src.models.solver import (
    Solver, 
    SolverStatus, 
    SolverTier,
    SolverPerformanceMetrics,
    SolverReputationScore,
    SolverStakeInfo
)

logger = logging.getLogger(__name__)


class IntentStatus(Enum):
    CREATED = "created"
    BROADCASTED = "broadcasted"
    BIDS_RECEIVED = "bids_received"
    SOLVER_SELECTED = "solver_selected"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


@dataclass
class SolverBid:
    """Solver bid for intent fulfillment"""
    solver_address: str
    intent_hash: str
    output_amount: str
    execution_time_estimate: int  # seconds
    gas_fee_estimate: str
    solver_fee: str
    total_cost: str
    bid_timestamp: datetime
    expiry_timestamp: datetime
    signature: str


@dataclass
class IntentBroadcast:
    """Intent broadcast information"""
    intent_hash: str
    intent_data: Dict
    broadcast_timestamp: datetime
    target_solvers: List[str]
    broadcast_channels: List[str]
    status: IntentStatus
    bids_received: List[SolverBid]
    selected_solver: Optional[str]
    selection_timestamp: Optional[datetime]
    execution_deadline: datetime


class SolverNetworkService:
    def __init__(self):
        # Enhanced storage using new Solver model
        self.registered_solvers: Dict[str, Solver] = {}
        self.active_intents: Dict[str, IntentBroadcast] = {}
        self.intent_history: Dict[str, IntentBroadcast] = {}
        self.solver_bids: Dict[str, List[SolverBid]] = {}
        
        # Staking configuration
        self.minimum_stake_amount = Decimal('10')  # 10 ETH equivalent minimum stake
        self.stake_token_address = "0x0000000000000000000000000000000000000000"  # ETH
        self.slashing_amounts = {
            "minor_violation": Decimal('0.1'),  # 0.1 ETH
            "major_violation": Decimal('1.0'),  # 1 ETH
            "malicious_behavior": Decimal('5.0')  # 5 ETH
        }
        
        # Reputation thresholds
        self.min_reputation_score = 0.7
        self.reputation_decay_rate = 0.01  # Daily decay for inactive solvers
        
        # Configuration
        self.bid_timeout = 30  # seconds
        self.execution_timeout = 1800  # 30 minutes
        self.max_concurrent_intents_per_solver = 10
        
        # WebSocket connections for real-time communication
        self.solver_connections: Dict[str, object] = {}
        self.user_connections: Dict[str, object] = {}
        
        # Background tasks
        self._cleanup_task = None
        self._monitoring_task = None
        self._reputation_update_task = None
        self._failure_detection_task = None
    
    async def start_background_tasks(self):
        """Start background monitoring and cleanup tasks"""
        self._cleanup_task = asyncio.create_task(self._cleanup_expired_intents())
        self._monitoring_task = asyncio.create_task(self._monitor_solver_health())
        self._reputation_update_task = asyncio.create_task(self._update_reputation_scores())
        self._failure_detection_task = asyncio.create_task(self._monitor_solver_failures())
    
    async def stop_background_tasks(self):
        """Stop background tasks"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
        if self._monitoring_task:
            self._monitoring_task.cancel()
        if self._reputation_update_task:
            self._reputation_update_task.cancel()
        if self._failure_detection_task:
            self._failure_detection_task.cancel()
    
    # Solver Registration and Management with Stake-Based System
    
    async def register_solver_with_stake(
        self, 
        address: str, 
        name: str, 
        endpoint: str,
        supported_chains: List[int],
        supported_tokens: List[str],
        stake_amount: Decimal,
        stake_token: str = None
    ) -> bool:
        """
        Register a new solver with stake-based registration
        Requirements: 4.5 - Stake-based solver registration
        """
        try:
            # Validate minimum stake requirement
            if stake_amount < self.minimum_stake_amount:
                logger.error(f"Insufficient stake amount: {stake_amount} < {self.minimum_stake_amount}")
                return False
            
            # Check if solver is already registered
            if address in self.registered_solvers:
                logger.warning(f"Solver {address} already registered")
                return False
            
            # Create new solver with stake
            solver = Solver(
                address=address,
                name=name,
                endpoint=endpoint,
                supported_chains=supported_chains,
                supported_tokens=supported_tokens,
                status=SolverStatus.INACTIVE  # Start inactive until stake is confirmed
            )
            
            # Register stake
            stake_token_addr = stake_token or self.stake_token_address
            registration_success = solver.register_with_stake(
                stake_amount=stake_amount,
                stake_token=stake_token_addr,
                minimum_stake_required=self.minimum_stake_amount
            )
            
            if not registration_success:
                logger.error(f"Failed to register stake for solver {address}")
                return False
            
            # Store solver
            self.registered_solvers[address] = solver
            
            logger.info(f"Solver {name} ({address}) registered with stake {stake_amount}")
            return True
            
        except Exception as e:
            logger.error(f"Error registering solver {address}: {e}")
            return False
    
    async def update_solver_reputation(
        self, 
        solver_address: str, 
        intent_completed: bool = False,
        intent_failed: bool = False,
        execution_time: Optional[float] = None,
        slippage: Optional[float] = None,
        volume_processed: Optional[Decimal] = None
    ) -> bool:
        """
        Update solver reputation based on performance
        Requirements: 4.5 - Reputation scoring and tracking
        """
        if solver_address not in self.registered_solvers:
            return False
        
        solver = self.registered_solvers[solver_address]
        
        # Update performance metrics which automatically updates reputation
        solver.update_performance_metrics(
            intent_completed=intent_completed,
            intent_failed=intent_failed,
            execution_time=execution_time,
            slippage=slippage,
            volume_processed=volume_processed
        )
        
        logger.info(f"Updated reputation for solver {solver_address}: {solver.reputation_score.total_score}")
        return True
    
    async def slash_solver(
        self, 
        solver_address: str, 
        violation_type: str = "minor_violation"
    ) -> bool:
        """
        Slash solver stake for violations
        Requirements: 4.5 - Solver performance metrics and slashing
        """
        if solver_address not in self.registered_solvers:
            return False
        
        solver = self.registered_solvers[solver_address]
        slash_amount = self.slashing_amounts.get(violation_type, Decimal('0.1'))
        
        # Apply slashing
        penalty_amount = 0.1 if violation_type == "minor_violation" else 0.3
        success = solver.slash_for_malicious_behavior(slash_amount, penalty_amount)
        
        if success:
            logger.warning(f"Slashed solver {solver_address} for {violation_type}: {slash_amount} ETH")
        
        return success
    
    async def get_solver_by_address(self, address: str) -> Optional[Solver]:
        """Get solver by address"""
        return self.registered_solvers.get(address)
    
    async def get_solvers_by_tier(self, tier: SolverTier) -> List[Solver]:
        """Get all solvers of a specific tier"""
        return [
            solver for solver in self.registered_solvers.values()
            if solver.tier == tier and solver.status == SolverStatus.ACTIVE
        ]
    
    async def get_top_solvers(self, limit: int = 10) -> List[Solver]:
        """Get top solvers by reputation score"""
        active_solvers = [
            solver for solver in self.registered_solvers.values()
            if solver.status == SolverStatus.ACTIVE
        ]
        
        # Sort by reputation score descending
        active_solvers.sort(key=lambda s: s.reputation_score.total_score, reverse=True)
        return active_solvers[:limit]
    
    async def get_active_solvers(self, chain_id: Optional[int] = None) -> List[Solver]:
        """Get list of active solvers, optionally filtered by chain"""
        active_solvers = []
        
        for solver in self.registered_solvers.values():
            if not solver.is_eligible_for_intents:
                continue
            
            if chain_id and chain_id not in solver.supported_chains:
                continue
            
            active_solvers.append(solver)
        
        # Sort by reputation score (descending)
        active_solvers.sort(key=lambda s: s.reputation_score.total_score, reverse=True)
        return active_solvers
    
    # Intent Broadcasting
    
    async def broadcast_intent(
        self, 
        intent_hash: str, 
        intent_data: Dict,
        target_chains: List[int]
    ) -> bool:
        """
        Broadcast intent to solver network
        Requirements: 1.4, 4.1
        """
        try:
            # Get eligible solvers for the intent
            eligible_solvers = await self._get_eligible_solvers(intent_data, target_chains)
            
            if not eligible_solvers:
                logger.warning(f"No eligible solvers found for intent {intent_hash}")
                return False
            
            # Create broadcast record
            broadcast = IntentBroadcast(
                intent_hash=intent_hash,
                intent_data=intent_data,
                broadcast_timestamp=datetime.now(),
                target_solvers=[s.address for s in eligible_solvers],
                broadcast_channels=["websocket", "http"],
                status=IntentStatus.BROADCASTED,
                bids_received=[],
                selected_solver=None,
                selection_timestamp=None,
                execution_deadline=datetime.now() + timedelta(seconds=self.execution_timeout)
            )
            
            self.active_intents[intent_hash] = broadcast
            
            # Broadcast to solvers via multiple channels
            broadcast_tasks = []
            
            # WebSocket broadcast
            for solver in eligible_solvers:
                if solver.address in self.solver_connections:
                    task = asyncio.create_task(
                        self._send_websocket_broadcast(solver.address, intent_data)
                    )
                    broadcast_tasks.append(task)
            
            # HTTP broadcast as fallback
            for solver in eligible_solvers:
                task = asyncio.create_task(
                    self._send_http_broadcast(solver.endpoint, intent_data)
                )
                broadcast_tasks.append(task)
            
            # Execute broadcasts concurrently
            results = await asyncio.gather(*broadcast_tasks, return_exceptions=True)
            
            successful_broadcasts = sum(1 for r in results if r is True)
            logger.info(f"Intent {intent_hash} broadcast to {successful_broadcasts}/{len(broadcast_tasks)} channels")
            
            # Start bid collection timer
            asyncio.create_task(self._collect_bids_with_timeout(intent_hash))
            
            return successful_broadcasts > 0
            
        except Exception as e:
            logger.error(f"Error broadcasting intent {intent_hash}: {e}")
            return False
    
    async def submit_solver_bid(
        self, 
        solver_address: str, 
        intent_hash: str,
        output_amount: str,
        execution_time_estimate: int,
        gas_fee_estimate: str,
        solver_fee: str,
        signature: str
    ) -> bool:
        """
        Submit a solver bid for an intent with enhanced validation
        Requirements: 4.2 - Competitive bidding system
        """
        try:
            # Validate solver is registered and eligible
            if solver_address not in self.registered_solvers:
                logger.error(f"Solver {solver_address} not registered")
                return False
            
            solver = self.registered_solvers[solver_address]
            if not solver.is_eligible_for_intents:
                logger.error(f"Solver {solver_address} not eligible for intents")
                return False
            
            # Validate intent exists and is accepting bids
            if intent_hash not in self.active_intents:
                logger.error(f"Intent {intent_hash} not found or not active")
                return False
            
            broadcast = self.active_intents[intent_hash]
            if broadcast.status not in [IntentStatus.BROADCASTED, IntentStatus.BIDS_RECEIVED]:
                logger.error(f"Intent {intent_hash} not accepting bids (status: {broadcast.status})")
                return False
            
            # Check if solver is eligible for this intent
            if solver_address not in broadcast.target_solvers:
                logger.error(f"Solver {solver_address} not eligible for intent {intent_hash}")
                return False
            
            # Check if solver already submitted a bid (prevent duplicate bids)
            existing_bid = next(
                (bid for bid in broadcast.bids_received if bid.solver_address == solver_address),
                None
            )
            if existing_bid:
                logger.warning(f"Solver {solver_address} already submitted bid for intent {intent_hash}")
                return False
            
            # Calculate total cost
            total_cost = str(Decimal(gas_fee_estimate) + Decimal(solver_fee))
            
            # Create bid
            bid = SolverBid(
                solver_address=solver_address,
                intent_hash=intent_hash,
                output_amount=output_amount,
                execution_time_estimate=execution_time_estimate,
                gas_fee_estimate=gas_fee_estimate,
                solver_fee=solver_fee,
                total_cost=total_cost,
                bid_timestamp=datetime.now(),
                expiry_timestamp=datetime.now() + timedelta(seconds=self.bid_timeout),
                signature=signature
            )
            
            # Validate bid signature
            if not await self._validate_bid_signature(bid):
                logger.error(f"Invalid bid signature from solver {solver_address}")
                return False
            
            # Validate bid meets minimum requirements
            if not await self._validate_bid_requirements(bid, broadcast.intent_data):
                logger.error(f"Bid from solver {solver_address} does not meet requirements")
                return False
            
            # Add bid to broadcast
            broadcast.bids_received.append(bid)
            broadcast.status = IntentStatus.BIDS_RECEIVED
            
            # Initialize solver bids list if needed
            if intent_hash not in self.solver_bids:
                self.solver_bids[intent_hash] = []
            
            self.solver_bids[intent_hash].append(bid)
            
            # Update solver performance metrics
            solver.update_performance_metrics(bid_submitted=True)
            
            logger.info(f"Bid received from solver {solver_address} for intent {intent_hash}")
            
            # Notify users of new bid via WebSocket
            await self._notify_users_of_bid(intent_hash, bid)
            
            # Check if we should auto-select best bid (if bid timeout reached)
            await self._check_auto_bid_selection(intent_hash)
            
            return True
            
        except Exception as e:
            logger.error(f"Error submitting bid from solver {solver_address}: {e}")
            return False
    
    async def select_best_solver(self, intent_hash: str) -> Optional[str]:
        """
        Select the best solver bid for an intent using enhanced scoring algorithm
        Requirements: 4.2 - Best bid selection algorithm
        """
        try:
            if intent_hash not in self.active_intents:
                return None
            
            broadcast = self.active_intents[intent_hash]
            
            if not broadcast.bids_received:
                logger.warning(f"No bids received for intent {intent_hash}")
                return None
            
            # Filter valid bids (not expired, from eligible solvers)
            valid_bids = []
            current_time = datetime.now()
            
            for bid in broadcast.bids_received:
                # Check if bid is still valid (not expired)
                if current_time > bid.expiry_timestamp:
                    logger.debug(f"Bid from {bid.solver_address} expired")
                    continue
                
                # Check if solver is still eligible
                solver = self.registered_solvers.get(bid.solver_address)
                if not solver or not solver.is_eligible_for_intents:
                    logger.debug(f"Solver {bid.solver_address} no longer eligible")
                    continue
                
                valid_bids.append(bid)
            
            if not valid_bids:
                logger.warning(f"No valid bids for intent {intent_hash}")
                return None
            
            # Score and rank bids using enhanced algorithm
            scored_bids = []
            
            for bid in valid_bids:
                solver = self.registered_solvers[bid.solver_address]
                
                # Calculate comprehensive bid score
                score = await self._calculate_enhanced_bid_score(bid, solver, broadcast.intent_data)
                scored_bids.append((score, bid, solver))
            
            if not scored_bids:
                return None
            
            # Sort by score (descending) and select best bid
            scored_bids.sort(key=lambda x: x[0], reverse=True)
            best_score, best_bid, best_solver = scored_bids[0]
            
            # Grant exclusive fulfillment rights
            success = await self._grant_exclusive_fulfillment_rights(
                intent_hash, 
                best_bid.solver_address, 
                best_bid
            )
            
            if not success:
                logger.error(f"Failed to grant exclusive rights to solver {best_bid.solver_address}")
                return None
            
            # Update broadcast with selected solver
            broadcast.selected_solver = best_bid.solver_address
            broadcast.selection_timestamp = datetime.now()
            broadcast.status = IntentStatus.SOLVER_SELECTED
            
            # Update solver performance metrics
            best_solver.update_performance_metrics(intent_won=True)
            
            logger.info(f"Selected solver {best_bid.solver_address} for intent {intent_hash} (score: {best_score:.3f})")
            
            # Notify selected solver
            await self._notify_solver_selection(best_bid.solver_address, intent_hash, True, best_bid)
            
            # Notify other solvers they were not selected
            for _, bid, _ in scored_bids[1:]:
                await self._notify_solver_selection(bid.solver_address, intent_hash, False, None)
            
            return best_bid.solver_address
            
        except Exception as e:
            logger.error(f"Error selecting solver for intent {intent_hash}: {e}")
            return None
    
    async def _calculate_enhanced_bid_score(self, bid: SolverBid, solver: Solver, intent_data: Dict) -> float:
        """
        Enhanced bid scoring algorithm considering multiple factors
        Requirements: 4.2 - Best bid selection algorithm
        """
        # Base scoring factors
        min_output = float(intent_data.get("minimumOutputAmount", "1"))
        bid_output = float(bid.output_amount)
        
        # 1. Output amount score (higher output is better)
        output_score = min(2.0, bid_output / min_output) if min_output > 0 else 1.0
        
        # 2. Execution time score (faster is better)
        max_acceptable_time = 1800  # 30 minutes
        time_score = max(0.1, 1.0 - (bid.execution_time_estimate / max_acceptable_time))
        
        # 3. Cost efficiency score (lower total cost is better)
        total_cost = float(bid.total_cost)
        # Normalize cost relative to output value
        cost_efficiency = max(0.1, 1.0 - (total_cost / bid_output)) if bid_output > 0 else 0.1
        
        # 4. Solver reputation score
        reputation_score = solver.reputation_score.total_score / 2.0  # Normalize to 0-1
        
        # 5. Solver tier bonus
        tier_multipliers = {
            SolverTier.BRONZE: 1.0,
            SolverTier.SILVER: 1.1,
            SolverTier.GOLD: 1.2,
            SolverTier.PLATINUM: 1.3
        }
        tier_multiplier = tier_multipliers.get(solver.tier, 1.0)
        
        # 6. Historical performance bonus
        performance_bonus = 1.0
        if solver.performance_metrics.total_intents_completed > 10:
            completion_rate = solver.performance_metrics.completion_rate / 100
            performance_bonus = 1.0 + (completion_rate - 0.8) * 0.5  # Bonus for >80% completion rate
        
        # 7. Stake-based confidence score
        stake_confidence = 1.0
        if solver.stake_info:
            stake_ratio = float(solver.stake_info.effective_stake) / float(self.minimum_stake_amount)
            stake_confidence = min(1.5, 1.0 + (stake_ratio - 1.0) * 0.1)  # Bonus for higher stake
        
        # 8. Availability score (lower concurrent load is better)
        availability_score = 1.0 - (solver.current_concurrent_intents / solver.max_concurrent_intents)
        
        # Weighted combination of all factors
        total_score = (
            output_score * 0.25 +           # 25% - Output amount
            time_score * 0.20 +             # 20% - Execution time
            cost_efficiency * 0.15 +        # 15% - Cost efficiency
            reputation_score * 0.15 +       # 15% - Reputation
            availability_score * 0.10 +     # 10% - Availability
            performance_bonus * 0.10 +      # 10% - Historical performance
            stake_confidence * 0.05         # 5% - Stake confidence
        ) * tier_multiplier
        
        return total_score
    
    async def _grant_exclusive_fulfillment_rights(
        self, 
        intent_hash: str, 
        solver_address: str, 
        winning_bid: SolverBid
    ) -> bool:
        """
        Grant exclusive fulfillment rights to the winning solver
        Requirements: 4.3 - Exclusive fulfillment rights management
        """
        try:
            broadcast = self.active_intents[intent_hash]
            solver = self.registered_solvers[solver_address]
            
            # Set exclusive fulfillment period (default 15 minutes)
            exclusive_period = timedelta(minutes=15)
            exclusive_deadline = datetime.now() + exclusive_period
            
            # Store exclusive rights information
            exclusive_rights = {
                "solver_address": solver_address,
                "intent_hash": intent_hash,
                "winning_bid": winning_bid,
                "granted_at": datetime.now(),
                "expires_at": exclusive_deadline,
                "status": "active"
            }
            
            # Add to broadcast metadata
            if not hasattr(broadcast, 'exclusive_rights'):
                broadcast.exclusive_rights = {}
            broadcast.exclusive_rights = exclusive_rights
            
            # Schedule automatic fallback if solver doesn't fulfill in time
            asyncio.create_task(
                self._monitor_exclusive_fulfillment(intent_hash, exclusive_deadline)
            )
            
            logger.info(f"Granted exclusive rights to solver {solver_address} for intent {intent_hash} until {exclusive_deadline}")
            return True
            
        except Exception as e:
            logger.error(f"Error granting exclusive rights: {e}")
            return False
    
    async def _monitor_exclusive_fulfillment(self, intent_hash: str, deadline: datetime):
        """
        Monitor exclusive fulfillment period and trigger fallback if needed
        Requirements: 4.3 - Exclusive fulfillment rights management
        """
        try:
            # Wait until deadline
            wait_time = (deadline - datetime.now()).total_seconds()
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            
            # Check if intent is still pending
            if intent_hash in self.active_intents:
                broadcast = self.active_intents[intent_hash]
                
                if broadcast.status == IntentStatus.SOLVER_SELECTED:
                    # Solver failed to fulfill in time, trigger fallback
                    logger.warning(f"Solver failed to fulfill intent {intent_hash} in time, triggering fallback")
                    await self._trigger_solver_fallback(intent_hash)
                    
        except Exception as e:
            logger.error(f"Error monitoring exclusive fulfillment for {intent_hash}: {e}")
    
    async def _validate_bid_requirements(self, bid: SolverBid, intent_data: Dict) -> bool:
        """
        Validate that bid meets minimum requirements
        Requirements: 4.2 - Bid submission and validation
        """
        try:
            # Check minimum output amount
            min_output = Decimal(intent_data.get("minimumOutputAmount", "0"))
            bid_output = Decimal(bid.output_amount)
            
            if bid_output < min_output:
                logger.debug(f"Bid output {bid_output} below minimum {min_output}")
                return False
            
            # Check maximum execution time (30 minutes)
            if bid.execution_time_estimate > 1800:
                logger.debug(f"Bid execution time {bid.execution_time_estimate}s exceeds maximum")
                return False
            
            # Check reasonable gas fee estimate
            gas_fee = Decimal(bid.gas_fee_estimate)
            if gas_fee <= 0:
                logger.debug(f"Invalid gas fee estimate: {gas_fee}")
                return False
            
            # Check solver fee is reasonable (not more than 1% of output)
            solver_fee = Decimal(bid.solver_fee)
            max_solver_fee = bid_output * Decimal('0.01')  # 1% max
            
            if solver_fee > max_solver_fee:
                logger.debug(f"Solver fee {solver_fee} exceeds maximum {max_solver_fee}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating bid requirements: {e}")
            return False
    
    async def _check_auto_bid_selection(self, intent_hash: str):
        """
        Check if we should automatically select the best bid
        Requirements: 4.2 - Competitive bidding system
        """
        try:
            broadcast = self.active_intents[intent_hash]
            
            # Auto-select if we have received bids from majority of target solvers
            if len(broadcast.bids_received) >= len(broadcast.target_solvers) * 0.7:
                logger.info(f"Auto-selecting best bid for intent {intent_hash} (received {len(broadcast.bids_received)}/{len(broadcast.target_solvers)} bids)")
                await self.select_best_solver(intent_hash)
                
        except Exception as e:
            logger.error(f"Error in auto bid selection for {intent_hash}: {e}")
    
    # Intent Status Management
    
    async def update_intent_status(self, intent_hash: str, status: IntentStatus) -> bool:
        """Update intent status and notify stakeholders"""
        try:
            if intent_hash not in self.active_intents:
                return False
            
            broadcast = self.active_intents[intent_hash]
            old_status = broadcast.status
            broadcast.status = status
            
            logger.info(f"Intent {intent_hash} status updated: {old_status.value} -> {status.value}")
            
            # Handle status-specific logic
            if status == IntentStatus.COMPLETED:
                await self._handle_intent_completion(intent_hash)
            elif status == IntentStatus.FAILED:
                await self._handle_intent_failure(intent_hash)
            elif status == IntentStatus.EXPIRED:
                await self._handle_intent_expiry(intent_hash)
            
            # Notify users via WebSocket
            await self._notify_users_of_status_change(intent_hash, status)
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating intent status {intent_hash}: {e}")
            return False
    
    async def get_intent_status(self, intent_hash: str) -> Optional[Dict]:
        """Get current intent status and details"""
        if intent_hash in self.active_intents:
            broadcast = self.active_intents[intent_hash]
        elif intent_hash in self.intent_history:
            broadcast = self.intent_history[intent_hash]
        else:
            return None
        
        return {
            "intent_hash": intent_hash,
            "status": broadcast.status.value,
            "broadcast_timestamp": broadcast.broadcast_timestamp.isoformat(),
            "target_solvers": broadcast.target_solvers,
            "bids_count": len(broadcast.bids_received),
            "selected_solver": broadcast.selected_solver,
            "selection_timestamp": broadcast.selection_timestamp.isoformat() if broadcast.selection_timestamp else None,
            "execution_deadline": broadcast.execution_deadline.isoformat()
        }
    
    async def get_solver_statistics(self, solver_address: str) -> Optional[Dict]:
        """Get solver performance statistics"""
        if solver_address not in self.registered_solvers:
            return None
        
        solver = self.registered_solvers[solver_address]
        
        return {
            "address": solver.address,
            "name": solver.name,
            "status": solver.status.value,
            "tier": solver.tier.value,
            "reputation_score": solver.reputation_score.total_score,
            "performance_metrics": {
                "total_intents_received": solver.performance_metrics.total_intents_received,
                "total_bids_submitted": solver.performance_metrics.total_bids_submitted,
                "total_intents_won": solver.performance_metrics.total_intents_won,
                "total_intents_completed": solver.performance_metrics.total_intents_completed,
                "total_intents_failed": solver.performance_metrics.total_intents_failed,
                "bid_win_rate": solver.performance_metrics.bid_win_rate,
                "completion_rate": solver.performance_metrics.completion_rate,
                "failure_rate": solver.performance_metrics.failure_rate,
                "average_execution_time": solver.performance_metrics.average_execution_time,
                "total_volume_processed": str(solver.performance_metrics.total_volume_processed),
            },
            "stake_info": {
                "stake_amount": str(solver.stake_info.stake_amount) if solver.stake_info else "0",
                "effective_stake": str(solver.stake_info.effective_stake) if solver.stake_info else "0",
                "is_sufficient": solver.stake_info.is_sufficient if solver.stake_info else False,
                "slashed_amount": str(solver.stake_info.slashed_amount) if solver.stake_info else "0",
            } if solver.stake_info else None,
            "supported_chains": solver.supported_chains,
            "last_seen": solver.last_seen.isoformat(),
            "registration_time": solver.registration_timestamp.isoformat(),
            "is_eligible_for_intents": solver.is_eligible_for_intents,
        }
    
    # Private Helper Methods
    
    def _validate_solver_address(self, address: str) -> bool:
        """Validate solver Ethereum address format"""
        return len(address) == 42 and address.startswith('0x')
    
    async def _validate_solver_endpoint(self, endpoint: str) -> bool:
        """Validate solver endpoint is reachable"""
        # In production, would make HTTP health check
        return endpoint.startswith(('http://', 'https://'))
    
    async def _get_eligible_solvers(self, intent_data: Dict, target_chains: List[int]) -> List[Solver]:
        """Get solvers eligible for the given intent"""
        eligible_solvers = []
        
        for solver in self.registered_solvers.values():
            if not solver.is_eligible_for_intents:
                continue
            
            # Check chain support
            if not any(chain in solver.supported_chains for chain in target_chains):
                continue
            
            eligible_solvers.append(solver)
        
        return eligible_solvers
    
    async def _send_websocket_broadcast(self, solver_address: str, intent_data: Dict) -> bool:
        """Send intent broadcast via WebSocket"""
        try:
            if solver_address not in self.solver_connections:
                return False
            
            connection = self.solver_connections[solver_address]
            message = {
                "type": "intent_broadcast",
                "data": intent_data,
                "timestamp": datetime.now().isoformat()
            }
            
            # In production, would use actual WebSocket send
            # await connection.send(json.dumps(message))
            logger.debug(f"WebSocket broadcast sent to solver {solver_address}")
            return True
            
        except Exception as e:
            logger.error(f"WebSocket broadcast failed for solver {solver_address}: {e}")
            return False
    
    async def _send_http_broadcast(self, endpoint: str, intent_data: Dict) -> bool:
        """Send intent broadcast via HTTP"""
        try:
            # In production, would make actual HTTP POST request
            # async with aiohttp.ClientSession() as session:
            #     async with session.post(f"{endpoint}/intent", json=intent_data) as response:
            #         return response.status == 200
            
            logger.debug(f"HTTP broadcast sent to endpoint {endpoint}")
            return True
            
        except Exception as e:
            logger.error(f"HTTP broadcast failed for endpoint {endpoint}: {e}")
            return False
    
    async def _collect_bids_with_timeout(self, intent_hash: str):
        """Collect bids for an intent with timeout"""
        await asyncio.sleep(self.bid_timeout)
        
        if intent_hash in self.active_intents:
            broadcast = self.active_intents[intent_hash]
            
            if broadcast.status == IntentStatus.BIDS_RECEIVED:
                # Automatically select best solver after timeout
                await self.select_best_solver(intent_hash)
            elif broadcast.status == IntentStatus.BROADCASTED:
                # No bids received, mark as failed
                await self.update_intent_status(intent_hash, IntentStatus.FAILED)
    
    async def _trigger_solver_fallback(self, intent_hash: str) -> bool:
        """
        Trigger fallback to next best solver when current solver fails
        Requirements: 4.4 - Automatic fallback to next best bid
        """
        try:
            if intent_hash not in self.active_intents:
                return False
            
            broadcast = self.active_intents[intent_hash]
            failed_solver = broadcast.selected_solver
            
            if not failed_solver:
                return False
            
            logger.warning(f"Triggering fallback for intent {intent_hash}, failed solver: {failed_solver}")
            
            # Update failed solver's reputation and concurrent intents
            await self.update_solver_reputation(failed_solver, intent_failed=True)
            
            # Decrease concurrent intents for failed solver
            if failed_solver in self.registered_solvers:
                failed_solver_obj = self.registered_solvers[failed_solver]
                failed_solver_obj.current_concurrent_intents = max(
                    0, failed_solver_obj.current_concurrent_intents - 1
                )
            
            # Remove failed solver from eligible bids
            remaining_bids = [
                bid for bid in broadcast.bids_received 
                if bid.solver_address != failed_solver
            ]
            
            if not remaining_bids:
                logger.error(f"No fallback solvers available for intent {intent_hash}")
                await self.update_intent_status(intent_hash, IntentStatus.FAILED)
                return False
            
            # Reset broadcast state for re-selection
            broadcast.bids_received = remaining_bids
            broadcast.selected_solver = None
            broadcast.selection_timestamp = None
            broadcast.status = IntentStatus.BIDS_RECEIVED
            
            # Clear exclusive rights
            if hasattr(broadcast, 'exclusive_rights'):
                broadcast.exclusive_rights = None
            
            # Select next best solver
            next_solver = await self.select_best_solver(intent_hash)
            
            if next_solver:
                logger.info(f"Fallback successful: selected solver {next_solver} for intent {intent_hash}")
                
                # Notify about fallback
                await self._notify_fallback_event(intent_hash, failed_solver, next_solver)
                return True
            else:
                logger.error(f"Fallback failed: no suitable solver found for intent {intent_hash}")
                await self.update_intent_status(intent_hash, IntentStatus.FAILED)
                return False
                
        except Exception as e:
            logger.error(f"Error in solver fallback for intent {intent_hash}: {e}")
            return False
    
    async def detect_solver_failure(self, intent_hash: str) -> bool:
        """
        Detect solver failure based on timeout and other indicators
        Requirements: 4.4 - Solver failure detection and handling
        """
        try:
            if intent_hash not in self.active_intents:
                return False
            
            broadcast = self.active_intents[intent_hash]
            
            if broadcast.status != IntentStatus.SOLVER_SELECTED:
                return False
            
            if not broadcast.selected_solver or not broadcast.selection_timestamp:
                return False
            
            # Check if solver has exceeded execution timeout
            current_time = datetime.now()
            execution_timeout = timedelta(minutes=30)  # 30 minutes default
            
            if current_time - broadcast.selection_timestamp > execution_timeout:
                logger.warning(f"Solver {broadcast.selected_solver} timed out for intent {intent_hash}")
                return True
            
            # Check if solver is still active and eligible
            solver = self.registered_solvers.get(broadcast.selected_solver)
            if not solver or not solver.is_eligible_for_intents:
                logger.warning(f"Solver {broadcast.selected_solver} no longer eligible for intent {intent_hash}")
                return True
            
            # Check exclusive rights expiration
            if hasattr(broadcast, 'exclusive_rights') and broadcast.exclusive_rights:
                expires_at = broadcast.exclusive_rights.get('expires_at')
                if expires_at and current_time > expires_at:
                    logger.warning(f"Exclusive rights expired for solver {broadcast.selected_solver} on intent {intent_hash}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error detecting solver failure for intent {intent_hash}: {e}")
            return False
    
    async def report_solver_failure(self, intent_hash: str, solver_address: str, failure_reason: str) -> bool:
        """
        Report solver failure and trigger fallback with appropriate penalties
        Requirements: 4.4 - Solver failure detection and handling
        """
        try:
            if intent_hash not in self.active_intents:
                return False
            
            broadcast = self.active_intents[intent_hash]
            
            if broadcast.selected_solver != solver_address:
                logger.warning(f"Solver {solver_address} not selected for intent {intent_hash}")
                return False
            
            logger.warning(f"Solver failure reported: {solver_address} for intent {intent_hash}, reason: {failure_reason}")
            
            # Apply penalty based on failure reason
            penalty_applied = False
            
            if failure_reason in ["malicious_behavior", "fraud", "invalid_execution"]:
                penalty_applied = await self.slash_solver(solver_address, "malicious_behavior")
                logger.warning(f"Applied malicious behavior penalty to solver {solver_address}")
                
            elif failure_reason in ["timeout", "execution_failure", "insufficient_funds"]:
                penalty_applied = await self.slash_solver(solver_address, "major_violation")
                logger.info(f"Applied major violation penalty to solver {solver_address}")
                
            elif failure_reason in ["network_error", "temporary_unavailability"]:
                penalty_applied = await self.slash_solver(solver_address, "minor_violation")
                logger.info(f"Applied minor violation penalty to solver {solver_address}")
            
            # Record failure in solver's performance metrics
            await self.update_solver_reputation(
                solver_address, 
                intent_failed=True,
                execution_time=1800.0  # Mark as slow execution
            )
            
            # Trigger fallback
            fallback_success = await self._trigger_solver_fallback(intent_hash)
            
            # Log the incident for monitoring
            await self._log_solver_incident(intent_hash, solver_address, failure_reason, penalty_applied, fallback_success)
            
            return fallback_success
            
        except Exception as e:
            logger.error(f"Error reporting solver failure: {e}")
            return False
    
    async def implement_solver_slashing(self, solver_address: str, violation_type: str, custom_amount: Optional[Decimal] = None) -> bool:
        """
        Implement solver slashing for malicious behavior with enhanced logic
        Requirements: 4.4 - Solver slashing for malicious behavior
        """
        try:
            if solver_address not in self.registered_solvers:
                logger.error(f"Cannot slash unknown solver: {solver_address}")
                return False
            
            solver = self.registered_solvers[solver_address]
            
            # Determine slash amount
            if custom_amount:
                slash_amount = custom_amount
            else:
                slash_amount = self.slashing_amounts.get(violation_type, Decimal('0.1'))
            
            # Calculate reputation penalty
            penalty_amounts = {
                "minor_violation": 0.1,
                "major_violation": 0.3,
                "malicious_behavior": 0.5
            }
            reputation_penalty = penalty_amounts.get(violation_type, 0.1)
            
            # Apply slashing
            success = solver.slash_for_malicious_behavior(slash_amount, reputation_penalty)
            
            if success:
                logger.warning(f"Slashed solver {solver_address} for {violation_type}: {slash_amount} ETH, reputation penalty: {reputation_penalty}")
                
                # Check if solver should be suspended
                if not solver.stake_info.is_sufficient:
                    solver.status = SolverStatus.SUSPENDED
                    logger.warning(f"Suspended solver {solver_address} due to insufficient stake after slashing")
                
                # Check for repeated violations (blacklisting)
                if solver.reputation_score.slashing_penalty > 1.0:  # Multiple major violations
                    solver.status = SolverStatus.BLACKLISTED
                    logger.error(f"Blacklisted solver {solver_address} due to repeated violations")
                
                # Cancel any active intents for severely penalized solvers
                if violation_type == "malicious_behavior":
                    await self._cancel_solver_active_intents(solver_address)
                
                return True
            else:
                logger.error(f"Failed to slash solver {solver_address}")
                return False
                
        except Exception as e:
            logger.error(f"Error implementing solver slashing: {e}")
            return False
    
    async def _cancel_solver_active_intents(self, solver_address: str):
        """Cancel all active intents for a penalized solver"""
        try:
            intents_to_fallback = []
            
            for intent_hash, broadcast in self.active_intents.items():
                if broadcast.selected_solver == solver_address:
                    intents_to_fallback.append(intent_hash)
            
            for intent_hash in intents_to_fallback:
                logger.info(f"Triggering fallback for intent {intent_hash} due to solver {solver_address} penalty")
                await self._trigger_solver_fallback(intent_hash)
                
        except Exception as e:
            logger.error(f"Error canceling active intents for solver {solver_address}: {e}")
    
    async def _notify_fallback_event(self, intent_hash: str, failed_solver: str, new_solver: str):
        """Notify stakeholders about fallback event"""
        try:
            fallback_event = {
                "type": "solver_fallback",
                "intent_hash": intent_hash,
                "failed_solver": failed_solver,
                "new_solver": new_solver,
                "timestamp": datetime.now().isoformat()
            }
            
            # Notify users via WebSocket
            await self._notify_users_of_status_change(intent_hash, IntentStatus.SOLVER_SELECTED)
            
            # Notify both solvers
            await self._notify_solver_fallback(failed_solver, intent_hash, False)
            await self._notify_solver_fallback(new_solver, intent_hash, True)
            
            logger.info(f"Notified stakeholders of fallback event for intent {intent_hash}")
            
        except Exception as e:
            logger.error(f"Error notifying fallback event: {e}")
    
    async def _notify_solver_fallback(self, solver_address: str, intent_hash: str, is_new_solver: bool):
        """Notify solver about fallback event"""
        try:
            message_data = {
                "type": "fallback_notification",
                "intent_hash": intent_hash,
                "is_new_solver": is_new_solver,
                "timestamp": datetime.now().isoformat()
            }
            
            if is_new_solver:
                message_data["message"] = "You have been selected as fallback solver for this intent"
            else:
                message_data["message"] = "Your intent has been reassigned due to failure"
            
            # In production, would send WebSocket/HTTP notification
            logger.debug(f"Notifying solver {solver_address} of fallback: is_new_solver={is_new_solver}")
            
        except Exception as e:
            logger.error(f"Error notifying solver {solver_address} of fallback: {e}")
    
    async def _log_solver_incident(self, intent_hash: str, solver_address: str, failure_reason: str, penalty_applied: bool, fallback_success: bool):
        """Log solver incident for monitoring and analysis"""
        try:
            incident = {
                "timestamp": datetime.now().isoformat(),
                "intent_hash": intent_hash,
                "solver_address": solver_address,
                "failure_reason": failure_reason,
                "penalty_applied": penalty_applied,
                "fallback_success": fallback_success,
                "solver_reputation_after": self.registered_solvers[solver_address].reputation_score.total_score if solver_address in self.registered_solvers else None
            }
            
            # In production, would store in database or send to monitoring system
            logger.info(f"Logged solver incident: {incident}")
            
        except Exception as e:
            logger.error(f"Error logging solver incident: {e}")
    
    async def get_solver_failure_statistics(self, solver_address: str) -> Optional[Dict]:
        """Get failure statistics for a solver"""
        try:
            if solver_address not in self.registered_solvers:
                return None
            
            solver = self.registered_solvers[solver_address]
            
            return {
                "solver_address": solver_address,
                "total_failures": solver.performance_metrics.total_intents_failed,
                "failure_rate": solver.performance_metrics.failure_rate,
                "reputation_score": solver.reputation_score.total_score,
                "slashing_penalty": solver.reputation_score.slashing_penalty,
                "status": solver.status.value,
                "stake_info": {
                    "effective_stake": str(solver.stake_info.effective_stake) if solver.stake_info else "0",
                    "slashed_amount": str(solver.stake_info.slashed_amount) if solver.stake_info else "0",
                    "is_sufficient": solver.stake_info.is_sufficient if solver.stake_info else False
                } if solver.stake_info else None
            }
            
        except Exception as e:
            logger.error(f"Error getting failure statistics for solver {solver_address}: {e}")
            return None
    
    async def _validate_bid_signature(self, bid: SolverBid) -> bool:
        """Validate bid signature"""
        # In production, would verify cryptographic signature
        return len(bid.signature) > 0
    
    async def _notify_users_of_bid(self, intent_hash: str, bid: SolverBid):
        """Notify users of new bid via WebSocket"""
        # In production, would send WebSocket message to connected users
        logger.debug(f"Notifying users of new bid for intent {intent_hash}")
    
    async def _notify_solver_selection(self, solver_address: str, intent_hash: str, selected: bool, winning_bid: Optional[SolverBid] = None):
        """Notify solver of selection result with enhanced information"""
        try:
            message_data = {
                "type": "solver_selection_result",
                "intent_hash": intent_hash,
                "selected": selected,
                "timestamp": datetime.now().isoformat()
            }
            
            if selected and winning_bid:
                message_data.update({
                    "winning_bid": {
                        "output_amount": winning_bid.output_amount,
                        "execution_time_estimate": winning_bid.execution_time_estimate,
                        "total_cost": winning_bid.total_cost
                    },
                    "exclusive_deadline": (datetime.now() + timedelta(minutes=15)).isoformat()
                })
            
            # In production, would send WebSocket/HTTP notification
            logger.debug(f"Notifying solver {solver_address} of selection result: {selected}")
            
        except Exception as e:
            logger.error(f"Error notifying solver {solver_address}: {e}")
    
    async def get_bidding_statistics(self, intent_hash: str) -> Optional[Dict]:
        """Get comprehensive bidding statistics for an intent"""
        try:
            if intent_hash not in self.active_intents and intent_hash not in self.intent_history:
                return None
            
            broadcast = self.active_intents.get(intent_hash) or self.intent_history.get(intent_hash)
            
            # Calculate bid statistics
            bids = broadcast.bids_received
            if not bids:
                return {
                    "intent_hash": intent_hash,
                    "total_bids": 0,
                    "status": broadcast.status.value
                }
            
            output_amounts = [float(bid.output_amount) for bid in bids]
            execution_times = [bid.execution_time_estimate for bid in bids]
            total_costs = [float(bid.total_cost) for bid in bids]
            
            return {
                "intent_hash": intent_hash,
                "status": broadcast.status.value,
                "total_bids": len(bids),
                "selected_solver": broadcast.selected_solver,
                "bid_statistics": {
                    "output_amount": {
                        "min": min(output_amounts),
                        "max": max(output_amounts),
                        "avg": sum(output_amounts) / len(output_amounts)
                    },
                    "execution_time": {
                        "min": min(execution_times),
                        "max": max(execution_times),
                        "avg": sum(execution_times) / len(execution_times)
                    },
                    "total_cost": {
                        "min": min(total_costs),
                        "max": max(total_costs),
                        "avg": sum(total_costs) / len(total_costs)
                    }
                },
                "solver_tiers": {
                    tier.value: sum(1 for bid in bids 
                                  if self.registered_solvers.get(bid.solver_address, {}).tier == tier)
                    for tier in SolverTier
                },
                "broadcast_timestamp": broadcast.broadcast_timestamp.isoformat(),
                "selection_timestamp": broadcast.selection_timestamp.isoformat() if broadcast.selection_timestamp else None
            }
            
        except Exception as e:
            logger.error(f"Error getting bidding statistics for {intent_hash}: {e}")
            return None
    
    async def _notify_users_of_status_change(self, intent_hash: str, status: IntentStatus):
        """Notify users of intent status change"""
        # In production, would send WebSocket message to connected users
        logger.debug(f"Notifying users of status change for intent {intent_hash}: {status.value}")
    
    async def _handle_intent_completion(self, intent_hash: str):
        """Handle successful intent completion"""
        broadcast = self.active_intents[intent_hash]
        
        if broadcast.selected_solver:
            # Update solver reputation for successful completion
            await self.update_solver_reputation(
                broadcast.selected_solver,
                intent_completed=True
            )
        
        # Move to history
        self.intent_history[intent_hash] = self.active_intents.pop(intent_hash)
    
    async def _handle_intent_failure(self, intent_hash: str):
        """Handle intent failure"""
        broadcast = self.active_intents[intent_hash]
        
        if broadcast.selected_solver:
            # Update solver reputation for failure
            await self.update_solver_reputation(
                broadcast.selected_solver,
                intent_failed=True
            )
        
        # Move to history
        self.intent_history[intent_hash] = self.active_intents.pop(intent_hash)
    
    async def _handle_intent_expiry(self, intent_hash: str):
        """Handle intent expiry"""
        # Similar to failure handling
        await self._handle_intent_failure(intent_hash)
    
    async def _update_reputation_scores(self):
        """Background task to update reputation scores and apply decay"""
        while True:
            try:
                current_time = datetime.now()
                
                for solver in self.registered_solvers.values():
                    # Apply reputation decay for inactive solvers
                    if solver.performance_metrics.last_activity:
                        days_inactive = (current_time - solver.performance_metrics.last_activity).days
                        if days_inactive > 1:
                            # Apply daily decay
                            decay_amount = self.reputation_decay_rate * days_inactive
                            solver.reputation_score.base_score = max(
                                0.5, 
                                solver.reputation_score.base_score - decay_amount
                            )
                            solver.reputation_score.last_updated = current_time
                
                await asyncio.sleep(86400)  # Check daily
                
            except Exception as e:
                logger.error(f"Error in reputation update task: {e}")
                await asyncio.sleep(86400)
    
    async def _monitor_solver_failures(self):
        """Background task to monitor and detect solver failures"""
        while True:
            try:
                current_time = datetime.now()
                failed_intents = []
                
                for intent_hash, broadcast in self.active_intents.items():
                    if broadcast.status == IntentStatus.SOLVER_SELECTED:
                        # Check for various failure conditions
                        failure_detected = await self.detect_solver_failure(intent_hash)
                        
                        if failure_detected:
                            failed_intents.append((intent_hash, broadcast.selected_solver))
                
                # Process detected failures
                for intent_hash, failed_solver in failed_intents:
                    logger.warning(f"Auto-detected failure for solver {failed_solver} on intent {intent_hash}")
                    await self.report_solver_failure(intent_hash, failed_solver, "timeout")
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in failure detection task: {e}")
                await asyncio.sleep(60)
    
    async def _cleanup_expired_intents(self):
        """Background task to clean up expired intents"""
        while True:
            try:
                current_time = datetime.now()
                expired_intents = []
                
                for intent_hash, broadcast in self.active_intents.items():
                    if current_time > broadcast.execution_deadline:
                        expired_intents.append(intent_hash)
                
                for intent_hash in expired_intents:
                    await self.update_intent_status(intent_hash, IntentStatus.EXPIRED)
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(60)
    
    async def _monitor_solver_health(self):
        """Background task to monitor solver health"""
        while True:
            try:
                current_time = datetime.now()
                
                for solver in self.registered_solvers.values():
                    # Mark solvers as inactive if not seen recently
                    if current_time - solver.last_seen > timedelta(minutes=5):
                        if solver.status == SolverStatus.ACTIVE:
                            solver.status = SolverStatus.INACTIVE
                            logger.warning(f"Solver {solver.address} marked as inactive")
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in monitoring task: {e}")
                await asyncio.sleep(300)


# Global instance
solver_network_service = SolverNetworkService()