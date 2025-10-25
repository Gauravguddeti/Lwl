"""
Database access layer for AI Telecaller System
Handles all database operations and data access methods
"""

from typing import List, Dict, Any, Optional
from app.database.postgres_data_access import db_access

class DatabaseAccess:
    """Database access wrapper for telecaller system"""
    
    def __init__(self):
        self.db_access = db_access
    
    def get_partners_from_database(self) -> List[Dict[str, Any]]:
        """Get all active partners from database"""
        try:
            partners = self.db_access.get_partners()
            return partners if partners else []
        except Exception as e:
            print(f"❌ Error fetching partners: {e}")
            return []
    
    def get_scheduled_calls_from_database(self) -> List[Dict[str, Any]]:
        """Get scheduled calls that need to be made"""
        try:
            # TODO: Implement scheduled calls functionality
            # For now, return empty list
            return []
        except Exception as e:
            print(f"❌ Error fetching scheduled calls: {e}")
            return []

# Global database access instance
database_access = DatabaseAccess()
