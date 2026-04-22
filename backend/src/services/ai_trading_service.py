"""
AI Trading Service
Executes trades based on AI signals with risk management
"""
import asyncio
import logging
from typing import Dict, Optional
from decimal import Decimal
from datetime import datetime
from eth_account import Account

from src.services.risk_manager import risk_manager
from src.services.dex_executor import dex_executor
from src.services.wallet_service import wallet_service
from src.ai.signal_generator import signal_generator
from src.api.websocket.ws_manager import broadcast_ai_signal, broadcast_trade_executed

logger = logging.getLogger(__name__)


class AITradingService:
    """Service for executing AI-powered trades"""
    
    CONFIDENCE_THRESHOLD = 75  # Minimum confidence to execute
    SIGNAL_INTERVAL = 60  # Generate signals every 60 seconds
    
    def __init__(self):
        self.is_running = False
        self.demo_wallet_key = None
        self.demo_wallet_address = "0x6739659248061A54E0f4de8f2cd60278B69468b3"
        self._task: Optional[asyncio.Task] = None
    
    def set_demo_wallet(self, private_key: str):
        """Set the demo wallet private key"""
        self.demo_wallet_key = private_key
    
    async def execute_ai_trade(
        self,
        signal: Dict
    ) -> Dict:
        """
        Execute a trade based on AI signal
        
        Args:
            signal: AI signal with action, token, confidence, etc.
            
        Returns:
            Trade execution result
        """
        try:
            # Check confidence threshold
            confidence = signal.get('confidence', 0)
            if confidence < self.CONFIDENCE_THRESHOLD:
                logger.info(f"Signal confidence {confidence}% below threshold {self.CONFIDENCE_THRESHOLD}%")
                return {
                    'success': False,
                    'error': f'Confidence {confidence}% below threshold'
                }
            
            # Get wallet account
            if not self.demo_wallet_key:
                return {
                    'success': False,
                    'error': 'Demo wallet not configured'
                }
            
            account = Account.from_key(self.demo_wallet_key)
            
            # Get portfolio value and balances
            portfolio = await wallet_service.calculate_portfolio_value(self.demo_wallet_address)
            portfolio_value = Decimal(str(portfolio.get('total_value_usd', 0)))
            eth_balance = Decimal(str(portfolio.get('eth_balance', 0)))
            
            # Parse signal
            action = signal.get('action', '').lower()
            token = signal.get('token', '')
            amount_usd = Decimal(str(signal.get('amount_usd', 0)))
            
            # Validate with risk manager
            is_valid, error = risk_manager.validate_trade(
                wallet_address=self.demo_wallet_address,
                amount=amount_usd,
                portfolio_value=portfolio_value,
                eth_balance=eth_balance
            )
            
            if not is_valid:
                logger.warning(f"Trade validation failed: {error}")
                return {
                    'success': False,
                    'error': error
                }
            
            # Execute trade based on action
            if action == 'buy':
                # Buy token with ETH
                token_in = 'ETH'
                token_out = token
                # Calculate ETH amount from USD
                eth_price = portfolio.get('eth_price_usd', 2500)
                amount_in = float(amount_usd / Decimal(str(eth_price)))
            elif action == 'sell':
                # Sell token for ETH
                token_in = token
                token_out = 'ETH'
                # Get token balance
                token_balances = portfolio.get('token_balances', [])
                token_balance = next(
                    (t for t in token_balances if t['symbol'] == token),
                    None
                )
                if not token_balance:
                    return {
                        'success': False,
                        'error': f'No {token} balance'
                    }
                amount_in = float(token_balance['balance'])
            else:
                return {
                    'success': False,
                    'error': f'Unknown action: {action}'
                }
            
            # Execute swap
            result = await dex_executor.execute_swap(
                account=account,
                token_in=token_in,
                token_out=token_out,
                amount_in=amount_in,
                slippage=0.5,
                trade_type="ai_executed"
            )
            
            # Broadcast trade execution
            if result.get('success'):
                await broadcast_trade_executed({
                    'tx_hash': result.get('tx_hash'),
                    'action': action,
                    'token': token,
                    'amount': amount_in,
                    'status': result.get('status'),
                    'confidence': confidence
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to execute AI trade: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def generate_and_execute_signals(self):
        """Generate AI signals and execute trades"""
        try:
            # Get portfolio data
            portfolio = await wallet_service.calculate_portfolio_value(self.demo_wallet_address)
            
            # Generate signals
            signals = await signal_generator.generate_signals(
                wallet_address=self.demo_wallet_address,
                portfolio_data=portfolio
            )
            
            # Execute high-confidence signals
            for signal in signals:
                confidence = signal.get('confidence', 0)
                
                # Broadcast signal
                await broadcast_ai_signal(signal)
                
                # Execute if confidence is high enough
                if confidence >= self.CONFIDENCE_THRESHOLD:
                    logger.info(f"Executing AI trade: {signal}")
                    result = await self.execute_ai_trade(signal)
                    
                    if result.get('success'):
                        logger.info(f"AI trade executed successfully: {result.get('tx_hash')}")
                    else:
                        logger.warning(f"AI trade failed: {result.get('error')}")
                    
                    # Wait between trades
                    await asyncio.sleep(5)
                    
        except Exception as e:
            logger.error(f"Signal generation failed: {e}")
    
    async def start(self):
        """Start the AI trading service"""
        if self.is_running:
            logger.warning("AI trading service already running")
            return
        
        self.is_running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("AI trading service started")
    
    async def stop(self):
        """Stop the AI trading service"""
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("AI trading service stopped")
    
    async def _run_loop(self):
        """Main trading loop"""
        while self.is_running:
            try:
                await self.generate_and_execute_signals()
                await asyncio.sleep(self.SIGNAL_INTERVAL)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"AI trading loop error: {e}")
                await asyncio.sleep(self.SIGNAL_INTERVAL)


# Global instance
ai_trading_service = AITradingService()
