"""
Position Monitor Service
Tracks and monitors executed trading positions
"""
import asyncio
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import httpx
from dataclasses import dataclass

from ..ai.multi_ai_provider import multi_ai_provider


@dataclass
class Position:
    """Trading position data"""
    id: str
    signal_id: str
    token_pair: str
    entry_price: float
    current_price: float
    target_price: float
    stop_loss: float
    amount_usd: float
    tokens_bought: float
    network: str
    wallet_address: str
    transaction_hash: str
    status: str  # ACTIVE, TARGET_HIT, STOP_LOSS_HIT, CLOSED
    pnl_usd: float
    pnl_percentage: float
    created_at: datetime
    updated_at: datetime


class PositionMonitorService:
    """Service for monitoring trading positions"""
    
    def __init__(self):
        self.active_positions = {}  # position_id -> Position
        self.position_history = []
        
    async def add_position(self, 
                          signal_id: str,
                          token_pair: str,
                          entry_price: float,
                          target_price: float,
                          stop_loss: float,
                          amount_usd: float,
                          tokens_bought: float,
                          network: str,
                          wallet_address: str,
                          transaction_hash: str) -> str:
        """Add a new position to monitor"""
        
        position_id = f"pos_{signal_id}_{int(datetime.now().timestamp())}"
        
        position = Position(
            id=position_id,
            signal_id=signal_id,
            token_pair=token_pair,
            entry_price=entry_price,
            current_price=entry_price,
            target_price=target_price,
            stop_loss=stop_loss,
            amount_usd=amount_usd,
            tokens_bought=tokens_bought,
            network=network,
            wallet_address=wallet_address,
            transaction_hash=transaction_hash,
            status="ACTIVE",
            pnl_usd=0.0,
            pnl_percentage=0.0,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.active_positions[position_id] = position
        return position_id
    
    async def update_positions(self) -> List[Position]:
        """Update all active positions with current prices"""
        if not self.active_positions:
            return []
        
        updated_positions = []
        
        for position_id, position in list(self.active_positions.items()):
            try:
                # Get current price
                current_price = await self._get_token_price(position.token_pair)
                
                if current_price > 0:
                    # Update position data
                    position.current_price = current_price
                    position.updated_at = datetime.now()
                    
                    # Calculate PnL
                    price_change = (current_price - position.entry_price) / position.entry_price
                    position.pnl_percentage = price_change * 100
                    position.pnl_usd = position.amount_usd * price_change
                    
                    # Check if target or stop loss hit
                    if current_price >= position.target_price:
                        position.status = "TARGET_HIT"
                        await self._move_to_history(position_id)
                    elif current_price <= position.stop_loss:
                        position.status = "STOP_LOSS_HIT"
                        await self._move_to_history(position_id)
                    
                    updated_positions.append(position)
                    
            except Exception as e:
                print(f"Error updating position {position_id}: {e}")
                continue
        
        return updated_positions
    
    async def _get_token_price(self, token_pair: str) -> float:
        """Get current token price from Binance"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.binance.com/api/v3/ticker/price?symbol={token_pair}",
                    timeout=5.0
                )
                if response.status_code == 200:
                    data = response.json()
                    return float(data['price'])
        except Exception as e:
            print(f"Error getting price for {token_pair}: {e}")
        return 0.0
    
    async def _move_to_history(self, position_id: str):
        """Move position from active to history"""
        if position_id in self.active_positions:
            position = self.active_positions.pop(position_id)
            self.position_history.append(position)
    
    async def get_active_positions(self) -> List[Dict[str, Any]]:
        """Get all active positions"""
        await self.update_positions()
        
        return [self.position_to_dict(pos) for pos in self.active_positions.values()]
    
    async def get_position_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get position history"""
        # Sort by created_at descending
        sorted_history = sorted(self.position_history, key=lambda x: x.created_at, reverse=True)
        
        return [self.position_to_dict(pos) for pos in sorted_history[:limit]]
    
    async def close_position(self, position_id: str) -> Dict[str, Any]:
        """Manually close a position"""
        if position_id not in self.active_positions:
            return {'success': False, 'error': 'Position not found'}
        
        position = self.active_positions[position_id]
        position.status = "CLOSED"
        
        await self._move_to_history(position_id)
        
        return {
            'success': True,
            'position_id': position_id,
            'final_pnl_usd': position.pnl_usd,
            'final_pnl_percentage': position.pnl_percentage
        }
    
    async def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get portfolio summary statistics"""
        await self.update_positions()
        
        active_positions = list(self.active_positions.values())
        
        if not active_positions:
            return {
                'total_positions': 0,
                'total_invested': 0.0,
                'total_pnl_usd': 0.0,
                'total_pnl_percentage': 0.0,
                'winning_positions': 0,
                'losing_positions': 0
            }
        
        total_invested = sum(pos.amount_usd for pos in active_positions)
        total_pnl_usd = sum(pos.pnl_usd for pos in active_positions)
        total_pnl_percentage = (total_pnl_usd / total_invested * 100) if total_invested > 0 else 0
        
        winning_positions = len([pos for pos in active_positions if pos.pnl_usd > 0])
        losing_positions = len([pos for pos in active_positions if pos.pnl_usd < 0])
        
        return {
            'total_positions': len(active_positions),
            'total_invested': total_invested,
            'total_pnl_usd': total_pnl_usd,
            'total_pnl_percentage': total_pnl_percentage,
            'winning_positions': winning_positions,
            'losing_positions': losing_positions
        }
    
    def position_to_dict(self, position: Position) -> Dict[str, Any]:
        """Convert position to dictionary"""
        return {
            'id': position.id,
            'signal_id': position.signal_id,
            'token_pair': position.token_pair,
            'entry_price': position.entry_price,
            'current_price': position.current_price,
            'target_price': position.target_price,
            'stop_loss': position.stop_loss,
            'amount_usd': position.amount_usd,
            'tokens_bought': position.tokens_bought,
            'network': position.network,
            'wallet_address': position.wallet_address,
            'transaction_hash': position.transaction_hash,
            'status': position.status,
            'pnl_usd': position.pnl_usd,
            'pnl_percentage': position.pnl_percentage,
            'created_at': position.created_at.isoformat(),
            'updated_at': position.updated_at.isoformat()
        }


# Global instance
position_monitor_service = PositionMonitorService()