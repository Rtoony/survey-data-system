"""
Database module - re-exports from database.py for compatibility
"""
from database import get_db, execute_query

__all__ = ['get_db', 'execute_query']
