"""
Reputation Manager - Solver Performance Tracking
Phase 3: Autonomy & MEV Protection

Tracks and manages solver reputation based on performance metrics.
"""

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class ReputationScore:
    solver_id: str
    score: float  # 0.0 to 1.0
    fulfillment_rate: float
    average_execution_time_ms: float
    price_improvement_avg: float
    total_fulfillments: int
    successful_fulfillments: int
    last_updated: datetime


@dataclass
class PerformanceRecord:
    solver_id: str
    auction_id: str
    success: bool
    execution_time_ms: int
    price_improvement: float
    timestamp: datetime


@dataclass
class SolverRanking:
    rank: int
    solver_id: str
    solver_name: str
    score: float
    total_volume: float
    fulfillment_rate: float


@dataclass
class PerformanceHistory:
    solver_id: str
    records: List[PerformanceRecord]
    period_start: datetime
    period_end: datetime
    summary: Dict[str, Any]


class ReputationManager:
    """
    Reputation Manager tracks solver performance and reputation.
    
    Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5
    """
    
    # Decay factor for time-weighted scoring (recent = more weight)
    DECAY_HALF_LIFE_DAYS = 7
    
    def __init__(self):
        self.reputations: Dict[str, ReputationScore] = {}
        self.performance_history: Dict[str, List[PerformanceRecord]] = {}
        self.user_preferences: Dict[str, Dict[str, List[str]]] = {}  # user -> {whitelist, blacklist}
    
    async def calculate_reputation(self, solver_id: str) -> ReputationScore:
        """
        Calculate reputation score for a solver.
        
        Property 21: Recency-Weighted Reputation
        For any reputation calculation, weights recent performance more heavily.
        """
        records = self.performance_history.get(solver_id, [])
        
        if not records:
            return ReputationScore(
                solver_id=solver_id,
                score=0.5,
                fulfillment_rate=1.0,
                average_execution_time_ms=0,
                price_improvement_avg=0,
                total_fulfillments=0,
                successful_fulfillments=0,
                last_updated=datetime.utcnow()
            )
        
        # Apply time decay weights
        now = datetime.utcnow()
        weighted_scores = []
        total_weight = 0
        
        for record in records:
            age_days = (now - record.timestamp).days
            weight = math.exp(-age_days / self.DECAY_HALF_LIFE_DAYS)
            
            # Score components
            success_score = 1.0 if record.success else 0.0
            speed_score = max(0, 1 - (record.execution_time_ms / 60000))
            price_score = min(1, record.price_improvement * 10)  # Scale improvement
            
            record_score = (success_score * 0.5) + (speed_score * 0.25) + (price_score * 0.25)
            weighted_scores.append(record_score * weight)
            total_weight += weight
        
        final_score = sum(weighted_scores) / total_weight if total_weight > 0 else 0.5
        
        # Calculate metrics
        successful = [r for r in records if r.success]
        fulfillment_rate = len(successful) / len(records) if records else 1.0
        avg_time = sum(r.execution_time_ms for r in successful) / len(successful) if successful else 0
        avg_improvement = sum(r.price_improvement for r in successful) / len(successful) if successful else 0
        
        reputation = ReputationScore(
            solver_id=solver_id,
            score=final_score,
            fulfillment_rate=fulfillment_rate,
            average_execution_time_ms=avg_time,
            price_improvement_avg=avg_improvement,
            total_fulfillments=len(records),
            successful_fulfillments=len(successful),
            last_updated=datetime.utcnow()
        )
        
        self.reputations[solver_id] = reputation
        return reputation

    async def update_from_fulfillment(
        self,
        solver_id: str,
        auction_id: str,
        success: bool,
        execution_time_ms: int,
        price_improvement: float
    ) -> None:
        """
        Update reputation from fulfillment result.
        
        Property 22: Real-Time Reputation Updates
        For any solver performance change, updates reputation in real-time.
        """
        record = PerformanceRecord(
            solver_id=solver_id,
            auction_id=auction_id,
            success=success,
            execution_time_ms=execution_time_ms,
            price_improvement=price_improvement,
            timestamp=datetime.utcnow()
        )
        
        if solver_id not in self.performance_history:
            self.performance_history[solver_id] = []
        
        self.performance_history[solver_id].append(record)
        
        # Recalculate reputation
        await self.calculate_reputation(solver_id)
        
        logger.info(f"Updated reputation for {solver_id}: success={success}")
    
    async def get_reputation(self, solver_id: str) -> Optional[ReputationScore]:
        """Get current reputation score."""
        if solver_id in self.reputations:
            return self.reputations[solver_id]
        return await self.calculate_reputation(solver_id)
    
    async def get_performance_history(
        self,
        solver_id: str,
        days: int = 30
    ) -> PerformanceHistory:
        """
        Get performance history for a solver.
        
        Property 20: Solver Performance Display
        For any solver, displays historical performance metrics.
        """
        records = self.performance_history.get(solver_id, [])
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        filtered = [r for r in records if r.timestamp >= cutoff]
        
        # Calculate summary
        successful = [r for r in filtered if r.success]
        summary = {
            "total_fulfillments": len(filtered),
            "successful_fulfillments": len(successful),
            "fulfillment_rate": len(successful) / len(filtered) if filtered else 0,
            "avg_execution_time_ms": sum(r.execution_time_ms for r in successful) / len(successful) if successful else 0,
            "avg_price_improvement": sum(r.price_improvement for r in successful) / len(successful) if successful else 0
        }
        
        return PerformanceHistory(
            solver_id=solver_id,
            records=filtered,
            period_start=cutoff,
            period_end=datetime.utcnow(),
            summary=summary
        )

    async def get_leaderboard(
        self,
        category: Optional[str] = None,
        limit: int = 20
    ) -> List[SolverRanking]:
        """Get solver leaderboard rankings."""
        # Ensure all reputations are calculated
        for solver_id in self.performance_history.keys():
            if solver_id not in self.reputations:
                await self.calculate_reputation(solver_id)
        
        # Sort by score
        sorted_reps = sorted(
            self.reputations.values(),
            key=lambda r: r.score,
            reverse=True
        )
        
        rankings = []
        for i, rep in enumerate(sorted_reps[:limit]):
            rankings.append(SolverRanking(
                rank=i + 1,
                solver_id=rep.solver_id,
                solver_name=rep.solver_id,  # Would lookup actual name
                score=rep.score,
                total_volume=rep.total_fulfillments * 1000,  # Estimate
                fulfillment_rate=rep.fulfillment_rate
            ))
        
        return rankings
    
    async def set_user_preference(
        self,
        user_address: str,
        whitelist: Optional[List[str]] = None,
        blacklist: Optional[List[str]] = None
    ) -> None:
        """
        Set user solver preferences.
        
        Property 23: Solver Preference Management
        For any user preference, supports whitelist/blacklist of solvers.
        """
        if user_address not in self.user_preferences:
            self.user_preferences[user_address] = {"whitelist": [], "blacklist": []}
        
        if whitelist is not None:
            self.user_preferences[user_address]["whitelist"] = whitelist
        
        if blacklist is not None:
            self.user_preferences[user_address]["blacklist"] = blacklist
    
    async def get_user_preferences(
        self,
        user_address: str
    ) -> Dict[str, List[str]]:
        """Get user solver preferences."""
        return self.user_preferences.get(user_address, {"whitelist": [], "blacklist": []})
    
    def filter_solvers_for_user(
        self,
        user_address: str,
        solver_ids: List[str]
    ) -> List[str]:
        """Filter solvers based on user preferences."""
        prefs = self.user_preferences.get(user_address, {"whitelist": [], "blacklist": []})
        
        # If whitelist exists, only allow whitelisted
        if prefs["whitelist"]:
            solver_ids = [s for s in solver_ids if s in prefs["whitelist"]]
        
        # Remove blacklisted
        if prefs["blacklist"]:
            solver_ids = [s for s in solver_ids if s not in prefs["blacklist"]]
        
        return solver_ids
    
    async def apply_reputation_decay(self) -> int:
        """Apply time-based decay to all reputations."""
        updated = 0
        for solver_id in list(self.reputations.keys()):
            await self.calculate_reputation(solver_id)
            updated += 1
        return updated
