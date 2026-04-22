"""
WebSocket API Routes
Provides WebSocket endpoints for real-time intent status updates and price feeds
Requirements: 10.3 - WebSocket real-time communication
"""
import asyncio
import json
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from fastapi.security import HTTPBearer
import jwt

from src.config.settings import settings
from src.models.user import User
from src.api.websocket.connection_manager import connection_manager, MessageType, WebSocketMessage
from src.services.system_logging_service import system_logging_service
from src.services.error_handling_service import error_handling_service, ErrorContext


router = APIRouter()
security = HTTPBearer()
logger = logging.getLogger(__name__)


async def get_user_from_token(token: str) -> Optional[User]:
    """Get user from JWT token for WebSocket authentication"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        if username is None:
            return None
        
        # In a real implementation, you would query the database here
        # For now, create a mock user
        from src.models.user import User
        user = User()
        user.id = 1
        user.username = username
        user.email = f"{username}@example.com"
        user.wallet_addresses = '{"1": "0x1234567890123456789012345678901234567890"}'
        user.is_active = True
        
        return user
        
    except jwt.PyJWTError:
        return None


@router.websocket("/ws/intents")
async def websocket_intent_updates(
    websocket: WebSocket,
    token: str = Query(..., description="JWT authentication token")
):
    """
    WebSocket endpoint for real-time intent status updates
    Requires JWT authentication via query parameter
    """
    connection_id = None
    
    try:
        # Authenticate user
        user = await get_user_from_token(token)
        if not user:
            await websocket.close(code=4001, reason="Authentication failed")
            return
        
        # Connect to WebSocket
        connection_id = await connection_manager.connect(websocket, str(user.id))
        
        # Subscribe to user's intent updates
        await connection_manager.subscribe_to_topic(connection_id, f"user:{user.id}:intents")
        
        logger.info(f"WebSocket connected for intent updates: user {user.id}, connection {connection_id}")
        
        # Listen for messages
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Handle different message types
                await handle_client_message(connection_id, user, message_data)
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected: {connection_id}")
                break
            except json.JSONDecodeError:
                # Send error message for invalid JSON
                error_message = WebSocketMessage(
                    type=MessageType.ERROR,
                    data={"error": "Invalid JSON format"},
                    timestamp=asyncio.get_event_loop().time()
                )
                await connection_manager._send_to_connection(connection_id, error_message)
            except Exception as e:
                logger.error(f"WebSocket message handling error: {e}")
                error_message = WebSocketMessage(
                    type=MessageType.ERROR,
                    data={"error": "Message processing failed"},
                    timestamp=asyncio.get_event_loop().time()
                )
                await connection_manager._send_to_connection(connection_id, error_message)
    
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        
        context = ErrorContext(
            user_address=str(user.id) if user else None,
            operation_type="websocket_intent_connection"
        )
        
        await error_handling_service.handle_error(
            error=e,
            context=context,
            error_code="WEBSOCKET_INTENT_CONNECTION_FAILED"
        )
    
    finally:
        if connection_id:
            await connection_manager.disconnect(connection_id)


@router.websocket("/ws/prices")
async def websocket_price_feeds(
    websocket: WebSocket,
    token: str = Query(..., description="JWT authentication token"),
    pairs: str = Query(None, description="Comma-separated list of token pairs to subscribe to")
):
    """
    WebSocket endpoint for real-time price feeds
    Requires JWT authentication via query parameter
    """
    connection_id = None
    
    try:
        # Authenticate user
        user = await get_user_from_token(token)
        if not user:
            await websocket.close(code=4001, reason="Authentication failed")
            return
        
        # Connect to WebSocket
        connection_id = await connection_manager.connect(websocket, str(user.id))
        
        # Subscribe to price feeds
        if pairs:
            pair_list = [pair.strip() for pair in pairs.split(",")]
            for pair in pair_list:
                await connection_manager.subscribe_to_topic(connection_id, f"price:{pair}")
        else:
            # Subscribe to all price updates
            await connection_manager.subscribe_to_topic(connection_id, "price:*")
        
        logger.info(f"WebSocket connected for price feeds: user {user.id}, connection {connection_id}")
        
        # Listen for messages
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Handle different message types
                await handle_client_message(connection_id, user, message_data)
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected: {connection_id}")
                break
            except json.JSONDecodeError:
                # Send error message for invalid JSON
                error_message = WebSocketMessage(
                    type=MessageType.ERROR,
                    data={"error": "Invalid JSON format"},
                    timestamp=asyncio.get_event_loop().time()
                )
                await connection_manager._send_to_connection(connection_id, error_message)
            except Exception as e:
                logger.error(f"WebSocket message handling error: {e}")
    
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        
        context = ErrorContext(
            user_address=str(user.id) if user else None,
            operation_type="websocket_price_connection"
        )
        
        await error_handling_service.handle_error(
            error=e,
            context=context,
            error_code="WEBSOCKET_PRICE_CONNECTION_FAILED"
        )
    
    finally:
        if connection_id:
            await connection_manager.disconnect(connection_id)


@router.websocket("/ws/general")
async def websocket_general_updates(
    websocket: WebSocket,
    token: str = Query(..., description="JWT authentication token")
):
    """
    WebSocket endpoint for general real-time updates
    Includes system notifications, solver updates, etc.
    """
    connection_id = None
    
    try:
        # Authenticate user
        user = await get_user_from_token(token)
        if not user:
            await websocket.close(code=4001, reason="Authentication failed")
            return
        
        # Connect to WebSocket
        connection_id = await connection_manager.connect(websocket, str(user.id))
        
        # Subscribe to general updates
        await connection_manager.subscribe_to_topic(connection_id, "system:notifications")
        await connection_manager.subscribe_to_topic(connection_id, f"user:{user.id}:general")
        
        logger.info(f"WebSocket connected for general updates: user {user.id}, connection {connection_id}")
        
        # Listen for messages
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Handle different message types
                await handle_client_message(connection_id, user, message_data)
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected: {connection_id}")
                break
            except json.JSONDecodeError:
                # Send error message for invalid JSON
                error_message = WebSocketMessage(
                    type=MessageType.ERROR,
                    data={"error": "Invalid JSON format"},
                    timestamp=asyncio.get_event_loop().time()
                )
                await connection_manager._send_to_connection(connection_id, error_message)
            except Exception as e:
                logger.error(f"WebSocket message handling error: {e}")
    
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        
        context = ErrorContext(
            user_address=str(user.id) if user else None,
            operation_type="websocket_general_connection"
        )
        
        await error_handling_service.handle_error(
            error=e,
            context=context,
            error_code="WEBSOCKET_GENERAL_CONNECTION_FAILED"
        )
    
    finally:
        if connection_id:
            await connection_manager.disconnect(connection_id)


async def handle_client_message(connection_id: str, user: User, message_data: Dict[str, Any]):
    """Handle messages received from WebSocket clients"""
    try:
        message_type = message_data.get("type")
        data = message_data.get("data", {})
        
        if message_type == "subscribe":
            # Handle subscription requests
            topic = data.get("topic")
            if topic:
                await connection_manager.subscribe_to_topic(connection_id, topic)
        
        elif message_type == "unsubscribe":
            # Handle unsubscription requests
            topic = data.get("topic")
            if topic:
                await connection_manager.unsubscribe_from_topic(connection_id, topic)
        
        elif message_type == "heartbeat":
            # Update last heartbeat time
            if connection_id in connection_manager.active_connections:
                connection_manager.active_connections[connection_id].last_heartbeat = asyncio.get_event_loop().time()
        
        elif message_type == "intent_subscribe":
            # Subscribe to specific intent updates
            intent_id = data.get("intent_id")
            if intent_id:
                await connection_manager.subscribe_to_topic(connection_id, f"intent:{intent_id}")
        
        elif message_type == "price_subscribe":
            # Subscribe to specific price pair updates
            token_pair = data.get("token_pair")
            if token_pair:
                await connection_manager.subscribe_to_topic(connection_id, f"price:{token_pair}")
        
        else:
            # Unknown message type
            error_message = WebSocketMessage(
                type=MessageType.ERROR,
                data={"error": f"Unknown message type: {message_type}"},
                timestamp=asyncio.get_event_loop().time()
            )
            await connection_manager._send_to_connection(connection_id, error_message)
    
    except Exception as e:
        logger.error(f"Client message handling error: {e}")
        
        error_message = WebSocketMessage(
            type=MessageType.ERROR,
            data={"error": "Message processing failed"},
            timestamp=asyncio.get_event_loop().time()
        )
        await connection_manager._send_to_connection(connection_id, error_message)


# HTTP endpoints for WebSocket management
@router.get("/ws/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics"""
    return connection_manager.get_connection_stats()


