"""
Solver Network API routes for intent broadcasting and management
"""
from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from typing import List, Optional, Dict
import json
import logging
from datetime import datetime

from src.core.schemas import *
from src.services.solver_network_service import (
    solver_network_service, 
    SolverStatus, 
    IntentStatus
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/solver-network", tags=["Solver Network"])


# Pydantic schemas for API
class SolverRegistrationRequest(BaseModel):
    address: str
    name: str
    endpoint: str
    supported_chains: List[int]
    supported_tokens: List[str]
    stake_amount: str


class SolverBidRequest(BaseModel):
    solver_address: str
    intent_hash: str
    output_amount: str
    execution_time_estimate: int
    gas_fee_estimate: str
    solver_fee: str
    signature: str


class IntentBroadcastRequest(BaseModel):
    intent_hash: str
    intent_data: Dict
    target_chains: List[int]


class SolverStatusUpdate(BaseModel):
    address: str
    status: str


# Solver Management Endpoints

@router.post("/solvers/register")
async def register_solver(request: SolverRegistrationRequest):
    """
    Register a new solver in the network
    
    Allows market makers and liquidity providers to register as solvers
    to receive and fulfill cross-chain trading intents.
    
    Requirements: 4.1
    """
    try:
        success = await solver_network_service.register_solver(
            address=request.address,
            name=request.name,
            endpoint=request.endpoint,
            supported_chains=request.supported_chains,
            supported_tokens=request.supported_tokens,
            stake_amount=request.stake_amount
        )
        
        if success:
            return {"success": True, "message": "Solver registered successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to register solver")
            
    except Exception as e:
        logger.error(f"Error registering solver: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/solvers")
async def get_active_solvers(chain_id: Optional[int] = None):
    """
    Get list of active solvers
    
    Returns all active solvers in the network, optionally filtered by
    supported chain ID. Includes reputation scores and performance metrics.
    """
    try:
        solvers = await solver_network_service.get_active_solvers(chain_id)
        
        return {
            "solvers": [
                {
                    "address": solver.address,
                    "name": solver.name,
                    "supported_chains": solver.supported_chains,
                    "reputation_score": solver.reputation_score,
                    "total_intents": solver.total_intents,
                    "successful_intents": solver.successful_intents,
                    "success_rate": solver.successful_intents / max(solver.total_intents, 1),
                    "average_execution_time": solver.average_execution_time,
                    "status": solver.status.value
                }
                for solver in solvers
            ],
            "total_count": len(solvers)
        }
        
    except Exception as e:
        logger.error(f"Error getting active solvers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/solvers/{solver_address}/stats")
async def get_solver_statistics(solver_address: str):
    """
    Get detailed solver performance statistics
    
    Returns comprehensive performance metrics for a specific solver
    including reputation score, success rate, and execution history.
    """
    try:
        stats = await solver_network_service.get_solver_statistics(solver_address)
        
        if not stats:
            raise HTTPException(status_code=404, detail="Solver not found")
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting solver statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/solvers/{solver_address}/status")
async def update_solver_status(solver_address: str, status_update: SolverStatusUpdate):
    """
    Update solver status (admin only)
    
    Allows administrators to activate, deactivate, suspend, or blacklist solvers
    based on their performance and behavior.
    """
    try:
        # Validate status
        try:
            status = SolverStatus(status_update.status)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid status value")
        
        success = await solver_network_service.update_solver_status(solver_address, status)
        
        if success:
            return {"success": True, "message": f"Solver status updated to {status.value}"}
        else:
            raise HTTPException(status_code=404, detail="Solver not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating solver status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Intent Broadcasting Endpoints

@router.post("/intents/broadcast")
async def broadcast_intent(request: IntentBroadcastRequest):
    """
    Broadcast intent to solver network
    
    Distributes a new trading intent to all eligible solvers in the network
    for competitive bidding. Solvers can then submit bids to fulfill the intent.
    
    Requirements: 1.4, 4.1
    """
    try:
        success = await solver_network_service.broadcast_intent(
            intent_hash=request.intent_hash,
            intent_data=request.intent_data,
            target_chains=request.target_chains
        )
        
        if success:
            return {
                "success": True, 
                "message": "Intent broadcast successfully",
                "intent_hash": request.intent_hash
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to broadcast intent")
            
    except Exception as e:
        logger.error(f"Error broadcasting intent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/intents/bids")
async def submit_solver_bid(request: SolverBidRequest):
    """
    Submit solver bid for intent fulfillment
    
    Allows registered solvers to submit competitive bids for fulfilling
    a specific trading intent. Bids include pricing, execution time, and fees.
    
    Requirements: 4.1
    """
    try:
        success = await solver_network_service.submit_solver_bid(
            solver_address=request.solver_address,
            intent_hash=request.intent_hash,
            output_amount=request.output_amount,
            execution_time_estimate=request.execution_time_estimate,
            gas_fee_estimate=request.gas_fee_estimate,
            solver_fee=request.solver_fee,
            signature=request.signature
        )
        
        if success:
            return {
                "success": True,
                "message": "Bid submitted successfully",
                "solver_address": request.solver_address,
                "intent_hash": request.intent_hash
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to submit bid")
            
    except Exception as e:
        logger.error(f"Error submitting solver bid: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/intents/{intent_hash}/select-solver")
async def select_best_solver(intent_hash: str):
    """
    Select best solver for intent fulfillment
    
    Evaluates all received bids and selects the optimal solver based on
    price, execution time, reputation, and other factors.
    
    Requirements: 4.2
    """
    try:
        selected_solver = await solver_network_service.select_best_solver(intent_hash)
        
        if selected_solver:
            return {
                "success": True,
                "selected_solver": selected_solver,
                "intent_hash": intent_hash
            }
        else:
            raise HTTPException(status_code=404, detail="No suitable solver found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error selecting solver: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Intent Status Management

@router.get("/intents/{intent_hash}/status")
async def get_intent_status(intent_hash: str):
    """
    Get current intent status and details
    
    Returns comprehensive information about an intent including current status,
    received bids, selected solver, and execution progress.
    """
    try:
        status = await solver_network_service.get_intent_status(intent_hash)
        
        if not status:
            raise HTTPException(status_code=404, detail="Intent not found")
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting intent status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/intents/{intent_hash}/status")
async def update_intent_status(intent_hash: str, status: str):
    """
    Update intent status
    
    Updates the current status of an intent (e.g., executing, completed, failed).
    Used by solvers and system components to track execution progress.
    """
    try:
        # Validate status
        try:
            intent_status = IntentStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid status value")
        
        success = await solver_network_service.update_intent_status(intent_hash, intent_status)
        
        if success:
            return {
                "success": True,
                "intent_hash": intent_hash,
                "status": status
            }
        else:
            raise HTTPException(status_code=404, detail="Intent not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating intent status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket Endpoints for Real-time Communication

@router.websocket("/ws/solver/{solver_address}")
async def solver_websocket_endpoint(websocket: WebSocket, solver_address: str):
    """
    WebSocket endpoint for solver real-time communication
    
    Provides real-time intent broadcasts and status updates to registered solvers.
    Solvers can receive new intents and submit bids through this connection.
    """
    await websocket.accept()
    
    # Register solver connection
    solver_network_service.solver_connections[solver_address] = websocket
    
    try:
        while True:
            # Receive messages from solver
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "bid":
                # Process bid submission
                bid_data = message.get("data", {})
                await solver_network_service.submit_solver_bid(
                    solver_address=solver_address,
                    intent_hash=bid_data.get("intent_hash"),
                    output_amount=bid_data.get("output_amount"),
                    execution_time_estimate=bid_data.get("execution_time_estimate"),
                    gas_fee_estimate=bid_data.get("gas_fee_estimate"),
                    solver_fee=bid_data.get("solver_fee"),
                    signature=bid_data.get("signature")
                )
                
                # Send confirmation
                await websocket.send_text(json.dumps({
                    "type": "bid_confirmation",
                    "success": True,
                    "intent_hash": bid_data.get("intent_hash")
                }))
            
            elif message.get("type") == "heartbeat":
                # Update solver last seen time
                if solver_address in solver_network_service.registered_solvers:
                    solver_network_service.registered_solvers[solver_address].last_seen = datetime.now()
                
                # Send heartbeat response
                await websocket.send_text(json.dumps({
                    "type": "heartbeat_response",
                    "timestamp": datetime.now().isoformat()
                }))
            
    except WebSocketDisconnect:
        # Remove solver connection
        if solver_address in solver_network_service.solver_connections:
            del solver_network_service.solver_connections[solver_address]
        
        logger.info(f"Solver {solver_address} disconnected")
    
    except Exception as e:
        logger.error(f"WebSocket error for solver {solver_address}: {e}")
        if solver_address in solver_network_service.solver_connections:
            del solver_network_service.solver_connections[solver_address]


@router.websocket("/ws/user/{user_address}")
async def user_websocket_endpoint(websocket: WebSocket, user_address: str):
    """
    WebSocket endpoint for user real-time updates
    
    Provides real-time updates to users about their intent status,
    received bids, and execution progress.
    """
    await websocket.accept()
    
    # Register user connection
    solver_network_service.user_connections[user_address] = websocket
    
    try:
        while True:
            # Receive messages from user (mostly heartbeats)
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "heartbeat":
                # Send heartbeat response
                await websocket.send_text(json.dumps({
                    "type": "heartbeat_response",
                    "timestamp": datetime.now().isoformat()
                }))
            
    except WebSocketDisconnect:
        # Remove user connection
        if user_address in solver_network_service.user_connections:
            del solver_network_service.user_connections[user_address]
        
        logger.info(f"User {user_address} disconnected")
    
    except Exception as e:
        logger.error(f"WebSocket error for user {user_address}: {e}")
        if user_address in solver_network_service.user_connections:
            del solver_network_service.user_connections[user_address]


# System Status and Monitoring

@router.get("/system/status")
async def get_system_status():
    """
    Get solver network system status
    
    Returns overall system health including active solvers count,
    active intents, and network performance metrics.
    """
    try:
        active_solvers = len([
            s for s in solver_network_service.registered_solvers.values()
            if s.status == SolverStatus.ACTIVE
        ])
        
        active_intents = len(solver_network_service.active_intents)
        
        total_intents_processed = len(solver_network_service.intent_history)
        
        return {
            "system_status": "healthy",
            "active_solvers": active_solvers,
            "total_registered_solvers": len(solver_network_service.registered_solvers),
            "active_intents": active_intents,
            "total_intents_processed": total_intents_processed,
            "websocket_connections": {
                "solvers": len(solver_network_service.solver_connections),
                "users": len(solver_network_service.user_connections)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system/metrics")
async def get_system_metrics():
    """
    Get detailed system performance metrics
    
    Returns comprehensive metrics about solver network performance
    including average execution times, success rates, and throughput.
    """
    try:
        # Calculate aggregate metrics
        total_solvers = len(solver_network_service.registered_solvers)
        active_solvers = len([
            s for s in solver_network_service.registered_solvers.values()
            if s.status == SolverStatus.ACTIVE
        ])
        
        # Calculate average reputation score
        if total_solvers > 0:
            avg_reputation = sum(
                s.reputation_score for s in solver_network_service.registered_solvers.values()
            ) / total_solvers
        else:
            avg_reputation = 0.0
        
        # Calculate system success rate
        total_intents = sum(
            s.total_intents for s in solver_network_service.registered_solvers.values()
        )
        successful_intents = sum(
            s.successful_intents for s in solver_network_service.registered_solvers.values()
        )
        
        system_success_rate = successful_intents / max(total_intents, 1)
        
        return {
            "solver_metrics": {
                "total_solvers": total_solvers,
                "active_solvers": active_solvers,
                "average_reputation": avg_reputation,
                "system_success_rate": system_success_rate
            },
            "intent_metrics": {
                "active_intents": len(solver_network_service.active_intents),
                "completed_intents": len(solver_network_service.intent_history),
                "total_intents_processed": total_intents
            },
            "network_metrics": {
                "solver_connections": len(solver_network_service.solver_connections),
                "user_connections": len(solver_network_service.user_connections)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))