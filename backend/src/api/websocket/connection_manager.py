"""
WebSocket Connection Manager
Manages WebSocket connections for real-time intent status updates and price feeds
Requirements: 10.3 - WebSocket real-time communication
"""
import asyncio
import json
import logging
import time
from typing import Dict, List, Set, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

from src.services.system_logging_service import system_logging_service
from src.services.error_handling_service import error_handling_service, ErrorContext


class MessageType(Enum):
    """Types of WebSocket messages"""
    INTENT_STATUS_UPDATE = "intent_status_update"
    PRICE_UPDATE = "price_update"
    SOLVER_BID_UPDATE = "solver_bid_update"
    SYSTEM_NOTIFICATION = "system_notification"
    SUBSCRIPTION_CONFIRMATION = "subscription_confirmation"
    ERROR = "error"
    HEARTBEAT = "heartbeat"


@dataclass
class WebSocketMessage:
    """WebSocket message structure"""
    type: MessageType
    data: Dict[str, Any]
    timestamp: float
    message_id: str = None
    
    def __post_init__(self):
        if self.message_id is None:
            self.message_id = str(uuid.uuid4())


@dataclass
class ConnectionInfo:
    """Information about a WebSocket connection"""
    websocket: WebSocket
    user_id: str
    connected_at: float
    last_heartbeat: float
    subscriptions: Set[str]  # Set of subscription topics
    
    def __post_init__(self):
        if not hasattr(self, 'subscriptions'):
            self.subscriptions = set()


