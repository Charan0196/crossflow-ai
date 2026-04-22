"""
Risk Manager Service
Implements risk management rules for autonomous trading
"""
import logging
from typing import Dict, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RiskManager:
    """Manages trading risk parameters and validations"""
    
    # Risk parameters
    MAX_POSITION_SIZE_PERCENT = Decimal('10')  # 10% of portfolio
    MAX_DRAWDOWN_PERCENT = Decimal('20')  # 20% circuit breaker
    MAX_DAILY_LOSS_PERCENT = Decimal('5')  # 5% daily loss limit
    MIN_GAS_BALANCE = Decimal('0.01')  # 0.01 ETH minimum
    STOP_LOSS_PERCENT = Decimal('5')  # 5% below entry
    TAKE_PROFIT_PERCENT = Decimal('10')  # 10% above entry
    
    def __init__(self):
        self.peak_portfolio_value: Dict[str, Decimal] = {}
        self.daily_loss_tracker: Dict[str, Dict] = {}
    
    def check_position_size(
        self,
        amount: Decimal,
        portfolio_value: Decimal
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if position size is within limits
        
        Args:
            amount: Trade amount in USD
            portfolio_value: Total portfolio value in USD
            
        Returns:
            (is_valid, error_message)
        """
        if portfolio_value <= 0:
            return False, "Portfolio value must be positive"
        
        position_percent = (amount / portfolio_value) * 100
        
        if position_percent > self.MAX_POSITION_SIZE_PERCENT:
            return False, f"Position size {position_percent:.2f}% exceeds limit of {self.MAX_POSITION_SIZE_PERCENT}%"
        
        return True, None
    
    def check_drawdown(
        self,
        wallet_address: str,
        current_value: Decimal,
        peak_value: Optional[Decimal] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if drawdown exceeds circuit breaker threshold
        
        Args:
            wallet_address: Wallet address
            current_value: Current portfolio value
            peak_value: Peak portfolio value (optional, will track if not provided)
            
        Returns:
            (is_valid, error_message)
        """
        # Update peak value
        if peak_value is not None:
            self.peak_portfolio_value[wallet_address] = peak_value
        elif wallet_address not in self.peak_portfolio_value:
            self.peak_portfolio_value[wallet_address] = current_value
        else:
            # Update peak if current is higher
            if current_value > self.peak_portfolio_value[wallet_address]:
                self.peak_portfolio_value[wallet_address] = current_value
        
        peak = self.peak_portfolio_value[wallet_address]
        
        if peak <= 0:
            return True, None
        
        drawdown_percent = ((peak - current_value) / peak) * 100
        
        if drawdown_percent > self.MAX_DRAWDOWN_PERCENT:
            return False, f"Drawdown {drawdown_percent:.2f}% exceeds circuit breaker at {self.MAX_DRAWDOWN_PERCENT}%"
        
        return True, None
    
    def check_daily_loss(
        self,
        wallet_address: str,
        daily_loss: Decimal,
        portfolio_value: Decimal
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if daily loss exceeds limit
        
        Args:
            wallet_address: Wallet address
            daily_loss: Loss amount today (positive number)
            portfolio_value: Total portfolio value
            
        Returns:
            (is_valid, error_message)
        """
        if portfolio_value <= 0:
            return False, "Portfolio value must be positive"
        
        # Reset daily tracker if new day
        today = datetime.utcnow().date()
        if wallet_address in self.daily_loss_tracker:
            tracker_date = self.daily_loss_tracker[wallet_address].get('date')
            if tracker_date != today:
                self.daily_loss_tracker[wallet_address] = {
                    'date': today,
                    'loss': Decimal('0')
                }
        else:
            self.daily_loss_tracker[wallet_address] = {
                'date': today,
                'loss': Decimal('0')
            }
        
        # Update daily loss
        self.daily_loss_tracker[wallet_address]['loss'] += daily_loss
        total_daily_loss = self.daily_loss_tracker[wallet_address]['loss']
        
        loss_percent = (total_daily_loss / portfolio_value) * 100
        
        if loss_percent > self.MAX_DAILY_LOSS_PERCENT:
            return False, f"Daily loss {loss_percent:.2f}% exceeds limit of {self.MAX_DAILY_LOSS_PERCENT}%"
        
        return True, None
    
    def validate_gas_balance(
        self,
        eth_balance: Decimal
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate minimum gas balance
        
        Args:
            eth_balance: ETH balance
            
        Returns:
            (is_valid, error_message)
        """
        if eth_balance < self.MIN_GAS_BALANCE:
            return False, f"ETH balance {eth_balance} below minimum {self.MIN_GAS_BALANCE}"
        
        return True, None
    
    def validate_token_balance(
        self,
        token: str,
        amount: Decimal,
        balance: Decimal
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate sufficient token balance
        
        Args:
            token: Token symbol
            amount: Required amount
            balance: Available balance
            
        Returns:
            (is_valid, error_message)
        """
        if balance < amount:
            return False, f"Insufficient {token} balance. Required: {amount}, Available: {balance}"
        
        return True, None
    
    def set_stop_loss(
        self,
        entry_price: Decimal
    ) -> Decimal:
        """
        Calculate stop loss price (5% below entry)
        
        Args:
            entry_price: Entry price
            
        Returns:
            Stop loss price
        """
        return entry_price * (1 - self.STOP_LOSS_PERCENT / 100)
    
    def set_take_profit(
        self,
        entry_price: Decimal
    ) -> Decimal:
        """
        Calculate take profit price (10% above entry)
        
        Args:
            entry_price: Entry price
            
        Returns:
            Take profit price
        """
        return entry_price * (1 + self.TAKE_PROFIT_PERCENT / 100)
    
    def validate_trade(
        self,
        wallet_address: str,
        amount: Decimal,
        portfolio_value: Decimal,
        eth_balance: Decimal,
        token_balance: Optional[Decimal] = None,
        token: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Comprehensive trade validation
        
        Args:
            wallet_address: Wallet address
            amount: Trade amount in USD
            portfolio_value: Total portfolio value
            eth_balance: ETH balance for gas
            token_balance: Token balance (if selling)
            token: Token symbol (if selling)
            
        Returns:
            (is_valid, error_message)
        """
        # Check gas balance
        is_valid, error = self.validate_gas_balance(eth_balance)
        if not is_valid:
            return False, error
        
        # Check position size
        is_valid, error = self.check_position_size(amount, portfolio_value)
        if not is_valid:
            return False, error
        
        # Check drawdown
        is_valid, error = self.check_drawdown(wallet_address, portfolio_value)
        if not is_valid:
            return False, error
        
        # Check token balance if selling
        if token_balance is not None and token is not None:
            is_valid, error = self.validate_token_balance(token, amount, token_balance)
            if not is_valid:
                return False, error
        
        return True, None


# Global instance
risk_manager = RiskManager()
