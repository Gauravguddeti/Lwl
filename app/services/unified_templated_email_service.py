#!/usr/bin/env python3
"""
Unified Templated Email Service - Simple template selection
Single endpoint with multiple template types and consistent body format
"""

import json
import boto3
import smtplib
import logging
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class UnifiedTemplatedEmailService:
    """Unified templated email service with simple template selection"""
    
    def __init__(self):
        """Initialize email clients"""
        self.ses_client = boto3.client('ses', region_name=os.getenv('AWS_REGION', 'us-west-2'))
        
    def send_templated_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send templated email with unified interface
        
        Args:
            email_data: Dictionary containing:
                - email_type: 'smtp', 'customdomain', 'subdomain' 
                - template_type: 'otp', 'login', 'registration'
                - to_email: recipient email
                - Other fields as needed
                
        Returns:
            Dict with success status and message details
        """
        try:
            # Validate required fields
            email_type = email_data.get('email_type', 'smtp')
            template_type = email_data.get('template_type')
            
            # Handle both 'to_email' and 'to' for compatibility
            to_email = email_data.get('to_email') or email_data.get('to')
            
            if not template_type or not to_email:
                return {
                    'success': False,
                    'error': 'Missing required fields: email_type, template_type, and to_email (or to) are required'
                }
            
            # Generate email content based on template type
            email_content = self._generate_template_content(template_type, email_data)
            if not email_content['success']:
                return email_content
            
            # Prepare email data for sending
            send_data = {
                'email_type': email_type,
                'to_email': to_email,
                'subject': email_content['subject'],
                'body': email_content['body'],
                'is_html': True
            }
            
            # Add email type specific fields
            if email_type == 'smtp':
                send_data.update({
                    'smtp_email': email_data.get('smtp_email'),
                    'smtp_password': email_data.get('smtp_password')
                })
            elif email_type == 'customdomain':
                send_data['sender_email'] = 'support@f5universe.com'
            elif email_type == 'subdomain':
                send_data['sender_email'] = 'noreply@mail.futuristic5.com'
            
            # Send email using appropriate method
            if email_type == 'smtp':
                return self._send_smtp_templated_email(send_data, template_type)
            else:
                return self._send_ses_templated_email(send_data, template_type)
                
        except Exception as e:
            logger.error(f"Templated email service error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _generate_template_content(self, template_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate email content based on template type"""
        try:
            username = data.get('username', 'User')
            
            templates = {
                'otp': {
                    'subject': 'Your Verification Code',
                    'body': f'''
                    <html>
                    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; color: white; border-radius: 10px 10px 0 0;">
                            <h1 style="margin: 0; font-size: 28px;">🔐 Verification Code</h1>
                        </div>
                        
                        <div style="background: white; padding: 30px; border: 1px solid #ddd; border-radius: 0 0 10px 10px;">
                            <h2 style="color: #333; margin-bottom: 20px;">Hello {username}!</h2>
                            
                            <p style="color: #666; font-size: 16px; line-height: 1.6;">
                                Your verification code is:
                            </p>
                            
                            <div style="background: #f8f9fa; border: 2px solid #667eea; border-radius: 8px; padding: 20px; text-align: center; margin: 20px 0;">
                                <span style="font-size: 32px; font-weight: bold; color: #667eea; letter-spacing: 8px;">{data.get('otp_code', '123456')}</span>
                            </div>
                            
                            <p style="color: #666; font-size: 14px;">
                                This code will expire in {data.get('expiry_minutes', 10)} minutes.
                            </p>
                            
                            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                            <p style="color: #999; font-size: 12px; text-align: center;">
                                If you didn't request this code, please ignore this email.
                            </p>
                        </div>
                    </body>
                    </html>
                    '''
                },
                
                'login': {
                    'subject': 'Successful Login Notification',
                    'body': f'''
                    <html>
                    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                        <div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); padding: 30px; text-align: center; color: white; border-radius: 10px 10px 0 0;">
                            <h1 style="margin: 0; font-size: 28px;">✅ Login Successful</h1>
                        </div>
                        
                        <div style="background: white; padding: 30px; border: 1px solid #ddd; border-radius: 0 0 10px 10px;">
                            <h2 style="color: #333; margin-bottom: 20px;">Hello {username}!</h2>
                            
                            <p style="color: #666; font-size: 16px; line-height: 1.6;">
                                We're confirming that you successfully logged into your account.
                            </p>
                            
                            <div style="background: #f8f9fa; border-left: 4px solid #11998e; padding: 15px; margin: 20px 0;">
                                <p style="margin: 0; color: #333;"><strong>Login Details:</strong></p>
                                <p style="margin: 5px 0 0 0; color: #666;">Time: {data.get('login_time', 'Just now')}</p>
                                <p style="margin: 5px 0 0 0; color: #666;">Device: {data.get('device', 'Unknown device')}</p>
                            </div>
                            
                            <p style="color: #666; font-size: 14px;">
                                If this wasn't you, please secure your account immediately.
                            </p>
                            
                            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                            <p style="color: #999; font-size: 12px; text-align: center;">
                                This is an automated security notification.
                            </p>
                        </div>
                    </body>
                    </html>
                    '''
                },
                
                'registration': {
                    'subject': 'Welcome! Registration Successful',
                    'body': f'''
                    <html>
                    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                        <div style="background: linear-gradient(135deg, #ff6b6b 0%, #ffa726 100%); padding: 30px; text-align: center; color: white; border-radius: 10px 10px 0 0;">
                            <h1 style="margin: 0; font-size: 28px;">🎉 Welcome Aboard!</h1>
                        </div>
                        
                        <div style="background: white; padding: 30px; border: 1px solid #ddd; border-radius: 0 0 10px 10px;">
                            <h2 style="color: #333; margin-bottom: 20px;">Hello {username}!</h2>
                            
                            <p style="color: #666; font-size: 16px; line-height: 1.6;">
                                Congratulations! Your registration was successful and your account is now active.
                            </p>
                            
                            <div style="background: #f8f9fa; border-left: 4px solid #ff6b6b; padding: 15px; margin: 20px 0;">
                                <p style="margin: 0; color: #333;"><strong>Account Details:</strong></p>
                                <p style="margin: 5px 0 0 0; color: #666;">Email: {data.get('to_email', 'your-email@example.com')}</p>
                                <p style="margin: 5px 0 0 0; color: #666;">Registration Date: {data.get('registration_date', 'Today')}</p>
                            </div>
                            
                            <div style="text-align: center; margin: 30px 0;">
                                <a href="{data.get('login_url', '#')}" style="background: #ff6b6b; color: white; padding: 12px 30px; text-decoration: none; border-radius: 25px; font-weight: bold;">
                                    Login to Your Account
                                </a>
                            </div>
                            
                            <p style="color: #666; font-size: 14px;">
                                Start exploring all the amazing features we have to offer!
                            </p>
                            
                            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                            <p style="color: #999; font-size: 12px; text-align: center;">
                                Thank you for choosing our platform!
                            </p>
                        </div>
                    </body>
                    </html>
                    '''
                }
            }
            
            if template_type not in templates:
                return {
                    'success': False,
                    'error': f'Invalid template_type: {template_type}. Supported: otp, login, registration'
                }
            
            return {
                'success': True,
                'subject': templates[template_type]['subject'],
                'body': templates[template_type]['body']
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Template generation failed: {str(e)}'}
    
    def _send_smtp_templated_email(self, email_data: Dict[str, Any], template_type: str) -> Dict[str, Any]:
        """Send templated email via SMTP"""
        try:
            smtp_email = email_data.get('smtp_email')
            smtp_password = email_data.get('smtp_password')
            
            if not smtp_email or not smtp_password:
                return {
                    'success': False,
                    'error': 'SMTP email and password are required for smtp email_type'
                }
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = smtp_email
            msg['To'] = email_data['to_email']
            msg['Subject'] = email_data['subject']
            
            # Add HTML body
            html_part = MIMEText(email_data['body'], 'html')
            msg.attach(html_part)
            
            # Connect and send
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(smtp_email, smtp_password)
            server.send_message(msg)
            server.quit()
            
            return {
                'success': True,
                'message': f'Templated email ({template_type}) sent successfully via SMTP',
                'provider': 'SMTP (Gmail)',
                'template_type': template_type,
                'to_email': email_data['to_email'],
                'subject': email_data['subject']
            }
            
        except Exception as e:
            logger.error(f"SMTP templated email error: {e}")
            return {'success': False, 'error': f'SMTP sending failed: {str(e)}'}
    
    def _send_ses_templated_email(self, email_data: Dict[str, Any], template_type: str) -> Dict[str, Any]:
        """Send templated email via SES"""
        try:
            response = self.ses_client.send_email(
                Source=email_data['sender_email'],
                Destination={'ToAddresses': [email_data['to_email']]},
                Message={
                    'Subject': {'Data': email_data['subject']},
                    'Body': {
                        'Html': {'Data': email_data['body']}
                    }
                }
            )
            
            provider = 'SES Custom Domain' if 'f5universe.com' in email_data['sender_email'] else 'SES Subdomain'
            
            return {
                'success': True,
                'message': f'Templated email ({template_type}) sent successfully via {provider}',
                'provider': provider,
                'template_type': template_type,
                'to_email': email_data['to_email'],
                'subject': email_data['subject'],
                'message_id': response['MessageId']
            }
            
        except Exception as e:
            logger.error(f"SES templated email error: {e}")
            return {'success': False, 'error': f'SES sending failed: {str(e)}'}