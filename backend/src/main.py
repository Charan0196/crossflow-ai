"""
Main FastAPI application entry point
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.api.routes import auth, trading, portfolio, admin, intent_validation, solver_network, intents
from src.api.routes import ai_chat, autonomous_trading, testnet_faucet, database, wallet, ai_trading, multi_ai, signal_scheduler, auto_trader, real_funds_trader, profitable_signals, position_monitor
from src.api.websocket import routes as websocket_routes
from src.config.database import init_db
from src.config.settings import settings
from src.services.price_feed_service import price_feed_service
from src.services.signal_scheduler import signal_scheduler as sig_scheduler
from src.services.auto_trader import auto_trader as auto_trading_service
from src.services.real_funds_trader import real_funds_trader as real_funds_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    
    # Start price feed service
    try:
        await price_feed_service.start()
    except Exception as e:
        print(f"Warning: Could not start price feed service: {e}")
    
    # Start signal scheduler
    try:
        await sig_scheduler.start()
        print("✅ Signal scheduler started - generating signals every 5 minutes")
    except Exception as e:
        print(f"Warning: Could not start signal scheduler: {e}")
    
    # Start auto trader
    try:
        import asyncio
        asyncio.create_task(auto_trading_service.start_auto_trading())
        print("✅ Auto trader started - trading with mock USD based on signals")
    except Exception as e:
        print(f"Warning: Could not start auto trader: {e}")
    
    # Start real funds automated trading
    try:
        import asyncio
        asyncio.create_task(real_funds_service.start_monitoring())
        print("✅ Real funds automated trading started - Ready for testnet/mainnet trading")
    except Exception as e:
        print(f"Warning: Could not start real funds trading: {e}")
    
    yield
    
    # Shutdown
    try:
        await price_feed_service.stop()
    except Exception as e:
        print(f"Warning: Error stopping price feed service: {e}")
    
    try:
        await sig_scheduler.stop()
    except Exception as e:
        print(f"Warning: Error stopping signal scheduler: {e}")


app = FastAPI(
    title="CrossFlow AI Trading Platform",
    description="Cross-chain AI-powered DeFi trading platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware - must be added before routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(trading.router, prefix="/api/trading", tags=["trading"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["portfolio"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(intent_validation.router, prefix="/api", tags=["intent-validation"])
app.include_router(solver_network.router, prefix="/api", tags=["solver-network"])
app.include_router(intents.router, prefix="/api", tags=["intents"])
app.include_router(ai_chat.router, prefix="/api", tags=["ai-chat"])
app.include_router(autonomous_trading.router, prefix="/api", tags=["autonomous-trading"])
app.include_router(testnet_faucet.router, prefix="/api", tags=["testnet-faucet"])
app.include_router(database.router, prefix="/api", tags=["database"])
app.include_router(wallet.router, prefix="/api", tags=["wallet"])
app.include_router(ai_trading.router, prefix="/api", tags=["ai-trading"])
app.include_router(multi_ai.router, tags=["multi-ai"])
app.include_router(signal_scheduler.router, tags=["signal-scheduler"])
app.include_router(auto_trader.router, tags=["auto-trader"])
app.include_router(real_funds_trader.router, tags=["real-funds-trader"])
app.include_router(profitable_signals.router, prefix="/api", tags=["profitable-signals"])
app.include_router(position_monitor.router, prefix="/api", tags=["position-monitor"])
app.include_router(websocket_routes.router, prefix="/api", tags=["websocket"])


@app.get("/")
async def root():
    return {"message": "CrossFlow AI Trading Platform API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )