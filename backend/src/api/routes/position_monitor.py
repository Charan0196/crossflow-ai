"""
Position Monitor API Routes
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from ...services.position_monitor_service import position_monitor_service


router = APIRouter(prefix="/position-monitor", tags=["Position Monitor"])


class AddPositionRequest(BaseModel):
    signal_id: str
    token_pair: str
    entry_price: float
    target_price: float
    stop_loss: float
    amount_usd: float
    tokens_bought: float
    network: str
    wallet_address: str
    transaction_hash: str


class ClosePositionRequest(BaseModel):
    position_id: str


@router.get("/positions")
async def get_active_positions():
    """Get all active positions"""
    try:
        positions = await position_monitor_service.get_active_positions()
        
        return {
            "success": True,
            "positions": positions,
            "count": len(positions)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get positions: {str(e)}")


@router.get("/history")
async def get_position_history(limit: int = 20):
    """Get position history"""
    try:
        history = await position_monitor_service.get_position_history(limit)
        
        return {
            "success": True,
            "history": history,
            "count": len(history)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")


@router.get("/summary")
async def get_portfolio_summary():
    """Get portfolio summary"""
    try:
        summary = await position_monitor_service.get_portfolio_summary()
        
        return {
            "success": True,
            "summary": summary
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")


@router.post("/add")
async def add_position(request: AddPositionRequest):
    """Add a new position to monitor"""
    try:
        position_id = await position_monitor_service.add_position(
            signal_id=request.signal_id,
            token_pair=request.token_pair,
            entry_price=request.entry_price,
            target_price=request.target_price,
            stop_loss=request.stop_loss,
            amount_usd=request.amount_usd,
            tokens_bought=request.tokens_bought,
            network=request.network,
            wallet_address=request.wallet_address,
            transaction_hash=request.transaction_hash
        )
        
        return {
            "success": True,
            "position_id": position_id,
            "message": "Position added successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add position: {str(e)}")


@router.post("/close")
async def close_position(request: ClosePositionRequest):
    """Close a position manually"""
    try:
        result = await position_monitor_service.close_position(request.position_id)
        
        if not result['success']:
            raise HTTPException(status_code=404, detail=result['error'])
        
        return {
            "success": True,
            "position_id": request.position_id,
            "final_pnl_usd": result['final_pnl_usd'],
            "final_pnl_percentage": result['final_pnl_percentage'],
            "message": "Position closed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to close position: {str(e)}")


@router.post("/update")
async def update_positions():
    """Manually trigger position updates"""
    try:
        positions = await position_monitor_service.update_positions()
        
        return {
            "success": True,
            "updated_positions": len(positions),
            "message": "Positions updated successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update positions: {str(e)}")