"""
Web3 service for blockchain interactions
"""
from web3 import Web3
from typing import Dict, Optional, List
import json
from decimal import Decimal

from src.config.settings import settings


class Web3Service:
    def __init__(self):
        self.rpcs = {
            1: settings.ethereum_rpc,      # Ethereum
            137: settings.polygon_rpc,     # Polygon
            42161: settings.arbitrum_rpc,  # Arbitrum
            10: settings.optimism_rpc,     # Optimism
            56: settings.bsc_rpc,          # BSC
            8453: "https://mainnet.base.org",  # Base
        }
        self.web3_instances = {}
        self._init_web3_instances()
    
    def _init_web3_instances(self):
        """Initialize Web3 instances for each chain"""
        for chain_id, rpc_url in self.rpcs.items():
            try:
                w3 = Web3(Web3.HTTPProvider(rpc_url))
                if w3.is_connected():
                    self.web3_instances[chain_id] = w3
                    print(f"Connected to chain {chain_id}")
                else:
                    print(f"Failed to connect to chain {chain_id}")
            except Exception as e:
                print(f"Error connecting to chain {chain_id}: {e}")
    
    def get_web3(self, chain_id: int) -> Optional[Web3]:
        """Get Web3 instance for specific chain"""
        return self.web3_instances.get(chain_id)
    
    async def get_native_balance(self, address: str, chain_id: int) -> Decimal:
        """Get native token balance (ETH, MATIC, etc.)"""
        w3 = self.get_web3(chain_id)
        if not w3:
            raise ValueError(f"Chain {chain_id} not supported")
        
        try:
            balance_wei = w3.eth.get_balance(address)
            balance_eth = w3.from_wei(balance_wei, 'ether')
            return Decimal(str(balance_eth))
        except Exception as e:
            print(f"Error getting native balance: {e}")
            return Decimal('0')
    
    async def get_token_balance(self, address: str, token_address: str, chain_id: int) -> Decimal:
        """Get ERC20 token balance"""
        w3 = self.get_web3(chain_id)
        if not w3:
            raise ValueError(f"Chain {chain_id} not supported")
        
        # ERC20 ABI for balanceOf function
        erc20_abi = [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "decimals",
                "outputs": [{"name": "", "type": "uint8"}],
                "type": "function"
            }
        ]
        
        try:
            contract = w3.eth.contract(
                address=w3.to_checksum_address(token_address),
                abi=erc20_abi
            )
            
            balance = contract.functions.balanceOf(address).call()
            decimals = contract.functions.decimals().call()
            
            # Convert to human readable format
            balance_decimal = Decimal(balance) / Decimal(10 ** decimals)
            return balance_decimal
            
        except Exception as e:
            print(f"Error getting token balance: {e}")
            return Decimal('0')
    
    async def get_transaction_receipt(self, tx_hash: str, chain_id: int) -> Optional[Dict]:
        """Get transaction receipt"""
        w3 = self.get_web3(chain_id)
        if not w3:
            return None
        
        try:
            receipt = w3.eth.get_transaction_receipt(tx_hash)
            return dict(receipt)
        except Exception as e:
            print(f"Error getting transaction receipt: {e}")
            return None
    
    async def estimate_gas_price(self, chain_id: int) -> Optional[int]:
        """Estimate current gas price"""
        w3 = self.get_web3(chain_id)
        if not w3:
            return None
        
        try:
            gas_price = w3.eth.gas_price
            return gas_price
        except Exception as e:
            print(f"Error estimating gas price: {e}")
            return None


# Global instance
web3_service = Web3Service()