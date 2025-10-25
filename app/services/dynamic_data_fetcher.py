"""
Dynamic Data Fetcher for System Prompts
Fetches real-time data from database to populate system prompts dynamically
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from app.database.postgres_data_access import db_access

logger = logging.getLogger(__name__)

class DynamicDataFetcher:
    """Fetches real-time data from database for dynamic system prompts"""
    
    def __init__(self):
        self.db = db_access
    
    def get_partner_data(self, partner_id: int = None, contact_number: str = None) -> Optional[Dict[str, Any]]:
        """
        Fetch partner data from PostgreSQL database (partners table)
        Can search by partner_id or contact number
        """
        try:
            if contact_number:
                # Search through all partners to find matching contact number
                partners = self.db.get_partners()
                for partner in partners:
                    # Check both contact_phone and contact_email fields
                    partner_phone = str(partner.get('contact_phone', ''))
                    partner_email = str(partner.get('contact_email', ''))
                    search_contact = str(contact_number).strip()
                    
                    # Remove common separators for comparison
                    partner_phone_clean = partner_phone.replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
                    search_clean = search_contact.replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
                    
                    # Check phone number or email match
                    if (partner_phone_clean and search_clean and (search_clean in partner_phone_clean or partner_phone_clean in search_clean)) or \
                       (partner_email and search_contact and search_contact.lower() in partner_email.lower()):
                        logger.info(f"Found partner by contact: {partner.get('partner_name')}")
                        return partner
            
            if partner_id:
                partner = self.db.get_partner_by_id(partner_id)
                if partner:
                    logger.info(f"Found partner by ID: {partner.get('partner_name')}")
                    return partner
            
            # If no specific criteria, return first partner (for testing)
            partners = self.db.get_partners()
            if partners:
                logger.info(f"Using default partner: {partners[0].get('partner_name')}")
                return partners[0]
            
            logger.warning("No partner data found")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching partner data: {str(e)}")
            return None
    
    def get_program_data(self, partner_id: int = None) -> Optional[Dict[str, Any]]:
        """
        Fetch program data from PostgreSQL database (programs table)
        """
        try:
            programs = self.db.get_programs()
            
            if programs:
                # Return the first program or the most relevant one
                program = programs[0]
                logger.info(f"Found program: {program.get('name', program.get('program_name'))}")
                return program
            
            logger.warning("No program data found")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching program data: {str(e)}")
            return None
    
    def get_event_data(self, program_id: int = None, partner_id: int = None) -> Optional[Dict[str, Any]]:
        """
        Fetch upcoming event data from PostgreSQL database (program_events table)
        Returns the next available event with seats, fees, discount
        """
        try:
            if program_id:
                events = self.db.get_program_events(program_id=program_id)
            else:
                events = self.db.get_upcoming_events(days_ahead=90)
            
            if events:
                # Find the first active event or just return the first one
                event = events[0]
                logger.info(f"Found event: {event.get('start_date')} for program {event.get('program_name')}")
                return event
            
            logger.warning("No event data found")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching event data: {str(e)}")
            return None
    
    def get_complete_call_context(self, partner_id: int = None, contact_number: str = None) -> Dict[str, Any]:
        """
        Fetch complete context for a call including partner, program, and event data
        This creates the dynamic data for system prompt generation
        """
        try:
            logger.info(f"Fetching complete call context from PostgreSQL database for contact: {contact_number}")
            
            # Get partner data
            partner_data = self.get_partner_data(partner_id, contact_number)
            
            # Get program and event data
            program_data = self.get_program_data()
            event_data = None
            
            if program_data:
                program_id = program_data.get('program_id')
                event_data = self.get_event_data(program_id=program_id)
            
            # If no events found, try to get any upcoming events
            if not event_data:
                event_data = self.get_event_data()
            
            # Compile complete context
            context = {
                'partner_info': partner_data,
                'program_info': program_data,
                'event_info': event_data,
                'fetched_at': datetime.now().isoformat(),
                'data_source': 'postgresql_database'
            }
            
            # Log what was found
            partner_name = partner_data.get('partner_name', 'Unknown') if partner_data else 'None'
            program_name = program_data.get('name', program_data.get('program_name', 'Unknown')) if program_data else 'None'
            event_date = event_data.get('start_date', event_data.get('event_date', 'Unknown')) if event_data else 'None'
            
            # Handle both fee structures (early_fee/regular_fee vs fees)
            fees = 'Unknown'
            discount = 0
            if event_data:
                # PostgreSQL structure uses early_fee and regular_fee
                early_fee = event_data.get('early_fee', 0)
                regular_fee = event_data.get('regular_fee', 0)
                fees = regular_fee if regular_fee else early_fee  # Prefer regular fee
                discount = event_data.get('discount', 0)
                
                # Fallback to generic 'fees' field if above not found
                if not fees:
                    fees = event_data.get('fees', 'Unknown')
            
            logger.info(f"Complete context fetched - Partner: {partner_name}, Program: {program_name}, Event: {event_date}, Fees: ${fees}, Discount: ${discount}")
            
            return context
            
        except Exception as e:
            logger.error(f"Error fetching complete call context: {str(e)}")
            return {
                'partner_info': None,
                'program_info': None,
                'event_info': None,
                'fetched_at': datetime.now().isoformat(),
                'data_source': 'error',
                'error': str(e)
            }
    
    def get_calendar_availability(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """
        Get available calendar slots for scheduling
        This would be used for tool calling during conversations
        """
        try:
            # For now, generate some sample available slots
            # In production, this would connect to calendar system
            available_slots = []
            
            from datetime import datetime, timedelta
            base_date = datetime.now() + timedelta(days=1)  # Start from tomorrow
            
            for day in range(days_ahead):
                date = base_date + timedelta(days=day)
                
                # Add morning slots (10 AM, 11 AM)
                for hour in [10, 11]:
                    slot = {
                        'datetime': date.replace(hour=hour, minute=0, second=0, microsecond=0),
                        'formatted_datetime': date.replace(hour=hour, minute=0).strftime('%Y-%m-%d %H:%M'),
                        'display_text': date.replace(hour=hour, minute=0).strftime('%B %d at %I:%M %p'),
                        'available': True
                    }
                    available_slots.append(slot)
                
                # Add afternoon slots (2 PM, 3 PM)
                for hour in [14, 15]:
                    slot = {
                        'datetime': date.replace(hour=hour, minute=0, second=0, microsecond=0),
                        'formatted_datetime': date.replace(hour=hour, minute=0).strftime('%Y-%m-%d %H:%M'),
                        'display_text': date.replace(hour=hour, minute=0).strftime('%B %d at %I:%M %p'),
                        'available': True
                    }
                    available_slots.append(slot)
            
            logger.info(f"Generated {len(available_slots)} available calendar slots")
            return available_slots
            
        except Exception as e:
            logger.error(f"Error getting calendar availability: {str(e)}")
            return []
    
    def format_pricing_info(self, program_info: Dict[str, Any], event_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format pricing information for use in conversations
        Calculates final price after discount
        """
        try:
            # Get base fee from program or event (handle PostgreSQL structure)
            base_fee = 0
            if program_info:
                base_fee = program_info.get('basefees', program_info.get('base_fees', 0))
            
            # Handle PostgreSQL event fee structure (early_fee/regular_fee)
            event_fee = 0
            if event_info:
                regular_fee = event_info.get('regular_fee', 0)
                early_fee = event_info.get('early_fee', 0)
                event_fee = regular_fee if regular_fee else early_fee
                
                # Fallback to generic 'fees' field
                if not event_fee:
                    event_fee = event_info.get('fees', 0)
            
            discount = event_info.get('discount', 0) if event_info else 0
            
            # Use event fee if available, otherwise use program base fee
            original_price = float(event_fee) if event_fee else float(base_fee)
            discount_amount = float(discount) if discount else 0
            final_price = max(0, original_price - discount_amount)  # Ensure non-negative
            
            # Detect currency based on price range (rough heuristic)
            if original_price > 1000:
                currency = 'INR'
                currency_symbol = '₹'
            else:
                currency = 'USD'
                currency_symbol = '$'
            
            pricing_info = {
                'original_price': original_price,
                'discount_amount': discount_amount,
                'final_price': final_price,
                'currency': currency,
                'formatted_original': f"{currency_symbol}{original_price:,.0f}",
                'formatted_discount': f"{currency_symbol}{discount_amount:,.0f}",
                'formatted_final': f"{currency_symbol}{final_price:,.0f}",
                'discount_percentage': round((discount_amount / original_price * 100), 1) if original_price > 0 else 0
            }
            
            logger.info(f"Pricing calculated: {currency_symbol}{original_price:,.0f} - {currency_symbol}{discount_amount:,.0f} = {currency_symbol}{final_price:,.0f} ({pricing_info['discount_percentage']}% discount)")
            return pricing_info
            
        except Exception as e:
            logger.error(f"Error formatting pricing info: {str(e)}")
            return {
                'original_price': 0,
                'discount_amount': 0,
                'final_price': 0,
                'currency': 'USD',
                'formatted_original': '$TBD',
                'formatted_discount': '$0',
                'formatted_final': '$TBD',
                'discount_percentage': 0
            }

# Global instance
dynamic_data_fetcher = DynamicDataFetcher()
