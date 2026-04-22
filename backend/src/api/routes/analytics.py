"""
Performance Analytics API Routes - Phase 4
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

router = APIRouter(prefix="/analytics", tags=["Performance Analytics"])


class RecordTradeRequest(BaseModel):
    strategy_id: str
    trade_id: str
    pnl: float
    return_pct: float
    trade_type: str
    portfolio_value: float


class UpdateStrategyDataRequest(BaseModel):
    strategy_id: str
    followers: int
    aum: float
    fees: float
    avg_allocation: float


@router.get("/strategy/{strategy_id}/metrics")
async def get_strategy_metrics(
    strategy_id: str,
    days: int = 30,
) -> Dict[str, Any]:
    """Get strategy performance metrics."""
    from ...analytics import PerformanceAnalytics, DateRange
    
    analytics = PerformanceAnalytics()
    
    period = DateRange(
        start=datetime.utcnow() - timedelta(days=days),
        end=datetime.utcnow(),
    )
    
    metrics = await analytics.calculate_metrics(strategy_id, period)
    
    return {
        "strategy_id": metrics.strategy_id,
        "period_days": days,
        "roi_percent": metrics.roi_percent,
        "max_drawdown_percent": metrics.max_drawdown_percent,
        "win_rate": metrics.win_rate,
        "sharpe_ratio": metrics.sharpe_ratio,
        "sortino_ratio": metrics.sortino_ratio,
        "benchmark_comparison": metrics.benchmark_comparison,
        "follower_count": metrics.follower_count,
        "follower_growth": metrics.follower_growth,
        "total_fees_earned": metrics.total_fees_earned,
    }


@router.get("/strategy/{strategy_id}/benchmark/{benchmark}")
async def compare_to_benchmark(
    strategy_id: str,
    benchmark: str,
) -> Dict[str, Any]:
    """Compare strategy to benchmark."""
    from ...analytics import PerformanceAnalytics
    
    analytics = PerformanceAnalytics()
    
    comparison = await analytics.compare_to_benchmark(strategy_id, benchmark)
    
    return {
        "strategy_id": comparison.strategy_id,
        "benchmark": comparison.benchmark_name,
        "strategy_return": comparison.strategy_return,
        "benchmark_return": comparison.benchmark_return,
        "alpha": comparison.alpha,
        "tracking_error": comparison.tracking_error,
        "period_start": comparison.period.start.isoformat(),
        "period_end": comparison.period.end.isoformat(),
    }


@router.get("/strategy/{strategy_id}/attribution")
async def get_trade_attribution(strategy_id: str) -> List[Dict[str, Any]]:
    """Get trade attribution analysis."""
    from ...analytics import PerformanceAnalytics
    
    analytics = PerformanceAnalytics()
    
    attribution = await analytics.get_attribution(strategy_id)
    
    return [
        {
            "trade_id": a.trade_id,
            "contribution_percent": a.contribution_percent,
            "pnl": a.pnl,
            "trade_type": a.trade_type,
            "timestamp": a.timestamp.isoformat(),
        }
        for a in attribution
    ]


@router.get("/strategy/{strategy_id}/degradation")
async def check_degradation(strategy_id: str) -> Dict[str, Any]:
    """Check for performance degradation."""
    from ...analytics import PerformanceAnalytics
    
    analytics = PerformanceAnalytics()
    
    alert = await analytics.detect_degradation(strategy_id)
    
    if not alert:
        return {"strategy_id": strategy_id, "degradation_detected": False}
    
    return {
        "strategy_id": alert.strategy_id,
        "degradation_detected": True,
        "alert_type": alert.alert_type,
        "severity": alert.severity,
        "message": alert.message,
        "current_value": alert.current_value,
        "threshold": alert.threshold,
        "detected_at": alert.detected_at.isoformat(),
    }


@router.get("/strategy/{strategy_id}/followers")
async def get_follower_analytics(strategy_id: str) -> Dict[str, Any]:
    """Get follower analytics for strategy."""
    from ...analytics import PerformanceAnalytics
    
    analytics = PerformanceAnalytics()
    
    follower_data = await analytics.get_follower_analytics(strategy_id)
    
    return {
        "strategy_id": follower_data.strategy_id,
        "total_followers": follower_data.total_followers,
        "follower_growth_percent": follower_data.follower_growth_percent,
        "total_aum": follower_data.total_aum,
        "total_fees_earned": follower_data.total_fees_earned,
        "avg_allocation": follower_data.avg_allocation,
        "period_start": follower_data.period.start.isoformat(),
        "period_end": follower_data.period.end.isoformat(),
    }


@router.post("/trade/record")
async def record_trade(request: RecordTradeRequest) -> Dict[str, Any]:
    """Record a trade for analytics."""
    from ...analytics import PerformanceAnalytics
    
    analytics = PerformanceAnalytics()
    
    analytics.record_trade(
        request.strategy_id,
        {
            "trade_id": request.trade_id,
            "pnl": request.pnl,
            "return_pct": request.return_pct,
            "type": request.trade_type,
            "portfolio_value": request.portfolio_value,
            "timestamp": datetime.utcnow(),
        },
    )
    
    return {"success": True, "trade_id": request.trade_id}


@router.post("/strategy/update")
async def update_strategy_data(request: UpdateStrategyDataRequest) -> Dict[str, Any]:
    """Update strategy metadata for analytics."""
    from ...analytics import PerformanceAnalytics
    
    analytics = PerformanceAnalytics()
    
    analytics.update_strategy_data(
        request.strategy_id,
        {
            "followers": request.followers,
            "aum": request.aum,
            "fees": request.fees,
            "avg_allocation": request.avg_allocation,
        },
    )
    
    analytics.record_follower_change(request.strategy_id, request.followers)
    
    return {"success": True, "strategy_id": request.strategy_id}


@router.get("/alerts")
async def get_degradation_alerts(
    strategy_id: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Get degradation alerts."""
    from ...analytics import PerformanceAnalytics
    
    analytics = PerformanceAnalytics()
    
    alerts = analytics.alerts
    
    if strategy_id:
        alerts = [a for a in alerts if a.strategy_id == strategy_id]
    
    if severity:
        alerts = [a for a in alerts if a.severity == severity]
    
    return [
        {
            "strategy_id": a.strategy_id,
            "alert_type": a.alert_type,
            "severity": a.severity,
            "message": a.message,
            "detected_at": a.detected_at.isoformat(),
        }
        for a in alerts[-limit:]
    ]
