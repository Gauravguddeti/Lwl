#!/usr/bin/env python3
"""
Email API Handler - AWS Lambda Function
Provides REST API endpoints for email services
Ready for integration into IVR systems
"""

import json
import logging
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.email_service import EmailService

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
    AWS Lambda handler for email API endpoints
    
    Supported endpoints:
    - GET /email/status - Check service status
    - POST /email - Send email
    """
    
    try:
        # Initialize email service
        email_service = EmailService()
        
        # Extract HTTP method and path
        http_method = event.get('httpMethod', 'POST')
        path = event.get('path', '/email')
        
        logger.info(f"Processing {http_method} request to {path}")
        
        if http_method == 'OPTIONS':
            # Handle CORS preflight requests
            return {
                'statusCode': 200,
                'headers': CORS_HEADERS,
                'body': ''
            }
        
        elif http_method == 'GET':
            # Handle status check
            if 'status' in path:
                result = email_service.get_service_status()
                
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
                        'error': 'Endpoint not found. Use GET /email/status for service status.'
                    })
                }
        
        elif http_method == 'POST':
            # Handle email sending
            try:
                # Parse request body
                body = event.get('body', '{}')
                if isinstance(body, str):
                    email_data = json.loads(body)
                else:
                    email_data = body
                
                logger.info(f"Email request data: {json.dumps(email_data, default=str)}")
                
                # Send email using service
                result = email_service.send_email(email_data)
                
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
                logger.error(f"Email sending error: {e}")
                return {
                    'statusCode': 500,
                    'headers': CORS_HEADERS,
                    'body': json.dumps({
                        'success': False,
                        'error': f'Email sending failed: {str(e)}'
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
        'path': '/email/status'
    }
    
    response = lambda_handler(test_event, None)
    print("Status Test Response:")
    print(json.dumps(json.loads(response['body']), indent=2))
    print()
    
    # Test email sending
    test_email_event = {
        'httpMethod': 'POST',
        'path': '/email',
        'body': json.dumps({
            'email_type': 'customdomain',
            'to_email': 'test@example.com',
            'subject': 'Test Email from API Package',
            'body': 'This is a test email sent through the Email API Package for IVR integration.',
            'sender_email': 'support@f5universe.com'
        })
    }
    
    response = lambda_handler(test_email_event, None)
    print("Email Test Response:")
    print(json.dumps(json.loads(response['body']), indent=2))

if __name__ == "__main__":
    # Run tests when executed directly
    test_handler()