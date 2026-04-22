"""
DEX aggregator service for token swaps using 1inch
"""
import aiohttp
import json
from typing import Dict, Optional, List
from decimal import Decimal

from src.config.settings import settings


class DexService:
    def __init__(self):
        self.base_url = settings.oneinch_base_url
        self.api_key = settings.oneinch_api_key
        
        # Chain ID mapping for 1inch
        self.supported_chains = {
            1: "ethereum",
            137: "polygon", 
            42161: "arbitrum",
            10: "optimism",
            56: "bsc"
        }
    
    async def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make HTTP request to 1inch API"""
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
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
                        print(f"1inch API error: {response.status}")
                        return None
        except Exception as e:
            print(f"Error making 1inch request: {e}")
            return None
    
    async def get_tokens(self, chain_id: int) -> Optional[Dict]:
        """Get list of supported tokens for a chain"""
        if chain_id not in self.supported_chains:
            return None
        
        endpoint = f"/swap/v6.0/{chain_id}/tokens"
        return await self._make_request(endpoint)
    
    async def get_quote(
        self,
        chain_id: int,
        from_token: str,
        to_token: str,
        amount: str,
        slippage: float = 1.0
    ) -> Optional[Dict]:
        """Get swap quote from 1inch"""
        if chain_id not in self.supported_chains:
            return None
        
        params = {
            "src": from_token,
            "dst": to_token,
            "amount": amount,
            "includeTokensInfo": "true",
            "includeProtocols": "true"
        }
        
        endpoint = f"/swap/v6.0/{chain_id}/quote"
        return await self._make_request(endpoint, params)
    
    async def get_swap_data(
        self,
        chain_id: int,
        from_token: str,
        to_token: str,
        amount: str,
        from_address: str,
        slippage: float = 1.0,
        disable_estimate: bool = True
    ) -> Optional[Dict]:
        """Get swap transaction data from 1inch"""
        if chain_id not in self.supported_chains:
            return None
        
        params = {
            "src": from_token,
            "dst": to_token,
            "amount": amount,
            "from": from_address,
            "slippage": str(slippage),
            "disableEstimate": str(disable_estimate).lower()
        }
        
        endpoint = f"/swap/v6.0/{chain_id}/swap"
        return await self._make_request(endpoint, params)
    
    async def get_allowance(
        self,
        chain_id: int,
        token_address: str,
        wallet_address: str
    ) -> Optional[Dict]:
        """Check token allowance for 1inch router"""
        if chain_id not in self.supported_chains:
            return None
        
        params = {
            "tokenAddress": token_address,
            "walletAddress": wallet_address
        }
        
        endpoint = f"/swap/v6.0/{chain_id}/approve/allowance"
        return await self._make_request(endpoint, params)
    
    async def get_approve_transaction(
        self,
        chain_id: int,
        token_address: str,
        amount: Optional[str] = None
    ) -> Optional[Dict]:
        """Get approve transaction data"""
        if chain_id not in self.supported_chains:
            return None
        
        params = {"tokenAddress": token_address}
        if amount:
            params["amount"] = amount
        
        endpoint = f"/swap/v6.0/{chain_id}/approve/transaction"
        return await self._make_request(endpoint, params)
    
    async def get_protocols(self, chain_id: int) -> Optional[Dict]:
        """Get available DEX protocols for a chain"""
        if chain_id not in self.supported_chains:
            return None
        
        endpoint = f"/swap/v6.0/{chain_id}/liquidity-sources"
        return await self._make_request(endpoint)


# Global instance
dex_service = DexService()