@router.post("/ws/broadcast")
async def broadcast_message(
    message_data: Dict[str, Any],
    current_user: User = Depends(lambda: None)  # TODO: Add proper authentication
):
    """
    Broadcast a message to all connected clients
    (Admin only endpoint)
    """
    try:
        message = WebSocketMessage(
            type=MessageType.SYSTEM_NOTIFICATION,
            data=message_data,
            timestamp=asyncio.get_event_loop().time()
        )
        
        # Broadcast to all connections
        for connection_id in connection_manager.active_connections:
            await connection_manager._send_to_connection(connection_id, message)
        
        return {"status": "success", "message": "Broadcast sent"}
    
    except Exception as e:
        logger.error(f"Broadcast error: {e}")
        raise HTTPException(status_code=500, detail="Broadcast failed")


@router.post("/ws/send-intent-update")
async def send_intent_update(
    intent_id: str,
    user_id: str,
    status_data: Dict[str, Any],
    current_user: User = Depends(lambda: None)  # TODO: Add proper authentication
):
    """
    Send intent status update to a specific user
    (Internal API endpoint)
    """
    try:
        await connection_manager.send_intent_status_update(intent_id, user_id, status_data)
        return {"status": "success", "message": "Intent update sent"}
    
    except Exception as e:
        logger.error(f"Intent update error: {e}")
        raise HTTPException(status_code=500, detail="Intent update failed")


@router.post("/ws/send-price-update")
async def send_price_update(
    token_pair: str,
    price_data: Dict[str, Any],
    current_user: User = Depends(lambda: None)  # TODO: Add proper authentication
):
    """
    Send price update to subscribers
    (Internal API endpoint)
    """
    try:
        await connection_manager.send_price_update(token_pair, price_data)
        return {"status": "success", "message": "Price update sent"}
    
    except Exception as e:
        logger.error(f"Price update error: {e}")
        raise HTTPException(status_code=500, detail="Price update failed")