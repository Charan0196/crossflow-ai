"""
Human Override System - Human-in-the-Loop Controls
Phase 4: Ecosystem & Compliance

Provides human override capabilities for AI decisions.
"""

import hashlib
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set
import logging

logger = logging.getLogger(__name__)


@dataclass
class OverrideConfig:
    user_address: str
    amount_threshold: Optional[float] = None
    frequency_threshold: Optional[int] = None  # Max trades per hour
    asset_types: List[str] = field(default_factory=list)
    always_ask_operations: List[str] = field(default_factory=list)
    enabled: bool = True


@dataclass
class OverrideRequest:
    request_id: str
    user_address: str
    operation: str
    trade_details: Dict[str, Any]
    trigger_reason: str
    potential_impact: str
    requested_at: datetime
    expires_at: datetime


@dataclass
class OverrideResponse:
    request_id: str
    approved: bool
    user_address: str
    responded_at: datetime
    notes: Optional[str] = None


class HumanOverrideSystem:
    """
    Human Override System for human-in-the-loop controls.
    
    Validates: Requirements 6.1-6.6
    """
    
    REQUEST_EXPIRY_MINUTES = 5
    PAUSE_TIMEOUT_MS = 100
    
    def __init__(self):
        self.configs: Dict[str, OverrideConfig] = {}
        self.pending_requests: Dict[str, OverrideRequest] = {}
        self.override_history: List[Dict[str, Any]] = []
        self.paused_users: Set[str] = set()
        self.trade_counts: Dict[str, List[datetime]] = {}

    async def check_requires_override(
        self,
        user: str,
        operation: str,
        details: Dict[str, Any]
    ) -> bool:
        """
        Check if operation requires human override.
        
        Property 20: Threshold-Based Confirmation
        For any trade exceeding user-defined thresholds, requires confirmation.
        
        Property 22: Always-Ask Mode Enforcement
        For any operation in always-ask mode, requires confirmation.
        """
        config = self.configs.get(user)
        if not config or not config.enabled:
            return False
        
        # Check always-ask operations
        if operation in config.always_ask_operations:
            return True
        
        # Check amount threshold
        amount = details.get("amount", 0)
        if config.amount_threshold and amount > config.amount_threshold:
            return True
        
        # Check asset type restrictions
        asset = details.get("asset_type", "")
        if asset in config.asset_types:
            return True
        
        # Check frequency threshold
        if config.frequency_threshold:
            if user not in self.trade_counts:
                self.trade_counts[user] = []
            
            # Count trades in last hour
            hour_ago = datetime.utcnow() - timedelta(hours=1)
            recent_trades = [t for t in self.trade_counts[user] if t > hour_ago]
            
            if len(recent_trades) >= config.frequency_threshold:
                return True
        
        return False

    async def request_override(self, request: OverrideRequest) -> str:
        """
        Create override request for user confirmation.
        
        Property 23: Override Impact Notification
        For any AI override, notifies user of potential impact.
        """
        self.pending_requests[request.request_id] = request
        
        # Log the request
        self.override_history.append({
            "request_id": request.request_id,
            "user_address": request.user_address,
            "operation": request.operation,
            "trigger_reason": request.trigger_reason,
            "potential_impact": request.potential_impact,
            "requested_at": request.requested_at,
            "status": "pending",
        })
        
        logger.info(f"Override request {request.request_id} created for {request.user_address}")
        return request.request_id

    async def process_response(self, response: OverrideResponse) -> None:
        """
        Process user response to override request.
        
        Property 21: Override Logging Completeness
        For any override action, creates log entry with timestamp and outcome.
        """
        request = self.pending_requests.get(response.request_id)
        if not request:
            raise ValueError("Override request not found or expired")
        
        # Update history
        for entry in self.override_history:
            if entry.get("request_id") == response.request_id:
                entry["status"] = "approved" if response.approved else "rejected"
                entry["responded_at"] = response.responded_at
                entry["notes"] = response.notes
                break
        
        # Remove from pending
        del self.pending_requests[response.request_id]
        
        # Record trade if approved
        if response.approved:
            if request.user_address not in self.trade_counts:
                self.trade_counts[request.user_address] = []
            self.trade_counts[request.user_address].append(datetime.utcnow())
        
        logger.info(f"Override {response.request_id} {'approved' if response.approved else 'rejected'}")

    async def pause_execution(self, user: str) -> bool:
        """
        Pause AI execution for user immediately.
        
        Property 19: Immediate Pause on Override
        For any override request, AI execution pauses within 100ms.
        """
        start_time = time.time()
        
        self.paused_users.add(user)
        
        # Log pause event
        self.override_history.append({
            "user_address": user,
            "action": "pause",
            "timestamp": datetime.utcnow(),
            "pause_time_ms": int((time.time() - start_time) * 1000),
        })
        
        elapsed_ms = int((time.time() - start_time) * 1000)
        logger.info(f"Paused execution for {user} in {elapsed_ms}ms")
        
        return elapsed_ms < self.PAUSE_TIMEOUT_MS

    async def resume_execution(self, user: str) -> bool:
        """Resume AI execution for user."""
        if user in self.paused_users:
            self.paused_users.remove(user)
            
            self.override_history.append({
                "user_address": user,
                "action": "resume",
                "timestamp": datetime.utcnow(),
            })
            
            logger.info(f"Resumed execution for {user}")
            return True
        return False

    def is_paused(self, user: str) -> bool:
        """Check if user execution is paused."""
        return user in self.paused_users

    async def get_override_config(self, user: str) -> Optional[OverrideConfig]:
        """Get user's override configuration."""
        return self.configs.get(user)

    async def update_override_config(self, config: OverrideConfig) -> bool:
        """Update user's override configuration."""
        self.configs[config.user_address] = config
        
        self.override_history.append({
            "user_address": config.user_address,
            "action": "config_update",
            "timestamp": datetime.utcnow(),
            "config": {
                "amount_threshold": config.amount_threshold,
                "frequency_threshold": config.frequency_threshold,
                "asset_types": config.asset_types,
                "always_ask_operations": config.always_ask_operations,
                "enabled": config.enabled,
            },
        })
        
        logger.info(f"Updated override config for {config.user_address}")
        return True

    async def get_override_history(
        self,
        user: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get override history for user."""
        user_history = [
            h for h in self.override_history
            if h.get("user_address") == user
        ]
        return user_history[-limit:]

    def create_override_request(
        self,
        user: str,
        operation: str,
        details: Dict[str, Any],
        trigger_reason: str
    ) -> OverrideRequest:
        """Create a new override request."""
        request_id = self._generate_id("override")
        
        # Calculate potential impact
        amount = details.get("amount", 0)
        impact = f"This operation will affect ${amount:,.2f} in assets."
        
        if operation == "trade":
            impact += f" Trade will execute at current market price."
        elif operation == "rebalance":
            impact += f" Portfolio allocation will be adjusted."
        
        return OverrideRequest(
            request_id=request_id,
            user_address=user,
            operation=operation,
            trade_details=details,
            trigger_reason=trigger_reason,
            potential_impact=impact,
            requested_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=self.REQUEST_EXPIRY_MINUTES),
        )

    def get_pending_requests(self, user: str) -> List[OverrideRequest]:
        """Get pending override requests for user."""
        now = datetime.utcnow()
        return [
            r for r in self.pending_requests.values()
            if r.user_address == user and r.expires_at > now
        ]

    def cleanup_expired_requests(self) -> int:
        """Remove expired override requests."""
        now = datetime.utcnow()
        expired = [
            rid for rid, req in self.pending_requests.items()
            if req.expires_at <= now
        ]
        
        for rid in expired:
            del self.pending_requests[rid]
            # Update history
            for entry in self.override_history:
                if entry.get("request_id") == rid and entry.get("status") == "pending":
                    entry["status"] = "expired"
        
        return len(expired)

    def _generate_id(self, prefix: str) -> str:
        """Generate unique ID."""
        return f"{prefix}_{hashlib.sha256(f'{time.time()}'.encode()).hexdigest()[:12]}"
