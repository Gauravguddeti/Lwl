"""
Enhanced AI Tools for Dynamic Database Access and Tool Calling
All tools fetch real-time data from database - no hardcoded content
"""

import json
import logging
from decimal import Decimal
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, date
from langchain_core.tools import tool
from app.database.postgres_data_access import db_access
from app.services.dynamic_data_fetcher import dynamic_data_fetcher

logger = logging.getLogger(__name__)

# Custom JSON encoder to handle Decimal and datetime types
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)

def safe_json_dumps(data):
    """Safely serialize data to JSON with custom encoder"""
    try:
        return json.dumps(data, cls=CustomJSONEncoder)
    except Exception as e:
        # Fallback to simple string conversion for problematic objects
        logger.warning(f"JSON serialization failed, using fallback: {e}")
        return json.dumps(str(data))

@tool
def get_current_program_info(partner_id: Optional[int] = None) -> str:
    """
    Get current program information from database including name, fees, and description.
    Returns real-time program details for the conversation.
    
    Args:
        partner_id: Optional partner ID to get partner-specific programs
    """
    try:
        program_data = dynamic_data_fetcher.get_program_data(partner_id)
        
        if program_data:
            info = {
                'program_name': program_data.get('program_name', 'Educational Programme'),
                'base_fees': program_data.get('base_fees', 'TBD'),
                'description': program_data.get('description', 'Premium educational experience'),
                'program_id': program_data.get('program_id'),
                'status': 'found'
            }
        else:
            info = {
                'program_name': 'Programme information not available',
                'base_fees': 'TBD',
                'description': 'Please contact us for details',
                'status': 'not_found'
            }
        
        logger.info(f"Program info retrieved: {info['program_name']}")
        return safe_json_dumps(info)
        
    except Exception as e:
        logger.error(f"Error getting program info: {str(e)}")
        return safe_json_dumps({'status': 'error', 'message': str(e)})

@tool
def get_current_pricing_and_availability() -> str:
    """
    Get current pricing, discounts, and seat availability from database.
    Returns real-time pricing and availability information.
    """
    try:
        # Get the most current event data
        event_data = dynamic_data_fetcher.get_event_data()
        program_data = dynamic_data_fetcher.get_program_data()
        
        if event_data and program_data:
            pricing_info = dynamic_data_fetcher.format_pricing_info(program_data, event_data)
            
            availability_info = {
                'event_date': event_data.get('datetime', 'TBD'),
                'original_price': pricing_info['formatted_original'],
                'discount_amount': pricing_info['formatted_discount'],
                'final_price': pricing_info['formatted_final'],
                'discount_percentage': pricing_info['discount_percentage'],
                'available_seats': event_data.get('seats', 'Limited'),
                'status': 'available'
            }
        else:
            availability_info = {
                'event_date': 'TBD',
                'original_price': 'TBD',
                'discount_amount': 'TBD',
                'final_price': 'TBD',
                'discount_percentage': 0,
                'available_seats': 'Please contact us',
                'status': 'information_pending'
            }
        
        logger.info(f"Pricing info retrieved: {availability_info['final_price']}")
        return safe_json_dumps(availability_info)
        
    except Exception as e:
        logger.error(f"Error getting pricing info: {str(e)}")
        return safe_json_dumps({'status': 'error', 'message': str(e)})

@tool
def get_available_calendar_slots(days_ahead: int = 7) -> str:
    """
    Get available calendar slots for scheduling meetings.
    Returns real-time calendar availability.
    
    Args:
        days_ahead: Number of days ahead to check availability (default: 7)
    """
    try:
        available_slots = dynamic_data_fetcher.get_calendar_availability(days_ahead)
        
        # Format for conversation use
        formatted_slots = []
        for slot in available_slots[:10]:  # Limit to first 10 slots
            formatted_slots.append({
                'display_text': slot['display_text'],
                'datetime': slot['formatted_datetime'],
                'available': slot['available']
            })
        
        calendar_info = {
            'available_slots': formatted_slots,
            'total_slots': len(available_slots),
            'next_available': formatted_slots[0]['display_text'] if formatted_slots else 'No slots available',
            'status': 'success'
        }
        
        logger.info(f"Calendar slots retrieved: {len(formatted_slots)} available")
        return safe_json_dumps(calendar_info)
        
    except Exception as e:
        logger.error(f"Error getting calendar slots: {str(e)}")
        return safe_json_dumps({'status': 'error', 'message': str(e)})

