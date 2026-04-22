"""
Phase 5: Transaction History Service

Tracks all transactions with:
- Complete transaction details
- Explorer URLs for each chain
- P&L calculation
- CSV export
"""

import csv
import io
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from decimal import Decimal
from enum import Enum
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


class TransactionType(str, Enum):
    SWAP = "swap"
    BRIDGE = "bridge"
    LIMIT_ORDER = "limit_order"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"


@dataclass
class TransactionRecord:
    id: str
    user_address: str
    tx_hash: str
    chain_id: int
    tx_type: TransactionType
    from_token: str
    to_token: str
    from_amount: Decimal
    to_amount: Decimal
    from_price_usd: Decimal
    to_price_usd: Decimal
    gas_used: int
    gas_price_gwei: Decimal
    gas_cost_usd: Decimal
    timestamp: datetime
    status: str
    explorer_url: str
    metadata: Dict[str, Any]


CHAIN_EXPLORERS = {
    1: "https://etherscan.io",
    137: "https://polygonscan.com",
    42161: "https://arbiscan.io",
    10: "https://optimistic.etherscan.io",
    56: "https://bscscan.com",
    43114: "https://snowtrace.io",
    8453: "https://basescan.org",
    324: "https://explorer.zksync.io",
}


class TransactionHistoryService:
    def __init__(self):
        self.transactions: Dict[str, TransactionRecord] = {}
        self.user_transactions: Dict[str, List[str]] = {}
    
    def get_explorer_url(self, chain_id: int, tx_hash: str) -> str:
        base_url = CHAIN_EXPLORERS.get(chain_id, "https://etherscan.io")
        return f"{base_url}/tx/{tx_hash}"
    
    async def record_transaction(
        self,
        user_address: str,
        tx_hash: str,
        chain_id: int,
        tx_type: TransactionType,
        from_token: str,
        to_token: str,
        from_amount: Decimal,
        to_amount: Decimal,
        from_price_usd: Decimal,
        to_price_usd: Decimal,
        gas_used: int = 0,
        gas_price_gwei: Decimal = Decimal("0"),
        gas_cost_usd: Decimal = Decimal("0"),
        status: str = "confirmed",
        metadata: Optional[Dict[str, Any]] = None
    ) -> TransactionRecord:
        """Record a new transaction."""
        tx_id = f"{chain_id}_{tx_hash}"
        
        record = TransactionRecord(
            id=tx_id,
            user_address=user_address.lower(),
            tx_hash=tx_hash,
            chain_id=chain_id,
            tx_type=tx_type,
            from_token=from_token,
            to_token=to_token,
            from_amount=from_amount,
            to_amount=to_amount,
            from_price_usd=from_price_usd,
            to_price_usd=to_price_usd,
            gas_used=gas_used,
            gas_price_gwei=gas_price_gwei,
            gas_cost_usd=gas_cost_usd,
            timestamp=datetime.utcnow(),
            status=status,
            explorer_url=self.get_explorer_url(chain_id, tx_hash),
            metadata=metadata or {}
        )
        
        self.transactions[tx_id] = record
        
        user_key = user_address.lower()
        if user_key not in self.user_transactions:
            self.user_transactions[user_key] = []
        self.user_transactions[user_key].append(tx_id)
        
        logger.info(f"Recorded transaction {tx_id} for user {user_address}")
        return record
    
    async def get_user_transactions(
        self,
        user_address: str,
        tx_type: Optional[TransactionType] = None,
        chain_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[TransactionRecord]:
        """Get transactions for a user with optional filters."""
        user_key = user_address.lower()
        tx_ids = self.user_transactions.get(user_key, [])
        
        records = []
        for tx_id in tx_ids:
            record = self.transactions.get(tx_id)
            if not record:
                continue
            
            if tx_type and record.tx_type != tx_type:
                continue
            if chain_id and record.chain_id != chain_id:
                continue
            if start_date and record.timestamp < start_date:
                continue
            if end_date and record.timestamp > end_date:
                continue
            
            records.append(record)
        
        records.sort(key=lambda x: x.timestamp, reverse=True)
        return records[offset:offset + limit]
    
    async def calculate_pnl(
        self,
        user_address: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Calculate P&L for a user's transactions."""
        transactions = await self.get_user_transactions(
            user_address, start_date=start_date, end_date=end_date, limit=10000
        )
        
        total_value_in = Decimal("0")
        total_value_out = Decimal("0")
        total_gas_cost = Decimal("0")
        trades_by_token: Dict[str, Dict[str, Decimal]] = {}
        
        for tx in transactions:
            value_in = tx.from_amount * tx.from_price_usd
            value_out = tx.to_amount * tx.to_price_usd
            
            total_value_in += value_in
            total_value_out += value_out
            total_gas_cost += tx.gas_cost_usd
            
            # Track by token
            if tx.from_token not in trades_by_token:
                trades_by_token[tx.from_token] = {"sold": Decimal("0"), "bought": Decimal("0")}
            if tx.to_token not in trades_by_token:
                trades_by_token[tx.to_token] = {"sold": Decimal("0"), "bought": Decimal("0")}
            
            trades_by_token[tx.from_token]["sold"] += value_in
            trades_by_token[tx.to_token]["bought"] += value_out
        
        gross_pnl = total_value_out - total_value_in
        net_pnl = gross_pnl - total_gas_cost
        
        return {
            "total_trades": len(transactions),
            "total_value_in_usd": float(total_value_in),
            "total_value_out_usd": float(total_value_out),
            "total_gas_cost_usd": float(total_gas_cost),
            "gross_pnl_usd": float(gross_pnl),
            "net_pnl_usd": float(net_pnl),
            "pnl_percentage": float(gross_pnl / total_value_in * 100) if total_value_in > 0 else 0,
            "trades_by_token": {
                token: {"sold_usd": float(data["sold"]), "bought_usd": float(data["bought"])}
                for token, data in trades_by_token.items()
            }
        }
    
    async def export_csv(
        self,
        user_address: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> str:
        """Export transactions to CSV format."""
        transactions = await self.get_user_transactions(
            user_address, start_date=start_date, end_date=end_date, limit=10000
        )
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            "Date", "Time", "Type", "Chain", "From Token", "From Amount",
            "To Token", "To Amount", "From Price USD", "To Price USD",
            "Value USD", "Gas Cost USD", "TX Hash", "Explorer URL", "Status"
        ])
        
        for tx in transactions:
            value_usd = float(tx.from_amount * tx.from_price_usd)
            writer.writerow([
                tx.timestamp.strftime("%Y-%m-%d"),
                tx.timestamp.strftime("%H:%M:%S"),
                tx.tx_type.value,
                tx.chain_id,
                tx.from_token,
                float(tx.from_amount),
                tx.to_token,
                float(tx.to_amount),
                float(tx.from_price_usd),
                float(tx.to_price_usd),
                value_usd,
                float(tx.gas_cost_usd),
                tx.tx_hash,
                tx.explorer_url,
                tx.status
            ])
        
        return output.getvalue()


# Singleton instance
transaction_history_service = TransactionHistoryService()
