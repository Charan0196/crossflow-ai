"""
Enhanced price data service with freshness validation
"""
import aiohttp
import json
from typing import Dict, Optional, List
from decimal import Decimal
from datetime import datetime, timedelta

from src.config.settings import settings
from src.services.price_freshness_validator import price_freshness_validator, PriceDataPoint, PriceDataSource


class EnhancedPriceService:
    """Enhanced price service with freshness validation and automatic refresh"""
    
    def __init__(self):
        self.base_url = settings.coingecko_base_url
        self.api_key = settings.coingecko_api_key
        
        # Common token mappings to CoinGecko IDs
        self.token_mappings = {
            # Ethereum
            "0x0000000000000000000000000000000000000000": "ethereum",  # ETH
            "0xa0b86a33e6c6c9c6c6c6c6c6c6c6c6c6c6c6c6c6": "usd-coin",  # USDC
            "0xdac17f958d2ee523a2206206994597c13d831ec7": "tether",     # USDT
            "0x6b175474e89094c44da98b954eedeac495271d0f": "dai",        # DAI
            
            # Native tokens by chain
            "native_1": "ethereum",      # ETH
            "native_137": "matic-network", # MATIC
            "native_42161": "ethereum",   # ETH on Arbitrum
            "native_10": "ethereum",      # ETH on Optimism
            "native_56": "binancecoin",   # BNB
        }
    
    async def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make HTTP request to CoinGecko API"""
        headers = {}
        if self.api_key:
            headers["x-cg-demo-api-key"] = self.api_key
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}{endpoint}",
                    params=params,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        print(f"CoinGecko API error: {response.status}")
                        return None
        except Exception as e:
            print(f"Error making CoinGecko request: {e}")
            return None
    
    async def get_fresh_token_price(self, token_address: str, chain_id: int, vs_currency: str = "usd") -> Optional[PriceDataPoint]:
        """Get fresh token price with automatic freshness validation"""
        # Try to get fresh price from validator first
        fresh_price = await price_freshness_validator.get_fresh_price(
            token_address, vs_currency, chain_id
        )
        
        if fresh_price and fresh_price.is_fresh:
            return fresh_price
        
        # Fallback to CoinGecko if no fresh data available
        coingecko_id = self.get_coingecko_id(token_address, chain_id)
        if coingecko_id:
            price = await self.get_token_price(coingecko_id, vs_currency)
            if price:
                return PriceDataPoint(
                    price=price,
                    timestamp=datetime.now(),
                    source=PriceDataSource.COINGECKO,
                    token_pair=f"{coingecko_id}/{vs_currency}",
                    chain_id=chain_id,
                    is_fresh=True,
                    staleness_seconds=0
                )
        
        return None
    
    async def get_token_price(self, token_id: str, vs_currency: str = "usd") -> Optional[Decimal]:
        """Get current token price from CoinGecko"""
        params = {
            "ids": token_id,
            "vs_currencies": vs_currency
        }
        
        endpoint = "/simple/price"
        result = await self._make_request(endpoint, params)
        
        if result and token_id in result:
            price = result[token_id].get(vs_currency)
            return Decimal(str(price)) if price else None
        return None
    
    async def get_multiple_fresh_prices(self, token_addresses: List[str], chain_ids: List[int], vs_currency: str = "usd") -> Dict[str, PriceDataPoint]:
        """Get fresh prices for multiple tokens with validation"""
        token_pairs = [(addr, vs_currency, chain_id) for addr, chain_id in zip(token_addresses, chain_ids)]
        
        # Get fresh prices from validator
        fresh_prices = await price_freshness_validator.get_multiple_fresh_prices(token_pairs)
        
        # For any missing prices, try CoinGecko fallback
        missing_tokens = []
        for i, (addr, chain_id) in enumerate(zip(token_addresses, chain_ids)):
            cache_key = f"{addr}_{vs_currency}_{chain_id}"
            if cache_key not in fresh_prices:
                coingecko_id = self.get_coingecko_id(addr, chain_id)
                if coingecko_id:
                    missing_tokens.append(coingecko_id)
        
        if missing_tokens:
            fallback_prices = await self.get_multiple_prices(missing_tokens, vs_currency)
            
            # Convert fallback prices to PriceDataPoint format
            for token_id, price in fallback_prices.items():
                # Find corresponding token address and chain_id
                for addr, chain_id in zip(token_addresses, chain_ids):
                    if self.get_coingecko_id(addr, chain_id) == token_id:
                        cache_key = f"{addr}_{vs_currency}_{chain_id}"
                        fresh_prices[cache_key] = PriceDataPoint(
                            price=price,
                            timestamp=datetime.now(),
                            source=PriceDataSource.COINGECKO,
                            token_pair=f"{token_id}/{vs_currency}",
                            chain_id=chain_id,
                            is_fresh=True,
                            staleness_seconds=0
                        )
                        break
        
        return fresh_prices
    
    async def get_multiple_prices(self, token_ids: List[str], vs_currency: str = "usd") -> Dict[str, Decimal]:
        """Get prices for multiple tokens from CoinGecko"""
        params = {
            "ids": ",".join(token_ids),
            "vs_currencies": vs_currency
        }
        
        endpoint = "/simple/price"
        result = await self._make_request(endpoint, params)
        
        prices = {}
        if result:
            for token_id in token_ids:
                if token_id in result:
                    price = result[token_id].get(vs_currency)
                    if price:
                        prices[token_id] = Decimal(str(price))
        
        return prices
    
    async def validate_price_freshness(self, token_address: str, chain_id: int, vs_currency: str = "usd") -> Dict[str, any]:
        """Validate freshness of cached price data"""
        fresh_price = await price_freshness_validator.get_fresh_price(
            token_address, vs_currency, chain_id
        )
        
        if fresh_price:
            return await price_freshness_validator.validate_price_freshness(fresh_price)
        
        return {
            "is_fresh": False,
            "is_stale": True,
            "is_expired": True,
            "staleness_seconds": float('inf'),
            "source": "none",
            "timestamp": None,
            "warnings": ["No price data available"],
            "errors": ["No cached price data found"]
        }
    
    def get_coingecko_id(self, token_address: str, chain_id: int) -> Optional[str]:
        """Map token address to CoinGecko ID"""
        # Check for native token
        native_key = f"native_{chain_id}"
        if token_address.lower() in ["0x0", "native", "eth", "matic", "bnb"]:
            return self.token_mappings.get(native_key)
        
        # Check direct mapping
        return self.token_mappings.get(token_address.lower())
    
    async def start_price_monitoring(self, token_address: str, chain_id: int, vs_currency: str = "usd"):
        """Start automatic price monitoring for a token"""
        price_freshness_validator.start_auto_refresh(token_address, vs_currency, chain_id)
    
    def stop_price_monitoring(self, token_address: str, chain_id: int, vs_currency: str = "usd"):
        """Stop automatic price monitoring for a token"""
        price_freshness_validator.stop_auto_refresh(token_address, vs_currency, chain_id)
    
    async def get_price_health_status(self) -> Dict[str, any]:
        """Get health status of price data sources"""
        return await price_freshness_validator.health_check()
    
    async def get_reliable_price(self, token_address: str, chain_id: int, vs_currency: str = "usd") -> Optional[PriceDataPoint]:
        """Get reliable price using fallback system"""
        from src.services.price_feed_fallback import price_feed_fallback
        
        fallback_result = await price_feed_fallback.get_price_with_fallback(
            token_address, vs_currency, chain_id
        )
        
        if fallback_result.price_data:
            return fallback_result.price_data
        
        # Final fallback to direct CoinGecko
        coingecko_id = self.get_coingecko_id(token_address, chain_id)
        if coingecko_id:
            price = await self.get_token_price(coingecko_id, vs_currency)
            if price:
                return PriceDataPoint(
                    price=price,
                    timestamp=datetime.now(),
                    source=PriceDataSource.COINGECKO,
                    token_pair=f"{coingecko_id}/{vs_currency}",
                    chain_id=chain_id,
                    is_fresh=True,
                    staleness_seconds=0
                )
        
        return None
    
    async def get_price_with_fallback_info(self, token_address: str, chain_id: int, vs_currency: str = "usd") -> Dict[str, any]:
        """Get price with detailed fallback information"""
        from src.services.price_feed_fallback import price_feed_fallback
        
        fallback_result = await price_feed_fallback.get_price_with_fallback(
            token_address, vs_currency, chain_id
        )
        
        return {
            "price_data": fallback_result.price_data,
            "source_used": fallback_result.source_used.value if fallback_result.source_used else None,
            "sources_tried": [s.value for s in fallback_result.sources_tried],
            "sources_failed": [(s.value, error) for s, error in fallback_result.sources_failed],
            "execution_time_ms": fallback_result.execution_time_ms,
            "fallback_triggered": fallback_result.fallback_triggered,
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_price_source_health(self) -> Dict[str, any]:
        """Get health status of all price sources"""
        from src.services.price_feed_fallback import price_feed_fallback
        
        return price_feed_fallback.get_source_health_status()


# Global instance
enhanced_price_service = EnhancedPriceService()

# Keep original service for backward compatibility
class PriceService:
    def __init__(self):
        self.base_url = settings.coingecko_base_url
        self.api_key = settings.coingecko_api_key
        
        # Common token mappings to CoinGecko IDs
        self.token_mappings = {
            # Ethereum
            "0x0000000000000000000000000000000000000000": "ethereum",  # ETH
            "0xa0b86a33e6c6c9c6c6c6c6c6c6c6c6c6c6c6c6c6": "usd-coin",  # USDC
            "0xdac17f958d2ee523a2206206994597c13d831ec7": "tether",     # USDT
            "0x6b175474e89094c44da98b954eedeac495271d0f": "dai",        # DAI
            
            # Native tokens by chain
            "native_1": "ethereum",      # ETH
            "native_137": "matic-network", # MATIC
            "native_42161": "ethereum",   # ETH on Arbitrum
            "native_10": "ethereum",      # ETH on Optimism
            "native_56": "binancecoin",   # BNB
        }
    
    async def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make HTTP request to CoinGecko API"""
        headers = {}
        if self.api_key:
            headers["x-cg-demo-api-key"] = self.api_key
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}{endpoint}",
                    params=params,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        print(f"CoinGecko API error: {response.status}")
                        return None
        except Exception as e:
            print(f"Error making CoinGecko request: {e}")
            return None
    
    async def get_token_price(self, token_id: str, vs_currency: str = "usd") -> Optional[Decimal]:
        """Get current token price"""
        params = {
            "ids": token_id,
            "vs_currencies": vs_currency
        }
        
        endpoint = "/simple/price"
        result = await self._make_request(endpoint, params)
        
        if result and token_id in result:
            price = result[token_id].get(vs_currency)
            return Decimal(str(price)) if price else None
        return None
    
    async def get_multiple_prices(self, token_ids: List[str], vs_currency: str = "usd") -> Dict[str, Decimal]:
        """Get prices for multiple tokens"""
        params = {
            "ids": ",".join(token_ids),
            "vs_currencies": vs_currency
        }
        
        endpoint = "/simple/price"
        result = await self._make_request(endpoint, params)
        
        prices = {}
        if result:
            for token_id in token_ids:
                if token_id in result:
                    price = result[token_id].get(vs_currency)
                    if price:
                        prices[token_id] = Decimal(str(price))
        
        return prices
    
    def get_coingecko_id(self, token_address: str, chain_id: int) -> Optional[str]:
        """Map token address to CoinGecko ID"""
        # Check for native token
        native_key = f"native_{chain_id}"
        if token_address.lower() in ["0x0", "native", "eth", "matic", "bnb"]:
            return self.token_mappings.get(native_key)
        
        # Check direct mapping
        return self.token_mappings.get(token_address.lower())

# Global instance for backward compatibility
price_service = PriceService()