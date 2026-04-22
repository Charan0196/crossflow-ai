"""
Phase 5: AI Signals API Routes

Endpoints for:
- Trading signal generation
- Portfolio analysis
- Rebalancing recommendations
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal

from src.config.database import get_db
from src.core.trading_schemas import (
    TradingSignalResponse, SignalListResponse, SignalFactor,
    PortfolioMetricsResponse, RebalanceResponse, RebalanceRecommendation
)
from src.ai.signal_generator import signal_generator, SignalType
from src.ai.portfolio_analyzer import portfolio_analyzer

router = APIRouter(prefix="/ai", tags=["AI Signals"])


@router.get("/signals/{token}", response_model=TradingSignalResponse)
async def get_trading_signal(
    token: str,
    timeframe: str = "1h",
    risk_tolerance: float = 0.5
):
    """
    Generate AI trading signal for a token
    
    Args:
        token: Token symbol (e.g., "BTC", "ETH")
        timeframe: Chart timeframe (1m, 5m, 15m, 1h, 4h, 1d)
        risk_tolerance: User's risk tolerance (0-1)
    """
    signal = await signal_generator.generate_signal(
        token=token,
        timeframe=timeframe,
        risk_tolerance=risk_tolerance
    )
    
    if not signal:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to generate signal for {token}"
        )
    
    return TradingSignalResponse(
        token=signal.token,
        signal_type=signal.signal_type.value.replace("_", " "),
        confidence=signal.confidence,
        target_price=str(signal.target_price),
        stop_loss=str(signal.stop_loss),
        take_profit=str(signal.take_profit),
        timeframe=signal.timeframe,
        explanation=signal.explanation,
        factors=[
            SignalFactor(
                name=f.name,
                value=f.value,
                weight=f.weight,
                description=f.description
            )
            for f in signal.factors
        ],
        created_at=signal.created_at.isoformat(),
        expires_at=signal.expires_at.isoformat()
    )


@router.get("/signals", response_model=SignalListResponse)
async def get_multiple_signals(
    tokens: str = "BTC,ETH,SOL,ARB,MATIC",
    timeframe: str = "1h",
    risk_tolerance: float = 0.5
):
    """
    Generate AI trading signals for multiple tokens
    
    Args:
        tokens: Comma-separated token symbols
        timeframe: Chart timeframe
        risk_tolerance: User's risk tolerance (0-1)
    """
    token_list = [t.strip() for t in tokens.split(",")]
    
    signals = await signal_generator.get_signals_for_tokens(
        tokens=token_list,
        timeframe=timeframe,
        risk_tolerance=risk_tolerance
    )
    
    signal_responses = []
    for signal in signals:
        signal_responses.append(TradingSignalResponse(
            token=signal.token,
            signal_type=signal.signal_type.value.replace("_", " "),
            confidence=signal.confidence,
            target_price=str(signal.target_price),
            stop_loss=str(signal.stop_loss),
            take_profit=str(signal.take_profit),
            timeframe=signal.timeframe,
            explanation=signal.explanation,
            factors=[
                SignalFactor(
                    name=f.name,
                    value=f.value,
                    weight=f.weight,
                    description=f.description
                )
                for f in signal.factors
            ],
            created_at=signal.created_at.isoformat(),
            expires_at=signal.expires_at.isoformat()
        ))
    
    # Get accuracy stats
    accuracy = signal_generator.get_signal_accuracy("overall")
    
    return SignalListResponse(
        signals=signal_responses,
        accuracy_30d=accuracy.accuracy_rate,
        total_signals_30d=accuracy.total_signals
    )


@router.post("/portfolio/analyze", response_model=PortfolioMetricsResponse)
async def analyze_portfolio(holdings: List[dict]):
    """
    Analyze a portfolio and return metrics
    
    Args:
        holdings: List of holdings with token, symbol, amount, chain_id
    
    Example:
        [
            {"token": "0x...", "symbol": "ETH", "amount": "1.5", "chain_id": 1},
            {"token": "0x...", "symbol": "USDC", "amount": "1000", "chain_id": 1}
        ]
    """
    metrics = await portfolio_analyzer.analyze_portfolio(holdings)
    
    return PortfolioMetricsResponse(
        total_value_usd=str(metrics.total_value_usd),
        allocations=metrics.allocations,
        chain_distribution=metrics.chain_distribution,
        risk_score=metrics.risk_score,
        sharpe_ratio=metrics.sharpe_ratio,
        max_drawdown=metrics.max_drawdown,
        concentration_risk=metrics.concentration_risk.value.upper(),
        performance_24h=metrics.performance_24h,
        performance_7d=metrics.performance_7d,
        performance_30d=metrics.performance_30d
    )


@router.post("/portfolio/rebalance", response_model=RebalanceResponse)
async def get_rebalance_recommendations(
    holdings: List[dict],
    risk_tolerance: float = 0.5,
    target_allocations: Optional[dict] = None
):
    """
    Get AI-powered rebalancing recommendations
    
    Args:
        holdings: Current portfolio holdings
        risk_tolerance: User's risk tolerance (0-1)
        target_allocations: Optional target allocation percentages
    """
    recommendation = await portfolio_analyzer.get_rebalance_recommendations(
        holdings=holdings,
        target_allocations=target_allocations,
        risk_tolerance=risk_tolerance
    )
    
    return RebalanceResponse(
        recommendations=[
            RebalanceRecommendation(
                action=r.action.upper(),
                token=r.token,
                token_symbol=r.symbol,
                amount=str(r.amount),
                amount_usd=str(r.amount_usd),
                reason=r.reason,
                expected_improvement=r.expected_improvement,
                gas_cost_usd=str(r.gas_cost_usd),
                chain_id=r.chain_id
            )
            for r in recommendation.recommendations
        ],
        current_risk_score=recommendation.current_risk_score,
        projected_risk_score=recommendation.projected_risk_score,
        total_gas_cost_usd=str(recommendation.total_gas_cost_usd)
    )


@router.post("/portfolio/arbitrage")
async def get_arbitrage_suggestions(holdings: List[dict]):
    """
    Get arbitrage suggestions based on portfolio holdings
    """
    suggestions = await portfolio_analyzer.get_arbitrage_suggestions(holdings)
    return {"suggestions": suggestions}


@router.get("/signal-accuracy/{token}")
async def get_signal_accuracy(token: str):
    """
    Get historical signal accuracy for a token
    """
    accuracy = signal_generator.get_signal_accuracy(token)
    
    return {
        "token": token,
        "total_signals": accuracy.total_signals,
        "correct_signals": accuracy.correct_signals,
        "accuracy_rate": accuracy.accuracy_rate,
        "avg_return": accuracy.avg_return
    }
