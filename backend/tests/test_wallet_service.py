"""
Unit tests for WalletService
"""
import pytest
import asyncio
import time
from decimal import Decimal
from unittest.mock import Mock, patch, AsyncMock, MagicMock

from src.services.wallet_service import (
    WalletService, 
    TokenBalance, 
    WalletBalance,
    CachedData
)


@pytest.fixture
def wallet_service():
    """Create a wallet service instance for testing"""
    return WalletService(network='sepolia')


@pytest.fixture
def demo_wallet_address():
    """Demo wallet address from spec"""
    return "0x6739659248061A54E0f4de8f2cd60278B69468b3"


@pytest.fixture
def mock_price_oracle():
    """Mock price oracle"""
    with patch('src.services.wallet_service.price_oracle') as mock:
        # Mock ETH price
        eth_price = Mock()
        eth_price.price = Decimal("2000.00")
        eth_price.change_24h = 2.5
        
        # Mock USDC price
        usdc_price = Mock()
        usdc_price.price = Decimal("1.00")
        usdc_price.change_24h = 0.0
        
        # Mock WETH price
        weth_price = Mock()
        weth_price.price = Decimal("2000.00")
        weth_price.change_24h = 2.5
        
        async def get_price_side_effect(symbol):
            if symbol.upper() in ['ETH', 'ETHUSDT']:
                return eth_price
            elif symbol.upper() in ['USDC', 'USDCUSDT']:
                return usdc_price
            elif symbol.upper() in ['WETH', 'WETHUSDT']:
                return weth_price
            return None
        
        mock.get_price = AsyncMock(side_effect=get_price_side_effect)
        yield mock


@pytest.fixture
def mock_web3():
    """Mock Web3 instance"""
    with patch('src.services.wallet_service.DEXExecutor') as mock_dex:
        # Create mock Web3 instance
        mock_w3 = Mock()
        
        # Mock ETH balance (0.5 ETH)
        mock_w3.eth.get_balance.return_value = 500000000000000000  # 0.5 ETH in wei
        mock_w3.from_wei.return_value = 0.5
        
        # Mock token contract
        mock_token_contract = Mock()
        mock_token_contract.functions.balanceOf.return_value.call.return_value = 1000000000  # 1000 USDC (6 decimals)
        mock_w3.eth.contract.return_value = mock_token_contract
        
        # Set up DEX executor mock
        mock_dex_instance = Mock()
        mock_dex_instance.w3 = mock_w3
        mock_dex_instance._get_token_address.side_effect = lambda symbol: {
            'USDC': '0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238',
            'WETH': '0x7b79995e5f793A07Bc00c21412e50Ecae098E7f9'
        }.get(symbol, '0x0000000000000000000000000000000000000000')
        mock_dex_instance.ERC20_ABI = []
        
        mock_dex.return_value = mock_dex_instance
        
        yield mock_dex_instance


