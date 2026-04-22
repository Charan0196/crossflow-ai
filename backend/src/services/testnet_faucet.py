"""
Testnet Faucet Service
Helps users get testnet tokens for testing
"""
import aiohttp
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class TestnetFaucet:
    """Manages testnet faucet requests"""
    
    # Popular testnet faucets
    FAUCETS = {
        'sepolia': [
            {
                'name': 'Alchemy Sepolia Faucet',
                'url': 'https://sepoliafaucet.com',
                'tokens': ['ETH'],
                'requires_login': True
            },
            {
                'name': 'Infura Sepolia Faucet',
                'url': 'https://www.infura.io/faucet/sepolia',
                'tokens': ['ETH'],
                'requires_login': True
            },
            {
                'name': 'QuickNode Sepolia Faucet',
                'url': 'https://faucet.quicknode.com/ethereum/sepolia',
                'tokens': ['ETH'],
                'requires_login': False
            }
        ],
        'goerli': [
            {
                'name': 'Alchemy Goerli Faucet',
                'url': 'https://goerlifaucet.com',
                'tokens': ['ETH'],
                'requires_login': True
            }
        ],
        'mumbai': [
            {
                'name': 'Alchemy Mumbai Faucet',
                'url': 'https://mumbaifaucet.com',
                'tokens': ['MATIC'],
                'requires_login': True
            },
            {
                'name': 'Polygon Mumbai Faucet',
                'url': 'https://faucet.polygon.technology',
                'tokens': ['MATIC'],
                'requires_login': False
            }
        ],
        'arbitrum-goerli': [
            {
                'name': 'Arbitrum Goerli Faucet',
                'url': 'https://faucet.triangleplatform.com/arbitrum/goerli',
                'tokens': ['ETH'],
                'requires_login': False
            }
        ],
        'optimism-goerli': [
            {
                'name': 'Optimism Goerli Faucet',
                'url': 'https://optimismfaucet.xyz',
                'tokens': ['ETH'],
                'requires_login': False
            }
        ],
        'base-goerli': [
            {
                'name': 'Base Goerli Faucet',
                'url': 'https://faucet.quicknode.com/base/goerli',
                'tokens': ['ETH'],
                'requires_login': False
            }
        ]
    }
    
    def get_faucets_for_network(self, network: str) -> List[Dict]:
        """Get available faucets for a network"""
        return self.FAUCETS.get(network.lower(), [])
    
    def get_all_faucets(self) -> Dict[str, List[Dict]]:
        """Get all available faucets"""
        return self.FAUCETS
    
    async def request_tokens(self, network: str, address: str, faucet_url: str = None) -> Dict:
        """
        Request tokens from a faucet
        
        Note: Most faucets require manual interaction through their website
        This method provides the information needed to request tokens
        """
        faucets = self.get_faucets_for_network(network)
        
        if not faucets:
            return {
                'success': False,
                'error': f'No faucets available for network: {network}'
            }
        
        # If specific faucet URL provided, use that
        if faucet_url:
            faucet = next((f for f in faucets if f['url'] == faucet_url), None)
            if not faucet:
                return {
                    'success': False,
                    'error': 'Faucet URL not found'
                }
        else:
            # Use first available faucet
            faucet = faucets[0]
        
        return {
            'success': True,
            'message': 'Please visit the faucet website to request tokens',
            'faucet': faucet,
            'address': address,
            'instructions': self._get_instructions(faucet, address)
        }
    
    def _get_instructions(self, faucet: Dict, address: str) -> str:
        """Get instructions for using a faucet"""
        instructions = f"""
To get testnet tokens from {faucet['name']}:

1. Visit: {faucet['url']}
2. Enter your wallet address: {address}
3. {'Complete login/verification if required' if faucet['requires_login'] else 'Complete any CAPTCHA if required'}
4. Click the request/claim button
5. Wait for the transaction to complete (usually 1-5 minutes)

Available tokens: {', '.join(faucet['tokens'])}

Note: Most faucets have rate limits (e.g., once per 24 hours per address)
"""
        return instructions.strip()
    
    def get_testnet_info(self) -> Dict:
        """Get information about testnets"""
        return {
            'sepolia': {
                'name': 'Sepolia Testnet',
                'chain_id': 11155111,
                'currency': 'ETH',
                'rpc': 'https://rpc.sepolia.org',
                'explorer': 'https://sepolia.etherscan.io'
            },
            'goerli': {
                'name': 'Goerli Testnet',
                'chain_id': 5,
                'currency': 'ETH',
                'rpc': 'https://goerli.infura.io/v3/YOUR-PROJECT-ID',
                'explorer': 'https://goerli.etherscan.io'
            },
            'mumbai': {
                'name': 'Mumbai Testnet (Polygon)',
                'chain_id': 80001,
                'currency': 'MATIC',
                'rpc': 'https://rpc-mumbai.maticvigil.com',
                'explorer': 'https://mumbai.polygonscan.com'
            },
            'arbitrum-goerli': {
                'name': 'Arbitrum Goerli',
                'chain_id': 421613,
                'currency': 'ETH',
                'rpc': 'https://goerli-rollup.arbitrum.io/rpc',
                'explorer': 'https://goerli.arbiscan.io'
            },
            'optimism-goerli': {
                'name': 'Optimism Goerli',
                'chain_id': 420,
                'currency': 'ETH',
                'rpc': 'https://goerli.optimism.io',
                'explorer': 'https://goerli-optimism.etherscan.io'
            },
            'base-goerli': {
                'name': 'Base Goerli',
                'chain_id': 84531,
                'currency': 'ETH',
                'rpc': 'https://goerli.base.org',
                'explorer': 'https://goerli.basescan.org'
            }
        }


# Global instance
testnet_faucet = TestnetFaucet()
