"""
PostgreSQL Database Models for AI Telecaller System
Handles Partners, Programs, Program Events, Scheduled Jobs, and Scheduled Job Events
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import logging
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PostgreSQLManager:
    """PostgreSQL database manager for lwl_pg_us_2 database"""
    
    def __init__(self):
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = int(os.getenv('DB_PORT', 5432))
        self.database = os.getenv('DB_NAME', 'lwl_pg_us_2')
        self.user = os.getenv('DB_USER', 'postgres')
        self.password = os.getenv('DB_PASSWORD', '')
        self.sslmode = os.getenv('DB_SSL_MODE', 'prefer')
        self.schema = os.getenv('DB_SCHEMA', 'public')
        self._connection = None
    
    @property
    def connection_string(self) -> str:
        return f"host={self.host} port={self.port} dbname={self.database} user={self.user} password={self.password} sslmode={self.sslmode}"
    
    def get_connection(self):
        """Get database connection"""
        try:
            if self._connection is None or self._connection.closed:
                self._connection = psycopg2.connect(self.connection_string)
                logger.info(f"Connected to PostgreSQL database: {self.database}")
            return self._connection
        except psycopg2.Error as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    @contextmanager
    def get_cursor(self, dict_cursor=True):
        """Context manager for database cursor"""
        conn = self.get_connection()
        cursor_class = RealDictCursor if dict_cursor else None
        cursor = conn.cursor(cursor_factory=cursor_class)
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database operation failed: {e}")
            raise
        finally:
            cursor.close()
    
    def execute_query(self, query: str, params: tuple = None, fetch: str = 'all') -> Optional[List[Dict[Any, Any]]]:
        """Execute a query and return results"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query, params)
                
                if fetch == 'one':
                    return cursor.fetchone()
                elif fetch == 'all':
                    return cursor.fetchall()
                elif fetch == 'none':
                    return None
                else:
                    return cursor.fetchmany(fetch)
        except psycopg2.Error as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    def close_connection(self):
        """Close database connection"""
        if self._connection and not self._connection.closed:
            self._connection.close()
            logger.info("Database connection closed")

