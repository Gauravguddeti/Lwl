"""
Database models for PostgreSQL tables in lwl_pg_us_2 database
Only contains data access functions, no table creation
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseAccess:
    """Database access class for reading data from PostgreSQL tables"""
    
    def __init__(self):
        # Try multiple environment variable sources
        self.db_host = os.getenv('POSTGRES_HOST') or os.getenv('DB_HOST')
        self.db_port = os.getenv('POSTGRES_PORT') or os.getenv('DB_PORT')
        self.db_name = os.getenv('POSTGRES_DB') or os.getenv('DB_NAME')
        self.db_user = os.getenv('POSTGRES_USER') or os.getenv('DB_USER')
        self.db_password = os.getenv('POSTGRES_PASSWORD') or os.getenv('DB_PASSWORD')
        self.db_schema = os.getenv('DB_SCHEMA', 'public')
        
        # Check for DATABASE_URL first (Lambda environment)
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            self.connection_string = database_url
        else:
            # Fallback to individual variables
            if not all([self.db_host, self.db_port, self.db_name, self.db_user, self.db_password]):
                logger.error("Missing database configuration")
                raise ValueError("Missing required database environment variables")
                
            # Properly encode username and password for URL
            encoded_user = quote_plus(str(self.db_user)) if self.db_user else ""
            encoded_password = quote_plus(str(self.db_password)) if self.db_password else ""
            
            self.connection_string = f"postgresql://{encoded_user}:{encoded_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        
        # Create engine with Lambda-optimized settings
        self.engine = create_engine(
            self.connection_string,
            pool_pre_ping=True,
            pool_recycle=300,
            pool_size=1,
            max_overflow=0,
            echo=False
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    def get_partners(self, partner_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get partners (schools/institutes/agencies) data
        Args:
            partner_type: Filter by contact_type ('Institute', 'School', 'Agency')
        """
        try:
            session = self.get_session()
            query = "SELECT * FROM partners WHERE is_active = true"
            params = {}
            
            if partner_type:
                query += " AND contact_type = :partner_type"
                params['partner_type'] = partner_type
            
            result = session.execute(text(query), params)
            partners_raw = [dict(row._mapping) for row in result]
            session.close()
            
            # Add compatibility fields for the main system
            partners = []
            for partner in partners_raw:
                # Create a compatible partner record
                compatible_partner = partner.copy()
                
                # Map new column names to expected ones
                compatible_partner['contact'] = partner.get('contact_phone', '')  # Main compatibility
                compatible_partner['location'] = partner.get('partner_name', '')  # Use partner name as location for now
                compatible_partner['partnership_type'] = partner.get('contact_type', 'unknown')
                
                # Ensure required fields exist
                if 'partner_name' not in compatible_partner:
                    compatible_partner['partner_name'] = 'Unknown Partner'
                
                partners.append(compatible_partner)
            
            logger.info(f"Retrieved {len(partners)} active partners")
            return partners
            
        except Exception as e:
            logger.error(f"Error getting partners: {str(e)}")
            return []
    
    def get_partner_by_id(self, partner_id: int) -> Optional[Dict[str, Any]]:
        """Get specific partner by ID"""
        try:
            session = self.get_session()
            query = "SELECT * FROM partners WHERE partner_id = :partner_id"
            result = session.execute(text(query), {'partner_id': partner_id})
            partner = result.fetchone()
            session.close()
            
            if partner:
                return dict(partner._mapping)
            return None
            
        except Exception as e:
            logger.error(f"Error getting partner by ID {partner_id}: {str(e)}")
            return None
    
    def get_programs(self, program_category_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get programs data
        Args:
            program_category_id: Filter by program category ID if specified
        """
        try:
            session = self.get_session()
            query = "SELECT * FROM programs"
            params = {}
            
            if program_category_id:
                query += " WHERE program_category_id = :program_category_id"
                params['program_category_id'] = program_category_id
            
            result = session.execute(text(query), params)
            programs = [dict(row._mapping) for row in result]
            session.close()
            
            logger.info(f"Retrieved {len(programs)} programs")
            return programs
            
        except Exception as e:
            logger.error(f"Error getting programs: {str(e)}")
            return []
    
    def get_program_by_id(self, program_id: int) -> Optional[Dict[str, Any]]:
        """Get specific program by ID"""
        try:
            session = self.get_session()
            query = "SELECT * FROM programs WHERE program_id = :program_id"
            result = session.execute(text(query), {'program_id': program_id})
            program = result.fetchone()
            session.close()
            
            if program:
                return dict(program._mapping)
            return None
            
        except Exception as e:
            logger.error(f"Error getting program by ID {program_id}: {str(e)}")
            return None
    
    def get_program_events(self, program_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get program events data
        Args:
            program_id: Filter by program ID if specified
        """
        try:
            session = self.get_session()
            query = """
            SELECT pe.*, p.name as program_name, p.description as program_description
            FROM program_events pe
            LEFT JOIN programs p ON pe.program_id = p.program_id
            """
            params = {}
            
            if program_id:
                query += " WHERE pe.program_id = :program_id"
                params['program_id'] = program_id
            
            query += " ORDER BY pe.start_date"
            
            result = session.execute(text(query), params)
            events = [dict(row._mapping) for row in result]
            session.close()
            
            logger.info(f"Retrieved {len(events)} program events")
            return events
            
        except Exception as e:
            logger.error(f"Error getting program events: {str(e)}")
            return []
    
    def get_program_event_by_id(self, event_id: int) -> Optional[Dict[str, Any]]:
        """Get specific program event by ID"""
        try:
            session = self.get_session()
            query = """
            SELECT pe.*, p.name as program_name, p.description as program_description
            FROM program_events pe
            LEFT JOIN programs p ON pe.program_id = p.program_id
            WHERE pe.program_event_id = :event_id
            """
            result = session.execute(text(query), {'event_id': event_id})
            event = result.fetchone()
            session.close()
            
            if event:
                return dict(event._mapping)
            return None
            
        except Exception as e:
            logger.error(f"Error getting program event by ID {event_id}: {str(e)}")
            return None
    
    def get_scheduled_jobs(self) -> List[Dict[str, Any]]:
        """Get scheduled jobs data"""
        try:
            session = self.get_session()
            query = "SELECT * FROM scheduled_jobs ORDER BY scheduled_at"
            result = session.execute(text(query))
            jobs = [dict(row._mapping) for row in result]
            session.close()
            
            logger.info(f"Retrieved {len(jobs)} scheduled jobs")
            return jobs
            
        except Exception as e:
            logger.error(f"Error getting scheduled jobs: {str(e)}")
            return []
    
    def get_scheduled_job_events(self, job_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get scheduled job events data
        Args:
            job_id: Filter by job ID if specified
        """
        try:
            session = self.get_session()
            query = """
            SELECT sje.*, sj.scheduled_at as job_datetime, 
                   pe.start_date as event_datetime, pe.early_fee, pe.regular_fee, pe.discount, pe.seats,
                   p.name as program_name, p.description as program_description,
                   pt.partner_name, pt.contact_phone, pt.contact_email, pt.contact_person_name, pt.contact_type as partner_type
            FROM scheduled_job_events sje
            LEFT JOIN scheduled_jobs sj ON sje.scheduled_job_id = sj.scheduled_job_id
            LEFT JOIN program_events pe ON sje.program_event_id = pe.program_event_id
            LEFT JOIN programs p ON pe.program_id = p.program_id
            LEFT JOIN partners pt ON sje.partner_id = pt.partner_id
            """
            params = {}
            
            if job_id:
                query += " WHERE sje.scheduled_job_id = :job_id"
                params['job_id'] = job_id
            
            query += " ORDER BY sj.scheduled_at, sje.scheduled_job_event_id"
            
            result = session.execute(text(query), params)
            events = [dict(row._mapping) for row in result]
            session.close()
            
            logger.info(f"Retrieved {len(events)} scheduled job events")
            return events
            
        except Exception as e:
            logger.error(f"Error getting scheduled job events: {str(e)}")
            return []
    
    def search_programs_by_name(self, search_term: str) -> List[Dict[str, Any]]:
        """Search programs by name"""
        try:
            session = self.get_session()
            query = """
            SELECT p.*, pt.partner_name 
            FROM programs p
            LEFT JOIN partners pt ON p.partner_id = pt.partner_id
            WHERE LOWER(p.program_name) LIKE LOWER(:search_term)
            """
            result = session.execute(text(query), {'search_term': f'%{search_term}%'})
            programs = [dict(row._mapping) for row in result]
            session.close()
            
            return programs
            
        except Exception as e:
            logger.error(f"Error searching programs: {str(e)}")
            return []
    
    def get_upcoming_events(self, days_ahead: int = 30) -> List[Dict[str, Any]]:
        """Get upcoming program events within specified days"""
        try:
            session = self.get_session()
            query = """
            SELECT pe.*, p.name as program_name, p.description as program_description
            FROM program_events pe
            LEFT JOIN programs p ON pe.program_id = p.program_id
            WHERE pe.start_date >= CURRENT_DATE 
            AND pe.start_date <= CURRENT_DATE + INTERVAL '%s days'
            ORDER BY pe.start_date
            """ % days_ahead
            
            result = session.execute(text(query))
            events = [dict(row._mapping) for row in result]
            session.close()
            
            return events
            
        except Exception as e:
            logger.error(f"Error getting upcoming events: {str(e)}")
            return []
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            session = self.get_session()
            result = session.execute(text("SELECT 1"))
            session.close()
            logger.info("Database connection successful")
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            return False

    def call_getcallstobedone(self) -> List[Dict[str, Any]]:
        """
        Call the DBA-provided getcallstobedone function
        
        This function returns all scheduled calls that need to be made.
        It takes no parameters and returns a complete dataset.
        
        Returns:
            List of dictionaries containing call details with keys:
                - contact_person_name: Name of person to call
                - contact_type: Type of contact (e.g., 'school')
                - contact_email: Email address
                - contact_phone: Phone number
                - partner_name: Name of the partner
                - scheduled_job_event_id: Event ID
                - scheduled_job_id: Job ID
                - call_datetime: Scheduled call time
                - system_prompt_id: Prompt ID
                - system_prompt: AI system prompt
                - ai_model_name: AI model to use
        """
        try:
            session = self.get_session()
            
            # Call the function without parameters as it doesn't take any
            query = text("SELECT * FROM getcallstobedone()")
            result = session.execute(query)
            
            calls = []
            for row in result:
                call_data = {
                    'contact_person_name': row.contact_person_name,
                    'contact_type': row.contact_type,
                    'contact_email': row.contact_email,
                    'contact_phone': row.contact_phone.strip() if row.contact_phone else None,  # Clean phone number
                    'partner_name': row.partner_name,
                    'scheduled_job_event_id': row.scheduled_job_event_id,
                    'scheduled_job_id': row.scheduled_job_id,
                    'call_datetime': row.call_datetime,
                    'system_prompt_id': row.system_prompt_id,
                    'system_prompt': row.system_prompt,
                    'ai_model_name': row.ai_model_name
                }
                calls.append(call_data)
            
            session.close()
            logger.info(f"getcallstobedone returned {len(calls)} results")
            return calls
            
        except Exception as e:
            logger.error(f"Error calling getcallstobedone function: {str(e)}")
            if 'session' in locals():
                session.close()
            return []
    
    def get_system_prompts(self, is_active: bool = True) -> List[Dict[str, Any]]:
        """
        Get system prompts from the database
        
        Args:
            is_active: Filter for active prompts only (default: True)
        """
        try:
            session = self.get_session()
            query = "SELECT * FROM system_prompts"
            params = {}
            
            if is_active:
                query += " WHERE is_active = :is_active"
                params['is_active'] = is_active
            
            query += " ORDER BY system_prompt_id"
            
            result = session.execute(text(query), params)
            prompts = [dict(row._mapping) for row in result]
            session.close()
            
            logger.info(f"Retrieved {len(prompts)} system prompts")
            return prompts
            
        except Exception as e:
            logger.error(f"Error getting system prompts: {str(e)}")
            return []
    
    def get_call_logs(self, scheduled_job_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get call logs from the database
        
        Args:
            scheduled_job_id: Filter by scheduled job ID if specified
        """
        try:
            session = self.get_session()
            query = "SELECT * FROM call_logs"
            params = {}
            
            if scheduled_job_id:
                query += " WHERE scheduled_job_id = :scheduled_job_id"
                params['scheduled_job_id'] = scheduled_job_id
            
            query += " ORDER BY call_log_id DESC"
            
            result = session.execute(text(query), params)
            logs = [dict(row._mapping) for row in result]
            session.close()
            
            logger.info(f"Retrieved {len(logs)} call logs")
            return logs
            
        except Exception as e:
            logger.error(f"Error getting call logs: {str(e)}")
            return []

# Global database instance
db_access = DatabaseAccess()