class TestWalletService:
    """Test suite for WalletService"""
    
    def test_initialization(self, wallet_service):
        """Test wallet service initializes correctly"""
        assert wallet_service.network == 'sepolia'
        assert wallet_service.CACHE_TTL == 10
        assert 'USDC' in wallet_service.SUPPORTED_TOKENS
        assert 'WETH' in wallet_service.SUPPORTED_TOKENS
    
    def test_cache_key_generation(self, wallet_service, demo_wallet_address):
        """Test cache key generation"""
        key = wallet_service._get_cache_key("balance", demo_wallet_address)
        assert key == f"balance:{demo_wallet_address.lower()}"
    
    def test_cache_set_and_get(self, wallet_service):
        """Test caching mechanism"""
        key = "test:key"
        data = {"test": "data"}
        
        # Set cache
        wallet_service._set_cache(key, data)
        
        # Get cache (should hit)
        cached = wallet_service._get_cached(key)
        assert cached == data
    
    def test_cache_expiry(self, wallet_service):
        """Test cache expiration"""
        key = "test:expiry"
        data = {"test": "data"}
        
        # Set cache with very short TTL
        wallet_service.CACHE_TTL = 0.1
        wallet_service._set_cache(key, data)
        
        # Should hit immediately
        assert wallet_service._get_cached(key) == data
        
        # Wait for expiry
        time.sleep(0.2)
        
        # Should miss after expiry
        assert wallet_service._get_cached(key) is None
        
        # Reset TTL
        wallet_service.CACHE_TTL = 10
    
    @pytest.mark.asyncio
    async def test_get_balance(
        self, wallet_service, demo_wallet_address, mock_web3, mock_price_oracle
    ):
        """Test getting wallet balance"""
        # Clear cache first
        wallet_service.clear_cache()
        
        # Get balance
        balance = await wallet_service.get_balance(demo_wallet_address)
        
        # Verify structure
        assert isinstance(balance, WalletBalance)
        assert balance.address == demo_wallet_address
        assert balance.eth_balance == "0.5000"
        assert balance.eth_balance_wei == 500000000000000000
        assert balance.eth_usd_value == 1000.0  # 0.5 ETH * $2000
        assert isinstance(balance.token_balances, list)
        assert balance.total_value_usd > 0
        assert balance.last_update > 0
    
    @pytest.mark.asyncio
    async def test_get_balance_caching(
        self, wallet_service, demo_wallet_address, mock_web3, mock_price_oracle
    ):
        """Test that balance is cached properly"""
        # Clear cache first
        wallet_service.clear_cache()
        
        # First call - should fetch from blockchain
        balance1 = await wallet_service.get_balance(demo_wallet_address)
        
        # Second call - should use cache
        balance2 = await wallet_service.get_balance(demo_wallet_address)
        
        # Should return same object from cache
        assert balance1.last_update == balance2.last_update
        assert balance1.eth_balance == balance2.eth_balance
    
    @pytest.mark.asyncio
    async def test_get_token_balances(
        self, wallet_service, demo_wallet_address, mock_web3, mock_price_oracle
    ):
        """Test getting token balances"""
        # Clear cache first
        wallet_service.clear_cache()
        
        # Get token balances
        balances = await wallet_service.get_token_balances(demo_wallet_address)
        
        # Verify structure
        assert isinstance(balances, list)
        assert len(balances) > 0
        
        # Check each token balance
        for token_balance in balances:
            assert isinstance(token_balance, TokenBalance)
            assert token_balance.symbol in wallet_service.SUPPORTED_TOKENS
            assert token_balance.name
            assert token_balance.address
            assert token_balance.balance
            assert isinstance(token_balance.balance_wei, int)
            assert isinstance(token_balance.usd_value, float)
    
    @pytest.mark.asyncio
    async def test_get_token_balances_caching(
        self, wallet_service, demo_wallet_address, mock_web3, mock_price_oracle
    ):
        """Test that token balances are cached"""
        # Clear cache first
        wallet_service.clear_cache()
        
        # First call
        balances1 = await wallet_service.get_token_balances(demo_wallet_address)
        
        # Second call - should use cache
        balances2 = await wallet_service.get_token_balances(demo_wallet_address)
        
        # Should return same data
        assert len(balances1) == len(balances2)
        for b1, b2 in zip(balances1, balances2):
            assert b1.symbol == b2.symbol
            assert b1.balance == b2.balance
    
    @pytest.mark.asyncio
    async def test_calculate_portfolio_value(
        self, wallet_service, demo_wallet_address, mock_web3, mock_price_oracle
    ):
        """Test portfolio value calculation"""
        # Clear cache first
        wallet_service.clear_cache()
        
        # Calculate portfolio value
        portfolio_value = await wallet_service.calculate_portfolio_value(
            demo_wallet_address
        )
        
        # Verify result
        assert isinstance(portfolio_value, Decimal)
        assert portfolio_value > 0
    
    @pytest.mark.asyncio
    async def test_portfolio_value_includes_all_assets(
        self, wallet_service, demo_wallet_address, mock_web3, mock_price_oracle
    ):
        """Test that portfolio value includes ETH and all tokens"""
        # Clear cache first
        wallet_service.clear_cache()
        
        # Get balance to see breakdown
        balance = await wallet_service.get_balance(demo_wallet_address)
        
        # Calculate expected total
        expected_total = balance.eth_usd_value + sum(
            token.usd_value for token in balance.token_balances
        )
        
        # Verify total matches
        assert abs(balance.total_value_usd - expected_total) < 0.01
    
    def test_clear_cache_specific_address(
        self, wallet_service, demo_wallet_address
    ):
        """Test clearing cache for specific address"""
        # Add some cache entries
        wallet_service._set_cache(f"balance:{demo_wallet_address.lower()}", {})
        wallet_service._set_cache(f"tokens:{demo_wallet_address.lower()}", {})
        wallet_service._set_cache("balance:0xother", {})
        
        # Clear cache for demo wallet
        wallet_service.clear_cache(demo_wallet_address)
        
        # Demo wallet cache should be cleared
        assert wallet_service._get_cached(f"balance:{demo_wallet_address.lower()}") is None
        assert wallet_service._get_cached(f"tokens:{demo_wallet_address.lower()}") is None
        
        # Other address cache should remain
        assert wallet_service._get_cached("balance:0xother") is not None
    
    def test_clear_cache_all(self, wallet_service):
        """Test clearing all cache"""
        # Add some cache entries
        wallet_service._set_cache("key1", {})
        wallet_service._set_cache("key2", {})
        wallet_service._set_cache("key3", {})
        
        # Clear all cache
        wallet_service.clear_cache()
        
        # All cache should be cleared
        assert len(wallet_service._cache) == 0
    
    @pytest.mark.asyncio
    async def test_get_balance_with_zero_balance(
        self, wallet_service, demo_wallet_address, mock_price_oracle
    ):
        """Test getting balance when wallet has zero balance"""
        with patch('src.services.wallet_service.DEXExecutor') as mock_dex:
            # Mock zero balance
            mock_w3 = Mock()
            mock_w3.eth.get_balance.return_value = 0
            mock_w3.from_wei.return_value = 0.0
            
            mock_token_contract = Mock()
            mock_token_contract.functions.balanceOf.return_value.call.return_value = 0
            mock_w3.eth.contract.return_value = mock_token_contract
            
            mock_dex_instance = Mock()
            mock_dex_instance.w3 = mock_w3
            mock_dex_instance._get_token_address.return_value = '0x0000000000000000000000000000000000000000'
            mock_dex_instance.ERC20_ABI = []
            mock_dex.return_value = mock_dex_instance
            
            # Create new service instance with mock
            service = WalletService()
            
            # Get balance
            balance = await service.get_balance(demo_wallet_address)
            
            # Verify zero balance
            assert balance.eth_balance == "0.0000"
            assert balance.eth_usd_value == 0.0
    
    @pytest.mark.asyncio
    async def test_token_balance_with_different_decimals(
        self, wallet_service, demo_wallet_address, mock_price_oracle
    ):
        """Test that token balances handle different decimal places correctly"""
        # USDC uses 6 decimals, WETH uses 18 decimals
        assert wallet_service.SUPPORTED_TOKENS['USDC']['decimals'] == 6
        assert wallet_service.SUPPORTED_TOKENS['WETH']['decimals'] == 18
    
    @pytest.mark.asyncio
    async def test_error_handling_on_rpc_failure(
        self, wallet_service, demo_wallet_address
    ):
        """Test error handling when RPC call fails"""
        with patch('src.services.wallet_service.DEXExecutor') as mock_dex:
            # Mock RPC failure
            mock_w3 = Mock()
            mock_w3.eth.get_balance.side_effect = Exception("RPC connection failed")
            
            mock_dex_instance = Mock()
            mock_dex_instance.w3 = mock_w3
            mock_dex.return_value = mock_dex_instance
            
            # Create new service instance with mock
            service = WalletService()
            
            # Should raise exception
            with pytest.raises(Exception) as exc_info:
                await service.get_balance(demo_wallet_address)
            
            assert "RPC connection failed" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
