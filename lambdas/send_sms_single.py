#!/usr/bin/env python3
"""
SMS API Handler - AWS Lambda Function
Provides REST API endpoints for SMS services
Ready for integration into IVR systems
Enhanced with better error handling, validation, and logging
"""

import json
import logging
import sys
import os
from typing import Dict, Any, Optional

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.sms_service import SMSService

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# CORS headers for web integration
CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
    'Content-Type': 'application/json'
}

def create_response(status_code: int, body: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Create standardized Lambda response
    
    Args:
        status_code: HTTP status code
        body: Response body as dictionary
        headers: Optional additional headers
        
    Returns:
        Formatted Lambda response
    """
    response_headers = CORS_HEADERS.copy()
    if headers:
        response_headers.update(headers)
    
    return {
        'statusCode': status_code,
        'headers': response_headers,
        'body': json.dumps(body, default=str)
    }

def validate_sms_request(sms_data: Dict[str, Any]) -> Optional[str]:
    """
    Validate SMS request data
    
    Args:
        sms_data: SMS request data
        
    Returns:
        Error message if validation fails, None if valid
    """
    if not isinstance(sms_data, dict):
        return "Request body must be a valid JSON object"
    
    # Check required fields
    required_fields = ['phone_number', 'message']
    for field in required_fields:
        if field not in sms_data:
            return f"Missing required field: {field}"
        
        if not sms_data[field] or not str(sms_data[field]).strip():
            return f"Field '{field}' cannot be empty"
    
    # Validate phone number format (basic check)
    phone = str(sms_data['phone_number']).strip()
    if len(phone) < 10 or len(phone) > 15:
        return "Phone number must be between 10-15 digits"
    
    # Validate message length
    message = str(sms_data['message']).strip()
    if len(message) == 0:
        return "Message cannot be empty"
    if len(message) > 1600:
        return "Message too long. Maximum 1600 characters allowed"
    
    # Validate sender_id if provided
    if 'sender_id' in sms_data:
        sender_id = str(sms_data['sender_id']).strip()
        if len(sender_id) > 11:
            return "Sender ID cannot exceed 11 characters"
    
    return None

def validate_bulk_sms_request(sms_data: Dict[str, Any]) -> Optional[str]:
    """
    Validate bulk SMS request data
    
    Args:
        sms_data: Bulk SMS request data
        
    Returns:
        Error message if validation fails, None if valid
    """
    if not isinstance(sms_data, dict):
        return "Request body must be a valid JSON object"
    
    # Check required fields
    if 'phone_numbers' not in sms_data:
        return "Missing required field: phone_numbers"
    
    if 'message' not in sms_data:
        return "Missing required field: message"
    
    # Validate phone_numbers array
    phone_numbers = sms_data['phone_numbers']
    if not isinstance(phone_numbers, list):
        return "phone_numbers must be an array"
    
    if len(phone_numbers) == 0:
        return "phone_numbers array cannot be empty"
    
    if len(phone_numbers) > 100:  # Conservative limit for rate limiting
        return "Maximum 100 phone numbers allowed per bulk request to respect rate limits"
    
    # Validate each phone number
    for i, phone in enumerate(phone_numbers):
        if not phone or not str(phone).strip():
            return f"Phone number at index {i} cannot be empty"
        
        phone_str = str(phone).strip()
        if len(phone_str) < 10 or len(phone_str) > 15:
            return f"Invalid phone number at index {i}: {phone_str}"
    
    # Validate message
    message = str(sms_data['message']).strip()
    if len(message) == 0:
        return "Message cannot be empty"
    if len(message) > 1600:
        return "Message too long. Maximum 1600 characters allowed"
    
    # Validate sender_id if provided
    if 'sender_id' in sms_data:
        sender_id = str(sms_data['sender_id']).strip()
        if len(sender_id) > 11:
            return "Sender ID cannot exceed 11 characters"
    
    return None

def lambda_handler(event, context):
    """
    AWS Lambda handler for SMS API endpoints
    
    Supported endpoints:
    - GET /sms/status - Check service status
    - POST /sms/send - Send single SMS
    - POST /sms/bulk - Send bulk SMS
    - POST /sms/sandbox - Add phone to sandbox
    - GET /sms/status/{message_id} - Check message status
    
    Rate Limiting Notes:
    - AWS SNS has default limits: 100 SMS/second per account
    - For production, consider implementing rate limiting middleware
    - Bulk SMS is processed sequentially to respect AWS limits
    - Monitor CloudWatch metrics for throttling events
    """
    
    try:
        # Initialize SMS service
        sms_service = SMSService()
        
        # Extract HTTP method and path
        http_method = event.get('httpMethod', 'POST')
        path = event.get('path', '/sms')
        path_parameters = event.get('pathParameters') or {}
        
        logger.info(f"Processing {http_method} request to {path}")
        logger.info(f"Path parameters: {path_parameters}")
        
        # Handle CORS preflight requests
        if http_method == 'OPTIONS':
            return create_response(200, {'message': 'CORS preflight successful'})
        
        # Route based on HTTP method and path
        if http_method == 'GET':
            return handle_get_request(sms_service, path, path_parameters)
        elif http_method == 'POST':
            return handle_post_request(sms_service, path, event)
        else:
            return create_response(405, {
                'success': False,
                'error': f'Method {http_method} not allowed',
                'supported_methods': ['GET', 'POST', 'OPTIONS']
            })
    
    except Exception as e:
        logger.error(f"Lambda handler error: {e}", exc_info=True)
        return create_response(500, {
            'success': False,
            'error': 'Internal server error',
            'message': 'An unexpected error occurred. Please try again later.'
        })

def handle_get_request(sms_service: SMSService, path: str, path_parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle GET requests
    
    Args:
        sms_service: SMS service instance
        path: Request path
        path_parameters: Path parameters
        
    Returns:
        Lambda response
    """
    try:
        if 'status' in path:
            # Check if message ID provided for specific status
            message_id = path_parameters.get('message_id')
            status_data = {'message_id': message_id} if message_id else {}
            
            result = sms_service.get_sms_status(status_data)
            
            if result.get('success'):
                return create_response(200, result)
            else:
                return create_response(400, result)
        else:
            return create_response(404, {
                'success': False,
                'error': 'Endpoint not found',
                'available_endpoints': [
                    'GET /sms/status - Check service status',
                    'GET /sms/status/{message_id} - Check specific message status'
                ]
            })
    
    except Exception as e:
        logger.error(f"GET request error: {e}", exc_info=True)
        return create_response(500, {
            'success': False,
            'error': 'Failed to process GET request',
            'message': str(e)
        })

def handle_post_request(sms_service: SMSService, path: str, event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle POST requests
    
    Args:
        sms_service: SMS service instance
        path: Request path
        event: Lambda event
        
    Returns:
        Lambda response
    """
    try:
        # Parse request body
        body = event.get('body', '{}')
        if isinstance(body, str):
            try:
                sms_data = json.loads(body)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in request body: {e}")
                return create_response(400, {
                    'success': False,
                    'error': 'Invalid JSON in request body',
                    'message': 'Please ensure your request body contains valid JSON'
                })
        else:
            sms_data = body
        
        logger.info(f"SMS request data: {json.dumps(sms_data, default=str)}")
        
        # Route to appropriate SMS function based on path
        if 'bulk' in path:
            # Validate bulk SMS request
            validation_error = validate_bulk_sms_request(sms_data)
            if validation_error:
                return create_response(400, {
                    'success': False,
                    'error': 'Validation failed',
                    'message': validation_error
                })
            
            # Handle bulk SMS
            result = sms_service.send_bulk_sms(sms_data)
            
        elif 'sandbox' in path:
            # Validate sandbox request
            if 'phone_number' not in sms_data:
                return create_response(400, {
                    'success': False,
                    'error': 'Missing required field: phone_number'
                })
            
            # Handle sandbox number addition
            result = sms_service.add_sandbox_number(sms_data)
            
        else:
            # Validate single SMS request
            validation_error = validate_sms_request(sms_data)
            if validation_error:
                return create_response(400, {
                    'success': False,
                    'error': 'Validation failed',
                    'message': validation_error
                })
            
            # Handle single SMS (default)
            result = sms_service.send_sms(sms_data)
        
        # Return response with appropriate status code
        status_code = 200 if result.get('success', False) else 400
        
        # Add request metadata to response
        if result.get('success'):
            result['request_info'] = {
                'endpoint': path,
                'timestamp': 'unknown'
            }
        
        return create_response(status_code, result)
        
    except Exception as e:
        logger.error(f"POST request error: {e}", exc_info=True)
        return create_response(500, {
            'success': False,
            'error': 'Failed to process POST request',
            'message': str(e)
        })

def test_handler():
    """Test function for local development"""
    
    print("=" * 60)
    print("SMS API Handler - Test Suite")
    print("=" * 60)
    
    # Test status endpoint
    print("\n1. Testing SMS Status Endpoint...")
    test_event = {
        'httpMethod': 'GET',
        'path': '/sms/status'
    }
    
    response = lambda_handler(test_event, None)
    print(f"Status Code: {response['statusCode']}")
    print("Response:")
    print(json.dumps(json.loads(response['body']), indent=2))
    
    # Test single SMS
    print("\n2. Testing Single SMS...")
    test_sms_event = {
        'httpMethod': 'POST',
        'path': '/sms/send',
        'body': json.dumps({
            'phone_number': '+1234567890',
            'message': 'Test SMS from Enhanced API Package for IVR integration',
            'sender_id': 'IVR'
        })
    }
    
    response = lambda_handler(test_sms_event, None)
    print(f"Status Code: {response['statusCode']}")
    print("Response:")
    print(json.dumps(json.loads(response['body']), indent=2))
    
    # Test bulk SMS
    print("\n3. Testing Bulk SMS...")
    test_bulk_event = {
        'httpMethod': 'POST',
        'path': '/sms/bulk',
        'body': json.dumps({
            'phone_numbers': ['+1234567890', '+1987654321'],
            'message': 'Bulk SMS test from Enhanced API Package',
            'sender_id': 'IVR'
        })
    }
    
    response = lambda_handler(test_bulk_event, None)
    print(f"Status Code: {response['statusCode']}")
    print("Response:")
    print(json.dumps(json.loads(response['body']), indent=2))
    
    # Test validation errors
    print("\n4. Testing Validation Errors...")
    test_invalid_event = {
        'httpMethod': 'POST',
        'path': '/sms/send',
        'body': json.dumps({
            'phone_number': '',  # Invalid empty phone
            'message': 'Test message'
        })
    }
    
    response = lambda_handler(test_invalid_event, None)
    print(f"Status Code: {response['statusCode']}")
    print("Response:")
    print(json.dumps(json.loads(response['body']), indent=2))
    
    print("\n" + "=" * 60)
    print("Test Suite Completed")
    print("=" * 60)

if __name__ == "__main__":
    # Run tests when executed directly
    test_handler()