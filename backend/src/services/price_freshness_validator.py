"""
Price data freshness validation service
"""
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
from decimal import Decimal
from dataclasses import dataclass
from enum import Enum
import asyncio
import logging


class PriceDataSource(Enum):
    """Price data source types"""
    UNISWAP_V3 = "uniswap_v3"
    JUPITER = "jupiter"
    COINGECKO = "coingecko"


@dataclass
class PriceDataPoint:
    """Price data with freshness information"""
    price: Decimal
    timestamp: datetime
    source: PriceDataSource
    token_pair: str
    chain_id: Optional[int] = None
    is_fresh: bool = True
    staleness_seconds: int = 0


@dataclass
class FreshnessConfig:
    """Configuration for price data freshness validation"""
    max_age_seconds: int = 30  # Maximum age for fresh data
    stale_warning_seconds: int = 60  # When to warn about stale data
    refresh_interval_seconds: int = 15  # How often to refresh data
    max_staleness_seconds: int = 300  # Maximum allowed staleness before rejection


class PriceFreshnessValidator:
    """Service for validating and managing price data freshness"""
    
    def __init__(self, config: Optional[FreshnessConfig] = None):
        self.config = config or FreshnessConfig()
        self.price_cache: Dict[str, PriceDataPoint] = {}
        self.refresh_tasks: Dict[str, asyncio.Task] = {}
        self.logger = logging.getLogger(__name__)
        
        # Track data source reliability
        self.source_reliability: Dict[PriceDataSource, Dict[str, int]] = {
            PriceDataSource.UNISWAP_V3: {"success": 0, "failure": 0},
            PriceDataSource.JUPITER: {"success": 0, "failure": 0},
            PriceDataSource.COINGECKO: {"success": 0, "failure": 0}
        }
    
    def _generate_cache_key(self, token_a: str, token_b: str, chain_id: Optional[int] = None) -> str:
        """Generate cache key for token pair"""
        if chain_id:
            return f"{token_a}_{token_b}_{chain_id}"
        return f"{token_a}_{token_b}"
    
    def _calculate_staleness(self, timestamp: datetime) -> int:
        """Calculate staleness in seconds"""
        return int((datetime.now() - timestamp).total_seconds())
    
    def _is_data_fresh(self, timestamp: datetime) -> bool:
        """Check if data is considered fresh"""
        staleness = self._calculate_staleness(timestamp)
        return staleness <= self.config.max_age_seconds
    
    def _is_data_stale(self, timestamp: datetime) -> bool:
        """Check if data is stale but still usable"""
        staleness = self._calculate_staleness(timestamp)
        return staleness > self.config.stale_warning_seconds
    
    def _is_data_expired(self, timestamp: datetime) -> bool:
        """Check if data is too old to use"""
        staleness = self._calculate_staleness(timestamp)
        return staleness > self.config.max_staleness_seconds
    
    async def _fetch_uniswap_price(self, token_a: str, token_b: str, chain_id: int, amount: int = 10**18) -> Optional[PriceDataPoint]:
        """Fetch price from Uniswap V3"""
        try:
            # Import here to avoid circular dependency
            from src.services.uniswap_v3_service import uniswap_v3_service
            
            quote = await uniswap_v3_service.get_quote(token_a, token_b, amount, chain_id)
            if quote:
                self.source_reliability[PriceDataSource.UNISWAP_V3]["success"] += 1
                return PriceDataPoint(
                    price=quote.price,
                    timestamp=quote.timestamp,
                    source=PriceDataSource.UNISWAP_V3,
                    token_pair=f"{token_a}/{token_b}",
                    chain_id=chain_id,
                    is_fresh=self._is_data_fresh(quote.timestamp),
                    staleness_seconds=self._calculate_staleness(quote.timestamp)
                )
        except Exception as e:
            self.logger.error(f"Error fetching Uniswap price: {e}")
            self.source_reliability[PriceDataSource.UNISWAP_V3]["failure"] += 1
        return None
    
    async def _fetch_jupiter_price(self, input_mint: str, output_mint: str, amount: int = 10**6) -> Optional[PriceDataPoint]:
        """Fetch price from Jupiter"""
        try:
            # Import here to avoid circular dependency
            from src.services.jupiter_service import jupiter_service
            
            quote = await jupiter_service.get_quote(input_mint, output_mint, amount)
            if quote:
                self.source_reliability[PriceDataSource.JUPITER]["success"] += 1
                price = Decimal(quote.out_amount) / Decimal(quote.in_amount)
                return PriceDataPoint(
                    price=price,
                    timestamp=quote.timestamp,
                    source=PriceDataSource.JUPITER,
                    token_pair=f"{input_mint}/{output_mint}",
                    is_fresh=self._is_data_fresh(quote.timestamp),
                    staleness_seconds=self._calculate_staleness(quote.timestamp)
                )
        except Exception as e:
            self.logger.error(f"Error fetching Jupiter price: {e}")
            self.source_reliability[PriceDataSource.JUPITER]["failure"] += 1
        return None
    
    async def _fetch_coingecko_price(self, token_id: str) -> Optional[PriceDataPoint]:
        """Fetch price from CoinGecko as fallback"""
        try:
            # Import here to avoid circular dependency
            from src.services.price_service import price_service
            
            price = await price_service.get_token_price(token_id)
            if price:
                self.source_reliability[PriceDataSource.COINGECKO]["success"] += 1
                return PriceDataPoint(
                    price=price,
                    timestamp=datetime.now(),  # CoinGecko doesn't provide timestamp
                    source=PriceDataSource.COINGECKO,
                    token_pair=f"{token_id}/USD",
                    is_fresh=True,  # Assume fresh since we just fetched it
                    staleness_seconds=0
                )
        except Exception as e:
            self.logger.error(f"Error fetching CoinGecko price: {e}")
            self.source_reliability[PriceDataSource.COINGECKO]["failure"] += 1
        return None
    
    async def get_fresh_price(self, token_a: str, token_b: str, chain_id: Optional[int] = None, force_refresh: bool = False) -> Optional[PriceDataPoint]:
        """Get fresh price data with automatic refresh if needed"""
        cache_key = self._generate_cache_key(token_a, token_b, chain_id)
        
        # Check cache first
        if not force_refresh and cache_key in self.price_cache:
            cached_data = self.price_cache[cache_key]
            
            # Return cached data if fresh
            if self._is_data_fresh(cached_data.timestamp):
                return cached_data
            
            # Check if data is expired
            if self._is_data_expired(cached_data.timestamp):
                self.logger.warning(f"Price data for {cache_key} is expired, forcing refresh")
                force_refresh = True
        
        # Fetch fresh data if needed
        if force_refresh or cache_key not in self.price_cache:
            fresh_data = await self._fetch_fresh_data(token_a, token_b, chain_id)
            if fresh_data:
                self.price_cache[cache_key] = fresh_data
                return fresh_data
        
        # Return cached data even if stale (better than no data)
        return self.price_cache.get(cache_key)
    
    async def _fetch_fresh_data(self, token_a: str, token_b: str, chain_id: Optional[int] = None) -> Optional[PriceDataPoint]:
        """Fetch fresh data from appropriate source"""
        # Import here to avoid circular dependency
        from src.services.uniswap_v3_service import uniswap_v3_service
        from src.services.price_service import price_service
        
        # For EVM chains, use Uniswap V3
        if chain_id and uniswap_v3_service.is_supported_chain(chain_id):
            return await self._fetch_uniswap_price(token_a, token_b, chain_id)
        
        # For Solana tokens, use Jupiter
        if not chain_id or chain_id == 101:  # Solana mainnet
            return await self._fetch_jupiter_price(token_a, token_b)
        
        # Fallback to CoinGecko
        coingecko_id = price_service.get_coingecko_id(token_a, chain_id or 1)
        if coingecko_id:
            return await self._fetch_coingecko_price(coingecko_id)
        
        return None
    
    async def validate_price_freshness(self, price_data: PriceDataPoint) -> Dict[str, any]:
        """Validate price data freshness and return validation result"""
        staleness = self._calculate_staleness(price_data.timestamp)
        
        validation_result = {
            "is_fresh": self._is_data_fresh(price_data.timestamp),
            "is_stale": self._is_data_stale(price_data.timestamp),
            "is_expired": self._is_data_expired(price_data.timestamp),
            "staleness_seconds": staleness,
            "source": price_data.source.value,
            "timestamp": price_data.timestamp.isoformat(),
            "warnings": [],
            "errors": []
        }
        
        # Add warnings and errors
        if validation_result["is_expired"]:
            validation_result["errors"].append(f"Price data is expired ({staleness}s old)")
        elif validation_result["is_stale"]:
            validation_result["warnings"].append(f"Price data is stale ({staleness}s old)")
        
        return validation_result
    
    async def get_multiple_fresh_prices(self, token_pairs: List[Tuple[str, str, Optional[int]]]) -> Dict[str, PriceDataPoint]:
        """Get fresh prices for multiple token pairs"""
        tasks = []
        cache_keys = []
        
        for token_a, token_b, chain_id in token_pairs:
            cache_key = self._generate_cache_key(token_a, token_b, chain_id)
            cache_keys.append(cache_key)
            task = self.get_fresh_price(token_a, token_b, chain_id)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        prices = {}
        for i, result in enumerate(results):
            if isinstance(result, PriceDataPoint):
                prices[cache_keys[i]] = result
        
        return prices
    
    def start_auto_refresh(self, token_a: str, token_b: str, chain_id: Optional[int] = None):
        """Start automatic price refresh for a token pair"""
        cache_key = self._generate_cache_key(token_a, token_b, chain_id)
        
        if cache_key in self.refresh_tasks:
            return  # Already refreshing
        
        async def refresh_loop():
            while True:
                try:
                    await asyncio.sleep(self.config.refresh_interval_seconds)
                    await self.get_fresh_price(token_a, token_b, chain_id, force_refresh=True)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self.logger.error(f"Error in refresh loop for {cache_key}: {e}")
        
        self.refresh_tasks[cache_key] = asyncio.create_task(refresh_loop())
    
    def stop_auto_refresh(self, token_a: str, token_b: str, chain_id: Optional[int] = None):
        """Stop automatic price refresh for a token pair"""
        cache_key = self._generate_cache_key(token_a, token_b, chain_id)
        
        if cache_key in self.refresh_tasks:
            self.refresh_tasks[cache_key].cancel()
            del self.refresh_tasks[cache_key]
    
    def get_source_reliability(self) -> Dict[str, Dict[str, float]]:
        """Get reliability statistics for each data source"""
        reliability_stats = {}
        
        for source, stats in self.source_reliability.items():
            total = stats["success"] + stats["failure"]
            if total > 0:
                reliability_stats[source.value] = {
                    "success_rate": stats["success"] / total,
                    "total_requests": total,
                    "successful_requests": stats["success"],
                    "failed_requests": stats["failure"]
                }
            else:
                reliability_stats[source.value] = {
                    "success_rate": 0.0,
                    "total_requests": 0,
                    "successful_requests": 0,
                    "failed_requests": 0
                }
        
        return reliability_stats
    
    def clear_stale_cache(self):
        """Remove expired entries from cache"""
        expired_keys = []
        
        for cache_key, price_data in self.price_cache.items():
            if self._is_data_expired(price_data.timestamp):
                expired_keys.append(cache_key)
        
        for key in expired_keys:
            del self.price_cache[key]
            self.logger.info(f"Removed expired price data for {key}")
    
    async def health_check(self) -> Dict[str, any]:
        """Perform health check on price data sources"""
        health_status = {
            "overall_status": "healthy",
            "sources": {},
            "cache_size": len(self.price_cache),
            "active_refresh_tasks": len(self.refresh_tasks),
            "timestamp": datetime.now().isoformat()
        }
        
        # Check each source
        reliability_stats = self.get_source_reliability()
        
        for source_name, stats in reliability_stats.items():
            source_health = {
                "status": "healthy" if stats["success_rate"] >= 0.8 else "degraded" if stats["success_rate"] >= 0.5 else "unhealthy",
                "success_rate": stats["success_rate"],
                "total_requests": stats["total_requests"]
            }
            health_status["sources"][source_name] = source_health
            
            # Update overall status
            if source_health["status"] == "unhealthy":
                health_status["overall_status"] = "degraded"
        
        return health_status


# Global instance
price_freshness_validator = PriceFreshnessValidator()