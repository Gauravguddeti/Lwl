#!/usr/bin/env python3
"""
Send Bulk SMS Lambda Function
============================

AWS Lambda function to send bulk SMS messages using AWS SNS.
Designed for educational institutions to send notifications to multiple students.

Input Format:
{
    "mobiles": ["+911234567890", "+911234567891"],
    "message": "Hello students"
}

Output Format:
{
    "status": "success|error",
    "message": "Bulk SMS completed: 2 successful, 0 failed",
    "total_numbers": 2,
    "successful": 2,
    "failed": 0,
    "total_cost": "$0.0150",
    "results": [...]
}

Author: AI Telecaller Team
Version: 1.0.0
"""

import json
import boto3
import logging
import re
import asyncio
import concurrent.futures
from typing import Dict, Any, List, Optional
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS SNS client
sns_client = boto3.client('sns', region_name='us-west-2')

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for sending bulk SMS
    
    Args:
        event: Lambda event containing mobiles and message
        context: Lambda context object
        
    Returns:
        Dict: Response with bulk operation results
    """
    try:
        # Parse input
        mobiles = event.get('mobiles', [])
        message = event.get('message')
        
        # Validate input
        if not mobiles or not isinstance(mobiles, list):
            return create_error_response(
                400,
                "Missing or invalid field: mobiles must be a non-empty array"
            )
        
        if not message:
            return create_error_response(
                400,
                "Missing required field: message is required"
            )
        
        if len(mobiles) == 0:
            return create_error_response(
                400,
                "mobiles array cannot be empty"
            )
        
        # Validate message length
        if len(message) > 1600:
            return create_error_response(
                400,
                "Message too long. Maximum 1600 characters allowed."
            )
        
        # Process SMS sending
        results = []
        successful = 0
        failed = 0
        total_cost = 0.0
        
        # Use ThreadPoolExecutor for concurrent SMS sending
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            # Submit all SMS tasks
            future_to_mobile = {
                executor.submit(send_single_sms, mobile, message): mobile 
                for mobile in mobiles
            }
            
            # Collect results
            for future in concurrent.futures.as_completed(future_to_mobile):
                mobile = future_to_mobile[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    if result['success']:
                        successful += 1
                        total_cost += result.get('cost', 0.0)
                    else:
                        failed += 1
                        
                except Exception as e:
                    logger.error(f"Error processing {mobile}: {str(e)}")
                    results.append({
                        'phone_number': mobile,
                        'success': False,
                        'error': str(e),
                        'cost': 0.0
                    })
                    failed += 1
        
        logger.info(f"Bulk SMS completed: {successful} successful, {failed} failed")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'status': 'success',
                'message': f'Bulk SMS completed: {successful} successful, {failed} failed',
                'total_numbers': len(mobiles),
                'successful': successful,
                'failed': failed,
                'total_cost': f'${total_cost:.4f}',
                'character_count': len(message),
                'provider': 'AWS SNS',
                'results': results
            })
        }
        
    except Exception as e:
        logger.error(f"Bulk SMS error: {str(e)}")
        return create_error_response(
            500,
            f'Bulk SMS sending failed: {str(e)}'
        )

def send_single_sms(mobile: str, message: str) -> Dict[str, Any]:
    """
    Send a single SMS message
    
    Args:
        mobile: Phone number
        message: SMS message
        
    Returns:
        Dict: Result of SMS sending
    """
    try:
        # Format phone number
        formatted_mobile = format_phone_number(mobile)
        if not formatted_mobile:
            return {
                'phone_number': mobile,
                'success': False,
                'error': 'Invalid phone number format',
                'cost': 0.0
            }
        
        # Send SMS via SNS
        response = sns_client.publish(
            PhoneNumber=formatted_mobile,
            Message=message,
            MessageAttributes={
                'AWS.SNS.SMS.SenderID': {
                    'DataType': 'String',
                    'StringValue': 'EDU'
                },
                'AWS.SNS.SMS.SMSType': {
                    'DataType': 'String',
                    'StringValue': 'Promotional'
                }
            }
        )
        
        # Calculate cost
        cost = estimate_sms_cost(formatted_mobile, message)
        
        return {
            'phone_number': formatted_mobile,
            'success': True,
            'message_id': response['MessageId'],
            'cost': cost
        }
        
    except ClientError as e:
        error_message = e.response['Error']['Message']
        return {
            'phone_number': mobile,
            'success': False,
            'error': f'AWS SNS error: {error_message}',
            'cost': 0.0
        }
        
    except Exception as e:
        return {
            'phone_number': mobile,
            'success': False,
            'error': str(e),
            'cost': 0.0
        }

def format_phone_number(phone_number: str) -> Optional[str]:
    """
    Format phone number to E.164 format
    
    Args:
        phone_number: Phone number in various formats
        
    Returns:
        Formatted phone number or None if invalid
    """
    if not phone_number:
        return None
    
    # Remove all non-digit characters except +
    cleaned = re.sub(r'[^\d+]', '', phone_number)
    
    # If it starts with +, validate it's a proper E.164 number
    if cleaned.startswith('+'):
        if len(cleaned) >= 8 and len(cleaned) <= 15:
            return cleaned
    
    # If it's just digits, assume Indian number and add +91
    elif cleaned.isdigit():
        if len(cleaned) == 10:  # Indian mobile number
            return f'+91{cleaned}'
        elif len(cleaned) == 11 and cleaned.startswith('91'):
            return f'+{cleaned}'
        elif len(cleaned) == 12 and cleaned.startswith('91'):
            return f'+{cleaned}'
    
    return None

def estimate_sms_cost(phone_number: str, message: str) -> float:
    """
    Estimate SMS cost based on destination and message length
    
    Args:
        phone_number: Formatted phone number
        message: SMS message content
        
    Returns:
        Estimated cost in USD
    """
    # Basic cost estimation
    base_cost = 0.0075  # US/Canada base cost
    
    # Adjust for international numbers
    if not phone_number.startswith('+1'):
        if phone_number.startswith('+91'):  # India
            base_cost = 0.0075
        else:  # Other international
            base_cost = 0.02
    
    # Calculate segments for long messages
    segments = max(1, len(message) // 160)
    
    return base_cost * segments

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
        'mobiles': ['+911234567890', '+911234567891'],
        'message': 'Hello students! Your exam is tomorrow.'
    }
    
    result = lambda_handler(test_event, {})
    print(json.dumps(result, indent=2))