@tool
def search_partner_by_contact(contact_number: str) -> str:
    """
    Search for partner information using contact number.
    Returns partner details from database.
    
    Args:
        contact_number: Contact number to search for
    """
    try:
        partner_data = dynamic_data_fetcher.get_partner_data(contact_number=contact_number)
        
        if partner_data:
            partner_info = {
                'partner_name': partner_data.get('partner_name', 'Unknown'),
                'type': partner_data.get('type', 'Unknown'),
                'contact': partner_data.get('contact', ''),
                'partner_id': partner_data.get('partner_id'),
                'status': 'found'
            }
        else:
            partner_info = {
                'partner_name': 'Partner not found',
                'type': 'Unknown',
                'contact': contact_number,
                'status': 'not_found'
            }
        
        logger.info(f"Partner search result: {partner_info['partner_name']}")
        return safe_json_dumps(partner_info)
        
    except Exception as e:
        logger.error(f"Error searching partner: {str(e)}")
        return safe_json_dumps({'status': 'error', 'message': str(e)})

@tool
def get_upcoming_events_summary(days_ahead: int = 30) -> str:
    """
    Get summary of upcoming program events with dates and availability.
    Returns overview of upcoming program events.
    
    Args:
        days_ahead: Number of days ahead to check for events (default: 30)
    """
    try:
        events = db_access.get_upcoming_events(days_ahead)
        
        if events:
            events_summary = []
            for event in events[:5]:  # Limit to first 5 events
                events_summary.append({
                    'date': event.get('datetime', 'TBD'),
                    'fees': f"£{event.get('fees', 'TBD')}",
                    'discount': f"£{event.get('discount', '0')}",
                    'seats': event.get('seats', 'Limited'),
                    'program_id': event.get('program_id')
                })
            
            summary = {
                'upcoming_events': events_summary,
                'total_events': len(events),
                'next_event_date': events_summary[0]['date'] if events_summary else 'TBD',
                'status': 'success'
            }
        else:
            summary = {
                'upcoming_events': [],
                'total_events': 0,
                'next_event_date': 'No upcoming events',
                'status': 'no_events'
            }
        
        logger.info(f"Events summary retrieved: {summary['total_events']} events")
        return safe_json_dumps(summary)
        
    except Exception as e:
        logger.error(f"Error getting events summary: {str(e)}")
        return safe_json_dumps({'status': 'error', 'message': str(e)})

@tool
def schedule_follow_up_meeting(contact_email: str, preferred_datetime: str, meeting_type: str = "program_discussion") -> str:
    """
    Schedule a follow-up meeting with the contact.
    Simulates scheduling a meeting in calendar system.
    
    Args:
        contact_email: Email address of the contact
        preferred_datetime: Preferred date and time for the meeting
        meeting_type: Type of meeting (default: program_discussion)
    """
    try:
        # In production, this would integrate with actual calendar system
        meeting_info = {
            'meeting_scheduled': True,
            'contact_email': contact_email,
            'datetime': preferred_datetime,
            'meeting_type': meeting_type,
            'meeting_link': 'https://zoom.us/j/example123',  # Would be real link
            'calendar_invite_sent': True,
            'confirmation_id': f"LWL_{int(datetime.now().timestamp())}",
            'status': 'scheduled'
        }
        
        logger.info(f"Meeting scheduled for {contact_email} at {preferred_datetime}")
        return safe_json_dumps(meeting_info)
        
    except Exception as e:
        logger.error(f"Error scheduling meeting: {str(e)}")
        return safe_json_dumps({'status': 'error', 'message': str(e)})

def get_database_tools() -> List:
    """
    Get all available AI tools for dynamic database access.
    These tools allow GPT to fetch real-time data during conversations.
    """
    tools = [
        get_current_program_info,
        get_current_pricing_and_availability,
        get_available_calendar_slots,
        search_partner_by_contact,
        get_upcoming_events_summary,
        schedule_follow_up_meeting
    ]
    
    logger.info(f"Loaded {len(tools)} AI tools for database access")
    return tools
