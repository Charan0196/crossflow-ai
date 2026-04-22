"""Wallet API Routes"""
from fastapi import APIRouter, HTTPException
from typing import Optional
from pydantic import BaseModel
from src.services.wallet_service import wallet_service
from src.services.trade_history_service import trade_history_service, TradeFilters
from src.services.performance_analytics import performance_analytics_service

router = APIRouter(prefix="/autonomous/wallet", tags=["wallet"])

class SwapExecuteRequest(BaseModel):
    address: str
    from_token: str
    to_token: str
    amount: float
    slippage: float = 0.5

@router.get("/balance")
async def get_balance(address: str = "0x6739659248061A54E0f4de8f2cd60278B69468b3"):
    """Get wallet balance"""
    try:
        balance = await wallet_service.get_balance(address)
        return {
            "address": balance.address,
            "eth_balance": balance.eth_balance,
            "token_balances": [
                {
                    "symbol": t.symbol,
                    "name": t.name,
                    "address": t.address,
                    "balance": t.balance,
                    "usd_value": t.usd_value,
                    "change_24h": t.change_24h
                }
                for t in balance.token_balances
            ],
            "total_value_usd": balance.total_value_usd,
            "last_update": balance.last_update
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/portfolio")
async def get_portfolio(address: str = "0x6739659248061A54E0f4de8f2cd60278B69468b3"):
    """Get portfolio holdings"""
    try:
        balance = await wallet_service.get_balance(address)
        total_value = balance.total_value_usd
        
        allocation = {}
        if total_value > 0:
            allocation["ETH"] = (balance.eth_usd_value / total_value) * 100
            for token in balance.token_balances:
                allocation[token.symbol] = (token.usd_value / total_value) * 100
        
        return {
            "address": address,
            "total_value_usd": total_value,
            "holdings": balance.token_balances,
            "allocation": allocation,
            "change_24h": 0.0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trades")
async def get_trades(
    address: str = "0x6739659248061A54E0f4de8f2cd60278B69468b3",
    page: int = 1,
    page_size: int = 20,
    token: Optional[str] = None,
    trade_type: Optional[str] = None,
    status: Optional[str] = None
):
    """Get trade history"""
    try:
        filters = TradeFilters(token=token, trade_type=trade_type, status=status)
        result = await trade_history_service.get_trades(address, filters, page, page_size)
        
        return {
            "trades": [t.to_dict() for t in result.trades],
            "total": result.total,
            "page": result.page,
            "page_size": result.page_size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics")
async def get_metrics(
    address: str = "0x6739659248061A54E0f4de8f2cd60278B69468b3",
    time_range: str = "all"
):
    """Get performance metrics"""
    try:
        metrics = await performance_analytics_service.calculate_metrics(address, time_range)
        return {
            "total_profit_loss": float(metrics.total_profit_loss),
            "profit_loss_percentage": metrics.profit_loss_percentage,
            "win_rate": metrics.win_rate,
            "total_trades": metrics.total_trades,
            "avg_trade_profit": float(metrics.avg_trade_profit),
            "avg_trade_loss": float(metrics.avg_trade_loss),
            "best_token": metrics.best_token,
            "sharpe_ratio": metrics.sharpe_ratio
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute")
async def execute_swap(request: SwapExecuteRequest):
    """Execute a swap transaction"""
    try:
        import asyncio
        import uuid
        import time
        from datetime import datetime
        
        # Basic validation
        if request.amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be greater than 0")
        
        if request.slippage < 0 or request.slippage > 50:
            raise HTTPException(status_code=400, detail="Slippage must be between 0 and 50")
        
        # Simulate processing time
        await asyncio.sleep(1)
        
        # Generate mock transaction hash
        tx_hash = f"0x{uuid.uuid4().hex}"
        
        # For demo purposes, always return success
        # In a real implementation, this would interact with DEX protocols
        return {
            "success": True,
            "tx_hash": tx_hash,
            "from_token": request.from_token,
            "to_token": request.to_token,
            "amount_in": request.amount,
            "amount_out": request.amount * 0.998,  # Simulate small slippage
            "gas_used": "21000",
            "gas_price": "20",
            "timestamp": datetime.utcnow().isoformat(),
            "network": "sepolia"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }