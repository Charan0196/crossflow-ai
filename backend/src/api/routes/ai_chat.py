"""
AI Chat API Routes
Provides endpoints for AI-powered trading assistant
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from ...services.ai_chat_service import ai_chat_service

router = APIRouter(prefix="/ai-chat", tags=["AI Chat"])


class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    message: str
    session_id: Optional[str] = "default"
    include_market_data: Optional[bool] = True
    provider: Optional[str] = "groq"
    model: Optional[str] = None


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    success: bool
    response: str
    timestamp: str
    model: str


class ClearHistoryRequest(BaseModel):
    """Request model for clearing chat history"""
    session_id: Optional[str] = "default"


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message to the AI trading assistant
    
    - **message**: The user's message/query
    - **session_id**: Optional session ID for conversation continuity
    - **include_market_data**: Whether to include real-time market data in context
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    result = await ai_chat_service.chat(
        message=request.message,
        session_id=request.session_id,
        include_market_data=request.include_market_data,
        provider=request.provider,
        model=request.model
    )
    
    return ChatResponse(**result)


@router.post("/clear-history")
async def clear_history(request: ClearHistoryRequest):
    """
    Clear conversation history for a session
    
    - **session_id**: The session ID to clear history for
    """
    ai_chat_service.clear_history(request.session_id)
    return {"success": True, "message": f"History cleared for session: {request.session_id}"}


@router.get("/health")
async def health_check():
    """Check if AI chat service is available"""
    return {
        "status": "healthy",
        "service": "ai-chat",
        "timestamp": datetime.utcnow().isoformat()
    }
