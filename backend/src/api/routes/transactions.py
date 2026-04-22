"""
Phase 5: Transaction History API Routes
"""

from fastapi import APIRouter, HTTPException, Query, Response
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from decimal import Decimal

from src.services.transaction_history import (
    transaction_history_service,
    TransactionType
)

router = APIRouter(prefix="/transactions", tags=["transactions"])


class TransactionFilter(BaseModel):
    tx_type: Optional[str] = None
    chain_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


@router.get("/")
async def get_transactions(
    user_address: str,
    tx_type: Optional[str] = None,
    chain_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(default=50, le=500),
    offset: int = 0
):
    """Get transaction history for a user."""
    tx_type_enum = TransactionType(tx_type) if tx_type else None
    
    transactions = await transaction_history_service.get_user_transactions(
        user_address=user_address,
        tx_type=tx_type_enum,
        chain_id=chain_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset
    )
    
    return {
        "transactions": [
            {
                "id": tx.id,
                "tx_hash": tx.tx_hash,
                "chain_id": tx.chain_id,
                "type": tx.tx_type.value,
                "from_token": tx.from_token,
                "to_token": tx.to_token,
                "from_amount": str(tx.from_amount),
                "to_amount": str(tx.to_amount),
                "value_usd": str(tx.from_amount * tx.from_price_usd),
                "gas_cost_usd": str(tx.gas_cost_usd),
                "timestamp": tx.timestamp.isoformat(),
                "status": tx.status,
                "explorer_url": tx.explorer_url
            }
            for tx in transactions
        ],
        "count": len(transactions)
    }


@router.get("/pnl")
async def get_pnl(
    user_address: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """Get P&L calculation for a user."""
    pnl = await transaction_history_service.calculate_pnl(
        user_address=user_address,
        start_date=start_date,
        end_date=end_date
    )
    return pnl


@router.get("/export")
async def export_transactions(
    user_address: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """Export transactions as CSV."""
    csv_content = await transaction_history_service.export_csv(
        user_address=user_address,
        start_date=start_date,
        end_date=end_date
    )
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=transactions_{user_address[:8]}.csv"
        }
    )
