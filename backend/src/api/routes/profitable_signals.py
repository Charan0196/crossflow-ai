"""
Profitable Signals API Routes
Endpoints for generating and executing profitable trading signals
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

from ...services.profitable_signals_service import profitable_signals_service
from ...services.signal_execution_service import signal_execution_service

router = APIRouter(prefix="/profitable-signals", tags=["Profitable Signals"])


class ExecuteSignalRequest(BaseModel):
    """Request model for executing a signal"""
    signal_id: str
    wallet_address: str
    amount: float
    network: Optional[str] = "ethereum"
    slippage: Optional[float] = 0.5


class SwapQuoteRequest(BaseModel):
    """Request model for getting swap quote"""
    from_token: str
    to_token: str
    amount: float
    network: Optional[str] = "ethereum"


class WalletValidationRequest(BaseModel):
    """Request model for wallet validation"""
    wallet_address: str
    network: Optional[str] = "ethereum"


@router.post("/clear-cache")
async def clear_signals_cache():
    """Clear signals cache to force regeneration"""
    try:
        success = await profitable_signals_service.clear_cache()
        
        return {
            "success": success,
            "message": "Signals cache cleared successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


@router.get("/signals/demo")
async def get_demo_signals(limit: int = 3):
    """Generate demo signals for testing"""
    try:
        from datetime import datetime, timedelta
        
        demo_signals = [
            {
                'id': f'demo_signal_1_{int(datetime.now().timestamp())}',
                'token_pair': 'BTCUSDT',
                'action': 'BUY',
                'confidence': 75,
                'profit_potential': 8.5,
                'entry_price': 68500.0,
                'target_price': 74322.5,
                'stop_loss': 65175.0,
                'timeframe': '1H-4H',
                'reason': 'Demo signal: Oversold bounce expected with volume support',
                'risk_level': 'MEDIUM',
                'market_cap': 1350000000000,
                'volume_24h': 25000000000,
                'ai_analysis': 'Demo analysis: Technical indicators suggest potential reversal',
                'created_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(hours=4)).isoformat()
            },
            {
                'id': f'demo_signal_2_{int(datetime.now().timestamp())}',
                'token_pair': 'ETHUSDT',
                'action': 'BUY',
                'confidence': 70,
                'profit_potential': 7.2,
                'entry_price': 1980.0,
                'target_price': 2122.56,
                'stop_loss': 1881.0,
                'timeframe': '1H-4H',
                'reason': 'Demo signal: Support level holding with increasing volume',
                'risk_level': 'MEDIUM',
                'market_cap': 238000000000,
                'volume_24h': 15000000000,
                'ai_analysis': 'Demo analysis: Strong support at current levels',
                'created_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(hours=4)).isoformat()
            },
            {
                'id': f'demo_signal_3_{int(datetime.now().timestamp())}',
                'token_pair': 'SOLUSDT',
                'action': 'BUY',
                'confidence': 68,
                'profit_potential': 6.8,
                'entry_price': 84.50,
                'target_price': 90.25,
                'stop_loss': 80.27,
                'timeframe': '1H-4H',
                'reason': 'Demo signal: Oversold conditions with bullish divergence',
                'risk_level': 'MEDIUM',
                'market_cap': 40000000000,
                'volume_24h': 2000000000,
                'ai_analysis': 'Demo analysis: RSI showing bullish divergence',
                'created_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(hours=4)).isoformat()
            }
        ]
        
        return {
            "success": True,
            "signals": demo_signals[:limit],
            "count": len(demo_signals[:limit]),
            "message": "Demo signals generated successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate demo signals: {str(e)}")


@router.get("/signals")
async def get_profitable_signals(limit: int = 5):
    """
    Get profitable trading signals with high profit potential
    
    - **limit**: Maximum number of signals to return (default: 5)
    
    Returns signals with:
    - AI-powered analysis
    - Technical indicators
    - Profit potential
    - Risk assessment
    - Entry/exit points
    """
    try:
        signals = await profitable_signals_service.get_cached_signals()
        
        # Convert signals to dictionaries
        signal_dicts = [
            profitable_signals_service.signal_to_dict(signal) 
            for signal in signals[:limit]
        ]
        
        return {
            "success": True,
            "signals": signal_dicts,
            "count": len(signal_dicts),
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get signals: {str(e)}")


@router.post("/signals/demo")
async def generate_demo_signals():
    """
    Generate demo signals for testing
    """
    try:
        from datetime import datetime, timedelta
        from ...services.profitable_signals_service import ProfitableSignal
        
        # Create demo signals
        demo_signals = [
            ProfitableSignal(
                id="signal_BTCUSDT_1709483924",
                token_pair="BTCUSDT",
                action="BUY",
                confidence=87.5,
                profit_potential=12.3,
                entry_price=65420.50,
                target_price=73500.00,
                stop_loss=61250.00,
                timeframe="4H",
                reason="Strong bullish momentum with RSI oversold at 28. Volume spike indicates institutional buying. Breaking above key resistance at $65,000 with high volume confirmation.",
                risk_level="MEDIUM",
                market_cap=1280000000000,
                volume_24h=28500000000,
                technical_indicators={
                    "rsi": 28.5,
                    "ma_20": 64200.0,
                    "ma_50": 62800.0,
                    "macd_line": 1250.0,
                    "volume_ratio": 2.3,
                    "support": 61000.0,
                    "resistance": 67000.0
                },
                ai_analysis="Technical analysis shows strong bullish divergence with oversold RSI and increasing volume. Breakout above $65k resistance level with institutional support.",
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=4)
            ),
            ProfitableSignal(
                id="signal_ETHUSDT_1709483925",
                token_pair="ETHUSDT",
                action="BUY",
                confidence=82.1,
                profit_potential=9.7,
                entry_price=3245.80,
                target_price=3560.00,
                stop_loss=3080.00,
                timeframe="2H",
                reason="ETH showing strong accumulation pattern. Whale addresses increasing holdings. EIP-4844 upgrade creating positive sentiment with reduced gas fees.",
                risk_level="LOW",
                market_cap=390000000000,
                volume_24h=15200000000,
                technical_indicators={
                    "rsi": 35.2,
                    "ma_20": 3180.0,
                    "ma_50": 3120.0,
                    "macd_line": 45.2,
                    "volume_ratio": 1.8,
                    "support": 3100.0,
                    "resistance": 3400.0
                },
                ai_analysis="Ethereum fundamentals remain strong with upcoming upgrades. Technical indicators suggest accumulation phase ending with potential breakout.",
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=2)
            ),
            ProfitableSignal(
                id="signal_ADAUSDT_1709483927",
                token_pair="ADAUSDT",
                action="BUY",
                confidence=85.3,
                profit_potential=15.2,
                entry_price=0.4820,
                target_price=0.5550,
                stop_loss=0.4580,
                timeframe="6H",
                reason="Cardano ecosystem growth accelerating. New DeFi protocols launching. Hydra scaling solution showing promising results. Undervalued compared to peers.",
                risk_level="MEDIUM",
                market_cap=17000000000,
                volume_24h=580000000,
                technical_indicators={
                    "rsi": 42.1,
                    "ma_20": 0.475,
                    "ma_50": 0.465,
                    "macd_line": 0.008,
                    "volume_ratio": 1.6,
                    "support": 0.460,
                    "resistance": 0.520
                },
                ai_analysis="ADA showing strong fundamentals with ecosystem development. Technical setup suggests breakout from consolidation pattern imminent.",
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=6)
            )
        ]
        
        # Cache the demo signals
        profitable_signals_service.signals_cache = demo_signals
        profitable_signals_service.last_update = datetime.now()
        
        signal_dicts = [
            profitable_signals_service.signal_to_dict(signal) 
            for signal in demo_signals
        ]
        
        return {
            "success": True,
            "message": "Demo signals generated successfully",
            "signals": signal_dicts,
            "count": len(signal_dicts)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate demo signals: {str(e)}")


@router.post("/signals/refresh")
async def refresh_signals(limit: int = 5):
    """
    Force refresh of profitable signals
    
    - **limit**: Maximum number of signals to generate (default: 5)
    """
    try:
        signals = await profitable_signals_service.generate_profitable_signals(limit)
        
        signal_dicts = [
            profitable_signals_service.signal_to_dict(signal) 
            for signal in signals
        ]
        
        return {
            "success": True,
            "signals": signal_dicts,
            "count": len(signal_dicts),
            "refreshed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh signals: {str(e)}")


@router.post("/execute")
async def execute_signal(request: ExecuteSignalRequest):
    """
    Execute a profitable trading signal
    
    - **signal_id**: ID of the signal to execute
    - **wallet_address**: User's wallet address
    - **amount**: Amount to trade (in base currency)
    - **network**: Blockchain network (ethereum, polygon, arbitrum)
    - **slippage**: Maximum slippage tolerance (default: 0.5%)
    
    Returns transaction details and status
    """
    try:
        result = await signal_execution_service.execute_signal(
            signal_id=request.signal_id,
            wallet_address=request.wallet_address,
            amount=request.amount,
            network=request.network,
            slippage=request.slippage
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Signal execution failed: {str(e)}")


@router.post("/quote")
async def get_swap_quote(request: SwapQuoteRequest):
    """
    Get swap quote for token exchange
    
    - **from_token**: Token to swap from (e.g., USDT, ETH)
    - **to_token**: Token to swap to (e.g., BTC, ETH)
    - **amount**: Amount to swap
    - **network**: Blockchain network
    
    Returns expected output amount and gas costs
    """
    try:
        quote = await signal_execution_service.get_swap_quote(
            from_token=request.from_token,
            to_token=request.to_token,
            amount=request.amount,
            network=request.network
        )
        
        return quote
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quote failed: {str(e)}")


@router.post("/validate-wallet")
async def validate_wallet(request: WalletValidationRequest):
    """
    Validate wallet connection and get balance
    
    - **wallet_address**: Wallet address to validate
    - **network**: Blockchain network to check
    
    Returns wallet status, balance, and network info
    """
    try:
        validation = await signal_execution_service.validate_wallet_connection(
            wallet_address=request.wallet_address,
            network=request.network
        )
        
        return validation
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Wallet validation failed: {str(e)}")


@router.get("/transaction/{tx_hash}")
async def get_transaction_status(tx_hash: str, network: str = "ethereum"):
    """
    Get transaction status
    
    - **tx_hash**: Transaction hash to check
    - **network**: Blockchain network
    
    Returns transaction status and details
    """
    try:
        status = await signal_execution_service.get_execution_status(
            transaction_hash=tx_hash,
            network=network
        )
        
        return status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


@router.get("/health")
async def health_check():
    """Check if profitable signals service is healthy"""
    try:
        # Test signal generation
        signals = await profitable_signals_service.get_cached_signals()
        
        return {
            "success": True,
            "status": "healthy",
            "signals_available": len(signals),
            "last_update": profitable_signals_service.last_update.isoformat() if profitable_signals_service.last_update else None,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }