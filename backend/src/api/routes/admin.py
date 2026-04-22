"""
Admin routes for platform management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Dict

from src.config.database import get_db
from src.api.routes.auth import get_current_user
from src.models.user import User
from src.models.portfolio import Portfolio, PortfolioSnapshot
from src.models.transaction import Transaction

router = APIRouter()


async def get_admin_user(current_user: User = Depends(get_current_user)):
    """Dependency to ensure user is admin"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


@router.get("/stats")
async def get_platform_stats(
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get platform statistics"""
    # User stats
    user_count = await db.scalar(select(func.count(User.id)))
    active_users = await db.scalar(
        select(func.count(User.id)).where(User.is_active == True)
    )
    
    # Transaction stats
    total_transactions = await db.scalar(select(func.count(Transaction.id)))
    total_volume = await db.scalar(
        select(func.sum(Transaction.usd_value)).where(Transaction.usd_value.isnot(None))
    ) or 0
    
    # Portfolio stats
    total_portfolios = await db.scalar(select(func.count(Portfolio.id)))
    total_tvl = await db.scalar(
        select(func.sum(Portfolio.usd_value)).where(Portfolio.usd_value.isnot(None))
    ) or 0
    
    return {
        "users": {
            "total": user_count,
            "active": active_users
        },
        "transactions": {
            "total": total_transactions,
            "volume_usd": str(total_volume)
        },
        "portfolio": {
            "total_portfolios": total_portfolios,
            "total_tvl_usd": str(total_tvl)
        }
    }


@router.get("/users")
async def get_all_users(
    limit: int = 50,
    offset: int = 0,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all users (admin only)"""
    result = await db.execute(
        select(User)
        .order_by(User.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    users = result.scalars().all()
    
    return [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_active": user.is_active,
            "is_admin": user.is_admin,
            "created_at": user.created_at,
            "last_login": user.last_login
        }
        for user in users
    ]


@router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: int,
    is_active: bool,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user active status"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = is_active
    await db.commit()
    
    return {"message": f"User {user_id} status updated to {'active' if is_active else 'inactive'}"}


@router.get("/transactions/recent")
async def get_recent_transactions(
    limit: int = 100,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get recent transactions across all users"""
    result = await db.execute(
        select(Transaction)
        .order_by(Transaction.created_at.desc())
        .limit(limit)
    )
    transactions = result.scalars().all()
    
    return [
        {
            "id": tx.id,
            "user_id": tx.user_id,
            "tx_hash": tx.tx_hash,
            "chain_id": tx.chain_id,
            "type": tx.type,
            "status": tx.status,
            "from_token_symbol": tx.from_token_symbol,
            "to_token_symbol": tx.to_token_symbol,
            "usd_value": str(tx.usd_value) if tx.usd_value else None,
            "created_at": tx.created_at
        }
        for tx in transactions
    ]


@router.get("/analytics/volume")
async def get_volume_analytics(
    days: int = 30,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get trading volume analytics"""
    from datetime import datetime, timedelta
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Daily volume
    result = await db.execute(
        select(
            func.date(Transaction.created_at).label('date'),
            func.sum(Transaction.usd_value).label('volume'),
            func.count(Transaction.id).label('count')
        )
        .where(
            Transaction.created_at >= start_date,
            Transaction.usd_value.isnot(None)
        )
        .group_by(func.date(Transaction.created_at))
        .order_by(func.date(Transaction.created_at))
    )
    
    daily_data = result.all()
    
    return {
        "period_days": days,
        "daily_volume": [
            {
                "date": str(row.date),
                "volume_usd": str(row.volume or 0),
                "transaction_count": row.count
            }
            for row in daily_data
        ]
    }


@router.get("/analytics/chains")
async def get_chain_analytics(
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Get analytics by chain"""
    # Transaction count by chain
    tx_result = await db.execute(
        select(
            Transaction.chain_id,
            func.count(Transaction.id).label('tx_count'),
            func.sum(Transaction.usd_value).label('volume')
        )
        .group_by(Transaction.chain_id)
        .order_by(func.count(Transaction.id).desc())
    )
    
    # TVL by chain
    tvl_result = await db.execute(
        select(
            Portfolio.chain_id,
            func.sum(Portfolio.usd_value).label('tvl')
        )
        .group_by(Portfolio.chain_id)
        .order_by(func.sum(Portfolio.usd_value).desc())
    )
    
    chain_names = {
        1: "Ethereum",
        137: "Polygon",
        42161: "Arbitrum", 
        10: "Optimism",
        56: "BSC"
    }
    
    tx_data = tx_result.all()
    tvl_data = {row.chain_id: row.tvl for row in tvl_result.all()}
    
    return {
        "chains": [
            {
                "chain_id": row.chain_id,
                "chain_name": chain_names.get(row.chain_id, f"Chain {row.chain_id}"),
                "transaction_count": row.tx_count,
                "volume_usd": str(row.volume or 0),
                "tvl_usd": str(tvl_data.get(row.chain_id, 0))
            }
            for row in tx_data
        ]
    }


@router.post("/maintenance/cleanup")
async def cleanup_old_data(
    days: int = 90,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Clean up old data (admin only)"""
    from datetime import datetime, timedelta
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Delete old portfolio snapshots
    result = await db.execute(
        select(func.count(PortfolioSnapshot.id))
        .where(PortfolioSnapshot.created_at < cutoff_date)
    )
    old_snapshots = result.scalar()
    
    if old_snapshots > 0:
        await db.execute(
            PortfolioSnapshot.__table__.delete()
            .where(PortfolioSnapshot.created_at < cutoff_date)
        )
        await db.commit()
    
    return {
        "message": f"Cleaned up {old_snapshots} old portfolio snapshots older than {days} days"
    }