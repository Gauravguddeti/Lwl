"""
Email & SMS API Package
Clean APIs extracted from working implementation for IVR integration

This package provides:
- Email service (SMTP, SES custom domain, SES subdomain)
- SMS service (Amazon SNS)  
- Templated email service (professional templates)
- AWS Lambda handlers for REST API deployment
- Configuration management
- Integration documentation

For your friend's IVR system integration.
"""

__version__ = "1.0.0"
__author__ = "Email & SMS API Package"
__description__ = "Clean APIs for IVR Email & SMS Integration"

# Import main services for easy access
try:
    from .services.email_service import EmailService
    from .services.sms_service import SMSService  
    from .services.templated_email_service import TemplatedEmailService
    from .config.settings import config, get_config
    
    __all__ = [
        'EmailService',
        'SMSService', 
        'TemplatedEmailService',
        'config',
        'get_config'
    ]
    
except ImportError:
    # If imports fail, still allow package to be imported
    __all__ = []