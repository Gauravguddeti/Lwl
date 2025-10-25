import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import logging
from typing import Optional, Dict, Any, List
from contextlib import contextmanager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseConfig:
    """Database configuration class"""
    
    def __init__(self):
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = int(os.getenv('DB_PORT', 5432))
        self.database = os.getenv('DB_NAME', 'lwl_pg_us_2')
        self.user = os.getenv('DB_USER', 'postgres')
        self.password = os.getenv('DB_PASSWORD', '')
        self.sslmode = os.getenv('DB_SSL_MODE', 'prefer')
        self.schema = os.getenv('DB_SCHEMA', 'public')
    
    @property
    def connection_string(self) -> str:
        return f"host={self.host} port={self.port} dbname={self.database} user={self.user} password={self.password} sslmode={self.sslmode}"

class DatabaseManager:
    """Database connection and query manager"""
    
    def __init__(self):
        self.config = DatabaseConfig()
        self._connection = None
    
    def get_connection(self):
        """Get database connection"""
        try:
            if self._connection is None or self._connection.closed:
                self._connection = psycopg2.connect(self.config.connection_string)
                logger.info("Database connection established")
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
    
    def execute_script_file(self, file_path: str) -> bool:
        """Execute SQL script from file"""
        try:
            with open(file_path, 'r') as file:
                script_content = file.read()
            
            with self.get_cursor(dict_cursor=False) as cursor:
                cursor.execute(script_content)
            
            logger.info(f"SQL script executed successfully: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to execute SQL script {file_path}: {e}")
            raise
    
    def close_connection(self):
        """Close database connection"""
        if self._connection and not self._connection.closed:
            self._connection.close()
            logger.info("Database connection closed")

# Database query functions
class DatabaseQueries:
    """Database query functions for the AI Telecaller system"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.schema = db_manager.config.schema
    
    def get_scheduled_job_events(self, job_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get scheduled job events with all details"""
        query = f"SELECT * FROM {self.schema}.get_scheduled_job_events(%s);"
        return self.db.execute_query(query, (job_id,))
    
    def is_slot_open(self, check_datetime: str) -> bool:
        """Check if a calendar slot is open"""
        query = f"SELECT {self.schema}.is_slot_open(%s) as is_open;"
        result = self.db.execute_query(query, (check_datetime,), fetch='one')
        return result['is_open'] if result else False
    
    def get_available_slots(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get available calendar slots"""
        query = f"""
        SELECT slot_datetime, slot_duration_minutes, notes
        FROM {self.schema}.calendar 
        WHERE is_available = TRUE 
        AND slot_datetime > NOW() 
        AND current_bookings < max_bookings
        ORDER BY slot_datetime ASC 
        LIMIT %s;
        """
        return self.db.execute_query(query, (limit,))
    
    def create_audit_log_entry(self, log_data: Dict[str, Any]) -> int:
        """Create an audit log entry"""
        query = """
        INSERT INTO audit_log (
            scheduled_job_event_id, school_id, program_event_id, call_sid,
            caller_number, recipient_number, call_start_time, call_end_time,
            call_duration_seconds, call_status, response_type, conversation_summary,
            reschedule_requested, reschedule_slot, follow_up_required,
            ai_prompt_used, twilio_response, error_message
        ) VALUES (
            %(scheduled_job_event_id)s, %(school_id)s, %(program_event_id)s, %(call_sid)s,
            %(caller_number)s, %(recipient_number)s, %(call_start_time)s, %(call_end_time)s,
            %(call_duration_seconds)s, %(call_status)s, %(response_type)s, %(conversation_summary)s,
            %(reschedule_requested)s, %(reschedule_slot)s, %(follow_up_required)s,
            %(ai_prompt_used)s, %(twilio_response)s, %(error_message)s
        ) RETURNING id;
        """
        result = self.db.execute_query(query, log_data, fetch='one')
        return result['id'] if result else None
    
    def update_scheduled_job_event_status(self, event_id: int, status: str, outcome: Optional[str] = None, 
                                        reschedule_slot: Optional[str] = None, notes: Optional[str] = None) -> bool:
        """Update scheduled job event status"""
        query = """
        UPDATE scheduled_job_events 
        SET call_status = %s, outcome = %s, reschedule_slot = %s, notes = %s, 
            call_completed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s;
        """
        try:
            self.db.execute_query(query, (status, outcome, reschedule_slot, notes, event_id), fetch='none')
            return True
        except Exception as e:
            logger.error(f"Failed to update scheduled job event {event_id}: {e}")
            return False
    
    def get_program_details(self, program_event_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed program information"""
        query = """
        SELECT p.name as program_name, p.description, p.base_fee, p.category,
               pe.discounted_fee, pe.discount_percentage, pe.total_seats, 
               pe.available_seats, pe.start_date, pe.end_date, pe.zoom_call_slot,
               pe.registration_deadline
        FROM program_events pe
        JOIN programs p ON pe.program_id = p.id
        WHERE pe.id = %s;
        """
        return self.db.execute_query(query, (program_event_id,), fetch='one')
    
    def get_school_details(self, school_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed school information"""
        query = """
        SELECT name, contact_person, phone_number, email, address, city, state
        FROM schools 
        WHERE id = %s;
        """
        return self.db.execute_query(query, (school_id,), fetch='one')

# Singleton database manager instance
db_manager = DatabaseManager()
db_queries = DatabaseQueries(db_manager)
