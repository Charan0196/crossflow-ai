"""
Phase 5: Orders API Routes

Endpoints for:
- Order creation (market, limit, stop-loss, take-profit)
- Order management (cancel, list)
- Order history
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal

from src.config.database import get_db
from src.core.trading_schemas import (
    CreateOrderRequest, OrderResponse, OrderListResponse
)
from src.models.trading import Order, OrderType, OrderSide, OrderStatus
from src.services.order_manager import order_manager

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/", response_model=OrderResponse)
async def create_order(
    request: CreateOrderRequest,
    user_id: str = "demo_user",  # Would come from auth
    db: Session = Depends(get_db)
):
    """
    Create a new order
    
    Supported order types:
    - market: Execute immediately at best price
    - limit: Execute when price reaches specified level
    - stop_loss: Sell when price falls below trigger
    - take_profit: Sell when price rises above trigger
    """
    # Map string to enum
    order_type = OrderType(request.order_type.value)
    side = OrderSide(request.side.value)
    
    # Get token symbols (would normally look up from token address)
    from_symbol = request.from_token[:6] if request.from_token.startswith("0x") else request.from_token
    to_symbol = request.to_token[:6] if request.to_token.startswith("0x") else request.to_token
    
    order = await order_manager.create_order(
        db=db,
        user_id=user_id,
        order_type=order_type,
        side=side,
        from_token=request.from_token,
        to_token=request.to_token,
        from_token_symbol=from_symbol,
        to_token_symbol=to_symbol,
        amount=Decimal(request.amount),
        chain_id=request.chain_id,
        price=Decimal(request.price) if request.price else None,
        trigger_price=Decimal(request.trigger_price) if request.trigger_price else None,
        expires_in=request.expires_in
    )
    
    return _order_to_response(order)


@router.get("/", response_model=OrderListResponse)
async def list_orders(
    status_filter: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    user_id: str = "demo_user",  # Would come from auth
    db: Session = Depends(get_db)
):
    """
    List orders for the current user
    
    Args:
        status_filter: Filter by status (open, filled, cancelled, etc.)
        page: Page number
        page_size: Items per page
    """
    # Parse status filter
    status_list = None
    if status_filter:
        if status_filter == "open":
            status_list = [OrderStatus.OPEN, OrderStatus.PENDING, OrderStatus.PARTIALLY_FILLED]
        elif status_filter == "closed":
            status_list = [OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.FAILED, OrderStatus.EXPIRED]
        else:
            try:
                status_list = [OrderStatus(status_filter)]
            except ValueError:
                pass
    
    offset = (page - 1) * page_size
    orders = order_manager.get_user_orders(
        db=db,
        user_id=user_id,
        status=status_list,
        limit=page_size,
        offset=offset
    )
    
    # Get total count
    total = db.query(Order).filter(Order.user_id == user_id).count()
    
    return OrderListResponse(
        orders=[_order_to_response(o) for o in orders],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/open", response_model=OrderListResponse)
async def list_open_orders(
    user_id: str = "demo_user",  # Would come from auth
    db: Session = Depends(get_db)
):
    """
    List all open orders for the current user
    """
    orders = order_manager.get_open_orders(db=db, user_id=user_id)
    
    return OrderListResponse(
        orders=[_order_to_response(o) for o in orders],
        total=len(orders),
        page=1,
        page_size=len(orders)
    )


@router.get("/history", response_model=OrderListResponse)
async def get_order_history(
    page: int = 1,
    page_size: int = 50,
    user_id: str = "demo_user",  # Would come from auth
    db: Session = Depends(get_db)
):
    """
    Get order history (filled, cancelled, failed orders)
    """
    offset = (page - 1) * page_size
    orders = order_manager.get_order_history(
        db=db,
        user_id=user_id,
        limit=page_size,
        offset=offset
    )
    
    return OrderListResponse(
        orders=[_order_to_response(o) for o in orders],
        total=len(orders),
        page=page,
        page_size=page_size
    )


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    user_id: str = "demo_user",  # Would come from auth
    db: Session = Depends(get_db)
):
    """
    Get details of a specific order
    """
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == user_id
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return _order_to_response(order)


@router.delete("/{order_id}")
async def cancel_order(
    order_id: str,
    user_id: str = "demo_user",  # Would come from auth
    db: Session = Depends(get_db)
):
    """
    Cancel an open order
    """
    success = await order_manager.cancel_order(
        db=db,
        order_id=order_id,
        user_id=user_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to cancel order. Order may not exist or is already filled."
        )
    
    return {"message": "Order cancelled", "order_id": order_id}


@router.post("/{order_id}/estimate")
async def get_order_estimate(
    order_id: str,
    user_id: str = "demo_user",  # Would come from auth
    db: Session = Depends(get_db)
):
    """
    Get fee estimate for an order
    """
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == user_id
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    estimate = await order_manager.get_order_estimate(
        from_token=order.from_token,
        to_token=order.to_token,
        amount=order.amount,
        chain_id=order.chain_id
    )
    
    if not estimate:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to get estimate"
        )
    
    return {
        "from_amount": str(estimate.from_amount),
        "to_amount_estimate": str(estimate.to_amount_estimate),
        "gas_fee_usd": str(estimate.gas_fee_usd),
        "protocol_fee_usd": str(estimate.protocol_fee_usd),
        "total_fee_usd": str(estimate.total_fee_usd),
        "price_impact": estimate.price_impact,
        "exchange_rate": str(estimate.exchange_rate)
    }


def _order_to_response(order: Order) -> OrderResponse:
    """Convert Order model to OrderResponse"""
    return OrderResponse(
        id=order.id,
        order_type=order.order_type.value,
        side=order.side.value,
        status=order.status.value,
        from_token=order.from_token,
        to_token=order.to_token,
        from_token_symbol=order.from_token_symbol,
        to_token_symbol=order.to_token_symbol,
        amount=str(order.amount),
        filled_amount=str(order.filled_amount),
        price=str(order.price) if order.price else None,
        trigger_price=str(order.trigger_price) if order.trigger_price else None,
        executed_price=str(order.executed_price) if order.executed_price else None,
        chain_id=order.chain_id,
        tx_hash=order.tx_hash,
        protocol_fee=str(order.protocol_fee),
        gas_fee=str(order.gas_fee),
        created_at=order.created_at.isoformat() if order.created_at else "",
        filled_at=order.filled_at.isoformat() if order.filled_at else None,
        expires_at=order.expires_at.isoformat() if order.expires_at else None
    )
