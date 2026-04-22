"""
Testnet Faucet API Routes
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from ...services.testnet_faucet import testnet_faucet

router = APIRouter(prefix="/faucet", tags=["Testnet Faucet"])


class FaucetRequest(BaseModel):
    """Request tokens from a faucet"""
    network: str
    address: str
    faucet_url: Optional[str] = None


@router.get("/networks")
async def get_testnet_networks():
    """Get information about available testnets"""
    return testnet_faucet.get_testnet_info()


@router.get("/list")
async def get_all_faucets():
    """Get all available faucets"""
    return {
        'faucets': testnet_faucet.get_all_faucets()
    }


@router.get("/list/{network}")
async def get_faucets_for_network(network: str):
    """Get available faucets for a specific network"""
    faucets = testnet_faucet.get_faucets_for_network(network)
    
    if not faucets:
        raise HTTPException(
            status_code=404,
            detail=f"No faucets available for network: {network}"
        )
    
    return {
        'network': network,
        'faucets': faucets
    }


@router.post("/request")
async def request_tokens(request: FaucetRequest):
    """
    Get instructions for requesting testnet tokens
    
    - **network**: Testnet network (e.g., 'sepolia', 'mumbai')
    - **address**: Your wallet address
    - **faucet_url**: Optional specific faucet URL to use
    """
    result = await testnet_faucet.request_tokens(
        network=request.network,
        address=request.address,
        faucet_url=request.faucet_url
    )
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result.get('error'))
    
    return result
