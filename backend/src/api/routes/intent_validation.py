"""
Intent validation API routes
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List

from src.core.schemas import (
    IntentValidationRequest, 
    ValidationResponse,
    LiquidityCheckRequest,
    LiquidityCheckResponse
)
from src.services.intent_validation_service import intent_validation_service

router = APIRouter(prefix="/intent-validation", tags=["Intent Validation"])


@router.post("/validate", response_model=ValidationResponse)
async def validate_intent(request: IntentValidationRequest):
    """
    Validate a single cross-chain intent
    
    Performs comprehensive validation including:
    - Basic parameter validation
    - Chain support verification
    - Token compatibility checking
    - Liquidity availability validation
    - Minimum output feasibility checks
    - Price impact analysis
    
    Requirements: 1.3, 7.1, 7.2
    """
    try:
        # Convert Pydantic model to dataclass for service
        from src.services.intent_validation_service import IntentValidationRequest as ServiceRequest
        
        service_request = ServiceRequest(
            user=request.user,
            source_chain=request.source_chain,
            destination_chain=request.destination_chain,
            input_token=request.input_token,
            output_token=request.output_token,
            input_amount=request.input_amount,
            minimum_output_amount=request.minimum_output_amount,
            deadline=request.deadline,
            nonce=request.nonce,
            recipient=request.recipient
        )
        
        result = await intent_validation_service.validate_intent(service_request)
        
        return ValidationResponse(
            is_valid=result.is_valid,
            result=result.result.value,
            reason=result.reason,
            liquidity_info=result.liquidity_info,
            price_impact=result.price_impact,
            estimated_output=result.estimated_output,
            gas_estimate=result.gas_estimate
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation error: {str(e)}")


@router.post("/validate-batch", response_model=List[ValidationResponse])
async def validate_batch_intents(requests: List[IntentValidationRequest]):
    """
    Validate multiple intents in batch
    
    Efficiently validates multiple intents concurrently.
    Useful for validating multiple trading strategies or bulk operations.
    """
    try:
        # Convert Pydantic models to dataclasses
        from src.services.intent_validation_service import IntentValidationRequest as ServiceRequest
        
        service_requests = [
            ServiceRequest(
                user=req.user,
                source_chain=req.source_chain,
                destination_chain=req.destination_chain,
                input_token=req.input_token,
                output_token=req.output_token,
                input_amount=req.input_amount,
                minimum_output_amount=req.minimum_output_amount,
                deadline=req.deadline,
                nonce=req.nonce,
                recipient=req.recipient
            )
            for req in requests
        ]
        
        results = await intent_validation_service.validate_batch_intents(service_requests)
        
        return [
            ValidationResponse(
                is_valid=result.is_valid,
                result=result.result.value,
                reason=result.reason,
                liquidity_info=result.liquidity_info,
                price_impact=result.price_impact,
                estimated_output=result.estimated_output,
                gas_estimate=result.gas_estimate
            )
            for result in results
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch validation error: {str(e)}")


@router.post("/check-liquidity", response_model=LiquidityCheckResponse)
async def check_liquidity_across_chains(request: LiquidityCheckRequest):
    """
    Check token liquidity across all supported chains
    
    Provides liquidity information for a specific token across all
    supported blockchain networks. Useful for finding the best
    execution venues for large trades.
    """
    try:
        liquidity_info = await intent_validation_service.check_liquidity_across_chains(
            token_address=request.token_address,
            amount=request.amount
        )
        
        return LiquidityCheckResponse(
            token_address=request.token_address,
            amount=request.amount,
            liquidity_by_chain=liquidity_info
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Liquidity check error: {str(e)}")


@router.get("/supported-chains")
async def get_supported_chains():
    """
    Get list of supported blockchain networks
    
    Returns the chains supported for cross-chain intent execution
    in Phase 1 of CrossFlow AI.
    """
    return {
        "supported_chains": intent_validation_service.supported_chains,
        "total_chains": len(intent_validation_service.supported_chains)
    }


@router.get("/validation-limits")
async def get_validation_limits():
    """
    Get current validation limits and thresholds
    
    Returns configuration parameters used for intent validation
    including deadline limits, price impact thresholds, etc.
    """
    return {
        "deadline_limits": {
            "minimum_seconds": intent_validation_service.min_deadline,
            "maximum_seconds": intent_validation_service.max_deadline
        },
        "price_impact_limits": {
            "maximum_allowed": float(intent_validation_service.max_price_impact),
            "warning_threshold": float(intent_validation_service.warning_price_impact)
        },
        "liquidity_thresholds": {
            key: float(value) for key, value in intent_validation_service.min_liquidity_usd.items()
        }
    }