"""
Autonomous Trading API Routes
WARNING: Only use with testnet accounts!
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from ...services.autonomous_trader import autonomous_trader
from ...services.auto_faucet import auto_faucet

router = APIRouter(prefix="/autonomous", tags=["Autonomous Trading"])


class AddWalletRequest(BaseModel):
    """Request to add a wallet for autonomous trading"""
    wallet_id: str
    private_key: Optional[str] = None  # TESTNET ONLY!
    seed_phrase: Optional[str] = None  # TESTNET ONLY! 12 or 24 words
    account_index: Optional[int] = 0  # For seed phrase derivation
    max_trade_amount: float = 0.01
    risk_level: str = "low"
    allowed_tokens: List[str] = ["ETH", "USDC", "WETH"]
    stop_loss_percent: float = 5.0
    take_profit_percent: float = 10.0


class WalletActionRequest(BaseModel):
    """Request to start/stop trading for a wallet"""
    wallet_id: str


class ManualTradeRequest(BaseModel):
    """Request to manually execute a trade"""
    wallet_id: str
    action: str  # 'buy' or 'sell'
    token: str  # Token symbol (e.g., 'USDC')
    amount: float  # Amount in ETH or token units


@router.post("/wallet/add")
async def add_wallet(request: AddWalletRequest):
    """
    Add a wallet for autonomous trading
    
    **WARNING: Only use testnet private keys or seed phrases!**
    
    - **wallet_id**: Unique identifier for this wallet
    - **private_key**: Private key (TESTNET ONLY!) - optional if seed_phrase provided
    - **seed_phrase**: 12 or 24 word seed phrase (TESTNET ONLY!) - optional if private_key provided
    - **account_index**: Account index to derive from seed phrase (default: 0)
    - **max_trade_amount**: Maximum amount per trade
    - **risk_level**: low/medium/high
    - **allowed_tokens**: List of token symbols to trade
    - **stop_loss_percent**: Stop loss percentage
    - **take_profit_percent**: Take profit percentage
    """
    # Validate that either private_key or seed_phrase is provided
    if not request.private_key and not request.seed_phrase:
        raise HTTPException(
            status_code=400, 
            detail="Either private_key or seed_phrase must be provided"
        )
    
    if request.private_key and request.seed_phrase:
        raise HTTPException(
            status_code=400,
            detail="Provide either private_key or seed_phrase, not both"
        )
    
    config = {
        'max_trade_amount': request.max_trade_amount,
        'risk_level': request.risk_level,
        'allowed_tokens': request.allowed_tokens,
        'stop_loss_percent': request.stop_loss_percent,
        'take_profit_percent': request.take_profit_percent
    }
    
    result = autonomous_trader.add_wallet(
        wallet_id=request.wallet_id,
        private_key=request.private_key,
        seed_phrase=request.seed_phrase,
        account_index=request.account_index,
        config=config
    )
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result.get('error', 'Failed to add wallet'))
    
    return result


@router.post("/wallet/remove")
async def remove_wallet(request: WalletActionRequest):
    """Remove a wallet from autonomous trading"""
    result = autonomous_trader.remove_wallet(request.wallet_id)
    
    if not result['success']:
        raise HTTPException(status_code=404, detail=result.get('error', 'Wallet not found'))
    
    return result


@router.post("/trading/start")
async def start_trading(request: WalletActionRequest):
    """Start autonomous trading for a wallet"""
    result = await autonomous_trader.start_trading(request.wallet_id)
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result.get('error', 'Failed to start trading'))
    
    return result


@router.post("/trading/stop")
async def stop_trading(request: WalletActionRequest):
    """Stop autonomous trading for a wallet"""
    result = await autonomous_trader.stop_trading(request.wallet_id)
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result.get('error', 'Failed to stop trading'))
    
    return result


@router.get("/wallet/{wallet_id}/status")
async def get_wallet_status(wallet_id: str):
    """Get status of a specific wallet"""
    status = autonomous_trader.get_wallet_status(wallet_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    return status


@router.get("/wallets")
async def get_all_wallets():
    """Get status of all wallets"""
    return {
        'wallets': autonomous_trader.get_all_wallets()
    }


@router.post("/trade/manual")
async def execute_manual_trade(request: ManualTradeRequest):
    """
    Manually execute a trade for testing
    
    - **wallet_id**: Wallet to trade with
    - **action**: 'buy' or 'sell'
    - **token**: Token symbol (e.g., 'USDC')
    - **amount**: Amount to trade
    """
    if request.wallet_id not in autonomous_trader.active_traders:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    decision = {
        'action': request.action,
        'token': request.token,
        'amount': request.amount
    }
    
    # Execute trade
    await autonomous_trader._execute_trade(request.wallet_id, decision)
    
    # Get updated wallet status
    status = autonomous_trader.get_wallet_status(request.wallet_id)
    
    return {
        'success': True,
        'message': 'Trade executed',
        'wallet': status
    }


@router.post("/wallet/{wallet_id}/auto-fund")
async def auto_fund_wallet(wallet_id: str):
    """
    Automatically request faucet tokens for a wallet if balance is low
    
    - **wallet_id**: Wallet to fund
    """
    if wallet_id not in autonomous_trader.active_traders:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    trader = autonomous_trader.active_traders[wallet_id]
    address = trader['address']
    
    # Try to auto-drip tokens
    result = await auto_faucet.auto_drip_for_wallet(address, network='sepolia', min_balance=0.01)
    
    return result


@router.post("/wallet/{wallet_id}/fund-and-trade")
async def fund_and_trade(wallet_id: str):
    """
    Auto-fund wallet and start trading
    
    - **wallet_id**: Wallet to fund and trade with
    """
    if wallet_id not in autonomous_trader.active_traders:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    trader = autonomous_trader.active_traders[wallet_id]
    address = trader['address']
    
    # Step 1: Check/request faucet tokens
    fund_result = await auto_faucet.auto_drip_for_wallet(address, network='sepolia', min_balance=0.01)
    
    # Step 2: Start trading if funded
    if fund_result.get('success') or fund_result.get('balance', 0) >= 0.01:
        trade_result = await autonomous_trader.start_trading(wallet_id)
        
        return {
            'success': True,
            'funding': fund_result,
            'trading': trade_result,
            'message': 'Wallet funded and trading started'
        }
    else:
        return {
            'success': False,
            'funding': fund_result,
            'message': 'Unable to auto-fund. Please use manual faucets.',
            'manual_faucets': fund_result.get('manual_faucets', []),
            'instructions': fund_result.get('instructions', '')
        }
