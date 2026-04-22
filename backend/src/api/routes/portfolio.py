"""
Portfolio management routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Dict
import json
from decimal import Decimal

from src.config.database import get_db
from src.api.routes.auth import get_current_user
from src.models.user import User
from src.models.portfolio import Portfolio, PortfolioSnapshot
from src.models.transaction import Transaction
from src.core.schemas import PortfolioItem, PortfolioSummary, TransactionCreate, TransactionResponse
from src.services.web3_service import web3_service
from src.services.price_service import price_service

router = APIRouter()


@router.get("/balance/{chain_id}")
async def get_portfolio_balance(
    chain_id: int,
    address: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get portfolio balance for a specific chain and address"""
    try:
        # Get native token balance
        native_balance = await web3_service.get_native_balance(address, chain_id)
        
        # Get native token price
        native_price = await price_service.get_price_by_address("native", chain_id)
        native_usd_value = native_balance * (native_price or Decimal('0'))
        
        # Get existing portfolio items for this user and chain
        result = await db.execute(
            select(Portfolio).where(
                Portfolio.user_id == current_user.id,
                Portfolio.chain_id == chain_id
            )
        )
        portfolio_items = result.scalars().all()
        
        # Update or create native token portfolio item
        native_portfolio = None
        for item in portfolio_items:
            if item.token_address == "native":
                native_portfolio = item
                break
        
        if not native_portfolio:
            native_portfolio = Portfolio(
                user_id=current_user.id,
                chain_id=chain_id,
                token_address="native",
                token_symbol=get_native_symbol(chain_id),
                token_name=get_native_name(chain_id),
                token_decimals=18
            )
            db.add(native_portfolio)
        
        native_portfolio.balance = native_balance
        native_portfolio.usd_value = native_usd_value
        
        await db.commit()
        
        return {
            "chain_id": chain_id,
            "address": address,
            "native_balance": str(native_balance),
            "native_usd_value": str(native_usd_value),
            "tokens": []  # TODO: Add ERC20 token balances
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error getting balance: {str(e)}")


@router.get("/summary", response_model=PortfolioSummary)
async def get_portfolio_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get portfolio summary across all chains"""
    result = await db.execute(
        select(Portfolio).where(Portfolio.user_id == current_user.id)
    )
    portfolio_items = result.scalars().all()
    
    total_usd_value = Decimal('0')
    chain_breakdown = {}
    
    for item in portfolio_items:
        total_usd_value += item.usd_value
        
        chain_key = str(item.chain_id)
        if chain_key not in chain_breakdown:
            chain_breakdown[chain_key] = Decimal('0')
        chain_breakdown[chain_key] += item.usd_value
    
    # Get top tokens by value
    top_tokens = sorted(portfolio_items, key=lambda x: x.usd_value, reverse=True)[:10]
    
    return PortfolioSummary(
        total_usd_value=total_usd_value,
        chain_breakdown=chain_breakdown,
        top_tokens=top_tokens
    )


@router.post("/refresh/{chain_id}")
async def refresh_portfolio(
    chain_id: int,
    address: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Refresh portfolio data for a specific chain"""
    try:
        # This would typically scan for all tokens held by the address
        # For now, we'll just update the native token balance
        await get_portfolio_balance(chain_id, address, current_user, db)
        
        return {"message": f"Portfolio refreshed for chain {chain_id}"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error refreshing portfolio: {str(e)}")


@router.post("/transactions", response_model=TransactionResponse)
async def create_transaction(
    transaction_data: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new transaction record"""
    transaction = Transaction(
        user_id=current_user.id,
        tx_hash=transaction_data.tx_hash,
        chain_id=transaction_data.chain_id,
        type=transaction_data.type,
        from_token_address=transaction_data.from_token_address,
        from_token_symbol=transaction_data.from_token_symbol,
        from_amount=transaction_data.from_amount,
        to_token_address=transaction_data.to_token_address,
        to_token_symbol=transaction_data.to_token_symbol,
        to_amount=transaction_data.to_amount,
        to_chain_id=transaction_data.to_chain_id
    )
    
    db.add(transaction)
    await db.commit()
    await db.refresh(transaction)
    
    return transaction


@router.get("/transactions", response_model=List[TransactionResponse])
async def get_transactions(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's transaction history"""
    result = await db.execute(
        select(Transaction)
        .where(Transaction.user_id == current_user.id)
        .order_by(Transaction.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    transactions = result.scalars().all()
    
    return transactions


@router.get("/transactions/{tx_hash}")
async def get_transaction_status(
    tx_hash: str,
    chain_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get transaction status from blockchain"""
    receipt = await web3_service.get_transaction_receipt(tx_hash, chain_id)
    
    if not receipt:
        return {"status": "pending", "tx_hash": tx_hash}
    
    return {
        "status": "confirmed" if receipt.get("status") == 1 else "failed",
        "tx_hash": tx_hash,
        "block_number": receipt.get("blockNumber"),
        "gas_used": str(receipt.get("gasUsed", 0)),
        "receipt": receipt
    }


@router.post("/snapshot")
async def create_portfolio_snapshot(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a portfolio snapshot for historical tracking"""
    # Get current portfolio summary
    summary = await get_portfolio_summary(current_user, db)
    
    snapshot = PortfolioSnapshot(
        user_id=current_user.id,
        total_usd_value=summary.total_usd_value,
        chain_breakdown=json.dumps({k: str(v) for k, v in summary.chain_breakdown.items()}),
        token_breakdown=json.dumps({})  # TODO: Add token breakdown
    )
    
    db.add(snapshot)
    await db.commit()
    
    return {"message": "Portfolio snapshot created", "total_value": str(summary.total_usd_value)}


def get_native_symbol(chain_id: int) -> str:
    """Get native token symbol for chain"""
    symbols = {
        1: "ETH",
        137: "MATIC", 
        42161: "ETH",
        10: "ETH",
        56: "BNB"
    }
    return symbols.get(chain_id, "UNKNOWN")


def get_native_name(chain_id: int) -> str:
    """Get native token name for chain"""
    names = {
        1: "Ethereum",
        137: "Polygon",
        42161: "Ethereum",
        10: "Ethereum", 
        56: "Binance Coin"
    }
    return names.get(chain_id, "Unknown")