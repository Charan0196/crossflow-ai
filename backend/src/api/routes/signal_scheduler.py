"""
Signal Scheduler API Routes
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

from src.services.signal_scheduler import signal_scheduler

router = APIRouter(prefix="/api/signals", tags=["Signal Scheduler"])


@router.get("/latest")
async def get_latest_signals(limit: int = 10):
    """
    Get latest generated trading signals
    
    Args:
        limit: Maximum number of signals to return
    
    Returns:
        List of latest signals sorted by confidence
    """
    try:
        signals = signal_scheduler.get_latest_signals(limit=limit)
        return {
            "success": True,
            "signals": signals,
            "count": len(signals)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/token/{token}")
async def get_signal_for_token(token: str):
    """
    Get latest signal for a specific token
    
    Args:
        token: Token symbol (e.g., "BTC", "ETH")
    
    Returns:
        Latest signal for the token
    """
    try:
        signal = signal_scheduler.get_signal_for_token(token.upper())
        
        if not signal:
            return {
                "success": False,
                "message": f"No signal available for {token}"
            }
        
        return {
            "success": True,
            "signal": signal
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_signal_history(limit: int = 100):
    """
    Get signal generation history
    
    Args:
        limit: Maximum number of historical signals to return
    
    Returns:
        List of historical signals
    """
    try:
        history = signal_scheduler.get_signal_history(limit=limit)
        return {
            "success": True,
            "history": history,
            "count": len(history)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_scheduler_stats():
    """
    Get signal scheduler statistics
    
    Returns:
        Scheduler status and statistics
    """
    try:
        stats = signal_scheduler.get_stats()
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate")
async def trigger_signal_generation():
    """
    Manually trigger signal generation for all tokens
    
    Returns:
        Success message
    """
    try:
        await signal_scheduler.generate_all_signals()
        return {
            "success": True,
            "message": "Signal generation triggered successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/demo")
async def create_demo_signals():
    """Create demo signals for testing auto trading"""
    try:
        from src.ai.signal_generator import TradingSignal, SignalType, SignalStrength
        from decimal import Decimal
        from datetime import datetime, timedelta
        
        demo_signals = [
            {"token": "BTC", "signal_type": "buy", "confidence": 85.0},
            {"token": "ETH", "signal_type": "buy", "confidence": 78.0}, 
            {"token": "SOL", "signal_type": "strong_buy", "confidence": 92.0},
            {"token": "BNB", "signal_type": "sell", "confidence": 72.0},
            {"token": "XRP", "signal_type": "buy", "confidence": 75.0}
        ]
        
        for signal_data in demo_signals:
            signal = TradingSignal(
                token=signal_data["token"],
                signal_type=SignalType(signal_data["signal_type"]),
                confidence=signal_data["confidence"],
                strength=SignalStrength.MODERATE,
                target_price=Decimal("50000"),  # Mock target
                stop_loss=Decimal("48000"),     # Mock stop loss
                take_profit=Decimal("55000"),   # Mock take profit
                timeframe="15m",
                explanation=f"Demo signal for {signal_data['token']}",
                factors=[],
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(hours=1)
            )
            signal_scheduler.latest_signals[signal_data["token"]] = signal
            signal_scheduler.signal_history.append({
                "timestamp": datetime.utcnow().isoformat(),
                "token": signal_data["token"],
                "signal_type": signal_data["signal_type"],
                "confidence": signal_data["confidence"],
                "timeframe": "15m"
            })
        
        return {
            "success": True,
            "message": f"Created {len(demo_signals)} demo signals",
            "signals": demo_signals
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Check if signal scheduler is running"""
    try:
        stats = signal_scheduler.get_stats()
        return {
            "success": True,
            "status": "running" if stats["is_running"] else "stopped",
            "active_tokens": stats["active_tokens"],
            "signals_count": stats["latest_signals_count"]
        }
    except Exception as e:
        return {
            "success": False,
            "status": "error",
            "error": str(e)
        }
