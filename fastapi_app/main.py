#!/usr/bin/env python3
"""
AI Telecaller System - FastAPI Main Application
==============================================

FastAPI version of the main Lambda handler with all endpoints converted.
This replaces the Flask-based lambda_handler.py with modern FastAPI.

Key Features:
- AI-powered voice calls via Twilio
- SMS messaging via AWS SNS
- Email services via AWS SES (templated and raw)
- PostgreSQL database integration
- Real-time webhook handling
- Automatic API documentation

Author: AI Telecaller Team
Version: 3.0.0 (FastAPI)
Last Updated: 2025-01-04
"""

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, Optional, List
import json
import logging
import os
import sys
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import local modules
from fastapi_app.config import config
from fastapi_app.models import *
from fastapi_app.dependencies import *

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=config.app_name,
    description="AI-powered IVR + Messaging system with voice calls, SMS, and email services",
    version=config.app_version,
    docs_url=config.docs_url,
    redoc_url=config.redoc_url
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=config.cors_allow_credentials,
    allow_methods=config.cors_allow_methods,
    allow_headers=config.cors_allow_headers,
)

# ==========================================
# HEALTH CHECK ENDPOINTS
# ==========================================

@app.get("/", response_model=HealthResponse)
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    """
    return HealthResponse(
        status="healthy",
        service="AI Telecaller System",
        version=config.app_version,
        timestamp=datetime.now().isoformat()
    )

# ==========================================
# SMS ENDPOINTS
# ==========================================

@app.post("/sms/send")
async def send_sms(request: SMSRequest, sms_service: Any = Depends(get_sms_service)):
    """
    Send a single SMS message
    """
    if not sms_service:
        raise HTTPException(status_code=500, detail="SMS service not available")
    
    try:
        result = sms_service.send_sms(request.dict())
        if result.get('success'):
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get('error', 'SMS sending failed'))
    except Exception as e:
        logger.error(f"SMS send error: {e}")
        raise HTTPException(status_code=500, detail=f"SMS service error: {str(e)}")

@app.post("/sms/bulk")
async def send_bulk_sms(request: SMSBulkRequest, sms_service: Any = Depends(get_sms_service)):
    """
    Send bulk SMS messages
    """
    if not sms_service:
        raise HTTPException(status_code=500, detail="SMS service not available")
    
    try:
        result = sms_service.send_bulk_sms(request.dict())
        if result.get('success'):
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get('error', 'Bulk SMS sending failed'))
    except Exception as e:
        logger.error(f"Bulk SMS error: {e}")
        raise HTTPException(status_code=500, detail=f"Bulk SMS service error: {str(e)}")

@app.get("/sms/status")
async def get_sms_status(sms_service: Any = Depends(get_sms_service)):
    """
    Get SMS service status
    """
    if not sms_service:
        raise HTTPException(status_code=500, detail="SMS service not available")
    
    try:
        result = sms_service.get_sms_status()
        return result
    except Exception as e:
        logger.error(f"SMS status error: {e}")
        raise HTTPException(status_code=500, detail=f"SMS status error: {str(e)}")

# ==========================================
# EMAIL ENDPOINTS
# ==========================================

@app.post("/email")
async def send_email(request: EmailRequest, email_service: Any = Depends(get_email_service)):
    """
    Send a single email
    """
    if not email_service:
        raise HTTPException(status_code=500, detail="Email service not available")
    
    try:
        result = email_service.send_email(request.dict())
        if result.get('success'):
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get('error', 'Email sending failed'))
    except Exception as e:
        logger.error(f"Email send error: {e}")
        raise HTTPException(status_code=500, detail=f"Email service error: {str(e)}")

@app.post("/email/bulk")
async def send_bulk_email(request: EmailBulkRequest, email_service: Any = Depends(get_email_service)):
    """
    Send bulk emails
    """
    if not email_service:
        raise HTTPException(status_code=500, detail="Email service not available")
    
    try:
        result = email_service.send_bulk_email(request.dict())
        if result.get('success'):
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get('error', 'Bulk email sending failed'))
    except Exception as e:
        logger.error(f"Bulk email error: {e}")
        raise HTTPException(status_code=500, detail=f"Bulk email service error: {str(e)}")

@app.get("/email/status")
async def get_email_status(email_service: Any = Depends(get_email_service)):
    """
    Get email service status
    """
    if not email_service:
        raise HTTPException(status_code=500, detail="Email service not available")
    
    try:
        result = email_service.get_service_status()
        return result
    except Exception as e:
        logger.error(f"Email status error: {e}")
        raise HTTPException(status_code=500, detail=f"Email status error: {str(e)}")

# ==========================================
# CALL ENDPOINTS
# ==========================================

@app.post("/call/start")
async def start_call(request: CallRequest, twilio_service: Any = Depends(get_twilio_service)):
    """
    Start a new AI telecaller call
    """
    if not twilio_service:
        raise HTTPException(status_code=500, detail="Twilio service not available")
    
    try:
        result = twilio_service.make_call(
            to_number=request.to_number,
            system_prompt=request.system_prompt,
            call_metadata=request.call_metadata
        )
        if result.get('call_sid'):
            return result
        else:
            raise HTTPException(status_code=400, detail="Failed to initiate call")
    except Exception as e:
        logger.error(f"Call start error: {e}")
        raise HTTPException(status_code=500, detail=f"Call service error: {str(e)}")

# ==========================================
# WEBHOOK ENDPOINTS
# ==========================================

@app.post("/webhook/voice")
async def voice_webhook(request: Request):
    """
    Handle Twilio voice webhook
    """
    try:
        # Parse form data from Twilio
        form_data = await request.form()
        webhook_data = dict(form_data)
        
        logger.info(f"Voice webhook received: {webhook_data}")
        
        # Process the webhook (implement your logic here)
        return {"message": "Voice webhook received successfully"}
        
    except Exception as e:
        logger.error(f"Voice webhook error: {e}")
        raise HTTPException(status_code=500, detail=f"Webhook error: {str(e)}")

@app.post("/webhook/status")
async def status_webhook(request: Request):
    """
    Handle Twilio call status webhook
    """
    try:
        # Parse form data from Twilio
        form_data = await request.form()
        webhook_data = dict(form_data)
        
        logger.info(f"Status webhook received: {webhook_data}")
        
        # Process the webhook (implement your logic here)
        return {"message": "Status webhook received successfully"}
        
    except Exception as e:
        logger.error(f"Status webhook error: {e}")
        raise HTTPException(status_code=500, detail=f"Webhook error: {str(e)}")

# ==========================================
# DATABASE ENDPOINTS (using existing tables)
# ==========================================

@app.get("/partners", response_model=PartnerResponse)
async def get_partners(db_service: Any = Depends(get_database_service)):
    """Get all partners from existing database table"""
    if not db_service:
        raise HTTPException(status_code=500, detail="Database service not available")
    
    try:
        partners = db_service.get_all_partners()
        return PartnerResponse(
            success=True,
            partners=partners or [],
            count=len(partners) if partners else 0
        )
    except Exception as e:
        logger.error(f"Error getting partners: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/programs", response_model=ProgramResponse)
async def get_programs(db_service: Any = Depends(get_database_service)):
    """Get all programs from existing database table"""
    if not db_service:
        raise HTTPException(status_code=500, detail="Database service not available")
    
    try:
        programs = db_service.get_all_programs()
        return ProgramResponse(
            success=True,
            programs=programs or [],
            count=len(programs) if programs else 0
        )
    except Exception as e:
        logger.error(f"Error getting programs: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/program-events", response_model=EventResponse)
async def get_program_events(db_service: Any = Depends(get_database_service)):
    """Get all program events from existing database table"""
    if not db_service:
        raise HTTPException(status_code=500, detail="Database service not available")
    
    try:
        events = db_service.get_program_events()
        return EventResponse(
            success=True,
            events=events or [],
            count=len(events) if events else 0
        )
    except Exception as e:
        logger.error(f"Error getting program events: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/call-records", response_model=CallRecordResponse)
async def get_call_records(limit: int = 10, db_service: Any = Depends(get_database_service)):
    """Get call records from existing database table"""
    if not db_service:
        raise HTTPException(status_code=500, detail="Database service not available")
    
    try:
        calls = db_service.get_call_records(limit)
        return CallRecordResponse(
            success=True,
            calls=calls or [],
            count=len(calls) if calls else 0
        )
    except Exception as e:
        logger.error(f"Error getting call records: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/database/status")
async def get_database_status(db_service: Any = Depends(get_database_service)):
    """Get database status and statistics"""
    if not db_service:
        raise HTTPException(status_code=500, detail="Database service not available")
    
    try:
        stats = db_service.get_database_stats()
        return {
            "success": True,
            "database_status": "connected",
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error getting database status: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# ==========================================
# TEMPLATED EMAIL ENDPOINTS
# ==========================================

@app.post("/templated-email/create-templates")
async def create_email_templates():
    """
    Create all SES email templates
    """
    try:
        from app.services.ses_templated_email_service import SESTemplatedEmailService
        templated_service = SESTemplatedEmailService()
        result = templated_service.create_ses_templates()
        
        success_count = sum(1 for r in result.values() if r.get('success'))
        total_count = len(result)
        
        return {
            'success': success_count == total_count,
            'message': f"{success_count} of {total_count} templates created successfully",
            'templates_created': success_count,
            'total_templates': total_count,
            'results': result
        }
        
    except Exception as e:
        logger.error(f"Error creating templates: {e}")
        raise HTTPException(status_code=500, detail=f"Template creation error: {str(e)}")

@app.post("/templated-email/send-signup")
async def send_signup_email(request: dict):
    """
    Send account signup email
    """
    try:
        from app.services.ses_templated_email_service import SESTemplatedEmailService
        templated_service = SESTemplatedEmailService()
        result = templated_service.send_account_signup_email(request)
        
        if result.get('success'):
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get('error', 'Signup email failed'))
            
    except Exception as e:
        logger.error(f"Error sending signup email: {e}")
        raise HTTPException(status_code=500, detail=f"Signup email error: {str(e)}")

@app.post("/templated-email/send-otp")
async def send_otp_email(request: dict):
    """
    Send OTP email
    """
    try:
        from app.services.ses_templated_email_service import SESTemplatedEmailService
        templated_service = SESTemplatedEmailService()
        result = templated_service.send_otp_email(request)
        
        if result.get('success'):
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get('error', 'OTP email failed'))
            
    except Exception as e:
        logger.error(f"Error sending OTP email: {e}")
        raise HTTPException(status_code=500, detail=f"OTP email error: {str(e)}")

@app.get("/templated-email/status")
async def get_templated_email_status():
    """
    Get templated email service status
    """
    try:
        return {
            'success': True,
            'service': 'SES Templated Email Service',
            'status': 'healthy',
            'available_templates': [
                'AccountSignupTemplate',
                'ForgotPasswordTemplate',
                'OTPTemplate',
                'OrderConfirmationTemplate'
            ],
            'version': config.app_version,
            'endpoints': {
                'POST /templated-email/create-templates': 'Create all SES email templates',
                'POST /templated-email/send-signup': 'Send account signup email',
                'POST /templated-email/send-otp': 'Send OTP verification email',
                'GET /templated-email/status': 'Get templated email service status'
            }
        }
    except Exception as e:
        logger.error(f"Error getting templated email status: {e}")
        raise HTTPException(status_code=500, detail=f"Status error: {str(e)}")

# ==========================================
# STARTUP EVENT
# ==========================================

@app.on_event("startup")
async def startup_event():
    """
    Application startup event
    """
    logger.info("AI Telecaller FastAPI application starting up...")
    logger.info(f"API documentation available at {config.docs_url}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.host, port=config.port)