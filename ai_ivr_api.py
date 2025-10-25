#!/usr/bin/env python3
"""
AI IVR API - Complete IVR orchestration with database integration
Handles scheduled calls with partner and program context from database
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import sys
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
import threading
import time

# Add the project root to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import database access
from app.database.postgres_data_access import DatabaseAccess
from app.services.email_service import EmailService
from app.services.sms_service import SMSService

# Import AI Telecaller (if available)
try:
    from ai_telecaller.core.telecaller import TelecallerSystem
    AI_TELECALLER_AVAILABLE = True
except ImportError:
    print("⚠️ AI Telecaller not available - running in simulation mode")
    AI_TELECALLER_AVAILABLE = False
    TelecallerSystem = None

# Try to import Twilio for making calls
try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    print("⚠️ Twilio not available - calls will be simulated")
    TWILIO_AVAILABLE = False
    Client = None

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize services
db_access = DatabaseAccess()
email_service = EmailService()
sms_service = SMSService()

# Initialize AI Telecaller system (if available)
telecaller_system = None
if AI_TELECALLER_AVAILABLE:
    try:
        telecaller_system = TelecallerSystem()
        print("✅ AI Telecaller System initialized")
    except Exception as e:
        print(f"⚠️ AI Telecaller initialization failed: {e}")
        telecaller_system = None

# Initialize Twilio client (if available)
twilio_client = None
if TWILIO_AVAILABLE:
    try:
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        if account_sid and auth_token:
            twilio_client = Client(account_sid, auth_token)
            print("✅ Twilio client initialized")
    except Exception as e:
        print(f"⚠️ Twilio client initialization failed: {e}")

# Store active calls for tracking
active_calls = {}

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'operational',
        'message': 'AI IVR API Server is running',
        'services': {
            'database': 'Available',
            'ai_telecaller': 'Available' if AI_TELECALLER_AVAILABLE else 'Simulated',
            'twilio': 'Available' if TWILIO_AVAILABLE else 'Simulated',
            'email': 'Available',
            'sms': 'Available'
        },
        'endpoints': {
            'make_call': '/ivr/make-call',
            'call_status': '/ivr/call-status/{call_id}',
            'active_calls': '/ivr/active-calls',
            'database_info': '/ivr/database-info',
            'test_context': '/ivr/test-context',
            'send_notification': '/ivr/send-notification'
        }
    })

@app.route('/ivr/make-call', methods=['POST', 'OPTIONS'])
def make_ivr_call():
    """
    Initiate AI IVR call with database context
    
    POST /ivr/make-call
    {
        "partner_id": 1,
        "program_event_id": 2,
        "scheduled_job_event_id": 3,  // Optional
        "call_mode": "live|simulation",  // Optional, defaults to simulation
        "webhook_url": "https://your-domain.com/webhooks"  // Optional for call status updates
    }
    """
    if request.method == 'OPTIONS':
        return jsonify({'message': 'CORS preflight'})
    
    try:
        data = request.get_json()
        
        # Validate required parameters
        partner_id = data.get('partner_id')
        program_event_id = data.get('program_event_id')
        scheduled_job_event_id = data.get('scheduled_job_event_id')  # Optional
        call_mode = data.get('call_mode', 'simulation')
        webhook_url = data.get('webhook_url')
        
        if not partner_id or not program_event_id:
            return jsonify({
                'success': False,
                'error': 'Missing required parameters: partner_id and program_event_id are required'
            }), 400
        
        # Fetch context from database
        context_result = get_call_context(partner_id, program_event_id, scheduled_job_event_id)
        
        if not context_result['success']:
            return jsonify(context_result), 400
        
        call_context = context_result['context']
        
        # Generate unique call ID
        call_id = f"ivr_call_{partner_id}_{program_event_id}_{int(time.time())}"
        
        # Initiate the call
        if call_mode == 'live' and TWILIO_AVAILABLE and twilio_client:
            call_result = initiate_live_call(call_id, call_context, webhook_url)
        else:
            call_result = initiate_simulation_call(call_id, call_context)
        
        # Store call info
        active_calls[call_id] = {
            'call_id': call_id,
            'partner_id': partner_id,
            'program_event_id': program_event_id,
            'scheduled_job_event_id': scheduled_job_event_id,
            'call_mode': call_mode,
            'context': call_context,
            'initiated_at': datetime.now().isoformat(),
            'status': call_result.get('status', 'initiated'),
            'twilio_call_sid': call_result.get('twilio_call_sid'),
            'webhook_url': webhook_url
        }
        
        return jsonify({
            'success': True,
            'call_id': call_id,
            'status': call_result.get('status', 'initiated'),
            'call_mode': call_mode,
            'partner_info': {
                'name': call_context['partner']['partner_name'],
                'phone': call_context['partner']['contact_phone'],
                'contact_person': call_context['partner']['contact_person_name']
            },
            'program_info': {
                'name': call_context['program_event']['program_name'],
                'event_date': call_context['program_event']['start_date'],
                'early_fee': call_context['program_event']['early_fee'],
                'regular_fee': call_context['program_event']['regular_fee']
            },
            'twilio_call_sid': call_result.get('twilio_call_sid'),
            'estimated_duration': '5-10 minutes',
            'message': call_result.get('message', 'Call initiated successfully')
        }), 200
        
    except Exception as e:
        logging.error(f"Error making IVR call: {e}")
        return jsonify({
            'success': False,
            'error': f'Call initiation failed: {str(e)}'
        }), 500

@app.route('/ivr/call-status/<call_id>', methods=['GET'])
def get_call_status(call_id):
    """Get status of specific call"""
    try:
        if call_id not in active_calls:
            return jsonify({
                'success': False,
                'error': f'Call ID {call_id} not found'
            }), 404
        
        call_info = active_calls[call_id]
        
        # If it's a live call, get real status from Twilio
        if call_info.get('twilio_call_sid') and twilio_client:
            try:
                twilio_call = twilio_client.calls(call_info['twilio_call_sid']).fetch()
                call_info['twilio_status'] = twilio_call.status
                call_info['duration'] = twilio_call.duration
                call_info['price'] = twilio_call.price
            except Exception as e:
                logging.warning(f"Failed to fetch Twilio call status: {e}")
        
        return jsonify({
            'success': True,
            'call_info': call_info
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Status check failed: {str(e)}'
        }), 500

@app.route('/ivr/active-calls', methods=['GET'])
def get_active_calls():
    """Get all active calls"""
    try:
        return jsonify({
            'success': True,
            'active_calls_count': len(active_calls),
            'active_calls': list(active_calls.values())
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get active calls: {str(e)}'
        }), 500

@app.route('/ivr/test-context', methods=['POST'])
def test_call_context():
    """
    Test call context retrieval without making actual call
    
    POST /ivr/test-context
    {
        "partner_id": 1,
        "program_event_id": 2,
        "scheduled_job_event_id": 3  // Optional
    }
    """
    try:
        data = request.get_json()
        
        partner_id = data.get('partner_id')
        program_event_id = data.get('program_event_id')
        scheduled_job_event_id = data.get('scheduled_job_event_id')
        
        if not partner_id or not program_event_id:
            return jsonify({
                'success': False,
                'error': 'Missing required parameters: partner_id and program_event_id are required'
            }), 400
        
        # Fetch context from database
        context_result = get_call_context(partner_id, program_event_id, scheduled_job_event_id)
        
        return jsonify(context_result), 200 if context_result['success'] else 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Context test failed: {str(e)}'
        }), 500

@app.route('/ivr/database-info', methods=['GET'])
def get_database_info():
    """Get database information for debugging"""
    try:
        # Test database connection
        connection_test = db_access.test_connection()
        
        # Get sample data counts
        partners = db_access.get_partners()
        programs = db_access.get_programs()
        events = db_access.get_program_events()
        scheduled_events = db_access.get_scheduled_job_events()
        
        return jsonify({
            'success': True,
            'database_status': 'connected' if connection_test else 'disconnected',
            'data_counts': {
                'partners': len(partners),
                'programs': len(programs),
                'program_events': len(events),
                'scheduled_job_events': len(scheduled_events)
            },
            'sample_partners': partners[:3] if partners else [],
            'sample_events': events[:3] if events else []
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Database info failed: {str(e)}'
        }), 500

def get_call_context(partner_id: int, program_event_id: int, scheduled_job_event_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Fetch complete call context from database
    
    Returns:
        Dict containing partner info, program event details, and call context
    """
    try:
        # Fetch partner information
        partner = db_access.get_partner_by_id(partner_id)
        if not partner:
            return {
                'success': False,
                'error': f'Partner with ID {partner_id} not found'
            }
        
        # Fetch program event information
        program_event = db_access.get_program_event_by_id(program_event_id)
        if not program_event:
            return {
                'success': False,
                'error': f'Program event with ID {program_event_id} not found'
            }
        
        # Fetch scheduled job event if provided
        scheduled_job_event = None
        if scheduled_job_event_id:
            scheduled_job_events = db_access.get_scheduled_job_events()
            scheduled_job_event = next(
                (event for event in scheduled_job_events if event.get('scheduled_job_event_id') == scheduled_job_event_id),
                None
            )
        
        # Build AI context for the call
        ai_context = build_ai_context(partner, program_event, scheduled_job_event)
        
        return {
            'success': True,
            'context': {
                'partner': partner,
                'program_event': program_event,
                'scheduled_job_event': scheduled_job_event,
                'ai_context': ai_context,
                'call_purpose': determine_call_purpose(program_event, scheduled_job_event),
                'key_talking_points': generate_talking_points(partner, program_event)
            }
        }
        
    except Exception as e:
        logging.error(f"Error getting call context: {e}")
        return {
            'success': False,
            'error': f'Failed to fetch call context: {str(e)}'
        }

