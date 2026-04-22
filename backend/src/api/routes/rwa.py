"""
RWA Trading API Routes - Phase 4
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from datetime import datetime

router = APIRouter(prefix="/rwa", tags=["RWA Trading"])


class RWATradeRequest(BaseModel):
    token_symbol: str
    direction: str  # buy, sell
    amount: float
    user_address: str


class CrossChainSettlementRequest(BaseModel):
    source_chain: str
    dest_chain: str
    token_symbol: str
    amount: float
    sender: str
    recipient: str


@router.get("/tokens")
async def get_supported_tokens() -> List[Dict[str, Any]]:
    """Get all supported RWA tokens."""
    from ...rwa import RWAIntegration
    
    integration = RWAIntegration()
    tokens = await integration.get_supported_tokens()
    
    return [
        {
            "token_id": t.token_id,
            "symbol": t.symbol,
            "asset_type": t.asset_type.value,
            "chain": t.chain,
            "contract_address": t.contract_address,
            "backing_verified": t.backing_verified,
            "compliance_status": t.compliance_status.value,
            "settlement_delay_hours": t.settlement_delay_hours,
        }
        for t in tokens
    ]


@router.get("/token/{symbol}/price")
async def get_token_price(symbol: str) -> Dict[str, Any]:
    """Get RWA token price."""
    from ...rwa import RWAIntegration
    
    integration = RWAIntegration()
    token = integration.tokens.get(symbol)
    
    if not token:
        raise HTTPException(404, f"Token not found: {symbol}")
    
    quote = await integration.get_price(token)
    
    return {
        "symbol": symbol,
        "price_usd": quote.price_usd,
        "timestamp": quote.timestamp.isoformat(),
        "oracle_source": quote.oracle_source,
        "confidence": quote.confidence,
    }


@router.get("/token/{symbol}/backing")
async def verify_token_backing(symbol: str) -> Dict[str, Any]:
    """Verify RWA token backing."""
    from ...rwa import RWAIntegration
    
    integration = RWAIntegration()
    token = integration.tokens.get(symbol)
    
    if not token:
        raise HTTPException(404, f"Token not found: {symbol}")
    
    verification = await integration.verify_backing(token)
    
    return {
        "symbol": symbol,
        "verified": verification.verified,
        "backing_ratio": verification.backing_ratio,
        "last_audit_date": verification.last_audit_date.isoformat(),
        "auditor": verification.auditor,
        "verification_url": verification.verification_url,
    }


@router.get("/jurisdiction/{user_address}/{symbol}")
async def check_jurisdiction(user_address: str, symbol: str) -> Dict[str, Any]:
    """Check jurisdiction restrictions for user."""
    from ...rwa import RWAIntegration
    
    integration = RWAIntegration()
    token = integration.tokens.get(symbol)
    
    if not token:
        raise HTTPException(404, f"Token not found: {symbol}")
    
    check = await integration.check_jurisdiction(user_address, token)
    
    return {
        "user_address": check.user_address,
        "jurisdiction": check.jurisdiction,
        "allowed": check.allowed,
        "restrictions": check.restrictions,
    }


@router.post("/trade")
async def execute_rwa_trade(request: RWATradeRequest) -> Dict[str, Any]:
    """Execute RWA trade."""
    from ...rwa import RWAIntegration, TradeDirection
    
    integration = RWAIntegration()
    
    direction_map = {
        "buy": TradeDirection.BUY,
        "sell": TradeDirection.SELL,
    }
    
    direction = direction_map.get(request.direction)
    if not direction:
        raise HTTPException(400, f"Invalid direction: {request.direction}")
    
    token = integration.tokens.get(request.token_symbol)
    if not token:
        raise HTTPException(404, f"Token not found: {request.token_symbol}")
    
    # Get current price
    quote = await integration.get_price(token)
    
    # Create and execute trade
    trade = integration.create_trade(
        request.token_symbol,
        direction,
        request.amount,
        request.user_address,
        quote.price_usd,
    )
    
    result = await integration.execute_trade(trade)
    
    if not result.success:
        raise HTTPException(400, result.message)
    
    return {
        "trade_id": result.trade_id,
        "success": result.success,
        "message": result.message,
        "settlement_eta": result.settlement_eta.isoformat() if result.settlement_eta else None,
    }


@router.get("/trade/{trade_id}/status")
async def get_trade_status(trade_id: str) -> Dict[str, Any]:
    """Get RWA trade settlement status."""
    from ...rwa import RWAIntegration
    
    integration = RWAIntegration()
    status = await integration.get_settlement_status(trade_id)
    
    return {
        "trade_id": trade_id,
        "settlement_status": status,
    }


# Cross-chain settlement endpoints
@router.post("/settlement/initiate")
async def initiate_settlement(request: CrossChainSettlementRequest) -> Dict[str, Any]:
    """Initiate cross-chain RWA settlement."""
    from ...rwa import RWAIntegration, SettlementBridge
    
    integration = RWAIntegration()
    bridge = SettlementBridge()
    
    token = integration.tokens.get(request.token_symbol)
    if not token:
        raise HTTPException(404, f"Token not found: {request.token_symbol}")
    
    settlement = bridge.create_settlement(
        request.source_chain,
        request.dest_chain,
        token,
        request.amount,
        request.sender,
        request.recipient,
    )
    
    try:
        settlement_id = await bridge.initiate_settlement(settlement)
        
        return {
            "settlement_id": settlement_id,
            "source_chain": request.source_chain,
            "dest_chain": request.dest_chain,
            "status": "pending",
        }
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/settlement/{settlement_id}/execute")
async def execute_settlement(settlement_id: str) -> Dict[str, Any]:
    """Execute cross-chain settlement."""
    from ...rwa import SettlementBridge
    
    bridge = SettlementBridge()
    settlement = bridge.settlements.get(settlement_id)
    
    if not settlement:
        raise HTTPException(404, "Settlement not found")
    
    result = await bridge.coordinate_atomic_settlement(settlement)
    
    return {
        "settlement_id": result.settlement_id,
        "success": result.success,
        "status": result.status.value,
        "message": result.message,
        "tx_hash": result.tx_hash,
    }


@router.get("/settlement/{settlement_id}/status")
async def get_settlement_status(settlement_id: str) -> Dict[str, Any]:
    """Get settlement status."""
    from ...rwa import SettlementBridge
    
    bridge = SettlementBridge()
    
    try:
        status = await bridge.get_settlement_status(settlement_id)
        return {
            "settlement_id": settlement_id,
            "status": status.value,
        }
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.post("/settlement/{settlement_id}/retry")
async def retry_settlement(settlement_id: str) -> Dict[str, Any]:
    """Retry failed settlement."""
    from ...rwa import SettlementBridge
    
    bridge = SettlementBridge()
    
    try:
        result = await bridge.retry_settlement(settlement_id)
        return {
            "settlement_id": result.settlement_id,
            "success": result.success,
            "status": result.status.value,
        }
    except ValueError as e:
        raise HTTPException(404, str(e))
