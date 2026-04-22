"""
Trading routes for swaps and bridges
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List

from src.config.database import get_db
from src.api.routes.auth import get_current_user
from src.models.user import User
from src.core.schemas import SwapRequest, SwapResponse, BridgeRequest, BridgeResponse
from src.services.dex_service import dex_service
from src.services.bridge_service import bridge_service
from src.services.web3_service import web3_service

router = APIRouter()


@router.get("/tokens/{chain_id}")
async def get_supported_tokens(chain_id: int):
    """Get supported tokens for a chain"""
    tokens = await dex_service.get_tokens(chain_id)
    if not tokens:
        raise HTTPException(status_code=400, detail="Chain not supported")
    
    return tokens


@router.post("/swap/quote", response_model=Dict)
async def get_swap_quote(
    swap_request: SwapRequest,
    current_user: User = Depends(get_current_user)
):
    """Get swap quote from DEX aggregator"""
    quote = await dex_service.get_quote(
        chain_id=swap_request.chain_id,
        from_token=swap_request.from_token,
        to_token=swap_request.to_token,
        amount=swap_request.amount,
        slippage=swap_request.slippage
    )
    
    if not quote:
        raise HTTPException(status_code=400, detail="Unable to get quote")
    
    return quote


@router.post("/swap/transaction")
async def get_swap_transaction(
    swap_request: SwapRequest,
    from_address: str,
    current_user: User = Depends(get_current_user)
):
    """Get swap transaction data"""
    transaction_data = await dex_service.get_swap_data(
        chain_id=swap_request.chain_id,
        from_token=swap_request.from_token,
        to_token=swap_request.to_token,
        amount=swap_request.amount,
        from_address=from_address,
        slippage=swap_request.slippage
    )
    
    if not transaction_data:
        raise HTTPException(status_code=400, detail="Unable to get transaction data")
    
    return transaction_data


@router.get("/swap/allowance/{chain_id}")
async def check_token_allowance(
    chain_id: int,
    token_address: str,
    wallet_address: str,
    current_user: User = Depends(get_current_user)
):
    """Check token allowance for DEX router"""
    allowance = await dex_service.get_allowance(
        chain_id=chain_id,
        token_address=token_address,
        wallet_address=wallet_address
    )
    
    if not allowance:
        raise HTTPException(status_code=400, detail="Unable to check allowance")
    
    return allowance


@router.post("/swap/approve/{chain_id}")
async def get_approve_transaction(
    chain_id: int,
    token_address: str,
    amount: str = None,
    current_user: User = Depends(get_current_user)
):
    """Get approve transaction data"""
    approve_data = await dex_service.get_approve_transaction(
        chain_id=chain_id,
        token_address=token_address,
        amount=amount
    )
    
    if not approve_data:
        raise HTTPException(status_code=400, detail="Unable to get approve transaction")
    
    return approve_data


@router.get("/bridge/chains")
async def get_bridge_chains(current_user: User = Depends(get_current_user)):
    """Get supported chains for bridging"""
    chains = await bridge_service.get_chains()
    if not chains:
        raise HTTPException(status_code=400, detail="Unable to get chains")
    
    return chains


@router.get("/bridge/tokens")
async def get_bridge_tokens(
    chain_id: int = None,
    current_user: User = Depends(get_current_user)
):
    """Get supported tokens for bridging"""
    tokens = await bridge_service.get_tokens(chain_id)
    if not tokens:
        raise HTTPException(status_code=400, detail="Unable to get tokens")
    
    return tokens


@router.post("/bridge/quote")
async def get_bridge_quote(
    bridge_request: BridgeRequest,
    from_address: str,
    current_user: User = Depends(get_current_user)
):
    """Get bridge quote"""
    quote = await bridge_service.get_quote(
        from_chain=bridge_request.from_chain,
        to_chain=bridge_request.to_chain,
        from_token=bridge_request.from_token,
        to_token=bridge_request.to_token,
        from_amount=bridge_request.amount,
        from_address=from_address,
        to_address=bridge_request.to_address,
        slippage=bridge_request.slippage
    )
    
    if not quote:
        raise HTTPException(status_code=400, detail="Unable to get bridge quote")
    
    return quote


@router.post("/bridge/routes")
async def get_bridge_routes(
    bridge_request: BridgeRequest,
    from_address: str,
    current_user: User = Depends(get_current_user)
):
    """Get available bridge routes"""
    routes = await bridge_service.get_routes(
        from_chain=bridge_request.from_chain,
        to_chain=bridge_request.to_chain,
        from_token=bridge_request.from_token,
        to_token=bridge_request.to_token,
        from_amount=bridge_request.amount,
        from_address=from_address,
        to_address=bridge_request.to_address
    )
    
    if not routes:
        raise HTTPException(status_code=400, detail="Unable to get routes")
    
    return routes


@router.get("/bridge/status")
async def get_bridge_status(
    tx_hash: str,
    bridge: str,
    from_chain: int,
    to_chain: int,
    current_user: User = Depends(get_current_user)
):
    """Get bridge transaction status"""
    status = await bridge_service.get_status(
        tx_hash=tx_hash,
        bridge=bridge,
        from_chain=from_chain,
        to_chain=to_chain
    )
    
    if not status:
        raise HTTPException(status_code=400, detail="Unable to get status")
    
    return status


@router.get("/protocols/{chain_id}")
async def get_dex_protocols(
    chain_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get available DEX protocols for a chain"""
    protocols = await dex_service.get_protocols(chain_id)
    if not protocols:
        raise HTTPException(status_code=400, detail="Unable to get protocols")
    
    return protocols


@router.get("/gas-price/{chain_id}")
async def get_gas_price(
    chain_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get current gas price for a chain"""
    gas_price = await web3_service.estimate_gas_price(chain_id)
    if gas_price is None:
        raise HTTPException(status_code=400, detail="Unable to get gas price")
    
    return {"gas_price": str(gas_price), "chain_id": chain_id}