"""
Migration: Create autonomous trading tables
Creates tables for autonomous_trades, portfolio_snapshots, and ai_signals
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from src.config.settings import settings

def upgrade():
    """Create autonomous trading tables"""
    database_url = settings.database_url
    
    # Handle SQLite
    if "sqlite" in database_url:
        engine = create_engine(database_url, connect_args={"check_same_thread": False})
    else:
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        engine = create_engine(database_url)
    
    with engine.connect() as conn:
        # Create autonomous_trades table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS autonomous_trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                wallet_address VARCHAR(42) NOT NULL,
                tx_hash VARCHAR(66) UNIQUE NOT NULL,
                timestamp INTEGER NOT NULL,
                from_token VARCHAR(42) NOT NULL,
                to_token VARCHAR(42) NOT NULL,
                from_token_symbol VARCHAR(20) NOT NULL,
                to_token_symbol VARCHAR(20) NOT NULL,
                from_amount TEXT NOT NULL,
                to_amount TEXT NOT NULL,
                gas_fee TEXT NOT NULL,
                slippage TEXT NOT NULL,
                status VARCHAR(20) NOT NULL,
                trade_type VARCHAR(10) NOT NULL,
                profit_loss TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Create indexes for autonomous_trades
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_autonomous_trades_wallet 
            ON autonomous_trades(wallet_address)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_autonomous_trades_timestamp 
            ON autonomous_trades(timestamp)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_autonomous_trades_status 
            ON autonomous_trades(status)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_autonomous_trades_type 
            ON autonomous_trades(trade_type)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_autonomous_trades_tx_hash 
            ON autonomous_trades(tx_hash)
        """))
        
        # Create wallet_snapshots table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS wallet_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                wallet_address VARCHAR(42) NOT NULL,
                timestamp INTEGER NOT NULL,
                total_value_usd TEXT NOT NULL,
                eth_balance TEXT NOT NULL,
                token_balances TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Create indexes for wallet_snapshots
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_wallet_snapshots_wallet 
            ON wallet_snapshots(wallet_address)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_wallet_snapshots_timestamp 
            ON wallet_snapshots(timestamp)
        """))
        
        # Create ai_signals table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ai_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER NOT NULL,
                action VARCHAR(10) NOT NULL,
                token VARCHAR(42) NOT NULL,
                token_symbol VARCHAR(20) NOT NULL,
                confidence TEXT NOT NULL,
                reason TEXT,
                executed INTEGER DEFAULT 0,
                trade_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (trade_id) REFERENCES autonomous_trades(id)
            )
        """))
        
        # Create indexes for ai_signals
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_ai_signals_timestamp 
            ON ai_signals(timestamp)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_ai_signals_executed 
            ON ai_signals(executed)
        """))
        
        conn.commit()
        print("✓ Autonomous trading tables created successfully")

def downgrade():
    """Drop autonomous trading tables"""
    database_url = settings.database_url
    
    # Handle SQLite
    if "sqlite" in database_url:
        engine = create_engine(database_url, connect_args={"check_same_thread": False})
    else:
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        engine = create_engine(database_url)
    
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS ai_signals"))
        conn.execute(text("DROP TABLE IF EXISTS wallet_snapshots"))
        conn.execute(text("DROP TABLE IF EXISTS autonomous_trades"))
        conn.commit()
        print("✓ Autonomous trading tables dropped successfully")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        downgrade()
    else:
        upgrade()
