"""
Uniswap V3 price feed service for EVM chains
"""
import asyncio
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from web3 import Web3
from web3.contract import Contract
import json
import aiohttp
from dataclasses import dataclass
from datetime import datetime, timedelta

from src.config.settings import settings


@dataclass
class PoolInfo:
    """Uniswap V3 pool information"""
    address: str
    token0: str
    token1: str
    fee: int
    liquidity: int
    sqrt_price_x96: int
    tick: int


@dataclass
class PriceQuote:
    """Price quote with impact calculation"""
    price: Decimal
    amount_out: Decimal
    price_impact: Decimal
    timestamp: datetime
    pool_address: str


class UniswapV3Service:
    """Uniswap V3 integration for price feeds and quotes"""
    
    # Uniswap V3 contract addresses by chain
    QUOTER_ADDRESSES = {
        1: "0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6",      # Ethereum
        137: "0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6",    # Polygon
        42161: "0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6",  # Arbitrum
        10: "0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6",     # Optimism
        8453: "0x3d4e44Eb1374240CE5F1B871ab261CD16335B76a",   # Base
    }
    
    FACTORY_ADDRESSES = {
        1: "0x1F98431c8aD98523631AE4a59f267346ea31F984",      # Ethereum
        137: "0x1F98431c8aD98523631AE4a59f267346ea31F984",    # Polygon
        42161: "0x1F98431c8aD98523631AE4a59f267346ea31F984",  # Arbitrum
        10: "0x1F98431c8aD98523631AE4a59f267346ea31F984",     # Optimism
        8453: "0x33128a8fC17869897dcE68Ed026d694621f6FDfD",   # Base
    }
    
    # Common fee tiers (in basis points)
    FEE_TIERS = [100, 500, 3000, 10000]  # 0.01%, 0.05%, 0.3%, 1%
    
    def __init__(self):
        self.web3_connections = {}
        self.quoter_contracts = {}
        self.factory_contracts = {}
        self.pool_cache = {}
        self.price_cache = {}
        self.cache_ttl = timedelta(seconds=30)  # 30 second cache
        
        # ABI definitions
        self.quoter_abi = [
            {
                "inputs": [
                    {"internalType": "bytes", "name": "path", "type": "bytes"},
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"}
                ],
                "name": "quoteExactInput",
                "outputs": [
                    {"internalType": "uint256", "name": "amountOut", "type": "uint256"},
                    {"internalType": "uint160[]", "name": "sqrtPriceX96AfterList", "type": "uint160[]"},
                    {"internalType": "uint32[]", "name": "initializedTicksCrossedList", "type": "uint32[]"},
                    {"internalType": "uint256", "name": "gasEstimate", "type": "uint256"}
                ],
                "stateMutability": "nonpayable",
                "type": "function"
            }
        ]
        
        self.factory_abi = [
            {
                "inputs": [
                    {"internalType": "address", "name": "tokenA", "type": "address"},
                    {"internalType": "address", "name": "tokenB", "type": "address"},
                    {"internalType": "uint24", "name": "fee", "type": "uint24"}
                ],
                "name": "getPool",
                "outputs": [{"internalType": "address", "name": "pool", "type": "address"}],
                "stateMutability": "view",
                "type": "function"
            }
        ]
        
        self.pool_abi = [
            {
                "inputs": [],
                "name": "slot0",
                "outputs": [
                    {"internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"},
                    {"internalType": "int24", "name": "tick", "type": "int24"},
                    {"internalType": "uint16", "name": "observationIndex", "type": "uint16"},
                    {"internalType": "uint16", "name": "observationCardinality", "type": "uint16"},
                    {"internalType": "uint16", "name": "observationCardinalityNext", "type": "uint16"},
                    {"internalType": "uint8", "name": "feeProtocol", "type": "uint8"},
                    {"internalType": "bool", "name": "unlocked", "type": "bool"}
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "liquidity",
                "outputs": [{"internalType": "uint128", "name": "", "type": "uint128"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "token0",
                "outputs": [{"internalType": "address", "name": "", "type": "address"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "token1",
                "outputs": [{"internalType": "address", "name": "", "type": "address"}],
                "stateMutability": "view",
                "type": "function"
            }
        ]
    
    def _get_web3_connection(self, chain_id: int) -> Optional[Web3]:
        """Get Web3 connection for chain"""
        if chain_id not in self.web3_connections:
            rpc_url = self._get_rpc_url(chain_id)
            if rpc_url:
                self.web3_connections[chain_id] = Web3(Web3.HTTPProvider(rpc_url))
        return self.web3_connections.get(chain_id)
    
    def _get_rpc_url(self, chain_id: int) -> Optional[str]:
        """Get RPC URL for chain"""
        rpc_urls = {
            1: settings.ethereum_rpc_url,
            137: settings.polygon_rpc_url,
            42161: settings.arbitrum_rpc_url,
            10: settings.optimism_rpc_url,
            8453: settings.base_rpc_url,
        }
        return rpc_urls.get(chain_id)
    
    def _get_quoter_contract(self, chain_id: int) -> Optional[Contract]:
        """Get Uniswap V3 quoter contract"""
        if chain_id not in self.quoter_contracts:
            web3 = self._get_web3_connection(chain_id)
            quoter_address = self.QUOTER_ADDRESSES.get(chain_id)
            if web3 and quoter_address:
                self.quoter_contracts[chain_id] = web3.eth.contract(
                    address=quoter_address,
                    abi=self.quoter_abi
                )
        return self.quoter_contracts.get(chain_id)
    
    def _get_factory_contract(self, chain_id: int) -> Optional[Contract]:
        """Get Uniswap V3 factory contract"""
        if chain_id not in self.factory_contracts:
            web3 = self._get_web3_connection(chain_id)
            factory_address = self.FACTORY_ADDRESSES.get(chain_id)
            if web3 and factory_address:
                self.factory_contracts[chain_id] = web3.eth.contract(
                    address=factory_address,
                    abi=self.factory_abi
                )
        return self.factory_contracts.get(chain_id)
    
    def _encode_path(self, tokens: List[str], fees: List[int]) -> bytes:
        """Encode path for multi-hop swaps"""
        if len(tokens) != len(fees) + 1:
            raise ValueError("Invalid path: tokens and fees length mismatch")
        
        path = tokens[0]
        for i, fee in enumerate(fees):
            path += fee.to_bytes(3, 'big').hex()
            path += tokens[i + 1][2:]  # Remove 0x prefix
        
        return bytes.fromhex(path[2:])  # Remove 0x prefix
    
    async def find_best_pools(self, token_a: str, token_b: str, chain_id: int) -> List[PoolInfo]:
        """Find best pools for token pair across all fee tiers"""
        factory = self._get_factory_contract(chain_id)
        web3 = self._get_web3_connection(chain_id)
        
        if not factory or not web3:
            return []
        
        pools = []
        for fee in self.FEE_TIERS:
            try:
                pool_address = factory.functions.getPool(token_a, token_b, fee).call()
                if pool_address != "0x0000000000000000000000000000000000000000":
                    pool_contract = web3.eth.contract(address=pool_address, abi=self.pool_abi)
                    
                    # Get pool state
                    slot0 = pool_contract.functions.slot0().call()
                    liquidity = pool_contract.functions.liquidity().call()
                    token0 = pool_contract.functions.token0().call()
                    token1 = pool_contract.functions.token1().call()
                    
                    pool_info = PoolInfo(
                        address=pool_address,
                        token0=token0,
                        token1=token1,
                        fee=fee,
                        liquidity=liquidity,
                        sqrt_price_x96=slot0[0],
                        tick=slot0[1]
                    )
                    pools.append(pool_info)
            except Exception as e:
                print(f"Error fetching pool for fee {fee}: {e}")
                continue
        
        # Sort by liquidity (higher is better)
        return sorted(pools, key=lambda p: p.liquidity, reverse=True)
    
    async def get_quote(self, token_in: str, token_out: str, amount_in: int, chain_id: int) -> Optional[PriceQuote]:
        """Get price quote for token swap"""
        cache_key = f"{token_in}_{token_out}_{amount_in}_{chain_id}"
        
        # Check cache
        if cache_key in self.price_cache:
            cached_quote, timestamp = self.price_cache[cache_key]
            if datetime.now() - timestamp < self.cache_ttl:
                return cached_quote
        
        quoter = self._get_quoter_contract(chain_id)
        if not quoter:
            return None
        
        try:
            # Find best pools
            pools = await self.find_best_pools(token_in, token_out, chain_id)
            if not pools:
                return None
            
            best_quote = None
            best_amount_out = 0
            
            for pool in pools[:3]:  # Try top 3 pools by liquidity
                try:
                    # Create path for single hop
                    path = self._encode_path([token_in, token_out], [pool.fee])
                    
                    # Get quote
                    result = quoter.functions.quoteExactInput(path, amount_in).call()
                    amount_out = result[0]
                    
                    if amount_out > best_amount_out:
                        # Calculate price
                        price = Decimal(amount_out) / Decimal(amount_in)
                        
                        # Calculate price impact (simplified)
                        price_impact = self._calculate_price_impact(pool, amount_in)
                        
                        best_quote = PriceQuote(
                            price=price,
                            amount_out=Decimal(amount_out),
                            price_impact=price_impact,
                            timestamp=datetime.now(),
                            pool_address=pool.address
                        )
                        best_amount_out = amount_out
                
                except Exception as e:
                    print(f"Error getting quote from pool {pool.address}: {e}")
                    continue
            
            # Cache result
            if best_quote:
                self.price_cache[cache_key] = (best_quote, datetime.now())
            
            return best_quote
        
        except Exception as e:
            print(f"Error getting Uniswap quote: {e}")
            return None
    
    def _calculate_price_impact(self, pool: PoolInfo, amount_in: int) -> Decimal:
        """Calculate price impact for trade"""
        try:
            # Simplified price impact calculation
            # In production, this would use more sophisticated math
            if pool.liquidity == 0:
                return Decimal("100")  # 100% impact if no liquidity
            
            # Rough approximation: impact = amount_in / liquidity * 100
            impact = (Decimal(amount_in) / Decimal(pool.liquidity)) * 100
            return min(impact, Decimal("100"))  # Cap at 100%
        
        except Exception:
            return Decimal("0")
    
    async def get_multiple_quotes(self, pairs: List[Tuple[str, str, int]], chain_id: int) -> Dict[str, PriceQuote]:
        """Get quotes for multiple token pairs"""
        tasks = []
        for token_in, token_out, amount_in in pairs:
            task = self.get_quote(token_in, token_out, amount_in, chain_id)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        quotes = {}
        for i, result in enumerate(results):
            if isinstance(result, PriceQuote):
                pair_key = f"{pairs[i][0]}_{pairs[i][1]}"
                quotes[pair_key] = result
        
        return quotes
    
    async def aggregate_pool_prices(self, token_a: str, token_b: str, chain_id: int) -> Optional[Decimal]:
        """Aggregate prices across multiple pools weighted by liquidity"""
        pools = await self.find_best_pools(token_a, token_b, chain_id)
        if not pools:
            return None
        
        total_liquidity = sum(pool.liquidity for pool in pools)
        if total_liquidity == 0:
            return None
        
        weighted_price = Decimal("0")
        
        for pool in pools:
            try:
                # Calculate price from sqrt_price_x96
                sqrt_price = Decimal(pool.sqrt_price_x96)
                price = (sqrt_price / Decimal(2**96)) ** 2
                
                # Adjust for token order
                if pool.token0.lower() != token_a.lower():
                    price = Decimal("1") / price
                
                # Weight by liquidity
                weight = Decimal(pool.liquidity) / Decimal(total_liquidity)
                weighted_price += price * weight
            
            except Exception as e:
                print(f"Error calculating price for pool {pool.address}: {e}")
                continue
        
        return weighted_price if weighted_price > 0 else None
    
    def is_supported_chain(self, chain_id: int) -> bool:
        """Check if chain is supported for Uniswap V3"""
        return chain_id in self.QUOTER_ADDRESSES


# Global instance
uniswap_v3_service = UniswapV3Service()