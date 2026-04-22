"""
Auction Manager - Fair Intent Fulfillment Auctions
Phase 3: Autonomy & MEV Protection

Runs fair and transparent auctions for intent fulfillment.
"""

import asyncio
import hashlib
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class AuctionStatus(Enum):
    OPEN = "open"
    CLOSED = "closed"
    FULFILLED = "fulfilled"
    FAILED = "failed"
    EXPIRED = "expired"


@dataclass
class Intent:
    intent_id: str
    user_address: str
    source_chain: str
    dest_chain: str
    input_token: str
    output_token: str
    input_amount: float
    min_output_amount: float
    deadline: datetime
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SolverBid:
    bid_id: str
    solver_id: str
    auction_id: str
    offered_output: float
    execution_time_estimate: int  # milliseconds
    gas_cost_estimate: float
    expiry: datetime
    signature: str
    submitted_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class WinningBid:
    bid: SolverBid
    selection_reason: str
    exclusive_until: datetime
    fulfillment_deadline: datetime


@dataclass
class Auction:
    auction_id: str
    intent: Intent
    status: AuctionStatus
    bids: List[SolverBid]
    winning_bid: Optional[WinningBid]
    created_at: datetime
    closes_at: datetime
    auction_window_seconds: int = 30


@dataclass
class AuctionResult:
    auction_id: str
    intent_id: str
    winning_solver: Optional[str]
    winning_bid: Optional[SolverBid]
    total_bids: int
    price_improvement: float
    execution_result: Optional[Dict[str, Any]]
    timestamp: datetime


@dataclass
class FailoverResult:
    success: bool
    new_winner: Optional[str]
    message: str


class AuctionManager:
    """
    Auction Manager runs fair auctions for intent fulfillment.
    
    Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5
    """
    
    DEFAULT_AUCTION_WINDOW = 30  # seconds
    EXCLUSIVE_WINDOW = 30  # seconds for winner to fulfill
    
    def __init__(self, solver_registry=None, reputation_manager=None):
        self.auctions: Dict[str, Auction] = {}
        self.auction_history: List[AuctionResult] = []
        self.solver_registry = solver_registry
        self.reputation_manager = reputation_manager

    async def create_auction(self, intent: Intent) -> Auction:
        """
        Create a new auction for an intent.
        
        Property 13: Fair Auction Mechanism
        For any auction, uses fair and transparent mechanism.
        """
        auction_id = self._generate_auction_id(intent)
        
        auction = Auction(
            auction_id=auction_id,
            intent=intent,
            status=AuctionStatus.OPEN,
            bids=[],
            winning_bid=None,
            created_at=datetime.utcnow(),
            closes_at=datetime.utcnow() + timedelta(seconds=self.DEFAULT_AUCTION_WINDOW)
        )
        
        self.auctions[auction_id] = auction
        logger.info(f"Created auction {auction_id} for intent {intent.intent_id}")
        
        return auction
    
    async def submit_bid(
        self,
        auction_id: str,
        bid: SolverBid
    ) -> Dict[str, Any]:
        """
        Submit a bid to an auction.
        
        Property 12: Open Bid Submission
        For any broadcast intent, all registered solvers can submit bids.
        """
        auction = self.auctions.get(auction_id)
        if not auction:
            return {"success": False, "message": "Auction not found"}
        
        if auction.status != AuctionStatus.OPEN:
            return {"success": False, "message": "Auction is not open"}
        
        if datetime.utcnow() > auction.closes_at:
            auction.status = AuctionStatus.CLOSED
            return {"success": False, "message": "Auction has closed"}
        
        # Validate bid meets minimum output
        if bid.offered_output < auction.intent.min_output_amount:
            return {"success": False, "message": "Bid below minimum output"}
        
        # Validate signature (simplified)
        if not self._validate_signature(bid):
            return {"success": False, "message": "Invalid signature"}
        
        auction.bids.append(bid)
        logger.info(f"Bid {bid.bid_id} submitted to auction {auction_id}")
        
        return {"success": True, "message": "Bid submitted", "bid_id": bid.bid_id}
    
    def _validate_signature(self, bid: SolverBid) -> bool:
        """Validate bid signature."""
        return len(bid.signature) > 0

    async def get_auction_status(self, auction_id: str) -> Optional[Dict[str, Any]]:
        """Get current auction status."""
        auction = self.auctions.get(auction_id)
        if not auction:
            return None
        
        return {
            "auction_id": auction_id,
            "status": auction.status.value,
            "bid_count": len(auction.bids),
            "closes_at": auction.closes_at.isoformat(),
            "winning_bid": auction.winning_bid.bid.bid_id if auction.winning_bid else None
        }
    
    async def select_winner(self, auction_id: str) -> Optional[WinningBid]:
        """
        Select winning bid based on ranking.
        
        Property 15: Bid Ranking Correctness
        For any set of bids, ranks correctly by price, speed, and reputation.
        """
        auction = self.auctions.get(auction_id)
        if not auction or not auction.bids:
            return None
        
        # Rank bids
        ranked_bids = await self._rank_bids(auction.bids, auction.intent)
        
        if not ranked_bids:
            auction.status = AuctionStatus.FAILED
            return None
        
        best_bid = ranked_bids[0]
        
        winning = WinningBid(
            bid=best_bid,
            selection_reason="Highest score based on price, speed, and reputation",
            exclusive_until=datetime.utcnow() + timedelta(seconds=self.EXCLUSIVE_WINDOW),
            fulfillment_deadline=auction.intent.deadline
        )
        
        auction.winning_bid = winning
        auction.status = AuctionStatus.CLOSED
        
        logger.info(f"Winner selected for auction {auction_id}: {best_bid.solver_id}")
        
        return winning
    
    async def _rank_bids(
        self,
        bids: List[SolverBid],
        intent: Intent
    ) -> List[SolverBid]:
        """
        Rank bids by composite score.
        
        Property 15: Bid Ranking Correctness
        """
        scored_bids = []
        
        for bid in bids:
            # Price improvement score (higher output = better)
            price_score = (bid.offered_output - intent.min_output_amount) / intent.min_output_amount
            price_score = min(price_score, 1.0)  # Cap at 100% improvement
            
            # Speed score (faster = better)
            speed_score = 1.0 - (bid.execution_time_estimate / 60000)  # Normalize to 1 minute
            speed_score = max(0, min(speed_score, 1.0))
            
            # Reputation score
            rep_score = 0.5  # Default
            if self.reputation_manager:
                rep = await self.reputation_manager.get_reputation(bid.solver_id)
                rep_score = rep.score if rep else 0.5
            
            # Composite score (weighted)
            total_score = (price_score * 0.5) + (speed_score * 0.2) + (rep_score * 0.3)
            
            scored_bids.append((bid, total_score))
        
        # Sort by score descending
        scored_bids.sort(key=lambda x: x[1], reverse=True)
        
        return [bid for bid, _ in scored_bids]

    async def handle_fulfillment_failure(
        self,
        auction_id: str,
        solver_id: str
    ) -> FailoverResult:
        """
        Handle solver failure and failover to next best.
        
        Property 17: Automatic Failover on Failure
        For any winning solver that fails, automatically assigns next best.
        """
        auction = self.auctions.get(auction_id)
        if not auction:
            return FailoverResult(False, None, "Auction not found")
        
        if not auction.winning_bid or auction.winning_bid.bid.solver_id != solver_id:
            return FailoverResult(False, None, "Solver is not current winner")
        
        # Get remaining bids excluding failed solver
        remaining_bids = [b for b in auction.bids if b.solver_id != solver_id]
        
        if not remaining_bids:
            auction.status = AuctionStatus.FAILED
            return FailoverResult(False, None, "No alternative solvers available")
        
        # Re-rank and select new winner
        ranked = await self._rank_bids(remaining_bids, auction.intent)
        new_winner = ranked[0]
        
        auction.winning_bid = WinningBid(
            bid=new_winner,
            selection_reason="Failover from failed solver",
            exclusive_until=datetime.utcnow() + timedelta(seconds=self.EXCLUSIVE_WINDOW),
            fulfillment_deadline=auction.intent.deadline
        )
        
        logger.info(f"Failover: {solver_id} -> {new_winner.solver_id} for auction {auction_id}")
        
        return FailoverResult(True, new_winner.solver_id, "Failover successful")
    
    async def record_fulfillment(
        self,
        auction_id: str,
        execution_result: Dict[str, Any]
    ) -> AuctionResult:
        """Record successful fulfillment."""
        auction = self.auctions.get(auction_id)
        if not auction:
            raise ValueError(f"Auction {auction_id} not found")
        
        auction.status = AuctionStatus.FULFILLED
        
        # Calculate price improvement
        price_improvement = 0.0
        if auction.winning_bid:
            actual = execution_result.get('output_amount', 0)
            min_out = auction.intent.min_output_amount
            if min_out > 0:
                price_improvement = (actual - min_out) / min_out
        
        result = AuctionResult(
            auction_id=auction_id,
            intent_id=auction.intent.intent_id,
            winning_solver=auction.winning_bid.bid.solver_id if auction.winning_bid else None,
            winning_bid=auction.winning_bid.bid if auction.winning_bid else None,
            total_bids=len(auction.bids),
            price_improvement=price_improvement,
            execution_result=execution_result,
            timestamp=datetime.utcnow()
        )
        
        self.auction_history.append(result)
        return result
    
    async def get_auction_history(
        self,
        solver_id: Optional[str] = None,
        limit: int = 100
    ) -> List[AuctionResult]:
        """Get auction history with optional filtering."""
        history = self.auction_history
        
        if solver_id:
            history = [h for h in history if h.winning_solver == solver_id]
        
        return history[-limit:]
    
    def _generate_auction_id(self, intent: Intent) -> str:
        """Generate unique auction ID."""
        data = f"{intent.intent_id}{time.time()}"
        return f"auction_{hashlib.sha256(data.encode()).hexdigest()[:12]}"
    
    async def grant_exclusive_rights(
        self,
        auction_id: str,
        solver_id: str,
        duration_seconds: int = 30
    ) -> Dict[str, Any]:
        """
        Grant exclusive fulfillment rights to winner.
        
        Property 16: Exclusive Fulfillment Rights
        For any winning solver, grants exclusive rights for specified window.
        """
        auction = self.auctions.get(auction_id)
        if not auction or not auction.winning_bid:
            return {"success": False, "message": "No winning bid"}
        
        if auction.winning_bid.bid.solver_id != solver_id:
            return {"success": False, "message": "Not the winning solver"}
        
        auction.winning_bid.exclusive_until = datetime.utcnow() + timedelta(seconds=duration_seconds)
        
        return {
            "success": True,
            "exclusive_until": auction.winning_bid.exclusive_until.isoformat(),
            "duration_seconds": duration_seconds
        }
