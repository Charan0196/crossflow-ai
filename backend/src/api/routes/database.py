"""
Database Viewer API Routes
"""
from fastapi import APIRouter
import sqlite3
from typing import Dict, List

router = APIRouter(prefix="/database", tags=["Database"])


@router.get("/tables")
async def get_tables():
    """Get list of all database tables"""
    conn = sqlite3.connect('crossflow.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    
    return {"tables": tables}


@router.get("/table/{table_name}")
async def get_table_data(table_name: str, limit: int = 100):
    """Get data from a specific table"""
    conn = sqlite3.connect('crossflow.db')
    cursor = conn.cursor()
    
    try:
        # Get column names
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        total_rows = cursor.fetchone()[0]
        
        # Get data
        cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
        rows = cursor.fetchall()
        
        # Convert to list of dicts
        data = []
        for row in rows:
            data.append(dict(zip(columns, row)))
        
        return {
            "table": table_name,
            "columns": columns,
            "total_rows": total_rows,
            "data": data,
            "showing": len(data)
        }
    except Exception as e:
        return {
            "error": str(e),
            "table": table_name
        }
    finally:
        conn.close()


@router.get("/stats")
async def get_database_stats():
    """Get database statistics"""
    conn = sqlite3.connect('crossflow.db')
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = [row[0] for row in cursor.fetchall()]
    
    # Get row counts
    stats = {}
    total_rows = 0
    
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        stats[table] = count
        total_rows += count
    
    conn.close()
    
    return {
        "total_tables": len(tables),
        "total_rows": total_rows,
        "table_stats": stats
    }


@router.get("/schema/{table_name}")
async def get_table_schema(table_name: str):
    """Get schema for a specific table"""
    conn = sqlite3.connect('crossflow.db')
    cursor = conn.cursor()
    
    try:
        # Get table schema
        cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        schema = cursor.fetchone()
        
        if schema:
            return {
                "table": table_name,
                "schema": schema[0]
            }
        else:
            return {
                "error": f"Table {table_name} not found"
            }
    finally:
        conn.close()
