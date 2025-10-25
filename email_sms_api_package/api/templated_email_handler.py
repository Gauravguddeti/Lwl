#!/usr/bin/env python3
"""
Templated Email API Handler - AWS Lambda Function
Provides REST API endpoints for templated email services
Ready for integration into IVR systems
"""

import json
import logging
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.templated_email_service import TemplatedEmailService

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
    AWS Lambda handler for templated email API endpoints
    
    Supported endpoints:
    - GET /templated-email/status - Check service status
    - POST /templated-email/create-templates - Create all templates
    - POST /templated-email/send - Send templated email (universal endpoint)
    - POST /templated-email/signup - Send account signup email
    - POST /templated-email/forgot-password - Send forgot password email
    - POST /templated-email/otp - Send OTP email
    - POST /templated-email/welcome-pack - Send welcome pack email
    - POST /templated-email/order-confirmation - Send order confirmation email
    """
    
    try:
        # Initialize templated email service
        template_service = TemplatedEmailService()
        
        # Extract HTTP method and path
        http_method = event.get('httpMethod', 'POST')
        path = event.get('path', '/templated-email')
        
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
                result = template_service.get_service_status()
                
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
                        'error': 'Endpoint not found. Use GET /templated-email/status for service status.'
                    })
                }
        
        elif http_method == 'POST':
            try:
                # Parse request body
                body = event.get('body', '{}')
                if isinstance(body, str):
                    template_data = json.loads(body)
                else:
                    template_data = body
                
                logger.info(f"Template request data: {json.dumps(template_data, default=str)}")
                
                # Route to appropriate template function based on path
                if 'create-templates' in path:
                    # Create all SES templates
                    result = template_service.create_templates()
                    
                elif 'signup' in path:
                    # Send account signup email
                    result = template_service.send_account_signup_email(template_data)
                    
                elif 'forgot-password' in path:
                    # Send forgot password email
                    result = template_service.send_forgot_password_email(template_data)
                    
                elif 'otp' in path:
                    # Send OTP email
                    result = template_service.send_otp_email(template_data)
                    
                elif 'welcome-pack' in path:
                    # Send welcome pack email
                    result = template_service.send_welcome_pack_email(template_data)
                    
                elif 'order-confirmation' in path:
                    # Send order confirmation email
                    result = template_service.send_order_confirmation_email(template_data)
                    
                elif 'send' in path:
                    # Universal templated email endpoint
                    template_type = template_data.get('template_type')
                    
                    if template_type == 'account_signup':
                        result = template_service.send_account_signup_email(template_data)
                    elif template_type == 'forgot_password':
                        result = template_service.send_forgot_password_email(template_data)
                    elif template_type == 'otp_verification':
                        result = template_service.send_otp_email(template_data)
                    elif template_type == 'welcome_pack':
                        result = template_service.send_welcome_pack_email(template_data)
                    elif template_type == 'order_confirmation':
                        result = template_service.send_order_confirmation_email(template_data)
                    else:
                        result = {
                            'success': False,
                            'error': f'Invalid template_type: {template_type}. Supported: account_signup, forgot_password, otp_verification, welcome_pack, order_confirmation'
                        }
                
                else:
                    result = {
                        'success': False,
                        'error': 'Invalid endpoint. Use specific template endpoints or /send with template_type.'
                    }
                
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
                logger.error(f"Template email processing error: {e}")
                return {
                    'statusCode': 500,
                    'headers': CORS_HEADERS,
                    'body': json.dumps({
                        'success': False,
                        'error': f'Template email processing failed: {str(e)}'
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
        'path': '/templated-email/status'
    }
    
    response = lambda_handler(test_event, None)
    print("Template Status Test Response:")
    print(json.dumps(json.loads(response['body']), indent=2))
    print()
    
    # Test template creation
    test_create_event = {
        'httpMethod': 'POST',
        'path': '/templated-email/create-templates',
        'body': '{}'
    }
    
    response = lambda_handler(test_create_event, None)
    print("Template Creation Test Response:")
    print(json.dumps(json.loads(response['body']), indent=2))
    print()
    
    # Test OTP email
    test_otp_event = {
        'httpMethod': 'POST',
        'path': '/templated-email/send',
        'body': json.dumps({
            'template_type': 'otp_verification',
            'to_email': 'test@example.com',
            'template_data': {
                'user_name': 'Test User',
                'otp_code': '123456',
                'expiry_minutes': '10',
                'support_email': 'support@f5universe.com'
            }
        })
    }
    
    response = lambda_handler(test_otp_event, None)
    print("OTP Email Test Response:")
    print(json.dumps(json.loads(response['body']), indent=2))

if __name__ == "__main__":
    # Run tests when executed directly
    test_handler()