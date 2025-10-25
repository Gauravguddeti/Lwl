#!/usr/bin/env python3
"""
SMS API Handler - AWS Lambda Function
Provides REST API endpoints for SMS services
Ready for integration into IVR systems
"""

import json
import logging
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.sms_service import SMSService

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

def lambda_handler(event, context):
    """
    AWS Lambda handler for SMS API endpoints
    
    Supported endpoints:
    - GET /sms/status - Check service status
    - POST /sms/send - Send single SMS
    - POST /sms/bulk - Send bulk SMS
    - POST /sms/sandbox - Add phone to sandbox
    - GET /sms/status/{message_id} - Check message status
    """
    
    try:
        # Initialize SMS service
        sms_service = SMSService()
        
        # Extract HTTP method and path
        http_method = event.get('httpMethod', 'POST')
        path = event.get('path', '/sms')
        path_parameters = event.get('pathParameters') or {}
        
        logger.info(f"Processing {http_method} request to {path}")
        
        if http_method == 'OPTIONS':
            # Handle CORS preflight requests
            return {
                'statusCode': 200,
                'headers': CORS_HEADERS,
                'body': ''
            }
        
        elif http_method == 'GET':
            # Handle status checks
            if 'status' in path:
                # Check if message ID provided for specific status
                message_id = path_parameters.get('message_id')
                status_data = {'message_id': message_id} if message_id else {}
                
                result = sms_service.get_sms_status(status_data)
                
                return {
                    'statusCode': 200,
                    'headers': CORS_HEADERS,
                    'body': json.dumps(result)
                }
            else:
                return {
                    'statusCode': 404,
                    'headers': CORS_HEADERS,
                    'body': json.dumps({
                        'success': False,
                        'error': 'Endpoint not found. Use GET /sms/status for service status.'
                    })
                }
        
        elif http_method == 'POST':
            try:
                # Parse request body
                body = event.get('body', '{}')
                if isinstance(body, str):
                    sms_data = json.loads(body)
                else:
                    sms_data = body
                
                logger.info(f"SMS request data: {json.dumps(sms_data, default=str)}")
                
                # Route to appropriate SMS function based on path
                if 'bulk' in path:
                    # Handle bulk SMS
                    result = sms_service.send_bulk_sms(sms_data)
                    
                elif 'sandbox' in path:
                    # Handle sandbox number addition
                    result = sms_service.add_sandbox_number(sms_data)
                    
                else:
                    # Handle single SMS (default)
                    result = sms_service.send_sms(sms_data)
                
                # Return response
                status_code = 200 if result['success'] else 400
                
                return {
                    'statusCode': status_code,
                    'headers': CORS_HEADERS,
                    'body': json.dumps(result)
                }
                
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in request body: {e}")
                return {
                    'statusCode': 400,
                    'headers': CORS_HEADERS,
                    'body': json.dumps({
                        'success': False,
                        'error': 'Invalid JSON in request body'
                    })
                }
            
            except Exception as e:
                logger.error(f"SMS processing error: {e}")
                return {
                    'statusCode': 500,
                    'headers': CORS_HEADERS,
                    'body': json.dumps({
                        'success': False,
                        'error': f'SMS processing failed: {str(e)}'
                    })
                }
        
        else:
            # Unsupported method
            return {
                'statusCode': 405,
                'headers': CORS_HEADERS,
                'body': json.dumps({
                    'success': False,
                    'error': f'Method {http_method} not allowed. Supported methods: GET, POST, OPTIONS'
                })
            }
    
    except Exception as e:
        logger.error(f"Lambda handler error: {e}")
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'success': False,
                'error': f'Internal server error: {str(e)}'
            })
        }

def test_handler():
    """Test function for local development"""
    
    # Test status endpoint
    test_event = {
        'httpMethod': 'GET',
        'path': '/sms/status'
    }
    
    response = lambda_handler(test_event, None)
    print("SMS Status Test Response:")
    print(json.dumps(json.loads(response['body']), indent=2))
    print()
    
    # Test single SMS
    test_sms_event = {
        'httpMethod': 'POST',
        'path': '/sms/send',
        'body': json.dumps({
            'phone_number': '+1234567890',
            'message': 'Test SMS from Email & SMS API Package for IVR integration',
            'sender_id': 'IVR'
        })
    }
    
    response = lambda_handler(test_sms_event, None)
    print("Single SMS Test Response:")
    print(json.dumps(json.loads(response['body']), indent=2))
    print()
    
    # Test bulk SMS
    test_bulk_event = {
        'httpMethod': 'POST',
        'path': '/sms/bulk',
        'body': json.dumps({
            'phone_numbers': ['+1234567890', '+1987654321'],
            'message': 'Bulk SMS test from API Package',
            'sender_id': 'IVR'
        })
    }
    
    response = lambda_handler(test_bulk_event, None)
    print("Bulk SMS Test Response:")
    print(json.dumps(json.loads(response['body']), indent=2))

if __name__ == "__main__":
    # Run tests when executed directly
    test_handler()