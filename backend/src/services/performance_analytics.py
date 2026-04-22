"""
Performance Analytics Service
Calculates trading performance metrics including profit/loss, win rate, and Sharpe ratio
"""
import logging
from typing import Dict, Optional
from decimal import Decimal
from datetime import datetime, timedelta
import math
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.trading import AutonomousTrade
from src.config.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """Performance metrics data structure"""
    def __init__(
        self,
        total_profit_loss: Decimal,
        profit_loss_percentage: float,
        win_rate: float,
        total_trades: int,
        avg_trade_profit: Decimal,
        avg_trade_loss: Decimal,
        best_token: Dict,
        sharpe_ratio: float
    ):
        self.total_profit_loss = total_profit_loss
        self.profit_loss_percentage = profit_loss_percentage
        self.win_rate = win_rate
        self.total_trades = total_trades
        self.avg_trade_profit = avg_trade_profit
        self.avg_trade_loss = avg_trade_loss
        self.best_token = best_token
        self.sharpe_ratio = sharpe_ratio


class PerformanceAnalyticsService:
    """Service for calculating trading performance metrics"""
    
    def _get_time_range_timestamp(self, time_range: str) -> Optional[int]:
        """Convert time range string to timestamp"""
        if time_range == "all":
            return None
        
        now = datetime.utcnow()
        if time_range == "24h":
            start = now - timedelta(hours=24)
        elif time_range == "7d":
            start = now - timedelta(days=7)
        elif time_range == "30d":
            start = now - timedelta(days=30)
        else:
            return None
        
        return int(start.timestamp())
    
    async def calculate_metrics(
        self,
        address: str,
        time_range: str = "all"
    ) -> PerformanceMetrics:
        """
        Calculate all performance metrics
        
        Args:
            address: Wallet address
            time_range: Time range (24h, 7d, 30d, all)
            
        Returns:
            PerformanceMetrics object
        """
        async with AsyncSessionLocal() as session:
            try:
                # Build base query
                query = select(AutonomousTrade).where(
                    and_(
                        AutonomousTrade.wallet_address == address,
                        AutonomousTrade.status == "confirmed"
                    )
                )
                
                # Apply time range filter
                start_timestamp = self._get_time_range_timestamp(time_range)
                if start_timestamp:
                    query = query.where(
                        AutonomousTrade.timestamp >= start_timestamp
                    )
                
                result = await session.execute(query)
                trades = result.scalars().all()
                
                # Calculate metrics
                total_profit_loss = await self.calculate_profit_loss(address, time_range)
                win_rate = await self.calculate_win_rate(address, time_range)
                total_trades = len(trades)
                
                # Calculate average profit and loss
                profitable_trades = [t for t in trades if t.profit_loss and t.profit_loss > 0]
                losing_trades = [t for t in trades if t.profit_loss and t.profit_loss < 0]
                
                avg_trade_profit = Decimal(0)
                if profitable_trades:
                    avg_trade_profit = sum(t.profit_loss for t in profitable_trades) / len(profitable_trades)
                
                avg_trade_loss = Decimal(0)
                if losing_trades:
                    avg_trade_loss = sum(t.profit_loss for t in losing_trades) / len(losing_trades)
                
                # Get best token
                best_token = await self.get_best_token(address, time_range)
                
                # Calculate Sharpe ratio
                sharpe_ratio = await self.calculate_sharpe_ratio(address, time_range)
                
                # Calculate profit/loss percentage (assuming starting value)
                profit_loss_percentage = 0.0
                if total_trades > 0 and total_profit_loss != 0:
                    # Estimate based on average trade size
                    avg_trade_size = sum(float(t.from_amount) for t in trades) / len(trades) if trades else 1
                    profit_loss_percentage = (float(total_profit_loss) / avg_trade_size) * 100
                
                return PerformanceMetrics(
                    total_profit_loss=total_profit_loss,
                    profit_loss_percentage=profit_loss_percentage,
                    win_rate=win_rate,
                    total_trades=total_trades,
                    avg_trade_profit=avg_trade_profit,
                    avg_trade_loss=avg_trade_loss,
                    best_token=best_token,
                    sharpe_ratio=sharpe_ratio
                )
                
            except Exception as e:
                logger.error(f"Failed to calculate metrics: {e}")
                raise
    
    async def calculate_win_rate(self, address: str, time_range: str = "all") -> float:
        """
        Calculate win rate as percentage of profitable trades
        
        Args:
            address: Wallet address
            time_range: Time range
            
        Returns:
            Win rate percentage
        """
        async with AsyncSessionLocal() as session:
            try:
                query = select(AutonomousTrade).where(
                    and_(
                        AutonomousTrade.wallet_address == address,
                        AutonomousTrade.status == "confirmed"
                    )
                )
                
                start_timestamp = self._get_time_range_timestamp(time_range)
                if start_timestamp:
                    query = query.where(
                        AutonomousTrade.timestamp >= start_timestamp
                    )
                
                result = await session.execute(query)
                trades = result.scalars().all()
                
                if not trades:
                    return 0.0
                
                profitable_trades = sum(
                    1 for t in trades
                    if t.profit_loss and t.profit_loss > 0
                )
                
                win_rate = (profitable_trades / len(trades)) * 100
                return win_rate
                
            except Exception as e:
                logger.error(f"Failed to calculate win rate: {e}")
                raise
    
    async def calculate_profit_loss(self, address: str, time_range: str = "all") -> Decimal:
        """
        Calculate total profit/loss
        
        Args:
            address: Wallet address
            time_range: Time range
            
        Returns:
            Total profit/loss
        """
        async with AsyncSessionLocal() as session:
            try:
                query = select(AutonomousTrade).where(
                    and_(
                        AutonomousTrade.wallet_address == address,
                        AutonomousTrade.status == "confirmed"
                    )
                )
                
                start_timestamp = self._get_time_range_timestamp(time_range)
                if start_timestamp:
                    query = query.where(
                        AutonomousTrade.timestamp >= start_timestamp
                    )
                
                result = await session.execute(query)
                trades = result.scalars().all()
                
                total_profit_loss = Decimal(0)
                for trade in trades:
                    if trade.profit_loss:
                        total_profit_loss += trade.profit_loss
                    # Subtract gas fees
                    total_profit_loss -= trade.gas_fee
                
                return total_profit_loss
                
            except Exception as e:
                logger.error(f"Failed to calculate profit/loss: {e}")
                raise
    
    async def get_best_token(self, address: str, time_range: str = "all") -> Dict:
        """
        Identify best performing token
        
        Args:
            address: Wallet address
            time_range: Time range
            
        Returns:
            Dict with symbol and profit
        """
        async with AsyncSessionLocal() as session:
            try:
                query = select(AutonomousTrade).where(
                    and_(
                        AutonomousTrade.wallet_address == address,
                        AutonomousTrade.status == "confirmed"
                    )
                )
                
                start_timestamp = self._get_time_range_timestamp(time_range)
                if start_timestamp:
                    query = query.where(
                        AutonomousTrade.timestamp >= start_timestamp
                    )
                
                result = await session.execute(query)
                trades = result.scalars().all()
                
                # Calculate profit by token
                token_profits = {}
                for trade in trades:
                    # Consider both from and to tokens
                    for token_symbol in [trade.from_token_symbol, trade.to_token_symbol]:
                        if token_symbol not in token_profits:
                            token_profits[token_symbol] = Decimal(0)
                        
                        if trade.profit_loss:
                            token_profits[token_symbol] += trade.profit_loss / 2  # Split profit between both tokens
                
                if not token_profits:
                    return {"symbol": "N/A", "profit": 0}
                
                # Find best token
                best_token_symbol = max(token_profits, key=token_profits.get)
                best_token_profit = token_profits[best_token_symbol]
                
                return {
                    "symbol": best_token_symbol,
                    "profit": float(best_token_profit)
                }
                
            except Exception as e:
                logger.error(f"Failed to get best token: {e}")
                raise
    
    async def calculate_sharpe_ratio(self, address: str, time_range: str = "all") -> float:
        """
        Calculate Sharpe ratio for risk-adjusted returns
        
        Args:
            address: Wallet address
            time_range: Time range
            
        Returns:
            Sharpe ratio
        """
        async with AsyncSessionLocal() as session:
            try:
                query = select(AutonomousTrade).where(
                    and_(
                        AutonomousTrade.wallet_address == address,
                        AutonomousTrade.status == "confirmed"
                    )
                )
                
                start_timestamp = self._get_time_range_timestamp(time_range)
                if start_timestamp:
                    query = query.where(
                        AutonomousTrade.timestamp >= start_timestamp
                    )
                
                result = await session.execute(query)
                trades = result.scalars().all()
                
                if len(trades) < 2:
                    return 0.0
                
                # Calculate returns for each trade
                returns = []
                for trade in trades:
                    if trade.profit_loss and trade.from_amount:
                        trade_return = float(trade.profit_loss) / float(trade.from_amount)
                        returns.append(trade_return)
                
                if not returns:
                    return 0.0
                
                # Calculate mean return
                mean_return = sum(returns) / len(returns)
                
                # Calculate standard deviation
                variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
                std_dev = math.sqrt(variance)
                
                if std_dev == 0:
                    return 0.0
                
                # Sharpe ratio (assuming risk-free rate of 0 for simplicity)
                sharpe_ratio = mean_return / std_dev
                
                return sharpe_ratio
                
            except Exception as e:
                logger.error(f"Failed to calculate Sharpe ratio: {e}")
                raise


# Global instance
performance_analytics_service = PerformanceAnalyticsService()
