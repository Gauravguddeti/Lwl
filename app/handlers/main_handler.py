import json
import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime
from app.models.data_models import CallStatus, ResponseType

# Configure logging
logger = logging.getLogger(__name__)

# Database setup - use embedded database if external not available
try:
    from app.database.connection import db_queries
    DATABASE_MODE = "external"
    logger.info("✅ Using external database connection")
except Exception as e:
    logger.warning(f"⚠️ External database unavailable: {e}")
    from app.database.embedded_db import EmbeddedDatabaseManager, EmbeddedDatabaseQueries
    
    # Initialize embedded database
    db_manager = EmbeddedDatabaseManager()
    db_queries = EmbeddedDatabaseQueries(db_manager)
    DATABASE_MODE = "embedded"
    logger.info("✅ Using embedded SQLite database for testing")

# Initialize call orchestrator
from app.services.call_orchestrator import CallOrchestrator
call_orchestrator = CallOrchestrator()

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for AI Telecaller system
    
    This handler routes different types of requests:
    - Execute scheduled job
    - Execute single call
    - Handle call webhook
    - Get call status
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
                logger.error("Invalid JSON in request body")
                return create_response(400, {'error': 'Invalid JSON in request body'})
        
        logger.info(f"Processing {http_method} request to {path}")
        
        # Route the request based on path
        if path == '/execute-job' and http_method == 'POST':
            return handle_execute_job(body)
        
        elif path == '/execute-call' and http_method == 'POST':
            return handle_execute_call(body)
        
        elif path == '/call-webhook' and http_method == 'POST':
            return handle_call_webhook(body)
        
        elif path == '/call-status' and http_method == 'GET':
            return handle_get_call_status(query_params)
        
        elif path == '/scheduled-events' and http_method == 'GET':
            return handle_get_scheduled_events(query_params)
        
        elif path == '/health' and http_method == 'GET':
            return handle_health_check()
        
        else:
            return create_response(404, {'error': 'Endpoint not found'})
    
    except Exception as e:
        logger.error(f"Unhandled error in lambda_handler: {e}")
        return create_response(500, {'error': 'Internal server error', 'message': str(e)})

def handle_execute_job(body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle execution of a scheduled job
    
    Expected body:
    {
        "job_id": 1
    }
    """
    
    if not body or 'job_id' not in body:
        return create_response(400, {'error': 'job_id is required'})
    
    job_id = body['job_id']
    
    try:
        logger.info(f"Executing scheduled job {job_id}")
        result = call_orchestrator.execute_scheduled_job(job_id)
        
        return create_response(200, {
            'message': f'Scheduled job {job_id} executed successfully',
            'result': result
        })
    
    except Exception as e:
        logger.error(f"Failed to execute scheduled job {job_id}: {e}")
        return create_response(500, {
            'error': 'Failed to execute scheduled job',
            'job_id': job_id,
            'message': str(e)
        })

def handle_execute_call(body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle execution of a single call
    
    Expected body:
    {
        "event_id": 1,
        "school_name": "Delhi Public School",
        "program_name": "Cambridge Summer Programme",
        ... other call event fields
    }
    """
    
    if not body:
        return create_response(400, {'error': 'Request body is required'})
    
    try:
        # Convert body to CallEvent (simplified - in real implementation you'd validate all fields)
        from app.services.call_orchestrator import CallOrchestrationService
        orchestrator = CallOrchestrationService()
        
        # Create CallEvent from body data
        call_event = orchestrator._dict_to_call_event(body)
        
        logger.info(f"Executing single call for event {call_event.event_id}")
        result = call_orchestrator.execute_single_call(call_event)
        
        return create_response(200, {
            'message': 'Call executed successfully',
            'result': result
        })
    
    except Exception as e:
        logger.error(f"Failed to execute single call: {e}")
        return create_response(500, {
            'error': 'Failed to execute call',
            'message': str(e)
        })

def handle_call_webhook(body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle Twilio webhook for call status updates
    
    Expected body (from Twilio):
    {
        "CallSid": "CA1234567890",
        "CallStatus": "completed",
        "From": "+1234567890",
        "To": "+0987654321",
        "Duration": "180",
        ... other Twilio fields
    }
    """
    
    if not body:
        return create_response(400, {'error': 'Webhook body is required'})
    
    try:
        call_sid = body.get('CallSid')
        call_status = body.get('CallStatus')
        duration = body.get('Duration')
        
        if not call_sid:
            return create_response(400, {'error': 'CallSid is required'})
        
        logger.info(f"Received webhook for call {call_sid}: {call_status}")
        
        # Determine response type based on call status
        response_type = map_twilio_status_to_response_type(call_status, body)
        
        # Handle the call outcome
        success = call_orchestrator.handle_call_outcome(
            call_sid=call_sid,
            outcome=response_type,
            conversation_summary=f"Call status: {call_status}, Duration: {duration}s"
        )
        
        if success:
            return create_response(200, {
                'message': 'Webhook processed successfully',
                'call_sid': call_sid,
                'status': call_status
            })
        else:
            return create_response(500, {
                'error': 'Failed to process webhook',
                'call_sid': call_sid
            })
    
    except Exception as e:
        logger.error(f"Failed to process webhook: {e}")
        return create_response(500, {
            'error': 'Failed to process webhook',
            'message': str(e)
        })

def handle_get_call_status(query_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get status of a specific call or job
    
    Query parameters:
    - call_sid: Twilio call SID
    - job_id: Scheduled job ID
    - event_id: Scheduled job event ID
    """
    
    call_sid = query_params.get('call_sid')
    job_id = query_params.get('job_id')
    event_id = query_params.get('event_id')
    
    try:
        if call_sid:
            # Get call status from Twilio
            from app.services.twilio_service import twilio_service
            call_status = twilio_service.get_call_status(call_sid)
            
            return create_response(200, {
                'call_sid': call_sid,
                'status': call_status.to_audit_dict() if call_status else None
            })
        
        elif job_id:
            # Get scheduled job events
            events = db_queries.get_scheduled_job_events(int(job_id))
            
            return create_response(200, {
                'job_id': job_id,
                'events': [dict(event) for event in events] if events else []
            })
        
        elif event_id:
            # Get specific event status (would need to implement this query)
            return create_response(200, {
                'event_id': event_id,
                'message': 'Event status lookup not yet implemented'
            })
        
        else:
            return create_response(400, {
                'error': 'Please provide call_sid, job_id, or event_id'
            })
    
    except Exception as e:
        logger.error(f"Failed to get call status: {e}")
        return create_response(500, {
            'error': 'Failed to get call status',
            'message': str(e)
        })

def handle_get_scheduled_events(query_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get all scheduled job events, optionally filtered by job_id
    
    Query parameters:
    - job_id: Filter by specific job ID (optional)
    """
    
    job_id = query_params.get('job_id')
    
    try:
        if job_id:
            events = db_queries.get_scheduled_job_events(int(job_id))
        else:
            events = db_queries.get_scheduled_job_events()
        
        return create_response(200, {
            'events': [dict(event) for event in events] if events else [],
            'count': len(events) if events else 0
        })
    
    except Exception as e:
        logger.error(f"Failed to get scheduled events: {e}")
        return create_response(500, {
            'error': 'Failed to get scheduled events',
            'message': str(e)
        })

def handle_health_check() -> Dict[str, Any]:
    """Health check endpoint"""
    
    try:
        # Test database connection
        db_queries.db.get_connection()
        
        return create_response(200, {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'service': 'AI Telecaller System',
            'version': '1.0.0'
        })
    
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return create_response(500, {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        })

def map_twilio_status_to_response_type(call_status: str, webhook_body: Dict[str, Any]) -> str:
    """
    Map Twilio call status to our response type
    
    Args:
        call_status: Twilio call status
        webhook_body: Full webhook body with additional context
        
    Returns:
        Response type string
    """
    
    status_mapping = {
        'completed': ResponseType.INTERESTED,  # Default for completed calls
        'busy': ResponseType.BUSY,
        'no-answer': ResponseType.NO_ANSWER,
        'failed': ResponseType.NO_ANSWER,
        'canceled': ResponseType.NO_ANSWER,
    }
    
    # In a real implementation, you'd analyze call recordings or use AI
    # to determine the actual response type from the conversation
    
    return status_mapping.get(call_status, ResponseType.NO_ANSWER)

def create_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a properly formatted Lambda response
    
    Args:
        status_code: HTTP status code
        body: Response body dictionary
        
    Returns:
        Lambda response dictionary
    """
    
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization'
        },
        'body': json.dumps(body, default=str)  # default=str handles datetime serialization
    }
