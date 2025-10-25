#!/usr/bin/env python3
"""
Email Service for AI IVR Telecaller System
Handles sending program details via SMTP
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, Any, Optional
import logging

class EmailService:
    """Email service for sending program details to prospects"""
    
    def __init__(self):
        """Initialize email service with SMTP configuration"""
        self.smtp_server = os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('EMAIL_SMTP_PORT', '587'))
        self.email_username = os.getenv('EMAIL_USERNAME')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        self.sender_email = self.email_username
        
        if not self.email_username or not self.email_password:
            logging.warning("Email credentials not configured - email functionality disabled")
            self.enabled = False
        else:
            self.enabled = True
            logging.info("Email service initialized successfully")
    
    def send_program_details(self, recipient_email: str, partner_info: Dict[str, Any], 
                           program_info: Dict[str, Any], event_info: Dict[str, Any]) -> bool:
        """Send detailed program information via email"""
        
        if not self.enabled:
            logging.error("Email service not enabled - missing credentials")
            return False
        
        try:
            # Create email content
            subject = f"Educational Program Details - {program_info.get('name', 'Professional Training')}"
            
            # Generate email body
            email_body = self.generate_email_body(partner_info, program_info, event_info)
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = recipient_email
            msg['Subject'] = subject
            
            # Add body to email
            msg.attach(MIMEText(email_body, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()  # Enable TLS encryption
                server.login(self.email_username, self.email_password)
                
                text = msg.as_string()
                server.sendmail(self.sender_email, recipient_email, text)
                
            logging.info(f"Program details sent successfully to {recipient_email}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to send email to {recipient_email}: {e}")
            return False
    
    def generate_email_body(self, partner_info: Dict[str, Any], 
                           program_info: Dict[str, Any], event_info: Dict[str, Any]) -> str:
        """Generate comprehensive email body with program details"""
        
        partner_name = partner_info.get('partner_name', 'Your Institution')
        contact_person = partner_info.get('contact_person_name', 'Dear Sir/Madam')
        
        program_name = program_info.get('name', 'Professional Training Program')
        program_description = program_info.get('description', 'Comprehensive professional development program')
        
        # Event details
        duration = event_info.get('duration_weeks', 'Flexible')
        start_date = event_info.get('start_date', 'Upcoming sessions')
        end_date = event_info.get('end_date', '')
        seats = event_info.get('seats', 'Limited')
        
        # Pricing information
        original_fee = event_info.get('original_fee', 0)
        discount_percentage = event_info.get('discount_percentage', 0)
        final_fee = event_info.get('final_fee', original_fee)
        
        # Format pricing
        if original_fee and discount_percentage:
            pricing_section = f"""
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd;"><strong>Investment</strong></td>
                <td style="padding: 10px; border: 1px solid #ddd;">
                    <span style="color: #e74c3c; text-decoration: line-through;">₹{original_fee:,}</span>
                    <strong style="color: #27ae60; font-size: 18px;">₹{final_fee:,}</strong>
                    <span style="background: #27ae60; color: white; padding: 2px 6px; border-radius: 4px; font-size: 12px;">
                        {discount_percentage}% OFF
                    </span>
                </td>
            </tr>
            """
        else:
            pricing_section = f"""
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd;"><strong>Investment</strong></td>
                <td style="padding: 10px; border: 1px solid #ddd;"><strong>₹{final_fee:,}</strong></td>
            </tr>
            """
        
        # Date formatting
        date_info = f"{start_date}" + (f" to {end_date}" if end_date else "")
        
        email_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Program Details - {program_name}</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px; margin-bottom: 20px;">
                <h1 style="margin: 0; font-size: 28px;">Learn with Leaders</h1>
                <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">Educational Excellence Program Details</p>
            </div>
            
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                <h2 style="color: #2c3e50; margin-top: 0;">Dear {contact_person},</h2>
                <p>Thank you for your interest in our educational programs during our call today. As promised, here are the comprehensive details about the <strong>{program_name}</strong> designed specifically for {partner_name}.</p>
            </div>
            
            <div style="background: white; border: 1px solid #e0e0e0; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
                <h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">Program Overview</h2>
                <h3 style="color: #2980b9;">{program_name}</h3>
                <p style="margin-bottom: 20px;">{program_description}</p>
                
                <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
                    <tr style="background: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Duration</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{duration} weeks</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Schedule</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{date_info}</td>
                    </tr>
                    <tr style="background: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Participants</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{seats} seats available</td>
                    </tr>
                    {pricing_section}
                </table>
            </div>
            
            <div style="background: #e8f5e8; border: 1px solid #27ae60; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
                <h3 style="color: #27ae60; margin-top: 0;">✅ Key Benefits</h3>
                <ul style="margin: 0; padding-left: 20px;">
                    <li>Industry-relevant curriculum designed by experts</li>
                    <li>Hands-on practical training sessions</li>
                    <li>Certificate of completion for all participants</li>
                    <li>Post-training support and resources</li>
                    <li>Flexible scheduling to accommodate institutional needs</li>
                    <li>Special institutional pricing and discounts</li>
                </ul>
            </div>
            
            <div style="background: #fff3cd; border: 1px solid #ffc107; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
                <h3 style="color: #856404; margin-top: 0;">⏰ Limited Time Offer</h3>
                <p style="margin: 0;">This special pricing is available for a limited time. We recommend securing your slots early to ensure availability for your students.</p>
            </div>
            
            <div style="background: white; border: 1px solid #e0e0e0; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
                <h3 style="color: #2c3e50; margin-top: 0;">Next Steps</h3>
                <ol>
                    <li><strong>Review the program details</strong> shared above</li>
                    <li><strong>Discuss with your team</strong> about student participation</li>
                    <li><strong>Contact us</strong> to confirm enrollment or ask questions</li>
                    <li><strong>Secure your slots</strong> before the deadline</li>
                </ol>
            </div>
            
            <div style="background: #2c3e50; color: white; padding: 20px; border-radius: 8px; text-align: center;">
                <h3 style="margin-top: 0; color: white;">Contact Information</h3>
                <p style="margin: 5px 0;"><strong>Sarah Johnson</strong> - Educational Program Consultant</p>
                <p style="margin: 5px 0;">📧 Email: {self.sender_email}</p>
                <p style="margin: 5px 0;">📞 Phone: +91-XXXXXXXXXX</p>
                <p style="margin: 15px 0 5px 0;"><strong>Learn with Leaders</strong></p>
                <p style="margin: 0; opacity: 0.8;">Empowering Education, Transforming Futures</p>
            </div>
            
            <div style="text-align: center; margin-top: 20px; color: #666; font-size: 12px;">
                <p>This email was sent following our conversation today. If you have any questions, please don't hesitate to contact us.</p>
            </div>
            
        </body>
        </html>
        """
        
        return email_body
    
    def confirm_email_address(self, email: str) -> bool:
        """Validate email address format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

# Global email service instance
email_service = EmailService()
