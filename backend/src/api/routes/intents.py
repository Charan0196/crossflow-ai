"""
Intent Management API Routes
Provides REST API endpoints for creating, monitoring, and managing intents
Requirements: 10.1, 10.2, 10.4 - REST API endpoints with authentication and rate limiting
"""
import asyncio
import time
import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, validator
from datetime import datetime, timedelta
import uuid

from src.config.database import get_db
from src.api.routes.auth import get_current_user
from src.models.user import User
from src.services.system_logging_service import system_logging_service
from src.services.analytics_reporting_service import analytics_reporting_service
from src.services.error_handling_service import error_handling_service, ErrorContext


logger = logging.getLogger(__name__)


# Rate limiting storage (in production, use Redis)
rate_limit_storage = {}
RATE_LIMIT_REQUESTS = 100  # requests per minute
RATE_LIMIT_WINDOW = 60  # seconds


def check_rate_limit(user_id: str) -> bool:
    """Check if user has exceeded rate limit"""
    current_time = time.time()
    user_requests = rate_limit_storage.get(user_id, [])
    
    # Remove old requests outside the window
    user_requests = [req_time for req_time in user_requests if current_time - req_time < RATE_LIMIT_WINDOW]
    
    # Check if limit exceeded
    if len(user_requests) >= RATE_LIMIT_REQUESTS:
        return False
    
    # Add current request
    user_requests.append(current_time)
    rate_limit_storage[user_id] = user_requests
    return True


# Pydantic models for request/response
class IntentCreateRequest(BaseModel):
    """Request model for creating an intent"""
    source_chain: int = Field(..., description="Source blockchain chain ID")
    destination_chain: int = Field(..., description="Destination blockchain chain ID")
    input_token: str = Field(..., description="Input token address")
    output_token: str = Field(..., description="Output token address")
    input_amount: str = Field(..., description="Input amount in token units")
    minimum_output_amount: str = Field(..., description="Minimum acceptable output amount")
    deadline: Optional[int] = Field(None, description="Intent deadline timestamp (default: 30 minutes)")
    recipient: Optional[str] = Field(None, description="Recipient address (default: sender)")
    max_gas_price: Optional[str] = Field(None, description="Maximum acceptable gas price")
    slippage_tolerance: Optional[float] = Field(0.5, description="Slippage tolerance percentage")
    
    @validator('source_chain', 'destination_chain')
    def validate_chain_ids(cls, v):
        supported_chains = [1, 137, 42161, 10, 56, 8453]  # Ethereum, Polygon, Arbitrum, Optimism, BSC, Base
        if v not in supported_chains:
            raise ValueError(f"Chain ID {v} not supported")
        return v
    
    @validator('slippage_tolerance')
    def validate_slippage(cls, v):
        if v < 0 or v > 50:
            raise ValueError("Slippage tolerance must be between 0 and 50 percent")
        return v


class IntentResponse(BaseModel):
    """Response model for intent operations"""
    intent_id: str
    status: str
    user_address: str
    source_chain: int
    destination_chain: int
    input_token: str
    output_token: str
    input_amount: str
    minimum_output_amount: str
    deadline: int
    created_at: datetime
    updated_at: datetime
    estimated_execution_time: Optional[int] = None
    estimated_gas_cost: Optional[str] = None
    solver_address: Optional[str] = None
    transaction_hash: Optional[str] = None
    error_message: Optional[str] = None


class IntentStatusResponse(BaseModel):
    """Response model for intent status"""
    intent_id: str
    status: str
    progress: Dict[str, Any]
    execution_details: Optional[Dict[str, Any]] = None
    error_details: Optional[Dict[str, Any]] = None
    estimated_completion: Optional[datetime] = None


class IntentListResponse(BaseModel):
    """Response model for intent list"""
    intents: List[IntentResponse]
    total_count: int
    page: int
    page_size: int
    has_next: bool


router = APIRouter()
security = HTTPBearer()


def _get_primary_wallet_address(user: User) -> str:
    """Extract primary wallet address from user's wallet_addresses JSON"""
    import json
    try:
        if user.wallet_addresses:
            addresses = json.loads(user.wallet_addresses)
            # Return the first available address, preferring Ethereum mainnet (chain 1)
            if "1" in addresses:
                return addresses["1"]
            elif addresses:
                return list(addresses.values())[0]
        # Fallback to a default address format
        return f"0x{user.id:040x}"  # Generate address from user ID
    except (json.JSONDecodeError, AttributeError):
        return f"0x{user.id:040x}"  # Generate address from user ID


