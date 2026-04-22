"""
CrossFlow AI Python SDK

A comprehensive SDK for interacting with the CrossFlow AI Trading Platform API.
Supports intent management, real-time WebSocket communication, and more.
"""

from .client import CrossFlowClient
from .websocket import WebSocketClient
from .intent_manager import IntentManager
from .types import *
from .errors import *

__version__ = "1.0.0"
__author__ = "CrossFlow AI Team"
__email__ = "sdk@crossflow.ai"

__all__ = [
    "CrossFlowClient",
    "WebSocketClient", 
    "IntentManager",
    "CrossFlowError",
    "AuthenticationError",
    "RateLimitError",
    "ValidationError",
    "NetworkError",
    "WebSocketError",
]