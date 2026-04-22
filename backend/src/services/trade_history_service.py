"""
Trade History Service
Manages trade records with filtering, pagination, and status updates
"""
import logging
from typing import List, Optional, Dict
from datetime import datetime
from decimal import Decimal
from sqlalchemy import select, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.trading import AutonomousTrade
from src.config.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class TradeFilters:
    """Trade filtering criteria"""
    def __init__(
        self,
        token: Optional[str] = None,
        trade_type: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[int] = None,
        end_date: Optional[int] = None
    ):
        self.token = token
        self.trade_type = trade_type
        self.status = status
        self.start_date = start_date
        self.end_date = end_date


class PaginatedTrades:
    """Paginated trade results"""
    def __init__(self, trades: List[AutonomousTrade], total: int, page: int, page_size: int):
        self.trades = trades
        self.total = total
        self.page = page
        self.page_size = page_size
        self.total_pages = (total + page_size - 1) // page_size


class TradeHistoryService:
    """Service for managing trade history"""
    
    async def record_trade(
        self,
        wallet_address: str,
        tx_hash: str,
        from_token: str,
        to_token: str,
        from_token_symbol: str,
        to_token_symbol: str,
        from_amount: Decimal,
        to_amount: Decimal,
        gas_fee: Decimal,
        slippage: Decimal,
        trade_type: str = "manual",
        profit_loss: Optional[Decimal] = None
    ) -> str:
        """
        Record a new trade
        
        Args:
            wallet_address: Wallet address
            tx_hash: Transaction hash
            from_token: Source token address
            to_token: Destination token address
            from_token_symbol: Source token symbol
            to_token_symbol: Destination token symbol
            from_amount: Amount of source token
            to_amount: Amount of destination token
            gas_fee: Gas fee paid
            slippage: Slippage tolerance
            trade_type: Type of trade (manual or ai_executed)
            profit_loss: Profit/loss amount
            
        Returns:
            Transaction hash
        """
        async with AsyncSessionLocal() as session:
            try:
                trade = AutonomousTrade(
                    wallet_address=wallet_address,
                    tx_hash=tx_hash,
                    timestamp=int(datetime.utcnow().timestamp()),
                    from_token=from_token,
                    to_token=to_token,
                    from_token_symbol=from_token_symbol,
                    to_token_symbol=to_token_symbol,
                    from_amount=from_amount,
                    to_amount=to_amount,
                    gas_fee=gas_fee,
                    slippage=slippage,
                    status="pending",
                    trade_type=trade_type,
                    profit_loss=profit_loss
                )
                
                session.add(trade)
                await session.commit()
                
                logger.info(f"Recorded trade: {tx_hash} ({trade_type})")
                return tx_hash
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to record trade: {e}")
                raise
    
    async def get_trades(
        self,
        address: str,
        filters: Optional[TradeFilters] = None,
        page: int = 1,
        page_size: int = 20
    ) -> PaginatedTrades:
        """
        Get trades with filtering and pagination
        
        Args:
            address: Wallet address
            filters: Filter criteria
            page: Page number (1-indexed)
            page_size: Number of trades per page
            
        Returns:
            PaginatedTrades object
        """
        async with AsyncSessionLocal() as session:
            try:
                # Build query
                query = select(AutonomousTrade).where(
                    AutonomousTrade.wallet_address == address
                )
                
                # Apply filters
                if filters:
                    if filters.token:
                        query = query.where(
                            or_(
                                AutonomousTrade.from_token_symbol == filters.token,
                                AutonomousTrade.to_token_symbol == filters.token
                            )
                        )
                    
                    if filters.trade_type:
                        query = query.where(
                            AutonomousTrade.trade_type == filters.trade_type
                        )
                    
                    if filters.status:
                        query = query.where(
                            AutonomousTrade.status == filters.status
                        )
                    
                    if filters.start_date:
                        query = query.where(
                            AutonomousTrade.timestamp >= filters.start_date
                        )
                    
                    if filters.end_date:
                        query = query.where(
                            AutonomousTrade.timestamp <= filters.end_date
                        )
                
                # Get total count
                count_query = select(AutonomousTrade).where(
                    AutonomousTrade.wallet_address == address
                )
                if filters:
                    # Apply same filters to count
                    if filters.token:
                        count_query = count_query.where(
                            or_(
                                AutonomousTrade.from_token_symbol == filters.token,
                                AutonomousTrade.to_token_symbol == filters.token
                            )
                        )
                    if filters.trade_type:
                        count_query = count_query.where(
                            AutonomousTrade.trade_type == filters.trade_type
                        )
                    if filters.status:
                        count_query = count_query.where(
                            AutonomousTrade.status == filters.status
                        )
                    if filters.start_date:
                        count_query = count_query.where(
                            AutonomousTrade.timestamp >= filters.start_date
                        )
                    if filters.end_date:
                        count_query = count_query.where(
                            AutonomousTrade.timestamp <= filters.end_date
                        )
                
                result = await session.execute(count_query)
                total = len(result.scalars().all())
                
                # Order by timestamp descending (newest first)
                query = query.order_by(desc(AutonomousTrade.timestamp))
                
                # Apply pagination
                offset = (page - 1) * page_size
                query = query.offset(offset).limit(page_size)
                
                # Execute query
                result = await session.execute(query)
                trades = result.scalars().all()
                
                return PaginatedTrades(
                    trades=trades,
                    total=total,
                    page=page,
                    page_size=page_size
                )
                
            except Exception as e:
                logger.error(f"Failed to get trades: {e}")
                raise
    
    async def get_trade_by_hash(self, tx_hash: str) -> Optional[AutonomousTrade]:
        """
        Get a single trade by transaction hash
        
        Args:
            tx_hash: Transaction hash
            
        Returns:
            AutonomousTrade or None
        """
        async with AsyncSessionLocal() as session:
            try:
                query = select(AutonomousTrade).where(
                    AutonomousTrade.tx_hash == tx_hash
                )
                result = await session.execute(query)
                trade = result.scalar_one_or_none()
                
                return trade
                
            except Exception as e:
                logger.error(f"Failed to get trade by hash: {e}")
                raise
    
    async def update_trade_status(
        self,
        tx_hash: str,
        status: str,
        profit_loss: Optional[Decimal] = None
    ) -> None:
        """
        Update trade status
        
        Args:
            tx_hash: Transaction hash
            status: New status (pending, confirmed, failed)
            profit_loss: Optional profit/loss amount
        """
        async with AsyncSessionLocal() as session:
            try:
                query = select(AutonomousTrade).where(
                    AutonomousTrade.tx_hash == tx_hash
                )
                result = await session.execute(query)
                trade = result.scalar_one_or_none()
                
                if trade:
                    trade.status = status
                    if profit_loss is not None:
                        trade.profit_loss = profit_loss
                    
                    await session.commit()
                    logger.info(f"Updated trade {tx_hash} status to {status}")
                else:
                    logger.warning(f"Trade not found: {tx_hash}")
                    
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to update trade status: {e}")
                raise
    
    async def update_trade_gas_fee(
        self,
        tx_hash: str,
        gas_fee: Decimal
    ) -> None:
        """
        Update trade gas fee
        
        Args:
            tx_hash: Transaction hash
            gas_fee: Gas fee amount
        """
        async with AsyncSessionLocal() as session:
            try:
                query = select(AutonomousTrade).where(
                    AutonomousTrade.tx_hash == tx_hash
                )
                result = await session.execute(query)
                trade = result.scalar_one_or_none()
                
                if trade:
                    trade.gas_fee = gas_fee
                    await session.commit()
                    logger.info(f"Updated trade {tx_hash} gas fee to {gas_fee}")
                else:
                    logger.warning(f"Trade not found: {tx_hash}")
                    
            except Exception as e:
                await session.rollback()
                logger.error(f"Failed to update trade gas fee: {e}")
                raise


# Global instance
trade_history_service = TradeHistoryService()
