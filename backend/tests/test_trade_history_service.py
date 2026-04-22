"""
Unit tests for TradeHistoryService
Tests trade recording, retrieval, filtering, pagination, and status updates.
"""
import pytest
import time
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.services.trade_history_service import (
    TradeHistoryService,
    TradeFilters,
    PaginatedTrades
)
from src.models.trading import AutonomousTrade
from src.config.database import Base


# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def db_session():
    """Create a test database session"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
def service(db_session):
    """Create TradeHistoryService instance with test database"""
    return TradeHistoryService(db_session=db_session)


@pytest.fixture
def sample_trade_data():
    """Sample trade data for testing"""
    return {
        'wallet_address': '0x6739659248061A54E0f4de8f2cd60278B69468b3',
        'tx_hash': '0xabc123def456',
        'timestamp': int(time.time()),
        'from_token': '0x0000000000000000000000000000000000000000',
        'to_token': '0x1111111111111111111111111111111111111111',
        'from_token_symbol': 'ETH',
        'to_token_symbol': 'USDC',
        'from_amount': '0.1',
        'to_amount': '250.00',
        'gas_fee': '0.002',
        'slippage': '0.5',
        'status': 'pending',
        'trade_type': 'manual',
        'profit_loss': None
    }


# Test: record_trade
@pytest.mark.asyncio
async def test_record_trade_success(service, sample_trade_data):
    """Test successful trade recording"""
    tx_hash = await service.record_trade(sample_trade_data)
    
    assert tx_hash == sample_trade_data['tx_hash']
    
    # Verify trade was stored
    trade = await service.get_trade_by_hash(tx_hash)
    assert trade is not None
    assert trade['wallet_address'] == sample_trade_data['wallet_address']
    assert trade['from_token_symbol'] == 'ETH'
    assert trade['to_token_symbol'] == 'USDC'
    assert trade['status'] == 'pending'
    assert trade['trade_type'] == 'manual'


@pytest.mark.asyncio
async def test_record_trade_with_profit_loss(service, sample_trade_data):
    """Test recording trade with profit/loss"""
    sample_trade_data['profit_loss'] = '5.23'
    tx_hash = await service.record_trade(sample_trade_data)
    
    trade = await service.get_trade_by_hash(tx_hash)
    assert trade['profit_loss'] == '5.23'


@pytest.mark.asyncio
async def test_record_trade_missing_fields(service):
    """Test recording trade with missing required fields"""
    incomplete_data = {
        'wallet_address': '0x123',
        'tx_hash': '0xabc'
        # Missing other required fields
    }
    
    with pytest.raises(ValueError, match="Missing required fields"):
        await service.record_trade(incomplete_data)


@pytest.mark.asyncio
async def test_record_trade_decimal_conversion(service, sample_trade_data):
    """Test that string amounts are properly converted to Decimal"""
    tx_hash = await service.record_trade(sample_trade_data)
    
    trade = await service.get_trade_by_hash(tx_hash)
    # Verify amounts are stored correctly
    assert trade['from_amount'] == '0.100000000000000000'  # 18 decimals
    assert trade['to_amount'] == '250.000000000000000000'


# Test: get_trade_by_hash
@pytest.mark.asyncio
async def test_get_trade_by_hash_found(service, sample_trade_data):
    """Test retrieving trade by hash when it exists"""
    tx_hash = await service.record_trade(sample_trade_data)
    
    trade = await service.get_trade_by_hash(tx_hash)
    assert trade is not None
    assert trade['tx_hash'] == tx_hash


@pytest.mark.asyncio
async def test_get_trade_by_hash_not_found(service):
    """Test retrieving trade by hash when it doesn't exist"""
    trade = await service.get_trade_by_hash('0xnonexistent')
    assert trade is None


