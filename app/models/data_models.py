from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List
from datetime import datetime
import json

@dataclass
class Program:
    """Program data model"""
    id: Optional[int] = None
    name: str = ""
    description: Optional[str] = None
    base_fee: float = 0.0
    duration_days: Optional[int] = None
    category: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class School:
    """School data model"""
    id: Optional[int] = None
    name: str = ""
    contact_person: Optional[str] = None
    phone_number: str = ""
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class ProgramEvent:
    """Program Event data model"""
    id: Optional[int] = None
    program_id: int = 0
    event_name: str = ""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    discounted_fee: Optional[float] = None
    discount_percentage: int = 0
    total_seats: int = 50
    available_seats: int = 50
    zoom_call_slot: Optional[datetime] = None
    registration_deadline: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class ScheduledJobEvent:
    """Scheduled Job Event data model"""
    id: Optional[int] = None
    scheduled_job_id: int = 0
    school_id: int = 0
    program_event_id: int = 0
    caller_number: Optional[str] = None
    call_status: str = "PENDING"
    call_scheduled_at: Optional[datetime] = None
    call_completed_at: Optional[datetime] = None
    outcome: Optional[str] = None
    reschedule_slot: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class CallEvent:
    """Complete call event with all related data"""
    event_id: int
    school_name: str
    program_name: str
    program_description: Optional[str] = None
    base_fee: float = 0.0
    discounted_fee: Optional[float] = None
    discount_percentage: int = 0
    total_seats: int = 0
    available_seats: int = 0
    zoom_call_slot: Optional[datetime] = None
    caller_number: Optional[str] = None
    call_status: str = "PENDING"
    school_phone: str = ""
    school_contact_person: Optional[str] = None
    program_start_date: Optional[datetime] = None
    program_end_date: Optional[datetime] = None
    registration_deadline: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        # Convert datetime objects to strings
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        return data

@dataclass
class AuditLog:
    """Audit Log data model"""
    id: Optional[int] = None
    scheduled_job_event_id: Optional[int] = None
    school_id: Optional[int] = None
    program_event_id: Optional[int] = None
    call_sid: Optional[str] = None
    caller_number: Optional[str] = None
    recipient_number: Optional[str] = None
    call_start_time: Optional[datetime] = None
    call_end_time: Optional[datetime] = None
    call_duration_seconds: Optional[int] = None
    call_status: Optional[str] = None
    response_type: Optional[str] = None
    conversation_summary: Optional[str] = None
    reschedule_requested: bool = False
    reschedule_slot: Optional[datetime] = None
    follow_up_required: bool = False
    ai_prompt_used: Optional[str] = None
    twilio_response: Optional[str] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None

@dataclass
class TwilioCallResponse:
    """Twilio API call response model"""
    call_sid: Optional[str] = None
    status: str = "PENDING"
    direction: Optional[str] = None
    from_number: Optional[str] = None
    to_number: Optional[str] = None
    duration: Optional[int] = None
    price: Optional[float] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None

    def to_audit_dict(self) -> Dict[str, Any]:
        """Convert to dictionary suitable for audit logging"""
        return {
            'call_sid': self.call_sid,
            'call_status': self.status,
            'call_duration_seconds': self.duration,
            'twilio_response': json.dumps(asdict(self)),
            'error_message': self.error_message
        }

@dataclass
class AIPromptData:
    """Data structure for AI prompt generation"""
    school_name: str
    contact_person: Optional[str]
    program_name: str
    program_description: str
    base_fee: float
    discounted_fee: Optional[float]
    discount_percentage: int
    total_seats: int
    available_seats: int
    zoom_call_slot: Optional[datetime]
    program_start_date: Optional[datetime] = None
    program_end_date: Optional[datetime] = None
    registration_deadline: Optional[datetime] = None
    caller_name: str = "AI Telecaller from Learn with Leaders"

    def get_savings_amount(self) -> float:
        """Calculate savings amount"""
        if self.discounted_fee and self.base_fee:
            return self.base_fee - self.discounted_fee
        return 0.0

    def get_formatted_dates(self) -> Dict[str, str]:
        """Get formatted dates for display"""
        date_format = "%d/%m/%Y"
        time_format = "%I:%M %p"
        
        result = {}
        
        if self.program_start_date:
            result['program_start'] = self.program_start_date.strftime(date_format)
        
        if self.program_end_date:
            result['program_end'] = self.program_end_date.strftime(date_format)
        
        if self.registration_deadline:
            result['registration_deadline'] = self.registration_deadline.strftime(date_format)
        
        if self.zoom_call_slot:
            result['zoom_call_date'] = self.zoom_call_slot.strftime(date_format)
            result['zoom_call_time'] = self.zoom_call_slot.strftime(time_format)
        
        return result

# Enum-like classes for constants
class CallStatus:
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    BUSY = "BUSY"
    NO_ANSWER = "NO_ANSWER"
    VOICEMAIL = "VOICEMAIL"

class ResponseType:
    INTERESTED = "INTERESTED"
    BUSY = "BUSY"
    NO_ANSWER = "NO_ANSWER"
    VOICEMAIL = "VOICEMAIL"
    NEEDS_APPROVAL = "NEEDS_APPROVAL"
    LANGUAGE_BARRIER = "LANGUAGE_BARRIER"
    NOT_INTERESTED = "NOT_INTERESTED"
    RESCHEDULE_REQUESTED = "RESCHEDULE_REQUESTED"

class JobStatus:
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
