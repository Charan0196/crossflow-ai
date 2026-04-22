"""
Real Funds Automated Trading API Routes

API endpoints for real funds automated trading system
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

from src.services.real_funds_trader import real_funds_trader
from src.services.signal_scheduler import signal_scheduler
from src.config.database import get_db

router = APIRouter(prefix="/api/real-trading")


class WalletSetup(BaseModel):
    """Wallet setup model"""
    private_key: Optional[str] = None
    seed_phrase: Optional[str] = None
    account_index: Optional[int] = 0
    network: Optional[str] = "sepolia"  # "sepolia" or "mainnet"


class NetworkSwitch(BaseModel):
    """Network switch model"""
    network: str  # "sepolia" or "mainnet"


class TradingSettings(BaseModel):
    """Real trading settings model"""
    min_confidence: Optional[float] = None
    max_position_size: Optional[float] = None
    max_total_exposure: Optional[float] = None
    stop_loss_pct: Optional[float] = None
    take_profit_pct: Optional[float] = None


class TradingResponse(BaseModel):
    """Standard trading response"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


@router.get("/status", response_model=Dict[str, Any])
async def get_real_trading_status():
    """Get current real trading status"""
    try:
        return {
            "success": True,
            "data": {
                "stats": real_funds_trader.get_stats(),
                "portfolio": real_funds_trader.get_portfolio_summary(),
                "performance": real_funds_trader.get_performance_summary(),
                "open_positions": real_funds_trader.get_open_positions(),
                "recent_trades": real_funds_trader.get_executed_trades(limit=5)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/opportunities", response_model=Dict[str, Any])
async def get_trading_opportunities(limit: int = 10):
    """Get current trading opportunities"""
    try:
        opportunities = real_funds_trader.get_opportunities(limit=limit)
        return {
            "success": True,
            "data": {
                "opportunities": opportunities,
                "total_count": len(opportunities),
                "mode": "DISPLAY_ONLY - No trades will be executed"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/portfolio", response_model=Dict[str, Any])
async def get_real_portfolio():
    """Get real portfolio summary"""
    try:
        return {
            "success": True,
            "data": real_funds_trader.get_portfolio_summary()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=Dict[str, Any])
async def get_real_trading_stats():
    """Get real trading statistics"""
    try:
        return {
            "success": True,
            "data": real_funds_trader.get_stats()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/setup-wallet", response_model=TradingResponse)
async def setup_wallet(wallet_setup: WalletSetup):
    """Setup wallet for automated trading using private key or seed phrase"""
    try:
        # Validate input
        if not wallet_setup.private_key and not wallet_setup.seed_phrase:
            raise HTTPException(status_code=400, detail="Either private_key or seed_phrase must be provided")
        
        if wallet_setup.private_key and wallet_setup.seed_phrase:
            raise HTTPException(status_code=400, detail="Provide either private_key OR seed_phrase, not both")
        
        # Switch network first
        if wallet_setup.network:
            real_funds_trader.switch_network(wallet_setup.network)
        
        # Setup wallet
        success = await real_funds_trader.setup_wallet(
            private_key=wallet_setup.private_key,
            seed_phrase=wallet_setup.seed_phrase,
            account_index=wallet_setup.account_index or 0
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to setup wallet")
        
        wallet_type = "seed phrase" if wallet_setup.seed_phrase else "private key"
        account_info = f" (account {wallet_setup.account_index})" if wallet_setup.seed_phrase else ""
        
        return TradingResponse(
            success=True,
            message=f"Wallet setup successfully from {wallet_type}{account_info} on {real_funds_trader.current_network}",
            data={
                "wallet_address": real_funds_trader.wallet_address,
                "network": real_funds_trader.current_network,
                "chain_id": real_funds_trader.chain_id,
                "mode": real_funds_trader.mode.value,
                "wallet_type": wallet_type,
                "account_index": wallet_setup.account_index if wallet_setup.seed_phrase else None
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/switch-network", response_model=TradingResponse)
async def switch_network(network_switch: NetworkSwitch):
    """Switch between testnet and mainnet"""
    try:
        if network_switch.network not in ["sepolia", "mainnet"]:
            raise HTTPException(status_code=400, detail="Invalid network. Use 'sepolia' or 'mainnet'")
        
        real_funds_trader.switch_network(network_switch.network)
        
        return TradingResponse(
            success=True,
            message=f"Switched to {network_switch.network} network",
            data={
                "network": real_funds_trader.current_network,
                "chain_id": real_funds_trader.chain_id,
                "mode": real_funds_trader.mode.value
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enable", response_model=TradingResponse)
async def enable_trading():
    """Enable automated trading"""
    try:
        real_funds_trader.enable_trading()
        return TradingResponse(
            success=True,
            message=f"Automated trading enabled on {real_funds_trader.current_network}",
            data={
                "is_enabled": real_funds_trader.is_enabled,
                "mode": real_funds_trader.mode.value,
                "network": real_funds_trader.current_network
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/disable", response_model=TradingResponse)
async def disable_trading():
    """Disable automated trading"""
    try:
        real_funds_trader.disable_trading()
        return TradingResponse(
            success=True,
            message="Automated trading disabled",
            data={"is_enabled": real_funds_trader.is_enabled}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/settings", response_model=TradingResponse)
async def update_settings(settings: TradingSettings):
    """Update real trading settings"""
    try:
        settings_dict = settings.dict(exclude_none=True)
        
        # Validate settings
        if "min_confidence" in settings_dict:
            if not 50 <= settings_dict["min_confidence"] <= 100:
                raise HTTPException(status_code=400, detail="min_confidence must be between 50 and 100")
        
        if "max_position_size" in settings_dict:
            if not 0 < settings_dict["max_position_size"] <= 0.1:
                raise HTTPException(status_code=400, detail="max_position_size must be between 0 and 0.1 (10%)")
        
        if "max_total_exposure" in settings_dict:
            if not 0 < settings_dict["max_total_exposure"] <= 0.5:
                raise HTTPException(status_code=400, detail="max_total_exposure must be between 0 and 0.5 (50%)")
        
        if "stop_loss_pct" in settings_dict:
            if not 0.005 <= settings_dict["stop_loss_pct"] <= 0.1:
                raise HTTPException(status_code=400, detail="stop_loss_pct must be between 0.005 and 0.1 (0.5% - 10%)")
        
        if "take_profit_pct" in settings_dict:
            if not 0.01 <= settings_dict["take_profit_pct"] <= 0.2:
                raise HTTPException(status_code=400, detail="take_profit_pct must be between 0.01 and 0.2 (1% - 20%)")
        
        real_funds_trader.update_settings(settings_dict)
        
        return TradingResponse(
            success=True,
            message="Real trading settings updated successfully",
            data=real_funds_trader.get_stats()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trades", response_model=Dict[str, Any])
async def get_executed_trades(limit: int = 20):
    """Get executed trades history"""
    try:
        trades = real_funds_trader.get_executed_trades(limit=limit)
        return {
            "success": True,
            "data": {
                "trades": trades,
                "total_count": len(trades)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/positions", response_model=Dict[str, Any])
async def get_open_positions():
    """Get current open positions"""
    try:
        positions = real_funds_trader.get_open_positions()
        return {
            "success": True,
            "data": {
                "positions": positions,
                "total_count": len(positions)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance", response_model=Dict[str, Any])
async def get_performance():
    """Get trading performance summary"""
    try:
        performance = real_funds_trader.get_performance_summary()
        return {
            "success": True,
            "data": performance
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/disconnect", response_model=TradingResponse)
async def disconnect_wallet():
    """Disconnect wallet and reset trading state"""
    try:
        # Disable trading first
        real_funds_trader.disable_trading()
        
        # Clear wallet connection completely
        real_funds_trader.wallet_address = None
        real_funds_trader.account = None
        real_funds_trader.w3 = None
        
        # Reset portfolio to default state
        from src.services.real_funds_trader import RealPortfolio
        real_funds_trader.portfolio = RealPortfolio()
        
        # Clear open positions and opportunities
        real_funds_trader.open_positions.clear()
        real_funds_trader.opportunities.clear()
        
        # Reset stats (keep executed trades for history)
        real_funds_trader.stats.update({
            "total_trades": len(real_funds_trader.executed_trades),
            "winning_trades": len([t for t in real_funds_trader.executed_trades if t.profit_loss_usd and t.profit_loss_usd > 0]),
            "losing_trades": len([t for t in real_funds_trader.executed_trades if t.profit_loss_usd and t.profit_loss_usd <= 0]),
        })
        
        return TradingResponse(
            success=True,
            message="Wallet disconnected successfully - you can now connect a different wallet",
            data={
                "is_enabled": real_funds_trader.is_enabled,
                "wallet_connected": False,
                "wallet_address": None
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/emergency-stop", response_model=TradingResponse)
async def emergency_stop():
    """Emergency stop - close all positions and disable trading"""
    try:
        await real_funds_trader.emergency_stop()
        return TradingResponse(
            success=True,
            message="Emergency stop executed - all positions closed and trading disabled",
            data={
                "is_enabled": real_funds_trader.is_enabled,
                "open_positions": len(real_funds_trader.open_positions)
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
async def get_opportunity_details(opportunity_id: str):
    """Get detailed information about a specific opportunity"""
    try:
        opportunities = real_funds_trader.get_opportunities(limit=100)
        opportunity = next((opp for opp in opportunities if opp["id"] == opportunity_id), None)
        
        if not opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        
        return {
            "success": True,
            "data": {
                "opportunity": opportunity,
                "warning": "DISPLAY ONLY - This trade will NOT be executed automatically",
                "manual_execution": {
                    "dex": "Uniswap V3 on Sepolia",
                    "token_address": "Check token contract on Sepolia",
                    "estimated_gas": opportunity["gas_estimate"],
                    "slippage_tolerance": "0.5%"
                }
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market-analysis", response_model=Dict[str, Any])
async def get_market_analysis():
    """Get current market analysis for real trading"""
    try:
        opportunities = real_funds_trader.get_opportunities(limit=20)
        
        # Analyze opportunities
        if not opportunities:
            return {
                "success": True,
                "data": {
                    "market_sentiment": "NEUTRAL",
                    "total_opportunities": 0,
                    "avg_confidence": 0,
                    "recommended_action": "Wait for higher confidence signals"
                }
            }
        
        # Calculate market metrics
        total_opps = len(opportunities)
        avg_confidence = sum(opp["confidence"] for opp in opportunities) / total_opps
        buy_signals = sum(1 for opp in opportunities if opp["signal_type"] in ["buy", "strong_buy"])
        sell_signals = sum(1 for opp in opportunities if opp["signal_type"] in ["sell", "strong_sell"])
        
        # Determine market sentiment
        if buy_signals > sell_signals * 1.5:
            sentiment = "BULLISH"
        elif sell_signals > buy_signals * 1.5:
            sentiment = "BEARISH"
        else:
            sentiment = "NEUTRAL"
        
        # Calculate potential profit
        total_potential = sum(
            float(opp["position_size_usd"]) * 0.04  # Assume 4% profit target
            for opp in opportunities
        )
        
        return {
            "success": True,
            "data": {
                "market_sentiment": sentiment,
                "total_opportunities": total_opps,
                "avg_confidence": round(avg_confidence, 1),
                "buy_signals": buy_signals,
                "sell_signals": sell_signals,
                "total_potential_profit": f"${total_potential:.2f}",
                "recommended_action": "Monitor opportunities - DISPLAY ONLY MODE",
                "top_opportunities": opportunities[:3]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scan", response_model=TradingResponse)
async def manual_scan():
    """Manually trigger opportunity scan"""
    try:
        await real_funds_trader.scan_opportunities()
        opportunities = real_funds_trader.get_opportunities(limit=10)
        
        return TradingResponse(
            success=True,
            message=f"Scan completed - found {len(opportunities)} opportunities",
            data={
                "opportunities_count": len(opportunities),
                "opportunities": opportunities
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test", response_model=Dict[str, Any])
async def test_real_funds():
    """Test real funds trader functionality"""
    try:
        print("🧪 [REAL FUNDS] Test endpoint called")
        
        # Test basic functionality
        stats = real_funds_trader.get_stats()
        print(f"🧪 [REAL FUNDS] Stats: {stats}")
        
        # Test signal fetching
        signals = signal_scheduler.get_latest_signals(limit=3)
        print(f"🧪 [REAL FUNDS] Signals: {len(signals)} found")
        
        return {
            "success": True,
            "data": {
                "message": "Real funds trader test completed",
                "stats": stats,
                "signals_count": len(signals),
                "signals": signals[:2] if signals else []
            }
        }
    except Exception as e:
        print(f"🧪 [REAL FUNDS] Test error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Health check for real funds trading system"""
    try:
        stats = real_funds_trader.get_stats()
        return {
            "success": True,
            "data": {
                "status": "healthy",
                "mode": stats["mode"],
                "network": stats["network"],
                "is_enabled": stats["is_enabled"],
                "wallet_connected": bool(stats["wallet_address"]),
                "open_positions": stats["open_positions"],
                "total_trades": stats["total_trades"],
                "chain_id": stats["chain_id"],
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))