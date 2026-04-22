"""
Solver Network API Routes - Phase 3
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from datetime import datetime

router = APIRouter(prefix="/solvers", tags=["Solver Network"])


class SolverApplicationRequest(BaseModel):
    name: str
    wallet_address: str
    api_endpoint: str
    supported_chains: List[str]
    supported_tokens: List[str]
    max_volume: float
    min_volume: float
    stake_amount: float
    contact_email: str
    company_name: Optional[str] = None


class BidRequest(BaseModel):
    solver_id: str
    auction_id: str
    offered_output: float
    execution_time_estimate: int
    gas_cost_estimate: float
    signature: str


@router.post("/register")
async def register_solver(request: SolverApplicationRequest) -> Dict[str, Any]:
    """Register a new solver."""
    from ...solvers import SolverRegistry
    from ...solvers.solver_registry import SolverApplication, SolverCapabilities
    
    registry = SolverRegistry()
    
    capabilities = SolverCapabilities(
        supported_chains=request.supported_chains,
        supported_tokens=request.supported_tokens,
        max_volume_per_trade=request.max_volume,
        min_volume_per_trade=request.min_volume,
        supported_intent_types=["swap", "bridge"]
    )
    
    application = SolverApplication(
        name=request.name,
        wallet_address=request.wallet_address,
        api_endpoint=request.api_endpoint,
        capabilities=capabilities,
        stake_amount=request.stake_amount,
        contact_email=request.contact_email,
        company_name=request.company_name
    )
    
    result = await registry.register_solver(application)
    
    return {
        "success": result.success,
        "solver_id": result.solver_id,
        "message": result.message,
        "requirements_met": result.requirements_met
    }


@router.get("/list")
async def list_solvers(
    chain: Optional[str] = None,
    min_reputation: Optional[float] = None
) -> List[Dict[str, Any]]:
    """List active solvers."""
    from ...solvers import SolverRegistry
    from ...solvers.solver_registry import SolverFilters
    
    registry = SolverRegistry()
    
    filters = SolverFilters(
        chains=[chain] if chain else None,
        min_reputation=min_reputation
    )
    
    solvers = await registry.list_active_solvers(filters)
    
    return [
        {
            "solver_id": s.solver_id,
            "name": s.name,
            "reputation_score": s.reputation_score,
            "fulfillment_rate": s.fulfillment_rate,
            "total_volume": s.total_volume,
            "status": s.status.value
        }
        for s in solvers
    ]


@router.get("/{solver_id}")
async def get_solver(solver_id: str) -> Dict[str, Any]:
    """Get solver details."""
    from ...solvers import SolverRegistry
    
    registry = SolverRegistry()
    solver = await registry.get_solver_info(solver_id)
    
    if not solver:
        raise HTTPException(404, "Solver not found")
    
    return {
        "solver_id": solver.solver_id,
        "name": solver.name,
        "status": solver.status.value,
        "reputation_score": solver.reputation_score,
        "fulfillment_rate": solver.fulfillment_rate,
        "total_volume": solver.total_volume,
        "average_execution_time": solver.average_execution_time,
        "capabilities": {
            "chains": solver.capabilities.supported_chains,
            "tokens": solver.capabilities.supported_tokens
        }
    }


@router.get("/network/stats")
async def get_network_stats() -> Dict[str, Any]:
    """Get solver network statistics."""
    from ...solvers import SolverRegistry
    
    registry = SolverRegistry()
    stats = await registry.get_network_statistics()
    
    return {
        "total_solvers": stats.total_solvers,
        "active_solvers": stats.active_solvers,
        "total_volume_24h": stats.total_volume_24h,
        "total_intents_fulfilled_24h": stats.total_intents_fulfilled_24h,
        "average_fulfillment_rate": stats.average_fulfillment_rate,
        "average_execution_time_ms": stats.average_execution_time_ms
    }


@router.get("/leaderboard")
async def get_leaderboard(limit: int = 20) -> List[Dict[str, Any]]:
    """Get solver leaderboard."""
    from ...solvers import ReputationManager
    
    manager = ReputationManager()
    rankings = await manager.get_leaderboard(limit=limit)
    
    return [
        {
            "rank": r.rank,
            "solver_id": r.solver_id,
            "name": r.solver_name,
            "score": r.score,
            "total_volume": r.total_volume,
            "fulfillment_rate": r.fulfillment_rate
        }
        for r in rankings
    ]
