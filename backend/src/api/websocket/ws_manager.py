"""
WebSocket Manager for Real-Time Updates

Handles WebSocket connections for:
- Price updates
- Transaction status updates
- AI signal notifications
- Order fill notifications
"""

import asyncio
import json
import logging
from typing import Dict, Set, Optional, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import websockets
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """WebSocket message types"""
    PRICE_UPDATE = "price_update"
    TRANSACTION_STATUS = "transaction_status"
    ORDER_UPDATE = "order_update"
    AI_SIGNAL = "ai_signal"
    PORTFOLIO_UPDATE = "portfolio_update"
    NOTIFICATION = "notification"
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"


@dataclass
class WSMessage:
    """WebSocket message structure"""
    type: str
    data: Dict[str, Any]
    timestamp: int
    
    def to_json(self) -> str:
        return json.dumps({
            "type": self.type,
            "data": self.data,
            "timestamp": self.timestamp
        })


class ConnectionManager:
    """Manages WebSocket connections and subscriptions"""
    
    def __init__(self):
        # Active connections by user_id
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Subscriptions: topic -> set of user_ids
        self.subscriptions: Dict[str, Set[str]] = {}
        # Connection metadata
        self.connection_metadata: Dict[WebSocket, Dict] = {}
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()
        
    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        """Accept a new WebSocket connection"""
        await websocket.accept()
        
        async with self._lock:
            if user_id not in self.active_connections:
                self.active_connections[user_id] = set()
            self.active_connections[user_id].add(websocket)
            
            self.connection_metadata[websocket] = {
                "user_id": user_id,
                "connected_at": datetime.utcnow().isoformat(),
                "subscriptions": set()
            }
        
        logger.info(f"WebSocket connected: user={user_id}")
        
        # Send welcome message
        await self.send_personal(
            websocket,
            MessageType.NOTIFICATION,
            {"message": "Connected to CrossFlow AI"}
        )
    
    async def disconnect(self, websocket: WebSocket) -> None:
        """Handle WebSocket disconnection"""
        async with self._lock:
            metadata = self.connection_metadata.get(websocket)
            if metadata:
                user_id = metadata["user_id"]
                
                # Remove from active connections
                if user_id in self.active_connections:
                    self.active_connections[user_id].discard(websocket)
                    if not self.active_connections[user_id]:
                        del self.active_connections[user_id]
                
                # Remove from subscriptions
                for topic in metadata.get("subscriptions", set()):
                    if topic in self.subscriptions:
                        self.subscriptions[topic].discard(user_id)
                
                del self.connection_metadata[websocket]
                logger.info(f"WebSocket disconnected: user={user_id}")
    
    async def subscribe(self, websocket: WebSocket, topic: str) -> None:
        """Subscribe a connection to a topic"""
        async with self._lock:
            metadata = self.connection_metadata.get(websocket)
            if metadata:
                user_id = metadata["user_id"]
                
                if topic not in self.subscriptions:
                    self.subscriptions[topic] = set()
                self.subscriptions[topic].add(user_id)
                metadata["subscriptions"].add(topic)
                
                logger.debug(f"User {user_id} subscribed to {topic}")
    
    async def unsubscribe(self, websocket: WebSocket, topic: str) -> None:
        """Unsubscribe a connection from a topic"""
        async with self._lock:
            metadata = self.connection_metadata.get(websocket)
            if metadata:
                user_id = metadata["user_id"]
                
                if topic in self.subscriptions:
                    self.subscriptions[topic].discard(user_id)
                metadata["subscriptions"].discard(topic)
                
                logger.debug(f"User {user_id} unsubscribed from {topic}")
    
    async def send_personal(
        self, 
        websocket: WebSocket, 
        msg_type: MessageType, 
        data: Dict[str, Any]
    ) -> None:
        """Send a message to a specific connection"""
        message = WSMessage(
            type=msg_type.value,
            data=data,
            timestamp=int(datetime.utcnow().timestamp() * 1000)
        )
        try:
            await websocket.send_text(message.to_json())
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
    
    async def send_to_user(
        self, 
        user_id: str, 
        msg_type: MessageType, 
        data: Dict[str, Any]
    ) -> None:
        """Send a message to all connections of a user"""
        connections = self.active_connections.get(user_id, set())
        message = WSMessage(
            type=msg_type.value,
            data=data,
            timestamp=int(datetime.utcnow().timestamp() * 1000)
        )
        
        for websocket in connections.copy():
            try:
                await websocket.send_text(message.to_json())
            except Exception as e:
                logger.error(f"Failed to send to user {user_id}: {e}")
                await self.disconnect(websocket)
    
    async def broadcast_to_topic(
        self, 
        topic: str, 
        msg_type: MessageType, 
        data: Dict[str, Any]
    ) -> None:
        """Broadcast a message to all subscribers of a topic"""
        subscribers = self.subscriptions.get(topic, set())
        message = WSMessage(
            type=msg_type.value,
            data=data,
            timestamp=int(datetime.utcnow().timestamp() * 1000)
        )
        
        for user_id in subscribers:
            connections = self.active_connections.get(user_id, set())
            for websocket in connections.copy():
                try:
                    await websocket.send_text(message.to_json())
                except Exception as e:
                    logger.error(f"Failed to broadcast to {user_id}: {e}")
    
    async def broadcast_all(
        self, 
        msg_type: MessageType, 
        data: Dict[str, Any]
    ) -> None:
        """Broadcast a message to all connected users"""
        message = WSMessage(
            type=msg_type.value,
            data=data,
            timestamp=int(datetime.utcnow().timestamp() * 1000)
        )
        
        for user_id, connections in self.active_connections.items():
            for websocket in connections.copy():
                try:
                    await websocket.send_text(message.to_json())
                except Exception as e:
                    logger.error(f"Failed to broadcast to {user_id}: {e}")
    
    def get_connection_count(self) -> int:
        """Get total number of active connections"""
        return sum(len(conns) for conns in self.active_connections.values())
    
    def get_user_count(self) -> int:
        """Get number of connected users"""
        return len(self.active_connections)


