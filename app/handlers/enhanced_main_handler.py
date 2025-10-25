"""
Enhanced Main Handler for LangGraph AI Telecaller
Integrates with PostgreSQL database and LangGraph service
"""

import json
import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

# Import services
try:
    from app.database.postgres_models import telecaller_db, pg_manager
    from app.services.langgraph_telecaller_service import langgraph_telecaller
    from app.services.twilio_service import TwilioService
    DATABASE_MODE = "postgresql"
    logger.info("✅ Using PostgreSQL database (lwl_pg_us_2)")
except Exception as e:
    logger.error(f"❌ Failed to initialize PostgreSQL: {e}")
    # Fallback to embedded database for development
    try:
        from app.database.embedded_db import EmbeddedDatabaseManager, EmbeddedDatabaseQueries
        db_manager = EmbeddedDatabaseManager()
        db_queries = EmbeddedDatabaseQueries(db_manager)
        DATABASE_MODE = "embedded"
        logger.warning("⚠️ Using embedded SQLite database as fallback")
    except Exception as fallback_error:
        logger.error(f"❌ Failed to initialize fallback database: {fallback_error}")
        raise

# Initialize services
twilio_service = TwilioService()

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Enhanced Lambda handler for LangGraph AI Telecaller system
    
    Routes:
    - POST /call/start - Start a new AI telecaller call
    - POST /call/webhook - Handle Twilio webhooks
    - GET /call/status/{call_id} - Get call status
    - POST /campaign/execute - Execute a campaign
    - GET /health - Health check
    - GET /programs - Get available programs
    - GET /partners - Get partners
    """
    
    try:
        # Parse the request
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '/')
        query_params = event.get('queryStringParameters', {}) or {}
        body = event.get('body')
        
        if body:
            try:
                body = json.loads(body)
            except json.JSONDecodeError:
                body = {}
        else:
            body = {}
        
        logger.info(f"Processing {http_method} {path}")
        
        # Route the request
        if path == '/health':
            return handle_health_check()
        elif path == '/programs':
            return handle_get_programs(query_params)
        elif path == '/partners':
            return handle_get_partners(query_params)
        elif path == '/call/start' and http_method == 'POST':
            return handle_start_call(body)
        elif path == '/call/webhook' and http_method == 'POST':
            return handle_call_webhook(body)
        elif path.startswith('/call/status/'):
            call_id = path.split('/')[-1]
            return handle_get_call_status(call_id)
        elif path == '/campaign/execute' and http_method == 'POST':
            return handle_execute_campaign(body)
        else:
            return create_response(404, {'error': 'Route not found'})
            
    except Exception as e:
        logger.error(f"Handler error: {e}")
        return create_response(500, {'error': 'Internal server error', 'details': str(e)})

def handle_health_check() -> Dict[str, Any]:
    """Health check endpoint"""
    try:
        # Test database connection
        db_status = "unknown"
        
        if DATABASE_MODE == "postgresql":
            try:
                programs = telecaller_db.get_programs(limit=1)
                db_status = "connected"
            except Exception as e:
                db_status = f"error: {str(e)}"
        else:
            db_status = "embedded_fallback"
        
        # Test AI service
        ai_status = "unknown"
        try:
            # Quick test of the LangGraph service
            test_result = langgraph_telecaller.process_call(
                {"test": "health_check"}, 
                "Hello"
            )
            ai_status = "operational" if test_result.get("success") else "error"
        except Exception as e:
            ai_status = f"error: {str(e)}"
        
        return create_response(200, {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': {
                'mode': DATABASE_MODE,
                'status': db_status
            },
            'ai_service': {
                'status': ai_status,
                'model': os.getenv('AI_MODEL', 'gpt-4o-mini')
            },
            'environment': {
                'OPENAI_API_KEY': bool(os.getenv('OPENAI_API_KEY')),
                'TWILIO_ACCOUNT_SID': bool(os.getenv('TWILIO_ACCOUNT_SID')),
                'DB_HOST': bool(os.getenv('DB_HOST')),
                'DB_NAME': os.getenv('DB_NAME', 'unknown')
            }
        })
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return create_response(500, {'error': 'Health check failed', 'details': str(e)})

def handle_get_programs(query_params: Dict[str, Any]) -> Dict[str, Any]:
    """Get available programs"""
    try:
        limit = int(query_params.get('limit', 50))
        
        if DATABASE_MODE == "postgresql":
            programs = telecaller_db.get_programs(limit=limit)
        else:
            # Fallback for embedded database
            programs = []
        
        return create_response(200, {
            'programs': programs,
            'count': len(programs),
            'database_mode': DATABASE_MODE
        })
        
    except Exception as e:
        logger.error(f"Error fetching programs: {e}")
        return create_response(500, {'error': 'Failed to fetch programs', 'details': str(e)})

def handle_get_partners(query_params: Dict[str, Any]) -> Dict[str, Any]:
    """Get available partners"""
    try:
        partner_type = query_params.get('type')
        limit = int(query_params.get('limit', 50))
        
        if DATABASE_MODE == "postgresql":
            partners = telecaller_db.get_partners(partner_type=partner_type, limit=limit)
        else:
            # Fallback for embedded database
            partners = []
        
        return create_response(200, {
            'partners': partners,
            'count': len(partners),
            'filter': {'type': partner_type} if partner_type else None,
            'database_mode': DATABASE_MODE
        })
        
    except Exception as e:
        logger.error(f"Error fetching partners: {e}")
        return create_response(500, {'error': 'Failed to fetch partners', 'details': str(e)})

def handle_start_call(body: Dict[str, Any]) -> Dict[str, Any]:
    """Start a new AI telecaller call"""
    try:
        # Validate required parameters
        required_fields = ['to_number']
        missing_fields = [field for field in required_fields if field not in body]
        if missing_fields:
            return create_response(400, {
                'error': 'Missing required fields',
                'missing': missing_fields
            })
        
        # Extract call parameters
        to_number = body['to_number']
        program_event_id = body.get('program_event_id')
        partner_id = body.get('partner_id')
        
        # Prepare call context
        call_context = {
            'to_number': to_number,
            'program_event_id': program_event_id,
            'partner_id': partner_id,
            'call_start_time': datetime.now(),
            'initiated_by': 'api'
        }
        
        # Start the call using Twilio
        try:
            call_result = twilio_service.make_call(
                to_number=to_number,
                webhook_url=os.getenv('WEBHOOK_URL', 'http://localhost:5000/call/webhook'),
                call_context=call_context
            )
            
            if call_result.get('success'):
                call_context['call_sid'] = call_result['call_sid']
                
                # Log the call initiation
                if DATABASE_MODE == "postgresql":
                    call_log_data = {
                        'program_event_id': program_event_id,
                        'partner_id': partner_id,
                        'call_sid': call_result['call_sid'],
                        'caller_number': twilio_service.from_number,
                        'recipient_number': to_number,
                        'call_start_time': datetime.now(),
                        'call_status': 'initiated',
                        'ai_prompt_used': 'LangGraph AI Telecaller'
                    }
                    
                    call_log_id = telecaller_db.create_call_log(call_log_data)
                    logger.info(f"Call logged with ID: {call_log_id}")
                
                return create_response(200, {
                    'success': True,
                    'call_sid': call_result['call_sid'],
                    'status': 'initiated',
                    'message': 'Call started successfully'
                })
            else:
                return create_response(500, {
                    'error': 'Failed to start call',
                    'details': call_result.get('error')
                })
                
        except Exception as e:
            logger.error(f"Error starting call: {e}")
            return create_response(500, {
                'error': 'Failed to start call',
                'details': str(e)
            })
            
    except Exception as e:
        logger.error(f"Error in start_call: {e}")
        return create_response(500, {'error': 'Failed to process call request', 'details': str(e)})

def handle_call_webhook(body: Dict[str, Any]) -> Dict[str, Any]:
    """Handle Twilio call webhooks using LangGraph"""
    try:
        # Extract Twilio parameters
        call_sid = body.get('CallSid')
        call_status = body.get('CallStatus')
        user_input = body.get('SpeechResult', '') or body.get('Digits', '')
        
        logger.info(f"Webhook received - CallSid: {call_sid}, Status: {call_status}")
        
        if call_status in ['ringing', 'in-progress']:
            # Prepare call context for LangGraph
            call_context = {
                'call_sid': call_sid,
                'call_status': call_status,
                'caller_number': body.get('From'),
                'recipient_number': body.get('To'),
                'timestamp': datetime.now()
            }
            
            # Add program/partner context if available (from call log)
            if DATABASE_MODE == "postgresql":
                try:
                    call_logs = telecaller_db.get_call_logs(limit=1)
                    matching_log = next((log for log in call_logs if log.get('call_sid') == call_sid), None)
                    if matching_log:
                        call_context['program_event_id'] = matching_log.get('program_event_id')
                        call_context['partner_id'] = matching_log.get('partner_id')
                except Exception as e:
                    logger.warning(f"Could not fetch call context: {e}")
            
            # Process with LangGraph AI
            ai_result = langgraph_telecaller.process_call(call_context, user_input)
            
            if ai_result.get('success'):
                ai_response = ai_result['response']
                
                # Generate TwiML response
                twiml_response = f"""
                <?xml version="1.0" encoding="UTF-8"?>
                <Response>
                    <Say voice="alice">{ai_response}</Say>
                    <Gather input="speech" timeout="5" speechTimeout="2" action="/call/webhook" method="POST">
                        <Say voice="alice">Please respond when you're ready.</Say>
                    </Gather>
                    <Redirect>/call/webhook</Redirect>
                </Response>
                """
                
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/xml'},
                    'body': twiml_response
                }
            else:
                # Fallback response
                fallback_twiml = """
                <?xml version="1.0" encoding="UTF-8"?>
                <Response>
                    <Say voice="alice">I apologize, but I'm experiencing technical difficulties. Let me transfer you to a human representative. Thank you for your patience.</Say>
                    <Hangup/>
                </Response>
                """
                
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/xml'},
                    'body': fallback_twiml
                }
        
        elif call_status in ['completed', 'failed', 'busy', 'no-answer']:
            # Call ended - update call log
            if DATABASE_MODE == "postgresql":
                try:
                    call_logs = telecaller_db.get_call_logs(limit=50)
                    matching_log = next((log for log in call_logs if log.get('call_sid') == call_sid), None)
                    if matching_log:
                        update_data = {
                            'call_status': call_status,
                            'call_end_time': datetime.now(),
                            'call_duration_seconds': body.get('CallDuration', 0)
                        }
                        telecaller_db.update_call_log(matching_log['call_log_id'], update_data)
                        logger.info(f"Call log updated for {call_sid}")
                except Exception as e:
                    logger.error(f"Error updating call log: {e}")
            
            return create_response(200, {'message': 'Call completed'})
        
        else:
            return create_response(200, {'message': 'Webhook received'})
            
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        # Always return a valid TwiML response for Twilio
        error_twiml = """
        <?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Say voice="alice">I apologize, but there was an error processing your call. Please try again later.</Say>
            <Hangup/>
        </Response>
        """
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/xml'},
            'body': error_twiml
        }

def handle_get_call_status(call_id: str) -> Dict[str, Any]:
    """Get status of a specific call"""
    try:
        if DATABASE_MODE == "postgresql":
            call_logs = telecaller_db.get_call_logs(limit=100)
            matching_log = next((log for log in call_logs if log.get('call_sid') == call_id), None)
            
            if matching_log:
                return create_response(200, {
                    'call_sid': call_id,
                    'status': matching_log.get('call_status'),
                    'duration': matching_log.get('call_duration_seconds'),
                    'outcome': matching_log.get('outcome'),
                    'summary': matching_log.get('conversation_summary'),
                    'created_at': matching_log.get('created_at').isoformat() if matching_log.get('created_at') else None
                })
            else:
                return create_response(404, {'error': 'Call not found'})
        else:
            return create_response(503, {'error': 'Call status not available in embedded mode'})
            
    except Exception as e:
        logger.error(f"Error fetching call status: {e}")
        return create_response(500, {'error': 'Failed to fetch call status', 'details': str(e)})

def handle_execute_campaign(body: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a telecaller campaign"""
    try:
        # Extract campaign parameters
        program_event_id = body.get('program_event_id')
        partner_ids = body.get('partner_ids', [])
        
        if not program_event_id:
            return create_response(400, {'error': 'program_event_id is required'})
        
        if not partner_ids:
            return create_response(400, {'error': 'partner_ids list is required'})
        
        results = []
        
        for partner_id in partner_ids:
            try:
                # Get partner details
                if DATABASE_MODE == "postgresql":
                    partner = telecaller_db.get_partner_by_id(partner_id)
                    if not partner:
                        results.append({
                            'partner_id': partner_id,
                            'success': False,
                            'error': 'Partner not found'
                        })
                        continue
                    
                    # Extract phone number from contact field
                    contact = partner.get('contact', '')
                    # Simple phone number extraction (you may need more sophisticated parsing)
                    phone_number = contact if contact.startswith('+') else f"+1{contact.replace('-', '').replace(' ', '')}"
                    
                    # Start call
                    call_data = {
                        'to_number': phone_number,
                        'program_event_id': program_event_id,
                        'partner_id': partner_id
                    }
                    
                    call_result = handle_start_call(call_data)
                    
                    if call_result.get('statusCode') == 200:
                        body_data = json.loads(call_result.get('body', '{}'))
                        results.append({
                            'partner_id': partner_id,
                            'partner_name': partner.get('partner_name'),
                            'success': True,
                            'call_sid': body_data.get('call_sid')
                        })
                    else:
                        results.append({
                            'partner_id': partner_id,
                            'success': False,
                            'error': 'Failed to start call'
                        })
                        
            except Exception as e:
                logger.error(f"Error calling partner {partner_id}: {e}")
                results.append({
                    'partner_id': partner_id,
                    'success': False,
                    'error': str(e)
                })
        
        successful_calls = len([r for r in results if r.get('success')])
        
        return create_response(200, {
            'campaign_id': f"campaign_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'program_event_id': program_event_id,
            'total_calls': len(partner_ids),
            'successful_calls': successful_calls,
            'failed_calls': len(partner_ids) - successful_calls,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error executing campaign: {e}")
        return create_response(500, {'error': 'Failed to execute campaign', 'details': str(e)})

def create_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Create standardized Lambda response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
        },
        'body': json.dumps(body, default=str)
    }

# Flask app for local development
if __name__ == "__main__":
    from flask import Flask, request
    
    app = Flask(__name__)
    
    @app.route('/<path:path>', methods=['GET', 'POST', 'OPTIONS'])
    def proxy(path=''):
        event = {
            'httpMethod': request.method,
            'path': f'/{path}',
            'queryStringParameters': dict(request.args),
            'body': request.get_data(as_text=True) if request.data else None
        }
        
        response = lambda_handler(event, None)
        
        return (
            response['body'],
            response['statusCode'],
            response['headers']
        )
    
    app.run(debug=True, host='0.0.0.0', port=5000)
