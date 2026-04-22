"""
Autonomous Trading Service
Handles automated trading based on AI signals using private keys or seed phrases
WARNING: Only use with testnet accounts!
"""
import asyncio
from typing import Optional, Dict, List
from web3 import Web3
from eth_account import Account
from mnemonic import Mnemonic
import logging
from datetime import datetime

from .dex_executor import DEXExecutor

logger = logging.getLogger(__name__)


class AutonomousTrader:
    """Manages autonomous trading operations"""
    
    def __init__(self):
        self.active_traders: Dict[str, dict] = {}
        self.is_running = False
        self.dex_executor = DEXExecutor(network='sepolia')  # Use Sepolia testnet
        
    def add_wallet(self, wallet_id: str, private_key: str = None, seed_phrase: str = None, 
                   account_index: int = 0, config: dict = None):
        """
        Add a wallet for autonomous trading
        
        Args:
            wallet_id: Unique identifier for this wallet
            private_key: Private key (TESTNET ONLY!) - optional if seed_phrase provided
            seed_phrase: 12 or 24 word seed phrase (TESTNET ONLY!) - optional if private_key provided
            account_index: Account index to derive from seed phrase (default: 0)
            config: Trading configuration
                - max_trade_amount: Maximum amount per trade
                - risk_level: low/medium/high
                - allowed_tokens: List of token symbols
                - stop_loss_percent: Stop loss percentage
                - take_profit_percent: Take profit percentage
        """
        try:
            # Validate that either private_key or seed_phrase is provided
            if not private_key and not seed_phrase:
                raise ValueError("Either private_key or seed_phrase must be provided")
            
            if private_key and seed_phrase:
                raise ValueError("Provide either private_key or seed_phrase, not both")
            
            # Create account from private key or seed phrase
            if private_key:
                account = Account.from_key(private_key)
                derivation_info = None
            else:
                # Derive account from seed phrase
                account, derivation_path = self._derive_account_from_seed(seed_phrase, account_index)
                derivation_info = {
                    'account_index': account_index,
                    'derivation_path': derivation_path
                }
            
            self.active_traders[wallet_id] = {
                'account': account,
                'address': account.address,
                'config': config or {},
                'active': False,
                'trades': [],
                'balance': 0,
                'derivation_info': derivation_info,
                'created_at': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Added wallet {wallet_id} with address {account.address}")
            return {
                'success': True,
                'wallet_id': wallet_id,
                'address': account.address,
                'derivation_info': derivation_info
            }
            
        except Exception as e:
            logger.error(f"Failed to add wallet: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _derive_account_from_seed(self, seed_phrase: str, account_index: int = 0):
        """
        Derive an Ethereum account from a seed phrase
        
        Args:
            seed_phrase: 12 or 24 word mnemonic phrase
            account_index: Account index to derive (default: 0)
            
        Returns:
            tuple: (Account object, derivation_path)
        """
        # Validate seed phrase
        mnemo = Mnemonic("english")
        if not mnemo.check(seed_phrase):
            raise ValueError("Invalid seed phrase")
        
        # Generate seed from mnemonic
        seed = mnemo.to_seed(seed_phrase)
        
        # Standard Ethereum derivation path: m/44'/60'/0'/0/{account_index}
        derivation_path = f"m/44'/60'/0'/0/{account_index}"
        
        # Derive private key from seed
        # Note: For production, use a proper BIP32/BIP44 library
        # This is a simplified version
        Account.enable_unaudited_hdwallet_features()
        account = Account.from_mnemonic(seed_phrase, account_path=derivation_path)
        
        return account, derivation_path
    
    def remove_wallet(self, wallet_id: str):
        """Remove a wallet from autonomous trading"""
        if wallet_id in self.active_traders:
            del self.active_traders[wallet_id]
            logger.info(f"Removed wallet {wallet_id}")
            return {'success': True}
        return {'success': False, 'error': 'Wallet not found'}
    
    async def start_trading(self, wallet_id: str):
        """Start autonomous trading for a wallet"""
        if wallet_id not in self.active_traders:
            return {'success': False, 'error': 'Wallet not found'}
        
        self.active_traders[wallet_id]['active'] = True
        logger.info(f"Started autonomous trading for {wallet_id}")
        
        # Start trading loop in background
        asyncio.create_task(self._trading_loop(wallet_id))
        
        return {'success': True, 'message': 'Autonomous trading started'}
    
    async def stop_trading(self, wallet_id: str):
        """Stop autonomous trading for a wallet"""
        if wallet_id not in self.active_traders:
            return {'success': False, 'error': 'Wallet not found'}
        
        self.active_traders[wallet_id]['active'] = False
        logger.info(f"Stopped autonomous trading for {wallet_id}")
        
        return {'success': True, 'message': 'Autonomous trading stopped'}
    
    async def _trading_loop(self, wallet_id: str):
        """Main trading loop for a wallet"""
        trader = self.active_traders[wallet_id]
        
        while trader['active']:
            try:
                # 1. Get AI signals
                signals = await self._get_ai_signals(trader['config']['allowed_tokens'])
                
                # 2. Analyze signals and decide on trades
                trade_decisions = await self._analyze_signals(signals, trader['config'])
                
                # 3. Execute trades
                for decision in trade_decisions:
                    await self._execute_trade(wallet_id, decision)
                
                # 4. Monitor existing positions
                await self._monitor_positions(wallet_id)
                
                # Wait before next iteration (e.g., 30 seconds)
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Error in trading loop for {wallet_id}: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _get_ai_signals(self, allowed_tokens: List[str]) -> List[dict]:
        """Get AI trading signals for allowed tokens"""
        # This would integrate with your AI signal generator
        # For now, return mock signals
        return []
    
    async def _analyze_signals(self, signals: List[dict], config: dict) -> List[dict]:
        """Analyze signals and create trade decisions"""
        decisions = []
        
        for signal in signals:
            # Check if signal meets criteria
            if signal['confidence'] >= 70:  # Minimum confidence
                decisions.append({
                    'action': 'buy' if signal['direction'] == 'bullish' else 'sell',
                    'token': signal['pair'].split('/')[0],
                    'amount': config['max_trade_amount'],
                    'stop_loss': signal['stop'],
                    'take_profit': signal['target']
                })
        
        return decisions
    
    async def _execute_trade(self, wallet_id: str, decision: dict):
        """Execute a trade decision using real DEX"""
        trader = self.active_traders[wallet_id]
        
        try:
            logger.info(f"Executing trade for {wallet_id}: {decision}")
            
            account = trader['account']
            
            # Get current balance
            balance = self.dex_executor.get_balance(account.address, 'ETH')
            logger.info(f"Wallet {account.address} balance: {balance} ETH")
            
            if balance < decision['amount']:
                logger.warning(f"Insufficient balance for trade. Required: {decision['amount']}, Available: {balance}")
                trade_record = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'action': decision['action'],
                    'token': decision['token'],
                    'amount': decision['amount'],
                    'status': 'failed',
                    'error': 'Insufficient balance'
                }
                trader['trades'].append(trade_record)
                return
            
            # Execute the swap
            if decision['action'] == 'buy':
                # Buy token with ETH
                result = await self.dex_executor.execute_swap(
                    account=account,
                    token_in='ETH',
                    token_out=decision['token'],
                    amount_in=decision['amount'],
                    slippage=1.0  # 1% slippage tolerance
                )
            else:
                # Sell token for ETH
                result = await self.dex_executor.execute_swap(
                    account=account,
                    token_in=decision['token'],
                    token_out='ETH',
                    amount_in=decision['amount'],
                    slippage=1.0
                )
            
            if result['success']:
                trade_record = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'action': decision['action'],
                    'token': decision['token'],
                    'amount': decision['amount'],
                    'status': result['status'],
                    'tx_hash': result['tx_hash'],
                    'gas_used': result.get('gas_used'),
                    'block_number': result.get('block_number'),
                    'stop_loss': decision.get('stop_loss'),
                    'take_profit': decision.get('take_profit')
                }
                logger.info(f"Trade executed successfully: {trade_record}")
            else:
                trade_record = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'action': decision['action'],
                    'token': decision['token'],
                    'amount': decision['amount'],
                    'status': 'failed',
                    'error': result.get('error', 'Unknown error')
                }
                logger.error(f"Trade failed: {trade_record}")
            
            trader['trades'].append(trade_record)
            
        except Exception as e:
            logger.error(f"Failed to execute trade: {e}")
            trade_record = {
                'timestamp': datetime.utcnow().isoformat(),
                'action': decision['action'],
                'token': decision['token'],
                'amount': decision['amount'],
                'status': 'failed',
                'error': str(e)
            }
            trader['trades'].append(trade_record)
    
    async def _monitor_positions(self, wallet_id: str):
        """Monitor open positions for stop loss / take profit"""
        trader = self.active_traders[wallet_id]
        
        # Check each open position
        for trade in trader['trades']:
            if trade['status'] == 'open':
                # Check current price vs stop loss / take profit
                # Execute close if needed
                pass
    
    def get_wallet_status(self, wallet_id: str) -> Optional[dict]:
        """Get status of a wallet"""
        if wallet_id not in self.active_traders:
            return None
        
        trader = self.active_traders[wallet_id]
        return {
            'wallet_id': wallet_id,
            'address': trader['address'],
            'active': trader['active'],
            'total_trades': len(trader['trades']),
            'config': trader['config'],
            'created_at': trader['created_at']
        }
    
    def get_all_wallets(self) -> List[dict]:
        """Get status of all wallets"""
        return [
            self.get_wallet_status(wallet_id)
            for wallet_id in self.active_traders.keys()
        ]


# Global instance
autonomous_trader = AutonomousTrader()
