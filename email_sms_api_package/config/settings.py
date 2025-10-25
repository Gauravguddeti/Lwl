#!/usr/bin/env python3
"""
Configuration Management for Email & SMS API Package
Centralized settings and environment management
"""

import os
from typing import Dict, Any, Optional

class APIConfig:
    """Configuration class for Email & SMS API Package"""
    
    def __init__(self):
        """Initialize configuration from environment variables"""
        
        # AWS Configuration
        self.AWS_REGION = os.getenv('AWS_REGION', 'us-west-2')
        self.AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
        self.AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
        
        # Email Configuration
        self.SES_SENDER_EMAIL = os.getenv('SES_SENDER_EMAIL', 'support@f5universe.com')
        self.CUSTOM_DOMAIN = os.getenv('CUSTOM_DOMAIN', 'f5universe.com')
        self.SUBDOMAIN = os.getenv('SUBDOMAIN', 'mail.futuristic5.com')
        
        # SMTP Configuration (for Gmail)
        self.SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
        self.EMAIL_USERNAME = os.getenv('EMAIL_USERNAME')  # Gmail address
        self.EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')  # Gmail app password
        
        # SMS Configuration
        self.SMS_SENDER_ID = os.getenv('SMS_SENDER_ID', 'IVR')
        self.SMS_SANDBOX_MODE = os.getenv('SMS_SANDBOX_MODE', 'true').lower() == 'true'
        
        # Service Feature Flags
        self.EMAIL_ENABLED = os.getenv('EMAIL_ENABLED', 'true').lower() == 'true'
        self.SMS_ENABLED = os.getenv('SMS_ENABLED', 'true').lower() == 'true'
        self.TEMPLATED_EMAIL_ENABLED = os.getenv('TEMPLATED_EMAIL_ENABLED', 'true').lower() == 'true'
        
        # Brand Configuration
        self.BRAND_LOGO_URL = os.getenv('BRAND_LOGO_URL', 'https://k43feq9x55.execute-api.us-west-2.amazonaws.com/dev/logo.png')
        self.BRAND_COLOR = os.getenv('BRAND_COLOR', '#007bff')
        self.BRAND_BG_COLOR = os.getenv('BRAND_BG_COLOR', '#f8f9fa')
        
        # API Configuration
        self.API_STAGE = os.getenv('API_STAGE', 'dev')
        self.API_TIMEOUT = int(os.getenv('API_TIMEOUT', '30'))
        
        # Validation
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate required configuration"""
        errors = []
        
        # Check AWS credentials
        if not self.AWS_ACCESS_KEY_ID:
            errors.append("AWS_ACCESS_KEY_ID is required")
        if not self.AWS_SECRET_ACCESS_KEY:
            errors.append("AWS_SECRET_ACCESS_KEY is required")
        
        # Warn about SMTP credentials
        if self.EMAIL_ENABLED and not (self.EMAIL_USERNAME and self.EMAIL_PASSWORD):
            print("⚠️  Warning: SMTP credentials not configured. Gmail email sending will not work.")
        
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
    
    def get_email_config(self) -> Dict[str, Any]:
        """Get email service configuration"""
        return {
            'enabled': self.EMAIL_ENABLED,
            'aws_region': self.AWS_REGION,
            'ses_sender': self.SES_SENDER_EMAIL,
            'custom_domain': self.CUSTOM_DOMAIN,
            'subdomain': self.SUBDOMAIN,
            'smtp_server': self.SMTP_SERVER,
            'smtp_port': self.SMTP_PORT,
            'smtp_configured': bool(self.EMAIL_USERNAME and self.EMAIL_PASSWORD),
            'brand_logo': self.BRAND_LOGO_URL,
            'brand_color': self.BRAND_COLOR,
            'bg_color': self.BRAND_BG_COLOR
        }
    
    def get_sms_config(self) -> Dict[str, Any]:
        """Get SMS service configuration"""
        return {
            'enabled': self.SMS_ENABLED,
            'aws_region': self.AWS_REGION,
            'sender_id': self.SMS_SENDER_ID,
            'sandbox_mode': self.SMS_SANDBOX_MODE,
            'features': {
                'single_sms': True,
                'bulk_sms': True,
                'international': True,
                'delivery_reports': False  # SNS doesn't provide by default
            }
        }
    
    def get_templated_email_config(self) -> Dict[str, Any]:
        """Get templated email service configuration"""
        return {
            'enabled': self.TEMPLATED_EMAIL_ENABLED,
            'aws_region': self.AWS_REGION,
            'sender_email': self.SES_SENDER_EMAIL,
            'supported_templates': [
                'account_signup',
                'forgot_password',
                'otp_verification',
                'welcome_pack',
                'order_confirmation'
            ],
            'pdf_generation': True,  # Assuming ReportLab is available
            'brand_logo': self.BRAND_LOGO_URL,
            'brand_color': self.BRAND_COLOR,
            'bg_color': self.BRAND_BG_COLOR
        }
    
    def get_api_config(self) -> Dict[str, Any]:
        """Get API configuration"""
        return {
            'stage': self.API_STAGE,
            'timeout': self.API_TIMEOUT,
            'cors_enabled': True,
            'aws_region': self.AWS_REGION,
            'endpoints': {
                'email': '/email',
                'sms': '/sms',
                'templated_email': '/templated-email'
            }
        }
    
    def get_all_config(self) -> Dict[str, Any]:
        """Get complete configuration summary"""
        return {
            'email': self.get_email_config(),
            'sms': self.get_sms_config(),
            'templated_email': self.get_templated_email_config(),
            'api': self.get_api_config(),
            'aws_region': self.AWS_REGION,
            'stage': self.API_STAGE
        }
    
    def validate_environment(self) -> Dict[str, Any]:
        """Validate current environment setup"""
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'services': {}
        }
        
        # Check AWS credentials
        if not (self.AWS_ACCESS_KEY_ID and self.AWS_SECRET_ACCESS_KEY):
            validation_results['valid'] = False
            validation_results['errors'].append("AWS credentials not configured")
        else:
            validation_results['services']['aws'] = 'configured'
        
        # Check email services
        email_issues = []
        if not self.SES_SENDER_EMAIL:
            email_issues.append("SES sender email not configured")
        if not (self.EMAIL_USERNAME and self.EMAIL_PASSWORD):
            email_issues.append("SMTP credentials not configured")
        
        if email_issues:
            validation_results['warnings'].extend(email_issues)
            validation_results['services']['email'] = 'partial'
        else:
            validation_results['services']['email'] = 'configured'
        
        # Check SMS service
        if self.SMS_ENABLED:
            validation_results['services']['sms'] = 'configured'
        else:
            validation_results['warnings'].append("SMS service disabled")
            validation_results['services']['sms'] = 'disabled'
        
        # Check templated email
        if self.TEMPLATED_EMAIL_ENABLED:
            validation_results['services']['templated_email'] = 'configured'
        else:
            validation_results['warnings'].append("Templated email service disabled")
            validation_results['services']['templated_email'] = 'disabled'
        
        return validation_results

# Global configuration instance
config = APIConfig()

# Convenience function for getting configuration
def get_config() -> APIConfig:
    """Get the global configuration instance"""
    return config