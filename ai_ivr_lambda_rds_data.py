"""
AI IVR Lambda Handler - RDS Data API Version
Using AWS RDS Data API to avoid psycopg2 driver issues in Lambda
"""

import json
import logging
import boto3
import os
from datetime import datetime
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize AWS clients
rds_data_client = boto3.client('rds-data')

# RDS cluster configuration - using Aurora Serverless with Data API
RDS_CLUSTER_ARN = os.getenv('RDS_CLUSTER_ARN', 'arn:aws:rds:us-west-2:YOUR_ACCOUNT:cluster:lwl-aurora-cluster')
RDS_SECRET_ARN = os.getenv('RDS_SECRET_ARN', 'arn:aws:secretsmanager:us-west-2:YOUR_ACCOUNT:secret:lwl-db-credentials')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'lwl_pg_us_2')

def execute_sql(sql: str, parameters: list = None) -> Dict[Any, Any]:
    """Execute SQL using RDS Data API"""
    try:
        params = {
            'resourceArn': RDS_CLUSTER_ARN,
            'secretArn': RDS_SECRET_ARN,
            'database': DATABASE_NAME,
            'sql': sql
        }
        
        if parameters:
            params['parameters'] = parameters
            
        response = rds_data_client.execute_statement(**params)
        return response
    except Exception as e:
        logger.error(f"❌ RDS Data API error: {e}")
        return None

def get_partner_info(partner_id: int) -> Optional[Dict[str, Any]]:
    """Get partner information using RDS Data API"""
    try:
        sql = """
        SELECT 
            partner_id,
            partner_name,
            partner_type,
            contact_email,
            phone_number,
            address,
            city,
            state,
            country,
            website,
            status
        FROM partners 
        WHERE partner_id = :partner_id AND status = 'active'
        """
        
        parameters = [
            {'name': 'partner_id', 'value': {'longValue': partner_id}}
        ]
        
        response = execute_sql(sql, parameters)
        
        if response and 'records' in response and response['records']:
            record = response['records'][0]
            return {
                'partner_id': record[0]['longValue'] if record[0] else None,
                'name': record[1]['stringValue'] if record[1] else 'Unknown Partner',
                'type': record[2]['stringValue'] if record[2] else 'general',
                'contact_email': record[3]['stringValue'] if record[3] else None,
                'phone_number': record[4]['stringValue'] if record[4] else None,
                'address': record[5]['stringValue'] if record[5] else None,
                'city': record[6]['stringValue'] if record[6] else None,
                'state': record[7]['stringValue'] if record[7] else None,
                'country': record[8]['stringValue'] if record[8] else None,
                'website': record[9]['stringValue'] if record[9] else None,
                'status': record[10]['stringValue'] if record[10] else 'active'
            }
        
        logger.warning(f"⚠️ No partner found with ID {partner_id}")
        return None
        
    except Exception as e:
        logger.error(f"❌ Error fetching partner info: {e}")
        return None

def get_program_event_info(program_event_id: int) -> Optional[Dict[str, Any]]:
    """Get program event information using RDS Data API"""
    try:
        sql = """
        SELECT 
            pe.program_event_id,
            pe.event_name,
            pe.event_type,
            pe.start_date,
            pe.end_date,
            pe.description,
            pe.location,
            pe.max_participants,
            pe.current_participants,
            pe.registration_deadline,
            pe.event_status,
            p.program_name,
            p.program_description,
            p.category
        FROM program_events pe
        LEFT JOIN programs p ON pe.program_id = p.program_id
        WHERE pe.program_event_id = :program_event_id 
        AND pe.event_status IN ('active', 'upcoming', 'registration_open')
        """
        
        parameters = [
            {'name': 'program_event_id', 'value': {'longValue': program_event_id}}
        ]
        
        response = execute_sql(sql, parameters)
        
        if response and 'records' in response and response['records']:
            record = response['records'][0]
            return {
                'program_event_id': record[0]['longValue'] if record[0] else None,
                'event_name': record[1]['stringValue'] if record[1] else 'Unknown Event',
                'event_type': record[2]['stringValue'] if record[2] else 'general',
                'start_date': record[3]['stringValue'] if record[3] else None,
                'end_date': record[4]['stringValue'] if record[4] else None,
                'description': record[5]['stringValue'] if record[5] else None,
                'location': record[6]['stringValue'] if record[6] else None,
                'max_participants': record[7]['longValue'] if record[7] else 0,
                'current_participants': record[8]['longValue'] if record[8] else 0,
                'registration_deadline': record[9]['stringValue'] if record[9] else None,
                'event_status': record[10]['stringValue'] if record[10] else 'active',
                'program_name': record[11]['stringValue'] if record[11] else None,
                'program_description': record[12]['stringValue'] if record[12] else None,
                'category': record[13]['stringValue'] if record[13] else None
            }
        
        logger.warning(f"⚠️ No program event found with ID {program_event_id}")
        return None
        
    except Exception as e:
        logger.error(f"❌ Error fetching program event info: {e}")
        return None

def get_call_context(partner_id: int, program_event_id: int) -> Dict[str, Any]:
    """Get comprehensive call context from database using RDS Data API"""
    try:
        # Get partner information
        partner_info = get_partner_info(partner_id)
        if not partner_info:
            logger.warning(f"⚠️ Partner {partner_id} not found - using fallback")
            partner_info = {
                'partner_id': partner_id,
                'name': f'Partner {partner_id}',
                'type': 'general',
                'status': 'unknown'
            }
        
        # Get program event information
        program_event_info = get_program_event_info(program_event_id)
        if not program_event_info:
            logger.warning(f"⚠️ Program event {program_event_id} not found - using fallback")
            program_event_info = {
                'program_event_id': program_event_id,
                'event_name': f'Event {program_event_id}',
                'event_type': 'general',
                'event_status': 'unknown'
            }
        
        context = {
            'partner_info': partner_info,
            'program_event_info': program_event_info,
            'call_timestamp': datetime.utcnow().isoformat(),
            'database_source': 'rds_data_api'
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
            'database_source': 'fallback_data',
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
                'simulation_message': f"Simulated IVR call to {call_context['partner_info']['name']} about {call_context['program_event_info']['event_name']}"
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
                    'database_api': 'rds_data_api'
                })
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