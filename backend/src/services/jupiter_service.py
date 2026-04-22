"""
Jupiter aggregator service for Solana token prices and swaps
"""
import aiohttp
import asyncio
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

from src.config.settings import settings


@dataclass
class JupiterQuote:
    """Jupiter price quote"""
    input_mint: str
    output_mint: str
    in_amount: int
    out_amount: int
    price_impact_pct: Decimal
    market_infos: List[Dict]
    timestamp: datetime
    route_plan: List[Dict]


@dataclass
class SolanaTokenInfo:
    """Solana token information"""
    address: str
    symbol: str
    name: str
    decimals: int
    logo_uri: Optional[str] = None
    tags: List[str] = None


class JupiterService:
    """Jupiter aggregator integration for Solana"""
    
    BASE_URL = "https://quote-api.jup.ag/v6"
    PRICE_API_URL = "https://price.jup.ag/v4"
    
    # Common Solana token addresses
    COMMON_TOKENS = {
        "SOL": "So11111111111111111111111111111111111111112",
        "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        "USDT": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
        "RAY": "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R",
        "SRM": "SRMuApVNdxXokk5GT7XD5cUUgXMBCoAz2LHeuAoKWRt",
        "ORCA": "orcaEKTdK7LKz57vaAYr9QeNsVEPfiu6QeMU1kektZE",
        "MNGO": "MangoCzJ36AjZyKwVj3VnYU4GTonjfVEnJmvvWaxLac",
    }
    
    def __init__(self):
        self.token_list_cache = {}
        self.price_cache = {}
        self.quote_cache = {}
        self.cache_ttl = timedelta(seconds=30)  # 30 second cache
        self.token_list_ttl = timedelta(hours=1)  # 1 hour for token list
    
    async def _make_request(self, url: str, params: Dict = None) -> Optional[Dict]:
        """Make HTTP request to Jupiter API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        print(f"Jupiter API error: {response.status} - {await response.text()}")
                        return None
        except Exception as e:
            print(f"Error making Jupiter request: {e}")
            return None
    
    async def get_token_list(self) -> List[SolanaTokenInfo]:
        """Get list of all tokens supported by Jupiter"""
        cache_key = "token_list"
        
        # Check cache
        if cache_key in self.token_list_cache:
            tokens, timestamp = self.token_list_cache[cache_key]
            if datetime.now() - timestamp < self.token_list_ttl:
                return tokens
        
        url = f"{self.BASE_URL}/tokens"
        result = await self._make_request(url)
        
        if not result:
            return []
        
        tokens = []
        for token_data in result:
            token = SolanaTokenInfo(
                address=token_data.get("address", ""),
                symbol=token_data.get("symbol", ""),
                name=token_data.get("name", ""),
                decimals=token_data.get("decimals", 0),
                logo_uri=token_data.get("logoURI"),
                tags=token_data.get("tags", [])
            )
            tokens.append(token)
        
        # Cache result
        self.token_list_cache[cache_key] = (tokens, datetime.now())
        return tokens
    
    async def get_quote(self, input_mint: str, output_mint: str, amount: int, slippage_bps: int = 50) -> Optional[JupiterQuote]:
        """Get swap quote from Jupiter"""
        cache_key = f"{input_mint}_{output_mint}_{amount}_{slippage_bps}"
        
        # Check cache
        if cache_key in self.quote_cache:
            quote, timestamp = self.quote_cache[cache_key]
            if datetime.now() - timestamp < self.cache_ttl:
                return quote
        
        params = {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": str(amount),
            "slippageBps": str(slippage_bps),
            "onlyDirectRoutes": "false",
            "asLegacyTransaction": "false"
        }
        
        url = f"{self.BASE_URL}/quote"
        result = await self._make_request(url, params)
        
        if not result:
            return None
        
        try:
            quote = JupiterQuote(
                input_mint=result["inputMint"],
                output_mint=result["outputMint"],
                in_amount=int(result["inAmount"]),
                out_amount=int(result["outAmount"]),
                price_impact_pct=Decimal(result.get("priceImpactPct", "0")),
                market_infos=result.get("marketInfos", []),
                timestamp=datetime.now(),
                route_plan=result.get("routePlan", [])
            )
            
            # Cache result
            self.quote_cache[cache_key] = (quote, datetime.now())
            return quote
        
        except Exception as e:
            print(f"Error parsing Jupiter quote: {e}")
            return None
    
    async def get_token_price(self, token_mint: str, vs_token: str = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v") -> Optional[Decimal]:
        """Get token price in terms of another token (default USDC)"""
        cache_key = f"price_{token_mint}_{vs_token}"
        
        # Check cache
        if cache_key in self.price_cache:
            price, timestamp = self.price_cache[cache_key]
            if datetime.now() - timestamp < self.cache_ttl:
                return price
        
        params = {
            "ids": token_mint,
            "vsToken": vs_token
        }
        
        url = f"{self.PRICE_API_URL}/price"
        result = await self._make_request(url, params)
        
        if not result or "data" not in result:
            return None
        
        try:
            price_data = result["data"].get(token_mint)
            if price_data and "price" in price_data:
                price = Decimal(str(price_data["price"]))
                
                # Cache result
                self.price_cache[cache_key] = (price, datetime.now())
                return price
        
        except Exception as e:
            print(f"Error parsing Jupiter price: {e}")
        
        return None
    
    async def get_multiple_prices(self, token_mints: List[str], vs_token: str = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v") -> Dict[str, Decimal]:
        """Get prices for multiple tokens"""
        params = {
            "ids": ",".join(token_mints),
            "vsToken": vs_token
        }
        
        url = f"{self.PRICE_API_URL}/price"
        result = await self._make_request(url, params)
        
        prices = {}
        if result and "data" in result:
            for token_mint in token_mints:
                price_data = result["data"].get(token_mint)
                if price_data and "price" in price_data:
                    try:
                        prices[token_mint] = Decimal(str(price_data["price"]))
                    except Exception as e:
                        print(f"Error parsing price for {token_mint}: {e}")
        
        return prices
    
    async def validate_token_pair(self, input_mint: str, output_mint: str) -> bool:
        """Validate if token pair is supported for swapping"""
        try:
            # Try to get a small quote to validate the pair
            quote = await self.get_quote(input_mint, output_mint, 1000000)  # 1 token with 6 decimals
            return quote is not None
        except Exception:
            return False
    
    async def get_supported_tokens_for_pair(self, base_token: str) -> List[str]:
        """Get list of tokens that can be swapped with base token"""
        tokens = await self.get_token_list()
        supported = []
        
        # Test a sample of tokens to see which ones work
        test_tokens = [token.address for token in tokens[:50]]  # Test first 50 tokens
        
        tasks = []
        for token_address in test_tokens:
            if token_address != base_token:
                task = self.validate_token_pair(base_token, token_address)
                tasks.append((token_address, task))
        
        results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, bool) and result:
                supported.append(test_tokens[i])
        
        return supported
    
    def get_token_address(self, symbol: str) -> Optional[str]:
        """Get token address by symbol"""
        return self.COMMON_TOKENS.get(symbol.upper())
    
    async def compare_cross_chain_prices(self, solana_token: str, evm_token_symbol: str) -> Dict[str, Decimal]:
        """Compare Solana token price with EVM equivalent"""
        prices = {}
        
        # Get Solana price
        sol_price = await self.get_token_price(solana_token)
        if sol_price:
            prices["solana"] = sol_price
        
        # For cross-chain comparison, we'd need to integrate with other price sources
        # This is a placeholder for the comparison logic
        prices["comparison_available"] = len(prices) > 0
        
        return prices
    
    async def get_route_info(self, input_mint: str, output_mint: str, amount: int) -> Optional[Dict]:
        """Get detailed route information for a swap"""
        quote = await self.get_quote(input_mint, output_mint, amount)
        if not quote:
            return None
        
        route_info = {
            "input_token": input_mint,
            "output_token": output_mint,
            "input_amount": quote.in_amount,
            "output_amount": quote.out_amount,
            "price_impact": quote.price_impact_pct,
            "route_plan": quote.route_plan,
            "market_infos": quote.market_infos,
            "timestamp": quote.timestamp.isoformat()
        }
        
        return route_info
    
    async def estimate_fees(self, input_mint: str, output_mint: str, amount: int) -> Dict[str, Decimal]:
        """Estimate fees for Jupiter swap"""
        quote = await self.get_quote(input_mint, output_mint, amount)
        if not quote:
            return {}
        
        fees = {
            "platform_fee": Decimal("0"),  # Jupiter doesn't charge platform fees
            "price_impact": quote.price_impact_pct,
            "estimated_slippage": Decimal("0.5"),  # Default 0.5% slippage
        }
        
        # Calculate implicit fees from market infos
        total_fee_pct = Decimal("0")
        for market_info in quote.market_infos:
            if "lpFee" in market_info:
                fee_pct = Decimal(str(market_info["lpFee"].get("pct", 0)))
                total_fee_pct += fee_pct
        
        fees["liquidity_provider_fees"] = total_fee_pct
        
        return fees


# Global instance
jupiter_service = JupiterService()