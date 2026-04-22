#!/usr/bin/env python3
"""
CrossFlow AI Database Browser
Simple CLI tool to explore the SQLite database
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any

class DatabaseBrowser:
    def __init__(self, db_path: str = "crossflow.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # Enable column access by name
        
    def get_tables(self) -> List[str]:
        """Get all table names"""
        cursor = self.conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        return [row[0] for row in cursor.fetchall()]
    
    def get_table_info(self, table_name: str) -> List[Dict]:
        """Get column information for a table"""
        cursor = self.conn.execute(f"PRAGMA table_info({table_name})")
        return [dict(row) for row in cursor.fetchall()]
    
    def get_table_count(self, table_name: str) -> int:
        """Get row count for a table"""
        cursor = self.conn.execute(f"SELECT COUNT(*) FROM {table_name}")
        return cursor.fetchone()[0]
    
    def query_table(self, table_name: str, limit: int = 10, order_by: str = None) -> List[Dict]:
        """Query table with optional ordering and limit"""
        query = f"SELECT * FROM {table_name}"
        if order_by:
            query += f" ORDER BY {order_by} DESC"
        query += f" LIMIT {limit}"
        
        cursor = self.conn.execute(query)
        return [dict(row) for row in cursor.fetchall()]
    
    def execute_query(self, query: str) -> List[Dict]:
        """Execute custom SQL query"""
        cursor = self.conn.execute(query)
        return [dict(row) for row in cursor.fetchall()]
    
    def show_database_summary(self):
        """Show a summary of the database"""
        print("=" * 60)
        print("CROSSFLOW AI DATABASE SUMMARY")
        print("=" * 60)
        
        tables = self.get_tables()
        print(f"Total Tables: {len(tables)}\n")
        
        for table in tables:
            count = self.get_table_count(table)
            print(f"📊 {table:<25} {count:>8} rows")
        
        print("\n" + "=" * 60)
    
    def show_table_details(self, table_name: str):
        """Show detailed information about a table"""
        print(f"\n📋 TABLE: {table_name}")
        print("-" * 50)
        
        # Show schema
        columns = self.get_table_info(table_name)
        print("COLUMNS:")
        for col in columns:
            pk = " (PK)" if col['pk'] else ""
            notnull = " NOT NULL" if col['notnull'] else ""
            print(f"  • {col['name']:<20} {col['type']:<15}{pk}{notnull}")
        
        # Show row count
        count = self.get_table_count(table_name)
        print(f"\nROW COUNT: {count}")
        
        # Show sample data
        if count > 0:
            print(f"\nSAMPLE DATA (last 5 rows):")
            try:
                # Try to order by common timestamp columns
                order_cols = ['created_at', 'timestamp', 'updated_at', 'id']
                order_by = None
                for col in order_cols:
                    if any(c['name'] == col for c in columns):
                        order_by = col
                        break
                
                rows = self.query_table(table_name, limit=5, order_by=order_by)
                for i, row in enumerate(rows, 1):
                    print(f"\n  Row {i}:")
                    for key, value in row.items():
                        if isinstance(value, str) and len(value) > 50:
                            value = value[:47] + "..."
                        print(f"    {key}: {value}")
            except Exception as e:
                print(f"    Error fetching sample data: {e}")
    
    def show_ai_signals_analysis(self):
        """Show analysis of AI signals"""
        print("\n🤖 AI SIGNALS ANALYSIS")
        print("-" * 40)
        
        # Signal counts by action
        query = "SELECT action, COUNT(*) as count FROM ai_signals GROUP BY action"
        results = self.execute_query(query)
        print("Signals by Action:")
        for row in results:
            print(f"  {row['action'].upper()}: {row['count']}")
        
        # Average confidence
        query = "SELECT AVG(confidence) as avg_confidence FROM ai_signals"
        result = self.execute_query(query)[0]
        print(f"\nAverage Confidence: {result['avg_confidence']:.1f}%")
        
        # Recent signals
        query = "SELECT token_symbol, action, confidence, reason FROM ai_signals ORDER BY timestamp DESC LIMIT 3"
        results = self.execute_query(query)
        print(f"\nRecent Signals:")
        for row in results:
            print(f"  {row['token_symbol']}: {row['action'].upper()} ({row['confidence']:.1f}%)")
            print(f"    Reason: {row['reason'][:60]}...")
    
    def show_trading_analysis(self):
        """Show trading performance analysis"""
        print("\n📈 TRADING ANALYSIS")
        print("-" * 40)
        
        # Mock trades summary
        query = """
        SELECT 
            COUNT(*) as total_trades,
            SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as winning_trades,
            SUM(CASE WHEN profit_loss < 0 THEN 1 ELSE 0 END) as losing_trades,
            AVG(profit_loss) as avg_pnl,
            SUM(profit_loss) as total_pnl
        FROM mock_trades 
        WHERE profit_loss IS NOT NULL
        """
        result = self.execute_query(query)[0]
        
        if result['total_trades'] > 0:
            win_rate = (result['winning_trades'] / result['total_trades']) * 100
            print(f"Total Trades: {result['total_trades']}")
            print(f"Winning Trades: {result['winning_trades']}")
            print(f"Losing Trades: {result['losing_trades']}")
            print(f"Win Rate: {win_rate:.1f}%")
            print(f"Average P&L: ${result['avg_pnl']:.2f}")
            print(f"Total P&L: ${result['total_pnl']:.2f}")
        else:
            print("No completed trades with P&L data")
        
        # Top performing tokens
        query = """
        SELECT token, COUNT(*) as trades, AVG(profit_loss) as avg_pnl
        FROM mock_trades 
        WHERE profit_loss IS NOT NULL
        GROUP BY token
        ORDER BY avg_pnl DESC
        LIMIT 5
        """
        results = self.execute_query(query)
        if results:
            print(f"\nTop Performing Tokens:")
            for row in results:
                print(f"  {row['token']}: {row['trades']} trades, ${row['avg_pnl']:.2f} avg P&L")
    
    def interactive_mode(self):
        """Interactive database browser"""
        print("\n🔍 INTERACTIVE DATABASE BROWSER")
        print("Commands: tables, info <table>, query <sql>, signals, trading, summary, quit")
        
        while True:
            try:
                command = input("\ndb> ").strip().lower()
                
                if command == 'quit' or command == 'exit':
                    break
                elif command == 'tables':
                    tables = self.get_tables()
                    print("Available tables:")
                    for table in tables:
                        count = self.get_table_count(table)
                        print(f"  • {table} ({count} rows)")
                elif command.startswith('info '):
                    table_name = command[5:].strip()
                    if table_name in self.get_tables():
                        self.show_table_details(table_name)
                    else:
                        print(f"Table '{table_name}' not found")
                elif command.startswith('query '):
                    sql = command[6:].strip()
                    try:
                        results = self.execute_query(sql)
                        if results:
                            for i, row in enumerate(results[:10], 1):  # Limit to 10 rows
                                print(f"Row {i}: {dict(row)}")
                            if len(results) > 10:
                                print(f"... and {len(results) - 10} more rows")
                        else:
                            print("No results")
                    except Exception as e:
                        print(f"Query error: {e}")
                elif command == 'signals':
                    self.show_ai_signals_analysis()
                elif command == 'trading':
                    self.show_trading_analysis()
                elif command == 'summary':
                    self.show_database_summary()
                else:
                    print("Unknown command. Available: tables, info <table>, query <sql>, signals, trading, summary, quit")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
    
    def close(self):
        """Close database connection"""
        self.conn.close()

def main():
    """Main function"""
    browser = DatabaseBrowser()
    
    try:
        # Show summary first
        browser.show_database_summary()
        browser.show_ai_signals_analysis()
        browser.show_trading_analysis()
        
        # Start interactive mode
        browser.interactive_mode()
        
    finally:
        browser.close()

if __name__ == "__main__":
    main()