# Global connection manager instance
ws_manager = ConnectionManager()


class PriceStreamManager:
    """Manages price streaming from external sources"""
    
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
        self.binance_ws: Optional[websockets.WebSocketClientProtocol] = None
        self.subscribed_symbols: Set[str] = set()
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    async def start(self) -> None:
        """Start the price streaming service"""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._run_binance_stream())
        logger.info("Price stream manager started")
    
    async def stop(self) -> None:
        """Stop the price streaming service"""
        self._running = False
        if self.binance_ws:
            await self.binance_ws.close()
        if self._task:
            self._task.cancel()
        logger.info("Price stream manager stopped")
    
    async def subscribe_symbol(self, symbol: str) -> None:
        """Subscribe to price updates for a symbol"""
        self.subscribed_symbols.add(symbol.upper())
    
    async def _run_binance_stream(self) -> None:
        """Run the Binance WebSocket stream"""
        while self._running:
            try:
                # Build stream URL for all subscribed symbols
                streams = [f"{s.lower()}@ticker" for s in self.subscribed_symbols]
                if not streams:
                    # Default symbols
                    streams = [
                        "btcusdt@ticker", "ethusdt@ticker", "solusdt@ticker",
                        "bnbusdt@ticker", "arbusdt@ticker", "maticusdt@ticker"
                    ]
                
                url = f"wss://stream.binance.com:9443/ws/{'/'.join(streams)}"
                
                async with websockets.connect(url) as ws:
                    self.binance_ws = ws
                    logger.info("Connected to Binance WebSocket")
                    
                    while self._running:
                        try:
                            message = await asyncio.wait_for(ws.recv(), timeout=30)
                            data = json.loads(message)
                            
                            # Parse Binance ticker data
                            price_data = {
                                "symbol": data.get("s", ""),
                                "price": float(data.get("c", 0)),
                                "change_24h": float(data.get("P", 0)),
                                "high_24h": float(data.get("h", 0)),
                                "low_24h": float(data.get("l", 0)),
                                "volume_24h": float(data.get("q", 0)),
                            }
                            
                            # Broadcast to subscribers
                            topic = f"price:{price_data['symbol']}"
                            await self.connection_manager.broadcast_to_topic(
                                topic,
                                MessageType.PRICE_UPDATE,
                                price_data
                            )
                            
                        except asyncio.TimeoutError:
                            # Send heartbeat
                            await ws.ping()
                            
            except Exception as e:
                logger.error(f"Binance stream error: {e}")
                await asyncio.sleep(5)  # Reconnect delay


# Notification helper functions
async def notify_transaction_status(
    user_id: str,
    tx_hash: str,
    status: str,
    chain_id: int,
    details: Optional[Dict] = None
) -> None:
    """Send transaction status notification"""
    await ws_manager.send_to_user(
        user_id,
        MessageType.TRANSACTION_STATUS,
        {
            "tx_hash": tx_hash,
            "status": status,
            "chain_id": chain_id,
            "details": details or {}
        }
    )


async def notify_order_update(
    user_id: str,
    order_id: str,
    status: str,
    details: Optional[Dict] = None
) -> None:
    """Send order update notification"""
    await ws_manager.send_to_user(
        user_id,
        MessageType.ORDER_UPDATE,
        {
            "order_id": order_id,
            "status": status,
            "details": details or {}
        }
    )


async def notify_ai_signal(
    user_id: str,
    signal: Dict[str, Any]
) -> None:
    """Send AI trading signal notification"""
    await ws_manager.send_to_user(
        user_id,
        MessageType.AI_SIGNAL,
        signal
    )


async def notify_portfolio_change(
    user_id: str,
    change_type: str,
    details: Dict[str, Any]
) -> None:
    """Send portfolio change notification"""
    await ws_manager.send_to_user(
        user_id,
        MessageType.PORTFOLIO_UPDATE,
        {
            "change_type": change_type,
            "details": details
        }
    )


async def broadcast_balance_update(
    wallet_address: str,
    balance_data: Dict[str, Any]
) -> None:
    """Broadcast balance update to all clients"""
    await ws_manager.broadcast_all(
        MessageType.PORTFOLIO_UPDATE,
        {
            "event": "balance_update",
            "wallet_address": wallet_address,
            "balance": balance_data
        }
    )


async def broadcast_trade_executed(
    trade_data: Dict[str, Any]
) -> None:
    """Broadcast trade execution to all clients"""
    await ws_manager.broadcast_all(
        MessageType.TRANSACTION_STATUS,
        {
            "event": "trade_executed",
            "trade": trade_data
        }
    )


async def broadcast_price_update(
    token: str,
    price_data: Dict[str, Any]
) -> None:
    """Broadcast token price update to all clients"""
    await ws_manager.broadcast_all(
        MessageType.PRICE_UPDATE,
        {
            "event": "price_update",
            "token": token,
            "price": price_data
        }
    )


async def broadcast_ai_signal(
    signal_data: Dict[str, Any]
) -> None:
    """Broadcast AI signal to all clients"""
    await ws_manager.broadcast_all(
        MessageType.AI_SIGNAL,
        {
            "event": "ai_signal",
            "signal": signal_data
        }
    )
