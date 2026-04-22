"""
Wallet Service
Manages wallet balance retrieval, token balances, and portfolio value calculations
with caching to reduce RPC calls.
"""
import time
import logging
from typing import Dict, List, Optional
from decimal import Decimal
from dataclasses import dataclass
from web3 import Web3

from src.services.dex_executor import DEXExecutor
from src.services.advanced_price_oracle import price_oracle, PriceData

logger = logging.getLogger(__name__)


@dataclass
class TokenBalance:
    """Token balance data structure"""
    symbol: str
    name: str
    address: str
    balance: str  # Human-readable balance
    balance_wei: int  # Raw balance in wei
    usd_value: float
    change_24h: float = 0.0


@dataclass
class WalletBalance:
    """Complete wallet balance data"""
    address: str
    eth_balance: str
    eth_balance_wei: int
    eth_usd_value: float
    token_balances: List[TokenBalance]
    total_value_usd: float
    last_update: int  # Unix timestamp


@dataclass
class CachedData:
    """Cached data with expiry"""
    data: any
    expiry: float


class WalletService:
    """
    Service for managing wallet data with caching
    """
    
    # Cache TTL in seconds
    CACHE_TTL = 10
    
    # Supported tokens configuration
    SUPPORTED_TOKENS = {
        'USDC': {
            'name': 'USD Coin',
            'decimals': 6  # USDC uses 6 decimals
        },
        'WETH': {
            'name': 'Wrapped Ether',
            'decimals': 18
        }
    }
    
    def __init__(self, network: str = 'sepolia'):
        """
        Initialize wallet service
        
        Args:
            network: Network to use (default: sepolia)
        """
        self.network = network
        self.dex_executor = DEXExecutor(network=network)
        self._cache: Dict[str, CachedData] = {}
        logger.info(f"WalletService initialized for network: {network}")
    
    def _get_cache_key(self, prefix: str, address: str) -> str:
        """Generate cache key"""
        return f"{prefix}:{address.lower()}"
    
    def _get_cached(self, key: str) -> Optional[any]:
        """Get cached data if not expired"""
        if key in self._cache:
            cached = self._cache[key]
            if time.time() < cached.expiry:
                logger.debug(f"Cache hit for key: {key}")
                return cached.data
            else:
                # Remove expired cache
                del self._cache[key]
                logger.debug(f"Cache expired for key: {key}")
        return None
    
    def _set_cache(self, key: str, data: any) -> None:
        """Cache data with TTL"""
        self._cache[key] = CachedData(
            data=data,
            expiry=time.time() + self.CACHE_TTL
        )
        logger.debug(f"Cached data for key: {key}")
    
    async def get_balance(self, address: str) -> WalletBalance:
        """
        Get complete wallet balance including ETH and all supported tokens
        
        Args:
            address: Wallet address
            
        Returns:
            WalletBalance with all balance information
        """
        cache_key = self._get_cache_key("balance", address)
        
        # Check cache first
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            # Get ETH balance
            eth_balance_wei = self.dex_executor.w3.eth.get_balance(address)
            eth_balance = float(self.dex_executor.w3.from_wei(eth_balance_wei, 'ether'))
            
            # Get ETH price in USD
            eth_price_data = await price_oracle.get_price("ETH")
            eth_price_usd = float(eth_price_data.price) if eth_price_data else 0.0
            eth_usd_value = eth_balance * eth_price_usd
            
            # Get token balances
            token_balances = await self.get_token_balances(address)
            
            # Calculate total portfolio value
            total_value_usd = eth_usd_value + sum(
                token.usd_value for token in token_balances
            )
            
            wallet_balance = WalletBalance(
                address=address,
                eth_balance=f"{eth_balance:.4f}",
                eth_balance_wei=eth_balance_wei,
                eth_usd_value=eth_usd_value,
                token_balances=token_balances,
                total_value_usd=total_value_usd,
                last_update=int(time.time())
            )
            
            # Cache the result
            self._set_cache(cache_key, wallet_balance)
            
            logger.info(
                f"Fetched balance for {address}: "
                f"ETH={eth_balance:.4f}, Total USD=${total_value_usd:.2f}"
            )
            
            return wallet_balance
            
        except Exception as e:
            logger.error(f"Failed to get balance for {address}: {e}")
            raise
    
    async def get_token_balances(self, address: str) -> List[TokenBalance]:
        """
        Get ERC-20 token balances for all supported tokens
        
        Args:
            address: Wallet address
            
        Returns:
            List of TokenBalance objects
        """
        cache_key = self._get_cache_key("tokens", address)
        
        # Check cache first
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        token_balances = []
        
        try:
            for symbol, token_info in self.SUPPORTED_TOKENS.items():
                try:
                    # Get token address from DEX executor
                    token_address = self.dex_executor._get_token_address(symbol)
                    
                    # Get token balance
                    token_contract = self.dex_executor.w3.eth.contract(
                        address=token_address,
                        abi=self.dex_executor.ERC20_ABI
                    )
                    balance_wei = token_contract.functions.balanceOf(address).call()
                    
                    # Convert to human-readable format
                    decimals = token_info['decimals']
                    balance = balance_wei / (10 ** decimals)
                    
                    # Get token price in USD
                    price_data = await price_oracle.get_price(symbol)
                    token_price_usd = float(price_data.price) if price_data else 0.0
                    change_24h = price_data.change_24h if price_data else 0.0
                    
                    # Calculate USD value
                    usd_value = balance * token_price_usd
                    
                    token_balance = TokenBalance(
                        symbol=symbol,
                        name=token_info['name'],
                        address=token_address,
                        balance=f"{balance:.6f}",
                        balance_wei=balance_wei,
                        usd_value=usd_value,
                        change_24h=change_24h
                    )
                    
                    token_balances.append(token_balance)
                    
                    logger.debug(
                        f"Token {symbol} balance for {address}: "
                        f"{balance:.6f} (${usd_value:.2f})"
                    )
                    
                except Exception as e:
                    logger.warning(f"Failed to get {symbol} balance: {e}")
                    # Continue with other tokens even if one fails
                    continue
            
            # Cache the result
            self._set_cache(cache_key, token_balances)
            
            return token_balances
            
        except Exception as e:
            logger.error(f"Failed to get token balances for {address}: {e}")
            raise
    
    async def calculate_portfolio_value(self, address: str) -> Decimal:
        """
        Calculate total portfolio value in USD
        
        Args:
            address: Wallet address
            
        Returns:
            Total portfolio value in USD as Decimal
        """
        try:
            # Get complete wallet balance
            wallet_balance = await self.get_balance(address)
            
            # Return as Decimal for precision
            return Decimal(str(wallet_balance.total_value_usd))
            
        except Exception as e:
            logger.error(f"Failed to calculate portfolio value for {address}: {e}")
            raise
    
    def clear_cache(self, address: Optional[str] = None) -> None:
        """
        Clear cache for a specific address or all addresses
        
        Args:
            address: Wallet address to clear cache for (None = clear all)
        """
        if address:
            # Clear cache for specific address
            keys_to_remove = [
                key for key in self._cache.keys()
                if address.lower() in key
            ]
            for key in keys_to_remove:
                del self._cache[key]
            logger.info(f"Cleared cache for address: {address}")
        else:
            # Clear all cache
            self._cache.clear()
            logger.info("Cleared all wallet service cache")


# Global wallet service instance
wallet_service = WalletService()
