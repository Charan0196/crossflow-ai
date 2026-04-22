#!/usr/bin/env python3
"""
Populate CrossFlow AI Database with Sample Data
Adds users, transactions, and other sample data
"""

import sqlite3
import hashlib
import uuid
from datetime import datetime, timedelta
import random
import json

def hash_password(password: str) -> str:
    """Simple password hashing for demo purposes"""
    return hashlib.sha256(password.encode()).hexdigest()

def populate_database():
    """Populate the database with sample data"""
    conn = sqlite3.connect('crossflow.db')
    cursor = conn.cursor()
    
    print("🚀 Populating CrossFlow AI Database...")
    
    # 1. Add Users (with conflict handling)
    print("👥 Adding users...")
    users_data = [
        {
            'email': 'admin@crossflow.ai',
            'username': 'admin',
            'password': 'admin123',
            'full_name': 'System Administrator',
            'is_admin': True,
            'wallet_addresses': json.dumps(['0x742d35Cc6634C0532925a3b8D4C9db96C4b4d4d4'])
        },
        {
            'email': 'charan@crossflow.ai',
            'username': 'charan',
            'password': 'charan123',
            'full_name': 'Charan Kumar',
            'is_admin': False,
            'wallet_addresses': json.dumps(['0x1234567890123456789012345678901234567890', '0x0987654321098765432109876543210987654321'])
        },
        {
            'email': 'santhossh@crossflow.ai',
            'username': 'santhossh',
            'password': 'santhossh123',
            'full_name': 'Santhossh Reddy',
            'is_admin': False,
            'wallet_addresses': json.dumps(['0xabcdefabcdefabcdefabcdefabcdefabcdefabcd', '0x1111222233334444555566667777888899990000'])
        }
    ]
    
    for user in users_data:
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO users (email, username, hashed_password, full_name, is_active, is_admin, wallet_addresses, created_at, last_login)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user['email'],
                user['username'],
                hash_password(user['password']),
                user['full_name'],
                True,
                user['is_admin'],
                user['wallet_addresses'],
                datetime.now(),
                datetime.now() - timedelta(hours=random.randint(1, 24))
            ))
            print(f"   ✅ Added user: {user['username']}")
        except sqlite3.IntegrityError:
            print(f"   ⚠️  User {user['username']} already exists, skipping...")
    
    # Get user IDs
    cursor.execute("SELECT id, username FROM users")
    users = {row[1]: row[0] for row in cursor.fetchall()}
    
    # 2. Add Transactions
    print("💰 Adding transactions...")
    
    # Sample transaction data
    tokens = [
        {'address': '0xA0b86a33E6441c8C06DD2b7c94b7E0e8b8b8b8b8', 'symbol': 'ETH'},
        {'address': '0xdAC17F958D2ee523a2206206994597C13D831ec7', 'symbol': 'USDT'},
        {'address': '0xA0b86a33E6441c8C06DD2b7c94b7E0e8b8b8b8b8', 'symbol': 'USDC'},
        {'address': '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599', 'symbol': 'WBTC'},
        {'address': '0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984', 'symbol': 'UNI'},
    ]
    
    transaction_types = ['swap', 'bridge']
    statuses = ['pending', 'confirmed', 'failed']
    
    for i in range(20):  # Add 20 sample transactions
        user_id = random.choice(list(users.values()))
        from_token = random.choice(tokens)
        to_token = random.choice([t for t in tokens if t != from_token])
        
        tx_hash = f"0x{''.join([f'{random.randint(0, 15):x}' for _ in range(64)])}"
        
        cursor.execute("""
            INSERT INTO transactions (
                user_id, tx_hash, chain_id, block_number, type, status,
                from_token_address, from_token_symbol, from_amount,
                to_token_address, to_token_symbol, to_amount,
                gas_used, gas_price, usd_value, created_at, confirmed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            tx_hash,
            random.choice([1, 137, 42161, 10]),  # Ethereum, Polygon, Arbitrum, Optimism
            random.randint(18000000, 19000000),
            random.choice(transaction_types),
            random.choice(statuses),
            from_token['address'],
            from_token['symbol'],
            round(random.uniform(0.01, 10.0), 6),
            to_token['address'],
            to_token['symbol'],
            round(random.uniform(0.01, 10.0), 6),
            random.randint(21000, 150000),
            random.randint(20, 100) * 1e9,  # Gas price in wei
            round(random.uniform(50, 5000), 2),
            datetime.now() - timedelta(days=random.randint(0, 30)),
            datetime.now() - timedelta(days=random.randint(0, 30)) if random.choice([True, False]) else None
        ))
    
    # 3. Add Transaction Records
    print("📊 Adding transaction records...")
    
    for i in range(15):  # Add 15 detailed transaction records
        user_id = random.choice(list(users.values()))
        from_token = random.choice(tokens)
        to_token = random.choice([t for t in tokens if t != from_token])
        
        tx_hash = f"0x{''.join([f'{random.randint(0, 15):x}' for _ in range(64)])}"
        
        cursor.execute("""
            INSERT INTO transaction_records (
                id, user_id, tx_hash, tx_type, status, chain_id, block_number,
                from_token, to_token, from_token_symbol, to_token_symbol,
                from_amount, to_amount, from_token_price_usd, to_token_price_usd,
                gas_used, gas_price, gas_fee_usd, protocol_fee, total_fee_usd,
                entry_price, realized_pnl, created_at, confirmed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()),
            user_id,
            tx_hash,
            random.choice(['swap', 'bridge']),
            random.choice(['pending', 'confirmed', 'failed']),
            random.choice([1, 137, 42161, 10]),
            random.randint(18000000, 19000000),
            from_token['address'],
            to_token['address'],
            from_token['symbol'],
            to_token['symbol'],
            round(random.uniform(0.1, 5.0), 6),
            round(random.uniform(0.1, 5.0), 6),
            round(random.uniform(1000, 4000), 2),  # Token price
            round(random.uniform(0.5, 2.0), 4),    # Token price
            random.randint(21000, 150000),
            random.randint(20, 100) * 1e9,
            round(random.uniform(5, 50), 2),
            round(random.uniform(0.1, 1.0), 4),
            round(random.uniform(5, 55), 2),
            round(random.uniform(1000, 4000), 2),
            round(random.uniform(-100, 200), 2),  # P&L
            datetime.now() - timedelta(days=random.randint(0, 30)),
            datetime.now() - timedelta(days=random.randint(0, 30)) if random.choice([True, False]) else None
        ))
    
    # 4. Add Orders
    print("📋 Adding orders...")
    
    order_types = ['market', 'limit', 'stop_loss']
    sides = ['buy', 'sell']
    order_statuses = ['pending', 'filled', 'cancelled', 'partially_filled']
    
    for i in range(12):  # Add 12 sample orders
        user_id = random.choice(list(users.values()))
        from_token = random.choice(tokens)
        to_token = random.choice([t for t in tokens if t != from_token])
        
        cursor.execute("""
            INSERT INTO orders (
                id, user_id, order_type, side, status,
                from_token, to_token, from_token_symbol, to_token_symbol,
                amount, filled_amount, price, trigger_price, executed_price,
                chain_id, tx_hash, gas_used, gas_price, protocol_fee, gas_fee,
                created_at, updated_at, filled_at, expires_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()),
            user_id,
            random.choice(order_types),
            random.choice(sides),
            random.choice(order_statuses),
            from_token['address'],
            to_token['address'],
            from_token['symbol'],
            to_token['symbol'],
            round(random.uniform(0.1, 10.0), 6),
            round(random.uniform(0.0, 10.0), 6) if random.choice([True, False]) else None,
            round(random.uniform(1000, 4000), 2),
            round(random.uniform(1000, 4000), 2) if random.choice([True, False]) else None,
            round(random.uniform(1000, 4000), 2) if random.choice([True, False]) else None,
            random.choice([1, 137, 42161, 10]),
            f"0x{''.join([f'{random.randint(0, 15):x}' for _ in range(64)])}" if random.choice([True, False]) else None,
            random.randint(21000, 150000) if random.choice([True, False]) else None,
            random.randint(20, 100) * 1e9 if random.choice([True, False]) else None,
            round(random.uniform(0.1, 1.0), 4),
            round(random.uniform(5, 50), 2),
            datetime.now() - timedelta(days=random.randint(0, 15)),
            datetime.now() - timedelta(days=random.randint(0, 15)),
            datetime.now() - timedelta(days=random.randint(0, 15)) if random.choice([True, False]) else None,
            datetime.now() + timedelta(days=random.randint(1, 30))
        ))
    
    # 5. Add Price Alerts
    print("🔔 Adding price alerts...")
    
    alert_tokens = ['ETH', 'BTC', 'USDT', 'UNI', 'LINK']
    conditions = ['above', 'below']
    
    for i in range(8):  # Add 8 price alerts
        user_id = random.choice(list(users.values()))
        
        cursor.execute("""
            INSERT INTO price_alerts (
                id, user_id, token_symbol, chain_id, target_price, condition,
                is_active, triggered, triggered_at, triggered_price, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()),
            user_id,
            random.choice(alert_tokens),
            random.choice([1, 137, 42161, 10]),
            round(random.uniform(1000, 5000), 2),
            random.choice(conditions),
            random.choice([True, False]),
            random.choice([True, False]),
            datetime.now() - timedelta(days=random.randint(0, 10)) if random.choice([True, False]) else None,
            round(random.uniform(1000, 5000), 2) if random.choice([True, False]) else None,
            datetime.now() - timedelta(days=random.randint(0, 20))
        ))
    
    # 6. Add Trading Preferences
    print("⚙️ Adding trading preferences...")
    
    for username, user_id in users.items():
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO trading_preferences (
                    id, user_id, risk_tolerance, default_slippage, max_slippage,
                    daily_limit, single_trade_limit, mev_protection_enabled,
                    notify_on_fill, notify_on_signal, notify_on_price_alert,
                    favorite_tokens, chart_preferences, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()),
                user_id,
                round(random.uniform(0.1, 1.0), 2),  # Risk tolerance
                round(random.uniform(0.1, 1.0), 2),  # Default slippage
                round(random.uniform(1.0, 5.0), 2),  # Max slippage
                round(random.uniform(1000, 10000), 2),  # Daily limit
                round(random.uniform(100, 1000), 2),   # Single trade limit
                random.choice([True, False]),
                random.choice([True, False]),
                random.choice([True, False]),
                random.choice([True, False]),
                json.dumps(['ETH', 'BTC', 'USDT', 'UNI']),
                json.dumps({'theme': 'dark', 'indicators': ['RSI', 'MACD'], 'timeframe': '1h'}),
                datetime.now() - timedelta(days=random.randint(0, 30)),
                datetime.now() - timedelta(days=random.randint(0, 5))
            ))
            print(f"   ✅ Added preferences for: {username}")
        except sqlite3.IntegrityError:
            print(f"   ⚠️  Preferences for {username} already exist, skipping...")
    
    # 7. Add Portfolios
    print("💼 Adding portfolios...")
    
    portfolio_tokens = [
        {'address': '0xA0b86a33E6441c8C06DD2b7c94b7E0e8b8b8b8b8', 'symbol': 'ETH', 'name': 'Ethereum', 'decimals': 18},
        {'address': '0xdAC17F958D2ee523a2206206994597C13D831ec7', 'symbol': 'USDT', 'name': 'Tether USD', 'decimals': 6},
        {'address': '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599', 'symbol': 'WBTC', 'name': 'Wrapped Bitcoin', 'decimals': 8},
        {'address': '0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984', 'symbol': 'UNI', 'name': 'Uniswap', 'decimals': 18},
    ]
    
    for username, user_id in users.items():
        for token in portfolio_tokens:
            if random.choice([True, False]):  # Randomly add tokens to portfolios
                cursor.execute("""
                    INSERT INTO portfolios (
                        user_id, chain_id, token_address, token_symbol, token_name,
                        token_decimals, balance, usd_value, last_updated
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    random.choice([1, 137, 42161, 10]),
                    token['address'],
                    token['symbol'],
                    token['name'],
                    token['decimals'],
                    round(random.uniform(0.1, 100.0), 6),
                    round(random.uniform(100, 10000), 2),
                    datetime.now() - timedelta(hours=random.randint(1, 48))
                ))
    
    # 8. Add Wallet Snapshots
    print("📸 Adding wallet snapshots...")
    
    sample_wallets = [
        '0x742d35Cc6634C0532925a3b8D4C9db96C4b4d4d4',
        '0x1234567890123456789012345678901234567890',
        '0xabcdefabcdefabcdefabcdefabcdefabcdefabcd'
    ]
    
    for i in range(10):  # Add 10 wallet snapshots
        cursor.execute("""
            INSERT INTO wallet_snapshots (
                wallet_address, timestamp, total_value_usd, eth_balance, token_balances, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            random.choice(sample_wallets),
            int((datetime.now() - timedelta(days=random.randint(0, 30))).timestamp()),
            round(random.uniform(1000, 50000), 2),
            round(random.uniform(0.1, 10.0), 6),
            json.dumps({
                'USDT': round(random.uniform(100, 5000), 2),
                'USDC': round(random.uniform(100, 3000), 2),
                'UNI': round(random.uniform(10, 500), 2),
                'WBTC': round(random.uniform(0.01, 1.0), 4)
            }),
            datetime.now() - timedelta(days=random.randint(0, 30))
        ))
    
    # Commit all changes
    conn.commit()
    conn.close()
    
    print("✅ Database populated successfully!")
    print("\n📊 Summary:")
    print(f"   👥 Users: 3 (admin, charan, santhossh)")
    print(f"   💰 Transactions: 20")
    print(f"   📊 Transaction Records: 15")
    print(f"   📋 Orders: 12")
    print(f"   🔔 Price Alerts: 8")
    print(f"   ⚙️ Trading Preferences: 3")
    print(f"   💼 Portfolio Entries: ~12")
    print(f"   📸 Wallet Snapshots: 10")
    
    print("\n🔐 Login Credentials:")
    print("   admin / admin123 (Administrator)")
    print("   charan / charan123 (User)")
    print("   santhossh / santhossh123 (User)")

if __name__ == "__main__":
    populate_database()