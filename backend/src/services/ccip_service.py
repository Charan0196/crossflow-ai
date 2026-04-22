"""
Chainlink CCIP (Cross-Chain Interoperability Protocol) service
"""
import asyncio
import json
import logging
from typing import Dict, Optional, List, Any
from dataclasses import dataclass
from enum import Enum
import aiohttp
from web3 import Web3
from decimal import Decimal

from src.config.settings import settings


logger = logging.getLogger(__name__)


@dataclass
class CCIPRouter:
    """CCIP router configuration for a chain"""
    chain_id: int
    router_address: str
    rpc_url: str
    ccip_chain_selector: str  # CCIP specific chain selector


@dataclass
class CCIPMessage:
    """CCIP message structure"""
    id: str
    source_chain: int
    destination_chain: int
    receiver: str
    data: bytes
    token_amounts: List[Dict] = None
    fee_token: str = ""
    gas_limit: int = 200000


class CCIPService:
    """Chainlink CCIP integration service"""
    
    def __init__(self):
        self.routers = self._initialize_routers()
        self.web3_instances = {}
        self._initialize_web3_connections()
    
    def _initialize_routers(self) -> Dict[int, CCIPRouter]:
        """Initialize CCIP routers for supported chains"""
        return {
            1: CCIPRouter(  # Ethereum
                chain_id=1,
                router_address="0x80226fc0Ee2b096224EeAc085Bb9a8cba1146f7D",
                rpc_url=settings.ethereum_rpc,
                ccip_chain_selector="5009297550715157269"
            ),
            137: CCIPRouter(  # Polygon
                chain_id=137,
                router_address="0x849c5ED5a80F5B408Dd4969b78c2C8fdf0565Bfe",
                rpc_url=settings.polygon_rpc,
                ccip_chain_selector="4051577828743386545"
            ),
            56: CCIPRouter(  # BSC
                chain_id=56,
                router_address="0x34B03Cb9086d7D758AC55af71584F81A598759FE",
                rpc_url=settings.bsc_rpc,
                ccip_chain_selector="11344663589394136015"
            ),
            42161: CCIPRouter(  # Arbitrum
                chain_id=42161,
                router_address="0x141fa059441E0ca23ce184B6A78bafD2A517DdE8",
                rpc_url=settings.arbitrum_rpc,
                ccip_chain_selector="4949039107694359620"
            ),
            10: CCIPRouter(  # Optimism
                chain_id=10,
                router_address="0x3206695CaE29952f4b0c22a169725a865bc8Ce0f",
                rpc_url=settings.optimism_rpc,
                ccip_chain_selector="3734403246176062136"
            ),
            8453: CCIPRouter(  # Base
                chain_id=8453,
                router_address="0x881e3A65B4d4a04dD529061dd0071cf975F58bCD",
                rpc_url="https://mainnet.base.org",
                ccip_chain_selector="15971525489660198786"
            )
        }
    
    def _initialize_web3_connections(self):
        """Initialize Web3 connections for all supported chains"""
        for chain_id, router in self.routers.items():
            try:
                self.web3_instances[chain_id] = Web3(Web3.HTTPProvider(router.rpc_url))
                logger.info(f"Initialized CCIP Web3 connection for chain {chain_id}")
            except Exception as e:
                logger.error(f"Failed to initialize CCIP Web3 for chain {chain_id}: {e}")
    
    def get_router(self, chain_id: int) -> Optional[CCIPRouter]:
        """Get CCIP router for a specific chain"""
        return self.routers.get(chain_id)
    
    def get_web3(self, chain_id: int) -> Optional[Web3]:
        """Get Web3 instance for a specific chain"""
        return self.web3_instances.get(chain_id)
    
    async def send_message(
        self,
        source_chain: int,
        destination_chain: int,
        receiver: str,
        data: bytes,
        token_amounts: Optional[List[Dict]] = None,
        gas_limit: int = 200000
    ) -> Optional[Dict]:
        """Send cross-chain message via Chainlink CCIP"""
        try:
            source_router = self.get_router(source_chain)
            dest_router = self.get_router(destination_chain)
            
            if not source_router or not dest_router:
                logger.error(f"Unsupported CCIP chain: {source_chain} -> {destination_chain}")
                return None
            
            web3 = self.get_web3(source_chain)
            if not web3:
                logger.error(f"No Web3 connection for CCIP chain {source_chain}")
                return None
            
            # Create CCIP message
            message = CCIPMessage(
                id=f"ccip_{source_chain}_{destination_chain}_{web3.eth.get_block_number()}",
                source_chain=source_chain,
                destination_chain=destination_chain,
                receiver=receiver,
                data=data,
                token_amounts=token_amounts or [],
                gas_limit=gas_limit
            )
            
            # Estimate fees
            fee_estimate = await self.estimate_fees(
                source_chain,
                destination_chain,
                data,
                token_amounts,
                gas_limit
            )
            
            if not fee_estimate:
                logger.error("Failed to estimate CCIP fees")
                return None
            
            logger.info(f"Sending CCIP message: {message.id}")
            logger.info(f"Estimated fee: {fee_estimate}")
            
            return {
                "message_id": message.id,
                "source_chain": source_chain,
                "destination_chain": destination_chain,
                "estimated_fee": fee_estimate,
                "status": "prepared",
                "data_size": len(data),
                "router_address": source_router.router_address
            }
            
        except Exception as e:
            logger.error(f"Error sending CCIP message: {e}")
            return None
    
    async def estimate_fees(
        self,
        source_chain: int,
        destination_chain: int,
        data: bytes,
        token_amounts: Optional[List[Dict]] = None,
        gas_limit: int = 200000
    ) -> Optional[Dict]:
        """Estimate CCIP messaging fees"""
        try:
            source_router = self.get_router(source_chain)
            dest_router = self.get_router(destination_chain)
            
            if not source_router or not dest_router:
                return None
            
            # Mock fee estimation (in production, this would call CCIP router contracts)
            base_fee = 0.002  # ETH - CCIP typically has higher fees than LayerZero
            data_fee = len(data) * 0.00002  # Per byte
            gas_fee = gas_limit * 0.000000025  # 25 gwei
            token_fee = 0.0001 if token_amounts else 0  # Additional fee for token transfers
            
            total_fee = base_fee + data_fee + gas_fee + token_fee
            
            return {
                "fee": str(total_fee),
                "fee_token": "ETH",  # Native token of source chain
                "base_fee": str(base_fee),
                "data_fee": str(data_fee),
                "gas_fee": str(gas_fee),
                "token_fee": str(token_fee)
            }
            
        except Exception as e:
            logger.error(f"Error estimating CCIP fees: {e}")
            return None
    
    async def verify_message(self, message_id: str, source_chain: int) -> Optional[Dict]:
        """Verify CCIP message authenticity and status"""
        try:
            web3 = self.get_web3(source_chain)
            if not web3:
                return None
            
            # Mock verification (in production, this would check CCIP contracts)
            verification_result = {
                "message_id": message_id,
                "verified": True,
                "block_number": web3.eth.get_block_number(),
                "timestamp": web3.eth.get_block('latest')['timestamp'],
                "status": "verified",
                "protocol": "CCIP"
            }
            
            logger.info(f"CCIP message verification result: {verification_result}")
            return verification_result
            
        except Exception as e:
            logger.error(f"Error verifying CCIP message: {e}")
            return None
    
    async def get_message_status(self, message_id: str, source_chain: int) -> Optional[Dict]:
        """Get status of a CCIP cross-chain message"""
        try:
            # Mock status check (in production, this would query CCIP infrastructure)
            status_info = {
                "message_id": message_id,
                "status": "success",
                "source_chain": source_chain,
                "confirmations": 15,  # CCIP typically requires more confirmations
                "delivery_time": "2024-01-02T10:35:00Z",
                "protocol": "CCIP"
            }
            
            return status_info
            
        except Exception as e:
            logger.error(f"Error getting CCIP message status: {e}")
            return None
    
    def is_chain_supported(self, chain_id: int) -> bool:
        """Check if a chain is supported by CCIP"""
        return chain_id in self.routers
    
    def get_supported_chains(self) -> List[int]:
        """Get list of supported chain IDs"""
        return list(self.routers.keys())
    
    async def get_supported_tokens(self, chain_id: int) -> Optional[List[str]]:
        """Get supported tokens for CCIP on a specific chain"""
        try:
            router = self.get_router(chain_id)
            if not router:
                return None
            
            # Mock supported tokens (in production, this would query CCIP contracts)
            supported_tokens = [
                "0xA0b86a33E6441E6C8D3C1C4C9C8C8C8C8C8C8C8C",  # USDC
                "0xdAC17F958D2ee523a2206206994597C13D831ec7",  # USDT
                "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",  # WBTC
                "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"   # WETH
            ]
            
            return supported_tokens
            
        except Exception as e:
            logger.error(f"Error getting supported tokens: {e}")
            return None


# Global instance
ccip_service = CCIPService()