"""
PostgreSQL Database Service for AI Telecaller System
Handles database operations for partners, programs, events, and call records
"""

import logging
import os
import psycopg2
import psycopg2.extras
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseService:
    """PostgreSQL database service for managing telecaller data"""
    
    def __init__(self, database_url: str = None):
        """Initialize PostgreSQL database service"""
        # Default PostgreSQL connection parameters - update these with your actual DB credentials
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'postgres'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'your_password')
        }
        
        if database_url:
            self.database_url = database_url
        
        self.use_sqlite = False
        self._test_connection()
        logger.info(f"✅ Database service initialized")
    
    def _test_connection(self):
        """Test PostgreSQL database connection"""
        try:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT version();")
                    version = cursor.fetchone()
                    logger.info(f"📦 Connected to PostgreSQL: {version[0]}")
                    # Commented out schema exploration to improve performance
                    # self._explore_database_schema(conn)
        except Exception as e:
            logger.error(f"❌ PostgreSQL connection failed: {e}")
            logger.warning("🔄 Falling back to SQLite for local testing")
            self._init_sqlite_fallback()
    
    def _explore_database_schema(self, conn):
        """Explore and log the actual database schema"""
        try:
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            tables = cursor.fetchall()
            logger.info(f"📋 Found tables: {[t[0] for t in tables]}")
            
            # Explore each table structure
            for table in tables:
                table_name = table[0]
                if table_name in ['partners', 'programs', 'program_events']:
                    cursor.execute(f"""
                        SELECT column_name, data_type, is_nullable
                        FROM information_schema.columns 
                        WHERE table_name = '{table_name}' 
                        ORDER BY ordinal_position;
                    """)
                    columns = cursor.fetchall()
                    logger.info(f"🔍 Table '{table_name}' columns: {[(c[0], c[1]) for c in columns]}")
                    
                    # Show sample data
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 2;")
                    sample_data = cursor.fetchall()
                    if sample_data:
                        logger.info(f"📊 Sample data from '{table_name}': {len(sample_data)} rows")
                    
        except Exception as e:
            logger.error(f"❌ Error exploring database schema: {e}")

    def _init_sqlite_fallback(self):
        """Initialize SQLite fallback for local testing"""
        import sqlite3
        self.use_sqlite = True
        self.database_path = "telecaller.db"
        
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                # Create partners table matching PostgreSQL structure
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS partners (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        type TEXT DEFAULT 'school',
                        active BOOLEAN DEFAULT true,
                        status_id INTEGER DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_by TEXT DEFAULT 'system',
                        phone TEXT,
                        email TEXT,
                        contact_person TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_by TEXT DEFAULT 'system'
                    )
                """)
                
                # Create programs table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS programs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        description TEXT,
                        type TEXT DEFAULT 'course',
                        active BOOLEAN DEFAULT true,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create program_events table  
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS program_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        program_id INTEGER,
                        name TEXT NOT NULL,
                        description TEXT,
                        start_date DATE,
                        end_date DATE,
                        location TEXT,
                        capacity INTEGER DEFAULT 50,
                        active BOOLEAN DEFAULT true,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (program_id) REFERENCES programs (id)
                    )
                """)
                
                # Insert sample data
                self._insert_sample_data_sqlite(cursor)
                conn.commit()
                
                logger.info("✅ SQLite fallback initialized with sample data")
                
        except Exception as e:
            logger.error(f"❌ SQLite fallback failed: {e}")
    
    def _insert_sample_data_sqlite(self, cursor):
        """Insert your actual partner data for SQLite fallback"""
        try:
            # Check if partners exist
            cursor.execute("SELECT COUNT(*) FROM partners")
            if cursor.fetchone()[0] == 0:
                # Insert the 3 partners from your PostgreSQL data
                partners = [
                    (1, "New Partner Name", "school", True, 2, "2025-08-16 18:19:09.630", "import_script", "7276082005", "guddetigaurav1@gmail.com", "abc", "2025-08-18 11:05:06.482", "manual_update"),
                    (2, "Global Learning Academy", "school", True, 3, "2025-08-16 18:20:55.361", "manual_entry", "7666815841", "nihalpardeshi12344@email.com", "xyz", "2025-08-18 11:07:05.394", "manual_update"),
                    (3, "NextGen Education Services", "institute", True, 3, "2025-08-16 18:21:16.048", "api_seed", "8208271283", "xyzpartner@email.com", "Jane Smith", "2025-08-18 11:08:44.714", "manual_update")
                ]
                
                cursor.executemany("""
                    INSERT INTO partners (id, name, type, active, status_id, created_at, created_by, phone, email, contact_person, updated_at, updated_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, partners)
                
                logger.info("✅ Sample partners inserted")
            
            # Insert sample programs
            cursor.execute("SELECT COUNT(*) FROM programs")
            if cursor.fetchone()[0] == 0:
                programs = [
                    (1, "Data Science Certification", "Comprehensive 6-month data science program", "certification", True, "2025-08-16 10:00:00"),
                    (2, "AI & Machine Learning Workshop", "Intensive 3-day AI/ML workshop", "workshop", True, "2025-08-16 10:00:00"),
                    (3, "Digital Marketing Bootcamp", "4-week digital marketing intensive", "bootcamp", True, "2025-08-16 10:00:00"),
                    (4, "Project Management Professional", "PMP certification preparation course", "certification", True, "2025-08-16 10:00:00"),
                    (5, "Full Stack Development", "6-month full stack web development program", "course", True, "2025-08-16 10:00:00")
                ]
                
                cursor.executemany("""
                    INSERT INTO programs (id, name, description, type, active, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, programs)
                
                logger.info("✅ Sample programs inserted")
            
            # Insert sample program events
            cursor.execute("SELECT COUNT(*) FROM program_events")
            if cursor.fetchone()[0] == 0:
                events = [
                    (1, 1, "Data Science Cohort Jan 2025", "January 2025 data science certification cohort", "2025-01-15", "2025-07-15", "Online", 30, True, "2025-08-16 10:00:00"),
                    (2, 1, "Data Science Cohort Mar 2025", "March 2025 data science certification cohort", "2025-03-01", "2025-09-01", "Hybrid", 25, True, "2025-08-16 10:00:00"),
                    (3, 2, "AI Workshop - Sep 2025", "September AI/ML workshop session", "2025-09-15", "2025-09-17", "Bangalore", 50, True, "2025-08-16 10:00:00"),
                    (4, 2, "AI Workshop - Oct 2025", "October AI/ML workshop session", "2025-10-10", "2025-10-12", "Mumbai", 40, True, "2025-08-16 10:00:00"),
                    (5, 3, "Digital Marketing Sep 2025", "September digital marketing bootcamp", "2025-09-20", "2025-10-18", "Online", 60, True, "2025-08-16 10:00:00"),
                    (6, 4, "PMP Certification Dec 2025", "December PMP certification course", "2025-12-01", "2025-12-20", "Delhi", 20, True, "2025-08-16 10:00:00"),
                    (7, 5, "Full Stack Cohort Oct 2025", "October full stack development cohort", "2025-10-01", "2026-04-01", "Online", 35, True, "2025-08-16 10:00:00")
                ]
                
                cursor.executemany("""
                    INSERT INTO program_events (id, program_id, name, description, start_date, end_date, location, capacity, active, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, events)
                
                logger.info("✅ Sample program events inserted")
                
        except Exception as e:
            logger.error(f"❌ Error inserting sample data: {e}")
    
    def get_all_partners(self) -> List[Dict[str, Any]]:
        """Get all partners from database"""
        try:
            if self.use_sqlite:
                return self._get_partners_sqlite()
            else:
                return self._get_partners_postgresql()
        except Exception as e:
            logger.error(f"❌ Error getting partners: {e}")
            return []
    
    def _get_partners_sqlite(self) -> List[Dict[str, Any]]:
        """Get partners from SQLite"""
        try:
            import sqlite3
            with sqlite3.connect(self.database_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, name, type, active, phone, email, contact_person, 
                           created_at, updated_at, status_id
                    FROM partners
                    WHERE active = 1
                    ORDER BY name
                """)
                
                partners = []
                for row in cursor.fetchall():
                    partners.append({
                        'id': row['id'],
                        'name': row['name'],
                        'type': row['type'],
                        'phone': row['phone'],
                        'email': row['email'],
                        'contact_person': row['contact_person'],
                        'active': bool(row['active']),
                        'status_id': row['status_id'],
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at']
                    })
                
                logger.info(f"📋 Retrieved {len(partners)} partners from SQLite")
                return partners
                
        except Exception as e:
            logger.error(f"❌ Error getting partners from SQLite: {e}")
            return []
    
    def _get_partners_postgresql(self) -> List[Dict[str, Any]]:
        """Get partners from PostgreSQL"""
        try:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT 
                            partner_id as id, 
                            partner_name as name, 
                            contact_type as type, 
                            is_active as active, 
                            contact_phone as phone,
                            contact_email as email,
                            contact_person_name as contact_person,
                            create_date as created_at,
                            update_date as updated_at
                        FROM partners
                        WHERE is_active = true
                        ORDER BY partner_name
                    """)
                    
                    partners = []
                    for row in cursor.fetchall():
                        partners.append(dict(row))
                    
                    logger.info(f"📋 Retrieved {len(partners)} partners from PostgreSQL")
                    return partners
                    
        except Exception as e:
            logger.error(f"❌ Error getting partners from PostgreSQL: {e}")
            return []
    
    def get_partner_by_id(self, partner_id):
        """Get a specific partner by ID"""
        try:
            if self.use_sqlite:
                return self._get_partner_by_id_sqlite(partner_id)
            else:
                return self._get_partner_by_id_postgresql(partner_id)
        except Exception as e:
            logger.error(f"Error getting partner by ID {partner_id}: {e}")
            return None

    def _get_partner_by_id_sqlite(self, partner_id):
        """Get a specific partner by ID from SQLite"""
        try:
            import sqlite3
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM partners WHERE id = ?", (partner_id,))
                row = cursor.fetchone()
                if row:
                    columns = [description[0] for description in cursor.description]
                    return dict(zip(columns, row))
                return None
        except Exception as e:
            logger.error(f"❌ Error getting partner {partner_id} from SQLite: {e}")
            return None

    def _get_partner_by_id_postgresql(self, partner_id):
        """Get a specific partner by ID from PostgreSQL"""
        try:
            from psycopg2.extras import RealDictCursor
            with psycopg2.connect(**self.db_config) as conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute("""
                    SELECT 
                        partner_id as id, 
                        partner_name as name, 
                        contact_type as type, 
                        is_active as active, 
                        contact_phone as phone,
                        contact_email as email,
                        contact_person_name as contact_person,
                        create_date as created_at,
                        update_date as updated_at
                    FROM partners 
                    WHERE partner_id = %s
                """, (partner_id,))
                result = cursor.fetchone()
                return dict(result) if result else None
        except Exception as e:
            logger.error(f"❌ Error getting partner {partner_id} from PostgreSQL: {e}")
            return None
    
    def get_all_programs(self) -> List[Dict[str, Any]]:
        """Get all programs from database"""
        try:
            if self.use_sqlite:
                return self._get_programs_sqlite()
            else:
                return self._get_programs_postgresql()
        except Exception as e:
            logger.error(f"❌ Error getting programs: {e}")
            return []
    
    def get_program_by_id(self, program_id: int) -> Dict[str, Any]:
        """Get a specific program by ID"""
        try:
            if self.use_sqlite:
                return self._get_program_by_id_sqlite(program_id)
            else:
                return self._get_program_by_id_postgresql(program_id)
        except Exception as e:
            logger.error(f"Error getting program by ID {program_id}: {e}")
            return None

    def _get_program_by_id_sqlite(self, program_id):
        """Get a specific program by ID from SQLite"""
        try:
            import sqlite3
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM programs WHERE id = ?", (program_id,))
                row = cursor.fetchone()
                if row:
                    columns = [description[0] for description in cursor.description]
                    return dict(zip(columns, row))
                return None
        except Exception as e:
            logger.error(f"❌ Error getting program {program_id} from SQLite: {e}")
            return None

    def _get_program_by_id_postgresql(self, program_id):
        """Get a specific program by ID from PostgreSQL"""
        try:
            from psycopg2.extras import RealDictCursor
            with psycopg2.connect(**self.db_config) as conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute("""
                    SELECT 
                        program_id as id, 
                        program_name as name, 
                        program_description as description,
                        program_duration as duration,
                        create_date as created_at,
                        update_date as updated_at
                    FROM programs 
                    WHERE program_id = %s
                """, (program_id,))
                result = cursor.fetchone()
                return dict(result) if result else None
        except Exception as e:
            logger.error(f"❌ Error getting program {program_id} from PostgreSQL: {e}")
            return None
    
    def _get_programs_sqlite(self) -> List[Dict[str, Any]]:
        """Get programs from SQLite"""
        try:
            import sqlite3
            with sqlite3.connect(self.database_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, name, description, type, active, created_at
                    FROM programs
                    WHERE active = 1
                    ORDER BY name
                """)
                
                programs = []
                for row in cursor.fetchall():
                    programs.append({
                        'id': row['id'],
                        'name': row['name'],
                        'description': row['description'],
                        'type': row['type'],
                        'active': bool(row['active']),
                        'created_at': row['created_at']
                    })
                
                logger.info(f"📚 Retrieved {len(programs)} programs from SQLite")
                return programs
                
        except Exception as e:
            logger.error(f"❌ Error getting programs from SQLite: {e}")
            return []
    
    def _get_programs_postgresql(self) -> List[Dict[str, Any]]:
        """Get programs from PostgreSQL"""
        try:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT 
                            program_id as id, 
                            name, 
                            description, 
                            program_category_id as type, 
                            is_active as active, 
                            create_date as created_at
                        FROM programs
                        WHERE is_active = true
                        ORDER BY name
                    """)
                    
                    programs = []
                    for row in cursor.fetchall():
                        programs.append(dict(row))
                    
                    logger.info(f"📚 Retrieved {len(programs)} programs from PostgreSQL")
                    return programs
                    
        except Exception as e:
            logger.error(f"❌ Error getting programs from PostgreSQL: {e}")
            return []
    
    def get_program_events(self, program_id: int = None) -> List[Dict[str, Any]]:
        """Get program events, optionally filtered by program_id"""
        try:
            if self.use_sqlite:
                return self._get_program_events_sqlite(program_id)
            else:
                return self._get_program_events_postgresql(program_id)
        except Exception as e:
            logger.error(f"❌ Error getting program events: {e}")
            return []
    
    def _get_program_events_sqlite(self, program_id: int = None) -> List[Dict[str, Any]]:
        """Get program events from SQLite"""
        try:
            import sqlite3
            with sqlite3.connect(self.database_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                if program_id:
                    cursor.execute("""
                        SELECT pe.id, pe.program_id, pe.name, pe.description, 
                               pe.start_date, pe.end_date, pe.location, pe.capacity,
                               pe.active, pe.created_at, p.name as program_name
                        FROM program_events pe
                        JOIN programs p ON pe.program_id = p.id
                        WHERE pe.active = 1 AND pe.program_id = ?
                        ORDER BY pe.start_date
                    """, (program_id,))
                else:
                    cursor.execute("""
                        SELECT pe.id, pe.program_id, pe.name, pe.description, 
                               pe.start_date, pe.end_date, pe.location, pe.capacity,
                               pe.active, pe.created_at, p.name as program_name
                        FROM program_events pe
                        JOIN programs p ON pe.program_id = p.id
                        WHERE pe.active = 1
                        ORDER BY pe.start_date
                    """)
                
                events = []
                for row in cursor.fetchall():
                    events.append({
                        'id': row['id'],
                        'program_id': row['program_id'],
                        'name': row['name'],
                        'description': row['description'],
                        'start_date': row['start_date'],
                        'end_date': row['end_date'],
                        'location': row['location'],
                        'capacity': row['capacity'],
                        'active': bool(row['active']),
                        'created_at': row['created_at'],
                        'program_name': row['program_name']
                    })
                
                logger.info(f"📅 Retrieved {len(events)} program events from SQLite")
                return events
                
        except Exception as e:
            logger.error(f"❌ Error getting program events from SQLite: {e}")
            return []
    
    def _get_program_events_postgresql(self, program_id: int = None) -> List[Dict[str, Any]]:
        """Get program events from PostgreSQL"""
        try:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    if program_id:
                        cursor.execute("""
                            SELECT 
                                pe.program_event_id as id, 
                                pe.program_id, 
                                pe.event_name as name, 
                                pe.start_date, 
                                pe.end_date, 
                                pe.program_delivery as location, 
                                pe.seats as capacity,
                                pe.is_active as active, 
                                pe.create_date as created_at, 
                                p.name as program_name
                            FROM program_events pe
                            JOIN programs p ON pe.program_id = p.program_id
                            WHERE pe.is_active = true AND pe.program_id = %s
                            ORDER BY pe.start_date
                        """, (program_id,))
                    else:
                        cursor.execute("""
                            SELECT 
                                pe.program_event_id as id, 
                                pe.program_id, 
                                pe.event_name as name, 
                                pe.start_date as event_date, 
                                pe.end_date, 
                                pe.program_delivery as location, 
                                pe.seats as capacity,
                                pe.is_active as active, 
                                pe.create_date as created_at, 
                                p.name as program_name
                            FROM program_events pe
                            JOIN programs p ON pe.program_id = p.program_id
                            WHERE pe.is_active = true
                            ORDER BY pe.start_date
                        """)
                    
                    events = []
                    for row in cursor.fetchall():
                        events.append(dict(row))
                    
                    logger.info(f"📅 Retrieved {len(events)} program events from PostgreSQL")
                    return events
                    
        except Exception as e:
            logger.error(f"❌ Error getting program events from PostgreSQL: {e}")
            return []
    
    def get_partner_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        """Get partner by phone number"""
        try:
            if self.use_sqlite:
                return self._get_partner_by_phone_sqlite(phone)
            else:
                return self._get_partner_by_phone_postgresql(phone)
        except Exception as e:
            logger.error(f"❌ Error getting partner by phone: {e}")
            return None
    
    def _get_partner_by_phone_sqlite(self, phone: str) -> Optional[Dict[str, Any]]:
        """Get partner by phone from SQLite"""
        try:
            import sqlite3
            with sqlite3.connect(self.database_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, name, type, phone, email, contact_person, active, status_id
                    FROM partners
                    WHERE phone = ? AND active = 1
                """, (phone,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'id': row['id'],
                        'name': row['name'],
                        'type': row['type'],
                        'phone': row['phone'],
                        'email': row['email'],
                        'contact_person': row['contact_person'],
                        'active': bool(row['active']),
                        'status_id': row['status_id']
                    }
                
                return None
                
        except Exception as e:
            logger.error(f"❌ Error getting partner by phone from SQLite: {e}")
            return None
    
    def _get_partner_by_phone_postgresql(self, phone: str) -> Optional[Dict[str, Any]]:
        """Get partner by phone from PostgreSQL"""
        try:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT id, name, type, phone, email, contact_person, active, status_id
                        FROM partners
                        WHERE phone = %s AND active = true
                    """, (phone,))
                    
                    row = cursor.fetchone()
                    if row:
                        return dict(row)
                    
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Error getting partner by phone from PostgreSQL: {e}")
            return None
    
    # Legacy methods for compatibility
    def get_all_events(self) -> List[Dict[str, Any]]:
        """Legacy method - returns program events for compatibility"""
        return self.get_program_events()
    
    def get_call_records(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent call records - placeholder"""
        return []
    
    def get_database_stats(self) -> Dict[str, int]:
        """Get database statistics"""
        try:
            partners = len(self.get_all_partners())
            programs = len(self.get_all_programs())
            events = len(self.get_program_events())
            
            return {
                'partners': partners,
                'programs': programs,
                'events': events,
                'calls': 0
            }
        except Exception as e:
            logger.error(f"❌ Error getting database stats: {e}")
            return {'partners': 0, 'programs': 0, 'events': 0, 'calls': 0}

    def get_event_participants(self, event_id: int) -> List[Dict[str, Any]]:
        """Get participants (partners) for a specific event"""
        try:
            if self.use_sqlite:
                return self._get_event_participants_sqlite(event_id)
            else:
                return self._get_event_participants_postgresql(event_id)
        except Exception as e:
            logger.error(f"❌ Error retrieving participants for event {event_id}: {e}")
            return []

    def _get_event_participants_postgresql(self, event_id: int) -> List[Dict[str, Any]]:
        """Get participants for an event from PostgreSQL"""
        try:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    query = """
                    SELECT DISTINCT
                        part.id,
                        part.name,
                        part.phone_number as phone,
                        part.email,
                        part.organization,
                        part.is_active
                    FROM partners part
                    JOIN partner_program_events ppe ON part.id = ppe.partner_id
                    WHERE ppe.event_id = %s AND part.is_active = true
                    ORDER BY part.name
                    """
                    cursor.execute(query, (event_id,))
                    results = cursor.fetchall()
                    
                    participants = [dict(row) for row in results]
                    logger.info(f"👥 Retrieved {len(participants)} participants for event {event_id}")
                    return participants
        except Exception as e:
            logger.error(f"❌ PostgreSQL error getting event participants: {e}")
            return []

    def _get_event_participants_sqlite(self, event_id: int) -> List[Dict[str, Any]]:
        """Get participants for an event from SQLite (fallback)"""
        # Return dummy data for SQLite
        return [
            {
                'id': 1,
                'name': 'Test Participant',
                'phone': '+1234567890',
                'email': 'test@example.com',
                'organization': 'Test Org',
                'is_active': True
            }
        ]
