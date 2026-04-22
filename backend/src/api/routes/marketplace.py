"""
Strategy Marketplace API Routes - Phase 4
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from datetime import datetime

router = APIRouter(prefix="/marketplace", tags=["Strategy Marketplace"])


class StrategyListingRequest(BaseModel):
    publisher_address: str
    name: str
    description: str
    category: str  # conservative, moderate, aggressive
    performance_fee_percent: float
    min_allocation: float
    track_record_start: str  # ISO date
    total_trades: int
    total_return_percent: float
    sharpe_ratio: float
    max_drawdown_percent: float
    win_rate: float
    volatility: float
    var_95: float
    sortino_ratio: float
    beta: float
    max_leverage: float


class FollowStrategyRequest(BaseModel):
    follower_address: str
    strategy_id: str
    allocation_amount: float


class UnfollowRequest(BaseModel):
    subscription_id: str


@router.post("/list")
async def list_strategy(request: StrategyListingRequest) -> Dict[str, Any]:
    """List a new strategy on the marketplace."""
    from ...marketplace import (
        StrategyMarketplace, StrategyListing, TrackRecord, RiskMetrics,
        StrategyCategory, ListingStatus
    )
    import hashlib
    import time
    
    marketplace = StrategyMarketplace()
    
    category_map = {
        "conservative": StrategyCategory.CONSERVATIVE,
        "moderate": StrategyCategory.MODERATE,
        "aggressive": StrategyCategory.AGGRESSIVE,
    }
    
    category = category_map.get(request.category)
    if not category:
        raise HTTPException(400, f"Invalid category: {request.category}")
    
    track_record = TrackRecord(
        start_date=datetime.fromisoformat(request.track_record_start),
        total_trades=request.total_trades,
        total_return_percent=request.total_return_percent,
        sharpe_ratio=request.sharpe_ratio,
        max_drawdown_percent=request.max_drawdown_percent,
        win_rate=request.win_rate,
    )
    
    risk_metrics = RiskMetrics(
        volatility=request.volatility,
        var_95=request.var_95,
        sortino_ratio=request.sortino_ratio,
        beta=request.beta,
        max_leverage=request.max_leverage,
    )
    
    strategy_id = f"strat_{hashlib.sha256(f'{request.name}{time.time()}'.encode()).hexdigest()[:12]}"
    
    listing = StrategyListing(
        strategy_id=strategy_id,
        publisher_address=request.publisher_address,
        name=request.name,
        description=request.description,
        category=category,
        performance_fee_percent=request.performance_fee_percent,
        min_allocation=request.min_allocation,
        track_record=track_record,
        risk_metrics=risk_metrics,
        status=ListingStatus.PENDING,
        created_at=datetime.utcnow(),
    )
    
    # Validate
    validation = await marketplace.validate_listing(listing)
    if not validation.valid:
        raise HTTPException(400, {"errors": validation.errors, "warnings": validation.warnings})
    
    await marketplace.list_strategy(listing)
    
    return {
        "strategy_id": strategy_id,
        "status": "active",
        "warnings": validation.warnings,
    }


@router.post("/follow")
async def follow_strategy(request: FollowStrategyRequest) -> Dict[str, Any]:
    """Follow a strategy."""
    from ...marketplace import StrategyMarketplace
    
    marketplace = StrategyMarketplace()
    
    try:
        subscription = await marketplace.follow_strategy(
            request.follower_address,
            request.strategy_id,
            request.allocation_amount,
        )
        
        return {
            "subscription_id": subscription.subscription_id,
            "strategy_id": subscription.strategy_id,
            "allocation": subscription.allocation_amount,
            "status": subscription.status.value,
        }
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/unfollow")
async def unfollow_strategy(request: UnfollowRequest) -> Dict[str, Any]:
    """Unfollow a strategy and settle fees."""
    from ...marketplace import StrategyMarketplace
    
    marketplace = StrategyMarketplace()
    
    try:
        settlement = await marketplace.unfollow_strategy(request.subscription_id)
        
        return {
            "subscription_id": settlement.subscription_id,
            "settled_amount": settlement.settled_amount,
            "settlement_time": settlement.settlement_time.isoformat(),
        }
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/strategies")
async def search_strategies(
    category: Optional[str] = None,
    min_return: Optional[float] = None,
    max_drawdown: Optional[float] = None,
    min_sharpe: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """Search strategies."""
    from ...marketplace import StrategyMarketplace, StrategyFilters, StrategyCategory
    
    marketplace = StrategyMarketplace()
    
    category_map = {
        "conservative": StrategyCategory.CONSERVATIVE,
        "moderate": StrategyCategory.MODERATE,
        "aggressive": StrategyCategory.AGGRESSIVE,
    }
    
    filters = StrategyFilters(
        category=category_map.get(category) if category else None,
        min_return=min_return,
        max_drawdown=max_drawdown,
        min_sharpe=min_sharpe,
    )
    
    strategies = await marketplace.search_strategies(filters)
    
    return [
        {
            "strategy_id": s.strategy_id,
            "name": s.name,
            "category": s.category.value,
            "performance_fee": s.performance_fee_percent,
            "sharpe_ratio": s.track_record.sharpe_ratio,
            "total_return": s.track_record.total_return_percent,
            "followers": s.followers_count,
        }
        for s in strategies
    ]


@router.get("/strategy/{strategy_id}")
async def get_strategy(strategy_id: str) -> Dict[str, Any]:
    """Get strategy details."""
    from ...marketplace import StrategyMarketplace
    
    marketplace = StrategyMarketplace()
    strategy = await marketplace.get_strategy(strategy_id)
    
    if not strategy:
        raise HTTPException(404, "Strategy not found")
    
    return {
        "strategy_id": strategy.strategy_id,
        "name": strategy.name,
        "description": strategy.description,
        "category": strategy.category.value,
        "performance_fee": strategy.performance_fee_percent,
        "min_allocation": strategy.min_allocation,
        "status": strategy.status.value,
        "followers": strategy.followers_count,
        "track_record": {
            "start_date": strategy.track_record.start_date.isoformat(),
            "total_trades": strategy.track_record.total_trades,
            "total_return": strategy.track_record.total_return_percent,
            "sharpe_ratio": strategy.track_record.sharpe_ratio,
            "max_drawdown": strategy.track_record.max_drawdown_percent,
            "win_rate": strategy.track_record.win_rate,
        },
        "risk_metrics": {
            "volatility": strategy.risk_metrics.volatility,
            "var_95": strategy.risk_metrics.var_95,
            "sortino_ratio": strategy.risk_metrics.sortino_ratio,
        },
    }


@router.get("/subscription/{subscription_id}/fees")
async def get_subscription_fees(subscription_id: str) -> Dict[str, Any]:
    """Get fee calculation for subscription."""
    from ...marketplace import StrategyMarketplace
    
    marketplace = StrategyMarketplace()
    
    try:
        fees = await marketplace.calculate_fees(subscription_id)
        
        return {
            "subscription_id": fees.subscription_id,
            "gross_profit": fees.gross_profit,
            "fee_amount": fees.fee_amount,
            "fee_percent": fees.fee_percent,
            "high_water_mark": fees.high_water_mark,
        }
    except ValueError as e:
        raise HTTPException(404, str(e))
