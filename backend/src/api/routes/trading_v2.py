"""
Phase 5: Trading API Routes

Endpoints for:
- Swap quotes and execution
- Bridge quotes and execution
- Transaction status tracking
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from decimal import Decimal

from src.config.database import get_db
from src.core.trading_schemas import (
    SwapQuoteRequest, SwapQuoteResponse,
    SwapExecuteRequest, SwapExecuteResponse,
    BridgeQuoteRequest, BridgeQuoteResponse,
    BridgeExecuteRequest, BridgeExecuteResponse,
)
from src.services.dex_aggregator import dex_aggregator
from src.services.cross_chain_router import cross_chain_router
from src.services.advanced_price_oracle import price_oracle
from src.config.phase5_config import phase5_config

router = APIRouter(prefix="/trading/v2", tags=["Trading V2"])


@router.post("/swap/quote", response_model=SwapQuoteResponse)
async def get_swap_quote(request: SwapQuoteRequest):
    """
    Get a swap quote from multiple DEXs
    
    Returns the best available route with price impact and fees
    """
    quote = await dex_aggregator.get_swap_quote(
        from_token=request.from_token,
        to_token=request.to_token,
        amount=Decimal(request.amount),
        chain_id=request.chain_id,
        slippage_tolerance=request.slippage_tolerance,
        user_address=request.user_address
    )
    
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to get quote for this swap"
        )
    
    route = quote.best_route
    return SwapQuoteResponse(
        from_token=request.from_token,
        to_token=request.to_token,
        from_amount=request.amount,
        to_amount=str(route.to_amount),
        to_amount_min=str(route.to_amount_min),
        price_impact=route.price_impact,
        route=route.route_path,
        gas_estimate=route.gas_estimate,
        gas_fee_usd=str(route.gas_fee_usd),
        protocol_fee=str(route.protocol_fee),
        total_fee_usd=str(route.total_fee_usd),
        exchange_rate=str(route.exchange_rate),
        expires_at=quote.expires_at,
        dex_name=route.dex_name
    )


@router.post("/swap/execute", response_model=SwapExecuteResponse)
async def execute_swap(request: SwapExecuteRequest):
    """
    Execute a swap transaction
    
    Returns transaction hash and status
    """
    result = await cross_chain_router.execute_swap(
        from_token=request.from_token,
        to_token=request.to_token,
        amount=Decimal(request.amount),
        chain_id=request.chain_id,
        user_address=request.user_address,
        slippage_tolerance=request.slippage_tolerance,
        deadline=request.deadline
    )
    
    return SwapExecuteResponse(
        tx_hash=result.tx_hash,
        status=result.status.value,
        from_amount=str(result.from_amount),
        to_amount=str(result.to_amount) if result.to_amount else None,
        gas_used=result.gas_used,
        explorer_url=result.explorer_url
    )


@router.post("/swap/simulate")
async def simulate_swap(request: SwapQuoteRequest):
    """
    Simulate a swap transaction before execution
    
    Returns expected output and potential warnings
    """
    result = await cross_chain_router.simulate_swap(
        from_token=request.from_token,
        to_token=request.to_token,
        amount=Decimal(request.amount),
        chain_id=request.chain_id,
        user_address=request.user_address
    )
    
    return result


@router.post("/bridge/quote", response_model=BridgeQuoteResponse)
async def get_bridge_quote(request: BridgeQuoteRequest):
    """
    Get a cross-chain bridge quote
    
    Returns bridge options with fees and estimated time
    """
    quote = await cross_chain_router.get_bridge_quote(
        from_token=request.from_token,
        to_token=request.to_token,
        amount=Decimal(request.amount),
        from_chain_id=request.from_chain_id,
        to_chain_id=request.to_chain_id,
        user_address=request.user_address,
        slippage_tolerance=request.slippage_tolerance
    )
    
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to get bridge quote"
        )
    
    return BridgeQuoteResponse(
        from_token=request.from_token,
        to_token=request.to_token,
        from_chain_id=request.from_chain_id,
        to_chain_id=request.to_chain_id,
        from_amount=request.amount,
        to_amount=str(quote.to_amount),
        bridge_fee=str(quote.bridge_fee),
        gas_fee_usd=str(quote.gas_fee_usd),
        total_fee_usd=str(quote.total_fee_usd),
        estimated_time=quote.estimated_time,
        bridge_name=quote.bridge_name,
        expires_at=int(quote.estimated_time) + 60
    )


@router.post("/bridge/execute", response_model=BridgeExecuteResponse)
async def execute_bridge(request: BridgeExecuteRequest):
    """
    Execute a cross-chain bridge transaction
    """
    result = await cross_chain_router.execute_bridge(
        from_token=request.from_token,
        to_token=request.to_token,
        amount=Decimal(request.amount),
        from_chain_id=request.from_chain_id,
        to_chain_id=request.to_chain_id,
        user_address=request.user_address,
        slippage_tolerance=request.slippage_tolerance
    )
    
    return BridgeExecuteResponse(
        source_tx_hash=result.source_tx_hash,
        status=result.status.value,
        from_amount=str(result.from_amount),
        estimated_arrival=result.estimated_arrival,
        explorer_url=phase5_config.get_explorer_url(
            request.from_chain_id, result.source_tx_hash
        )
    )


@router.get("/transaction/{tx_hash}")
async def get_transaction_status(tx_hash: str):
    """
    Get status of a pending transaction
    """
    result = await cross_chain_router.get_transaction_status(tx_hash)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    return result.to_dict()


@router.get("/bridge/{bridge_id}")
async def get_bridge_status(bridge_id: str):
    """
    Get status of a pending bridge transaction
    """
    result = await cross_chain_router.get_bridge_status(bridge_id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bridge transaction not found"
        )
    
    return result.to_dict()


@router.get("/supported-chains")
async def get_supported_chains():
    """
    Get list of supported blockchain networks
    """
    chains = []
    for chain_id, config in phase5_config.chains.items():
        chains.append({
            "chain_id": chain_id,
            "name": config.name,
            "symbol": config.symbol,
            "native_token": config.native_token,
            "explorer_url": config.explorer_url,
            "supported_dexs": config.supported_dexs
        })
    return {"chains": chains}


@router.get("/supported-tokens/{chain_id}")
async def get_supported_tokens(chain_id: int):
    """
    Get list of supported tokens for a chain
    """
    tokens = await dex_aggregator.get_supported_tokens(chain_id)
    return {"tokens": tokens, "chain_id": chain_id}


@router.get("/price/{symbol}")
async def get_token_price(symbol: str):
    """
    Get current price for a token
    """
    price_data = await price_oracle.get_price(symbol)
    
    if not price_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Price not found for {symbol}"
        )
    
    return price_data.to_dict()


@router.get("/prices")
async def get_multiple_prices(symbols: str):
    """
    Get prices for multiple tokens (comma-separated)
    """
    symbol_list = [s.strip() for s in symbols.split(",")]
    prices = await price_oracle.get_prices(symbol_list)
    
    return {
        symbol: data.to_dict() 
        for symbol, data in prices.items()
    }


@router.get("/arbitrage/{token}")
async def get_arbitrage_opportunities(token: str, amount_usd: float = 1000):
    """
    Get cross-chain arbitrage opportunities for a token
    """
    opportunities = await price_oracle.detect_arbitrage_opportunities(
        token, Decimal(str(amount_usd))
    )
    
    return {
        "token": token,
        "amount_usd": amount_usd,
        "opportunities": [opp.to_dict() for opp in opportunities]
    }
