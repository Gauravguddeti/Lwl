#!/usr/bin/env python3
"""
Send Bulk Email Lambda Function
==============================

AWS Lambda function to send bulk emails using AWS SES.
Designed for educational institutions to send notifications to multiple students.

Input Format:
{
    "emails": ["user1@example.com", "user2@example.com"],
    "subject": "Important Announcement",
    "body": "Dear students..."
}

Output Format:
{
    "status": "success|error",
    "message": "Bulk email completed: 2 successful, 0 failed",
    "total_emails": 2,
    "successful": 2,
    "failed": 0,
    "results": [...]
}

Author: AI Telecaller Team
Version: 1.0.0
"""

import json
import boto3
import logging
import re
import concurrent.futures
from typing import Dict, Any, List, Optional
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
    AWS Lambda handler for sending bulk emails
    
    Args:
        event: Lambda event containing emails, subject, and body
        context: Lambda context object
        
    Returns:
        Dict: Response with bulk operation results
    """
    try:
        # Parse input
        emails = event.get('emails', [])
        subject = event.get('subject')
        body = event.get('body')
        sender_email = event.get('sender_email', DEFAULT_SENDER)
        is_html = event.get('is_html', False)
        
        # Validate input
        if not emails or not isinstance(emails, list):
            return create_error_response(
                400,
                "Missing or invalid field: emails must be a non-empty array"
            )
        
        if not subject or not body:
            return create_error_response(
                400,
                "Missing required fields: subject and body are required"
            )
        
        if len(emails) == 0:
            return create_error_response(
                400,
                "emails array cannot be empty"
            )
        
        # Validate sender email
        if not is_valid_email(sender_email):
            return create_error_response(
                400,
                "Invalid sender email format"
            )
        
        # Process email sending
        results = []
        successful = 0
        failed = 0
        
        # Use ThreadPoolExecutor for concurrent email sending
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # Submit all email tasks
            future_to_email = {
                executor.submit(
                    send_single_email, 
                    email, 
                    subject, 
                    body, 
                    sender_email, 
                    is_html
                ): email 
                for email in emails
            }
            
            # Collect results
            for future in concurrent.futures.as_completed(future_to_email):
                email = future_to_email[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    if result['success']:
                        successful += 1
                    else:
                        failed += 1
                        
                except Exception as e:
                    logger.error(f"Error processing {email}: {str(e)}")
                    results.append({
                        'email': email,
                        'success': False,
                        'error': str(e)
                    })
                    failed += 1
        
        logger.info(f"Bulk email completed: {successful} successful, {failed} failed")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'status': 'success',
                'message': f'Bulk email completed: {successful} successful, {failed} failed',
                'total_emails': len(emails),
                'successful': successful,
                'failed': failed,
                'subject': subject,
                'provider': 'AWS SES',
                'sender': sender_email,
                'is_html': is_html,
                'results': results
            })
        }
        
    except Exception as e:
        logger.error(f"Bulk email error: {str(e)}")
        return create_error_response(
            500,
            f'Bulk email sending failed: {str(e)}'
        )

def send_single_email(email: str, subject: str, body: str, sender_email: str, is_html: bool) -> Dict[str, Any]:
    """
    Send a single email message
    
    Args:
        email: Recipient email address
        subject: Email subject
        body: Email body
        sender_email: Sender email address
        is_html: Whether body is HTML
        
    Returns:
        Dict: Result of email sending
    """
    try:
        # Validate email format
        if not is_valid_email(email):
            return {
                'email': email,
                'success': False,
                'error': 'Invalid email format'
            }
        
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
        
        return {
            'email': email,
            'success': True,
            'message_id': response['MessageId']
        }
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        
        return {
            'email': email,
            'success': False,
            'error': f'AWS SES error: {error_message}'
        }
        
    except Exception as e:
        return {
            'email': email,
            'success': False,
            'error': str(e)
        }

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
        'emails': ['student1@example.com', 'student2@example.com'],
        'subject': 'Important Announcement',
        'body': 'Dear Students,\n\nThis is an important announcement regarding the upcoming examination.\n\nPlease check the notice board for more details.\n\nBest regards,\nAdministration',
        'is_html': False
    }
    
    result = lambda_handler(test_event, {})
    print(json.dumps(result, indent=2))
