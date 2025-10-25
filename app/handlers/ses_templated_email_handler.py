"""
SES Templated Email Handler for AI Telecaller System
Provides API endpoints for 5 templated email types
"""

import json
import logging
from typing import Dict, Any
import os
import sys

# Add the app directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.ses_templated_email_service import SESTemplatedEmailService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize templated email service
templated_email_service = SESTemplatedEmailService()

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for SES templated email API endpoints
    
    Args:
        event: AWS Lambda event object
        context: AWS Lambda context object
        
    Returns:
        API Gateway response
    """
    try:
        # Parse the request
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '/')
        
        logger.info(f"Processing {http_method} request to {path}")
        
        # CORS headers
        headers = {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        }
        
        # Handle OPTIONS requests (CORS preflight)
        if http_method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'message': 'CORS preflight OK'})
            }
        
        # Route to appropriate handler
        if path == '/create-templates' and http_method == 'POST':
            return handle_create_templates(event, headers)
        elif path == '/send-signup-email' and http_method == 'POST':
            return handle_send_signup_email(event, headers)
        elif path == '/send-forgot-password-email' and http_method == 'POST':
            return handle_send_forgot_password_email(event, headers)
        elif path == '/send-otp-email' and http_method == 'POST':
            return handle_send_otp_email(event, headers)
        elif path == '/send-order-confirmation-email' and http_method == 'POST':
            return handle_send_order_confirmation_email(event, headers)
        elif path == '/send-welcome-pack-email' and http_method == 'POST':
            return handle_send_welcome_pack_email(event, headers)
        elif path == '/templated-email-status' and http_method == 'GET':
            return handle_templated_email_status(event, headers)
        else:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({
                    'error': 'Not Found',
                    'message': f'Path {path} with method {http_method} not found',
                    'available_endpoints': {
                        'POST /create-templates': 'Create all SES email templates',
                        'POST /send-signup-email': 'Send account signup email',
                        'POST /send-forgot-password-email': 'Send password reset email',
                        'POST /send-otp-email': 'Send OTP verification email',
                        'POST /send-order-confirmation-email': 'Send order confirmation email',
                        'POST /send-welcome-pack-email': 'Send welcome pack email with PDF',
                        'GET /templated-email-status': 'Get templated email service status'
                    }
                })
            }
            
    except Exception as e:
        logger.error(f"Lambda handler error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Internal Server Error',
                'message': str(e)
            })
        }

def handle_create_templates(event: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
    """
    Handle POST /create-templates requests
    Creates all SES email templates
    
    Args:
        event: Lambda event
        headers: Response headers
        
    Returns:
        API Gateway response
    """
    try:
        logger.info("Creating SES email templates...")
        
        # Create templates
        result = templated_email_service.create_ses_templates()
        
        success_count = sum(1 for r in result.values() if r.get('success'))
        total_count = len(result)
        
        if success_count == total_count:
            status_code = 200
            message = f"All {total_count} SES email templates created successfully"
        elif success_count > 0:
            status_code = 207  # Multi-status
            message = f"{success_count} of {total_count} templates created successfully"
        else:
            status_code = 500
            message = "Failed to create any templates"
        
        return {
            'statusCode': status_code,
            'headers': headers,
            'body': json.dumps({
                'success': success_count == total_count,
                'message': message,
                'templates_created': success_count,
                'total_templates': total_count,
                'results': result
            })
        }
        
    except Exception as e:
        logger.error(f"Error creating templates: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }

def handle_send_signup_email(event: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
    """
    Handle POST /send-signup-email requests
    
    Expected JSON body:
    {
        "to_email": "user@example.com",
        "name": "John Doe",
        "signupLink": "https://app.chatmaven.ai/account/register",
        "brandLogo": "https://app.chatmaven.ai/assets/logo.png",
        "bgColor": "#f8f9fa"
    }
    """
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Validate required fields
        if not body.get('to_email'):
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'error': 'to_email is required'
                })
            }
        
        # Send email
        result = templated_email_service.send_account_signup_email(body)
        
        status_code = 200 if result.get('success') else 500
        
        return {
            'statusCode': status_code,
            'headers': headers,
            'body': json.dumps(result)
        }
        
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({
                'success': False,
                'error': 'Invalid JSON in request body'
            })
        }
    except Exception as e:
        logger.error(f"Error sending signup email: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }

def handle_send_forgot_password_email(event: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
    """
    Handle POST /send-forgot-password-email requests
    
    Expected JSON body:
    {
        "to_email": "user@example.com",
        "name": "John Doe",
        "resetLink": "https://app.chatmaven.ai/account/forgotpassword",
        "brandLogo": "https://app.chatmaven.ai/assets/logo.png",
        "bgColor": "#f8f9fa"
    }
    """
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Validate required fields
        if not body.get('to_email'):
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'error': 'to_email is required'
                })
            }
        
        # Send email
        result = templated_email_service.send_forgot_password_email(body)
        
        status_code = 200 if result.get('success') else 500
        
        return {
            'statusCode': status_code,
            'headers': headers,
            'body': json.dumps(result)
        }
        
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({
                'success': False,
                'error': 'Invalid JSON in request body'
            })
        }
    except Exception as e:
        logger.error(f"Error sending forgot password email: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }

def handle_send_otp_email(event: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
    """
    Handle POST /send-otp-email requests
    
    Expected JSON body:
    {
        "to_email": "user@example.com",
        "name": "John Doe",
        "otp": "123456",
        "brandLogo": "https://app.chatmaven.ai/assets/logo.png",
        "bgColor": "#f8f9fa"
    }
    """
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Validate required fields
        if not body.get('to_email') or not body.get('otp'):
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'error': 'to_email and otp are required'
                })
            }
        
        # Send email
        result = templated_email_service.send_otp_email(body)
        
        status_code = 200 if result.get('success') else 500
        
        return {
            'statusCode': status_code,
            'headers': headers,
            'body': json.dumps(result)
        }
        
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({
                'success': False,
                'error': 'Invalid JSON in request body'
            })
        }
    except Exception as e:
        logger.error(f"Error sending OTP email: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }

def handle_send_order_confirmation_email(event: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
    """
    Handle POST /send-order-confirmation-email requests
    
    Expected JSON body:
    {
        "to_email": "user@example.com",
        "name": "John Doe",
        "orderId": "ORD-123456",
        "orderDate": "2025-01-15",
        "brandLogo": "https://app.chatmaven.ai/assets/logo.png",
        "bgColor": "#f8f9fa"
    }
    """
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Validate required fields
        if not body.get('to_email') or not body.get('orderId'):
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'error': 'to_email and orderId are required'
                })
            }
        
        # Send email
        result = templated_email_service.send_order_confirmation_email(body)
        
        status_code = 200 if result.get('success') else 500
        
        return {
            'statusCode': status_code,
            'headers': headers,
            'body': json.dumps(result)
        }
        
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({
                'success': False,
                'error': 'Invalid JSON in request body'
            })
        }
    except Exception as e:
        logger.error(f"Error sending order confirmation email: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }

def handle_send_welcome_pack_email(event: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
    """
    Handle POST /send-welcome-pack-email requests
    
    Expected JSON body:
    {
        "to_email": "user@example.com",
        "name": "John Doe",
        "signupLink": "https://app.chatmaven.ai/account/register",
        "loginLink": "https://app.chatmaven.ai/account?ReturnUrl=%2F",
        "brandLogo": "https://app.chatmaven.ai/assets/logo.png",
        "bgColor": "#f8f9fa"
    }
    """
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Validate required fields
        if not body.get('to_email'):
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'error': 'to_email is required'
                })
            }
        
        # Send email
        result = templated_email_service.send_welcome_pack_email(body)
        
        status_code = 200 if result.get('success') else 500
        
        return {
            'statusCode': status_code,
            'headers': headers,
            'body': json.dumps(result)
        }
        
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({
                'success': False,
                'error': 'Invalid JSON in request body'
            })
        }
    except Exception as e:
        logger.error(f"Error sending welcome pack email: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }

def handle_templated_email_status(event: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
    """
    Handle GET /templated-email-status requests
    """
    try:
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'success': True,
                'service': 'SES Templated Email Service',
                'status': 'healthy',
                'available_templates': [
                    'AccountSignupTemplate',
                    'ForgotPasswordTemplate',
                    'OTPTemplate',
                    'OrderConfirmationTemplate'
                ],
                'special_endpoints': [
                    'WelcomePackWithPDF (uses SendRawEmail)'
                ],
                'version': '1.0.0'
            })
        }
        
    except Exception as e:
        logger.error(f"Error getting templated email status: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }
