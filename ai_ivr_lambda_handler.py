"""
AI IVR Lambda Handler - pg8000 Version  
Using pure Python pg8000 driver to avoid compilation issues in Lambda
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import pg8000 (pure Python PostgreSQL driver)
try:
    import pg8000.native
    DB_AVAILABLE = True
    logger.info("✅ pg8000 driver imported successfully")
except ImportError as e:
    logger.error(f"❌ pg8000 import failed: {e}")
    DB_AVAILABLE = False

# Database configuration
DB_CONFIG = {
    'host': 'lwl-pg-us-2.czq8mh1i8p1n.us-west-2.rds.amazonaws.com',
    'port': 5432,
    'database': 'lwl_pg_us_2',
    'user': 'lwl_db_user',
    'password': 'Lwl2024pass!'
}

def get_db_connection():
    """Get database connection using pg8000"""
    if not DB_AVAILABLE:
        return None
    
    try:
        connection = pg8000.native.Connection(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            database=DB_CONFIG['database'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        logger.info("✅ Database connection established with pg8000")
        return connection
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return None

def get_partner_info(partner_id: int) -> Optional[Dict[str, Any]]:
    """Get partner information from database"""
    connection = get_db_connection()
    if not connection:
        logger.warning("⚠️ No database connection - using fallback")
        return None
    
    try:
        query = """
        SELECT 
            partner_id,
            partner_name,
            contact_type,
            is_active
        FROM partners 
        WHERE partner_id = %s AND is_active = true
        """
        
        result = connection.run(query, [partner_id])
        
        if result:
            row = result[0]
            return {
                'partner_id': row[0],
                'name': row[1],
                'type': row[2],
                'is_active': row[3],
                'status': 'active' if row[3] else 'inactive'
            }
        
        logger.warning(f"⚠️ No partner found with ID {partner_id}")
        return None
        
    except Exception as e:
        logger.error(f"❌ Error fetching partner info: {e}")
        return None
    finally:
        try:
            connection.close()
        except:
            pass

def get_program_event_info(program_event_id: int) -> Optional[Dict[str, Any]]:
    """Get program event information from database"""
    connection = get_db_connection()
    if not connection:
        logger.warning("⚠️ No database connection - using fallback")
        return None
    
    try:
        query = """
        SELECT 
            program_event_id,
            event_name,
            program_id
        FROM program_events 
        WHERE program_event_id = %s
        """
        
        result = connection.run(query, [program_event_id])
        
        if result:
            row = result[0]
            return {
                'program_event_id': row[0],
                'event_name': row[1],
                'program_id': row[2],
                'event_type': 'general',
                'event_status': 'active'
            }
        
        logger.warning(f"⚠️ No program event found with ID {program_event_id}")
        return None
        
    except Exception as e:
        logger.error(f"❌ Error fetching program event info: {e}")
        return None
    finally:
        try:
            connection.close()
        except:
            pass

def get_call_context(partner_id: int, program_event_id: int) -> Dict[str, Any]:
    """Get comprehensive call context from database"""
    try:
        # Get partner information
        partner_info = get_partner_info(partner_id)
        if not partner_info:
            logger.warning(f"⚠️ Partner {partner_id} not found in database - using fallback")
            partner_info = {
                'partner_id': partner_id,
                'name': f'Partner {partner_id}',
                'type': 'general',
                'status': 'unknown_from_db'
            }
        
        # Get program event information
        program_event_info = get_program_event_info(program_event_id)
        if not program_event_info:
            logger.warning(f"⚠️ Program event {program_event_id} not found in database - using fallback")
            program_event_info = {
                'program_event_id': program_event_id,
                'event_name': f'Event {program_event_id}',
                'event_type': 'general',
                'event_status': 'unknown_from_db'
            }
        
        context = {
            'partner_info': partner_info,
            'program_event_info': program_event_info,
            'call_timestamp': datetime.utcnow().isoformat(),
            'database_source': 'postgresql_pg8000' if DB_AVAILABLE else 'no_database'
        }
        
        logger.info(f"✅ Call context retrieved for partner {partner_id}, event {program_event_id}")
        return context
        
    except Exception as e:
        logger.error(f"❌ Error getting call context: {e}")
        # Return basic fallback context
        return {
            'partner_info': {
                'partner_id': partner_id,
                'name': f'Partner {partner_id}',
                'type': 'general',
                'status': 'error_fallback'
            },
            'program_event_info': {
                'program_event_id': program_event_id,
                'event_name': f'Event {program_event_id}',
                'event_type': 'general',
                'event_status': 'error_fallback'
            },
            'call_timestamp': datetime.utcnow().isoformat(),
            'database_source': 'error_fallback',
            'error': str(e)
        }

def make_ivr_call(partner_id: int, program_event_id: int, call_mode: str = 'simulation') -> Dict[str, Any]:
    """Make IVR call with database context"""
    try:
        logger.info(f"🔄 Starting IVR call: partner_id={partner_id}, program_event_id={program_event_id}, mode={call_mode}")
        
        # Get call context from database
        call_context = get_call_context(partner_id, program_event_id)
        
        # Generate call ID
        call_id = f"ivr_call_{partner_id}_{program_event_id}_{int(datetime.utcnow().timestamp())}"
        
        # Simulate call based on mode
        if call_mode == 'simulation':
            call_result = {
                'call_id': call_id,
                'status': 'simulated_success',
                'partner_info': call_context['partner_info'],
                'program_event_info': call_context['program_event_info'],
                'call_timestamp': call_context['call_timestamp'],
                'database_source': call_context['database_source'],
                'simulation_message': f"Simulated IVR call to {call_context['partner_info']['name']} about {call_context['program_event_info']['event_name']}",
                'database_available': DB_AVAILABLE
            }
            
            if 'error' in call_context:
                call_result['database_error'] = call_context['error']
            
            logger.info(f"✅ Simulated IVR call completed: {call_id}")
            return call_result
        
        else:
            # For actual calls, would integrate with Twilio here
            logger.info(f"🔄 Actual IVR call not implemented yet for mode: {call_mode}")
            return {
                'call_id': call_id,
                'status': 'not_implemented',
                'message': f'Actual IVR calls not implemented for mode: {call_mode}',
                'partner_info': call_context['partner_info'],
                'program_event_info': call_context['program_event_info']
            }
    
    except Exception as e:
        logger.error(f"❌ IVR call failed: {e}")
        return {
            'error': f'IVR call failed: {str(e)}',
            'partner_id': partner_id,
            'program_event_id': program_event_id,
            'call_mode': call_mode
        }

def inspect_database() -> Dict[str, Any]:
    """Safely inspect database contents to understand the data structure"""
    connection = get_db_connection()
    if not connection:
        return {'error': 'No database connection'}
    
    try:
        result = {}
        
        # First, just list all tables
        tables_query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
        """
        tables = connection.run(tables_query)
        result['tables'] = [table[0] for table in tables] if tables else []
        
        return result
        
    except Exception as e:
        return {'error': str(e), 'detail': 'Failed to query database tables'}
    finally:
        try:
            connection.close()
        except:
            pass

