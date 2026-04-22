"""
DEX Trade Executor
Executes actual trades on DEXs (Uniswap, etc.) on testnets
"""
from web3 import Web3
from eth_account import Account
import logging
from typing import Dict, Optional
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class DEXExecutor:
    """Executes trades on decentralized exchanges"""
    
    # Testnet configurations
    NETWORKS = {
        'sepolia': {
            'rpc': 'https://ethereum-sepolia-rpc.publicnode.com',  # More reliable RPC
            'chain_id': 11155111,
            'uniswap_router': '0xC532a74256D3Db42D0Bf7a0400fEFDbad7694008',  # Uniswap V2 Router on Sepolia
            'weth': '0x7b79995e5f793A07Bc00c21412e50Ecae098E7f9',
            'usdc': '0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238'
        }
    }
    
    # Uniswap V2 Router ABI (simplified)
    ROUTER_ABI = json.loads('''[
        {
            "inputs": [
                {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
                {"internalType": "address[]", "name": "path", "type": "address[]"},
                {"internalType": "address", "name": "to", "type": "address"},
                {"internalType": "uint256", "name": "deadline", "type": "uint256"}
            ],
            "name": "swapExactETHForTokens",
            "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
            "stateMutability": "payable",
            "type": "function"
        },
        {
            "inputs": [
                {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
                {"internalType": "address[]", "name": "path", "type": "address[]"},
                {"internalType": "address", "name": "to", "type": "address"},
                {"internalType": "uint256", "name": "deadline", "type": "uint256"}
            ],
            "name": "swapExactTokensForETH",
            "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "inputs": [
                {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                {"internalType": "address[]", "name": "path", "type": "address[]"}
            ],
            "name": "getAmountsOut",
            "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
            "stateMutability": "view",
            "type": "function"
        }
    ]''')
    
    # ERC20 ABI (simplified)
    ERC20_ABI = json.loads('''[
        {
            "constant": true,
            "inputs": [{"name": "_owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "type": "function"
        },
        {
            "constant": false,
            "inputs": [
                {"name": "_spender", "type": "address"},
                {"name": "_value", "type": "uint256"}
            ],
            "name": "approve",
            "outputs": [{"name": "", "type": "bool"}],
            "type": "function"
        },
        {
            "constant": true,
            "inputs": [
                {"name": "_owner", "type": "address"},
                {"name": "_spender", "type": "address"}
            ],
            "name": "allowance",
            "outputs": [{"name": "", "type": "uint256"}],
            "type": "function"
        }
    ]''')
    
    def __init__(self, network: str = 'sepolia'):
        """Initialize DEX executor for a specific network"""
        self.network = network
        self.config = self.NETWORKS.get(network)
        
        if not self.config:
            raise ValueError(f"Unsupported network: {network}")
        
        # Create HTTPProvider with increased timeout
        from web3.providers import HTTPProvider
        from web3.middleware import geth_poa_middleware
        
        provider = HTTPProvider(
            self.config['rpc'],
            request_kwargs={'timeout': 30}  # 30 second timeout
        )
        
        self.w3 = Web3(provider)
        
        # Add POA middleware for testnets
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        
        self.router = self.w3.eth.contract(
            address=self.config['uniswap_router'],
            abi=self.ROUTER_ABI
        )
        
        # Import trade history service for recording trades
        self.trade_history_service = None
        try:
            from src.services.trade_history_service import trade_history_service
            self.trade_history_service = trade_history_service
        except ImportError:
            logger.warning("TradeHistoryService not available")
    
    async def execute_swap(self, account: Account, token_in: str, token_out: str, 
                          amount_in: float, slippage: float = 0.5, trade_type: str = "manual") -> Dict:
        """
        Execute a token swap
        
        Args:
            account: Account to trade with
            token_in: Input token symbol ('ETH', 'USDC', etc.)
            token_out: Output token symbol
            amount_in: Amount to swap
            slippage: Slippage tolerance (default 0.5%)
            trade_type: Type of trade ("manual" or "ai_executed")
            
        Returns:
            Dict with transaction details
        """
        trade_id = None
        try:
            # Get token addresses
            token_in_addr = self._get_token_address(token_in)
            token_out_addr = self._get_token_address(token_out)
            
            # Check balance
            if token_in == 'ETH':
                balance = self.w3.eth.get_balance(account.address)
                balance_readable = self.w3.from_wei(balance, 'ether')
            else:
                token_contract = self.w3.eth.contract(address=token_in_addr, abi=self.ERC20_ABI)
                balance = token_contract.functions.balanceOf(account.address).call()
                balance_readable = self.w3.from_wei(balance, 'ether')
            
            logger.info(f"Balance of {token_in}: {balance_readable}")
            
            if balance_readable < amount_in:
                return {
                    'success': False,
                    'error': f'Insufficient balance. Required: {amount_in}, Available: {balance_readable}'
                }
            
            # Convert amount to wei
            amount_in_wei = self.w3.to_wei(amount_in, 'ether')
            
            # Get expected output amount
            path = [token_in_addr, token_out_addr]
            amounts_out = self.router.functions.getAmountsOut(amount_in_wei, path).call()
            amount_out_min = int(amounts_out[1] * (1 - slippage / 100))
            amount_out_expected = float(self.w3.from_wei(amounts_out[1], 'ether'))
            
            # Build transaction
            deadline = self.w3.eth.get_block('latest')['timestamp'] + 300  # 5 minutes
            
            if token_in == 'ETH':
                # Swap ETH for tokens
                tx = self.router.functions.swapExactETHForTokens(
                    amount_out_min,
                    path,
                    account.address,
                    deadline
                ).build_transaction({
                    'from': account.address,
                    'value': amount_in_wei,
                    'gas': 250000,
                    'gasPrice': self.w3.eth.gas_price,
                    'nonce': self.w3.eth.get_transaction_count(account.address),
                    'chainId': self.config['chain_id']
                })
            else:
                # Approve token spending first
                token_contract = self.w3.eth.contract(address=token_in_addr, abi=self.ERC20_ABI)
                allowance = token_contract.functions.allowance(
                    account.address, 
                    self.config['uniswap_router']
                ).call()
                
                if allowance < amount_in_wei:
                    # Need to approve
                    approve_tx = token_contract.functions.approve(
                        self.config['uniswap_router'],
                        amount_in_wei
                    ).build_transaction({
                        'from': account.address,
                        'gas': 100000,
                        'gasPrice': self.w3.eth.gas_price,
                        'nonce': self.w3.eth.get_transaction_count(account.address),
                        'chainId': self.config['chain_id']
                    })
                    
                    # Sign and send approval
                    signed_approve = account.sign_transaction(approve_tx)
                    approve_hash = self.w3.eth.send_raw_transaction(signed_approve.rawTransaction)
                    logger.info(f"Approval tx sent: {approve_hash.hex()}")
                    
                    # Wait for approval
                    self.w3.eth.wait_for_transaction_receipt(approve_hash)
                
                # Swap tokens for ETH
                tx = self.router.functions.swapExactTokensForETH(
                    amount_in_wei,
                    amount_out_min,
                    path,
                    account.address,
                    deadline
                ).build_transaction({
                    'from': account.address,
                    'gas': 250000,
                    'gasPrice': self.w3.eth.gas_price,
                    'nonce': self.w3.eth.get_transaction_count(account.address),
                    'chainId': self.config['chain_id']
                })
            
            # Sign transaction
            signed_tx = account.sign_transaction(tx)
            
            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_hash_hex = tx_hash.hex()
            logger.info(f"Swap tx sent: {tx_hash_hex}")
            
            # Record trade as pending
            if self.trade_history_service:
                try:
                    from decimal import Decimal
                    trade_id = await self.trade_history_service.record_trade(
                        wallet_address=account.address,
                        tx_hash=tx_hash_hex,
                        from_token=token_in_addr,
                        to_token=token_out_addr,
                        from_token_symbol=token_in,
                        to_token_symbol=token_out,
                        from_amount=Decimal(str(amount_in)),
                        to_amount=Decimal(str(amount_out_expected)),
                        gas_fee=Decimal('0'),  # Will update after confirmation
                        slippage=Decimal(str(slippage)),
                        trade_type=trade_type
                    )
                except Exception as e:
                    logger.error(f"Failed to record trade: {e}")
            
            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            # Calculate gas fee
            from decimal import Decimal
            gas_fee = float(self.w3.from_wei(receipt['gasUsed'] * tx['gasPrice'], 'ether'))
            
            # Update trade status
            status = 'confirmed' if receipt['status'] == 1 else 'failed'
            if self.trade_history_service and trade_id:
                try:
                    await self.trade_history_service.update_trade_status(tx_hash_hex, status)
                    # Update gas fee
                    await self.trade_history_service.update_trade_gas_fee(tx_hash_hex, Decimal(str(gas_fee)))
                except Exception as e:
                    logger.error(f"Failed to update trade status: {e}")
            
            return {
                'success': True,
                'tx_hash': tx_hash_hex,
                'status': status,
                'gas_used': receipt['gasUsed'],
                'gas_fee': gas_fee,
                'block_number': receipt['blockNumber'],
                'trade_id': trade_id
            }
            
        except Exception as e:
            logger.error(f"Swap failed: {e}")
            
            # Update trade as failed if we recorded it
            if self.trade_history_service and trade_id:
                try:
                    await self.trade_history_service.update_trade_status(trade_id, 'failed')
                except Exception as update_error:
                    logger.error(f"Failed to update trade status: {update_error}")
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_token_address(self, symbol: str) -> str:
        """Get token contract address by symbol"""
        symbol_upper = symbol.upper()
        
        if symbol_upper == 'ETH' or symbol_upper == 'WETH':
            return self.config['weth']
        elif symbol_upper == 'USDC':
            return self.config['usdc']
        else:
            raise ValueError(f"Unsupported token: {symbol}")
    
    def get_balance(self, address: str, token: str = 'ETH') -> float:
        """Get token balance for an address"""
        try:
            if token == 'ETH':
                balance = self.w3.eth.get_balance(address)
                return float(self.w3.from_wei(balance, 'ether'))
            else:
                token_addr = self._get_token_address(token)
                token_contract = self.w3.eth.contract(address=token_addr, abi=self.ERC20_ABI)
                balance = token_contract.functions.balanceOf(address).call()
                return float(self.w3.from_wei(balance, 'ether'))
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            return 0.0


# Global instance
dex_executor = DEXExecutor()
