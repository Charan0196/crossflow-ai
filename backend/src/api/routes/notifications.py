"""
Phase 5: Notifications API Routes
"""

from fastapi import APIRouter, HTTPException
from typing import Optional, List
from pydantic import BaseModel

from src.services.notification_service import notification_service

router = APIRouter(prefix="/notifications", tags=["notifications"])


class PreferencesUpdate(BaseModel):
    enabled_types: Optional[List[str]] = None
    price_alert_tokens: Optional[List[str]] = None
    price_alert_thresholds: Optional[dict] = None
    min_signal_confidence: Optional[float] = None
    portfolio_change_threshold: Optional[float] = None


@router.get("/")
async def get_notifications(
    user_id: str,
    unread_only: bool = False,
    limit: int = 50
):
    """Get notifications for a user."""
    notifications = await notification_service.get_user_notifications(
        user_id=user_id,
        unread_only=unread_only,
        limit=limit
    )
    
    return {
        "notifications": [n.to_dict() for n in notifications],
        "unread_count": len([n for n in notifications if not n.read])
    }


@router.post("/{notification_id}/read")
async def mark_as_read(user_id: str, notification_id: str):
    """Mark a notification as read."""
    await notification_service.mark_as_read(user_id, notification_id)
    return {"success": True}


@router.post("/read-all")
async def mark_all_as_read(user_id: str):
    """Mark all notifications as read."""
    await notification_service.mark_all_as_read(user_id)
    return {"success": True}


@router.put("/preferences")
async def update_preferences(user_id: str, preferences: PreferencesUpdate):
    """Update notification preferences."""
    await notification_service.update_preferences(user_id, preferences.dict(exclude_none=True))
    return {"success": True}


@router.get("/preferences")
async def get_preferences(user_id: str):
    """Get notification preferences."""
    prefs = notification_service.preferences.get(
        user_id,
        notification_service.get_default_preferences(user_id)
    )
    
    return {
        "enabled_types": [t.value for t in prefs.enabled_types],
        "price_alert_tokens": prefs.price_alert_tokens,
        "price_alert_thresholds": prefs.price_alert_thresholds,
        "min_signal_confidence": prefs.min_signal_confidence,
        "portfolio_change_threshold": prefs.portfolio_change_threshold
    }