class WebSocketConnectionManager:
    """
    Manages WebSocket connections for real-time communication
    Handles intent status updates, price feeds, and connection lifecycle
    """
    
    def __init__(self):
        # Active connections: connection_id -> ConnectionInfo
        self.active_connections: Dict[str, ConnectionInfo] = {}
        
        # User connections: user_id -> Set[connection_id]
        self.user_connections: Dict[str, Set[str]] = {}
        
        # Topic subscriptions: topic -> Set[connection_id]
        self.topic_subscriptions: Dict[str, Set[str]] = {}
        
        # Message queue for offline users: user_id -> List[WebSocketMessage]
        self.offline_message_queue: Dict[str, List[WebSocketMessage]] = {}
        
        # Connection statistics
        self.connection_stats = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "messages_received": 0,
            "connection_errors": 0
        }
        
        # Heartbeat settings
        self.heartbeat_interval = 30  # seconds
        self.heartbeat_timeout = 60  # seconds
        
        # Start background tasks
        self._heartbeat_task = None
        self._cleanup_task = None
        
        self.logger = logging.getLogger(__name__)
    
    async def connect(self, websocket: WebSocket, user_id: str) -> str:
        """
        Accept a new WebSocket connection
        Returns connection ID
        """
        try:
            await websocket.accept()
            
            connection_id = str(uuid.uuid4())
            current_time = time.time()
            
            # Create connection info
            connection_info = ConnectionInfo(
                websocket=websocket,
                user_id=user_id,
                connected_at=current_time,
                last_heartbeat=current_time,
                subscriptions=set()
            )
            
            # Store connection
            self.active_connections[connection_id] = connection_info
            
            # Update user connections
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection_id)
            
            # Update statistics
            self.connection_stats["total_connections"] += 1
            self.connection_stats["active_connections"] = len(self.active_connections)
            
            # Send queued messages for this user
            await self._send_queued_messages(user_id, connection_id)
            
            # Send connection confirmation
            confirmation_message = WebSocketMessage(
                type=MessageType.SUBSCRIPTION_CONFIRMATION,
                data={
                    "connection_id": connection_id,
                    "user_id": user_id,
                    "connected_at": current_time,
                    "status": "connected"
                },
                timestamp=current_time
            )
            
            await self._send_to_connection(connection_id, confirmation_message)
            
            # Log connection
            self.logger.info(f"WebSocket connected: {connection_id} for user {user_id}")
            
            # Log to system logging service using health check method as a workaround
            try:
                system_logging_service.log_system_health_check(
                    service_name="websocket",
                    status="healthy",
                    response_time_ms=0,
                    details={
                        "event": "websocket_connected",
                        "connection_id": connection_id,
                        "user_id": user_id,
                        "timestamp": current_time
                    }
                )
            except Exception as log_error:
                self.logger.warning(f"Failed to log WebSocket connection: {log_error}")
            
            # Start background tasks if not running
            if self._heartbeat_task is None:
                self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            if self._cleanup_task is None:
                self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            
            self.logger.info(f"WebSocket connected: {connection_id} for user {user_id}")
            return connection_id
            
        except Exception as e:
            self.connection_stats["connection_errors"] += 1
            
            context = ErrorContext(
                user_address=user_id,
                operation_type="websocket_connection"
            )
            
            await error_handling_service.handle_error(
                error=e,
                context=context,
                error_code="WEBSOCKET_CONNECTION_FAILED"
            )
            
            raise
    
    async def disconnect(self, connection_id: str):
        """Disconnect a WebSocket connection"""
        try:
            if connection_id not in self.active_connections:
                return
            
            connection_info = self.active_connections[connection_id]
            user_id = connection_info.user_id
            
            # Remove from topic subscriptions
            for topic in connection_info.subscriptions:
                if topic in self.topic_subscriptions:
                    self.topic_subscriptions[topic].discard(connection_id)
                    if not self.topic_subscriptions[topic]:
                        del self.topic_subscriptions[topic]
            
            # Remove from user connections
            if user_id in self.user_connections:
                self.user_connections[user_id].discard(connection_id)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
            
            # Remove connection
            del self.active_connections[connection_id]
            
            # Update statistics
            self.connection_stats["active_connections"] = len(self.active_connections)
            
            # Log disconnection
            self.logger.info(f"WebSocket disconnected: {connection_id} for user {user_id}")
            
            # Log to system logging service using health check method as a workaround
            try:
                system_logging_service.log_system_health_check(
                    service_name="websocket",
                    status="disconnected",
                    response_time_ms=0,
                    details={
                        "event": "websocket_disconnected",
                        "connection_id": connection_id,
                        "user_id": user_id,
                        "timestamp": time.time()
                    }
                )
            except Exception as log_error:
                self.logger.warning(f"Failed to log WebSocket disconnection: {log_error}")
            
            self.logger.info(f"WebSocket disconnected: {connection_id} for user {user_id}")
            
        except Exception as e:
            context = ErrorContext(
                operation_type="websocket_disconnection"
            )
            
            await error_handling_service.handle_error(
                error=e,
                context=context,
                error_code="WEBSOCKET_DISCONNECTION_FAILED"
            )
    
    async def subscribe_to_topic(self, connection_id: str, topic: str):
        """Subscribe a connection to a topic"""
        try:
            if connection_id not in self.active_connections:
                return False
            
            connection_info = self.active_connections[connection_id]
            connection_info.subscriptions.add(topic)
            
            # Add to topic subscriptions
            if topic not in self.topic_subscriptions:
                self.topic_subscriptions[topic] = set()
            self.topic_subscriptions[topic].add(connection_id)
            
            # Send subscription confirmation
            confirmation_message = WebSocketMessage(
                type=MessageType.SUBSCRIPTION_CONFIRMATION,
                data={
                    "topic": topic,
                    "status": "subscribed",
                    "connection_id": connection_id
                },
                timestamp=time.time()
            )
            
            await self._send_to_connection(connection_id, confirmation_message)
            
            self.logger.info(f"Connection {connection_id} subscribed to topic: {topic}")
            return True
            
        except Exception as e:
            context = ErrorContext(
                operation_type="websocket_subscription"
            )
            
            await error_handling_service.handle_error(
                error=e,
                context=context,
                error_code="WEBSOCKET_SUBSCRIPTION_FAILED"
            )
            return False
    
    async def unsubscribe_from_topic(self, connection_id: str, topic: str):
        """Unsubscribe a connection from a topic"""
        try:
            if connection_id not in self.active_connections:
                return False
            
            connection_info = self.active_connections[connection_id]
            connection_info.subscriptions.discard(topic)
            
            # Remove from topic subscriptions
            if topic in self.topic_subscriptions:
                self.topic_subscriptions[topic].discard(connection_id)
                if not self.topic_subscriptions[topic]:
                    del self.topic_subscriptions[topic]
            
            self.logger.info(f"Connection {connection_id} unsubscribed from topic: {topic}")
            return True
            
        except Exception as e:
            context = ErrorContext(
                operation_type="websocket_unsubscription"
            )
            
            await error_handling_service.handle_error(
                error=e,
                context=context,
                error_code="WEBSOCKET_UNSUBSCRIPTION_FAILED"
            )
            return False
    
    async def send_to_user(self, user_id: str, message: WebSocketMessage):
        """Send a message to all connections for a specific user"""
        try:
            if user_id not in self.user_connections:
                # Queue message for offline user
                if user_id not in self.offline_message_queue:
                    self.offline_message_queue[user_id] = []
                self.offline_message_queue[user_id].append(message)
                
                # Limit queue size
                if len(self.offline_message_queue[user_id]) > 100:
                    self.offline_message_queue[user_id] = self.offline_message_queue[user_id][-100:]
                
                return
            
            # Send to all user connections
            connection_ids = list(self.user_connections[user_id])
            for connection_id in connection_ids:
                await self._send_to_connection(connection_id, message)
                
        except Exception as e:
            context = ErrorContext(
                user_address=user_id,
                operation_type="websocket_send_to_user"
            )
            
            await error_handling_service.handle_error(
                error=e,
                context=context,
                error_code="WEBSOCKET_SEND_FAILED"
            )
    
    async def broadcast_to_topic(self, topic: str, message: WebSocketMessage):
        """Broadcast a message to all connections subscribed to a topic"""
        try:
            if topic not in self.topic_subscriptions:
                return
            
            connection_ids = list(self.topic_subscriptions[topic])
            for connection_id in connection_ids:
                await self._send_to_connection(connection_id, message)
                
        except Exception as e:
            context = ErrorContext(
                operation_type="websocket_broadcast"
            )
            
            await error_handling_service.handle_error(
                error=e,
                context=context,
                error_code="WEBSOCKET_BROADCAST_FAILED"
            )
    
    async def send_intent_status_update(self, intent_id: str, user_id: str, status_data: Dict[str, Any]):
        """Send intent status update to user"""
        message = WebSocketMessage(
            type=MessageType.INTENT_STATUS_UPDATE,
            data={
                "intent_id": intent_id,
                "status": status_data,
                "updated_at": time.time()
            },
            timestamp=time.time()
        )
        
        await self.send_to_user(user_id, message)
    
    async def send_price_update(self, token_pair: str, price_data: Dict[str, Any]):
        """Send price update to subscribers"""
        topic = f"price:{token_pair}"
        
        message = WebSocketMessage(
            type=MessageType.PRICE_UPDATE,
            data={
                "token_pair": token_pair,
                "price_data": price_data,
                "updated_at": time.time()
            },
            timestamp=time.time()
        )
        
        await self.broadcast_to_topic(topic, message)
    
    async def send_solver_bid_update(self, intent_id: str, bid_data: Dict[str, Any]):
        """Send solver bid update to intent subscribers"""
        topic = f"intent:{intent_id}"
        
        message = WebSocketMessage(
            type=MessageType.SOLVER_BID_UPDATE,
            data={
                "intent_id": intent_id,
                "bid_data": bid_data,
                "updated_at": time.time()
            },
            timestamp=time.time()
        )
        
        await self.broadcast_to_topic(topic, message)
    
    async def _send_to_connection(self, connection_id: str, message: WebSocketMessage):
        """Send a message to a specific connection"""
        try:
            if connection_id not in self.active_connections:
                return
            
            connection_info = self.active_connections[connection_id]
            websocket = connection_info.websocket
            
            # Convert message to JSON
            message_json = json.dumps({
                "type": message.type.value,
                "data": message.data,
                "timestamp": message.timestamp,
                "message_id": message.message_id
            })
            
            await websocket.send_text(message_json)
            self.connection_stats["messages_sent"] += 1
            
        except WebSocketDisconnect:
            # Connection was closed, clean up
            await self.disconnect(connection_id)
        except Exception as e:
            # Connection error, clean up
            await self.disconnect(connection_id)
            self.connection_stats["connection_errors"] += 1
    
    async def _send_queued_messages(self, user_id: str, connection_id: str):
        """Send queued messages to a newly connected user"""
        if user_id not in self.offline_message_queue:
            return
        
        messages = self.offline_message_queue[user_id]
        for message in messages:
            await self._send_to_connection(connection_id, message)
        
        # Clear queue
        del self.offline_message_queue[user_id]
    
    async def _heartbeat_loop(self):
        """Background task to send heartbeat messages"""
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                
                current_time = time.time()
                heartbeat_message = WebSocketMessage(
                    type=MessageType.HEARTBEAT,
                    data={"timestamp": current_time},
                    timestamp=current_time
                )
                
                # Send heartbeat to all connections
                connection_ids = list(self.active_connections.keys())
                for connection_id in connection_ids:
                    await self._send_to_connection(connection_id, heartbeat_message)
                
            except Exception as e:
                self.logger.error(f"Heartbeat loop error: {e}")
    
    async def _cleanup_loop(self):
        """Background task to clean up stale connections"""
        while True:
            try:
                await asyncio.sleep(60)  # Run cleanup every minute
                
                current_time = time.time()
                stale_connections = []
                
                # Find stale connections
                for connection_id, connection_info in self.active_connections.items():
                    if current_time - connection_info.last_heartbeat > self.heartbeat_timeout:
                        stale_connections.append(connection_id)
                
                # Clean up stale connections
                for connection_id in stale_connections:
                    await self.disconnect(connection_id)
                
                # Clean up old offline messages
                for user_id in list(self.offline_message_queue.keys()):
                    messages = self.offline_message_queue[user_id]
                    # Keep only messages from last 24 hours
                    cutoff_time = current_time - 86400  # 24 hours
                    self.offline_message_queue[user_id] = [
                        msg for msg in messages if msg.timestamp > cutoff_time
                    ]
                    
                    if not self.offline_message_queue[user_id]:
                        del self.offline_message_queue[user_id]
                
            except Exception as e:
                self.logger.error(f"Cleanup loop error: {e}")
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            **self.connection_stats,
            "active_users": len(self.user_connections),
            "active_topics": len(self.topic_subscriptions),
            "queued_messages": sum(len(msgs) for msgs in self.offline_message_queue.values())
        }


# Global connection manager instance
connection_manager = WebSocketConnectionManager()