# Test: update_trade_status
@pytest.mark.asyncio
async def test_update_trade_status_success(service, sample_trade_data):
    """Test successful status update"""
    tx_hash = await service.record_trade(sample_trade_data)
    
    # Update status to confirmed
    result = await service.update_trade_status(tx_hash, 'confirmed')
    assert result is True
    
    # Verify update
    trade = await service.get_trade_by_hash(tx_hash)
    assert trade['status'] == 'confirmed'


@pytest.mark.asyncio
async def test_update_trade_status_with_profit_loss(service, sample_trade_data):
    """Test updating status with profit/loss"""
    tx_hash = await service.record_trade(sample_trade_data)
    
    profit_loss = Decimal('10.50')
    result = await service.update_trade_status(tx_hash, 'confirmed', profit_loss)
    assert result is True
    
    trade = await service.get_trade_by_hash(tx_hash)
    assert trade['status'] == 'confirmed'
    assert trade['profit_loss'] == '10.50'


@pytest.mark.asyncio
async def test_update_trade_status_invalid_status(service, sample_trade_data):
    """Test updating with invalid status"""
    tx_hash = await service.record_trade(sample_trade_data)
    
    with pytest.raises(ValueError, match="Invalid status"):
        await service.update_trade_status(tx_hash, 'invalid_status')


@pytest.mark.asyncio
async def test_update_trade_status_not_found(service):
    """Test updating status for non-existent trade"""
    result = await service.update_trade_status('0xnonexistent', 'confirmed')
    assert result is False


# Test: get_trades with pagination
@pytest.mark.asyncio
async def test_get_trades_empty(service):
    """Test getting trades when none exist"""
    result = await service.get_trades('0x123', page=1, page_size=20)
    
    assert isinstance(result, PaginatedTrades)
    assert result.total == 0
    assert len(result.trades) == 0
    assert result.page == 1
    assert result.total_pages == 0


@pytest.mark.asyncio
async def test_get_trades_pagination(service, sample_trade_data):
    """Test pagination with multiple trades"""
    address = sample_trade_data['wallet_address']
    
    # Create 25 trades
    for i in range(25):
        trade_data = sample_trade_data.copy()
        trade_data['tx_hash'] = f'0xhash{i:03d}'
        trade_data['timestamp'] = int(time.time()) + i
        await service.record_trade(trade_data)
    
    # Get first page (20 trades)
    page1 = await service.get_trades(address, page=1, page_size=20)
    assert page1.total == 25
    assert len(page1.trades) == 20
    assert page1.page == 1
    assert page1.total_pages == 2
    
    # Get second page (5 trades)
    page2 = await service.get_trades(address, page=2, page_size=20)
    assert page2.total == 25
    assert len(page2.trades) == 5
    assert page2.page == 2


@pytest.mark.asyncio
async def test_get_trades_ordering(service, sample_trade_data):
    """Test that trades are ordered by timestamp descending (newest first)"""
    address = sample_trade_data['wallet_address']
    
    # Create trades with different timestamps
    timestamps = [1000, 2000, 3000]
    for i, ts in enumerate(timestamps):
        trade_data = sample_trade_data.copy()
        trade_data['tx_hash'] = f'0xhash{i}'
        trade_data['timestamp'] = ts
        await service.record_trade(trade_data)
    
    result = await service.get_trades(address, page=1, page_size=10)
    
    # Verify newest first
    assert result.trades[0]['timestamp'] == 3000
    assert result.trades[1]['timestamp'] == 2000
    assert result.trades[2]['timestamp'] == 1000


@pytest.mark.asyncio
async def test_get_trades_invalid_page(service):
    """Test invalid page number"""
    with pytest.raises(ValueError, match="Page must be >= 1"):
        await service.get_trades('0x123', page=0, page_size=20)


@pytest.mark.asyncio
async def test_get_trades_invalid_page_size(service):
    """Test invalid page size"""
    with pytest.raises(ValueError, match="Page size must be between 1 and 100"):
        await service.get_trades('0x123', page=1, page_size=0)
    
    with pytest.raises(ValueError, match="Page size must be between 1 and 100"):
        await service.get_trades('0x123', page=1, page_size=101)


