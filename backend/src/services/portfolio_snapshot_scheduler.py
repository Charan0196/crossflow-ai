"""
Portfolio Snapshot Scheduler

Creates daily snapshots of portfolio values for historical tracking
"""

import asyncio
import logging
from datetime import datetime, time, timedelta
from typing import Optional

from src.config.database import get_db
from src.services.wallet_service import wallet_service

logger = logging.getLogger(__name__)


class PortfolioSnapshotScheduler:
    """
    Scheduler for creating daily portfolio snapshots
    """
    
    def __init__(self):
        self.is_running = False
        self.task: Optional[asyncio.Task] = None
        self.snapshot_time = time(23, 59)  # End of day snapshot
    
    async def start(self):
        """Start the scheduler"""
        if self.is_running:
            logger.warning("Portfolio snapshot scheduler already running")
            return
        
        self.is_running = True
        self.task = asyncio.create_task(self._run_scheduler())
        logger.info("Portfolio snapshot scheduler started")
    
    async def stop(self):
        """Stop the scheduler"""
        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Portfolio snapshot scheduler stopped")
    
    async def _run_scheduler(self):
        """Main scheduler loop"""
        while self.is_running:
            try:
                # Calculate time until next snapshot
                now = datetime.utcnow()
                next_snapshot = datetime.combine(now.date(), self.snapshot_time)
                
                # If we've passed today's snapshot time, schedule for tomorrow
                if now.time() > self.snapshot_time:
                    next_snapshot += timedelta(days=1)
                
                # Wait until snapshot time
                wait_seconds = (next_snapshot - now).total_seconds()
                logger.info(f"Next portfolio snapshot in {wait_seconds/3600:.1f} hours")
                
                await asyncio.sleep(wait_seconds)
                
                # Create snapshots for all wallets
                await self.create_snapshots()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in portfolio snapshot scheduler: {e}")
                # Wait 1 hour before retrying
                await asyncio.sleep(3600)
    
    async def create_snapshots(self):
        """Create portfolio snapshots for all wallets"""
        try:
            db = next(get_db())
            
            # Get all unique wallet addresses from trades
            cursor = db.execute("""
                SELECT DISTINCT wallet_address 
                FROM autonomous_trades 
                WHERE wallet_address IS NOT NULL
            """)
            
            wallets = [row[0] for row in cursor.fetchall()]
            
            logger.info(f"Creating portfolio snapshots for {len(wallets)} wallets")
            
            for wallet_address in wallets:
                try:
                    await self.create_snapshot(wallet_address)
                except Exception as e:
                    logger.error(f"Failed to create snapshot for {wallet_address}: {e}")
            
            logger.info("Portfolio snapshots created successfully")
            
        except Exception as e:
            logger.error(f"Error creating portfolio snapshots: {e}")
    
    async def create_snapshot(self, wallet_address: str):
        """Create a snapshot for a specific wallet"""
        try:
            # Calculate portfolio value
            portfolio_value = await wallet_service.calculate_portfolio_value(wallet_address)
            
            # Store snapshot in database
            db = next(get_db())
            db.execute("""
                INSERT INTO portfolio_snapshots (
                    wallet_address, total_value, timestamp
                ) VALUES (?, ?, ?)
            """, (
                wallet_address,
                float(portfolio_value),
                datetime.utcnow().isoformat()
            ))
            db.commit()
            
            logger.info(f"Created snapshot for {wallet_address}: ${portfolio_value}")
            
        except Exception as e:
            logger.error(f"Error creating snapshot for {wallet_address}: {e}")
            raise
    
    async def get_snapshots(
        self, 
        wallet_address: str, 
        days: int = 30
    ) -> list:
        """Get historical snapshots for a wallet"""
        try:
            db = next(get_db())
            
            cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
            
            cursor = db.execute("""
                SELECT wallet_address, total_value, timestamp
                FROM portfolio_snapshots
                WHERE wallet_address = ? AND timestamp >= ?
                ORDER BY timestamp DESC
            """, (wallet_address, cutoff_date))
            
            snapshots = []
            for row in cursor.fetchall():
                snapshots.append({
                    "wallet_address": row[0],
                    "total_value": row[1],
                    "timestamp": row[2]
                })
            
            return snapshots
            
        except Exception as e:
            logger.error(f"Error fetching snapshots: {e}")
            return []


# Global scheduler instance
portfolio_snapshot_scheduler = PortfolioSnapshotScheduler()
