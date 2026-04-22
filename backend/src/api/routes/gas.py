"""
Phase 5: Gas Optimization API Routes
"""

from fastapi import APIRouter, HTTPException
from typing import Optional, List
from pydantic import BaseModel
from decimal import Decimal

from src.services.gas_optimizer import gas_optimizer, GasSpeed

router = APIRouter(prefix="/gas", tags=["gas"])


class RouteForOptimization(BaseModel):
    chain_id: int
    output_amount_usd: float


@router.get("/info/{chain_id}")
async def get_gas_info(chain_id: int):
    """Get current gas info for a chain."""
    gas_info = await gas_optimizer.get_gas_info(chain_id)
    
    if not gas_info:
        raise HTTPException(status_code=404, detail="Chain not supported")
    
    return {
        "chain_id": gas_info.chain_id,
        "chain_name": gas_info.chain_name,
        "native_token": gas_info.native_token,
        "native_price_usd": float(gas_info.native_price_usd),
        "base_fee_gwei": float(gas_info.base_fee_gwei),
        "gas_prices": {
            "slow": float(gas_info.slow_gwei),
            "standard": float(gas_info.standard_gwei),
            "fast": float(gas_info.fast_gwei),
            "instant": float(gas_info.instant_gwei)
        },
        "is_congested": gas_info.is_congested,
        "congestion_level": gas_info.congestion_level,
        "last_updated": gas_info.last_updated.isoformat()
    }


@router.get("/estimate/{chain_id}")
async def estimate_gas(
    chain_id: int,
    operation: str = "swap_simple",
    speed: str = "standard",
    gas_limit: Optional[int] = None
):
    """Estimate gas cost for an operation."""
    try:
        speed_enum = GasSpeed(speed)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid speed")
    
    estimate = await gas_optimizer.estimate_gas(
        chain_id=chain_id,
        operation=operation,
        speed=speed_enum,
        custom_gas_limit=gas_limit
    )
    
    if not estimate:
        raise HTTPException(status_code=404, detail="Chain not supported")
    
    return {
        "chain_id": estimate.chain_id,
        "gas_limit": estimate.gas_limit,
        "gas_price_gwei": float(estimate.gas_price_gwei),
        "max_fee_gwei": float(estimate.max_fee_gwei),
        "priority_fee_gwei": float(estimate.priority_fee_gwei),
        "estimated_cost_native": float(estimate.estimated_cost_native),
        "estimated_cost_usd": float(estimate.estimated_cost_usd),
        "speed": estimate.speed.value,
        "estimated_time_seconds": estimate.estimated_time_seconds
    }


@router.post("/optimal-route")
async def find_optimal_route(
    routes: List[RouteForOptimization],
    max_gas_usd: Optional[float] = None
):
    """Find the most cost-effective route."""
    routes_dict = [r.dict() for r in routes]
    max_gas = Decimal(str(max_gas_usd)) if max_gas_usd else None
    
    result = await gas_optimizer.find_optimal_route(routes_dict, max_gas)
    
    if not result:
        return {"optimal_route": None, "message": "No valid routes found"}
    
    return {
        "optimal_route": result["route"],
        "gas_cost_usd": float(result["gas_cost_usd"]),
        "net_value_usd": float(result["net_value_usd"])
    }


@router.get("/should-wait/{chain_id}")
async def should_wait_for_lower_gas(
    chain_id: int,
    threshold_gwei: Optional[float] = None
):
    """Check if user should wait for lower gas prices."""
    threshold = Decimal(str(threshold_gwei)) if threshold_gwei else None
    return await gas_optimizer.should_wait_for_lower_gas(chain_id, threshold)


@router.get("/all-chains")
async def get_all_chains_gas():
    """Get gas info for all supported chains."""
    gas_infos = await gas_optimizer.get_all_chains_gas()
    
    return {
        "chains": [
            {
                "chain_id": info.chain_id,
                "chain_name": info.chain_name,
                "native_token": info.native_token,
                "base_fee_gwei": float(info.base_fee_gwei),
                "is_congested": info.is_congested,
                "congestion_level": info.congestion_level
            }
            for info in gas_infos
        ]
    }
