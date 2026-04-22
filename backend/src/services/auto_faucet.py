"""
Automated Faucet Service
Automatically requests testnet tokens from faucets for connected wallets
"""
import aiohttp
import asyncio
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AutoFaucet:
    """Automatically drips testnet tokens to wallets"""
    
    # Faucet APIs that support programmatic access
    FAUCET_APIS = {
        'sepolia': [
            {
                'name': 'Alchemy Sepolia',
                'url': 'https://sepoliafaucet.com/api/claim',
                'method': 'POST',
                'requires_key': True
            }
        ]
    }
    
    def __init__(self):
        self.last_requests: Dict[str, datetime] = {}
        self.request_cooldown = timedelta(hours=24)  # Most faucets have 24h cooldown
    
    async def request_tokens(self, address: str, network: str = 'sepolia') -> Dict:
        """
        Request testnet tokens from faucets
        
        Args:
            address: Wallet address to send tokens to
            network: Network name (default: sepolia)
            
        Returns:
            Dict with success status and details
        """
        # Check cooldown
        cooldown_key = f"{network}:{address}"
        if cooldown_key in self.last_requests:
            time_since_last = datetime.utcnow() - self.last_requests[cooldown_key]
            if time_since_last < self.request_cooldown:
                remaining = self.request_cooldown - time_since_last
                return {
                    'success': False,
                    'error': f'Cooldown active. Try again in {remaining.seconds // 3600}h {(remaining.seconds % 3600) // 60}m'
                }
        
        # Try automated faucet request
        result = await self._try_automated_faucet(address, network)
        
        if result['success']:
            self.last_requests[cooldown_key] = datetime.utcnow()
            return result
        
        # If automated fails, provide manual instructions
        return {
            'success': False,
            'automated': False,
            'message': 'Automated faucet request not available. Please use manual faucets.',
            'manual_faucets': self._get_manual_faucets(network),
            'instructions': f"""
To get testnet tokens manually:

1. Visit one of these faucets:
   - https://sepoliafaucet.com
   - https://faucet.quicknode.com/ethereum/sepolia
   - https://www.infura.io/faucet/sepolia

2. Enter your address: {address}

3. Complete any verification (CAPTCHA, login, etc.)

4. Click "Request" or "Claim"

5. Wait 1-5 minutes for tokens to arrive

Most faucets give 0.5 - 1.0 ETH per request.
"""
        }
    
    async def _try_automated_faucet(self, address: str, network: str) -> Dict:
        """Try to request from automated faucet APIs"""
        faucets = self.FAUCET_APIS.get(network, [])
        
        for faucet in faucets:
            try:
                # Most public faucets don't have open APIs
                # This is a placeholder for when/if they do
                logger.info(f"Attempting automated faucet request from {faucet['name']}")
                
                # For now, return False to use manual process
                return {'success': False}
                
            except Exception as e:
                logger.error(f"Faucet request failed: {e}")
                continue
        
        return {'success': False}
    
    def _get_manual_faucets(self, network: str) -> list:
        """Get list of manual faucets for a network"""
        if network == 'sepolia':
            return [
                {
                    'name': 'Alchemy Sepolia Faucet',
                    'url': 'https://sepoliafaucet.com',
                    'amount': '0.5 ETH',
                    'cooldown': '24 hours'
                },
                {
                    'name': 'QuickNode Sepolia Faucet',
                    'url': 'https://faucet.quicknode.com/ethereum/sepolia',
                    'amount': '0.1 ETH',
                    'cooldown': '12 hours'
                },
                {
                    'name': 'Infura Sepolia Faucet',
                    'url': 'https://www.infura.io/faucet/sepolia',
                    'amount': '0.5 ETH',
                    'cooldown': '24 hours'
                }
            ]
        return []
    
    async def auto_drip_for_wallet(self, address: str, network: str = 'sepolia', 
                                   min_balance: float = 0.01) -> Dict:
        """
        Automatically request tokens if balance is low
        
        Args:
            address: Wallet address
            network: Network name
            min_balance: Minimum balance threshold to trigger drip
            
        Returns:
            Dict with drip status
        """
        from web3 import Web3
        
        # Check current balance
        if network == 'sepolia':
            w3 = Web3(Web3.HTTPProvider('https://rpc.sepolia.org'))
            balance = w3.eth.get_balance(address)
            balance_eth = float(w3.from_wei(balance, 'ether'))
            
            logger.info(f"Wallet {address} balance: {balance_eth} ETH")
            
            if balance_eth < min_balance:
                logger.info(f"Balance below threshold ({min_balance} ETH), requesting tokens...")
                return await self.request_tokens(address, network)
            else:
                return {
                    'success': True,
                    'message': f'Balance sufficient: {balance_eth} ETH',
                    'balance': balance_eth,
                    'drip_needed': False
                }
        
        return {'success': False, 'error': 'Unsupported network'}


# Global instance
auto_faucet = AutoFaucet()
