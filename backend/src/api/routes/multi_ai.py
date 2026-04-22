"""
Multi-AI API Routes
Endpoints for interacting with multiple AI providers
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from src.ai.multi_ai_provider import multi_ai_provider, AIProvider

router = APIRouter(prefix="/api/multi-ai", tags=["Multi-AI"])


class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]
    provider: Optional[str] = None
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1000


class MarketAnalysisRequest(BaseModel):
    token: str
    timeframe: str
    price_data: Dict[str, Any]
    indicators: Dict[str, Any]
    use_ensemble: bool = True


class TradingSignalRequest(BaseModel):
    token: str
    timeframe: str
    indicators: Dict[str, Any]
    provider: Optional[str] = None


@router.get("/providers")
async def get_available_providers():
    """Get list of available AI providers"""
    try:
        providers = multi_ai_provider.get_available_providers()
        
        return {
            "success": True,
            "providers": [
                {
                    "name": p.value,
                    "models": multi_ai_provider.providers[p]["models"],
                    "enabled": multi_ai_provider.providers[p]["enabled"]
                }
                for p in providers
            ],
            "total": len(providers)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat")
async def chat_completion(request: ChatRequest):
    """
    Get chat completion from AI provider
    
    Example:
    ```json
    {
        "messages": [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Analyze BTC price trend"}
        ],
        "provider": "deepseek",
        "temperature": 0.7
    }
    ```
    """
    try:
        # Convert provider string to enum
        provider = None
        if request.provider:
            try:
                provider = AIProvider(request.provider.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid provider: {request.provider}")
        
        response = await multi_ai_provider.chat_completion(
            messages=request.messages,
            provider=provider,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        return {
            "success": True,
            "provider": response.provider.value,
            "model": response.model,
            "content": response.content,
            "tokens_used": response.tokens_used,
            "confidence": response.confidence,
            "metadata": response.metadata
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-market")
async def analyze_market(request: MarketAnalysisRequest):
    """
    Analyze market data using AI
    
    Example:
    ```json
    {
        "token": "BTC",
        "timeframe": "1h",
        "price_data": {
            "current_price": 45000,
            "24h_change": 2.5,
            "volume": 1000000000
        },
        "indicators": {
            "rsi": 65,
            "macd": "bullish",
            "moving_averages": {"ma_50": 44000, "ma_200": 42000}
        },
        "use_ensemble": true
    }
    ```
    """
    try:
        market_data = {
            "token": request.token,
            "timeframe": request.timeframe,
            "price_data": request.price_data,
            "indicators": request.indicators
        }
        
        analysis = await multi_ai_provider.analyze_market(
            market_data=market_data,
            use_ensemble=request.use_ensemble
        )
        
        return {
            "success": True,
            "token": request.token,
            "timeframe": request.timeframe,
            "analysis": analysis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trading-signal")
async def generate_trading_signal(request: TradingSignalRequest):
    """
    Generate trading signal using AI
    
    Example:
    ```json
    {
        "token": "ETH",
        "timeframe": "4h",
        "indicators": {
            "rsi": 45,
            "macd": "bearish",
            "volume_trend": "decreasing",
            "support_levels": [3000, 2900],
            "resistance_levels": [3200, 3300]
        },
        "provider": "gemini"
    }
    ```
    """
    try:
        signal = await multi_ai_provider.generate_trading_signal(
            token=request.token,
            timeframe=request.timeframe,
            indicators=request.indicators
        )
        
        return {
            "success": True,
            "token": request.token,
            "timeframe": request.timeframe,
            "signal": signal
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Check health of AI providers"""
    try:
        providers = multi_ai_provider.get_available_providers()
        
        return {
            "success": True,
            "status": "healthy",
            "providers_available": len(providers),
            "providers": [p.value for p in providers]
        }
    except Exception as e:
        return {
            "success": False,
            "status": "unhealthy",
            "error": str(e)
        }
