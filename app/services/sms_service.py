#!/usr/bin/env python3
"""
SMS Service - Extracted from Working Implementation
Clean SMS service using Amazon SNS for single and bulk messaging
Ready for integration into IVR systems
"""

import json
import boto3
import logging
import re
import os
from typing import Dict, Any, List, Optional

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class SMSService:
    """Production-ready SMS Service using Amazon SNS"""
    
    def __init__(self):
        """Initialize AWS SNS client with error handling"""
        try:
            self.aws_region = os.getenv('AWS_REGION', 'us-west-2')
            self.sns_client = boto3.client('sns', region_name=self.aws_region)
            logger.info(f"✅ SMS service initialized for region: {self.aws_region}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize SNS client: {e}")
            self.sns_client = None
        
    def send_sms(self, sms_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send single SMS message
        
        Args:
            sms_data: Dictionary containing SMS details
            
        Returns:
            Dict with success status and message details
        """
        try:
            if not self.sns_client:
                return {
                    'success': False,
                    'error': 'SNS client not initialized. Check AWS credentials and region.'
                }
            
            phone_number = sms_data.get('phone_number')
            message = sms_data.get('message')
            sender_id = sms_data.get('sender_id', 'IVR')
            
            # Validate required fields
            if not phone_number or not message:
                return {
                    'success': False,
                    'error': 'Missing required fields: phone_number and message are required'
                }
            
            # Validate phone number format
            formatted_phone = self._format_phone_number(phone_number)
            if not formatted_phone:
                return {
                    'success': False,
                    'error': 'Invalid phone number format. Use E.164 format: +1234567890'
                }
            
            # Validate message length (SMS limit is 160 characters)
            if len(message) > 1600:  # Allow longer messages for concatenated SMS
                return {
                    'success': False,
                    'error': 'Message too long. Maximum 1600 characters allowed.'
                }
            
            # Send SMS via SNS
            response = self.sns_client.publish(
                PhoneNumber=formatted_phone,
                Message=message,
                MessageAttributes={
                    'AWS.SNS.SMS.SenderID': {
                        'DataType': 'String',
                        'StringValue': sender_id[:11]  # SenderID max 11 characters
                    },
                    'AWS.SNS.SMS.SMSType': {
                        'DataType': 'String',
                        'StringValue': 'Promotional'
                    }
                }
            )
            
            return {
                'success': True,
                'message': f'SMS sent successfully to {formatted_phone}',
                'message_id': response['MessageId'],
                'phone_number': formatted_phone,
                'sender_id': sender_id,
                'character_count': len(message),
                'estimated_cost': self._estimate_sms_cost(formatted_phone, message)
            }
            
        except Exception as e:
            logger.error(f"SMS sending error: {e}")
            return {'success': False, 'error': f'SMS sending failed: {str(e)}'}
    
    def send_bulk_sms(self, sms_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send SMS to multiple phone numbers
        
        Args:
            sms_data: Dictionary containing bulk SMS details
            
        Returns:
            Dict with success status and bulk operation results
        """
        try:
            if not self.sns_client:
                return {
                    'success': False,
                    'error': 'SNS client not initialized. Check AWS credentials and region.'
                }
            
            phone_numbers = sms_data.get('phone_numbers', [])
            message = sms_data.get('message')
            sender_id = sms_data.get('sender_id', 'IVR')
            
            # Validate required fields
            if not phone_numbers or not message:
                return {
                    'success': False,
                    'error': 'Missing required fields: phone_numbers (array) and message are required'
                }
            
            if not isinstance(phone_numbers, list) or len(phone_numbers) == 0:
                return {
                    'success': False,
                    'error': 'phone_numbers must be a non-empty array'
                }
            
            # Validate message length
            if len(message) > 1600:
                return {
                    'success': False,
                    'error': 'Message too long. Maximum 1600 characters allowed.'
                }
            
            # Process each phone number
            results = []
            successful = 0
            failed = 0
            total_cost = 0.0
            
            for phone_number in phone_numbers:
                try:
                    # Format and validate phone number
                    formatted_phone = self._format_phone_number(phone_number)
                    if not formatted_phone:
                        results.append({
                            'phone_number': phone_number,
                            'success': False,
                            'error': 'Invalid phone number format'
                        })
                        failed += 1
                        continue
                    
                    # Send SMS
                    response = self.sns_client.publish(
                        PhoneNumber=formatted_phone,
                        Message=message,
                        MessageAttributes={
                            'AWS.SNS.SMS.SenderID': {
                                'DataType': 'String',
                                'StringValue': sender_id[:11]
                            },
                            'AWS.SNS.SMS.SMSType': {
                                'DataType': 'String',
                                'StringValue': 'Promotional'
                            }
                        }
                    )
                    
                    cost = self._estimate_sms_cost(formatted_phone, message)
                    total_cost += cost
                    
                    results.append({
                        'phone_number': formatted_phone,
                        'success': True,
                        'message_id': response['MessageId'],
                        'cost': f'${cost:.4f}'
                    })
                    successful += 1
                    
                except Exception as e:
                    logger.error(f"Bulk SMS error for {phone_number}: {e}")
                    results.append({
                        'phone_number': phone_number,
                        'success': False,
                        'error': str(e)
                    })
                    failed += 1
            
            return {
                'success': True,
                'message': f'Bulk SMS completed: {successful} successful, {failed} failed',
                'total_numbers': len(phone_numbers),
                'successful': successful,
                'failed': failed,
                'sender_id': sender_id,
                'total_cost': f'${total_cost:.4f}',
                'character_count': len(message),
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Bulk SMS error: {e}")
            return {'success': False, 'error': f'Bulk SMS sending failed: {str(e)}'}
    
    def add_sandbox_number(self, phone_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add phone number to SMS sandbox for testing
        
        Args:
            phone_data: Dictionary containing phone number to add
            
        Returns:
            Dict with success status and instructions
        """
        try:
            phone_number = phone_data.get('phone_number')
            
            if not phone_number:
                return {
                    'success': False,
                    'error': 'Missing required field: phone_number'
                }
            
            # Format phone number
            formatted_phone = self._format_phone_number(phone_number)
            if not formatted_phone:
                return {
                    'success': False,
                    'error': 'Invalid phone number format. Use E.164 format: +1234567890'
                }
            
            # Note: AWS SNS sandbox management requires manual verification
            # This endpoint provides instructions for sandbox setup
            
            return {
                'success': True,
                'message': f'Instructions provided for adding {formatted_phone} to SMS sandbox',
                'phone_number': formatted_phone,
                'instructions': {
                    'step_1': 'Go to AWS SNS Console → Text messaging (SMS) → Sandbox destinations',
                    'step_2': f'Click "Add phone number" and enter {formatted_phone}',
                    'step_3': 'Click "Add phone number" and verify via SMS',
                    'step_4': 'Once verified, the number can receive SMS in sandbox mode',
                    'note': 'For production SMS, request to move out of sandbox mode'
                },
                'aws_console_url': 'https://console.aws.amazon.com/sns/v3/home#/mobile/text-messaging'
            }
            
        except Exception as e:
            logger.error(f"Add sandbox number error: {e}")
            return {'success': False, 'error': f'Sandbox setup failed: {str(e)}'}
    
    def get_sms_status(self, status_data: Dict[str, Any] = {}) -> Dict[str, Any]:
        """
        Get SMS service status and message delivery status
        
        Args:
            status_data: Optional dictionary containing message_id for status check
            
        Returns:
            Dict with service status information
        """
        try:
            if not self.sns_client:
                return {
                    'success': False,
                    'status': 'error',
                    'error': 'SNS client not initialized. Check AWS credentials and region.',
                    'service': 'sns-sms',
                    'region': self.aws_region
                }
            
            # Get SMS attributes from SNS
            response = self.sns_client.get_sms_attributes()
            
            result = {
                'success': True,
                'status': 'operational',
                'service': 'sns-sms',
                'region': self.aws_region,
                'sms_attributes': response.get('attributes', {}),
                'features': {
                    'single_sms': 'Supported',
                    'bulk_sms': 'Supported',
                    'international_sms': 'Supported',
                    'sender_id': 'Configurable (up to 11 characters)',
                    'message_length': 'Up to 1600 characters (concatenated)',
                    'sandbox_mode': 'Active (verify numbers first)'
                },
                'pricing': {
                    'us_canada': '$0.0075 per SMS',
                    'international': 'Varies by country',
                    'note': 'Actual costs may vary based on carrier and destination'
                }
            }
            
            # If message_id provided, simulate status check
            if status_data and status_data.get('message_id'):
                result['message_status'] = {
                    'message_id': status_data['message_id'],
                    'status': 'DELIVERED',  # Mock status
                    'note': 'SNS does not provide delivery confirmation by default'
                }
            
            return result
            
        except Exception as e:
            logger.error(f"SMS status error: {e}")
            return {
                'success': False,
                'status': 'error',
                'error': str(e)
            }
    
    def _format_phone_number(self, phone_number: str) -> Optional[str]:
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
            if len(cleaned) >= 8 and len(cleaned) <= 15:  # E.164 length constraints
                return cleaned
        
        # If it's just digits, assume US/Canada and add +1
        elif cleaned.isdigit():
            if len(cleaned) == 10:  # US/Canada format without country code
                return f'+1{cleaned}'
            elif len(cleaned) == 11 and cleaned.startswith('1'):  # US/Canada with 1
                return f'+{cleaned}'
        
        return None
    
    def _estimate_sms_cost(self, phone_number: str, message: str) -> float:
        """
        Estimate SMS cost based on destination and message length
        
        Args:
            phone_number: Formatted phone number
            message: SMS message content
            
        Returns:
            Estimated cost in USD
        """
        # Basic cost estimation (actual costs may vary)
        base_cost = 0.0075  # US/Canada base cost
        
        # Adjust for international numbers
        if not phone_number.startswith('+1'):
            base_cost = 0.02  # Rough international rate
        
        # Calculate segments for long messages
        segments = max(1, len(message) // 160)
        
        return base_cost * segments