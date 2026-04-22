"""
ZK Proof API Routes - Phase 4
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from datetime import datetime

router = APIRouter(prefix="/zk", tags=["ZK Proofs"])


class ProofGenerationRequest(BaseModel):
    trade_id: str
    trade_type: str  # swap, bridge, rwa
    execution_params: Dict[str, Any]
    strategy_commitment: str  # hex encoded


class ProofVerificationRequest(BaseModel):
    proof_id: str


class BatchVerificationRequest(BaseModel):
    proof_ids: List[str]


@router.post("/generate")
async def generate_proof(request: ProofGenerationRequest) -> Dict[str, Any]:
    """Generate ZK proof for trade execution."""
    from ...zk import ZKProofSystem, ProofGenerationRequest as PGR, TradeType
    
    system = ZKProofSystem()
    
    trade_type_map = {
        "swap": TradeType.SWAP,
        "bridge": TradeType.BRIDGE,
        "rwa": TradeType.RWA,
    }
    
    trade_type = trade_type_map.get(request.trade_type)
    if not trade_type:
        raise HTTPException(400, f"Invalid trade type: {request.trade_type}")
    
    pgr = PGR(
        trade_id=request.trade_id,
        trade_type=trade_type,
        execution_params=request.execution_params,
        strategy_commitment=bytes.fromhex(request.strategy_commitment),
    )
    
    proof = await system.generate_proof(pgr)
    await system.store_proof(proof)
    
    return {
        "proof_id": proof.proof_id,
        "trade_id": proof.trade_id,
        "proof_type": proof.proof_type.value,
        "public_inputs": proof.public_inputs,
        "timestamp": proof.timestamp.isoformat(),
        "circuit_version": proof.circuit_version,
    }


@router.post("/verify")
async def verify_proof(request: ProofVerificationRequest) -> Dict[str, Any]:
    """Verify a ZK proof."""
    from ...zk import ZKProofSystem
    
    system = ZKProofSystem()
    proof = await system.get_proof(request.proof_id)
    
    if not proof:
        raise HTTPException(404, "Proof not found")
    
    result = await system.verify_proof(proof)
    
    return {
        "valid": result.valid,
        "proof_id": result.proof_id,
        "verification_time_ms": result.verification_time_ms,
        "failure_reason": result.failure_reason,
        "verified_at": result.verified_at.isoformat(),
    }


@router.post("/verify/batch")
async def batch_verify(request: BatchVerificationRequest) -> List[Dict[str, Any]]:
    """Verify multiple proofs in batch."""
    from ...zk import ZKProofSystem
    
    system = ZKProofSystem()
    proofs = []
    
    for proof_id in request.proof_ids:
        proof = await system.get_proof(proof_id)
        if proof:
            proofs.append(proof)
    
    results = await system.batch_verify(proofs)
    
    return [
        {
            "valid": r.valid,
            "proof_id": r.proof_id,
            "verification_time_ms": r.verification_time_ms,
            "failure_reason": r.failure_reason,
        }
        for r in results
    ]


@router.get("/proof/{proof_id}")
async def get_proof(proof_id: str) -> Dict[str, Any]:
    """Get proof details."""
    from ...zk import ZKProofSystem
    
    system = ZKProofSystem()
    proof = await system.get_proof(proof_id)
    
    if not proof:
        raise HTTPException(404, "Proof not found")
    
    return {
        "proof_id": proof.proof_id,
        "trade_id": proof.trade_id,
        "proof_type": proof.proof_type.value,
        "public_inputs": proof.public_inputs,
        "timestamp": proof.timestamp.isoformat(),
        "circuit_version": proof.circuit_version,
        "verification_key_hash": proof.verification_key_hash,
    }


@router.get("/trade/{trade_id}/proofs")
async def get_proofs_for_trade(trade_id: str) -> List[Dict[str, Any]]:
    """Get all proofs for a trade."""
    from ...zk import ZKProofSystem
    
    system = ZKProofSystem()
    proofs = await system.get_proofs_for_trade(trade_id)
    
    return [
        {
            "proof_id": p.proof_id,
            "proof_type": p.proof_type.value,
            "timestamp": p.timestamp.isoformat(),
        }
        for p in proofs
    ]
