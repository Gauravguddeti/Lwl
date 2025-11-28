#!/usr/bin/env python3
"""
IVR Call Student Lambda Function
===============================

AWS Lambda function to make AI-powered voice calls to students using Twilio.
Designed for educational institutions to make automated calls about fees, attendance, etc.

Input Format:
{
    "student_id": "123",
    "topic": "fees",
    "phone": "+911234567890"
}

Output Format:
{
    "status": "success|error",
    "message": "Call initiated successfully",
    "call_sid": "CAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "student_id": "123",
    "phone": "+911234567890",
    "topic": "fees"
}

Author: AI Telecaller Team
Version: 1.0.0
"""

import json
import boto3
import logging
import os
import psycopg2
from typing import Dict, Any, Optional
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
from datetime import datetime

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize Twilio client
twilio_client = Client(
    os.getenv('TWILIO_ACCOUNT_SID'),
    os.getenv('TWILIO_AUTH_TOKEN')
)

# Twilio phone number
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'lwl_pg_us_2'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', '')
}

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for making IVR calls to students
    
    Args:
        event: Lambda event containing student_id, topic, and phone
        context: Lambda context object
        
    Returns:
        Dict: Response with call details
    """
    try:
        # Parse input
        student_id = event.get('student_id')
        topic = event.get('topic')
        phone = event.get('phone')
        
        # Validate input
        if not student_id or not topic or not phone:
            return create_error_response(
                400,
                "Missing required fields: student_id, topic, and phone are required"
            )
        
        # Get student information from database
        student_info = get_student_info(student_id)
        if not student_info:
            return create_error_response(
                404,
                f"Student with ID {student_id} not found"
            )
        
        # Generate AI prompt based on topic
        ai_prompt = generate_ai_prompt(student_info, topic)
        
        # Make the call via Twilio
        call_response = make_twilio_call(phone, ai_prompt, student_id, topic)
        
        if not call_response.get('call_sid'):
            return create_error_response(
                500,
                "Failed to initiate call"
            )
        
        # Log call in database
        log_call_in_database(
            call_sid=call_response['call_sid'],
            student_id=student_id,
            phone=phone,
            topic=topic,
            status='initiated'
        )
        
        logger.info(f"Call initiated successfully for student {student_id}: {call_response['call_sid']}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'status': 'success',
                'message': 'Call initiated successfully',
                'call_sid': call_response['call_sid'],
                'student_id': student_id,
                'phone': phone,
                'topic': topic,
                'student_name': student_info.get('name', 'Unknown'),
                'provider': 'Twilio'
            })
        }
        
    except TwilioException as e:
        logger.error(f"Twilio error: {str(e)}")
        return create_error_response(
            500,
            f'Call initiation failed: {str(e)}'
        )
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return create_error_response(
            500,
            f'Internal server error: {str(e)}'
        )

def get_student_info(student_id: str) -> Optional[Dict[str, Any]]:
    """
    Get student information from database
    
    Args:
        student_id: Student ID
        
    Returns:
        Dict with student information or None if not found
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Query student information
        cursor.execute("""
            SELECT id, name, email, phone, course, batch, fees_due, last_payment_date
            FROM students 
            WHERE id = %s
        """, (student_id,))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result:
            return {
                'id': result[0],
                'name': result[1],
                'email': result[2],
                'phone': result[3],
                'course': result[4],
                'batch': result[5],
                'fees_due': result[6],
                'last_payment_date': result[7]
            }
        
        return None
        
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        return None

def generate_ai_prompt(student_info: Dict[str, Any], topic: str) -> str:
    """
    Generate AI prompt based on student info and topic
    
    Args:
        student_info: Student information
        topic: Call topic (fees, attendance, etc.)
        
    Returns:
        AI prompt string
    """
    student_name = student_info.get('name', 'Student')
    course = student_info.get('course', 'your course')
    
    prompts = {
        'fees': f"""
        You are calling {student_name} from the educational institution about their fee payment.
        
        Student Details:
        - Name: {student_name}
        - Course: {course}
        - Fees Due: {student_info.get('fees_due', 'Not specified')}
        
        Be polite, professional, and helpful. Explain the fee structure and payment options.
        Ask if they have any questions about the payment process.
        """,
        
        'attendance': f"""
        You are calling {student_name} from the educational institution about their attendance.
        
        Student Details:
        - Name: {student_name}
        - Course: {course}
        
        Be polite and professional. Discuss their attendance record and encourage regular attendance.
        Mention the importance of attendance for academic success.
        """,
        
        'exam': f"""
        You are calling {student_name} from the educational institution about upcoming examinations.
        
        Student Details:
        - Name: {student_name}
        - Course: {course}
        
        Be polite and professional. Inform them about exam schedules, important dates, and preparation tips.
        Ask if they need any clarification about the examination process.
        """,
        
        'general': f"""
        You are calling {student_name} from the educational institution for a general inquiry.
        
        Student Details:
        - Name: {student_name}
        - Course: {course}
        
        Be polite, professional, and helpful. Ask how they are doing and if they need any assistance.
        """
    }
    
    return prompts.get(topic, prompts['general'])

def make_twilio_call(phone: str, ai_prompt: str, student_id: str, topic: str) -> Dict[str, Any]:
    """
    Make a call using Twilio Voice API
    
    Args:
        phone: Phone number to call
        ai_prompt: AI prompt for the call
        student_id: Student ID
        topic: Call topic
        
    Returns:
        Dict with call response
    """
    try:
        # Create TwiML for the call
        twiml_url = create_twiml_url(ai_prompt, student_id, topic)
        
        # Make the call
        call = twilio_client.calls.create(
            to=phone,
            from_=TWILIO_PHONE_NUMBER,
            url=twiml_url,
            method='POST',
            timeout=30,
            record=True,
            status_callback=f"https://your-webhook-url.com/call-status",
            status_callback_event=['initiated', 'ringing', 'answered', 'completed']
        )
        
        return {
            'call_sid': call.sid,
            'status': call.status,
            'to': call.to,
            'from': call.from_
        }
        
    except TwilioException as e:
        logger.error(f"Twilio call error: {str(e)}")
        raise

def create_twiml_url(ai_prompt: str, student_id: str, topic: str) -> str:
    """
    Create TwiML URL for the call
    
    Args:
        ai_prompt: AI prompt for the call
        student_id: Student ID
        topic: Call topic
        
    Returns:
        TwiML URL
    """
    # In a real implementation, this would point to your TwiML generation endpoint
    # For now, return a placeholder URL
    base_url = os.getenv('TWIML_WEBHOOK_URL', 'https://your-lambda-url.amazonaws.com/twiml')
    
    # Encode parameters
    import urllib.parse
    params = {
        'prompt': ai_prompt,
        'student_id': student_id,
        'topic': topic
    }
    
    query_string = urllib.parse.urlencode(params)
    return f"{base_url}?{query_string}"

def log_call_in_database(call_sid: str, student_id: str, phone: str, topic: str, status: str):
    """
    Log call details in database
    
    Args:
        call_sid: Twilio call SID
        student_id: Student ID
        phone: Phone number
        topic: Call topic
        status: Call status
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO call_logs (call_sid, student_id, phone, topic, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (call_sid, student_id, phone, topic, status, datetime.now()))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Call logged in database: {call_sid}")
        
    except Exception as e:
        logger.error(f"Database logging error: {str(e)}")

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
        'student_id': '123',
        'topic': 'fees',
        'phone': '+911234567890'
    }
    
    result = lambda_handler(test_event, {})
    print(json.dumps(result, indent=2))
