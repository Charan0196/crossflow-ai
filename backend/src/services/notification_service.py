"""
Phase 5: Notification Service

Provides:
- WebSocket notification delivery
- Event-based notifications
- Notification preferences
"""

import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, List, Set, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import json

logger = logging.getLogger(__name__)


class NotificationType(str, Enum):
    TRANSACTION_STATUS = "transaction_status"
    ORDER_FILLED = "order_filled"
    ORDER_CANCELLED = "order_cancelled"
    PRICE_ALERT = "price_alert"
    AI_SIGNAL = "ai_signal"
    PORTFOLIO_CHANGE = "portfolio_change"
    SECURITY_WARNING = "security_warning"
    SYSTEM = "system"


class NotificationPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class Notification:
    id: str
    user_id: str
    type: NotificationType
    priority: NotificationPriority
    title: str
    message: str
    data: Dict[str, Any]
    timestamp: datetime
    read: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type.value,
            "priority": self.priority.value,
            "title": self.title,
            "message": self.message,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "read": self.read
        }


@dataclass
class UserPreferences:
    user_id: str
    enabled_types: Set[NotificationType]
    price_alert_tokens: List[str]
    price_alert_thresholds: Dict[str, float]  # token -> % change
    min_signal_confidence: float
    portfolio_change_threshold: float  # % change


