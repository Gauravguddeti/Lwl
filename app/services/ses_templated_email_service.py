"""
AWS SES Templated Email Service for AI Telecaller System
Supports 5 templated email types with customizable variables and PDF attachments
"""

import boto3
import os
import logging
import json
import base64
from botocore.exceptions import ClientError
from typing import Dict, Any, Optional
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from reportlab.lib.pagesizes import letter
from reportlab.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import io

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SESTemplatedEmailService:
    """
    AWS SES Templated Email Service supporting:
    1. Account Signup Email
    2. Forgot Password Email  
    3. OTP Email
    4. Order Confirmation Email
    5. Welcome Pack Email (with PDF attachment)
    """
    
    def __init__(self):
        """Initialize SES client and configuration"""
        self.aws_region = os.getenv('AWS_REGION', 'us-west-2')
        self.ses_client = boto3.client('ses', region_name=self.aws_region)
        self.default_sender = os.getenv('SES_SENDER_EMAIL', 'support@f5universe.com')
        
        # Default brand settings
        self.default_brand_logo = "https://app.chatmaven.ai/assets/logo.png"
        self.default_bg_color = "#f8f9fa"
        
        logger.info("SESTemplatedEmailService initialized")

    def create_ses_templates(self) -> Dict[str, Any]:
        """
        Create all 5 SES email templates
        
        Returns:
            Dict with creation status for each template
        """
        results = {}
        
        # Template configurations
        templates = {
            'AccountSignupTemplate': self._get_signup_template(),
            'ForgotPasswordTemplate': self._get_forgot_password_template(),
            'OTPTemplate': self._get_otp_template(),
            'OrderConfirmationTemplate': self._get_order_confirmation_template()
        }
        
        for template_name, template_config in templates.items():
            try:
                # Delete template if it exists
                try:
                    self.ses_client.delete_template(TemplateName=template_name)
                    logger.info(f"Deleted existing template: {template_name}")
                except ClientError as e:
                    if e.response['Error']['Code'] != 'TemplateDoesNotExist':
                        logger.warning(f"Error deleting template {template_name}: {e}")
                
                # Create new template
                self.ses_client.create_template(Template=template_config)
                results[template_name] = {'success': True, 'message': 'Template created successfully'}
                logger.info(f"Created SES template: {template_name}")
                
            except Exception as e:
                results[template_name] = {'success': False, 'error': str(e)}
                logger.error(f"Error creating template {template_name}: {e}")
        
        return results

    def send_account_signup_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send account signup email using SES template
        
        Args:
            email_data: Dict containing recipient, name, signupLink, brandLogo, bgColor
            
        Returns:
            Dict with success status and message
        """
        try:
            # Extract parameters
            to_email = email_data.get('to_email')
            name = email_data.get('name', 'User')
            signup_link = email_data.get('signupLink', 'https://app.chatmaven.ai/account/register')
            brand_logo = email_data.get('brandLogo', self.default_brand_logo)
            bg_color = email_data.get('bgColor', self.default_bg_color)
            sender_email = email_data.get('sender_email', self.default_sender)
            
            if not to_email:
                return {'success': False, 'error': 'to_email is required'}
            
            # Template data
            template_data = {
                'name': name,
                'signupLink': signup_link,
                'brandLogo': brand_logo,
                'bgColor': bg_color
            }
            
            # Send templated email
            response = self.ses_client.send_templated_email(
                Source=sender_email,
                Destination={'ToAddresses': [to_email]},
                Template='AccountSignupTemplate',
                TemplateData=json.dumps(template_data)
            )
            
            return {
                'success': True,
                'message': f'Account signup email sent to {to_email}',
                'message_id': response['MessageId'],
                'template': 'AccountSignupTemplate'
            }
            
        except Exception as e:
            logger.error(f"Error sending signup email: {e}")
            return {'success': False, 'error': str(e)}

    def send_forgot_password_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send forgot password email using SES template
        
        Args:
            email_data: Dict containing recipient, name, resetLink, brandLogo, bgColor
            
        Returns:
            Dict with success status and message
        """
        try:
            # Extract parameters
            to_email = email_data.get('to_email')
            name = email_data.get('name', 'User')
            reset_link = email_data.get('resetLink', 'https://app.chatmaven.ai/account/forgotpassword')
            brand_logo = email_data.get('brandLogo', self.default_brand_logo)
            bg_color = email_data.get('bgColor', self.default_bg_color)
            sender_email = email_data.get('sender_email', self.default_sender)
            
            if not to_email:
                return {'success': False, 'error': 'to_email is required'}
            
            # Template data
            template_data = {
                'name': name,
                'resetLink': reset_link,
                'brandLogo': brand_logo,
                'bgColor': bg_color
            }
            
            # Send templated email
            response = self.ses_client.send_templated_email(
                Source=sender_email,
                Destination={'ToAddresses': [to_email]},
                Template='ForgotPasswordTemplate',
                TemplateData=json.dumps(template_data)
            )
            
            return {
                'success': True,
                'message': f'Password reset email sent to {to_email}',
                'message_id': response['MessageId'],
                'template': 'ForgotPasswordTemplate'
            }
            
        except Exception as e:
            logger.error(f"Error sending forgot password email: {e}")
            return {'success': False, 'error': str(e)}

    def send_otp_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send OTP email using SES template
        
        Args:
            email_data: Dict containing recipient, name, otp, brandLogo, bgColor
            
        Returns:
            Dict with success status and message
        """
        try:
            # Extract parameters
            to_email = email_data.get('to_email')
            name = email_data.get('name', 'User')
            otp = email_data.get('otp')
            brand_logo = email_data.get('brandLogo', self.default_brand_logo)
            bg_color = email_data.get('bgColor', self.default_bg_color)
            sender_email = email_data.get('sender_email', self.default_sender)
            
            if not to_email or not otp:
                return {'success': False, 'error': 'to_email and otp are required'}
            
            # Template data
            template_data = {
                'name': name,
                'otp': str(otp),
                'brandLogo': brand_logo,
                'bgColor': bg_color
            }
            
            # Send templated email
            response = self.ses_client.send_templated_email(
                Source=sender_email,
                Destination={'ToAddresses': [to_email]},
                Template='OTPTemplate',
                TemplateData=json.dumps(template_data)
            )
            
            return {
                'success': True,
                'message': f'OTP email sent to {to_email}',
                'message_id': response['MessageId'],
                'template': 'OTPTemplate'
            }
            
        except Exception as e:
            logger.error(f"Error sending OTP email: {e}")
            return {'success': False, 'error': str(e)}

    def send_order_confirmation_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send order confirmation email using SES template
        
        Args:
            email_data: Dict containing recipient, name, orderId, orderDate, brandLogo, bgColor
            
        Returns:
            Dict with success status and message
        """
        try:
            # Extract parameters
            to_email = email_data.get('to_email')
            name = email_data.get('name', 'User')
            order_id = email_data.get('orderId')
            order_date = email_data.get('orderDate')
            brand_logo = email_data.get('brandLogo', self.default_brand_logo)
            bg_color = email_data.get('bgColor', self.default_bg_color)
            sender_email = email_data.get('sender_email', self.default_sender)
            
            if not to_email or not order_id:
                return {'success': False, 'error': 'to_email and orderId are required'}
            
            if not order_date:
                from datetime import datetime
                order_date = datetime.now().strftime('%Y-%m-%d')
            
            # Template data
            template_data = {
                'name': name,
                'orderId': str(order_id),
                'orderDate': order_date,
                'brandLogo': brand_logo,
                'bgColor': bg_color
            }
            
            # Send templated email
            response = self.ses_client.send_templated_email(
                Source=sender_email,
                Destination={'ToAddresses': [to_email]},
                Template='OrderConfirmationTemplate',
                TemplateData=json.dumps(template_data)
            )
            
            return {
                'success': True,
                'message': f'Order confirmation email sent to {to_email}',
                'message_id': response['MessageId'],
                'template': 'OrderConfirmationTemplate'
            }
            
        except Exception as e:
            logger.error(f"Error sending order confirmation email: {e}")
            return {'success': False, 'error': str(e)}

    def send_welcome_pack_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send welcome pack email with PDF attachment using SES SendRawEmail
        
        Args:
            email_data: Dict containing recipient, name, signupLink, loginLink, brandLogo, bgColor
            
        Returns:
            Dict with success status and message
        """
        try:
            # Extract parameters
            to_email = email_data.get('to_email')
            name = email_data.get('name', 'User')
            signup_link = email_data.get('signupLink', 'https://app.chatmaven.ai/account/register')
            login_link = email_data.get('loginLink', 'https://app.chatmaven.ai/account?ReturnUrl=%2F')
            brand_logo = email_data.get('brandLogo', self.default_brand_logo)
            bg_color = email_data.get('bgColor', self.default_bg_color)
            sender_email = email_data.get('sender_email', self.default_sender)
            
            if not to_email:
                return {'success': False, 'error': 'to_email is required'}
            
            # Generate welcome pack PDF
            pdf_buffer = self._generate_welcome_pack_pdf(name)
            
            # Create multipart email
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = to_email
            msg['Subject'] = f"Welcome to ChatMaven, {name}! 🎉"
            
            # HTML body for welcome pack email
            html_body = self._get_welcome_pack_html(name, signup_link, login_link, brand_logo, bg_color)
            msg.attach(MIMEText(html_body, 'html'))
            
            # Attach PDF
            pdf_attachment = MIMEApplication(pdf_buffer.getvalue())
            pdf_attachment.add_header('Content-Disposition', 'attachment', filename='WelcomePack.pdf')
            msg.attach(pdf_attachment)
            
            # Send raw email
            response = self.ses_client.send_raw_email(
                Source=sender_email,
                Destinations=[to_email],
                RawMessage={'Data': msg.as_string()}
            )
            
            return {
                'success': True,
                'message': f'Welcome pack email with PDF sent to {to_email}',
                'message_id': response['MessageId'],
                'template': 'WelcomePackWithPDF',
                'attachment': 'WelcomePack.pdf'
            }
            
        except Exception as e:
            logger.error(f"Error sending welcome pack email: {e}")
            return {'success': False, 'error': str(e)}

    def _generate_welcome_pack_pdf(self, name: str) -> io.BytesIO:
        """
        Generate a welcome pack PDF with introductory content
        
        Args:
            name: User's name
            
        Returns:
            BytesIO buffer containing PDF data
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor('#2c3e50'),
            alignment=1  # Center
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.HexColor('#34495e')
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=12,
            textColor=colors.HexColor('#2c3e50')
        )
        
        # Content
        story.append(Paragraph(f"Welcome to ChatMaven, {name}!", title_style))
        story.append(Spacer(1, 20))
        
        story.append(Paragraph("🎉 Getting Started Guide", heading_style))
        story.append(Paragraph(
            "Thank you for joining ChatMaven! This welcome pack will help you get started with our AI-powered conversation platform.",
            body_style
        ))
        story.append(Spacer(1, 15))
        
        story.append(Paragraph("🚀 Key Features", heading_style))
        features = [
            "• AI-Powered Conversations: Advanced AI that understands context and provides intelligent responses",
            "• Real-time Communication: Instant messaging with AI assistants and team members",
            "• Customizable Workflows: Create personalized conversation flows for your specific needs",
            "• Analytics Dashboard: Track conversation metrics and performance insights",
            "• Integration Hub: Connect with your favorite tools and platforms"
        ]
        for feature in features:
            story.append(Paragraph(feature, body_style))
        story.append(Spacer(1, 15))
        
        story.append(Paragraph("📚 How to Get Started", heading_style))
        steps = [
            "1. Complete your account setup by verifying your email address",
            "2. Explore the dashboard to familiarize yourself with the interface",
            "3. Start your first conversation using our guided tutorial",
            "4. Customize your AI assistant settings to match your preferences",
            "5. Invite team members and set up collaborative workspaces"
        ]
        for step in steps:
            story.append(Paragraph(step, body_style))
        story.append(Spacer(1, 15))
        
        story.append(Paragraph("💡 Pro Tips", heading_style))
        tips = [
            "• Use specific prompts for better AI responses",
            "• Set up conversation templates for recurring scenarios",
            "• Leverage our analytics to optimize your communication strategy",
            "• Join our community forum to connect with other users"
        ]
        for tip in tips:
            story.append(Paragraph(tip, body_style))
        story.append(Spacer(1, 15))
        
        story.append(Paragraph("📞 Need Help?", heading_style))
        story.append(Paragraph(
            "Our support team is here to help! Contact us at support@chatmaven.ai or visit our help center for tutorials and documentation.",
            body_style
        ))
        story.append(Spacer(1, 20))
        
        story.append(Paragraph("Welcome aboard! 🎊", title_style))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer

    def _get_welcome_pack_html(self, name: str, signup_link: str, login_link: str, brand_logo: str, bg_color: str) -> str:
        """Generate HTML content for welcome pack email"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Welcome to ChatMaven</title>
        </head>
        <body style="margin: 0; padding: 0; background-color: {bg_color}; font-family: Arial, sans-serif;">
            <table role="presentation" style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 40px 20px; text-align: center;">
                        <table role="presentation" style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                            <tr>
                                <td style="padding: 40px; text-align: center;">
                                    <img src="{brand_logo}" alt="ChatMaven Logo" style="max-width: 200px; height: auto; margin-bottom: 30px;">
                                    <h1 style="color: #2c3e50; font-size: 28px; margin: 0 0 20px 0;">Welcome to ChatMaven, {name}! 🎉</h1>
                                    <p style="color: #34495e; font-size: 16px; line-height: 1.6; margin: 0 0 30px 0;">
                                        We're thrilled to have you join our AI-powered conversation platform! Your journey to smarter communication starts now.
                                    </p>
                                    <p style="color: #34495e; font-size: 16px; line-height: 1.6; margin: 0 0 30px 0;">
                                        We've attached a comprehensive welcome pack PDF with everything you need to get started, including tutorials, tips, and best practices.
                                    </p>
                                    <table role="presentation" style="margin: 0 auto;">
                                        <tr>
                                            <td style="padding: 0 10px;">
                                                <a href="{signup_link}" style="display: inline-block; padding: 15px 30px; background-color: #3498db; color: #ffffff; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 16px;">Complete Setup</a>
                                            </td>
                                            <td style="padding: 0 10px;">
                                                <a href="{login_link}" style="display: inline-block; padding: 15px 30px; background-color: #2ecc71; color: #ffffff; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 16px;">Sign In</a>
                                            </td>
                                        </tr>
                                    </table>
                                    <p style="color: #7f8c8d; font-size: 14px; line-height: 1.6; margin: 30px 0 0 0;">
                                        📎 Don't forget to check the attached WelcomePack.pdf for detailed getting started instructions!
                                    </p>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 20px; background-color: #ecf0f1; border-radius: 0 0 8px 8px; text-align: center;">
                                    <p style="color: #7f8c8d; font-size: 12px; margin: 0;">
                                        © 2025 ChatMaven. All rights reserved. | Need help? Contact us at support@chatmaven.ai
                                    </p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """

    def _get_signup_template(self) -> Dict[str, Any]:
        """Get account signup email template configuration"""
        return {
            'TemplateName': 'AccountSignupTemplate',
            'Subject': 'Welcome to ChatMaven - Complete Your Registration! 🚀',
            'HtmlPart': '''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Welcome to ChatMaven</title>
            </head>
            <body style="margin: 0; padding: 0; background-color: {{bgColor}}; font-family: Arial, sans-serif;">
                <table role="presentation" style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 40px 20px; text-align: center;">
                            <table role="presentation" style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                                <tr>
                                    <td style="padding: 40px; text-align: center;">
                                        <img src="{{brandLogo}}" alt="ChatMaven Logo" style="max-width: 200px; height: auto; margin-bottom: 30px;">
                                        <h1 style="color: #2c3e50; font-size: 28px; margin: 0 0 20px 0;">Welcome {{name}}! 🎉</h1>
                                        <p style="color: #34495e; font-size: 16px; line-height: 1.6; margin: 0 0 30px 0;">
                                            Thank you for choosing ChatMaven! We're excited to help you transform your communication with AI-powered conversations.
                                        </p>
                                        <p style="color: #34495e; font-size: 16px; line-height: 1.6; margin: 0 0 30px 0;">
                                            Click the button below to complete your account registration and start exploring our platform.
                                        </p>
                                        <a href="{{signupLink}}" style="display: inline-block; padding: 15px 40px; background-color: #3498db; color: #ffffff; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 18px; margin: 10px 0;">Complete Registration</a>
                                        <p style="color: #7f8c8d; font-size: 14px; line-height: 1.6; margin: 30px 0 0 0;">
                                            If the button doesn't work, copy and paste this link into your browser:<br>
                                            <a href="{{signupLink}}" style="color: #3498db;">{{signupLink}}</a>
                                        </p>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 20px; background-color: #ecf0f1; border-radius: 0 0 8px 8px; text-align: center;">
                                        <p style="color: #7f8c8d; font-size: 12px; margin: 0;">
                                            © 2025 ChatMaven. All rights reserved.
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </body>
            </html>
            ''',
            'TextPart': '''
            Welcome to ChatMaven, {{name}}!
            
            Thank you for choosing ChatMaven! We're excited to help you transform your communication with AI-powered conversations.
            
            Complete your registration by visiting: {{signupLink}}
            
            © 2025 ChatMaven. All rights reserved.
            '''
        }

    def _get_forgot_password_template(self) -> Dict[str, Any]:
        """Get forgot password email template configuration"""
        return {
            'TemplateName': 'ForgotPasswordTemplate',
            'Subject': 'Reset Your ChatMaven Password 🔐',
            'HtmlPart': '''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Reset Your Password</title>
            </head>
            <body style="margin: 0; padding: 0; background-color: {{bgColor}}; font-family: Arial, sans-serif;">
                <table role="presentation" style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 40px 20px; text-align: center;">
                            <table role="presentation" style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                                <tr>
                                    <td style="padding: 40px; text-align: center;">
                                        <img src="{{brandLogo}}" alt="ChatMaven Logo" style="max-width: 200px; height: auto; margin-bottom: 30px;">
                                        <h1 style="color: #2c3e50; font-size: 28px; margin: 0 0 20px 0;">Password Reset Request</h1>
                                        <p style="color: #34495e; font-size: 16px; line-height: 1.6; margin: 0 0 30px 0;">
                                            Hi {{name}},
                                        </p>
                                        <p style="color: #34495e; font-size: 16px; line-height: 1.6; margin: 0 0 30px 0;">
                                            We received a request to reset your ChatMaven account password. Click the button below to create a new password.
                                        </p>
                                        <a href="{{resetLink}}" style="display: inline-block; padding: 15px 40px; background-color: #e74c3c; color: #ffffff; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 18px; margin: 10px 0;">Reset Password</a>
                                        <p style="color: #7f8c8d; font-size: 14px; line-height: 1.6; margin: 30px 0 0 0;">
                                            If you didn't request this password reset, please ignore this email. Your password will remain unchanged.
                                        </p>
                                        <p style="color: #7f8c8d; font-size: 14px; line-height: 1.6; margin: 15px 0 0 0;">
                                            This link will expire in 24 hours for security reasons.
                                        </p>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 20px; background-color: #ecf0f1; border-radius: 0 0 8px 8px; text-align: center;">
                                        <p style="color: #7f8c8d; font-size: 12px; margin: 0;">
                                            © 2025 ChatMaven. All rights reserved.
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </body>
            </html>
            ''',
            'TextPart': '''
            Password Reset Request
            
            Hi {{name}},
            
            We received a request to reset your ChatMaven account password.
            
            Reset your password by visiting: {{resetLink}}
            
            If you didn't request this password reset, please ignore this email.
            This link will expire in 24 hours for security reasons.
            
            © 2025 ChatMaven. All rights reserved.
            '''
        }

    def _get_otp_template(self) -> Dict[str, Any]:
        """Get OTP email template configuration"""
        return {
            'TemplateName': 'OTPTemplate',
            'Subject': 'Your ChatMaven Verification Code 🔢',
            'HtmlPart': '''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Verification Code</title>
            </head>
            <body style="margin: 0; padding: 0; background-color: {{bgColor}}; font-family: Arial, sans-serif;">
                <table role="presentation" style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 40px 20px; text-align: center;">
                            <table role="presentation" style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                                <tr>
                                    <td style="padding: 40px; text-align: center;">
                                        <img src="{{brandLogo}}" alt="ChatMaven Logo" style="max-width: 200px; height: auto; margin-bottom: 30px;">
                                        <h1 style="color: #2c3e50; font-size: 28px; margin: 0 0 20px 0;">Verification Code</h1>
                                        <p style="color: #34495e; font-size: 16px; line-height: 1.6; margin: 0 0 30px 0;">
                                            Hi {{name}},
                                        </p>
                                        <p style="color: #34495e; font-size: 16px; line-height: 1.6; margin: 0 0 30px 0;">
                                            Use the verification code below to complete your action on ChatMaven:
                                        </p>
                                        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; border: 2px dashed #3498db; margin: 20px 0;">
                                            <h2 style="color: #2c3e50; font-size: 36px; font-family: 'Courier New', monospace; margin: 0; letter-spacing: 8px;">{{otp}}</h2>
                                        </div>
                                        <p style="color: #7f8c8d; font-size: 14px; line-height: 1.6; margin: 30px 0 0 0;">
                                            This code will expire in 10 minutes for security reasons.
                                        </p>
                                        <p style="color: #7f8c8d; font-size: 14px; line-height: 1.6; margin: 15px 0 0 0;">
                                            If you didn't request this code, please ignore this email.
                                        </p>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 20px; background-color: #ecf0f1; border-radius: 0 0 8px 8px; text-align: center;">
                                        <p style="color: #7f8c8d; font-size: 12px; margin: 0;">
                                            © 2025 ChatMaven. All rights reserved.
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </body>
            </html>
            ''',
            'TextPart': '''
            Verification Code
            
            Hi {{name}},
            
            Use this verification code to complete your action on ChatMaven:
            
            {{otp}}
            
            This code will expire in 10 minutes for security reasons.
            If you didn't request this code, please ignore this email.
            
            © 2025 ChatMaven. All rights reserved.
            '''
        }

    def _get_order_confirmation_template(self) -> Dict[str, Any]:
        """Get order confirmation email template configuration"""
        return {
            'TemplateName': 'OrderConfirmationTemplate',
            'Subject': 'Order Confirmation #{{orderId}} - Thank You! 📦',
            'HtmlPart': '''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Order Confirmation</title>
            </head>
            <body style="margin: 0; padding: 0; background-color: {{bgColor}}; font-family: Arial, sans-serif;">
                <table role="presentation" style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 40px 20px; text-align: center;">
                            <table role="presentation" style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                                <tr>
                                    <td style="padding: 40px; text-align: center;">
                                        <img src="{{brandLogo}}" alt="ChatMaven Logo" style="max-width: 200px; height: auto; margin-bottom: 30px;">
                                        <h1 style="color: #2c3e50; font-size: 28px; margin: 0 0 20px 0;">Order Confirmed! 🎉</h1>
                                        <p style="color: #34495e; font-size: 16px; line-height: 1.6; margin: 0 0 30px 0;">
                                            Hi {{name}},
                                        </p>
                                        <p style="color: #34495e; font-size: 16px; line-height: 1.6; margin: 0 0 30px 0;">
                                            Thank you for your order! We've received your payment and your order is being processed.
                                        </p>
                                        <div style="background-color: #f8f9fa; padding: 25px; border-radius: 8px; text-align: left; margin: 20px 0;">
                                            <h3 style="color: #2c3e50; margin: 0 0 15px 0;">Order Details</h3>
                                            <p style="color: #34495e; margin: 5px 0;"><strong>Order ID:</strong> #{{orderId}}</p>
                                            <p style="color: #34495e; margin: 5px 0;"><strong>Order Date:</strong> {{orderDate}}</p>
                                            <p style="color: #34495e; margin: 5px 0;"><strong>Status:</strong> Processing</p>
                                        </div>
                                        <p style="color: #34495e; font-size: 16px; line-height: 1.6; margin: 30px 0;">
                                            You'll receive another email with tracking information once your order ships.
                                        </p>
                                        <p style="color: #7f8c8d; font-size: 14px; line-height: 1.6; margin: 30px 0 0 0;">
                                            Questions about your order? Contact our support team at support@chatmaven.ai
                                        </p>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding: 20px; background-color: #ecf0f1; border-radius: 0 0 8px 8px; text-align: center;">
                                        <p style="color: #7f8c8d; font-size: 12px; margin: 0;">
                                            © 2025 ChatMaven. All rights reserved.
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </body>
            </html>
            ''',
            'TextPart': '''
            Order Confirmed!
            
            Hi {{name}},
            
            Thank you for your order! We've received your payment and your order is being processed.
            
            Order Details:
            - Order ID: #{{orderId}}
            - Order Date: {{orderDate}}
            - Status: Processing
            
            You'll receive another email with tracking information once your order ships.
            
            Questions about your order? Contact our support team at support@chatmaven.ai
            
            © 2025 ChatMaven. All rights reserved.
            '''
        }
