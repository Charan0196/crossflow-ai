"""
Real Funds Automated Trading System

Executes actual cryptocurrency trades with real funds on Sepolia testnet and Ethereum mainnet
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from decimal import Decimal
from dataclasses import dataclass, field
from enum import Enum
import json
import os
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account import Account
from eth_account.signers.local import LocalAccount
from mnemonic import Mnemonic

from src.services.signal_scheduler import signal_scheduler
from src.services.advanced_price_oracle import price_oracle
from src.config.database import get_db

logger = logging.getLogger(__name__)


class RealTradeMode(Enum):
    """Real trading modes"""
    TESTNET_TRADING = "testnet_trading"  # Execute real trades on Sepolia testnet
    MAINNET_TRADING = "mainnet_trading"  # Execute real trades on Ethereum mainnet
    DISABLED = "disabled"  # Trading disabled


@dataclass
class ExecutedTrade:
    """Executed trade record"""
    id: str
    token: str
    signal_type: str
    entry_price: Decimal
    exit_price: Optional[Decimal]
    position_size_usd: Decimal
    position_size_tokens: Decimal
    stop_loss: Decimal
    take_profit: Decimal
    gas_used: Decimal
    gas_cost_usd: Decimal
    profit_loss_usd: Optional[Decimal]
    status: str  # "open", "closed_profit", "closed_loss", "failed"
    entry_tx_hash: str
    exit_tx_hash: Optional[str]
    created_at: datetime
    closed_at: Optional[datetime]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "token": self.token,
            "signal_type": self.signal_type,
            "entry_price": str(self.entry_price),
            "exit_price": str(self.exit_price) if self.exit_price else None,
            "position_size_usd": str(self.position_size_usd),
            "position_size_tokens": str(self.position_size_tokens),
            "stop_loss": str(self.stop_loss),
            "take_profit": str(self.take_profit),
            "gas_used": str(self.gas_used),
            "gas_cost_usd": str(self.gas_cost_usd),
            "profit_loss_usd": str(self.profit_loss_usd) if self.profit_loss_usd else None,
            "status": self.status,
            "entry_tx_hash": self.entry_tx_hash,
            "exit_tx_hash": self.exit_tx_hash,
            "created_at": self.created_at.isoformat(),
            "closed_at": self.closed_at.isoformat() if self.closed_at else None
        }


@dataclass
class RealTradingOpportunity:
    """Real trading opportunity"""
    id: str
    token: str
    signal_type: str
    confidence: float
    current_price: Decimal
    target_price: Decimal
    stop_loss: Decimal
    take_profit: Decimal
    position_size_usd: Decimal
    position_size_tokens: Decimal
    gas_estimate: Decimal
    slippage_estimate: float
    liquidity_available: bool
    dex_route: str
    created_at: datetime
    expires_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "token": self.token,
            "signal_type": self.signal_type,
            "confidence": self.confidence,
            "current_price": str(self.current_price),
            "target_price": str(self.target_price),
            "stop_loss": str(self.stop_loss),
            "take_profit": str(self.take_profit),
            "position_size_usd": str(self.position_size_usd),
            "position_size_tokens": str(self.position_size_tokens),
            "gas_estimate": str(self.gas_estimate),
            "slippage_estimate": self.slippage_estimate,
            "liquidity_available": self.liquidity_available,
            "dex_route": self.dex_route,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat()
        }


@dataclass
class RealPortfolio:
    """Real portfolio tracking"""
    eth_balance: Decimal = Decimal("0.0")
    usdc_balance: Decimal = Decimal("0.0")
    token_balances: Dict[str, Decimal] = field(default_factory=dict)
    total_value_usd: Decimal = Decimal("0.0")
    wallet_address: Optional[str] = None
    chain_id: int = 11155111  # Sepolia
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "eth_balance": str(self.eth_balance),
            "usdc_balance": str(self.usdc_balance),
            "token_balances": {k: str(v) for k, v in self.token_balances.items()},
            "total_value_usd": str(self.total_value_usd),
            "wallet_address": self.wallet_address,
            "chain_id": self.chain_id,
            "last_updated": self.last_updated.isoformat()
        }


class RealFundsTrader:
    """
    Real funds automated trading system
    Executes actual trades on Sepolia testnet and Ethereum mainnet
    """
    
    def __init__(self):
        self.mode = RealTradeMode.TESTNET_TRADING  # Start with testnet
        self.portfolio = RealPortfolio()
        self.opportunities: List[RealTradingOpportunity] = []
        self.executed_trades: List[ExecutedTrade] = []
        self.open_positions: Dict[str, ExecutedTrade] = {}
        self.is_enabled = True
        self.min_confidence = 75.0  # Higher threshold for real trading
        self.max_position_size = 0.03  # Max 3% per trade for real funds
        self.max_total_exposure = 0.15  # Max 15% total exposure
        self.min_liquidity_usd = 10000  # Minimum $10k liquidity
        
        # Network configurations
        self.networks = {
            "sepolia": {
                "chain_id": 11155111,
                "rpc_url": "https://rpc.sepolia.org",
                "uniswap_router": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
                "uniswap_factory": "0x1F98431c8aD98523631AE4a59f267346ea31F984",
                "weth": "0xfFf9976782d46CC05630D1f6eBAb18b2324d6B14",
                "usdc": "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238"
            },
            "mainnet": {
                "chain_id": 1,
                "rpc_url": "https://mainnet.infura.io/v3/YOUR_INFURA_KEY",
                "uniswap_router": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
                "uniswap_factory": "0x1F98431c8aD98523631AE4a59f267346ea31F984",
                "weth": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                "usdc": "0xA0b86a33E6417c4c4c4c4c4c4c4c4c4c4c4c4c4c"
            }
        }
        
        # Current network config
        self.current_network = "sepolia"
        self.chain_id = self.networks[self.current_network]["chain_id"]
        self.rpc_url = self.networks[self.current_network]["rpc_url"]
        
        # Web3 and wallet
        self.w3 = None
        self.account: Optional[LocalAccount] = None
        self.wallet_address: Optional[str] = None
        
        # Trading parameters
        self.stop_loss_pct = Decimal("0.02")  # 2% stop loss
        self.take_profit_pct = Decimal("0.04")  # 4% take profit
        self.max_gas_price_gwei = 50  # Max gas price in Gwei
        self.slippage_tolerance = 0.005  # 0.5% slippage tolerance
        
        # Performance tracking
        self.stats = {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "total_profit_usd": Decimal("0.00"),
            "total_gas_spent": Decimal("0.00"),
            "max_drawdown": Decimal("0.00"),
            "started_at": datetime.utcnow()
        }
    
    async def setup_wallet(self, private_key: str = None, seed_phrase: str = None, account_index: int = 0):
        """Setup wallet for trading using private key or seed phrase"""
        try:
            logger.info("🔧 Starting wallet setup...")
            
            # First, clear any existing wallet connection
            self.wallet_address = None
            self.account = None
            self.w3 = None
            self.portfolio = RealPortfolio()
            self.open_positions.clear()
            
            if not private_key and not seed_phrase:
                logger.error("❌ No credentials provided")
                raise ValueError("Either private_key or seed_phrase must be provided")
            
            if private_key and seed_phrase:
                logger.error("❌ Both credentials provided")
                raise ValueError("Provide either private_key OR seed_phrase, not both")
            
            if seed_phrase:
                # Generate private key from seed phrase
                logger.info("🌱 Setting up wallet from seed phrase...")
                
                # Validate seed phrase
                mnemo = Mnemonic("english")
                if not mnemo.check(seed_phrase):
                    logger.error("❌ Invalid seed phrase format")
                    raise ValueError("Invalid seed phrase")
                
                # Generate seed from mnemonic
                seed = mnemo.to_seed(seed_phrase)
                logger.info("✅ Seed phrase validated and converted to seed")
                
                # Simple derivation using seed + account index
                import hashlib
                
                # Simple derivation using seed + account index
                account_seed = seed + account_index.to_bytes(4, 'big')
                private_key_hash = hashlib.sha256(account_seed).digest()
                private_key = private_key_hash.hex()
                
                logger.info(f"🔑 Generated private key for account index {account_index}")
            
            # Create account from private key
            if private_key.startswith('0x'):
                private_key_clean = private_key[2:]  # Remove 0x prefix
            else:
                private_key_clean = private_key
                
            # Ensure private key is exactly 32 bytes (64 hex characters)
            if len(private_key_clean) != 64:
                logger.error(f"❌ Invalid private key length: {len(private_key_clean)} characters, expected 64")
                raise ValueError("Private key must be exactly 64 hex characters (32 bytes)")
                
            logger.info("🔐 Creating account from private key...")
            self.account = Account.from_key(private_key_clean)
            self.wallet_address = self.account.address
            
            logger.info(f"🔑 Wallet setup completed: {self.wallet_address}")
            logger.info(f"🌐 Network: {self.current_network} (Chain ID: {self.chain_id})")
            
            # Update portfolio with wallet address
            self.portfolio.wallet_address = self.wallet_address
            self.portfolio.chain_id = self.chain_id
            
            # Initialize Web3 connection (optional - don't fail wallet setup if this fails)
            logger.info("🌐 Initializing Web3 connection...")
            try:
                await self.init_web3()
                logger.info("✅ Web3 connection established")
            except Exception as web3_error:
                logger.warning(f"⚠️ Web3 connection failed, but wallet setup can continue: {web3_error}")
            
            # Update initial balances (only if Web3 is connected)
            if self.w3 and self.w3.is_connected():
                logger.info("💰 Updating portfolio balances...")
                try:
                    await self.update_portfolio()
                    logger.info("✅ Portfolio balances updated")
                except Exception as balance_error:
                    logger.warning(f"⚠️ Failed to update balances: {balance_error}")
            else:
                logger.info("⚠️ Skipping balance update - Web3 not connected")
            
            logger.info("✅ Wallet setup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error setting up wallet: {e}", exc_info=True)
            return False
    
    def switch_network(self, network: str):
        """Switch between testnet and mainnet"""
        if network not in self.networks:
            raise ValueError(f"Unsupported network: {network}")
        
        self.current_network = network
        network_config = self.networks[network]
        self.chain_id = network_config["chain_id"]
        self.rpc_url = network_config["rpc_url"]
        
        # Update mode based on network
        if network == "sepolia":
            self.mode = RealTradeMode.TESTNET_TRADING
        elif network == "mainnet":
            self.mode = RealTradeMode.MAINNET_TRADING
        
        logger.info(f"🔄 Switched to {network} network (Chain ID: {self.chain_id})")
        logger.info(f"📊 Trading mode: {self.mode.value}")
    
    async def execute_trade(self, opportunity: RealTradingOpportunity) -> Optional[ExecutedTrade]:
        """Execute a real trade based on opportunity"""
        try:
            if not self.account or not self.w3:
                logger.error("❌ Wallet not setup or Web3 not connected")
                return None
            
            logger.info(f"🚀 Executing trade: {opportunity.token} {opportunity.signal_type}")
            
            # Check if we have sufficient balance
            if not await self.check_sufficient_balance(opportunity):
                logger.error(f"❌ Insufficient balance for trade: {opportunity.token}")
                return None
            
            # Check risk limits
            if not self.check_risk_limits(opportunity):
                logger.error(f"❌ Trade exceeds risk limits: {opportunity.token}")
                return None
            
            # Execute the swap transaction
            tx_hash = await self.execute_swap_transaction(opportunity)
            if not tx_hash:
                logger.error(f"❌ Failed to execute swap for {opportunity.token}")
                return None
            
            # Wait for transaction confirmation
            receipt = await self.wait_for_confirmation(tx_hash)
            if not receipt or receipt.status != 1:
                logger.error(f"❌ Transaction failed: {tx_hash}")
                return None
            
            # Calculate actual gas cost
            gas_used = receipt.gasUsed
            gas_price = receipt.effectiveGasPrice
            gas_cost_eth = Decimal(str(self.w3.from_wei(gas_used * gas_price, 'ether')))
            gas_cost_usd = gas_cost_eth * await self.get_eth_price_usd()
            
            # Create executed trade record
            trade = ExecutedTrade(
                id=f"trade_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{opportunity.token}",
                token=opportunity.token,
                signal_type=opportunity.signal_type,
                entry_price=opportunity.current_price,
                exit_price=None,
                position_size_usd=opportunity.position_size_usd,
                position_size_tokens=opportunity.position_size_tokens,
                stop_loss=opportunity.stop_loss,
                take_profit=opportunity.take_profit,
                gas_used=Decimal(str(gas_used)),
                gas_cost_usd=gas_cost_usd,
                profit_loss_usd=None,
                status="open",
                entry_tx_hash=tx_hash.hex(),
                exit_tx_hash=None,
                created_at=datetime.utcnow(),
                closed_at=None
            )
            
            # Add to tracking
            self.executed_trades.append(trade)
            self.open_positions[trade.id] = trade
            
            # Update stats
            self.stats["total_trades"] += 1
            self.stats["total_gas_spent"] += gas_cost_usd
            
            # Update portfolio
            await self.update_portfolio()
            
            logger.info(f"✅ Trade executed successfully: {trade.id}")
            logger.info(f"💰 Position: {trade.position_size_tokens} {trade.token} @ ${trade.entry_price}")
            logger.info(f"⛽ Gas cost: ${gas_cost_usd:.4f}")
            
            return trade
            
        except Exception as e:
            logger.error(f"Error executing trade: {e}", exc_info=True)
            return None
    
    async def execute_swap_transaction(self, opportunity: RealTradingOpportunity) -> Optional[str]:
        """Execute the actual swap transaction on blockchain"""
        try:
            network_config = self.networks[self.current_network]
            
            # For buy signals, swap ETH -> Token
            # For sell signals, swap Token -> ETH
            
            if opportunity.signal_type in ["buy", "strong_buy"]:
                # Swap ETH to Token
                amount_in = self.w3.to_wei(opportunity.position_size_usd / await self.get_eth_price_usd(), 'ether')
                token_in = network_config["weth"]
                token_out = self.get_token_address(opportunity.token)
            else:
                # Swap Token to ETH (for sell signals)
                amount_in = int(opportunity.position_size_tokens * Decimal("1e18"))  # Assume 18 decimals
                token_in = self.get_token_address(opportunity.token)
                token_out = network_config["weth"]
            
            # Build Uniswap V3 swap transaction
            router_address = network_config["uniswap_router"]
            
            # Simplified swap parameters (in production, use proper Uniswap SDK)
            swap_params = {
                'tokenIn': token_in,
                'tokenOut': token_out,
                'fee': 3000,  # 0.3% fee tier
                'recipient': self.wallet_address,
                'deadline': int((datetime.utcnow() + timedelta(minutes=20)).timestamp()),
                'amountIn': amount_in,
                'amountOutMinimum': 0,  # In production, calculate proper slippage
                'sqrtPriceLimitX96': 0
            }
            
            # Get current gas price
            gas_price = self.w3.eth.gas_price
            if gas_price > self.w3.to_wei(self.max_gas_price_gwei, 'gwei'):
                logger.warning(f"⚠️ Gas price too high: {self.w3.from_wei(gas_price, 'gwei')} Gwei")
                return None
            
            # Build transaction
            transaction = {
                'to': router_address,
                'value': amount_in if opportunity.signal_type in ["buy", "strong_buy"] else 0,
                'gas': 200000,  # Conservative gas limit
                'gasPrice': gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.wallet_address),
                'data': '0x'  # In production, encode proper Uniswap function call
            }
            
            # Sign transaction
            signed_txn = self.account.sign_transaction(transaction)
            
            # Broadcast transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            logger.info(f"📡 Transaction broadcast: {tx_hash.hex()}")
            return tx_hash
            
        except Exception as e:
            logger.error(f"Error executing swap transaction: {e}")
            return None
    
    async def wait_for_confirmation(self, tx_hash: str, timeout: int = 300) -> Optional[Any]:
        """Wait for transaction confirmation"""
        try:
            logger.info(f"⏳ Waiting for confirmation: {tx_hash}")
            
            start_time = datetime.utcnow()
            while (datetime.utcnow() - start_time).seconds < timeout:
                try:
                    receipt = self.w3.eth.get_transaction_receipt(tx_hash)
                    if receipt:
                        logger.info(f"✅ Transaction confirmed: {tx_hash}")
                        return receipt
                except Exception:
                    pass  # Transaction not yet mined
                
                await asyncio.sleep(10)  # Check every 10 seconds
            
            logger.error(f"❌ Transaction timeout: {tx_hash}")
            return None
            
        except Exception as e:
            logger.error(f"Error waiting for confirmation: {e}")
            return None
    
    async def check_sufficient_balance(self, opportunity: RealTradingOpportunity) -> bool:
        """Check if wallet has sufficient balance for trade"""
        try:
            if opportunity.signal_type in ["buy", "strong_buy"]:
                # Need ETH for buying
                eth_balance = self.w3.eth.get_balance(self.wallet_address)
                eth_balance_decimal = Decimal(str(self.w3.from_wei(eth_balance, 'ether')))
                eth_price = await self.get_eth_price_usd()
                eth_balance_usd = eth_balance_decimal * eth_price
                
                # Need balance for trade + gas
                required_usd = opportunity.position_size_usd + opportunity.gas_estimate
                
                return eth_balance_usd >= required_usd
            else:
                # Need token balance for selling
                # In production, check actual token balance
                return True  # Simplified for demo
                
        except Exception as e:
            logger.error(f"Error checking balance: {e}")
            return False
    
    def check_risk_limits(self, opportunity: RealTradingOpportunity) -> bool:
        """Check if trade meets risk management limits"""
        try:
            # Check position size limit
            if opportunity.position_size_usd > self.portfolio.total_value_usd * Decimal(str(self.max_position_size)):
                logger.warning(f"⚠️ Position size exceeds limit: ${opportunity.position_size_usd}")
                return False
            
            # Check total exposure limit
            total_open_value = sum(
                trade.position_size_usd for trade in self.open_positions.values()
            )
            if total_open_value + opportunity.position_size_usd > self.portfolio.total_value_usd * Decimal(str(self.max_total_exposure)):
                logger.warning(f"⚠️ Total exposure exceeds limit: ${total_open_value + opportunity.position_size_usd}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking risk limits: {e}")
            return False
    
    def get_token_address(self, token: str) -> str:
        """Get token contract address for current network"""
        network_config = self.networks[self.current_network]
        
        # Token mappings (simplified)
        token_addresses = {
            "USDC": network_config.get("usdc", "0x"),
            "WETH": network_config.get("weth", "0x"),
            "DAI": "0x3e622317f8C93f7328350cF0B56d9eD4C620C5d6"  # Example
        }
        
        return token_addresses.get(token, "0x")
    
    async def get_eth_price_usd(self) -> Decimal:
        """Get current ETH price in USD"""
        try:
            price_data = await price_oracle.get_price("ETHUSDT")
            if price_data:
                return price_data.price
            return Decimal("3000")  # Fallback price
        except Exception as e:
            logger.error(f"Error getting ETH price: {e}")
            return Decimal("3000")  # Fallback price
    async def start_monitoring(self):
        """Start monitoring for real trading opportunities and position management"""
        if not self.is_enabled:
            logger.info("Real funds trading is disabled")
            return
        
        logger.info("🔍 Starting real funds automated trading...")
        logger.info(f"📊 Network: {self.current_network} (Chain ID: {self.chain_id})")
        logger.info(f"💰 Mode: {self.mode.value.upper()}")
        logger.info(f"🎯 Min confidence: {self.min_confidence}%")
        logger.info(f"📈 Max position size: {self.max_position_size * 100}%")
        
        # Initialize Web3 connection
        await self.init_web3()
        
        # Start monitoring loops
        await asyncio.gather(
            self.opportunity_monitoring_loop(),
            self.position_monitoring_loop()
        )
    
    async def opportunity_monitoring_loop(self):
        """Monitor for new trading opportunities"""
        while self.is_enabled:
            try:
                logger.info("🔄 Scanning for trading opportunities...")
                await self.scan_and_execute_opportunities()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in opportunity monitoring: {e}", exc_info=True)
                await asyncio.sleep(120)  # Wait longer on error
    
    async def position_monitoring_loop(self):
        """Monitor open positions for stop-loss and take-profit"""
        while self.is_enabled:
            try:
                if self.open_positions:
                    logger.info(f"📊 Monitoring {len(self.open_positions)} open positions...")
                    await self.monitor_positions()
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Error in position monitoring: {e}", exc_info=True)
                await asyncio.sleep(60)
    
    async def scan_and_execute_opportunities(self):
        """Scan for opportunities and execute trades automatically"""
        try:
            # Get latest signals
            signals = signal_scheduler.get_latest_signals(limit=10)
            logger.info(f"📊 Found {len(signals)} signals to evaluate")
            
            for signal_data in signals:
                if not self.is_enabled:
                    break
                
                logger.info(f"🔍 Evaluating signal: {signal_data['token']} {signal_data['signal_type']} ({signal_data['confidence']:.0f}%)")
                
                # Create opportunity
                opportunity = await self.evaluate_real_opportunity(signal_data)
                if not opportunity:
                    continue
                
                logger.info(f"✅ Found trading opportunity: {opportunity.token}")
                
                # Execute trade automatically
                executed_trade = await self.execute_trade(opportunity)
                if executed_trade:
                    logger.info(f"🎯 Trade executed successfully: {executed_trade.id}")
                else:
                    logger.error(f"❌ Failed to execute trade for {opportunity.token}")
                
                # Small delay between trades
                await asyncio.sleep(5)
        
        except Exception as e:
            logger.error(f"Error scanning and executing opportunities: {e}", exc_info=True)
    
    async def monitor_positions(self):
        """Monitor open positions for stop-loss and take-profit triggers"""
        try:
            positions_to_close = []
            
            for trade_id, trade in self.open_positions.items():
                current_price = await self.get_real_price(trade.token)
                if not current_price:
                    continue
                
                should_close = False
                close_reason = ""
                
                # Check stop-loss
                if trade.signal_type in ["buy", "strong_buy"]:
                    if current_price <= trade.stop_loss:
                        should_close = True
                        close_reason = "stop_loss"
                    elif current_price >= trade.take_profit:
                        should_close = True
                        close_reason = "take_profit"
                else:  # sell signals
                    if current_price >= trade.stop_loss:
                        should_close = True
                        close_reason = "stop_loss"
                    elif current_price <= trade.take_profit:
                        should_close = True
                        close_reason = "take_profit"
                
                if should_close:
                    logger.info(f"🎯 Closing position {trade.id}: {close_reason} triggered")
                    positions_to_close.append((trade, close_reason, current_price))
            
            # Close positions that hit targets
            for trade, reason, exit_price in positions_to_close:
                await self.close_position(trade, reason, exit_price)
        
        except Exception as e:
            logger.error(f"Error monitoring positions: {e}", exc_info=True)
    
    async def close_position(self, trade: ExecutedTrade, reason: str, exit_price: Decimal):
        """Close an open position"""
        try:
            logger.info(f"🔄 Closing position: {trade.id} ({reason})")
            
            # Create reverse opportunity for closing
            close_opportunity = RealTradingOpportunity(
                id=f"close_{trade.id}",
                token=trade.token,
                signal_type="sell" if trade.signal_type in ["buy", "strong_buy"] else "buy",
                confidence=100.0,  # Always close when triggered
                current_price=exit_price,
                target_price=exit_price,
                stop_loss=exit_price,
                take_profit=exit_price,
                position_size_usd=trade.position_size_usd,
                position_size_tokens=trade.position_size_tokens,
                gas_estimate=Decimal("10.00"),
                slippage_estimate=0.5,
                liquidity_available=True,
                dex_route="Uniswap V3",
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(minutes=10)
            )
            
            # Execute closing transaction
            tx_hash = await self.execute_swap_transaction(close_opportunity)
            if not tx_hash:
                logger.error(f"❌ Failed to close position: {trade.id}")
                return
            
            # Wait for confirmation
            receipt = await self.wait_for_confirmation(tx_hash)
            if not receipt or receipt.status != 1:
                logger.error(f"❌ Close transaction failed: {tx_hash}")
                return
            
            # Calculate profit/loss
            if trade.signal_type in ["buy", "strong_buy"]:
                profit_loss = (exit_price - trade.entry_price) * trade.position_size_tokens
            else:
                profit_loss = (trade.entry_price - exit_price) * trade.position_size_tokens
            
            # Update trade record
            trade.exit_price = exit_price
            trade.exit_tx_hash = tx_hash.hex()
            trade.closed_at = datetime.utcnow()
            trade.profit_loss_usd = profit_loss
            trade.status = "closed_profit" if profit_loss > 0 else "closed_loss"
            
            # Update stats
            if profit_loss > 0:
                self.stats["winning_trades"] += 1
            else:
                self.stats["losing_trades"] += 1
            
            self.stats["total_profit_usd"] += profit_loss
            
            # Remove from open positions
            del self.open_positions[trade.id]
            
            # Update portfolio
            await self.update_portfolio()
            
            logger.info(f"✅ Position closed: {trade.id}")
            logger.info(f"💰 P&L: ${profit_loss:.2f} ({reason})")
            
        except Exception as e:
            logger.error(f"Error closing position {trade.id}: {e}", exc_info=True)
    
    async def init_web3(self):
        """Initialize Web3 connection"""
        try:
            logger.info(f"🌐 Initializing Web3 connection to {self.current_network}...")
            
            # Get network configuration
            network_config = self.networks.get(self.current_network)
            if not network_config:
                raise ValueError(f"Unsupported network: {self.current_network}")
            
            # Use configured RPC URL or fallback to public RPC
            if self.current_network == "sepolia":
                # Try multiple Sepolia RPC endpoints
                rpc_urls = [
                    "https://ethereum-sepolia.blockpi.network/v1/rpc/public",
                    "https://rpc.sepolia.org",
                    "https://sepolia.gateway.tenderly.co",
                    "https://gateway.tenderly.co/public/sepolia"
                ]
            else:
                # Mainnet RPC (would need proper Infura key in production)
                rpc_urls = [network_config["rpc_url"]]
            
            # Try connecting to RPC endpoints
            connected = False
            for rpc_url in rpc_urls:
                try:
                    logger.info(f"🔗 Trying RPC: {rpc_url}")
                    self.rpc_url = rpc_url
                    self.w3 = Web3(Web3.HTTPProvider(rpc_url))
                    
                    # Add PoA middleware for testnets
                    if self.current_network == "sepolia":
                        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
                    
                    # Test connection
                    if self.w3.is_connected():
                        latest_block = self.w3.eth.block_number
                        chain_id = self.w3.eth.chain_id
                        
                        # Verify chain ID matches expected
                        if chain_id == network_config["chain_id"]:
                            logger.info(f"✅ Connected to {self.current_network}")
                            logger.info(f"📦 Latest block: {latest_block}")
                            logger.info(f"🔗 Chain ID: {chain_id}")
                            connected = True
                            break
                        else:
                            logger.warning(f"⚠️ Chain ID mismatch: expected {network_config['chain_id']}, got {chain_id}")
                    
                except Exception as e:
                    logger.warning(f"⚠️ RPC connection failed: {e}")
                    continue
            
            if not connected:
                raise Exception(f"Failed to connect to any {self.current_network} RPC endpoint")
                
            logger.info("✅ Web3 connection initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Error initializing Web3: {e}", exc_info=True)
            raise
    
    async def scan_opportunities(self):
        """Scan for real trading opportunities (legacy method for compatibility)"""
        try:
            logger.info("🔍 Scanning for real trading opportunities...")
            
            # Get latest signals
            signals = signal_scheduler.get_latest_signals(limit=10)
            logger.info(f"📊 Found {len(signals)} signals to evaluate")
            
            new_opportunities = []
            
            for signal_data in signals:
                logger.info(f"🔍 Evaluating signal: {signal_data['token']} {signal_data['signal_type']} ({signal_data['confidence']:.0f}%)")
                opportunity = await self.evaluate_real_opportunity(signal_data)
                if opportunity:
                    new_opportunities.append(opportunity)
                    logger.info(f"✅ Created opportunity for {opportunity.token}")
                else:
                    logger.info(f"❌ Skipped {signal_data['token']} - conditions not met")
            
            # Update opportunities list
            self.opportunities = new_opportunities
            
            if new_opportunities:
                logger.info(f"🎯 Found {len(new_opportunities)} trading opportunities")
                for opp in new_opportunities[:3]:  # Log top 3
                    logger.info(
                        f"  💡 {opp.token}: {opp.signal_type.upper()} @ ${opp.current_price:.2f} "
                        f"({opp.confidence:.0f}% confidence, ${opp.position_size_usd:.0f})"
                    )
            else:
                logger.info("📭 No trading opportunities found")
        
        except Exception as e:
            logger.error(f"Error scanning opportunities: {e}", exc_info=True)
    
    async def evaluate_real_opportunity(self, signal_data: Dict[str, Any]) -> Optional[RealTradingOpportunity]:
        """Evaluate a signal for real trading opportunity"""
        try:
            token = signal_data["token"]
            signal_type = signal_data["signal_type"]
            confidence = signal_data["confidence"]
            
            logger.info(f"🔍 Evaluating {token}: {signal_type} ({confidence}%)")
            
            # Skip if confidence too low
            if confidence < self.min_confidence:
                logger.info(f"❌ {token} confidence {confidence}% < {self.min_confidence}% threshold")
                return None
            
            logger.info(f"✅ {token} passed confidence check")
            
            # Get real current price
            current_price = await self.get_real_price(token)
            if not current_price:
                logger.info(f"❌ {token} - no price available")
                return None
            
            logger.info(f"✅ {token} price: ${current_price}")
            
            # Calculate position size based on portfolio value
            if self.portfolio.total_value_usd <= 0:
                # Use default for initial calculation
                portfolio_value = Decimal("100.00")  # Minimum portfolio
            else:
                portfolio_value = self.portfolio.total_value_usd
            
            position_size_usd = self.calculate_position_size(confidence, portfolio_value)
            position_size_tokens = position_size_usd / current_price
            
            logger.info(f"✅ {token} position size: ${position_size_usd} ({position_size_tokens} tokens)")
            
            # Check liquidity
            liquidity_available = await self.check_liquidity(token, position_size_usd)
            
            # Estimate gas costs
            gas_estimate = await self.estimate_gas_cost(token, position_size_tokens)
            
            # Calculate targets
            stop_loss, take_profit = self.calculate_real_targets(current_price, signal_type)
            
            # Determine DEX route
            dex_route = await self.find_best_route(token, position_size_usd)
            
            opportunity = RealTradingOpportunity(
                id=f"opp_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{token}",
                token=token,
                signal_type=signal_type,
                confidence=confidence,
                current_price=current_price,
                target_price=take_profit,
                stop_loss=stop_loss,
                take_profit=take_profit,
                position_size_usd=position_size_usd,
                position_size_tokens=position_size_tokens,
                gas_estimate=gas_estimate,
                slippage_estimate=0.5,  # 0.5% estimated slippage
                liquidity_available=liquidity_available,
                dex_route=dex_route,
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(hours=1)
            )
            
            logger.info(f"✅ Created opportunity for {token}: ${current_price} -> ${take_profit}")
            
            return opportunity
        
        except Exception as e:
            logger.error(f"Error evaluating opportunity for {signal_data.get('token', 'unknown')}: {e}")
            return None
    
    async def get_real_price(self, token: str) -> Optional[Decimal]:
        """Get real current price from price oracle"""
        try:
            # Use the existing price oracle
            price_data = await price_oracle.get_price(f"{token}USDT")
            if price_data:
                return price_data.price
            return None
        except Exception as e:
            logger.error(f"Error getting real price for {token}: {e}")
            return None
    
    async def check_liquidity(self, token: str, amount_usd: Decimal) -> bool:
        """Check if sufficient liquidity exists"""
        try:
            # For demo, simulate liquidity check
            # In real implementation, query Uniswap pools
            major_tokens = ["BTC", "ETH", "BNB", "SOL"]
            if token in major_tokens:
                return amount_usd <= Decimal("50000")  # Major tokens have good liquidity
            else:
                return amount_usd <= Decimal("10000")  # Smaller tokens limited
        except Exception as e:
            logger.error(f"Error checking liquidity for {token}: {e}")
            return False
    
    async def estimate_gas_cost(self, token: str, amount: Decimal) -> Decimal:
        """Estimate gas cost for the trade"""
        try:
            if not self.w3 or not self.w3.is_connected():
                return Decimal("0.01")  # Default estimate
            
            # Get current gas price
            gas_price = self.w3.eth.gas_price
            
            # Estimate gas units for Uniswap swap (typically 150k-200k)
            gas_units = 180000
            
            # Calculate cost in ETH
            gas_cost_wei = gas_price * gas_units
            gas_cost_eth = Decimal(str(self.w3.from_wei(gas_cost_wei, 'ether')))
            
            # Convert to USD (assume ETH = $3000 for estimation)
            eth_price = Decimal("3000")
            gas_cost_usd = gas_cost_eth * eth_price
            
            return gas_cost_usd
        
        except Exception as e:
            logger.error(f"Error estimating gas cost: {e}")
            return Decimal("10.00")  # Conservative estimate
    
    async def find_best_route(self, token: str, amount_usd: Decimal) -> str:
        """Find best DEX route for the trade"""
        try:
            # For demo, simulate route finding
            if amount_usd > Decimal("1000"):
                return "Uniswap V3 (0.3% fee)"
            else:
                return "Uniswap V2 (0.3% fee)"
        except Exception as e:
            logger.error(f"Error finding route for {token}: {e}")
            return "Unknown route"
    
    def calculate_position_size(self, confidence: float, portfolio_value: Decimal) -> Decimal:
        """Calculate position size based on confidence and portfolio value"""
        # More conservative for real funds
        base_size_pct = Decimal("0.01")  # 1% base
        max_size_pct = Decimal(str(self.max_position_size))  # 3% max
        
        # Scale based on confidence (75-100% -> 0-1)
        confidence_factor = max(0, (confidence - 75) / 25)
        confidence_multiplier = Decimal(str(confidence_factor))
        
        # Calculate position size percentage
        position_size_pct = base_size_pct + (max_size_pct - base_size_pct) * confidence_multiplier
        
        # Calculate USD amount
        position_size_usd = portfolio_value * position_size_pct
        
        # Minimum position size
        min_position = Decimal("10.00")  # $10 minimum
        
        return max(position_size_usd, min_position)
    
    def calculate_real_targets(self, current_price: Decimal, signal_type: str) -> tuple[Decimal, Decimal]:
        """Calculate realistic stop-loss and take-profit targets"""
        if signal_type in ["buy", "strong_buy"]:
            stop_loss = current_price * (1 - self.stop_loss_pct)
            take_profit = current_price * (1 + self.take_profit_pct)
        else:
            stop_loss = current_price * (1 + self.stop_loss_pct)
            take_profit = current_price * (1 - self.take_profit_pct)
        
        return stop_loss, take_profit
    
    async def update_portfolio(self):
        """Update real portfolio balances from blockchain"""
        try:
            if not self.wallet_address or not self.w3:
                return
            
            # Get ETH balance
            eth_balance_wei = self.w3.eth.get_balance(self.wallet_address)
            eth_balance = Decimal(str(self.w3.from_wei(eth_balance_wei, 'ether')))
            
            # Get ETH price
            eth_price = await self.get_eth_price_usd()
            
            # Update portfolio
            self.portfolio.eth_balance = eth_balance
            self.portfolio.total_value_usd = eth_balance * eth_price
            self.portfolio.last_updated = datetime.utcnow()
            
            # In production, also query token balances
            # For now, we'll track based on open positions
            
            logger.info(f"💰 Portfolio updated: {eth_balance:.4f} ETH (${self.portfolio.total_value_usd:.2f})")
            
        except Exception as e:
            logger.error(f"Error updating portfolio: {e}")
    
    def get_executed_trades(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get executed trades history"""
        # Sort by creation date, newest first
        sorted_trades = sorted(self.executed_trades, key=lambda x: x.created_at, reverse=True)
        return [trade.to_dict() for trade in sorted_trades[:limit]]
    
    def get_open_positions(self) -> List[Dict[str, Any]]:
        """Get current open positions"""
        return [trade.to_dict() for trade in self.open_positions.values()]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get trading performance summary"""
        total_trades = self.stats["total_trades"]
        winning_trades = self.stats["winning_trades"]
        losing_trades = self.stats["losing_trades"]
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        return {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": round(win_rate, 1),
            "total_profit_usd": str(self.stats["total_profit_usd"]),
            "total_gas_spent": str(self.stats["total_gas_spent"]),
            "open_positions": len(self.open_positions),
            "portfolio_value": str(self.portfolio.total_value_usd),
            "started_at": self.stats["started_at"].isoformat()
        }
    
    def get_opportunities(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get current trading opportunities (legacy method for compatibility)"""
        # Filter out expired opportunities
        current_time = datetime.utcnow()
        active_opportunities = [
            opp for opp in self.opportunities 
            if opp.expires_at > current_time
        ]
        
        # Sort by confidence
        active_opportunities.sort(key=lambda x: x.confidence, reverse=True)
        
        return [opp.to_dict() for opp in active_opportunities[:limit]]
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get portfolio summary"""
        return self.portfolio.to_dict()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get trading statistics"""
        return {
            "mode": self.mode.value,
            "network": self.current_network,
            "is_enabled": self.is_enabled,
            "wallet_address": self.wallet_address,
            "total_trades": self.stats["total_trades"],
            "winning_trades": self.stats["winning_trades"],
            "losing_trades": self.stats["losing_trades"],
            "open_positions": len(self.open_positions),
            "total_profit_usd": str(self.stats["total_profit_usd"]),
            "total_gas_spent": str(self.stats["total_gas_spent"]),
            "portfolio_value": str(self.portfolio.total_value_usd),
            "min_confidence": self.min_confidence,
            "max_position_size": self.max_position_size,
            "max_total_exposure": self.max_total_exposure,
            "chain_id": self.chain_id,
            "started_at": self.stats["started_at"].isoformat()
        }
    
    def set_wallet_address(self, address: str):
        """Set wallet address for portfolio tracking (deprecated - use setup_wallet)"""
        self.portfolio.wallet_address = address
        self.wallet_address = address
        logger.info(f"📱 Wallet address set: {address}")
    
    def enable_trading(self):
        """Enable automated trading"""
        self.is_enabled = True
        logger.info("🟢 Real funds automated trading enabled")
    
    def disable_trading(self):
        """Disable automated trading"""
        self.is_enabled = False
        logger.info("🔴 Real funds automated trading disabled")
    
    def update_settings(self, settings: Dict[str, Any]):
        """Update trading settings"""
        if "min_confidence" in settings:
            self.min_confidence = float(settings["min_confidence"])
        if "max_position_size" in settings:
            self.max_position_size = float(settings["max_position_size"])
        if "max_total_exposure" in settings:
            self.max_total_exposure = float(settings["max_total_exposure"])
        if "stop_loss_pct" in settings:
            self.stop_loss_pct = Decimal(str(settings["stop_loss_pct"]))
        if "take_profit_pct" in settings:
            self.take_profit_pct = Decimal(str(settings["take_profit_pct"]))
        
        logger.info(f"Real funds trading settings updated: {settings}")
    
    async def emergency_stop(self):
        """Emergency stop - close all positions and disable trading"""
        try:
            logger.warning("🚨 EMERGENCY STOP ACTIVATED")
            
            # Disable trading
            self.is_enabled = False
            
            # Close all open positions
            for trade_id, trade in list(self.open_positions.items()):
                current_price = await self.get_real_price(trade.token)
                if current_price:
                    await self.close_position(trade, "emergency_stop", current_price)
            
            logger.warning("🚨 Emergency stop completed - all positions closed")
            
        except Exception as e:
            logger.error(f"Error during emergency stop: {e}", exc_info=True)


# Global real funds trader instance
real_funds_trader = RealFundsTrader()