class NotificationService:
    def __init__(self):
        self.notifications: Dict[str, List[Notification]] = {}
        self.preferences: Dict[str, UserPreferences] = {}
        self.websocket_handlers: Dict[str, Callable] = {}
        self._notification_counter = 0
    
    def _generate_id(self) -> str:
        self._notification_counter += 1
        return f"notif_{self._notification_counter}_{datetime.utcnow().timestamp()}"
    
    def register_websocket_handler(self, user_id: str, handler: Callable):
        """Register a WebSocket handler for a user."""
        self.websocket_handlers[user_id] = handler
    
    def unregister_websocket_handler(self, user_id: str):
        """Unregister a WebSocket handler."""
        self.websocket_handlers.pop(user_id, None)
    
    def get_default_preferences(self, user_id: str) -> UserPreferences:
        return UserPreferences(
            user_id=user_id,
            enabled_types=set(NotificationType),
            price_alert_tokens=["BTC", "ETH"],
            price_alert_thresholds={"BTC": 5.0, "ETH": 5.0},
            min_signal_confidence=0.7,
            portfolio_change_threshold=5.0
        )

    async def send_notification(
        self,
        user_id: str,
        notification_type: NotificationType,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        priority: NotificationPriority = NotificationPriority.MEDIUM
    ) -> Notification:
        """Send a notification to a user."""
        prefs = self.preferences.get(user_id, self.get_default_preferences(user_id))
        
        if notification_type not in prefs.enabled_types:
            logger.debug(f"Notification type {notification_type} disabled for user {user_id}")
            return None
        
        notification = Notification(
            id=self._generate_id(),
            user_id=user_id,
            type=notification_type,
            priority=priority,
            title=title,
            message=message,
            data=data or {},
            timestamp=datetime.utcnow()
        )
        
        if user_id not in self.notifications:
            self.notifications[user_id] = []
        self.notifications[user_id].append(notification)
        
        # Send via WebSocket if handler registered
        handler = self.websocket_handlers.get(user_id)
        if handler:
            try:
                await handler(notification.to_dict())
            except Exception as e:
                logger.error(f"Failed to send WebSocket notification: {e}")
        
        logger.info(f"Sent notification {notification.id} to user {user_id}")
        return notification
    
    async def notify_transaction_status(
        self,
        user_id: str,
        tx_hash: str,
        status: str,
        chain_id: int,
        details: Optional[Dict[str, Any]] = None
    ):
        """Send transaction status notification."""
        status_messages = {
            "pending": "Transaction is pending confirmation",
            "confirmed": "Transaction confirmed successfully",
            "failed": "Transaction failed",
            "cancelled": "Transaction was cancelled"
        }
        
        priority = NotificationPriority.HIGH if status == "failed" else NotificationPriority.MEDIUM
        
        await self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.TRANSACTION_STATUS,
            title=f"Transaction {status.title()}",
            message=status_messages.get(status, f"Transaction status: {status}"),
            data={"tx_hash": tx_hash, "status": status, "chain_id": chain_id, **(details or {})},
            priority=priority
        )

    async def notify_order_filled(
        self,
        user_id: str,
        order_id: str,
        order_type: str,
        from_token: str,
        to_token: str,
        amount: float,
        price: float
    ):
        """Send order filled notification."""
        await self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.ORDER_FILLED,
            title=f"{order_type.title()} Order Filled",
            message=f"Your {order_type} order for {amount} {from_token} → {to_token} was filled at ${price:,.2f}",
            data={"order_id": order_id, "order_type": order_type, "from_token": from_token,
                  "to_token": to_token, "amount": amount, "price": price},
            priority=NotificationPriority.HIGH
        )
    
    async def notify_price_alert(
        self,
        user_id: str,
        token: str,
        current_price: float,
        change_percent: float,
        direction: str
    ):
        """Send price alert notification."""
        prefs = self.preferences.get(user_id, self.get_default_preferences(user_id))
        threshold = prefs.price_alert_thresholds.get(token, 5.0)
        
        if abs(change_percent) < threshold:
            return
        
        await self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.PRICE_ALERT,
            title=f"{token} Price Alert",
            message=f"{token} is {direction} {abs(change_percent):.1f}% - now ${current_price:,.2f}",
            data={"token": token, "price": current_price, "change_percent": change_percent},
            priority=NotificationPriority.HIGH if abs(change_percent) > 10 else NotificationPriority.MEDIUM
        )
    
    async def notify_ai_signal(
        self,
        user_id: str,
        token: str,
        signal_type: str,
        confidence: float,
        explanation: str
    ):
        """Send AI signal notification."""
        prefs = self.preferences.get(user_id, self.get_default_preferences(user_id))
        
        if confidence < prefs.min_signal_confidence:
            return
        
        await self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.AI_SIGNAL,
            title=f"AI Signal: {signal_type.upper()} {token}",
            message=explanation,
            data={"token": token, "signal": signal_type, "confidence": confidence},
            priority=NotificationPriority.HIGH if confidence > 0.85 else NotificationPriority.MEDIUM
        )

    async def notify_portfolio_change(
        self,
        user_id: str,
        total_value: float,
        change_percent: float,
        change_usd: float
    ):
        """Send portfolio change notification."""
        prefs = self.preferences.get(user_id, self.get_default_preferences(user_id))
        
        if abs(change_percent) < prefs.portfolio_change_threshold:
            return
        
        direction = "up" if change_percent > 0 else "down"
        await self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.PORTFOLIO_CHANGE,
            title=f"Portfolio {direction.title()} {abs(change_percent):.1f}%",
            message=f"Your portfolio is now ${total_value:,.2f} ({'+' if change_usd > 0 else ''}{change_usd:,.2f})",
            data={"total_value": total_value, "change_percent": change_percent, "change_usd": change_usd},
            priority=NotificationPriority.MEDIUM
        )
    
    async def notify_security_warning(
        self,
        user_id: str,
        warning_type: str,
        message: str,
        details: Dict[str, Any]
    ):
        """Send security warning notification."""
        await self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.SECURITY_WARNING,
            title=f"Security Alert: {warning_type}",
            message=message,
            data=details,
            priority=NotificationPriority.URGENT
        )
    
    async def get_user_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Notification]:
        """Get notifications for a user."""
        notifications = self.notifications.get(user_id, [])
        
        if unread_only:
            notifications = [n for n in notifications if not n.read]
        
        return sorted(notifications, key=lambda x: x.timestamp, reverse=True)[:limit]
    
    async def mark_as_read(self, user_id: str, notification_id: str):
        """Mark a notification as read."""
        notifications = self.notifications.get(user_id, [])
        for n in notifications:
            if n.id == notification_id:
                n.read = True
                break
    
    async def mark_all_as_read(self, user_id: str):
        """Mark all notifications as read."""
        for n in self.notifications.get(user_id, []):
            n.read = True
    
    async def update_preferences(self, user_id: str, preferences: Dict[str, Any]):
        """Update user notification preferences."""
        current = self.preferences.get(user_id, self.get_default_preferences(user_id))
        
        if "enabled_types" in preferences:
            current.enabled_types = {NotificationType(t) for t in preferences["enabled_types"]}
        if "price_alert_tokens" in preferences:
            current.price_alert_tokens = preferences["price_alert_tokens"]
        if "price_alert_thresholds" in preferences:
            current.price_alert_thresholds = preferences["price_alert_thresholds"]
        if "min_signal_confidence" in preferences:
            current.min_signal_confidence = preferences["min_signal_confidence"]
        if "portfolio_change_threshold" in preferences:
            current.portfolio_change_threshold = preferences["portfolio_change_threshold"]
        
        self.preferences[user_id] = current


# Singleton instance
notification_service = NotificationService()