def lambda_handler(event, context):
    """AWS Lambda handler for AI IVR API"""
    try:
        logger.info(f"🔄 Lambda event: {json.dumps(event, default=str)}")
        
        # Parse the request
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = event
        
        # Handle different endpoints
        http_method = event.get('httpMethod', 'POST')
        path = event.get('path', '/ivr/make-call')
        
        if path == '/health' or (http_method == 'GET' and 'health' in path):
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'status': 'healthy',
                    'service': 'ai-ivr-api',
                    'timestamp': datetime.utcnow().isoformat(),
                    'database_driver': 'pg8000',
                    'database_available': DB_AVAILABLE,
                    'database_host': DB_CONFIG['host']
                })
            }
        
        elif path == '/ivr/inspect-db' or 'inspect-db' in path:
            # Safely inspect database contents
            inspection_result = inspect_database()
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(inspection_result, default=str)
            }
        
        elif path == '/ivr/make-call' or 'make-call' in path:
            # Extract parameters
            partner_id = int(body.get('partner_id', 1))
            program_event_id = int(body.get('program_event_id', 1))
            call_mode = body.get('call_mode', 'simulation')
            
            # Make IVR call
            result = make_ivr_call(partner_id, program_event_id, call_mode)
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(result, default=str)
            }
        
        else:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Endpoint not found'})
            }
    
    except Exception as e:
        logger.error(f"❌ Lambda handler error: {e}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': f'Internal server error: {str(e)}'})
        }