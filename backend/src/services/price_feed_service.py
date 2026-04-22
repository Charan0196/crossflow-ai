"""
Price Feed Service
Provides real-time price feeds for WebSocket clients
Requirements: 10.3 - WebSocket real-time communication
"""
import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from decimal import Decimal
import aiohttp
from datetime import datetime, timedelta

from src.api.websocket.connection_manager import connection_manager
from src.services.system_logging_service import system_logging_service
from src.services.error_handling_service import error_handling_service, ErrorContext


@dataclass
class PriceData:
    """Price data structure"""
    token_pair: str
    price: Decimal
    volume_24h: Decimal
    change_24h: Decimal
    change_percent_24h: Decimal
    high_24h: Decimal
    low_24h: Decimal
    timestamp: float
    source: str


@dataclass
class TokenInfo:
    """Token information"""
    symbol: str
    address: str
    chain_id: int
    decimals: int
    name: str


class PriceFeedService:
    """
    Service for managing real-time price feeds
    Aggregates prices from multiple sources and broadcasts updates via WebSocket
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Price cache: token_pair -> PriceData
        self.price_cache: Dict[str, PriceData] = {}
        
        # Subscribed token pairs
        self.subscribed_pairs: Set[str] = set()
        
        # Price sources configuration
        self.price_sources = {
            "coingecko": {
                "url": "https://api.coingecko.com/api/v3/simple/price",
                "enabled": True,
                "rate_limit": 50,  # requests per minute
                "last_request": 0
            },
            "coinmarketcap": {
                "url": "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest",
                "enabled": False,  # Requires API key
                "rate_limit": 333,  # requests per minute
                "last_request": 0
            }
        }
        
        # Supported token pairs (symbol pairs)
        self.supported_pairs = {
            "ETH/USDC", "ETH/USDT", "ETH/DAI",
            "BTC/USDC", "BTC/USDT", "BTC/ETH",
            "MATIC/USDC", "MATIC/ETH",
            "ARB/ETH", "ARB/USDC",
            "OP/ETH", "OP/USDC",
            "BNB/USDT", "BNB/ETH"
        }
        
        # Token mapping (symbol -> token info by chain)
        self.token_mapping = {
            "ETH": {
                1: TokenInfo("ETH", "0x0000000000000000000000000000000000000000", 1, 18, "Ethereum"),
                137: TokenInfo("ETH", "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619", 137, 18, "Ethereum (PoS)"),
                42161: TokenInfo("ETH", "0x0000000000000000000000000000000000000000", 42161, 18, "Ethereum"),
            },
            "USDC": {
                1: TokenInfo("USDC", "0xA0b86a33E6441c8C06DD2b7c94b7E6E42342f8e", 1, 6, "USD Coin"),
                137: TokenInfo("USDC", "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174", 137, 6, "USD Coin (PoS)"),
                42161: TokenInfo("USDC", "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8", 42161, 6, "USD Coin (Arb1)"),
            },
            "USDT": {
                1: TokenInfo("USDT", "0xdAC17F958D2ee523a2206206994597C13D831ec7", 1, 6, "Tether USD"),
                137: TokenInfo("USDT", "0xc2132D05D31c914a87C6611C10748AEb04B58e8F", 137, 6, "Tether USD (PoS)"),
                42161: TokenInfo("USDT", "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9", 42161, 6, "Tether USD"),
            }
        }
        
        # Update intervals
        self.update_interval = 10  # seconds
        self.cleanup_interval = 300  # 5 minutes
        
        # Background tasks
        self._price_update_task = None
        self._cleanup_task = None
        
        # Statistics
        self.stats = {
            "total_updates": 0,
            "successful_updates": 0,
            "failed_updates": 0,
            "active_subscriptions": 0,
            "last_update": None
        }
    
    async def start(self):
        """Start the price feed service"""
        try:
            self.logger.info("Starting price feed service...")
            
            # Start background tasks
            self._price_update_task = asyncio.create_task(self._price_update_loop())
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            
            # Initialize with some default pairs
            await self.subscribe_to_pairs(["ETH/USDC", "ETH/USDT", "BTC/USDC"])
            
            self.logger.info("Price feed service started successfully")
            
        except Exception as e:
            context = ErrorContext(
                operation_type="price_feed_start"
            )
            
            await error_handling_service.handle_error(
                error=e,
                context=context,
                error_code="PRICE_FEED_START_FAILED"
            )
            raise
    
    async def stop(self):
        """Stop the price feed service"""
        try:
            self.logger.info("Stopping price feed service...")
            
            # Cancel background tasks
            if self._price_update_task:
                self._price_update_task.cancel()
            if self._cleanup_task:
                self._cleanup_task.cancel()
            
            self.logger.info("Price feed service stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping price feed service: {e}")
    
    async def subscribe_to_pairs(self, pairs: List[str]):
        """Subscribe to price updates for specific token pairs"""
        try:
            for pair in pairs:
                if pair in self.supported_pairs:
                    self.subscribed_pairs.add(pair)
                    self.logger.info(f"Subscribed to price feed: {pair}")
                else:
                    self.logger.warning(f"Unsupported token pair: {pair}")
            
            self.stats["active_subscriptions"] = len(self.subscribed_pairs)
            
        except Exception as e:
            context = ErrorContext(
                operation_type="price_feed_subscription"
            )
            
            await error_handling_service.handle_error(
                error=e,
                context=context,
                error_code="PRICE_FEED_SUBSCRIPTION_FAILED"
            )
    
    async def unsubscribe_from_pairs(self, pairs: List[str]):
        """Unsubscribe from price updates for specific token pairs"""
        try:
            for pair in pairs:
                self.subscribed_pairs.discard(pair)
                self.logger.info(f"Unsubscribed from price feed: {pair}")
            
            self.stats["active_subscriptions"] = len(self.subscribed_pairs)
            
        except Exception as e:
            self.logger.error(f"Error unsubscribing from pairs: {e}")
    
    async def get_price(self, token_pair: str) -> Optional[PriceData]:
        """Get current price for a token pair"""
        return self.price_cache.get(token_pair)
    
    async def get_all_prices(self) -> Dict[str, PriceData]:
        """Get all cached prices"""
        return self.price_cache.copy()
    
    async def _price_update_loop(self):
        """Background task to update prices"""
        while True:
            try:
                await asyncio.sleep(self.update_interval)
                
                if not self.subscribed_pairs:
                    continue
                
                # Update prices for subscribed pairs
                await self._update_prices()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Price update loop error: {e}")
                self.stats["failed_updates"] += 1
    
    async def _cleanup_loop(self):
        """Background task to clean up old price data"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                
                current_time = time.time()
                cutoff_time = current_time - 3600  # Remove data older than 1 hour
                
                # Clean up old price data
                pairs_to_remove = []
                for pair, price_data in self.price_cache.items():
                    if price_data.timestamp < cutoff_time:
                        pairs_to_remove.append(pair)
                
                for pair in pairs_to_remove:
                    del self.price_cache[pair]
                
                if pairs_to_remove:
                    self.logger.info(f"Cleaned up {len(pairs_to_remove)} old price entries")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Cleanup loop error: {e}")
    
    async def _update_prices(self):
        """Update prices from external sources"""
        try:
            self.stats["total_updates"] += 1
            
            # For demo purposes, generate mock price data
            # In production, this would fetch from real price APIs
            await self._update_mock_prices()
            
            self.stats["successful_updates"] += 1
            self.stats["last_update"] = datetime.now().isoformat()
            
        except Exception as e:
            self.logger.error(f"Price update error: {e}")
            self.stats["failed_updates"] += 1
    
    async def _update_mock_prices(self):
        """Generate mock price data for testing"""
        import random
        
        base_prices = {
            "ETH/USDC": 2000.0,
            "ETH/USDT": 2001.0,
            "ETH/DAI": 1999.0,
            "BTC/USDC": 45000.0,
            "BTC/USDT": 45050.0,
            "BTC/ETH": 22.5,
            "MATIC/USDC": 0.85,
            "MATIC/ETH": 0.000425,
            "ARB/ETH": 0.0008,
            "ARB/USDC": 1.6,
            "OP/ETH": 0.0012,
            "OP/USDC": 2.4,
            "BNB/USDT": 320.0,
            "BNB/ETH": 0.16
        }
        
        current_time = time.time()
        
        for pair in self.subscribed_pairs:
            if pair not in base_prices:
                continue
            
            base_price = base_prices[pair]
            
            # Add some random variation (±2%)
            variation = random.uniform(-0.02, 0.02)
            current_price = base_price * (1 + variation)
            
            # Generate mock 24h data
            change_24h = random.uniform(-0.1, 0.1)  # ±10%
            high_24h = current_price * (1 + abs(change_24h) * 0.5)
            low_24h = current_price * (1 - abs(change_24h) * 0.5)
            volume_24h = random.uniform(1000000, 10000000)  # Mock volume
            
            price_data = PriceData(
                token_pair=pair,
                price=Decimal(str(round(current_price, 6))),
                volume_24h=Decimal(str(round(volume_24h, 2))),
                change_24h=Decimal(str(round(change_24h * base_price, 6))),
                change_percent_24h=Decimal(str(round(change_24h * 100, 2))),
                high_24h=Decimal(str(round(high_24h, 6))),
                low_24h=Decimal(str(round(low_24h, 6))),
                timestamp=current_time,
                source="mock"
            )
            
            # Update cache
            old_price = self.price_cache.get(pair)
            self.price_cache[pair] = price_data
            
            # Send WebSocket update if price changed significantly
            if not old_price or abs(float(price_data.price - old_price.price)) > float(old_price.price) * 0.001:  # 0.1% change
                await self._broadcast_price_update(price_data)
    
    async def _broadcast_price_update(self, price_data: PriceData):
        """Broadcast price update via WebSocket"""
        try:
            price_update_data = {
                "token_pair": price_data.token_pair,
                "price": str(price_data.price),
                "volume_24h": str(price_data.volume_24h),
                "change_24h": str(price_data.change_24h),
                "change_percent_24h": str(price_data.change_percent_24h),
                "high_24h": str(price_data.high_24h),
                "low_24h": str(price_data.low_24h),
                "timestamp": price_data.timestamp,
                "source": price_data.source
            }
            
            # Broadcast to WebSocket subscribers
            await connection_manager.send_price_update(price_data.token_pair, price_update_data)
            
            # Log price update
            self.logger.info(f"Price update broadcast: {price_data.token_pair} = {price_data.price}")
            
            # Log to system logging service using health check method as a workaround
            try:
                system_logging_service.log_system_health_check(
                    service_name="price_feed",
                    passed=True,
                    response_time_ms=0,
                    details={
                        "event": "price_update",
                        "token_pair": price_data.token_pair,
                        "price": str(price_data.price),
                        "change_percent_24h": str(price_data.change_percent_24h),
                        "timestamp": price_data.timestamp
                    }
                )
            except Exception as log_error:
                self.logger.warning(f"Failed to log price update: {log_error}")
            
        except Exception as e:
            self.logger.error(f"Price broadcast error: {e}")
    
    async def _fetch_coingecko_prices(self, pairs: List[str]) -> Dict[str, PriceData]:
        """Fetch prices from CoinGecko API"""
        try:
            # Rate limiting check
            current_time = time.time()
            source_config = self.price_sources["coingecko"]
            
            if current_time - source_config["last_request"] < 60 / source_config["rate_limit"]:
                return {}
            
            # Map pairs to CoinGecko IDs
            coingecko_ids = {
                "ETH": "ethereum",
                "BTC": "bitcoin",
                "MATIC": "matic-network",
                "ARB": "arbitrum",
                "OP": "optimism",
                "BNB": "binancecoin",
                "USDC": "usd-coin",
                "USDT": "tether",
                "DAI": "dai"
            }
            
            # Build request parameters
            ids = set()
            for pair in pairs:
                base, quote = pair.split("/")
                if base in coingecko_ids:
                    ids.add(coingecko_ids[base])
            
            if not ids:
                return {}
            
            # Make API request
            async with aiohttp.ClientSession() as session:
                params = {
                    "ids": ",".join(ids),
                    "vs_currencies": "usd",
                    "include_24hr_change": "true",
                    "include_24hr_vol": "true"
                }
                
                async with session.get(source_config["url"], params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        source_config["last_request"] = current_time
                        return self._parse_coingecko_response(data, pairs)
                    else:
                        self.logger.error(f"CoinGecko API error: {response.status}")
                        return {}
        
        except Exception as e:
            self.logger.error(f"CoinGecko fetch error: {e}")
            return {}
    
    def _parse_coingecko_response(self, data: Dict, pairs: List[str]) -> Dict[str, PriceData]:
        """Parse CoinGecko API response"""
        result = {}
        current_time = time.time()
        
        # This is a simplified parser - in production you'd need more sophisticated mapping
        for pair in pairs:
            try:
                base, quote = pair.split("/")
                # For simplicity, assume USD quotes for now
                if quote == "USDC" or quote == "USDT":
                    quote = "USD"
                
                # Find matching data
                # This would need more sophisticated logic in production
                
            except Exception as e:
                self.logger.error(f"Error parsing price for {pair}: {e}")
        
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """Get price feed service statistics"""
        return {
            **self.stats,
            "subscribed_pairs": list(self.subscribed_pairs),
            "cached_pairs": list(self.price_cache.keys()),
            "supported_pairs": list(self.supported_pairs)
        }


# Global price feed service instance
price_feed_service = PriceFeedService()