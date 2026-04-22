"""
Cross-chain bridge service using LI.FI
"""
import aiohttp
import json
from typing import Dict, Optional, List
from decimal import Decimal

from src.config.settings import settings


class BridgeService:
    def __init__(self):
        self.base_url = settings.lifi_base_url
        self.api_key = settings.lifi_api_key
    
    async def _make_request(self, endpoint: str, params: Dict = None, method: str = "GET", data: Dict = None) -> Optional[Dict]:
        """Make HTTP request to LI.FI API"""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["x-lifi-api-key"] = self.api_key
        
        try:
            async with aiohttp.ClientSession() as session:
                if method == "GET":
                    async with session.get(
                        f"{self.base_url}{endpoint}",
                        params=params,
                        headers=headers
                    ) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            print(f"LI.FI API error: {response.status}")
                            return None
                elif method == "POST":
                    async with session.post(
                        f"{self.base_url}{endpoint}",
                        json=data,
                        headers=headers
                    ) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            print(f"LI.FI API error: {response.status}")
                            return None
        except Exception as e:
            print(f"Error making LI.FI request: {e}")
            return None
    
    async def get_chains(self) -> Optional[Dict]:
        """Get supported chains"""
        endpoint = "/chains"
        return await self._make_request(endpoint)
    
    async def get_tokens(self, chain_id: Optional[int] = None) -> Optional[Dict]:
        """Get supported tokens"""
        endpoint = "/tokens"
        params = {}
        if chain_id:
            params["chains"] = str(chain_id)
        
        return await self._make_request(endpoint, params)
    
    async def get_quote(
        self,
        from_chain: int,
        to_chain: int,
        from_token: str,
        to_token: str,
        from_amount: str,
        from_address: str,
        to_address: str,
        slippage: float = 0.03  # 3%
    ) -> Optional[Dict]:
        """Get bridge quote"""
        data = {
            "fromChain": from_chain,
            "toChain": to_chain,
            "fromToken": from_token,
            "toToken": to_token,
            "fromAmount": from_amount,
            "fromAddress": from_address,
            "toAddress": to_address,
            "options": {
                "slippage": slippage,
                "allowBridges": ["across", "stargate", "hop", "cbridge"],
                "allowExchanges": ["1inch", "paraswap", "0x"]
            }
        }
        
        endpoint = "/quote"
        return await self._make_request(endpoint, method="POST", data=data)
    
    async def get_routes(
        self,
        from_chain: int,
        to_chain: int,
        from_token: str,
        to_token: str,
        from_amount: str,
        from_address: str,
        to_address: str
    ) -> Optional[Dict]:
        """Get available bridge routes"""
        params = {
            "fromChain": from_chain,
            "toChain": to_chain,
            "fromToken": from_token,
            "toToken": to_token,
            "fromAmount": from_amount,
            "fromAddress": from_address,
            "toAddress": to_address
        }
        
        endpoint = "/routes"
        return await self._make_request(endpoint, params)
    
    async def get_status(self, tx_hash: str, bridge: str, from_chain: int, to_chain: int) -> Optional[Dict]:
        """Get bridge transaction status"""
        params = {
            "txHash": tx_hash,
            "bridge": bridge,
            "fromChain": from_chain,
            "toChain": to_chain
        }
        
        endpoint = "/status"
        return await self._make_request(endpoint, params)
    
    async def get_tools(self) -> Optional[Dict]:
        """Get available bridge tools/protocols"""
        endpoint = "/tools"
        return await self._make_request(endpoint)


# Global instance
bridge_service = BridgeService()