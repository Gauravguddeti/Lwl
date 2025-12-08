#!/usr/bin/env python3
"""
OTP API Handler - AWS Lambda Function
Provides REST API endpoints for OTP services
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

from services.otp_service import OTPService

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

def validate_otp_request(otp_data: Dict[str, Any]) -> Optional[str]:
    """
    Validate OTP request data
    
    Args:
        otp_data: OTP request data
        
    Returns:
        Error message if validation fails, None if valid
    """
    if not isinstance(otp_data, dict):
        return "Request body must be a valid JSON object"
    
    # Check required fields
    if 'mobile' not in otp_data:
        return "Missing required field: mobile"
    
    if not otp_data['mobile'] or not str(otp_data['mobile']).strip():
        return "Field 'mobile' cannot be empty"
    
    # Validate phone number format (basic check)
    mobile = str(otp_data['mobile']).strip()
    if len(mobile) < 10 or len(mobile) > 15:
        return "Mobile number must be between 10-15 digits"
    
    # Validate purpose if provided
    if 'purpose' in otp_data:
        purpose = str(otp_data['purpose']).strip().lower()
        valid_purposes = ['login', 'registration', 'password_reset', 'verification']
        if purpose not in valid_purposes:
            return f"Invalid purpose. Must be one of: {', '.join(valid_purposes)}"
    
    # Validate sender_id if provided
    if 'sender_id' in otp_data:
        sender_id = str(otp_data['sender_id']).strip()
        if len(sender_id) > 11:
            return "Sender ID cannot exceed 11 characters"
    
    return None

def validate_otp_verification_request(verification_data: Dict[str, Any]) -> Optional[str]:
    """
    Validate OTP verification request data
    
    Args:
        verification_data: OTP verification request data
        
    Returns:
        Error message if validation fails, None if valid
    """
    if not isinstance(verification_data, dict):
        return "Request body must be a valid JSON object"
    
    # Check required fields
    required_fields = ['otp_id', 'otp_code']
    for field in required_fields:
        if field not in verification_data:
            return f"Missing required field: {field}"
        
        if not verification_data[field] or not str(verification_data[field]).strip():
            return f"Field '{field}' cannot be empty"
    
    # Validate OTP code format
    otp_code = str(verification_data['otp_code']).strip()
    if not otp_code.isdigit() or len(otp_code) != 6:
        return "OTP code must be exactly 6 digits"
    
    return None

def lambda_handler(event, context):
    """
    AWS Lambda handler for OTP API endpoints
    
    Supported endpoints:
    - GET /otp/status - Check service status
    - POST /otp/send - Send OTP
    - POST /otp/verify - Verify OTP
    - GET /otp/status/{otp_id} - Check specific OTP status
    
    Rate Limiting Notes:
    - Default rate limit: 5 OTP requests per hour per mobile number
    - OTP expiry: 10 minutes
    - OTP length: 6 digits
    """
    
    try:
        # Initialize OTP service
        otp_service = OTPService()
        
        # Extract HTTP method and path
        http_method = event.get('httpMethod', 'POST')
        path = event.get('path', '/otp')
        path_parameters = event.get('pathParameters') or {}
        
        logger.info(f"Processing {http_method} request to {path}")
        logger.info(f"Path parameters: {path_parameters}")
        
        # Handle CORS preflight requests
        if http_method == 'OPTIONS':
            return create_response(200, {'message': 'CORS preflight successful'})
        
        # Route based on HTTP method and path
        if http_method == 'GET':
            return handle_get_request(otp_service, path, path_parameters)
        elif http_method == 'POST':
            return handle_post_request(otp_service, path, event)
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

def handle_get_request(otp_service: OTPService, path: str, path_parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle GET requests
    
    Args:
        otp_service: OTP service instance
        path: Request path
        path_parameters: Path parameters
        
    Returns:
        Lambda response
    """
    try:
        if 'status' in path:
            # Check if OTP ID provided for specific status
            otp_id = path_parameters.get('otp_id')
            status_data = {'otp_id': otp_id} if otp_id else {}
            
            result = otp_service.get_otp_status(status_data)
            
            if result.get('success'):
                return create_response(200, result)
            else:
                return create_response(400, result)
        else:
            return create_response(404, {
                'success': False,
                'error': 'Endpoint not found',
                'available_endpoints': [
                    'GET /otp/status - Check service status',
                    'GET /otp/status/{otp_id} - Check specific OTP status'
                ]
            })
    
    except Exception as e:
        logger.error(f"GET request error: {e}", exc_info=True)
        return create_response(500, {
            'success': False,
            'error': 'Failed to process GET request',
            'message': str(e)
        })

def handle_post_request(otp_service: OTPService, path: str, event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle POST requests
    
    Args:
        otp_service: OTP service instance
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
                otp_data = json.loads(body)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in request body: {e}")
                return create_response(400, {
                    'success': False,
                    'error': 'Invalid JSON in request body',
                    'message': 'Please ensure your request body contains valid JSON'
                })
        else:
            otp_data = body
        
        logger.info(f"OTP request data: {json.dumps(otp_data, default=str)}")
        
        # Route to appropriate OTP function based on path
        if 'verify' in path:
            # Validate OTP verification request
            validation_error = validate_otp_verification_request(otp_data)
            if validation_error:
                return create_response(400, {
                    'success': False,
                    'error': 'Validation failed',
                    'message': validation_error
                })
            
            # Handle OTP verification
            result = otp_service.verify_otp(otp_data)
            
        else:
            # Validate OTP send request
            validation_error = validate_otp_request(otp_data)
            if validation_error:
                return create_response(400, {
                    'success': False,
                    'error': 'Validation failed',
                    'message': validation_error
                })
            
            # Handle OTP sending (default)
            result = otp_service.send_otp(otp_data)
        
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
    print("OTP API Handler - Test Suite")
    print("=" * 60)
    
    # Test status endpoint
    print("\n1. Testing OTP Status Endpoint...")
    test_event = {
        'httpMethod': 'GET',
        'path': '/otp/status'
    }
    
    response = lambda_handler(test_event, None)
    print(f"Status Code: {response['statusCode']}")
    print("Response:")
    print(json.dumps(json.loads(response['body']), indent=2))
    
    # Test send OTP
    print("\n2. Testing Send OTP...")
    test_otp_event = {
        'httpMethod': 'POST',
        'path': '/otp/send',
        'body': json.dumps({
            'mobile': '+1234567890',
            'purpose': 'login',
            'sender_id': 'EDUOTP'
        })
    }
    
    response = lambda_handler(test_otp_event, None)
    print(f"Status Code: {response['statusCode']}")
    print("Response:")
    print(json.dumps(json.loads(response['body']), indent=2))
    
    # Test verify OTP
    print("\n3. Testing Verify OTP...")
    test_verify_event = {
        'httpMethod': 'POST',
        'path': '/otp/verify',
        'body': json.dumps({
            'otp_id': 'otp_1234567890',
            'otp_code': '123456',
            'mobile': '+1234567890'
        })
    }
    
    response = lambda_handler(test_verify_event, None)
    print(f"Status Code: {response['statusCode']}")
    print("Response:")
    print(json.dumps(json.loads(response['body']), indent=2))
    
    # Test validation errors
    print("\n4. Testing Validation Errors...")
    test_invalid_event = {
        'httpMethod': 'POST',
        'path': '/otp/send',
        'body': json.dumps({
            'mobile': '',  # Invalid empty mobile
            'purpose': 'login'
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
