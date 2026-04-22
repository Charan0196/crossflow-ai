"""
Auto Trading API Routes

API endpoints for automated mock trading system
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

from src.services.auto_trader import auto_trader
from src.config.database import get_db

router = APIRouter(prefix="/api/auto-trading")


class TradingSettings(BaseModel):
    """Trading settings update model"""
    min_confidence: Optional[float] = None
    max_position_size: Optional[float] = None
    stop_loss_pct: Optional[float] = None
    take_profit_pct: Optional[float] = None


class TradingResponse(BaseModel):
    """Standard trading response"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


@router.get("/status", response_model=Dict[str, Any])
async def get_trading_status():
    """Get current auto trading status"""
    try:
        return {
            "success": True,
            "data": {
                "is_enabled": auto_trader.is_enabled,
                "portfolio": auto_trader.get_portfolio_summary(),
                "stats": auto_trader.get_trading_stats(),
                "active_positions": auto_trader.get_active_positions()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/portfolio", response_model=Dict[str, Any])
async def get_portfolio():
    """Get current portfolio summary"""
    try:
        return {
            "success": True,
            "data": auto_trader.get_portfolio_summary()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trades/recent", response_model=Dict[str, Any])
async def get_recent_trades(limit: int = 20):
    """Get recent trades"""
    try:
        return {
            "success": True,
            "data": {
                "trades": auto_trader.get_recent_trades(limit=limit),
                "total_trades": auto_trader.portfolio.trades_count
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/positions/active", response_model=Dict[str, Any])
async def get_active_positions():
    """Get active trading positions"""
    try:
        return {
            "success": True,
            "data": {
                "positions": auto_trader.get_active_positions(),
                "total_positions": len(auto_trader.active_trades)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=Dict[str, Any])
async def get_trading_stats():
    """Get detailed trading statistics"""
    try:
        return {
            "success": True,
            "data": auto_trader.get_trading_stats()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enable", response_model=TradingResponse)
async def enable_trading():
    """Enable automated trading"""
    try:
        auto_trader.enable_trading()
        return TradingResponse(
            success=True,
            message="Automated trading enabled successfully",
            data={"is_enabled": auto_trader.is_enabled}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/disable", response_model=TradingResponse)
async def disable_trading():
    """Disable automated trading"""
    try:
        auto_trader.disable_trading()
        return TradingResponse(
            success=True,
            message="Automated trading disabled successfully",
            data={"is_enabled": auto_trader.is_enabled}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/settings", response_model=TradingResponse)
async def update_settings(settings: TradingSettings):
    """Update trading settings"""
    try:
        settings_dict = settings.dict(exclude_none=True)
        
        # Validate settings
        if "min_confidence" in settings_dict:
            if not 0 <= settings_dict["min_confidence"] <= 100:
                raise HTTPException(status_code=400, detail="min_confidence must be between 0 and 100")
        
        if "max_position_size" in settings_dict:
            if not 0 < settings_dict["max_position_size"] <= 1:
                raise HTTPException(status_code=400, detail="max_position_size must be between 0 and 1")
        
        if "stop_loss_pct" in settings_dict:
            if not 0 < settings_dict["stop_loss_pct"] <= 0.5:
                raise HTTPException(status_code=400, detail="stop_loss_pct must be between 0 and 0.5")
        
        if "take_profit_pct" in settings_dict:
            if not 0 < settings_dict["take_profit_pct"] <= 1:
                raise HTTPException(status_code=400, detail="take_profit_pct must be between 0 and 1")
        
        auto_trader.update_settings(settings_dict)
        
        return TradingResponse(
            success=True,
            message="Trading settings updated successfully",
            data=auto_trader.get_trading_stats()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset", response_model=TradingResponse)
async def reset_portfolio():
    """Reset portfolio to initial state"""
    try:
        # Reset portfolio
        auto_trader.portfolio = auto_trader.__class__().portfolio
        auto_trader.active_trades.clear()
        auto_trader.trade_history.clear()
        auto_trader.stats = {
            "total_trades": 0,
            "profitable_trades": 0,
            "total_profit": 0.0,
            "max_drawdown": 0.0,
            "sharpe_ratio": 0.0,
            "started_at": datetime.utcnow()
        }
        
        return TradingResponse(
            success=True,
            message="Portfolio reset to initial state successfully",
            data=auto_trader.get_portfolio_summary()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance", response_model=Dict[str, Any])
async def get_performance_metrics():
    """Get detailed performance metrics"""
    try:
        portfolio = auto_trader.get_portfolio_summary()
        stats = auto_trader.get_trading_stats()
        
        return {
            "success": True,
            "data": {
                "portfolio_value": portfolio["total_value"],
                "profit_loss": portfolio["profit_loss"],
                "roi_percentage": portfolio["roi_percentage"],
                "win_rate": portfolio["win_rate"],
                "total_trades": portfolio["trades_count"],
                "winning_trades": portfolio["winning_trades"],
                "losing_trades": portfolio["losing_trades"],
                "is_enabled": stats["is_enabled"],
                "started_at": stats["started_at"]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trades/history", response_model=Dict[str, Any])
async def get_trade_history(
    limit: int = 50,
    token: Optional[str] = None,
    trade_type: Optional[str] = None
):
    """Get filtered trade history"""
    try:
        trades = auto_trader.get_recent_trades(limit=1000)  # Get more for filtering
        
        # Apply filters
        if token:
            trades = [t for t in trades if t["token"].upper() == token.upper()]
        
        if trade_type:
            trades = [t for t in trades if t["trade_type"] == trade_type.lower()]
        
        # Apply limit after filtering
        trades = trades[:limit]
        
        return {
            "success": True,
            "data": {
                "trades": trades,
                "total_count": len(trades),
                "filters": {
                    "token": token,
                    "trade_type": trade_type,
                    "limit": limit
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Health check for auto trading system"""
    try:
        return {
            "success": True,
            "data": {
                "status": "healthy",
                "is_enabled": auto_trader.is_enabled,
                "portfolio_value": str(auto_trader.portfolio.total_value),
                "active_positions": len(auto_trader.active_trades),
                "total_trades": auto_trader.portfolio.trades_count,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))