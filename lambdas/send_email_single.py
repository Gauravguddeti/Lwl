#!/usr/bin/env python3
"""
Send Single Email Lambda Function
================================

AWS Lambda function to send a single email using AWS SES.
Designed for educational institutions to send individual email notifications.

Input Format:
{
    "email": "user@example.com",
    "subject": "Reminder",
    "body": "Fee due"
}

Output Format:
{
    "status": "success|error",
    "message": "Email sent successfully",
    "message_id": "0000014a-f4d4-4f96-9feb-0cdfa9c3e3ed-000000",
    "recipient": "user@example.com",
    "provider": "AWS SES"
}

Author: AI Telecaller Team
Version: 1.0.0
"""

import json
import boto3
import logging
import re
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS SES client
ses_client = boto3.client('ses', region_name='us-west-2')

# Default sender email (should be verified in SES)
DEFAULT_SENDER = 'noreply@f5universe.com'

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for sending single email
    
    Args:
        event: Lambda event containing email, subject, and body
        context: Lambda context object
        
    Returns:
        Dict: Response with delivery result
    """
    try:
        # Parse input
        email = event.get('email')
        subject = event.get('subject')
        body = event.get('body')
        sender_email = event.get('sender_email', DEFAULT_SENDER)
        is_html = event.get('is_html', False)
        
        # Validate input
        if not email or not subject or not body:
            return create_error_response(
                400,
                "Missing required fields: email, subject, and body are required"
            )
        
        # Validate email format
        if not is_valid_email(email):
            return create_error_response(
                400,
                "Invalid email format"
            )
        
        # Validate sender email
        if not is_valid_email(sender_email):
            return create_error_response(
                400,
                "Invalid sender email format"
            )
        
        # Send email via SES
        response = ses_client.send_email(
            Source=sender_email,
            Destination={
                'ToAddresses': [email]
            },
            Message={
                'Subject': {
                    'Data': subject,
                    'Charset': 'UTF-8'
                },
                'Body': {
                    'Text' if not is_html else 'Html': {
                        'Data': body,
                        'Charset': 'UTF-8'
                    }
                }
            }
        )
        
        logger.info(f"Email sent successfully to {email}: {response['MessageId']}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'status': 'success',
                'message': f'Email sent successfully to {email}',
                'message_id': response['MessageId'],
                'recipient': email,
                'subject': subject,
                'provider': 'AWS SES',
                'sender': sender_email,
                'is_html': is_html
            })
        }
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        
        logger.error(f"AWS SES error: {error_code} - {error_message}")
        
        # Handle specific SES errors
        if error_code == 'MessageRejected':
            return create_error_response(
                400,
                f'Email rejected: {error_message}'
            )
        elif error_code == 'MailFromDomainNotVerifiedException':
            return create_error_response(
                400,
                'Sender email domain not verified in SES'
            )
        else:
            return create_error_response(
                500,
                f'Email sending failed: {error_message}'
            )
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return create_error_response(
            500,
            f'Internal server error: {str(e)}'
        )

def is_valid_email(email: str) -> bool:
    """
    Validate email address format
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not email:
        return False
    
    # Basic email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def create_error_response(status_code: int, message: str) -> Dict[str, Any]:
    """
    Create standardized error response
    
    Args:
        status_code: HTTP status code
        message: Error message
        
    Returns:
        Dict: Error response
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'status': 'error',
            'message': message,
            'timestamp': '2025-01-04T00:00:00Z'
        })
    }

# For local testing
if __name__ == '__main__':
    test_event = {
        'email': 'student@example.com',
        'subject': 'Fee Payment Reminder',
        'body': 'Dear Student,\n\nThis is a reminder that your fee payment is due on 2025-01-15.\n\nPlease make the payment at your earliest convenience.\n\nBest regards,\nAdministration',
        'is_html': False
    }
    
    result = lambda_handler(test_event, {})
    print(json.dumps(result, indent=2))
