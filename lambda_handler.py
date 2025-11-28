#!/usr/bin/env python3
"""
AI Telecaller System - Main Lambda Handler
==========================================

This is the main entry point for the AI-powered IVR + Messaging system deployed on AWS Lambda.
The system provides comprehensive voice calling, SMS, and email services with AI integration.

Key Features:
- AI-powered voice calls via Twilio
- SMS messaging via AWS SNS
- Email services via AWS SES (templated and raw)
- PostgreSQL database integration
- Real-time webhook handling
- Dashboard and analytics

Architecture:
- Flask API Gateway integration
- Serverless Lambda functions
- Multi-service orchestration
- Graceful error handling and fallbacks

Author: AI Telecaller Team
Version: 2.0.0
Last Updated: 2025-01-04
"""

import json
import logging
import os
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for AI Telecaller system
    
    This is the main entry point for all API requests to the AI Telecaller system.
    It handles routing, authentication, and response formatting for all services.
    
    Supported Endpoints:
    - Health checks and system status
    - Voice call initiation and management
    - SMS sending (single and bulk)
    - Email sending (SMTP, SES templated, SES raw)
    - Database operations and analytics
    - Webhook handling for Twilio events
    
    Args:
        event (Dict[str, Any]): AWS Lambda event object containing:
            - httpMethod: HTTP method (GET, POST, PUT, DELETE)
            - path: Request path
            - queryStringParameters: Query parameters
            - headers: Request headers
            - body: Request body (JSON string)
        context (Any): AWS Lambda context object with execution metadata
        
    Returns:
        Dict[str, Any]: API Gateway response containing:
            - statusCode: HTTP status code
            - headers: Response headers (including CORS)
            - body: JSON response body
            
    Example:
        >>> event = {
        ...     'httpMethod': 'POST',
        ...     'path': '/sms/send',
        ...     'body': '{"phone_number": "+1234567890", "message": "Hello!"}'
        ... }
        >>> response = lambda_handler(event, context)
        >>> print(response['statusCode'])  # 200
    """
    try:
        # Parse the request
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '/')
        query_params = event.get('queryStringParameters') or {}
        headers = event.get('headers', {})
        body = event.get('body', '')
        
        logger.info(f"Processing {http_method} request to {path}")
        
        # Handle CORS preflight
        if http_method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Api-Key'
                },
                'body': json.dumps({'message': 'CORS preflight'})
            }
        
        # Route to appropriate handler based on path
        if path == '/health' or path == '/':
            return handle_health_check()
        elif path.startswith('/sms'):
            return handle_sms_request(http_method, path, body, query_params)
        elif path.startswith('/email'):
            return handle_email_request(http_method, path, body, query_params)
        elif path.startswith('/templated-email'):
            return handle_templated_email_request(http_method, path, body, query_params)
        elif path.startswith('/call') or path.startswith('/ivr'):
            return handle_call_request(http_method, path, body, query_params)
        elif path.startswith('/webhook'):
            return handle_webhook_request(http_method, path, body, query_params)
        else:
            return create_error_response(404, 'Endpoint not found')
            
    except Exception as e:
        logger.error(f"Lambda handler error: {e}")
        return create_error_response(500, f'Internal server error: {str(e)}')

def handle_health_check() -> Dict[str, Any]:
    """
    Handle health check requests
    
    Returns:
        Dict: Health status response
    """
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({
            'status': 'healthy',
            'service': 'AI Telecaller System',
            'version': '2.0.0',
            'timestamp': '2025-01-04T00:00:00Z'
        })
    }

def handle_sms_request(method: str, path: str, body: str, query_params: Dict) -> Dict[str, Any]:
    """
    Handle SMS-related requests
    
    Args:
        method: HTTP method
        path: Request path
        body: Request body
        query_params: Query parameters
        
    Returns:
        Dict: SMS response
    """
    # Import SMS service
    try:
        from app.services.sms_service import SMSService
        sms_service = SMSService()
        
        if method == 'POST' and path == '/sms/send':
            data = json.loads(body) if body else {}
            result = sms_service.send_sms(data)
            return create_response(200 if result.get('success') else 400, result)
        elif method == 'POST' and path == '/sms/bulk':
            data = json.loads(body) if body else {}
            result = sms_service.send_bulk_sms(data)
            return create_response(200 if result.get('success') else 400, result)
        elif method == 'GET' and path == '/sms/status':
            result = sms_service.get_sms_status()
            return create_response(200 if result.get('success') else 400, result)
        else:
            return create_error_response(404, 'SMS endpoint not found')
    except Exception as e:
        logger.error(f"SMS request error: {e}")
        return create_error_response(500, f'SMS service error: {str(e)}')

def handle_email_request(method: str, path: str, body: str, query_params: Dict) -> Dict[str, Any]:
    """
    Handle email-related requests
    
    Args:
        method: HTTP method
        path: Request path
        body: Request body
        query_params: Query parameters
        
    Returns:
        Dict: Email response
    """
    try:
        from app.services.email_service import EmailService
        email_service = EmailService()
        
        if method == 'POST' and path == '/email':
            data = json.loads(body) if body else {}
            result = email_service.send_email(data)
            return create_response(200 if result.get('success') else 400, result)
        elif method == 'POST' and path == '/email/bulk':
            data = json.loads(body) if body else {}
            result = email_service.send_bulk_email(data)
            return create_response(200 if result.get('success') else 400, result)
        elif method == 'GET' and path == '/email/status':
            result = email_service.get_service_status()
            return create_response(200 if result.get('success') else 400, result)
        else:
            return create_error_response(404, 'Email endpoint not found')
    except Exception as e:
        logger.error(f"Email request error: {e}")
        return create_error_response(500, f'Email service error: {str(e)}')

def handle_templated_email_request(method: str, path: str, body: str, query_params: Dict) -> Dict[str, Any]:
    """
    Handle templated email requests
    
    Args:
        method: HTTP method
        path: Request path
        body: Request body
        query_params: Query parameters
        
    Returns:
        Dict: Templated email response
    """
    try:
        from app.services.ses_templated_email_service import SESTemplatedEmailService
        templated_service = SESTemplatedEmailService()
        
        if method == 'POST' and path == '/templated-email/create-templates':
            result = templated_service.create_ses_templates()
            return create_response(200 if result.get('success') else 400, result)
        elif method == 'POST' and path == '/templated-email/send-signup':
            data = json.loads(body) if body else {}
            result = templated_service.send_account_signup_email(data)
            return create_response(200 if result.get('success') else 400, result)
        elif method == 'POST' and path == '/templated-email/send-otp':
            data = json.loads(body) if body else {}
            result = templated_service.send_otp_email(data)
            return create_response(200 if result.get('success') else 400, result)
        else:
            return create_error_response(404, 'Templated email endpoint not found')
    except Exception as e:
        logger.error(f"Templated email request error: {e}")
        return create_error_response(500, f'Templated email service error: {str(e)}')

def handle_call_request(method: str, path: str, body: str, query_params: Dict) -> Dict[str, Any]:
    """
    Handle voice call requests
    
    Args:
        method: HTTP method
        path: Request path
        body: Request body
        query_params: Query parameters
        
    Returns:
        Dict: Call response
    """
    try:
        from app.services.twilio_service import TwilioService
        twilio_service = TwilioService()
        
        if method == 'POST' and path == '/call/start':
            data = json.loads(body) if body else {}
            result = twilio_service.make_call(
                to_number=data.get('to_number'),
                system_prompt=data.get('system_prompt', ''),
                call_metadata=data.get('call_metadata', {})
            )
            return create_response(200 if result.get('call_sid') else 400, result)
        else:
            return create_error_response(404, 'Call endpoint not found')
    except Exception as e:
        logger.error(f"Call request error: {e}")
        return create_error_response(500, f'Call service error: {str(e)}')

def handle_webhook_request(method: str, path: str, body: str, query_params: Dict) -> Dict[str, Any]:
    """
    Handle webhook requests from Twilio
    
    Args:
        method: HTTP method
        path: Request path
        body: Request body
        query_params: Query parameters
        
    Returns:
        Dict: Webhook response
    """
    try:
        # Parse Twilio webhook data
        webhook_data = {}
        if body:
            # Twilio sends form-encoded data
            import urllib.parse
            webhook_data = urllib.parse.parse_qs(body)
            # Convert single-item lists to strings
            webhook_data = {k: v[0] if len(v) == 1 else v for k, v in webhook_data.items()}
        
        if path == '/webhook/voice':
            # Handle voice webhook
            return create_response(200, {'message': 'Voice webhook received'})
        elif path == '/webhook/status':
            # Handle call status webhook
            return create_response(200, {'message': 'Status webhook received'})
        else:
            return create_error_response(404, 'Webhook endpoint not found')
    except Exception as e:
        logger.error(f"Webhook request error: {e}")
        return create_error_response(500, f'Webhook error: {str(e)}')

def create_response(status_code: int, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a standardized API response
    
    Args:
        status_code: HTTP status code
        data: Response data
        
    Returns:
        Dict: API Gateway response
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Api-Key'
        },
        'body': json.dumps(data)
    }

def create_error_response(status_code: int, message: str) -> Dict[str, Any]:
    """
    Create a standardized error response
    
    Args:
        status_code: HTTP status code
        message: Error message
        
    Returns:
        Dict: API Gateway error response
    """
    return create_response(status_code, {
        'success': False,
        'error': message,
        'timestamp': '2025-01-04T00:00:00Z'
    })

if __name__ == '__main__':
    # For local testing
    test_event = {
        'httpMethod': 'GET',
        'path': '/health',
        'queryStringParameters': {},
        'headers': {'Content-Type': 'application/json'},
        'body': ''
    }
    
    result = lambda_handler(test_event, {})
    print(json.dumps(result, indent=2))
