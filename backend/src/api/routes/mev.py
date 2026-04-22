"""
MEV Protection API Routes - Phase 3
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from datetime import datetime

router = APIRouter(prefix="/mev", tags=["MEV Protection"])


class TransactionRequest(BaseModel):
    tx_hash: str
    from_address: str
    to_address: str
    value: float
    data: str
    gas_limit: int
    gas_price: float
    chain: str


class MEVRiskRequest(BaseModel):
    tx_hash: str
    value: float
    gas_price: float
    chain: str


@router.post("/route")
async def route_transaction(request: TransactionRequest) -> Dict[str, Any]:
    """Route transaction through private RPC for MEV protection."""
    from ...mev import MEVShield
    from ...mev.mev_shield import Transaction, Chain
    
    shield = MEVShield()
    
    try:
        chain = Chain(request.chain)
    except ValueError:
        raise HTTPException(400, f"Unsupported chain: {request.chain}")
    
    tx = Transaction(
        tx_hash=request.tx_hash,
        from_address=request.from_address,
        to_address=request.to_address,
        value=request.value,
        data=request.data,
        gas_limit=request.gas_limit,
        gas_price=request.gas_price,
        chain=chain,
        nonce=0
    )
    
    result = await shield.route_transaction(tx, chain)
    
    return {
        "submission_id": result.submission_id,
        "private_rpc": result.private_rpc,
        "status": result.status.value,
        "protection_strategy": result.protection_strategy.value
    }


@router.get("/risk/{chain}")
async def get_mev_risk(chain: str, tx_hash: str, value: float, gas_price: float) -> Dict[str, Any]:
    """Get MEV risk score for a transaction."""
    from ...mev import MEVAnalyzer
    
    analyzer = MEVAnalyzer()
    
    risk = await analyzer.get_realtime_risk_score({
        "hash": tx_hash,
        "value": value,
        "gas_price": gas_price,
        "chain": chain
    })
    
    return {
        "transaction_hash": risk.transaction_hash,
        "risk_score": risk.risk_score,
        "risk_level": risk.risk_level.value,
        "attack_vectors": risk.attack_vectors,
        "estimated_exposure": risk.estimated_exposure,
        "recommendations": risk.recommendations
    }


@router.get("/rpc-status/{chain}")
async def get_rpc_status(chain: str) -> List[Dict[str, Any]]:
    """Get status of private RPCs for a chain."""
    from ...mev import MEVShield
    from ...mev.mev_shield import Chain
    
    shield = MEVShield()
    
    try:
        chain_enum = Chain(chain)
    except ValueError:
        raise HTTPException(400, f"Unsupported chain: {chain}")
    
    return await shield.get_private_rpc_status(chain_enum)


@router.get("/savings")
async def get_mev_savings(user: Optional[str] = None) -> Dict[str, Any]:
    """Get total MEV savings."""
    from ...mev import MEVAnalyzer
    
    analyzer = MEVAnalyzer()
    return await analyzer.calculate_total_savings(user)


@router.get("/supported-chains")
async def get_supported_chains() -> Dict[str, bool]:
    """Get chains with MEV protection support."""
    from ...mev import MEVShield
    
    shield = MEVShield()
    return {chain.value: supported for chain, supported in shield.MEV_SUPPORTED_CHAINS.items()}
