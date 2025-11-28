#!/usr/bin/env python3
"""
Schedule IVR Call Lambda Function
================================

AWS Lambda function to schedule IVR calls using EventBridge/CloudWatch Events.
Designed for educational institutions to schedule automated calls at specific times.

Input Format:
{
    "student_id": "123",
    "time": "2025-10-27T15:00:00Z",
    "topic": "fees",
    "phone": "+911234567890"
}

Output Format:
{
    "status": "success|error",
    "message": "Call scheduled successfully",
    "schedule_id": "schedule-1234567890",
    "student_id": "123",
    "scheduled_time": "2025-10-27T15:00:00Z"
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
from datetime import datetime, timezone
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS EventBridge client
eventbridge_client = boto3.client('events', region_name='us-west-2')

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'lwl_pg_us_2'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', '')
}

# Lambda function ARN for ivr_call_student
IVR_CALL_LAMBDA_ARN = os.getenv('IVR_CALL_LAMBDA_ARN', 'arn:aws:lambda:us-west-2:123456789012:function:ivr_call_student')

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for scheduling IVR calls
    
    Args:
        event: Lambda event containing student_id, time, topic, and phone
        context: Lambda context object
        
    Returns:
        Dict: Response with schedule details
    """
    try:
        # Parse input
        student_id = event.get('student_id')
        scheduled_time_str = event.get('time')
        topic = event.get('topic', 'general')
        phone = event.get('phone')
        
        # Validate input
        if not student_id or not scheduled_time_str:
            return create_error_response(
                400,
                "Missing required fields: student_id and time are required"
            )
        
        # Parse and validate scheduled time
        try:
            scheduled_time = datetime.fromisoformat(scheduled_time_str.replace('Z', '+00:00'))
        except ValueError:
            return create_error_response(
                400,
                "Invalid time format. Use ISO 8601 format: 2025-10-27T15:00:00Z"
            )
        
        # Check if scheduled time is in the future
        if scheduled_time <= datetime.now(timezone.utc):
            return create_error_response(
                400,
                "Scheduled time must be in the future"
            )
        
        # Get student information
        student_info = get_student_info(student_id)
        if not student_info:
            return create_error_response(
                404,
                f"Student with ID {student_id} not found"
            )
        
        # Use phone from student info if not provided
        if not phone:
            phone = student_info.get('phone')
            if not phone:
                return create_error_response(
                    400,
                    "Phone number not provided and not found in student record"
                )
        
        # Create EventBridge rule
        rule_name = f"ivr-call-{student_id}-{int(scheduled_time.timestamp())}"
        schedule_id = create_eventbridge_rule(
            rule_name=rule_name,
            scheduled_time=scheduled_time,
            student_id=student_id,
            topic=topic,
            phone=phone
        )
        
        # Log schedule in database
        log_schedule_in_database(
            schedule_id=schedule_id,
            student_id=student_id,
            scheduled_time=scheduled_time,
            topic=topic,
            phone=phone,
            status='scheduled'
        )
        
        logger.info(f"Call scheduled successfully for student {student_id} at {scheduled_time}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'status': 'success',
                'message': 'Call scheduled successfully',
                'schedule_id': schedule_id,
                'student_id': student_id,
                'scheduled_time': scheduled_time_str,
                'topic': topic,
                'phone': phone,
                'student_name': student_info.get('name', 'Unknown')
            })
        }
        
    except Exception as e:
        logger.error(f"Schedule error: {str(e)}")
        return create_error_response(
            500,
            f'Failed to schedule call: {str(e)}'
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
            SELECT id, name, email, phone, course, batch
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
                'batch': result[5]
            }
        
        return None
        
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        return None

def create_eventbridge_rule(rule_name: str, scheduled_time: datetime, 
                          student_id: str, topic: str, phone: str) -> str:
    """
    Create EventBridge rule for scheduled call
    
    Args:
        rule_name: Name for the EventBridge rule
        scheduled_time: When to trigger the call
        student_id: Student ID
        topic: Call topic
        phone: Phone number
        
    Returns:
        Rule ARN
    """
    try:
        # Create the rule
        response = eventbridge_client.put_rule(
            Name=rule_name,
            ScheduleExpression=f"at({scheduled_time.strftime('%Y-%m-%dT%H:%M:%S')})",
            State='ENABLED',
            Description=f"Scheduled IVR call for student {student_id}"
        )
        
        rule_arn = response['RuleArn']
        
        # Add target (Lambda function)
        eventbridge_client.put_targets(
            Rule=rule_name,
            Targets=[
                {
                    'Id': '1',
                    'Arn': IVR_CALL_LAMBDA_ARN,
                    'Input': json.dumps({
                        'student_id': student_id,
                        'topic': topic,
                        'phone': phone
                    })
                }
            ]
        )
        
        # Add permission for EventBridge to invoke Lambda
        lambda_client = boto3.client('lambda', region_name='us-west-2')
        try:
            lambda_client.add_permission(
                FunctionName=IVR_CALL_LAMBDA_ARN.split(':')[-1],
                StatementId=f"eventbridge-{rule_name}",
                Action='lambda:InvokeFunction',
                Principal='events.amazonaws.com',
                SourceArn=rule_arn
            )
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceConflictException':
                logger.warning(f"Permission already exists or error: {e}")
        
        return rule_arn
        
    except ClientError as e:
        logger.error(f"EventBridge error: {str(e)}")
        raise

def log_schedule_in_database(schedule_id: str, student_id: str, scheduled_time: datetime,
                           topic: str, phone: str, status: str):
    """
    Log schedule details in database
    
    Args:
        schedule_id: Schedule ID/ARN
        student_id: Student ID
        scheduled_time: When the call is scheduled
        topic: Call topic
        phone: Phone number
        status: Schedule status
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO scheduled_calls (schedule_id, student_id, scheduled_time, topic, phone, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (schedule_id, student_id, scheduled_time, topic, phone, status, datetime.now()))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Schedule logged in database: {schedule_id}")
        
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
        'time': '2025-01-05T15:00:00Z',
        'topic': 'fees',
        'phone': '+911234567890'
    }
    
    result = lambda_handler(test_event, {})
    print(json.dumps(result, indent=2))