# Test: filtering
@pytest.mark.asyncio
async def test_filter_by_token(service, sample_trade_data):
    """Test filtering trades by token symbol"""
    address = sample_trade_data['wallet_address']
    
    # Create trades with different tokens
    for i, (from_token, to_token) in enumerate([('ETH', 'USDC'), ('USDC', 'DAI'), ('ETH', 'DAI')]):
        trade_data = sample_trade_data.copy()
        trade_data['tx_hash'] = f'0xhash{i}'
        trade_data['from_token_symbol'] = from_token
        trade_data['to_token_symbol'] = to_token
        await service.record_trade(trade_data)
    
    # Filter by ETH (should match trades where ETH is from_token or to_token)
    filters = TradeFilters(token='ETH')
    result = await service.get_trades(address, filters=filters, page=1, page_size=10)
    
    assert result.total == 2
    assert len(result.trades) == 2


@pytest.mark.asyncio
async def test_filter_by_trade_type(service, sample_trade_data):
    """Test filtering trades by trade type"""
    address = sample_trade_data['wallet_address']
    
    # Create manual and AI trades
    for i, trade_type in enumerate(['manual', 'ai_executed', 'manual']):
        trade_data = sample_trade_data.copy()
        trade_data['tx_hash'] = f'0xhash{i}'
        trade_data['trade_type'] = trade_type
        await service.record_trade(trade_data)
    
    # Filter by manual trades
    filters = TradeFilters(trade_type='manual')
    result = await service.get_trades(address, filters=filters, page=1, page_size=10)
    
    assert result.total == 2
    assert all(t['trade_type'] == 'manual' for t in result.trades)


@pytest.mark.asyncio
async def test_filter_by_status(service, sample_trade_data):
    """Test filtering trades by status"""
    address = sample_trade_data['wallet_address']
    
    # Create trades with different statuses
    for i, status in enumerate(['pending', 'confirmed', 'failed', 'confirmed']):
        trade_data = sample_trade_data.copy()
        trade_data['tx_hash'] = f'0xhash{i}'
        trade_data['status'] = status
        await service.record_trade(trade_data)
    
    # Filter by confirmed trades
    filters = TradeFilters(status='confirmed')
    result = await service.get_trades(address, filters=filters, page=1, page_size=10)
    
    assert result.total == 2
    assert all(t['status'] == 'confirmed' for t in result.trades)


@pytest.mark.asyncio
async def test_filter_by_date_range(service, sample_trade_data):
    """Test filtering trades by date range"""
    address = sample_trade_data['wallet_address']
    
    # Create trades with different timestamps
    base_time = 1000000
    for i in range(5):
        trade_data = sample_trade_data.copy()
        trade_data['tx_hash'] = f'0xhash{i}'
        trade_data['timestamp'] = base_time + (i * 1000)
        await service.record_trade(trade_data)
    
    # Filter by date range (middle 3 trades)
    filters = TradeFilters(
        start_date=base_time + 1000,
        end_date=base_time + 3000
    )
    result = await service.get_trades(address, filters=filters, page=1, page_size=10)
    
    assert result.total == 3
    for trade in result.trades:
        assert base_time + 1000 <= trade['timestamp'] <= base_time + 3000