class TelecallerDBQueries:
    """Database query functions for AI Telecaller system with PostgreSQL"""
    
    def __init__(self, db_manager: PostgreSQLManager):
        self.db = db_manager
    
    # Programs Queries
    def get_programs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all programs"""
        query = """
        SELECT program_id, program_name, description, base_fees, category, 
               created_at, updated_at
        FROM programs 
        ORDER BY created_at DESC 
        LIMIT %s;
        """
        return self.db.execute_query(query, (limit,))
    
    def get_program_by_id(self, program_id: int) -> Optional[Dict[str, Any]]:
        """Get program by ID"""
        query = """
        SELECT program_id, program_name, description, base_fees, category, 
               created_at, updated_at
        FROM programs 
        WHERE program_id = %s;
        """
        return self.db.execute_query(query, (program_id,), fetch='one')
    
    def create_program(self, program_data: Dict[str, Any]) -> int:
        """Create a new program"""
        query = """
        INSERT INTO programs (program_name, description, base_fees, category)
        VALUES (%(program_name)s, %(description)s, %(base_fees)s, %(category)s)
        RETURNING program_id;
        """
        result = self.db.execute_query(query, program_data, fetch='one')
        return result['program_id'] if result else None
    
    # Partners Queries
    def get_partners(self, partner_type: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get partners, optionally filtered by type"""
        if partner_type:
            query = """
            SELECT partner_id, partner_name, contact, type, created_at, updated_at
            FROM partners 
            WHERE type = %s
            ORDER BY created_at DESC 
            LIMIT %s;
            """
            return self.db.execute_query(query, (partner_type, limit))
        else:
            query = """
            SELECT partner_id, partner_name, contact, type, created_at, updated_at
            FROM partners 
            ORDER BY created_at DESC 
            LIMIT %s;
            """
            return self.db.execute_query(query, (limit,))
    
    def get_partner_by_id(self, partner_id: int) -> Optional[Dict[str, Any]]:
        """Get partner by ID"""
        query = """
        SELECT partner_id, partner_name, contact, type, created_at, updated_at
        FROM partners 
        WHERE partner_id = %s;
        """
        return self.db.execute_query(query, (partner_id,), fetch='one')
    
    def create_partner(self, partner_data: Dict[str, Any]) -> int:
        """Create a new partner"""
        query = """
        INSERT INTO partners (partner_name, contact, type)
        VALUES (%(partner_name)s, %(contact)s, %(type)s)
        RETURNING partner_id;
        """
        result = self.db.execute_query(query, partner_data, fetch='one')
        return result['partner_id'] if result else None
    
    # Program Events Queries
    def get_program_events(self, program_id: Optional[int] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get program events, optionally filtered by program"""
        if program_id:
            query = """
            SELECT pe.program_event_id, pe.program_id, pe.event_datetime, 
                   pe.fees, pe.discount, pe.seats, pe.created_at, pe.updated_at,
                   p.program_name, p.description, p.base_fees, p.category
            FROM program_events pe
            JOIN programs p ON pe.program_id = p.program_id
            WHERE pe.program_id = %s
            ORDER BY pe.event_datetime DESC 
            LIMIT %s;
            """
            return self.db.execute_query(query, (program_id, limit))
        else:
            query = """
            SELECT pe.program_event_id, pe.program_id, pe.event_datetime, 
                   pe.fees, pe.discount, pe.seats, pe.created_at, pe.updated_at,
                   p.program_name, p.description, p.base_fees, p.category
            FROM program_events pe
            JOIN programs p ON pe.program_id = p.program_id
            ORDER BY pe.event_datetime DESC 
            LIMIT %s;
            """
            return self.db.execute_query(query, (limit,))
    
    def get_program_event_by_id(self, program_event_id: int) -> Optional[Dict[str, Any]]:
        """Get program event by ID with program details"""
        query = """
        SELECT pe.program_event_id, pe.program_id, pe.event_datetime, 
               pe.fees, pe.discount, pe.seats, pe.created_at, pe.updated_at,
               p.program_name, p.description, p.base_fees, p.category
        FROM program_events pe
        JOIN programs p ON pe.program_id = p.program_id
        WHERE pe.program_event_id = %s;
        """
        return self.db.execute_query(query, (program_event_id,), fetch='one')
    
    def create_program_event(self, event_data: Dict[str, Any]) -> int:
        """Create a new program event"""
        query = """
        INSERT INTO program_events (program_id, event_datetime, fees, discount, seats)
        VALUES (%(program_id)s, %(event_datetime)s, %(fees)s, %(discount)s, %(seats)s)
        RETURNING program_event_id;
        """
        result = self.db.execute_query(query, event_data, fetch='one')
        return result['program_event_id'] if result else None
    
    # Scheduled Jobs Queries (when available)
    def get_scheduled_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get scheduled jobs - will be implemented when table is available"""
        # Placeholder - will be implemented when colleague creates the table
        logger.info("Scheduled jobs table not yet available")
        return []
    
    def get_scheduled_job_by_id(self, scheduled_job_id: int) -> Optional[Dict[str, Any]]:
        """Get scheduled job by ID - will be implemented when table is available"""
        # Placeholder - will be implemented when colleague creates the table
        logger.info("Scheduled jobs table not yet available")
        return None
    
    # Scheduled Job Events Queries (when available)
    def get_scheduled_job_events(self, scheduled_job_id: Optional[int] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get scheduled job events - will be implemented when table is available"""
        # Placeholder - will be implemented when colleague creates the table
        logger.info("Scheduled job events table not yet available")
        return []
    
    def get_scheduled_job_event_by_id(self, scheduled_job_event_id: int) -> Optional[Dict[str, Any]]:
        """Get scheduled job event by ID - will be implemented when table is available"""
        # Placeholder - will be implemented when colleague creates the table
        logger.info("Scheduled job events table not yet available")
        return None
    
    # Call Management Queries
    def create_call_log(self, call_data: Dict[str, Any]) -> int:
        """Create a call log entry"""
        query = """
        INSERT INTO call_logs (
            program_event_id, partner_id, call_sid, caller_number, recipient_number,
            call_start_time, call_end_time, call_duration_seconds, call_status,
            conversation_summary, outcome, recording_url, transcription_path,
            ai_prompt_used, created_at
        ) VALUES (
            %(program_event_id)s, %(partner_id)s, %(call_sid)s, %(caller_number)s, %(recipient_number)s,
            %(call_start_time)s, %(call_end_time)s, %(call_duration_seconds)s, %(call_status)s,
            %(conversation_summary)s, %(outcome)s, %(recording_url)s, %(transcription_path)s,
            %(ai_prompt_used)s, CURRENT_TIMESTAMP
        ) RETURNING call_log_id;
        """
        result = self.db.execute_query(query, call_data, fetch='one')
        return result['call_log_id'] if result else None
    
    def update_call_log(self, call_log_id: int, update_data: Dict[str, Any]) -> bool:
        """Update call log entry"""
        set_clauses = []
        params = []
        
        for key, value in update_data.items():
            set_clauses.append(f"{key} = %s")
            params.append(value)
        
        params.append(call_log_id)
        
        query = f"""
        UPDATE call_logs 
        SET {', '.join(set_clauses)}, updated_at = CURRENT_TIMESTAMP
        WHERE call_log_id = %s;
        """
        
        try:
            self.db.execute_query(query, tuple(params), fetch='none')
            return True
        except Exception as e:
            logger.error(f"Failed to update call log {call_log_id}: {e}")
            return False
    
    def get_call_logs(self, partner_id: Optional[int] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get call logs, optionally filtered by partner"""
        if partner_id:
            query = """
            SELECT cl.*, p.partner_name, pe.event_datetime, pr.program_name
            FROM call_logs cl
            LEFT JOIN partners p ON cl.partner_id = p.partner_id
            LEFT JOIN program_events pe ON cl.program_event_id = pe.program_event_id
            LEFT JOIN programs pr ON pe.program_id = pr.program_id
            WHERE cl.partner_id = %s
            ORDER BY cl.created_at DESC
            LIMIT %s;
            """
            return self.db.execute_query(query, (partner_id, limit))
        else:
            query = """
            SELECT cl.*, p.partner_name, pe.event_datetime, pr.program_name
            FROM call_logs cl
            LEFT JOIN partners p ON cl.partner_id = p.partner_id
            LEFT JOIN program_events pe ON cl.program_event_id = pe.program_event_id
            LEFT JOIN programs pr ON pe.program_id = pr.program_id
            ORDER BY cl.created_at DESC
            LIMIT %s;
            """
            return self.db.execute_query(query, (limit,))

# Initialize database manager and queries
pg_manager = PostgreSQLManager()
telecaller_db = TelecallerDBQueries(pg_manager)
