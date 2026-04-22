"""
Phase 5: Charts API Routes

Endpoints for:
- Chart data (OHLCV)
- Technical indicators
- Order book and recent trades
- Chart configuration persistence
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal

from src.config.database import get_db
from src.core.trading_schemas import (
    ChartDataRequest, ChartDataResponse, OHLCV,
    ChartConfigRequest, ChartConfigResponse
)
from src.services.advanced_price_oracle import price_oracle
from src.ai.signal_generator import TechnicalIndicators
from src.models.trading import ChartConfiguration
from src.config.phase5_config import CHART_TIMEFRAMES, INDICATOR_PARAMS

router = APIRouter(prefix="/charts", tags=["Charts"])


@router.post("/data", response_model=ChartDataResponse)
async def get_chart_data(request: ChartDataRequest):
    """
    Get OHLCV chart data with optional technical indicators
    
    Args:
        symbol: Trading pair (e.g., "BTCUSDT")
        timeframe: Chart timeframe (1m, 5m, 15m, 1h, 4h, 1d, 1w)
        limit: Number of candles (max 1000)
        indicators: List of indicators to calculate (MA, EMA, RSI, MACD, BB)
    """
    # Validate timeframe
    if request.timeframe not in CHART_TIMEFRAMES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid timeframe. Supported: {CHART_TIMEFRAMES}"
        )
    
    # Get historical data
    candles = await price_oracle.get_historical_prices(
        symbol=request.symbol,
        interval=request.timeframe,
        limit=request.limit
    )
    
    if not candles:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No data found for {request.symbol}"
        )
    
    # Convert to OHLCV format
    ohlcv_data = [
        OHLCV(
            timestamp=c["timestamp"],
            open=c["open"],
            high=c["high"],
            low=c["low"],
            close=c["close"],
            volume=c["volume"]
        )
        for c in candles
    ]
    
    # Calculate indicators
    indicators_data = {}
    prices = [c["close"] for c in candles]
    
    for indicator in request.indicators:
        indicator = indicator.upper()
        
        if indicator == "MA" or indicator == "SMA":
            for period in INDICATOR_PARAMS["MA"]["periods"]:
                ma = TechnicalIndicators.calculate_sma(prices, period)
                indicators_data[f"MA_{period}"] = ma
        
        elif indicator == "EMA":
            for period in INDICATOR_PARAMS["EMA"]["periods"]:
                ema = TechnicalIndicators.calculate_ema(prices, period)
                indicators_data[f"EMA_{period}"] = ema
        
        elif indicator == "RSI":
            rsi = TechnicalIndicators.calculate_rsi(
                prices, INDICATOR_PARAMS["RSI"]["period"]
            )
            indicators_data["RSI"] = rsi
        
        elif indicator == "MACD":
            macd, signal, histogram = TechnicalIndicators.calculate_macd(
                prices,
                INDICATOR_PARAMS["MACD"]["fast"],
                INDICATOR_PARAMS["MACD"]["slow"],
                INDICATOR_PARAMS["MACD"]["signal"]
            )
            indicators_data["MACD"] = macd
            indicators_data["MACD_Signal"] = signal
            indicators_data["MACD_Histogram"] = histogram
        
        elif indicator == "BB" or indicator == "BOLLINGER":
            upper, middle, lower = TechnicalIndicators.calculate_bollinger_bands(
                prices,
                INDICATOR_PARAMS["BB"]["period"],
                INDICATOR_PARAMS["BB"]["std_dev"]
            )
            indicators_data["BB_Upper"] = upper
            indicators_data["BB_Middle"] = middle
            indicators_data["BB_Lower"] = lower
    
    return ChartDataResponse(
        symbol=request.symbol,
        timeframe=request.timeframe,
        candles=ohlcv_data,
        indicators=indicators_data
    )


@router.get("/orderbook/{symbol}")
async def get_order_book(symbol: str, limit: int = 20):
    """
    Get order book depth for a symbol
    """
    order_book = await price_oracle.get_order_book(symbol, limit)
    
    if not order_book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order book not found for {symbol}"
        )
    
    return order_book


@router.get("/trades/{symbol}")
async def get_recent_trades(symbol: str, limit: int = 50):
    """
    Get recent trades for a symbol
    """
    trades = await price_oracle.get_recent_trades(symbol, limit)
    
    return {
        "symbol": symbol,
        "trades": trades
    }


@router.get("/timeframes")
async def get_supported_timeframes():
    """
    Get list of supported chart timeframes
    """
    return {"timeframes": CHART_TIMEFRAMES}


@router.get("/indicators")
async def get_supported_indicators():
    """
    Get list of supported technical indicators with parameters
    """
    return {"indicators": INDICATOR_PARAMS}


@router.post("/config", response_model=ChartConfigResponse)
async def save_chart_config(
    request: ChartConfigRequest,
    user_id: str,  # Would come from auth
    db: Session = Depends(get_db)
):
    """
    Save a chart configuration
    """
    config = ChartConfiguration(
        user_id=user_id,
        name=request.name,
        symbol=request.symbol,
        timeframe=request.timeframe,
        indicators=request.indicators,
        drawings=request.drawings,
        layout=request.layout
    )
    
    db.add(config)
    db.commit()
    db.refresh(config)
    
    return ChartConfigResponse(
        id=config.id,
        name=config.name,
        symbol=config.symbol,
        timeframe=config.timeframe,
        indicators=config.indicators,
        drawings=config.drawings,
        layout=config.layout,
        created_at=config.created_at.isoformat(),
        updated_at=config.updated_at.isoformat()
    )


@router.get("/config/{config_id}", response_model=ChartConfigResponse)
async def get_chart_config(
    config_id: str,
    user_id: str,  # Would come from auth
    db: Session = Depends(get_db)
):
    """
    Get a saved chart configuration
    """
    config = db.query(ChartConfiguration).filter(
        ChartConfiguration.id == config_id,
        ChartConfiguration.user_id == user_id
    ).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chart configuration not found"
        )
    
    return ChartConfigResponse(
        id=config.id,
        name=config.name,
        symbol=config.symbol,
        timeframe=config.timeframe,
        indicators=config.indicators,
        drawings=config.drawings,
        layout=config.layout,
        created_at=config.created_at.isoformat(),
        updated_at=config.updated_at.isoformat()
    )


@router.get("/configs", response_model=List[ChartConfigResponse])
async def list_chart_configs(
    user_id: str,  # Would come from auth
    db: Session = Depends(get_db)
):
    """
    List all saved chart configurations for a user
    """
    configs = db.query(ChartConfiguration).filter(
        ChartConfiguration.user_id == user_id
    ).all()
    
    return [
        ChartConfigResponse(
            id=c.id,
            name=c.name,
            symbol=c.symbol,
            timeframe=c.timeframe,
            indicators=c.indicators,
            drawings=c.drawings,
            layout=c.layout,
            created_at=c.created_at.isoformat(),
            updated_at=c.updated_at.isoformat()
        )
        for c in configs
    ]


@router.delete("/config/{config_id}")
async def delete_chart_config(
    config_id: str,
    user_id: str,  # Would come from auth
    db: Session = Depends(get_db)
):
    """
    Delete a saved chart configuration
    """
    config = db.query(ChartConfiguration).filter(
        ChartConfiguration.id == config_id,
        ChartConfiguration.user_id == user_id
    ).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chart configuration not found"
        )
    
    db.delete(config)
    db.commit()
    
    return {"message": "Configuration deleted"}