@pytest.mark.asyncio
async def test_filter_multiple_criteria(service, sample_trade_data):
    """Test filtering with multiple criteria combined"""
    address = sample_trade_data['wallet_address']
    
    # Create various trades
    trades_config = [
        {'token': 'ETH', 'type': 'manual', 'status': 'confirmed', 'time': 1000},
        {'token': 'USDC', 'type': 'ai_executed', 'status': 'confirmed', 'time': 2000},
        {'token': 'ETH', 'type': 'manual', 'status': 'pending', 'time': 3000},
        {'token': 'ETH', 'type': 'manual', 'status': 'confirmed', 'time': 4000},
    ]
    
    for i, config in enumerate(trades_config):
        trade_data = sample_trade_data.copy()
        trade_data['tx_hash'] = f'0xhash{i}'
        trade_data['from_token_symbol'] = config['token']
        trade_data['trade_type'] = config['type']
        trade_data['status'] = config['status']
        trade_data['timestamp'] = config['time']
        await service.record_trade(trade_data)
    
    # Filter: ETH + manual + confirmed
    filters = TradeFilters(
        token='ETH',
        trade_type='manual',
        status='confirmed'
    )
    result = await service.get_trades(address, filters=filters, page=1, page_size=10)
    
    assert result.total == 2
    for trade in result.trades:
        assert trade['from_token_symbol'] == 'ETH'
        assert trade['trade_type'] == 'manual'
        assert trade['status'] == 'confirmed'


# Test: get_trade_count
@pytest.mark.asyncio
async def test_get_trade_count(service, sample_trade_data):
    """Test getting trade count"""
    address = sample_trade_data['wallet_address']
    
    # Initially zero
    count = await service.get_trade_count(address)
    assert count == 0
    
    # Add trades
    for i in range(5):
        trade_data = sample_trade_data.copy()
        trade_data['tx_hash'] = f'0xhash{i}'
        await service.record_trade(trade_data)
    
    count = await service.get_trade_count(address)
    assert count == 5


@pytest.mark.asyncio
async def test_get_trade_count_with_filters(service, sample_trade_data):
    """Test getting trade count with filters"""
    address = sample_trade_data['wallet_address']
    
    # Create trades
    for i in range(3):
        trade_data = sample_trade_data.copy()
        trade_data['tx_hash'] = f'0xhash{i}'
        trade_data['trade_type'] = 'manual' if i < 2 else 'ai_executed'
        await service.record_trade(trade_data)
    
    # Count manual trades
    filters = TradeFilters(trade_type='manual')
    count = await service.get_trade_count(address, filters=filters)
    assert count == 2


# Test: PaginatedTrades.to_dict
def test_paginated_trades_to_dict():
    """Test PaginatedTrades serialization"""
    trades = [{'id': 1}, {'id': 2}]
    paginated = PaginatedTrades(trades=trades, total=25, page=2, page_size=20)
    
    result = paginated.to_dict()
    
    assert result['trades'] == trades
    assert result['total'] == 25
    assert result['page'] == 2
    assert result['page_size'] == 20
    assert result['total_pages'] == 2


# Test: Edge cases
@pytest.mark.asyncio
async def test_empty_filters(service, sample_trade_data):
    """Test that empty filters return all trades"""
    address = sample_trade_data['wallet_address']
    
    # Create trades
    for i in range(3):
        trade_data = sample_trade_data.copy()
        trade_data['tx_hash'] = f'0xhash{i}'
        await service.record_trade(trade_data)
    
    # Empty filters should return all
    filters = TradeFilters()
    result = await service.get_trades(address, filters=filters, page=1, page_size=10)
    assert result.total == 3


@pytest.mark.asyncio
async def test_different_wallet_addresses(service, sample_trade_data):
    """Test that trades are properly isolated by wallet address"""
    address1 = '0x1111111111111111111111111111111111111111'
    address2 = '0x2222222222222222222222222222222222222222'
    
    # Create trades for address1
    for i in range(3):
        trade_data = sample_trade_data.copy()
        trade_data['wallet_address'] = address1
        trade_data['tx_hash'] = f'0xhash1_{i}'
        await service.record_trade(trade_data)
    
    # Create trades for address2
    for i in range(2):
        trade_data = sample_trade_data.copy()
        trade_data['wallet_address'] = address2
        trade_data['tx_hash'] = f'0xhash2_{i}'
        await service.record_trade(trade_data)
    
    # Verify isolation
    result1 = await service.get_trades(address1, page=1, page_size=10)
    assert result1.total == 3
    
    result2 = await service.get_trades(address2, page=1, page_size=10)
    assert result2.total == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
