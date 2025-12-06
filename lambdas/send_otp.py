#!/usr/bin/env python3
"""
Send OTP Lambda Function
========================

AWS Lambda function to generate and send OTP (One-Time Password) via SMS.
Designed for educational institutions to send OTPs for student verification.

Input Format:
{
    "mobile": "+911234567890",
    "purpose": "login|registration|password_reset"
}

Output Format:
{
    "status": "success|error",
    "message": "OTP sent successfully",
    "otp_id": "otp_1234567890",
    "mobile": "+911234567890",
    "expires_in": 600
}

Author: AI Telecaller Team
Version: 1.0.0
"""

import json
import boto3
import logging
import os
import psycopg2
import random
import re
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS SNS client
sns_client = boto3.client('sns', region_name='us-west-2')

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'lwl_pg_us_2'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', '')
}

# OTP configuration
OTP_LENGTH = 6
OTP_EXPIRY_MINUTES = 10
MAX_OTP_ATTEMPTS = 3

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for sending OTP
    
    Args:
        event: Lambda event containing mobile and purpose
        context: Lambda context object
        
    Returns:
        Dict: Response with OTP details
    """
    try:
        # Parse input
        mobile = event.get('mobile')
        purpose = event.get('purpose', 'login')
        
        # Validate input
        if not mobile:
            return create_error_response(
                400,
                "Missing required field: mobile is required"
            )
        
        # Validate phone number format
        formatted_mobile = format_phone_number(mobile)
        if not formatted_mobile:
            return create_error_response(
                400,
                "Invalid phone number format. Use E.164 format: +1234567890"
            )
        
        # Check rate limiting
        if not check_rate_limit(formatted_mobile):
            return create_error_response(
                429,
                "Too many OTP requests. Please try again later."
            )
        
        # Generate OTP
        otp_code = generate_otp()
        otp_id = f"otp_{int(datetime.now().timestamp())}"
        
        # Store OTP in database
        store_otp_in_database(otp_id, formatted_mobile, otp_code, purpose)
        
        # Send OTP via SMS
        sms_result = send_otp_sms(formatted_mobile, otp_code, purpose)
        
        if not sms_result['success']:
            return create_error_response(
                500,
                f"Failed to send OTP: {sms_result['error']}"
            )
        
        logger.info(f"OTP sent successfully to {formatted_mobile}: {otp_id}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'status': 'success',
                'message': 'OTP sent successfully',
                'otp_id': otp_id,
                'mobile': formatted_mobile,
                'purpose': purpose,
                'expires_in': OTP_EXPIRY_MINUTES * 60,
                'message_id': sms_result.get('message_id'),
                'provider': 'AWS SNS'
            })
        }
        
    except Exception as e:
        logger.error(f"OTP sending error: {str(e)}")
        return create_error_response(
            500,
            f'Failed to send OTP: {str(e)}'
        )

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

def generate_otp() -> str:
    """
    Generate a random OTP
    
    Returns:
        OTP string
    """
    return str(random.randint(10**(OTP_LENGTH-1), 10**OTP_LENGTH - 1))

def check_rate_limit(mobile: str) -> bool:
    """
    Check if mobile number is within rate limits
    
    Args:
        mobile: Phone number
        
    Returns:
        True if within limits, False otherwise
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Check OTP requests in the last hour
        one_hour_ago = datetime.now() - timedelta(hours=1)
        cursor.execute("""
            SELECT COUNT(*) FROM otp_requests 
            WHERE mobile = %s AND created_at > %s
        """, (mobile, one_hour_ago))
        
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        # Allow maximum 5 OTP requests per hour
        return count < 5
        
    except Exception as e:
        logger.error(f"Rate limit check error: {str(e)}")
        return True  # Allow if check fails

def store_otp_in_database(otp_id: str, mobile: str, otp_code: str, purpose: str):
    """
    Store OTP in database
    
    Args:
        otp_id: Unique OTP ID
        mobile: Phone number
        otp_code: OTP code
        purpose: OTP purpose
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Calculate expiry time
        expires_at = datetime.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)
        
        # Store OTP
        cursor.execute("""
            INSERT INTO otp_requests (otp_id, mobile, otp_code, purpose, expires_at, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (otp_id, mobile, otp_code, purpose, expires_at, datetime.now()))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"OTP stored in database: {otp_id}")
        
    except Exception as e:
        logger.error(f"Database storage error: {str(e)}")
        raise

def send_otp_sms(mobile: str, otp_code: str, purpose: str) -> Dict[str, Any]:
    """
    Send OTP via SMS
    
    Args:
        mobile: Phone number
        otp_code: OTP code
        purpose: OTP purpose
        
    Returns:
        Dict with SMS result
    """
    try:
        # Generate SMS message based on purpose
        messages = {
            'login': f"Your login OTP is {otp_code}. Valid for {OTP_EXPIRY_MINUTES} minutes. Do not share with anyone.",
            'registration': f"Your registration OTP is {otp_code}. Valid for {OTP_EXPIRY_MINUTES} minutes. Do not share with anyone.",
            'password_reset': f"Your password reset OTP is {otp_code}. Valid for {OTP_EXPIRY_MINUTES} minutes. Do not share with anyone."
        }
        
        message = messages.get(purpose, f"Your OTP is {otp_code}. Valid for {OTP_EXPIRY_MINUTES} minutes. Do not share with anyone.")
        
        # Send SMS via SNS
        response = sns_client.publish(
            PhoneNumber=mobile,
            Message=message,
            MessageAttributes={
                'AWS.SNS.SMS.SenderID': {
                    'DataType': 'String',
                    'StringValue': 'EDUOTP'
                },
                'AWS.SNS.SMS.SMSType': {
                    'DataType': 'String',
                    'StringValue': 'Transactional'
                }
            }
        )
        
        return {
            'success': True,
            'message_id': response['MessageId']
        }
        
    except ClientError as e:
        error_message = e.response['Error']['Message']
        return {
            'success': False,
            'error': f'AWS SNS error: {error_message}'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

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
        'mobile': '+911234567890',
        'purpose': 'login'
    }
    
    result = lambda_handler(test_event, {})
    print(json.dumps(result, indent=2))