def build_ai_context(partner: Dict[str, Any], program_event: Dict[str, Any], scheduled_job_event: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Build AI context for the telecaller system"""
    
    # Extract key information
    partner_name = partner.get('partner_name', 'Unknown Institution')
    contact_person = partner.get('contact_person_name', 'Sir/Madam')
    partner_type = partner.get('contact_type', 'Institution')
    
    program_name = program_event.get('program_name', 'Educational Program')
    event_date = program_event.get('start_date', 'TBD')
    early_fee = program_event.get('early_fee', 'Contact for pricing')
    regular_fee = program_event.get('regular_fee', 'Contact for pricing')
    discount = program_event.get('discount', 0)
    seats = program_event.get('seats', 'Limited')
    
    return {
        'partner_context': {
            'institution_name': partner_name,
            'contact_person': contact_person,
            'institution_type': partner_type,
            'relationship': 'Potential educational partner'
        },
        'program_context': {
            'program_name': program_name,
            'event_date': str(event_date),
            'pricing': {
                'early_bird': str(early_fee),
                'regular': str(regular_fee),
                'discount_available': discount > 0,
                'discount_percentage': discount
            },
            'availability': {
                'seats_available': str(seats),
                'urgency': 'Limited seats available'
            }
        },
        'call_objective': 'Introduce program, explain benefits, and secure enrollment interest',
        'conversation_tone': 'Professional, educational, partnership-focused',
        'key_benefits': [
            f'Tailored for {partner_type.lower()}s like {partner_name}',
            'Industry-recognized certification',
            'Flexible scheduling options',
            'Expert-led training sessions'
        ]
    }

def determine_call_purpose(program_event: Dict[str, Any], scheduled_job_event: Optional[Dict[str, Any]]) -> str:
    """Determine the main purpose of the call"""
    
    program_name = program_event.get('program_name', 'Educational Program')
    event_date = program_event.get('start_date')
    
    if scheduled_job_event:
        return f"Scheduled outreach for {program_name} program starting {event_date}"
    else:
        return f"Program introduction and enrollment opportunity for {program_name}"

def generate_talking_points(partner: Dict[str, Any], program_event: Dict[str, Any]) -> List[str]:
    """Generate key talking points for the call"""
    
    partner_name = partner.get('partner_name', 'your institution')
    partner_type = partner.get('contact_type', 'institution')
    program_name = program_event.get('program_name', 'our program')
    
    return [
        f"Introduce {program_name} specifically designed for {partner_type.lower()}s",
        f"Highlight how {program_name} can benefit {partner_name}",
        "Explain certification and accreditation benefits",
        "Discuss flexible scheduling and delivery options",
        "Present pricing options and early bird discounts",
        "Address any questions about curriculum or requirements",
        "Secure next steps (meeting, proposal, enrollment)"
    ]

def initiate_live_call(call_id: str, call_context: Dict[str, Any], webhook_url: Optional[str] = None) -> Dict[str, Any]:
    """Initiate a live call using Twilio"""
    
    try:
        partner = call_context['partner']
        phone_number = partner.get('contact_phone')
        
        if not phone_number:
            return {
                'status': 'failed',
                'message': 'No phone number available for partner'
            }
        
        # Prepare the call
        twilio_phone = os.getenv('TWILIO_PHONE_NUMBER')
        if not twilio_phone:
            return {
                'status': 'failed',
                'message': 'Twilio phone number not configured'
            }
        
        # Create TwiML URL for handling the call
        twiml_url = f"{os.getenv('BASE_URL', 'http://localhost:8080')}/ivr/handle-call/{call_id}"
        
        # Make the call
        if not twilio_client:
            return {
                'status': 'failed',
                'message': 'Twilio client not available'
            }
            
        call = twilio_client.calls.create(
            to=phone_number,
            from_=twilio_phone,
            url=twiml_url,
            status_callback=webhook_url if webhook_url else None,
            status_callback_event=['initiated', 'ringing', 'answered', 'completed'],
            method='POST'
        )
        
        return {
            'status': 'initiated',
            'message': f'Live call initiated to {phone_number}',
            'twilio_call_sid': call.sid
        }
        
    except Exception as e:
        logging.error(f"Failed to initiate live call: {e}")
        return {
            'status': 'failed',
            'message': f'Live call failed: {str(e)}'
        }

def initiate_simulation_call(call_id: str, call_context: Dict[str, Any]) -> Dict[str, Any]:
    """Initiate a simulated call for testing"""
    
    try:
        partner = call_context['partner']
        program_event = call_context['program_event']
        
        # Simulate call processing in background
        def simulate_call():
            time.sleep(2)  # Simulate dialing
            active_calls[call_id]['status'] = 'ringing'
            
            time.sleep(3)  # Simulate ringing
            active_calls[call_id]['status'] = 'answered'
            active_calls[call_id]['answered_at'] = datetime.now().isoformat()
            
            # Simulate AI conversation
            simulate_ai_conversation(call_id, call_context)
            
            time.sleep(30)  # Simulate 30-second conversation
            active_calls[call_id]['status'] = 'completed'
            active_calls[call_id]['completed_at'] = datetime.now().isoformat()
            active_calls[call_id]['duration'] = '30 seconds'
            active_calls[call_id]['outcome'] = 'Interested - Follow-up required'
        
        # Start simulation in background thread
        threading.Thread(target=simulate_call, daemon=True).start()
        
        return {
            'status': 'initiated',
            'message': f'Simulation call initiated to {partner.get("partner_name")} for {program_event.get("program_name")}'
        }
        
    except Exception as e:
        logging.error(f"Failed to initiate simulation call: {e}")
        return {
            'status': 'failed',
            'message': f'Simulation call failed: {str(e)}'
        }

def simulate_ai_conversation(call_id: str, call_context: Dict[str, Any]):
    """Simulate AI conversation for testing purposes"""
    
    try:
        partner = call_context['partner']
        program_event = call_context['program_event']
        
        # Add conversation simulation details
        active_calls[call_id]['conversation'] = {
            'greeting': f"Hello, this is calling from our education services team. Am I speaking with {partner.get('contact_person_name', 'the right person')}?",
            'introduction': f"We're reaching out regarding our {program_event.get('program_name')} program.",
            'key_points_covered': call_context['key_talking_points'][:3],
            'customer_response': 'Showed interest, requested more information',
            'next_steps': 'Send detailed program brochure and schedule follow-up call'
        }
        
        # Simulate sending follow-up email
        if partner.get('contact_email'):
            email_data = {
                'email_type': 'smtp',
                'to_email': partner['contact_email'],
                'subject': f'Follow-up: {program_event.get("program_name")} Program Information',
                'body': f"""
Dear {partner.get('contact_person_name', 'Sir/Madam')},

Thank you for your time during our call today regarding the {program_event.get('program_name')} program.

As discussed, this program is specifically designed for institutions like {partner.get('partner_name')} and offers:

- Industry-recognized certification
- Flexible scheduling options  
- Expert-led training sessions
- Early bird pricing: {program_event.get('early_fee')}
- Regular pricing: {program_event.get('regular_fee')}

We'll follow up with more detailed information as requested.

Best regards,
Education Services Team
                """,
                'is_html': False
            }
            
            # Send follow-up email
            email_result = email_service.send_email(email_data)
            active_calls[call_id]['follow_up_email'] = email_result
            
            # Send follow-up SMS if phone number is available
            contact_phone = partner.get('contact_phone')
            if contact_phone:
                sms_message = f"""Hi {partner.get('contact_person_name', 'there')}, thank you for your interest in our {program_event.get('program_name')} program. We'll send you detailed information shortly. Early bird fee: {program_event.get('early_fee')} | Regular fee: {program_event.get('regular_fee')}. Reply STOP to opt out."""
                
                sms_data = {
                    'phone_number': contact_phone,
                    'message': sms_message,
                    'sender_id': 'EduServices'
                }
                
                sms_result = sms_service.send_sms(sms_data)
                active_calls[call_id]['follow_up_sms'] = sms_result
            else:
                active_calls[call_id]['follow_up_sms'] = {'status': 'skipped', 'reason': 'No phone number available'}
        
    except Exception as e:
        logging.error(f"Error in AI conversation simulation: {e}")

@app.route('/ivr/handle-call/<call_id>', methods=['POST'])
def handle_live_call(call_id):
    """Handle live Twilio call - TwiML response"""
    
    try:
        if call_id not in active_calls:
            # Return basic TwiML for unknown calls
            return '''<?xml version="1.0" encoding="UTF-8"?>
            <Response>
                <Say>Thank you for your call. Please try again later.</Say>
            </Response>''', 200, {'Content-Type': 'text/xml'}
        
        call_context = active_calls[call_id]['context']
        partner = call_context['partner']
        program_event = call_context['program_event']
        
        # Build TwiML response with AI context
        twiml_response = f'''<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Say voice="alice">
                Hello, this is calling from our education services team. 
                Am I speaking with {partner.get('contact_person_name', 'the right person')}?
            </Say>
            <Pause length="2"/>
            <Say voice="alice">
                We're reaching out regarding our {program_event.get('program_name')} program 
                specifically designed for institutions like {partner.get('partner_name')}.
            </Say>
            <Pause length="1"/>
            <Say voice="alice">
                This program offers industry-recognized certification with flexible scheduling. 
                Would you be interested in learning more about how this can benefit your organization?
            </Say>
            <Record maxLength="30" action="/ivr/process-response/{call_id}" />
        </Response>'''
        
        return twiml_response, 200, {'Content-Type': 'text/xml'}
        
    except Exception as e:
        logging.error(f"Error handling live call: {e}")
        return '''<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Say>We're experiencing technical difficulties. Please try again later.</Say>
        </Response>''', 200, {'Content-Type': 'text/xml'}

@app.route('/ivr/send-notification', methods=['POST'])
def send_notification():
    """
    Send email/SMS notification using database context
    
    POST /ivr/send-notification
    {
        "partner_id": 1,
        "program_event_id": 2,
        "notification_type": "email|sms|both",
        "custom_message": "Optional custom message"
    }
    """
    try:
        data = request.get_json()
        
        # Validate required parameters
        partner_id = data.get('partner_id')
        program_event_id = data.get('program_event_id')
        notification_type = data.get('notification_type', 'both')
        custom_message = data.get('custom_message')
        
        if not partner_id or not program_event_id:
            return jsonify({
                'success': False,
                'error': 'Missing required parameters: partner_id and program_event_id are required'
            }), 400
        
        # Fetch context from database
        context_result = get_call_context(partner_id, program_event_id)
        
        if not context_result['success']:
            return jsonify(context_result), 400
        
        call_context = context_result['context']
        partner = call_context['partner']
        program_event = call_context['program_event']
        
        results = {}
        
        # Send Email
        if notification_type in ['email', 'both']:
            contact_email = partner.get('contact_email')
            if contact_email:
                subject = f"Follow-up: {program_event.get('program_name')} Program Information"
                message = custom_message or f"""
Dear {partner.get('contact_person_name', 'Valued Partner')},

Thank you for your interest in our {program_event.get('program_name')} program.

This program is specifically designed for institutions like {partner.get('partner_name')} and offers:

- Industry-recognized certification
- Flexible scheduling options  
- Expert-led training sessions
- Early bird pricing: {program_event.get('early_fee')}
- Regular pricing: {program_event.get('regular_fee')}

We're here to help answer any questions you may have about this program.

Best regards,
Education Services Team
                """
                
                email_data = {
                    'to_email': contact_email,
                    'subject': subject,
                    'message': message.strip(),
                    'is_html': False
                }
                
                results['email'] = email_service.send_email(email_data)
            else:
                results['email'] = {'success': False, 'error': 'No email address available'}
        
        # Send SMS
        if notification_type in ['sms', 'both']:
            contact_phone = partner.get('contact_phone')
            if contact_phone:
                sms_message = custom_message or f"Hi {partner.get('contact_person_name', 'there')}, thank you for your interest in our {program_event.get('program_name')} program. Early bird fee: {program_event.get('early_fee')} | Regular fee: {program_event.get('regular_fee')}. We'll follow up with details."
                
                sms_data = {
                    'phone_number': contact_phone,
                    'message': sms_message,
                    'sender_id': 'EduServices'
                }
                
                results['sms'] = sms_service.send_sms(sms_data)
            else:
                results['sms'] = {'success': False, 'error': 'No phone number available'}
        
        return jsonify({
            'success': True,
            'message': f'Notifications sent for {partner.get("partner_name")} - {program_event.get("program_name")}',
            'partner': {
                'id': partner_id,
                'name': partner.get('partner_name'),
                'contact_person': partner.get('contact_person_name'),
                'email': partner.get('contact_email'),
                'phone': partner.get('contact_phone')
            },
            'program': {
                'id': program_event_id,
                'name': program_event.get('program_name'),
                'early_fee': program_event.get('early_fee'),
                'regular_fee': program_event.get('regular_fee')
            },
            'results': results
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Notification sending failed: {str(e)}'
        }), 500

if __name__ == '__main__':
    # Load environment variables
    port = int(os.getenv('PORT', 8090))
    debug = os.getenv('DEBUG', 'True').lower() == 'true'
    
    print(f"🚀 Starting AI IVR API Server on port {port}")
    print(f"🤖 AI Telecaller: {'Available' if AI_TELECALLER_AVAILABLE else 'Simulated'}")
    print(f"📞 Twilio: {'Available' if TWILIO_AVAILABLE else 'Simulated'}")
    print(f"🗄️  Database: PostgreSQL lwl_pg_us_2")
    print(f"🔧 Debug Mode: {debug}")
    print(f"\n📚 Available endpoints:")
    print(f"   GET  /                        - Health check")
    print(f"   POST /ivr/make-call           - Initiate IVR call with context")
    print(f"   GET  /ivr/call-status/<id>    - Get call status")
    print(f"   GET  /ivr/active-calls        - List active calls")
    print(f"   POST /ivr/test-context        - Test database context")
    print(f"   GET  /ivr/database-info       - Database information")
    print(f"   POST /ivr/send-notification   - Send email/SMS with context")
    print(f"\n🎯 Test with Postman: http://localhost:{port}")
    print(f"📋 Database Integration: Partners, Programs, Events, Scheduled Jobs")
    
    app.run(host='0.0.0.0', port=port, debug=debug)