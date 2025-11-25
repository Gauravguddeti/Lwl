"""
FastAPI Dependencies
===================

Dependency injection for FastAPI services.
Reuses existing services from the Flask application.
"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

def get_database_service() -> Optional[Any]:
    """Get the existing database service (uses same tables as Flask)"""
    try:
        from app.services.database_service import DatabaseService
        return DatabaseService()
    except Exception as e:
        logger.error(f"Error initializing Database service: {e}")
        return None

def get_sms_service() -> Optional[Any]:
    """Get the existing SMS service (uses same database tables)"""
    try:
        from app.services.sms_service import SMSService
        return SMSService()
    except Exception as e:
        logger.error(f"Error initializing SMS service: {e}")
        return None

def get_email_service() -> Optional[Any]:
    """Get the existing Email service (uses same database tables)"""
    try:
        from app.services.email_service import EmailService
        return EmailService()
    except Exception as e:
        logger.error(f"Error initializing Email service: {e}")
        return None

def get_twilio_service() -> Optional[Any]:
    """Get the existing Twilio service (uses same database tables)"""
    try:
        from app.services.twilio_service import TwilioService
        return TwilioService()
    except Exception as e:
        logger.error(f"Error initializing Twilio service: {e}")
        return None

def get_templated_email_service() -> Optional[Any]:
    """Get the existing Templated Email service"""
    try:
        from app.services.templated_email_service import TemplatedEmailService
        return TemplatedEmailService()
    except Exception as e:
        logger.error(f"Error initializing Templated Email service: {e}")
        return None

def get_ses_templated_email_service() -> Optional[Any]:
    """Get the existing SES Templated Email service"""
    try:
        from app.services.ses_templated_email_service import SESTemplatedEmailService
        return SESTemplatedEmailService()
    except Exception as e:
        logger.error(f"Error initializing SES Templated Email service: {e}")
        return None
