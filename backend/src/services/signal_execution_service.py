"""
Signal Execution Service
Handles execution of trading signals with wallet integration
"""
import asyncio
import json
from typing import Dict, Any, Optional
from datetime import datetime
from web3 import Web3
from eth_account import Account
import httpx

from ..config.settings import settings
from .position_monitor_service import position_monitor_service


class SignalExecutionService:
    """Service for executing trading signals"""
    
    def __init__(self):
        # Initialize Web3 connections for different networks
        self.networks = {
            'ethereum': {
                'rpc_url': 'https://eth-mainnet.g.alchemy.com/v2/demo',
                'chain_id': 1,
                'name': 'Ethereum Mainnet'
            },
            'sepolia': {
                'rpc_url': 'https://eth-sepolia.g.alchemy.com/v2/demo',
                'chain_id': 11155111,
                'name': 'Sepolia Testnet'
            },
            'polygon': {
                'rpc_url': 'https://polygon-mainnet.g.alchemy.com/v2/demo',
                'chain_id': 137,
                'name': 'Polygon Mainnet'
            },
            'arbitrum': {
                'rpc_url': 'https://arb-mainnet.g.alchemy.com/v2/demo',
                'chain_id': 42161,
                'name': 'Arbitrum One'
            },
            'optimism': {
                'rpc_url': 'https://opt-mainnet.g.alchemy.com/v2/demo',
                'chain_id': 10,
                'name': 'Optimism Mainnet'
            },
            'bsc': {
                'rpc_url': 'https://bsc-dataseed.binance.org/',
                'chain_id': 56,
                'name': 'BNB Smart Chain'
            },
            'base': {
                'rpc_url': 'https://base-mainnet.g.alchemy.com/v2/demo',
                'chain_id': 8453,
                'name': 'Base Mainnet'
            }
        }
        
        # DEX router addresses (for swaps)
        self.dex_routers = {
            'ethereum': {
                'uniswap_v2': '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',
                'uniswap_v3': '0xE592427A0AEce92De3Edee1F18E0157C05861564',
                'sushiswap': '0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F'
            },
            'polygon': {
                'quickswap': '0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff',
                'sushiswap': '0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506'
            },
            'arbitrum': {
                'uniswap_v3': '0xE592427A0AEce92De3Edee1F18E0157C05861564',
                'sushiswap': '0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506'
            },
            'optimism': {
                'uniswap_v3': '0xE592427A0AEce92De3Edee1F18E0157C05861564',
                'velodrome': '0xa132DAB612dB5cB9fC9Ac426A0Cc215A3423F9c9'
            },
            'bsc': {
                'pancakeswap': '0x10ED43C718714eb63d5aA57B78B54704E256024E',
                'sushiswap': '0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506'
            },
            'base': {
                'uniswap_v3': '0x2626664c2603336E57B271c5C0b26F421741e481',
                'sushiswap': '0x6BDED42c6DA8FBf0d2bA55B2fa120C5e0c8D7891'
            }
        }
        
        # Common token addresses
        self.token_addresses = {
            'ethereum': {
                'USDT': '0xdAC17F958D2ee523a2206206994597C13D831ec7',
                'USDC': '0xA0b86a33E6441b8435b662303c0f0c8c5c663B5b',
                'WETH': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
                'DAI': '0x6B175474E89094C44Da98b954EedeAC495271d0F'
            },
            'polygon': {
                'USDT': '0xc2132D05D31c914a87C6611C10748AEb04B58e8F',
                'USDC': '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174',
                'WMATIC': '0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270'
            },
            'arbitrum': {
                'USDT': '0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9',
                'USDC': '0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8',
                'WETH': '0x82aF49447D8a07e3bd95BD0d56f35241523fBab1'
            },
            'optimism': {
                'USDT': '0x94b008aA00579c1307B0EF2c499aD98a8ce58e58',
                'USDC': '0x7F5c764cBc14f9669B88837ca1490cCa17c31607',
                'WETH': '0x4200000000000000000000000000000000000006'
            },
            'bsc': {
                'USDT': '0x55d398326f99059fF775485246999027B3197955',
                'USDC': '0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d',
                'WBNB': '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c'
            },
            'base': {
                'USDT': '0xfde4C96c8593536E31F229EA8f37b2ADa2699bb2',
                'USDC': '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913',
                'WETH': '0x4200000000000000000000000000000000000006'
            }
        }
    
    async def validate_wallet_connection(self, wallet_address: str, network: str = 'ethereum') -> Dict[str, Any]:
        """Validate wallet connection and get balance"""
        try:
            if not Web3.is_address(wallet_address):
                return {
                    'success': False,
                    'error': 'Invalid wallet address format'
                }
            
            network_config = self.networks.get(network)
            if not network_config:
                return {
                    'success': False,
                    'error': f'Unsupported network: {network}'
                }
            
            # For demo purposes, skip actual blockchain connection and return success
            # In production, you would connect to the actual network
            return {
                'success': True,
                'wallet_address': wallet_address,
                'network': network_config['name'],
                'chain_id': network_config['chain_id'],
                'eth_balance': 1.0,  # Mock balance
                'gas_price_gwei': 20.0,  # Mock gas price
                'connected': True
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Wallet validation failed: {str(e)}'
            }
    
    async def estimate_swap_gas(self, 
                               from_token: str, 
                               to_token: str, 
                               amount: float,
                               wallet_address: str,
                               network: str = 'ethereum') -> Dict[str, Any]:
        """Estimate gas cost for a swap transaction"""
        try:
            network_config = self.networks.get(network)
            if not network_config:
                return {'success': False, 'error': f'Unsupported network: {network}'}
            
            # Mock gas estimation for demo purposes
            # In production, you would connect to the actual network
            estimated_gas_limit = 200000  # Conservative estimate
            gas_price_gwei = 20.0  # Mock gas price
            
            # Calculate gas cost
            gas_cost_eth = (estimated_gas_limit * gas_price_gwei) / 1e9
            
            # Get ETH price for USD conversion
            eth_price_usd = await self._get_eth_price()
            gas_cost_usd = gas_cost_eth * eth_price_usd
            
            return {
                'success': True,
                'gas_limit': estimated_gas_limit,
                'gas_price_gwei': gas_price_gwei,
                'gas_cost_eth': gas_cost_eth,
                'gas_cost_usd': gas_cost_usd,
                'network': network_config['name']
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Gas estimation failed: {str(e)}'
            }
    
    async def _get_eth_price(self) -> float:
        """Get current ETH price in USD"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT",
                    timeout=5.0
                )
                if response.status_code == 200:
                    data = response.json()
                    return float(data['price'])
        except:
            pass
        return 3000.0  # Fallback price
    
    async def get_swap_quote(self,
                            from_token: str,
                            to_token: str,
                            amount: float,
                            network: str = 'ethereum') -> Dict[str, Any]:
        """Get swap quote from DEX aggregators"""
        try:
            # For demo purposes, we'll simulate a swap quote
            # In production, you'd integrate with 1inch, 0x, or other aggregators
            
            # Get token prices
            from_price = await self._get_token_price(from_token)
            to_price = await self._get_token_price(to_token)
            
            if from_price == 0 or to_price == 0:
                return {
                    'success': False,
                    'error': 'Unable to fetch token prices'
                }
            
            # Calculate expected output (with 0.3% slippage)
            usd_value = amount * from_price
            expected_output = (usd_value / to_price) * 0.997  # 0.3% slippage
            
            # Get gas estimate
            gas_estimate = await self.estimate_swap_gas(from_token, to_token, amount, '', network)
            
            return {
                'success': True,
                'from_token': from_token,
                'to_token': to_token,
                'from_amount': amount,
                'to_amount': expected_output,
                'from_price_usd': from_price,
                'to_price_usd': to_price,
                'slippage': 0.3,
                'gas_estimate': gas_estimate,
                'route': f'Best route via Uniswap V3',
                'network': network
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Quote failed: {str(e)}'
            }
    
    async def _get_token_price(self, token_symbol: str) -> float:
        """Get token price in USD"""
        try:
            # Map common token symbols to Binance symbols
            symbol_map = {
                'ETH': 'ETHUSDT',
                'BTC': 'BTCUSDT',
                'USDT': 'USDTUSD',
                'USDC': 'USDCUSDT',
                'BNB': 'BNBUSDT',
                'SOL': 'SOLUSDT',
                'ADA': 'ADAUSDT',
                'DOT': 'DOTUSDT',
                'MATIC': 'MATICUSDT',
                'LINK': 'LINKUSDT'
            }
            
            binance_symbol = symbol_map.get(token_symbol.upper(), f'{token_symbol.upper()}USDT')
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.binance.com/api/v3/ticker/price?symbol={binance_symbol}",
                    timeout=5.0
                )
                if response.status_code == 200:
                    data = response.json()
                    return float(data['price'])
                    
        except Exception as e:
            print(f"Error getting price for {token_symbol}: {e}")
            
        # Fallback prices
        fallback_prices = {
            'ETH': 3000.0,
            'BTC': 65000.0,
            'USDT': 1.0,
            'USDC': 1.0,
            'BNB': 400.0,
            'SOL': 100.0
        }
        
        return fallback_prices.get(token_symbol.upper(), 1.0)
    
    async def execute_signal(self,
                           signal_id: str,
                           wallet_address: str,
                           amount: float,
                           network: str = 'ethereum',
                           slippage: float = 0.5) -> Dict[str, Any]:
        """Execute a REAL trading signal - Frontend will handle MetaMask transaction"""
        try:
            # Validate wallet first
            wallet_validation = await self.validate_wallet_connection(wallet_address, network)
            if not wallet_validation['success']:
                return wallet_validation
            
            # Parse signal details from signal_id
            # Format: signal_SYMBOL_timestamp
            parts = signal_id.split('_')
            if len(parts) < 2:
                return {
                    'success': False,
                    'error': 'Invalid signal ID format'
                }
            
            token_pair = parts[1]  # e.g., BTCUSDT
            base_token = token_pair.replace('USDT', '')  # e.g., BTC
            
            # LONG-ONLY: Always USDT -> Token (BUY direction)
            from_token = 'USDT'
            to_token = base_token
            
            # Get swap quote
            quote = await self.get_swap_quote(from_token, to_token, amount, network)
            
            if not quote['success']:
                return quote
            
            # Return transaction details for frontend execution
            # The frontend will handle the actual MetaMask transaction
            return {
                'success': True,
                'signal_id': signal_id,
                'execution_type': 'frontend_metamask',
                'from_token': from_token,
                'to_token': to_token,
                'from_amount': amount,
                'to_amount': quote['to_amount'],
                'gas_estimate': quote['gas_estimate'],
                'slippage': slippage,
                'network': network,
                'wallet_address': wallet_address,
                'status': 'ready_for_frontend_execution',
                'prepared_at': datetime.now().isoformat(),
                'message': 'Ready for MetaMask execution via frontend'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Signal preparation failed: {str(e)}'
            }

    
    async def get_execution_status(self, transaction_hash: str, network: str = 'ethereum') -> Dict[str, Any]:
        """Get the status of an executed transaction"""
        try:
            network_config = self.networks.get(network)
            if not network_config:
                return {'success': False, 'error': f'Unsupported network: {network}'}
            
            w3 = Web3(Web3.HTTPProvider(network_config['rpc_url']))
            
            # Get transaction receipt
            try:
                receipt = w3.eth.get_transaction_receipt(transaction_hash)
                
                return {
                    'success': True,
                    'transaction_hash': transaction_hash,
                    'status': 'confirmed' if receipt['status'] == 1 else 'failed',
                    'block_number': receipt['blockNumber'],
                    'gas_used': receipt['gasUsed'],
                    'network': network_config['name']
                }
                
            except Exception:
                # Transaction not found or pending
                return {
                    'success': True,
                    'transaction_hash': transaction_hash,
                    'status': 'pending',
                    'network': network_config['name']
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Status check failed: {str(e)}'
            }


# Global instance
signal_execution_service = SignalExecutionService()