async def rate_limit_dependency(request: Request, current_user: User = Depends(get_current_user)):
    """Rate limiting dependency"""
    if not check_rate_limit(str(current_user.id)):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Maximum 100 requests per minute."
        )
    return current_user


@router.post("/intents", response_model=IntentResponse)
async def create_intent(
    intent_request: IntentCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(rate_limit_dependency),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new trading intent
    Requirements: 10.1 - REST API endpoints for creating intents
    """
    try:
        # Generate intent ID
        intent_id = f"intent_{uuid.uuid4().hex[:16]}"
        
        # Set default deadline (30 minutes from now)
        if not intent_request.deadline:
            intent_request.deadline = int(time.time() + 1800)  # 30 minutes
        
        # Set default recipient
        recipient = intent_request.recipient or self._get_primary_wallet_address(current_user)
        
        # Create intent context for logging
        context = ErrorContext(
            user_address=self._get_primary_wallet_address(current_user),
            intent_id=intent_id,
            chain_id=intent_request.source_chain,
            operation_type="intent_creation"
        )
        
        # Log intent creation
        system_logging_service.log_intent_created(
            intent_id=intent_id,
            user_address=self._get_primary_wallet_address(current_user),
            source_chain=intent_request.source_chain,
            destination_chain=intent_request.destination_chain,
            input_token=intent_request.input_token,
            output_token=intent_request.output_token,
            input_amount=intent_request.input_amount,
            minimum_output_amount=intent_request.minimum_output_amount,
            details={
                "deadline": intent_request.deadline,
                "recipient": recipient,
                "max_gas_price": intent_request.max_gas_price,
                "slippage_tolerance": intent_request.slippage_tolerance
            }
        )
        
        # TODO: Integrate with actual intent engine for validation and processing
        # For now, simulate intent creation
        
        # Create response
        intent_response = IntentResponse(
            intent_id=intent_id,
            status="created",
            user_address=self._get_primary_wallet_address(current_user),
            source_chain=intent_request.source_chain,
            destination_chain=intent_request.destination_chain,
            input_token=intent_request.input_token,
            output_token=intent_request.output_token,
            input_amount=intent_request.input_amount,
            minimum_output_amount=intent_request.minimum_output_amount,
            deadline=intent_request.deadline,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            estimated_execution_time=300,  # 5 minutes estimate
            estimated_gas_cost="0.01"  # Estimated gas cost in ETH
        )
        
        # Schedule background processing
        background_tasks.add_task(process_intent_async, intent_id, intent_request, current_user)
        
        # Send WebSocket update for intent creation
        try:
            from src.api.websocket.connection_manager import connection_manager
            await connection_manager.send_intent_status_update(
                intent_id=intent_id,
                user_id=str(current_user.id),
                status_data={
                    "status": "created",
                    "intent_id": intent_id,
                    "estimated_execution_time": 300,
                    "estimated_gas_cost": "0.01",
                    "created_at": datetime.now().isoformat()
                }
            )
        except Exception as ws_error:
            # Don't fail the API call if WebSocket update fails
            logger.warning(f"WebSocket update failed: {ws_error}")
        
        return intent_response
        
    except Exception as e:
        # Handle error
        context = ErrorContext(
            user_address=_get_primary_wallet_address(current_user),
            intent_id=intent_id if 'intent_id' in locals() else None,
            operation_type="intent_creation"
        )
        
        error_entry = await error_handling_service.handle_error(
            error=e,
            context=context,
            error_code="INTENT_CREATION_FAILED"
        )
        
        raise HTTPException(
            status_code=400,
            detail=f"Failed to create intent: {str(e)}"
        )


@router.get("/intents/{intent_id}", response_model=IntentResponse)
async def get_intent(
    intent_id: str,
    current_user: User = Depends(rate_limit_dependency),
    db: AsyncSession = Depends(get_db)
):
    """
    Get intent details by ID
    Requirements: 10.1 - REST API endpoints for monitoring intents
    """
    try:
        # TODO: Implement actual intent retrieval from database
        # For now, simulate intent retrieval
        
        # Check if intent exists in logs
        intent_logs = [log for log in system_logging_service.intent_logs if log.intent_id == intent_id]
        if not intent_logs:
            raise HTTPException(status_code=404, detail="Intent not found")
        
        # Get the creation log
        creation_log = next((log for log in intent_logs if log.event_type.value == "intent_created"), None)
        if not creation_log:
            raise HTTPException(status_code=404, detail="Intent creation record not found")
        
        # Check if user owns this intent
        if creation_log.user_address != _get_primary_wallet_address(current_user):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Determine current status
        status = "created"
        solver_address = None
        transaction_hash = None
        error_message = None
        
        # Check for completion or failure
        completion_logs = [log for log in intent_logs if log.event_type.value == "execution_completed"]
        failure_logs = [log for log in intent_logs if log.event_type.value == "execution_failed"]
        
        if completion_logs:
            status = "completed"
            solver_address = completion_logs[-1].solver_address
            transaction_hash = completion_logs[-1].details.get("transaction_hash")
        elif failure_logs:
            status = "failed"
            error_message = failure_logs[-1].error_message
        
        return IntentResponse(
            intent_id=intent_id,
            status=status,
            user_address=creation_log.user_address,
            source_chain=creation_log.source_chain,
            destination_chain=creation_log.destination_chain,
            input_token=creation_log.input_token,
            output_token=creation_log.output_token,
            input_amount=creation_log.input_amount,
            minimum_output_amount=creation_log.minimum_output_amount,
            deadline=int(creation_log.details.get("deadline", time.time() + 1800)),
            created_at=datetime.fromtimestamp(creation_log.timestamp),
            updated_at=datetime.fromtimestamp(max(log.timestamp for log in intent_logs)),
            solver_address=solver_address,
            transaction_hash=transaction_hash,
            error_message=error_message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        context = ErrorContext(
            user_address=_get_primary_wallet_address(current_user),
            intent_id=intent_id,
            operation_type="intent_retrieval"
        )
        
        await error_handling_service.handle_error(
            error=e,
            context=context,
            error_code="INTENT_RETRIEVAL_FAILED"
        )
        
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve intent"
        )


@router.get("/intents/{intent_id}/status", response_model=IntentStatusResponse)
async def get_intent_status(
    intent_id: str,
    current_user: User = Depends(rate_limit_dependency),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed intent status and progress
    Requirements: 10.1 - REST API endpoints for monitoring intents
    """
    try:
        # Get intent logs
        intent_logs = [log for log in system_logging_service.intent_logs if log.intent_id == intent_id]
        if not intent_logs:
            raise HTTPException(status_code=404, detail="Intent not found")
        
        # Check ownership
        creation_log = next((log for log in intent_logs if log.event_type.value == "intent_created"), None)
        if not creation_log or creation_log.user_address != _get_primary_wallet_address(current_user):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Build progress information
        progress = {
            "created": True,
            "validated": any(log.event_type.value == "intent_validated" for log in intent_logs),
            "submitted": any(log.event_type.value == "intent_submitted" for log in intent_logs),
            "solver_selected": any(log.event_type.value == "solver_selected" for log in intent_logs),
            "funds_locked": any(log.event_type.value == "funds_locked" for log in intent_logs),
            "executing": any(log.event_type.value == "execution_started" for log in intent_logs),
            "completed": any(log.event_type.value == "execution_completed" for log in intent_logs),
            "failed": any(log.event_type.value == "execution_failed" for log in intent_logs)
        }
        
        # Determine status
        if progress["failed"]:
            status = "failed"
        elif progress["completed"]:
            status = "completed"
        elif progress["executing"]:
            status = "executing"
        elif progress["solver_selected"]:
            status = "solver_selected"
        elif progress["submitted"]:
            status = "submitted"
        elif progress["validated"]:
            status = "validated"
        else:
            status = "created"
        
        # Get execution details
        execution_details = None
        if progress["completed"]:
            completion_log = next((log for log in intent_logs if log.event_type.value == "execution_completed"), None)
            if completion_log:
                execution_details = {
                    "execution_time_ms": completion_log.execution_time_ms,
                    "gas_used": completion_log.gas_used,
                    "fees_paid": completion_log.fees_paid,
                    "solver_address": completion_log.solver_address,
                    "output_amount": completion_log.details.get("output_amount")
                }
        
        # Get error details
        error_details = None
        if progress["failed"]:
            failure_log = next((log for log in intent_logs if log.event_type.value == "execution_failed"), None)
            if failure_log:
                error_details = {
                    "error_message": failure_log.error_message,
                    "execution_time_ms": failure_log.execution_time_ms,
                    "solver_address": failure_log.solver_address
                }
        
        # Estimate completion time
        estimated_completion = None
        if status in ["created", "validated", "submitted", "solver_selected", "executing"]:
            # Estimate based on average execution time (5 minutes default)
            estimated_completion = datetime.fromtimestamp(creation_log.timestamp + 300)
        
        return IntentStatusResponse(
            intent_id=intent_id,
            status=status,
            progress=progress,
            execution_details=execution_details,
            error_details=error_details,
            estimated_completion=estimated_completion
        )
        
    except HTTPException:
        raise
    except Exception as e:
        context = ErrorContext(
            user_address=_get_primary_wallet_address(current_user),
            intent_id=intent_id,
            operation_type="intent_status_check"
        )
        
        await error_handling_service.handle_error(
            error=e,
            context=context,
            error_code="INTENT_STATUS_FAILED"
        )
        
        raise HTTPException(
            status_code=500,
            detail="Failed to get intent status"
        )


@router.get("/intents", response_model=IntentListResponse)
async def list_user_intents(
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    source_chain: Optional[int] = None,
    destination_chain: Optional[int] = None,
    current_user: User = Depends(rate_limit_dependency),
    db: AsyncSession = Depends(get_db)
):
    """
    List user's intents with filtering and pagination
    Requirements: 10.1 - REST API endpoints for managing intents
    """
    try:
        # Validate pagination parameters
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 20
        
        # Get user's intent creation logs
        user_intent_logs = [
            log for log in system_logging_service.intent_logs 
            if (log.event_type.value == "intent_created" and 
                log.user_address == _get_primary_wallet_address(current_user))
        ]
        
        # Apply filters
        if status:
            # Filter by status would require checking all logs for each intent
            # For simplicity, we'll implement basic filtering
            pass
        
        if source_chain:
            user_intent_logs = [log for log in user_intent_logs if log.source_chain == source_chain]
        
        if destination_chain:
            user_intent_logs = [log for log in user_intent_logs if log.destination_chain == destination_chain]
        
        # Sort by timestamp (newest first)
        user_intent_logs.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Calculate pagination
        total_count = len(user_intent_logs)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_logs = user_intent_logs[start_idx:end_idx]
        
        # Build intent responses
        intents = []
        for log in paginated_logs:
            # Get all logs for this intent to determine status
            intent_logs = [l for l in system_logging_service.intent_logs if l.intent_id == log.intent_id]
            
            # Determine status
            status = "created"
            if any(l.event_type.value == "execution_completed" for l in intent_logs):
                status = "completed"
            elif any(l.event_type.value == "execution_failed" for l in intent_logs):
                status = "failed"
            elif any(l.event_type.value == "execution_started" for l in intent_logs):
                status = "executing"
            
            intent_response = IntentResponse(
                intent_id=log.intent_id,
                status=status,
                user_address=log.user_address,
                source_chain=log.source_chain,
                destination_chain=log.destination_chain,
                input_token=log.input_token,
                output_token=log.output_token,
                input_amount=log.input_amount,
                minimum_output_amount=log.minimum_output_amount,
                deadline=int(log.details.get("deadline", time.time() + 1800)),
                created_at=datetime.fromtimestamp(log.timestamp),
                updated_at=datetime.fromtimestamp(max(l.timestamp for l in intent_logs))
            )
            intents.append(intent_response)
        
        return IntentListResponse(
            intents=intents,
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_next=end_idx < total_count
        )
        
    except Exception as e:
        context = ErrorContext(
            user_address=_get_primary_wallet_address(current_user),
            operation_type="intent_list"
        )
        
        await error_handling_service.handle_error(
            error=e,
            context=context,
            error_code="INTENT_LIST_FAILED"
        )
        
        raise HTTPException(
            status_code=500,
            detail="Failed to list intents"
        )


@router.delete("/intents/{intent_id}")
async def cancel_intent(
    intent_id: str,
    current_user: User = Depends(rate_limit_dependency),
    db: AsyncSession = Depends(get_db)
):
    """
    Cancel a pending intent
    Requirements: 10.1 - REST API endpoints for managing intents
    """
    try:
        # Check if intent exists and belongs to user
        intent_logs = [log for log in system_logging_service.intent_logs if log.intent_id == intent_id]
        if not intent_logs:
            raise HTTPException(status_code=404, detail="Intent not found")
        
        creation_log = next((log for log in intent_logs if log.event_type.value == "intent_created"), None)
        if not creation_log or creation_log.user_address != _get_primary_wallet_address(current_user):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Check if intent can be cancelled
        if any(log.event_type.value in ["execution_completed", "execution_failed", "intent_cancelled"] for log in intent_logs):
            raise HTTPException(status_code=400, detail="Intent cannot be cancelled")
        
        # Log cancellation
        system_logging_service.log_intent_created(  # Using this as a placeholder for cancellation
            intent_id=intent_id,
            user_address=_get_primary_wallet_address(current_user),
            source_chain=creation_log.source_chain,
            destination_chain=creation_log.destination_chain,
            input_token=creation_log.input_token,
            output_token=creation_log.output_token,
            input_amount=creation_log.input_amount,
            minimum_output_amount=creation_log.minimum_output_amount,
            details={"cancelled": True, "cancelled_at": time.time()}
        )
        
        return {"message": "Intent cancelled successfully", "intent_id": intent_id}
        
    except HTTPException:
        raise
    except Exception as e:
        context = ErrorContext(
            user_address=_get_primary_wallet_address(current_user),
            intent_id=intent_id,
            operation_type="intent_cancellation"
        )
        
        await error_handling_service.handle_error(
            error=e,
            context=context,
            error_code="INTENT_CANCELLATION_FAILED"
        )
        
        raise HTTPException(
            status_code=500,
            detail="Failed to cancel intent"
        )


@router.get("/intents/{intent_id}/estimate")
async def get_intent_estimate(
    intent_id: str,
    current_user: User = Depends(rate_limit_dependency),
    db: AsyncSession = Depends(get_db)
):
    """
    Get updated cost and time estimates for an intent
    Requirements: 10.1 - REST API endpoints for monitoring intents
    """
    try:
        # Check if intent exists and belongs to user
        intent_logs = [log for log in system_logging_service.intent_logs if log.intent_id == intent_id]
        if not intent_logs:
            raise HTTPException(status_code=404, detail="Intent not found")
        
        creation_log = next((log for log in intent_logs if log.event_type.value == "intent_created"), None)
        if not creation_log or creation_log.user_address != _get_primary_wallet_address(current_user):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # TODO: Implement actual cost estimation logic
        # For now, return mock estimates
        
        return {
            "intent_id": intent_id,
            "estimated_execution_time_seconds": 300,
            "estimated_gas_cost_eth": "0.015",
            "estimated_gas_cost_usd": "45.00",
            "estimated_output_amount": creation_log.minimum_output_amount,
            "price_impact_percentage": 0.1,
            "updated_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        context = ErrorContext(
            user_address=_get_primary_wallet_address(current_user),
            intent_id=intent_id,
            operation_type="intent_estimation"
        )
        
        await error_handling_service.handle_error(
            error=e,
            context=context,
            error_code="INTENT_ESTIMATION_FAILED"
        )
        
        raise HTTPException(
            status_code=500,
            detail="Failed to get intent estimate"
        )


async def process_intent_async(intent_id: str, intent_request: IntentCreateRequest, user: User):
    """Background task to process intent"""
    try:
        # Simulate intent processing
        await asyncio.sleep(2)  # Simulate validation time
        
        # Log validation
        system_logging_service.log_intent_created(  # Using as placeholder for validation
            intent_id=intent_id,
            user_address=_get_primary_wallet_address(user),
            source_chain=intent_request.source_chain,
            destination_chain=intent_request.destination_chain,
            input_token=intent_request.input_token,
            output_token=intent_request.output_token,
            input_amount=intent_request.input_amount,
            minimum_output_amount=intent_request.minimum_output_amount,
            details={"validated": True, "validated_at": time.time()}
        )
        
        # TODO: Integrate with actual intent engine
        # - Validate intent parameters
        # - Submit to solver network
        # - Monitor execution
        # - Handle completion/failure
        
    except Exception as e:
        # Log processing error
        context = ErrorContext(
            user_address=_get_primary_wallet_address(user),
            intent_id=intent_id,
            operation_type="intent_processing"
        )
        
        await error_handling_service.handle_error(
            error=e,
            context=context,
            error_code="INTENT_PROCESSING_FAILED"
        )