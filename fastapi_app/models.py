"""
FastAPI Pydantic Models
======================

Pydantic models for request/response validation.
Uses same data structures as existing database tables.
"""

from pydantic import BaseModel, EmailStr
from typing import Dict, Any, Optional, List
from datetime import datetime

# ==========================================
# REQUEST MODELS
# ==========================================

class SMSRequest(BaseModel):
    """SMS request model"""
    phone_number: str
    message: str

class SMSBulkRequest(BaseModel):
    """Bulk SMS request model"""
    phone_numbers: List[str]
    message: str

class EmailRequest(BaseModel):
    """Email request model"""
    to_email: EmailStr
    subject: str
    body: str
    from_email: Optional[str] = None

class EmailBulkRequest(BaseModel):
    """Bulk email request model"""
    emails: List[Dict[str, str]]

class CallRequest(BaseModel):
    """Call request model"""
    to_number: str
    system_prompt: str
    call_metadata: Dict[str, Any]

class TemplatedEmailRequest(BaseModel):
    """Templated email request model"""
    to_email: EmailStr
    template_name: str
    template_data: Dict[str, Any]

# ==========================================
# RESPONSE MODELS
# ==========================================

class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    service: str
    version: str
    timestamp: str

class DatabaseResponse(BaseModel):
    """Database response model"""
    success: bool
    count: int
    data: List[Dict[str, Any]]

class PartnerResponse(BaseModel):
    """Partner response model"""
    success: bool
    partners: List[Dict[str, Any]]
    count: int

class ProgramResponse(BaseModel):
    """Program response model"""
    success: bool
    programs: List[Dict[str, Any]]
    count: int

class EventResponse(BaseModel):
    """Program event response model"""
    success: bool
    events: List[Dict[str, Any]]
    count: int

class CallRecordResponse(BaseModel):
    """Call record response model"""
    success: bool
    calls: List[Dict[str, Any]]
    count: int

# ==========================================
# DATABASE MODELS (matching existing tables)
# ==========================================

class Partner(BaseModel):
    """Partner model matching database table"""
    id: Optional[int] = None
    name: str
    type: str = "school"
    active: bool = True
    status_id: int = 1
    created_at: Optional[datetime] = None
    created_by: str = "system"
    phone: Optional[str] = None
    email: Optional[str] = None
    contact_person: Optional[str] = None
    updated_at: Optional[datetime] = None
    updated_by: str = "system"

class Program(BaseModel):
    """Program model matching database table"""
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    type: str = "course"
    active: bool = True
    created_at: Optional[datetime] = None

class ProgramEvent(BaseModel):
    """Program event model matching database table"""
    id: Optional[int] = None
    program_id: int
    name: str
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    location: Optional[str] = None
    capacity: int = 50
    active: bool = True
    created_at: Optional[datetime] = None

class CallLog(BaseModel):
    """Call log model matching database table"""
    id: Optional[int] = None
    call_sid: Optional[str] = None
    partner_id: Optional[int] = None
    program_id: Optional[int] = None
    event_id: Optional[int] = None
    status: str = "initiated"
    outcome: Optional[str] = None
    duration: Optional[int] = None
    recording_url: Optional[str] = None
    created_at: Optional[datetime] = None
