"""
Phase 5: Order Manager Service

Handles all order types:
- Market orders
- Limit orders
- Stop-loss orders
- Take-profit orders
- Order monitoring and execution
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime, timedelta
from enum import Enum
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from src.models.trading import (
    Order, OrderType, OrderSide, OrderStatus
)
from src.services.advanced_price_oracle import price_oracle
from src.services.cross_chain_router import cross_chain_router

logger = logging.getLogger(__name__)


@dataclass
class OrderEstimate:
    """Estimated costs for an order"""
    from_amount: Decimal
    to_amount_estimate: Decimal
    gas_fee_usd: Decimal
    protocol_fee_usd: Decimal
    total_fee_usd: Decimal
    price_impact: float
    exchange_rate: Decimal


class OrderManager:
    """
    Manages order creation, monitoring, and execution
    """
    
    def __init__(self):
        self._running = False
        self._price_monitor_task: Optional[asyncio.Task] = None
        self._order_callbacks: Dict[str, List[Callable]] = {}
    
    async def start(self) -> None:
        """Start the order manager"""
        self._running = True
        self._price_monitor_task = asyncio.create_task(self._monitor_prices())
        logger.info("Order Manager started")
    
    async def stop(self) -> None:
        """Stop the order manager"""
        self._running = False
        if self._price_monitor_task:
            self._price_monitor_task.cancel()
        logger.info("Order Manager stopped")
    
    async def create_order(
        self,
        db: Session,
        user_id: str,
        order_type: OrderType,
        side: OrderSide,
        from_token: str,
        to_token: str,
        from_token_symbol: str,
        to_token_symbol: str,
        amount: Decimal,
        chain_id: int,
        price: Optional[Decimal] = None,
        trigger_price: Optional[Decimal] = None,
        expires_in: Optional[int] = None
    ) -> Order:
        """
        Create a new order
        
        Args:
            db: Database session
            user_id: User ID
            order_type: Type of order (market, limit, stop_loss, take_profit)
            side: Buy or sell
            from_token: Source token address
            to_token: Destination token address
            from_token_symbol: Source token symbol
            to_token_symbol: Destination token symbol
            amount: Amount to trade
            chain_id: Chain ID
            price: Limit price (for limit orders)
            trigger_price: Trigger price (for stop-loss/take-profit)
            expires_in: Seconds until expiry
        
        Returns:
            Created Order object
        """
        # Calculate expiry
        expires_at = None
        if expires_in:
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        
        # Create order
        order = Order(
            id=str(uuid.uuid4()),
            user_id=user_id,
            order_type=order_type,
            side=side,
            status=OrderStatus.PENDING if order_type == OrderType.MARKET else OrderStatus.OPEN,
            from_token=from_token,
            to_token=to_token,
            from_token_symbol=from_token_symbol,
            to_token_symbol=to_token_symbol,
            amount=amount,
            filled_amount=Decimal("0"),
            price=price,
            trigger_price=trigger_price,
            chain_id=chain_id,
            expires_at=expires_at
        )
        
        db.add(order)
        db.commit()
        db.refresh(order)
        
        # Execute market orders immediately
        if order_type == OrderType.MARKET:
            asyncio.create_task(self._execute_market_order(db, order))
        
        logger.info(f"Created order {order.id} for user {user_id}")
        return order
    
    async def _execute_market_order(self, db: Session, order: Order) -> None:
        """Execute a market order immediately"""
        try:
            # Execute swap
            result = await cross_chain_router.execute_swap(
                from_token=order.from_token,
                to_token=order.to_token,
                amount=order.amount,
                chain_id=order.chain_id,
                user_address="",  # Would come from user wallet
                slippage_tolerance=0.5
            )
            
            # Update order status
            if result.status.value == "confirmed":
                order.status = OrderStatus.FILLED
                order.filled_amount = order.amount
                order.executed_price = result.to_amount / order.amount if result.to_amount else None
                order.tx_hash = result.tx_hash
                order.gas_used = result.gas_used
                order.filled_at = datetime.utcnow()
            else:
                order.status = OrderStatus.FAILED
            
            db.commit()
            
            # Notify callbacks
            await self._notify_order_update(order)
            
        except Exception as e:
            logger.error(f"Market order execution failed: {e}")
            order.status = OrderStatus.FAILED
            db.commit()
    
    async def cancel_order(self, db: Session, order_id: str, user_id: str) -> bool:
        """
        Cancel an open order
        
        Returns:
            True if cancelled successfully
        """
        order = db.query(Order).filter(
            and_(
                Order.id == order_id,
                Order.user_id == user_id,
                Order.status.in_([OrderStatus.OPEN, OrderStatus.PENDING])
            )
        ).first()
        
        if not order:
            return False
        
        order.status = OrderStatus.CANCELLED
        db.commit()
        
        await self._notify_order_update(order)
        logger.info(f"Cancelled order {order_id}")
        return True
    
    def get_user_orders(
        self,
        db: Session,
        user_id: str,
        status: Optional[List[OrderStatus]] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Order]:
        """Get orders for a user"""
        query = db.query(Order).filter(Order.user_id == user_id)
        
        if status:
            query = query.filter(Order.status.in_(status))
        
        return query.order_by(Order.created_at.desc()).offset(offset).limit(limit).all()
    
    def get_open_orders(self, db: Session, user_id: str) -> List[Order]:
        """Get all open orders for a user"""
        return self.get_user_orders(
            db, user_id, 
            status=[OrderStatus.OPEN, OrderStatus.PENDING, OrderStatus.PARTIALLY_FILLED]
        )
    
    def get_order_history(
        self,
        db: Session,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Order]:
        """Get order history for a user"""
        return self.get_user_orders(
            db, user_id,
            status=[OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.FAILED, OrderStatus.EXPIRED],
            limit=limit,
            offset=offset
        )
    
    async def get_order_estimate(
        self,
        from_token: str,
        to_token: str,
        amount: Decimal,
        chain_id: int
    ) -> Optional[OrderEstimate]:
        """
        Get estimated costs for an order
        """
        from src.services.dex_aggregator import dex_aggregator
        
        quote = await dex_aggregator.get_swap_quote(
            from_token, to_token, amount, chain_id
        )
        
        if not quote:
            return None
        
        route = quote.best_route
        return OrderEstimate(
            from_amount=amount,
            to_amount_estimate=route.to_amount,
            gas_fee_usd=route.gas_fee_usd,
            protocol_fee_usd=route.protocol_fee,
            total_fee_usd=route.total_fee_usd,
            price_impact=route.price_impact,
            exchange_rate=route.exchange_rate
        )
    
    async def _monitor_prices(self) -> None:
        """
        Background task to monitor prices and trigger conditional orders
        """
        while self._running:
            try:
                # This would query the database for open conditional orders
                # and check if trigger conditions are met
                await self._check_conditional_orders()
                await asyncio.sleep(5)  # Check every 5 seconds
            except Exception as e:
                logger.error(f"Price monitoring error: {e}")
                await asyncio.sleep(10)
    
    async def _check_conditional_orders(self) -> None:
        """Check and execute conditional orders"""
        # In production, this would:
        # 1. Query all open limit/stop-loss/take-profit orders
        # 2. Get current prices for relevant tokens
        # 3. Execute orders where conditions are met
        pass
    
    async def check_limit_order(
        self, order: Order, current_price: Decimal
    ) -> bool:
        """
        Check if a limit order should be executed
        
        Returns:
            True if order should be executed
        """
        if order.order_type != OrderType.LIMIT or not order.price:
            return False
        
        if order.side == OrderSide.BUY:
            # Buy limit: execute when price <= limit price
            return current_price <= order.price
        else:
            # Sell limit: execute when price >= limit price
            return current_price >= order.price
    
    async def check_stop_loss(
        self, order: Order, current_price: Decimal
    ) -> bool:
        """
        Check if a stop-loss order should be triggered
        
        Returns:
            True if stop-loss should trigger
        """
        if order.order_type != OrderType.STOP_LOSS or not order.trigger_price:
            return False
        
        # Stop-loss triggers when price falls below trigger
        return current_price <= order.trigger_price
    
    async def check_take_profit(
        self, order: Order, current_price: Decimal
    ) -> bool:
        """
        Check if a take-profit order should be triggered
        
        Returns:
            True if take-profit should trigger
        """
        if order.order_type != OrderType.TAKE_PROFIT or not order.trigger_price:
            return False
        
        # Take-profit triggers when price rises above trigger
        return current_price >= order.trigger_price
    
    def register_order_callback(
        self, order_id: str, callback: Callable
    ) -> None:
        """Register callback for order updates"""
        if order_id not in self._order_callbacks:
            self._order_callbacks[order_id] = []
        self._order_callbacks[order_id].append(callback)
    
    async def _notify_order_update(self, order: Order) -> None:
        """Notify registered callbacks of order update"""
        callbacks = self._order_callbacks.get(order.id, [])
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(order)
                else:
                    callback(order)
            except Exception as e:
                logger.error(f"Order callback error: {e}")


# Global order manager instance
order_manager = OrderManager()
