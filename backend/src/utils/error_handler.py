"""
Error Handling Utilities for Autonomous Trading

Provides:
- Error message sanitization
- RPC failover management
- Database offline caching
- AI signal error recovery
"""

import logging
import re
from typing import Any, Dict, List, Optional
from functools import wraps
from datetime import datetime

logger = logging.getLogger(__name__)


class ErrorSanitizer:
    """Sanitize error messages to remove sensitive information"""
    
    # Patterns to remove from error messages
    SENSITIVE_PATTERNS = [
        r'0x[a-fA-F0-9]{40}',  # Ethereum addresses
        r'[a-fA-F0-9]{64}',    # Private keys/hashes
        r'sk_[a-zA-Z0-9]{32,}', # API keys
        r'password[=:]\s*\S+',  # Passwords
        r'token[=:]\s*\S+',     # Tokens
    ]
    
    @classmethod
    def sanitize(cls, error_message: str) -> str:
        """Remove sensitive information from error messages"""
        sanitized = error_message
        
        for pattern in cls.SENSITIVE_PATTERNS:
            sanitized = re.sub(pattern, '[REDACTED]', sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    @classmethod
    def sanitize_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively sanitize dictionary values"""
        sanitized = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = cls.sanitize(value)
            elif isinstance(value, dict):
                sanitized[key] = cls.sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    cls.sanitize(v) if isinstance(v, str) else v
                    for v in value
                ]
            else:
                sanitized[key] = value
        
        return sanitized


class RPCFailover:
    """Manage RPC endpoint failover"""
    
    def __init__(self, endpoints: List[str]):
        self.endpoints = endpoints
        self.current_index = 0
        self.failed_endpoints = set()
    
    def get_endpoint(self) -> Optional[str]:
        """Get next available endpoint"""
        attempts = 0
        
        while attempts < len(self.endpoints):
            endpoint = self.endpoints[self.current_index]
            
            if endpoint not in self.failed_endpoints:
                return endpoint
            
            self.current_index = (self.current_index + 1) % len(self.endpoints)
            attempts += 1
        
        # All endpoints failed, reset and try again
        self.failed_endpoints.clear()
        return self.endpoints[0] if self.endpoints else None
    
    def mark_failed(self, endpoint: str):
        """Mark endpoint as failed"""
        self.failed_endpoints.add(endpoint)
        logger.warning(f"RPC endpoint marked as failed: {endpoint}")
        
        # Move to next endpoint
        self.current_index = (self.current_index + 1) % len(self.endpoints)
    
    def mark_success(self, endpoint: str):
        """Mark endpoint as successful"""
        if endpoint in self.failed_endpoints:
            self.failed_endpoints.remove(endpoint)
            logger.info(f"RPC endpoint recovered: {endpoint}")


class DatabaseCache:
    """Simple in-memory cache for database offline scenarios"""
    
    def __init__(self, max_size: int = 1000):
        self.cache: Dict[str, Any] = {}
        self.max_size = max_size
        self.timestamps: Dict[str, datetime] = {}
    
    def set(self, key: str, value: Any):
        """Set cache value"""
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            oldest_key = min(self.timestamps.keys(), key=lambda k: self.timestamps[k])
            del self.cache[oldest_key]
            del self.timestamps[oldest_key]
        
        self.cache[key] = value
        self.timestamps[key] = datetime.utcnow()
    
    def get(self, key: str) -> Optional[Any]:
        """Get cache value"""
        return self.cache.get(key)
    
    def has(self, key: str) -> bool:
        """Check if key exists"""
        return key in self.cache
    
    def clear(self):
        """Clear cache"""
        self.cache.clear()
        self.timestamps.clear()


# Global instances
db_cache = DatabaseCache()


def with_error_recovery(func):
    """Decorator for error recovery in AI signal generation"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {ErrorSanitizer.sanitize(str(e))}")
            # Log and continue - don't crash the service
            return None
    return wrapper


def with_rpc_failover(rpc_manager: RPCFailover):
    """Decorator for RPC failover"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            max_attempts = len(rpc_manager.endpoints)
            
            for attempt in range(max_attempts):
                endpoint = rpc_manager.get_endpoint()
                if not endpoint:
                    raise Exception("No RPC endpoints available")
                
                try:
                    # Pass endpoint to function
                    result = await func(*args, endpoint=endpoint, **kwargs)
                    rpc_manager.mark_success(endpoint)
                    return result
                except Exception as e:
                    logger.warning(f"RPC call failed on {endpoint}: {str(e)}")
                    rpc_manager.mark_failed(endpoint)
                    
                    if attempt == max_attempts - 1:
                        raise
            
            raise Exception("All RPC endpoints failed")
        return wrapper
    return decorator


def with_db_cache(cache_key_func):
    """Decorator for database caching"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache_key_func(*args, **kwargs)
            
            try:
                # Try database operation
                result = await func(*args, **kwargs)
                # Cache successful result
                db_cache.set(cache_key, result)
                return result
            except Exception as e:
                logger.warning(f"Database operation failed, using cache: {str(e)}")
                # Return cached value if available
                if db_cache.has(cache_key):
                    return db_cache.get(cache_key)
                raise
        return wrapper
    return decorator


class AdminNotificationService:
    """Service for sending critical error notifications to admins"""
    
    def __init__(self):
        self.notifications: List[Dict[str, Any]] = []
        self.max_notifications = 100
    
    def notify(self, level: str, message: str, details: Optional[Dict] = None):
        """Send notification to admins"""
        notification = {
            "level": level,
            "message": ErrorSanitizer.sanitize(message),
            "details": ErrorSanitizer.sanitize_dict(details) if details else {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.notifications.append(notification)
        
        # Keep only recent notifications
        if len(self.notifications) > self.max_notifications:
            self.notifications = self.notifications[-self.max_notifications:]
        
        # Log critical errors
        if level == "critical":
            logger.critical(f"ADMIN NOTIFICATION: {message}")
        elif level == "error":
            logger.error(f"ADMIN NOTIFICATION: {message}")
        else:
            logger.warning(f"ADMIN NOTIFICATION: {message}")
    
    def get_notifications(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent notifications"""
        return self.notifications[-limit:]
    
    def clear_notifications(self):
        """Clear all notifications"""
        self.notifications.clear()


# Global admin notification service
admin_notifier = AdminNotificationService()
