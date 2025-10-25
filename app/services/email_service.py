#!/usr/bin/env python3
"""
Email Service - Extracted from Working Implementation
Clean email service supporting SMTP, SES Custom Domain, and SES Subdomain
Ready for integration into IVR systems
"""

import json
import boto3
import smtplib
import logging
import base64
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import Dict, Any, List, Optional

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class EmailService:
    """Production-ready Email Service supporting multiple providers"""
    
    def __init__(self):
        """Initialize AWS SES client"""
        self.ses_client = boto3.client('ses', region_name=os.getenv('AWS_REGION', 'us-west-2'))
        
    def send_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Universal email sending method
        
        Args:
            email_data: Dictionary containing email details
            
        Returns:
            Dict with success status and message details
        """
        try:
            email_type = email_data.get('email_type', 'smtp')
            
            # Validate required fields
            required_fields = ['to_email', 'subject', 'body']
            for field in required_fields:
                if not email_data.get(field):
                    return {
                        'success': False,
                        'error': f'Missing required field: {field}'
                    }
            
            # Route to appropriate email provider
            if email_type == 'smtp':
                return self._send_smtp_email(email_data)
            elif email_type == 'customdomain':
                return self._send_ses_custom_domain_email(email_data)
            elif email_type == 'subdomain':
                return self._send_ses_subdomain_email(email_data)
            else:
                return {
                    'success': False,
                    'error': f'Invalid email_type: {email_type}. Supported: smtp, customdomain, subdomain'
                }
                
        except Exception as e:
            logger.error(f"Email service error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _send_smtp_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send email using SMTP (Gmail)"""
        try:
            # SMTP configuration
            smtp_server = email_data.get('smtp_server', 'smtp.gmail.com')
            smtp_port = int(email_data.get('smtp_port', 587))
            smtp_email = email_data.get('smtp_email')
            smtp_password = email_data.get('smtp_password')
            
            if not smtp_email or not smtp_password:
                return {
                    'success': False,
                    'error': 'SMTP email and password are required for Gmail sending'
                }
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = smtp_email
            msg['To'] = email_data['to_email']
            msg['Subject'] = email_data['subject']
            
            # Add CC and BCC if provided
            if email_data.get('cc'):
                msg['Cc'] = ', '.join(email_data['cc'])
            if email_data.get('reply_to'):
                msg['Reply-To'] = email_data['reply_to']
            
            # Add body (support HTML)
            body_type = 'html' if email_data.get('is_html', False) else 'plain'
            msg.attach(MIMEText(email_data['body'], body_type))
            
            # Add attachments if provided
            attachments_count = 0
            if email_data.get('attachments'):
                attachments_count = self._add_attachments(msg, email_data['attachments'])
            
            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_email, smtp_password)
                
                recipients = [email_data['to_email']]
                if email_data.get('cc'):
                    recipients.extend(email_data['cc'])
                if email_data.get('bcc'):
                    recipients.extend(email_data['bcc'])
                
                server.send_message(msg, to_addrs=recipients)
            
            return {
                'success': True,
                'message': f'SMTP email sent successfully to {email_data["to_email"]}',
                'provider': 'SMTP (Gmail)',
                'recipient': email_data['to_email'],
                'attachments_count': attachments_count
            }
            
        except Exception as e:
            logger.error(f"SMTP email error: {e}")
            return {'success': False, 'error': f'SMTP sending failed: {str(e)}'}
    
    def _send_ses_custom_domain_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send email using SES with custom domain (f5universe.com)"""
        try:
            sender_email = email_data.get('sender_email', 'support@f5universe.com')
            
            # For attachments, use raw email
            if email_data.get('attachments'):
                return self._send_ses_raw_email(email_data, sender_email)
            
            # Simple email without attachments
            response = self.ses_client.send_email(
                Source=sender_email,
                Destination={
                    'ToAddresses': [email_data['to_email']],
                    'CcAddresses': email_data.get('cc', []),
                    'BccAddresses': email_data.get('bcc', [])
                },
                Message={
                    'Subject': {'Data': email_data['subject'], 'Charset': 'UTF-8'},
                    'Body': {
                        'Text' if not email_data.get('is_html') else 'Html': {
                            'Data': email_data['body'],
                            'Charset': 'UTF-8'
                        }
                    }
                },
                ReplyToAddresses=[email_data.get('reply_to', sender_email)]
            )
            
            return {
                'success': True,
                'message': f'SES Custom Domain email sent to {email_data["to_email"]}',
                'message_id': response['MessageId'],
                'provider': 'SES Custom Domain (f5universe.com)',
                'recipient': email_data['to_email']
            }
            
        except Exception as e:
            logger.error(f"SES Custom Domain error: {e}")
            return {'success': False, 'error': f'SES Custom Domain sending failed: {str(e)}'}
    
    def _send_ses_subdomain_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send email using SES with subdomain (mail.futuristic5.com)"""
        try:
            sender_email = email_data.get('sender_email', 'noreply@mail.futuristic5.com')
            
            # For attachments, use raw email
            if email_data.get('attachments'):
                return self._send_ses_raw_email(email_data, sender_email)
            
            # Simple email without attachments
            response = self.ses_client.send_email(
                Source=sender_email,
                Destination={
                    'ToAddresses': [email_data['to_email']],
                    'CcAddresses': email_data.get('cc', []),
                    'BccAddresses': email_data.get('bcc', [])
                },
                Message={
                    'Subject': {'Data': email_data['subject'], 'Charset': 'UTF-8'},
                    'Body': {
                        'Text' if not email_data.get('is_html') else 'Html': {
                            'Data': email_data['body'],
                            'Charset': 'UTF-8'
                        }
                    }
                },
                ReplyToAddresses=[email_data.get('reply_to', sender_email)]
            )
            
            return {
                'success': True,
                'message': f'SES Subdomain email sent to {email_data["to_email"]}',
                'message_id': response['MessageId'],
                'provider': 'SES Subdomain (mail.futuristic5.com)',
                'recipient': email_data['to_email']
            }
            
        except Exception as e:
            logger.error(f"SES Subdomain error: {e}")
            return {'success': False, 'error': f'SES Subdomain sending failed: {str(e)}'}
    
    def _send_ses_raw_email(self, email_data: Dict[str, Any], sender_email: str) -> Dict[str, Any]:
        """Send email with attachments using SES SendRawEmail"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = email_data['to_email']
            msg['Subject'] = email_data['subject']
            
            # Add CC, BCC, Reply-To
            if email_data.get('cc'):
                msg['Cc'] = ', '.join(email_data['cc'])
            if email_data.get('reply_to'):
                msg['Reply-To'] = email_data['reply_to']
            
            # Add body
            body_type = 'html' if email_data.get('is_html', False) else 'plain'
            msg.attach(MIMEText(email_data['body'], body_type))
            
            # Add attachments
            attachments_count = 0
            if email_data.get('attachments'):
                attachments_count = self._add_attachments(msg, email_data['attachments'])
            
            # Send raw email
            response = self.ses_client.send_raw_email(
                Source=sender_email,
                Destinations=[email_data['to_email']] + email_data.get('cc', []) + email_data.get('bcc', []),
                RawMessage={'Data': msg.as_string()}
            )
            
            provider = 'SES Custom Domain' if 'f5universe.com' in sender_email else 'SES Subdomain'
            
            return {
                'success': True,
                'message': f'{provider} email with attachments sent to {email_data["to_email"]}',
                'message_id': response['MessageId'],
                'provider': provider,
                'recipient': email_data['to_email'],
                'attachments_count': attachments_count
            }
            
        except Exception as e:
            logger.error(f"SES raw email error: {e}")
            return {'success': False, 'error': f'SES raw email sending failed: {str(e)}'}
    
    def _add_attachments(self, msg: MIMEMultipart, attachments: List[Dict[str, Any]]) -> int:
        """Add attachments to email message"""
        added_count = 0
        
        for attachment in attachments:
            try:
                # Decode base64 attachment data
                file_data = base64.b64decode(attachment['content'])
                filename = attachment['filename']
                content_type = attachment.get('content_type', 'application/octet-stream')
                
                # Create attachment
                attachment_part = MIMEApplication(file_data)
                attachment_part.add_header(
                    'Content-Disposition',
                    'attachment',
                    filename=filename
                )
                attachment_part.add_header('Content-Type', content_type)
                
                msg.attach(attachment_part)
                added_count += 1
                
            except Exception as e:
                logger.warning(f"Failed to attach {attachment.get('filename', 'unknown')}: {e}")
        
        return added_count
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get email service status"""
        try:
            # Test SES connectivity
            response = self.ses_client.get_send_quota()
            
            return {
                'success': True,
                'status': 'operational',
                'service': 'email',
                'providers': {
                    'smtp': 'Available (Gmail)',
                    'ses_custom': 'Available (f5universe.com)',
                    'ses_subdomain': 'Available (mail.futuristic5.com)'
                },
                'ses_quota': {
                    'max_24_hour': response['Max24HourSend'],
                    'max_per_second': response['MaxSendRate'],
                    'sent_last_24_hours': response['SentLast24Hours']
                },
                'features': {
                    'attachments': 'Supported',
                    'html_emails': 'Supported',
                    'cc_bcc': 'Supported',
                    'reply_to': 'Supported'
                }
            }
            
        except Exception as e:
            logger.error(f"Email status check error: {e}")
            return {
                'success': False,
                'status': 'error',
                'error': str(e)
            }