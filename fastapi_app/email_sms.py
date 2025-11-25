#!/usr/bin/env python3
"""
FastAPI Email/SMS API Server
============================

FastAPI version of the integrated email/SMS API.
Clean REST APIs for email and SMS services.

Author: AI Telecaller Team
Version: 3.0.0 (FastAPI)
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Dict, Any, Optional
import logging
import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models
class SMSRequest(BaseModel):
    phone_number: str
    message: str

class SMSBulkRequest(BaseModel):
    phone_numbers: List[str]
    message: str

class EmailRequest(BaseModel):
    to_email: EmailStr
    subject: str
    body: str
    from_email: Optional[str] = None

class EmailBulkRequest(BaseModel):
    emails: List[Dict[str, str]]

class TemplatedEmailRequest(BaseModel):
    to_email: EmailStr
    template_name: str
    template_data: Dict[str, Any]

class HealthResponse(BaseModel):
    status: str
    message: str
    services: Dict[str, str]
    endpoints: Dict[str, str]

# Initialize FastAPI app
app = FastAPI(
    title="Email/SMS API",
    description="Clean REST APIs for email and SMS services",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service dependencies
def get_sms_service():
    try:
        from app.services.sms_service import SMSService
        return SMSService()
    except Exception as e:
        logger.error(f"Error initializing SMS service: {e}")
        return None

def get_email_service():
    try:
        from app.services.email_service import EmailService
        return EmailService()
    except Exception as e:
        logger.error(f"Error initializing Email service: {e}")
        return None

def get_templated_email_service():
    try:
        from app.services.templated_email_service import TemplatedEmailService
        return TemplatedEmailService()
    except Exception as e:
        logger.error(f"Error initializing Templated Email service: {e}")
        return None

# ==========================================
# HEALTH CHECK
# ==========================================

@app.get("/", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="operational",
        message="Email/SMS API Server is running",
        services={
            "email": "Available",
            "sms": "Available", 
            "templated_email": "Available"
        },
        endpoints={
            "email": "/email",
            "sms": "/sms/send",
            "bulk_sms": "/sms/bulk",
            "templated_email": "/templated-email/{template_name}",
            "status": "/status"
        }
    )

# ==========================================
# SMS ENDPOINTS
# ==========================================

@app.post("/sms/send")
async def send_sms(request: SMSRequest, sms_service: Any = Depends(get_sms_service)):
    """Send a single SMS message"""
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
    """Send bulk SMS messages"""
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
    """Get SMS service status"""
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
    """Send a single email"""
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
    """Send bulk emails"""
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
    """Get email service status"""
    if not email_service:
        raise HTTPException(status_code=500, detail="Email service not available")
    
    try:
        result = email_service.get_service_status()
        return result
    except Exception as e:
        logger.error(f"Email status error: {e}")
        raise HTTPException(status_code=500, detail=f"Email status error: {str(e)}")

# ==========================================
# TEMPLATED EMAIL ENDPOINTS
# ==========================================

@app.post("/templated-email/send")
async def send_templated_email(request: TemplatedEmailRequest, templated_service: Any = Depends(get_templated_email_service)):
    """Send templated email"""
    if not templated_service:
        raise HTTPException(status_code=500, detail="Templated email service not available")
    
    try:
        result = templated_service.send_templated_email(
            to_email=request.to_email,
            template_name=request.template_name,
            template_data=request.template_data
        )
        if result.get('success'):
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get('error', 'Templated email sending failed'))
    except Exception as e:
        logger.error(f"Templated email error: {e}")
        raise HTTPException(status_code=500, detail=f"Templated email service error: {str(e)}")

@app.get("/templated-email/status")
async def get_templated_email_status(templated_service: Any = Depends(get_templated_email_service)):
    """Get templated email service status"""
    if not templated_service:
        raise HTTPException(status_code=500, detail="Templated email service not available")
    
    try:
        result = templated_service.get_service_status()
        return result
    except Exception as e:
        logger.error(f"Templated email status error: {e}")
        raise HTTPException(status_code=500, detail=f"Templated email status error: {str(e)}")

# ==========================================
# STATUS ENDPOINT
# ==========================================

@app.get("/status")
async def get_overall_status():
    """Get overall service status"""
    try:
        return {
            "status": "operational",
            "services": {
                "sms": "Available",
                "email": "Available",
                "templated_email": "Available"
            },
            "version": "3.0.0",
            "timestamp": "2025-01-04T00:00:00Z"
        }
    except Exception as e:
        logger.error(f"Status error: {e}")
        raise HTTPException(status_code=500, detail=f"Status error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
