#!/usr/bin/env python3
"""
Templated Email Service - Extracted from Working Implementation
Professional email templates for common use cases
Ready for integration into IVR systems
"""

import json
import boto3
import logging
import base64
import io
import os
from typing import Dict, Any
from botocore.exceptions import ClientError

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Try to import reportlab for PDF generation
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logger.warning("ReportLab not available - PDF generation disabled")

class TemplatedEmailService:
    """Production-ready Templated Email Service using AWS SES"""
    
    def __init__(self):
        """Initialize SES client and configuration"""
        self.ses_client = boto3.client('ses', region_name=os.getenv('AWS_REGION', 'us-west-2'))
        self.default_sender = os.getenv('SES_SENDER_EMAIL', 'support@f5universe.com')
        self.default_brand_logo = "https://k43feq9x55.execute-api.us-west-2.amazonaws.com/dev/logo.png"
        self.default_bg_color = "#f8f9fa"
        
    def create_templates(self) -> Dict[str, Any]:
        """Create all SES email templates"""
        try:
            templates_created = 0
            templates_failed = 0
            results = []
            
            # Template definitions
            templates = [
                {
                    'name': 'AccountSignupTemplate',
                    'subject': 'Welcome! Please verify your account',
                    'html_content': self._get_signup_template_html(),
                    'text_content': self._get_signup_template_text()
                },
                {
                    'name': 'ForgotPasswordTemplate', 
                    'subject': 'Reset your password',
                    'html_content': self._get_forgot_password_template_html(),
                    'text_content': self._get_forgot_password_template_text()
                },
                {
                    'name': 'OTPTemplate',
                    'subject': 'Your verification code',
                    'html_content': self._get_otp_template_html(),
                    'text_content': self._get_otp_template_text()
                },
                {
                    'name': 'WelcomePackTemplate',
                    'subject': 'Welcome to {{company_name}}!',
                    'html_content': self._get_welcome_pack_template_html(),
                    'text_content': self._get_welcome_pack_template_text()
                },
                {
                    'name': 'OrderConfirmationTemplate',
                    'subject': 'Order Confirmation - {{order_number}}',
                    'html_content': self._get_order_confirmation_template_html(),
                    'text_content': self._get_order_confirmation_template_text()
                }
            ]
            
            # Create each template
            for template in templates:
                try:
                    self.ses_client.create_template(
                        Template={
                            'TemplateName': template['name'],
                            'SubjectPart': template['subject'],
                            'HtmlPart': template['html_content'],
                            'TextPart': template['text_content']
                        }
                    )
                    
                    results.append(f"✅ {template['name']} created successfully")
                    templates_created += 1
                    
                except ClientError as e:
                    if e.response['Error']['Code'] == 'AlreadyExistsException':
                        # Update existing template
                        try:
                            self.ses_client.update_template(
                                Template={
                                    'TemplateName': template['name'],
                                    'SubjectPart': template['subject'],
                                    'HtmlPart': template['html_content'],
                                    'TextPart': template['text_content']
                                }
                            )
                            results.append(f"🔄 {template['name']} updated successfully")
                            templates_created += 1
                        except Exception as update_error:
                            results.append(f"❌ {template['name']} update failed: {str(update_error)}")
                            templates_failed += 1
                    else:
                        results.append(f"❌ {template['name']} creation failed: {str(e)}")
                        templates_failed += 1
                        
                except Exception as e:
                    results.append(f"❌ {template['name']} failed: {str(e)}")
                    templates_failed += 1
            
            return {
                'success': templates_created > 0,
                'message': f'Template creation completed: {templates_created} created/updated, {templates_failed} failed',
                'templates_created': templates_created,
                'templates_failed': templates_failed,
                'total_templates': len(templates),
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Template creation error: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_account_signup_email(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send account signup email using SES template"""
        try:
            to_email = template_data.get('to_email')
            template_vars = template_data.get('template_data', {})
            
            if not to_email:
                return {'success': False, 'error': 'Missing required field: to_email'}
            
            # Default template variables
            template_variables = {
                'user_name': template_vars.get('user_name', 'User'),
                'verification_link': template_vars.get('verification_link', 'https://yourapp.com/verify'),
                'support_email': template_vars.get('support_email', self.default_sender),
                'brand_logo': template_vars.get('brand_logo', self.default_brand_logo),
                'bg_color': template_vars.get('bg_color', self.default_bg_color)
            }
            
            # Send templated email
            response = self.ses_client.send_templated_email(
                Source=self.default_sender,
                Destination={'ToAddresses': [to_email]},
                Template='AccountSignupTemplate',
                TemplateData=json.dumps(template_variables)
            )
            
            return {
                'success': True,
                'message': f'Account signup email sent to {to_email}',
                'message_id': response['MessageId'],
                'template': 'AccountSignupTemplate',
                'destination': to_email
            }
            
        except Exception as e:
            logger.error(f"Account signup email error: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_forgot_password_email(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send forgot password email using SES template"""
        try:
            to_email = template_data.get('to_email')
            template_vars = template_data.get('template_data', {})
            
            if not to_email:
                return {'success': False, 'error': 'Missing required field: to_email'}
            
            # Default template variables
            template_variables = {
                'user_name': template_vars.get('user_name', 'User'),
                'reset_link': template_vars.get('reset_link', 'https://yourapp.com/reset'),
                'expiry_time': template_vars.get('expiry_time', '24 hours'),
                'support_email': template_vars.get('support_email', self.default_sender),
                'brand_logo': template_vars.get('brand_logo', self.default_brand_logo),
                'bg_color': template_vars.get('bg_color', self.default_bg_color)
            }
            
            # Send templated email
            response = self.ses_client.send_templated_email(
                Source=self.default_sender,
                Destination={'ToAddresses': [to_email]},
                Template='ForgotPasswordTemplate',
                TemplateData=json.dumps(template_variables)
            )
            
            return {
                'success': True,
                'message': f'Forgot password email sent to {to_email}',
                'message_id': response['MessageId'],
                'template': 'ForgotPasswordTemplate',
                'destination': to_email
            }
            
        except Exception as e:
            logger.error(f"Forgot password email error: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_otp_email(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send OTP verification email using SES template"""
        try:
            to_email = template_data.get('to_email')
            template_vars = template_data.get('template_data', {})
            
            if not to_email:
                return {'success': False, 'error': 'Missing required field: to_email'}
            
            # Default template variables
            template_variables = {
                'user_name': template_vars.get('user_name', 'User'),
                'otp_code': str(template_vars.get('otp_code', '123456')),
                'expiry_minutes': template_vars.get('expiry_minutes', '10'),
                'support_email': template_vars.get('support_email', self.default_sender),
                'brand_logo': template_vars.get('brand_logo', self.default_brand_logo),
                'bg_color': template_vars.get('bg_color', self.default_bg_color)
            }
            
            # Send templated email
            response = self.ses_client.send_templated_email(
                Source=self.default_sender,
                Destination={'ToAddresses': [to_email]},
                Template='OTPTemplate',
                TemplateData=json.dumps(template_variables)
            )
            
            return {
                'success': True,
                'message': f'OTP email sent to {to_email}',
                'message_id': response['MessageId'],
                'template': 'OTPTemplate',
                'destination': to_email
            }
            
        except Exception as e:
            logger.error(f"OTP email error: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_welcome_pack_email(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send welcome pack email with PDF attachment using SES template"""
        try:
            to_email = template_data.get('to_email')
            template_vars = template_data.get('template_data', {})
            
            if not to_email:
                return {'success': False, 'error': 'Missing required field: to_email'}
            
            # Default template variables
            template_variables = {
                'user_name': template_vars.get('user_name', 'User'),
                'company_name': template_vars.get('company_name', 'Our Company'),
                'login_url': template_vars.get('login_url', 'https://yourapp.com/login'),
                'support_email': template_vars.get('support_email', self.default_sender),
                'brand_logo': template_vars.get('brand_logo', self.default_brand_logo),
                'bg_color': template_vars.get('bg_color', self.default_bg_color)
            }
            
            # Send templated email with PDF attachment
            if PDF_AVAILABLE:
                return self._send_welcome_pack_with_pdf(to_email, template_variables)
            else:
                # Send without PDF if ReportLab not available
                response = self.ses_client.send_templated_email(
                    Source=self.default_sender,
                    Destination={'ToAddresses': [to_email]},
                    Template='WelcomePackTemplate',
                    TemplateData=json.dumps(template_variables)
                )
                
                return {
                    'success': True,
                    'message': f'Welcome pack email sent to {to_email} (PDF generation unavailable)',
                    'message_id': response['MessageId'],
                    'template': 'WelcomePackTemplate',
                    'destination': to_email
                }
            
        except Exception as e:
            logger.error(f"Welcome pack email error: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_order_confirmation_email(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send order confirmation email using SES template"""
        try:
            to_email = template_data.get('to_email')
            template_vars = template_data.get('template_data', {})
            
            if not to_email:
                return {'success': False, 'error': 'Missing required field: to_email'}
            
            # Default template variables
            template_variables = {
                'customer_name': template_vars.get('customer_name', 'Customer'),
                'order_number': template_vars.get('order_number', 'ORD-12345'),
                'order_date': template_vars.get('order_date', '2024-01-01'),
                'total_amount': template_vars.get('total_amount', '$0.00'),
                'delivery_address': template_vars.get('delivery_address', 'Not specified'),
                'tracking_url': template_vars.get('tracking_url', 'https://yourapp.com/track'),
                'support_email': template_vars.get('support_email', self.default_sender),
                'brand_logo': template_vars.get('brand_logo', self.default_brand_logo),
                'bg_color': template_vars.get('bg_color', self.default_bg_color)
            }
            
            # Send templated email
            response = self.ses_client.send_templated_email(
                Source=self.default_sender,
                Destination={'ToAddresses': [to_email]},
                Template='OrderConfirmationTemplate',
                TemplateData=json.dumps(template_variables)
            )
            
            return {
                'success': True,
                'message': f'Order confirmation email sent to {to_email}',
                'message_id': response['MessageId'],
                'template': 'OrderConfirmationTemplate',
                'destination': to_email
            }
            
        except Exception as e:
            logger.error(f"Order confirmation email error: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get templated email service status"""
        try:
            # Test SES connectivity
            response = self.ses_client.get_send_quota()
            
            # List existing templates
            templates_response = self.ses_client.list_templates()
            template_names = [t['Name'] for t in templates_response.get('TemplatesMetadata', [])]
            
            return {
                'success': True,
                'status': 'operational',
                'service': 'templated-email',
                'ses_quota': {
                    'max_24_hour': response['Max24HourSend'],
                    'max_per_second': response['MaxSendRate'],
                    'sent_last_24_hours': response['SentLast24Hours']
                },
                'templates': {
                    'available': template_names,
                    'count': len(template_names),
                    'pdf_generation': 'Available' if PDF_AVAILABLE else 'Unavailable'
                },
                'supported_templates': [
                    'AccountSignupTemplate',
                    'ForgotPasswordTemplate', 
                    'OTPTemplate',
                    'WelcomePackTemplate',
                    'OrderConfirmationTemplate'
                ]
            }
            
        except Exception as e:
            logger.error(f"Templated email status error: {e}")
            return {
                'success': False,
                'status': 'error',
                'error': str(e)
            }
    
    # Template HTML content methods
    def _get_signup_template_html(self) -> str:
        """Get HTML content for account signup template"""
        return """
        <html>
        <body style="font-family: Arial, sans-serif; background-color: {{bg_color}}; margin: 0; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px;">
                <img src="{{brand_logo}}" alt="Logo" style="height: 50px; margin-bottom: 20px;">
                <h2 style="color: #333;">Welcome {{user_name}}!</h2>
                <p>Thank you for signing up. Please verify your account by clicking the link below:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{{verification_link}}" style="background: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px;">Verify Account</a>
                </div>
                <p>If you didn't create this account, please ignore this email.</p>
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                <p style="font-size: 12px; color: #666;">
                    Need help? Contact us at <a href="mailto:{{support_email}}">{{support_email}}</a>
                </p>
            </div>
        </body>
        </html>
        """
    
    def _get_signup_template_text(self) -> str:
        """Get text content for account signup template"""
        return """
        Welcome {{user_name}}!
        
        Thank you for signing up. Please verify your account by visiting:
        {{verification_link}}
        
        If you didn't create this account, please ignore this email.
        
        Need help? Contact us at {{support_email}}
        """
    
    def _get_forgot_password_template_html(self) -> str:
        """Get HTML content for forgot password template"""
        return """
        <html>
        <body style="font-family: Arial, sans-serif; background-color: {{bg_color}}; margin: 0; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px;">
                <img src="{{brand_logo}}" alt="Logo" style="height: 50px; margin-bottom: 20px;">
                <h2 style="color: #333;">Reset Your Password</h2>
                <p>Hello {{user_name}},</p>
                <p>We received a request to reset your password. Click the link below to create a new password:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{{reset_link}}" style="background: #dc3545; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px;">Reset Password</a>
                </div>
                <p><strong>This link will expire in {{expiry_time}}.</strong></p>
                <p>If you didn't request this reset, please ignore this email.</p>
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                <p style="font-size: 12px; color: #666;">
                    Need help? Contact us at <a href="mailto:{{support_email}}">{{support_email}}</a>
                </p>
            </div>
        </body>
        </html>
        """
    
    def _get_forgot_password_template_text(self) -> str:
        """Get text content for forgot password template"""
        return """
        Reset Your Password
        
        Hello {{user_name}},
        
        We received a request to reset your password. Visit this link to create a new password:
        {{reset_link}}
        
        This link will expire in {{expiry_time}}.
        
        If you didn't request this reset, please ignore this email.
        
        Need help? Contact us at {{support_email}}
        """
    
    def _get_otp_template_html(self) -> str:
        """Get HTML content for OTP template"""
        return """
        <html>
        <body style="font-family: Arial, sans-serif; background-color: {{bg_color}}; margin: 0; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px;">
                <img src="{{brand_logo}}" alt="Logo" style="height: 50px; margin-bottom: 20px;">
                <h2 style="color: #333;">Your Verification Code</h2>
                <p>Hello {{user_name}},</p>
                <p>Your verification code is:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <div style="background: #f8f9fa; border: 2px solid #007bff; padding: 20px; border-radius: 10px; display: inline-block;">
                        <span style="font-size: 32px; font-weight: bold; color: #007bff; letter-spacing: 5px;">{{otp_code}}</span>
                    </div>
                </div>
                <p><strong>This code will expire in {{expiry_minutes}} minutes.</strong></p>
                <p>If you didn't request this code, please ignore this email.</p>
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                <p style="font-size: 12px; color: #666;">
                    Need help? Contact us at <a href="mailto:{{support_email}}">{{support_email}}</a>
                </p>
            </div>
        </body>
        </html>
        """
    
    def _get_otp_template_text(self) -> str:
        """Get text content for OTP template"""
        return """
        Your Verification Code
        
        Hello {{user_name}},
        
        Your verification code is: {{otp_code}}
        
        This code will expire in {{expiry_minutes}} minutes.
        
        If you didn't request this code, please ignore this email.
        
        Need help? Contact us at {{support_email}}
        """
    
    def _get_welcome_pack_template_html(self) -> str:
        """Get HTML content for welcome pack template"""
        return """
        <html>
        <body style="font-family: Arial, sans-serif; background-color: {{bg_color}}; margin: 0; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px;">
                <img src="{{brand_logo}}" alt="Logo" style="height: 50px; margin-bottom: 20px;">
                <h2 style="color: #333;">Welcome to {{company_name}}!</h2>
                <p>Hello {{user_name}},</p>
                <p>Welcome to our community! We're excited to have you on board.</p>
                <p>Your account is now active and ready to use. You can access your dashboard using the link below:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{{login_url}}" style="background: #28a745; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px;">Access Dashboard</a>
                </div>
                <p>We've also attached a welcome guide to help you get started.</p>
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                <p style="font-size: 12px; color: #666;">
                    Need help? Contact us at <a href="mailto:{{support_email}}">{{support_email}}</a>
                </p>
            </div>
        </body>
        </html>
        """
    
    def _get_welcome_pack_template_text(self) -> str:
        """Get text content for welcome pack template"""
        return """
        Welcome to {{company_name}}!
        
        Hello {{user_name}},
        
        Welcome to our community! We're excited to have you on board.
        
        Your account is now active and ready to use. Access your dashboard at:
        {{login_url}}
        
        We've also attached a welcome guide to help you get started.
        
        Need help? Contact us at {{support_email}}
        """
    
    def _get_order_confirmation_template_html(self) -> str:
        """Get HTML content for order confirmation template"""
        return """
        <html>
        <body style="font-family: Arial, sans-serif; background-color: {{bg_color}}; margin: 0; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px;">
                <img src="{{brand_logo}}" alt="Logo" style="height: 50px; margin-bottom: 20px;">
                <h2 style="color: #333;">Order Confirmed!</h2>
                <p>Hello {{customer_name}},</p>
                <p>Thank you for your order. Here are the details:</p>
                <div style="background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <p><strong>Order Number:</strong> {{order_number}}</p>
                    <p><strong>Order Date:</strong> {{order_date}}</p>
                    <p><strong>Total Amount:</strong> {{total_amount}}</p>
                    <p><strong>Delivery Address:</strong> {{delivery_address}}</p>
                </div>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{{tracking_url}}" style="background: #ffc107; color: #212529; padding: 12px 24px; text-decoration: none; border-radius: 5px;">Track Your Order</a>
                </div>
                <p>We'll send you updates as your order is processed and shipped.</p>
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                <p style="font-size: 12px; color: #666;">
                    Need help? Contact us at <a href="mailto:{{support_email}}">{{support_email}}</a>
                </p>
            </div>
        </body>
        </html>
        """
    
    def _get_order_confirmation_template_text(self) -> str:
        """Get text content for order confirmation template"""
        return """
        Order Confirmed!
        
        Hello {{customer_name}},
        
        Thank you for your order. Here are the details:
        
        Order Number: {{order_number}}
        Order Date: {{order_date}}
        Total Amount: {{total_amount}}
        Delivery Address: {{delivery_address}}
        
        Track your order at: {{tracking_url}}
        
        We'll send you updates as your order is processed and shipped.
        
        Need help? Contact us at {{support_email}}
        """
    
    def _send_welcome_pack_with_pdf(self, to_email: str, template_variables: Dict[str, Any]) -> Dict[str, Any]:
        """Send welcome pack email with PDF attachment using SES SendRawEmail"""
        try:
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText
            from email.mime.application import MIMEApplication
            
            # Create welcome PDF
            pdf_content = self._create_welcome_pdf(
                template_variables['user_name'],
                template_variables['company_name']
            )
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = self.default_sender
            msg['To'] = to_email
            msg['Subject'] = f"Welcome to {template_variables['company_name']}!"
            
            # Create HTML body from template
            html_body = self._get_welcome_pack_template_html()
            for key, value in template_variables.items():
                html_body = html_body.replace('{{' + key + '}}', str(value))
            
            msg.attach(MIMEText(html_body, 'html'))
            
            # Attach PDF
            pdf_attachment = MIMEApplication(pdf_content)
            pdf_attachment.add_header('Content-Disposition', 'attachment', filename='welcome_guide.pdf')
            msg.attach(pdf_attachment)
            
            # Send via SES
            response = self.ses_client.send_raw_email(
                Source=self.default_sender,
                Destinations=[to_email],
                RawMessage={'Data': msg.as_string()}
            )
            
            return {
                'success': True,
                'message': f'Welcome pack email with PDF sent to {to_email}',
                'message_id': response['MessageId'],
                'template': 'WelcomePackTemplate',
                'destination': to_email,
                'pdf_attached': True
            }
            
        except Exception as e:
            logger.error(f"Welcome pack with PDF error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _create_welcome_pdf(self, user_name: str, company_name: str) -> bytes:
        """Create a welcome PDF guide"""
        try:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            
            # Get styles
            styles = getSampleStyleSheet()
            
            # Content
            content = []
            
            # Title
            title = Paragraph(f"Welcome to {company_name}!", styles['Title'])
            content.append(title)
            content.append(Spacer(1, 0.2*inch))
            
            # Greeting
            greeting = Paragraph(f"Hello {user_name},", styles['Normal'])
            content.append(greeting)
            content.append(Spacer(1, 0.1*inch))
            
            # Welcome message
            welcome_text = """
            Thank you for joining our community! This guide will help you get started with our services.
            
            <b>Getting Started:</b><br/>
            1. Log into your account dashboard<br/>
            2. Complete your profile information<br/>
            3. Explore available features<br/>
            4. Contact support if you need help<br/>
            
            <b>Support:</b><br/>
            Our support team is available 24/7 to assist you with any questions or concerns.
            
            Welcome aboard!
            """
            
            welcome_para = Paragraph(welcome_text, styles['Normal'])
            content.append(welcome_para)
            
            # Build PDF
            doc.build(content)
            
            # Get PDF content
            buffer.seek(0)
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"PDF creation error: {e}")
            # Return empty PDF content if creation fails
            return b"PDF generation failed"