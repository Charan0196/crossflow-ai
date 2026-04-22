"""
LayerZero V2 cross-chain messaging service
"""
import asyncio
import json
import logging
from typing import Dict, Optional, List, Any
from dataclasses import dataclass
from enum import Enum
import aiohttp
from web3 import Web3
from eth_account import Account
from decimal import Decimal

from src.config.settings import settings


logger = logging.getLogger(__name__)


class ChainId(Enum):
    """Supported chain IDs for LayerZero V2"""
    ETHEREUM = 1
    POLYGON = 137
    BSC = 56
    ARBITRUM = 42161
    OPTIMISM = 10
    BASE = 8453


@dataclass
class LayerZeroEndpoint:
    """LayerZero endpoint configuration for a chain"""
    chain_id: int
    endpoint_address: str
    rpc_url: str
    lz_chain_id: int  # LayerZero specific chain ID


@dataclass
class CrossChainMessage:
    """Cross-chain message structure"""
    id: str
    source_chain: int
    destination_chain: int
    payload: bytes
    gas_limit: int
    recipient: str
    sender: str
    nonce: int
    status: str = "pending"


class LayerZeroService:
    """LayerZero V2 integration service"""
    
    def __init__(self):
        self.endpoints = self._initialize_endpoints()
        self.web3_instances = {}
        self._initialize_web3_connections()
    
    def _initialize_endpoints(self) -> Dict[int, LayerZeroEndpoint]:
        """Initialize LayerZero endpoints for supported chains"""
        return {
            ChainId.ETHEREUM.value: LayerZeroEndpoint(
                chain_id=1,
                endpoint_address="0x1a44076050125825900e736c501f859c50fE728c",  # LayerZero V2 Endpoint
                rpc_url=settings.ethereum_rpc,
                lz_chain_id=30101
            ),
            ChainId.POLYGON.value: LayerZeroEndpoint(
                chain_id=137,
                endpoint_address="0x1a44076050125825900e736c501f859c50fE728c",
                rpc_url=settings.polygon_rpc,
                lz_chain_id=30109
            ),
            ChainId.BSC.value: LayerZeroEndpoint(
                chain_id=56,
                endpoint_address="0x1a44076050125825900e736c501f859c50fE728c",
                rpc_url=settings.bsc_rpc,
                lz_chain_id=30102
            ),
            ChainId.ARBITRUM.value: LayerZeroEndpoint(
                chain_id=42161,
                endpoint_address="0x1a44076050125825900e736c501f859c50fE728c",
                rpc_url=settings.arbitrum_rpc,
                lz_chain_id=30110
            ),
            ChainId.OPTIMISM.value: LayerZeroEndpoint(
                chain_id=10,
                endpoint_address="0x1a44076050125825900e736c501f859c50fE728c",
                rpc_url=settings.optimism_rpc,
                lz_chain_id=30111
            ),
            ChainId.BASE.value: LayerZeroEndpoint(
                chain_id=8453,
                endpoint_address="0x1a44076050125825900e736c501f859c50fE728c",
                rpc_url="https://mainnet.base.org",  # Default Base RPC
                lz_chain_id=30184
            )
        }
    
    def _initialize_web3_connections(self):
        """Initialize Web3 connections for all supported chains"""
        for chain_id, endpoint in self.endpoints.items():
            try:
                self.web3_instances[chain_id] = Web3(Web3.HTTPProvider(endpoint.rpc_url))
                logger.info(f"Initialized Web3 connection for chain {chain_id}")
            except Exception as e:
                logger.error(f"Failed to initialize Web3 for chain {chain_id}: {e}")
    
    def get_endpoint(self, chain_id: int) -> Optional[LayerZeroEndpoint]:
        """Get LayerZero endpoint for a specific chain"""
        return self.endpoints.get(chain_id)
    
    def get_web3(self, chain_id: int) -> Optional[Web3]:
        """Get Web3 instance for a specific chain"""
        return self.web3_instances.get(chain_id)
    
    async def send_message(
        self,
        source_chain: int,
        destination_chain: int,
        payload: bytes,
        recipient: str,
        gas_limit: int = 200000,
        sender_private_key: Optional[str] = None
    ) -> Optional[Dict]:
        """Send cross-chain message via LayerZero V2"""
        try:
            source_endpoint = self.get_endpoint(source_chain)
            dest_endpoint = self.get_endpoint(destination_chain)
            
            if not source_endpoint or not dest_endpoint:
                logger.error(f"Unsupported chain: {source_chain} -> {destination_chain}")
                return None
            
            web3 = self.get_web3(source_chain)
            if not web3:
                logger.error(f"No Web3 connection for chain {source_chain}")
                return None
            
            # Create message structure
            message = CrossChainMessage(
                id=f"lz_{source_chain}_{destination_chain}_{web3.eth.get_block_number()}",
                source_chain=source_chain,
                destination_chain=destination_chain,
                payload=payload,
                gas_limit=gas_limit,
                recipient=recipient,
                sender="",  # Will be set when transaction is sent
                nonce=web3.eth.get_transaction_count(recipient) if sender_private_key else 0
            )
            
            # Estimate gas and fees
            fee_estimate = await self.estimate_fees(
                source_chain, 
                destination_chain, 
                payload, 
                gas_limit
            )
            
            if not fee_estimate:
                logger.error("Failed to estimate LayerZero fees")
                return None
            
            logger.info(f"Sending LayerZero message: {message.id}")
            logger.info(f"Estimated fee: {fee_estimate}")
            
            # Return message info (actual transaction sending would require private key handling)
            return {
                "message_id": message.id,
                "source_chain": source_chain,
                "destination_chain": destination_chain,
                "estimated_fee": fee_estimate,
                "status": "prepared",
                "payload_size": len(payload)
            }
            
        except Exception as e:
            logger.error(f"Error sending LayerZero message: {e}")
            return None
    
    async def estimate_fees(
        self,
        source_chain: int,
        destination_chain: int,
        payload: bytes,
        gas_limit: int
    ) -> Optional[Dict]:
        """Estimate LayerZero messaging fees"""
        try:
            source_endpoint = self.get_endpoint(source_chain)
            dest_endpoint = self.get_endpoint(destination_chain)
            
            if not source_endpoint or not dest_endpoint:
                return None
            
            # Mock fee estimation (in production, this would call LayerZero contracts)
            base_fee = 0.001  # ETH
            payload_fee = len(payload) * 0.00001  # Per byte
            gas_fee = gas_limit * 0.000000020  # 20 gwei
            
            total_fee = base_fee + payload_fee + gas_fee
            
            return {
                "native_fee": str(total_fee),
                "lz_token_fee": "0",
                "base_fee": str(base_fee),
                "payload_fee": str(payload_fee),
                "gas_fee": str(gas_fee)
            }
            
        except Exception as e:
            logger.error(f"Error estimating LayerZero fees: {e}")
            return None
    
    async def verify_message(self, message_id: str, source_chain: int) -> Optional[Dict]:
        """Verify message authenticity and status"""
        try:
            web3 = self.get_web3(source_chain)
            if not web3:
                return None
            
            # Mock verification (in production, this would check LayerZero contracts)
            # This would involve checking the message hash on-chain
            verification_result = {
                "message_id": message_id,
                "verified": True,
                "block_number": web3.eth.get_block_number(),
                "timestamp": web3.eth.get_block('latest')['timestamp'],
                "status": "verified"
            }
            
            logger.info(f"Message verification result: {verification_result}")
            return verification_result
            
        except Exception as e:
            logger.error(f"Error verifying LayerZero message: {e}")
            return None
    
    async def get_message_status(self, message_id: str, source_chain: int) -> Optional[Dict]:
        """Get status of a cross-chain message"""
        try:
            # Mock status check (in production, this would query LayerZero infrastructure)
            status_info = {
                "message_id": message_id,
                "status": "delivered",
                "source_chain": source_chain,
                "confirmations": 12,
                "delivery_time": "2024-01-02T10:30:00Z"
            }
            
            return status_info
            
        except Exception as e:
            logger.error(f"Error getting message status: {e}")
            return None
    
    def is_chain_supported(self, chain_id: int) -> bool:
        """Check if a chain is supported by LayerZero"""
        return chain_id in self.endpoints
    
    def get_supported_chains(self) -> List[int]:
        """Get list of supported chain IDs"""
        return list(self.endpoints.keys())


# Global instance
layerzero_service = LayerZeroService()