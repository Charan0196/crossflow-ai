"""
AI Trading API Routes
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
import logging

from src.services.ai_trading_service import ai_trading_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/autonomous/ai", tags=["ai-trading"])


class AIStatusResponse(BaseModel):
    """AI trading status response"""
    is_running: bool
    confidence_threshold: int
    signal_interval: int
    wallet_address: str


class ToggleRequest(BaseModel):
    """Toggle AI trading request"""
    enabled: bool
    wallet_key: Optional[str] = None


class SignalResponse(BaseModel):
    """AI signal response"""
    signals: List[Dict]
    count: int


@router.get("/status")
async def get_ai_status() -> AIStatusResponse:
    """Get AI trading status"""
    try:
        return AIStatusResponse(
            is_running=ai_trading_service.is_running,
            confidence_threshold=ai_trading_service.CONFIDENCE_THRESHOLD,
            signal_interval=ai_trading_service.SIGNAL_INTERVAL,
            wallet_address=ai_trading_service.demo_wallet_address
        )
    except Exception as e:
        logger.error(f"Failed to get AI status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/toggle")
async def toggle_ai_trading(request: ToggleRequest) -> Dict:
    """Enable or disable AI trading"""
    try:
        if request.enabled:
            # Set wallet key if provided
            if request.wallet_key:
                ai_trading_service.set_demo_wallet(request.wallet_key)
            
            # Start AI trading
            await ai_trading_service.start()
            
            return {
                "success": True,
                "message": "AI trading enabled",
                "is_running": True
            }
        else:
            # Stop AI trading
            await ai_trading_service.stop()
            
            return {
                "success": True,
                "message": "AI trading disabled",
                "is_running": False
            }
            
    except Exception as e:
        logger.error(f"Failed to toggle AI trading: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/signals")
async def get_ai_signals(limit: int = 10) -> SignalResponse:
    """Get recent AI signals"""
    try:
        # Import here to avoid circular dependency
        from src.models.trading import AISignal
        from src.config.database import AsyncSessionLocal
        from sqlalchemy import select, desc
        
        async with AsyncSessionLocal() as session:
            query = select(AISignal).order_by(
                desc(AISignal.timestamp)
            ).limit(limit)
            
            result = await session.execute(query)
            signals = result.scalars().all()
            
            signal_list = [
                {
                    "id": signal.id,
                    "timestamp": signal.timestamp,
                    "action": signal.action,
                    "token": signal.token,
                    "confidence": float(signal.confidence),
                    "reason": signal.reason,
                    "executed": signal.executed,
                    "trade_id": signal.trade_id
                }
                for signal in signals
            ]
            
            return SignalResponse(
                signals=signal_list,
                count=len(signal_list)
            )
            
    except Exception as e:
        logger.error(f"Failed to get AI signals: {e}")
        raise HTTPException(status_code=500, detail=str(e))
