"""
Simplified IVR Service for handling calls using the getcallstobedone database function
This works with the actual DBA function that takes no parameters
"""

import logging
from datetime import datetime
from typing import Dict, Any, List
from app.database.postgres_data_access import db_access

logger = logging.getLogger(__name__)

class SimpleIVRService:
    """Simplified service class for IVR operations using getcallstobedone function"""
    
    def __init__(self):
        self.db = db_access
    
    def get_all_calls_to_be_done(self) -> List[Dict[str, Any]]:
        """
        Get all scheduled calls that need to be made using the DBA function
        
        The DBA's getcallstobedone() function returns all calls scheduled for today
        with complete call information including:
        - contact_person_name: Name of person to call
        - contact_type: Type of contact (e.g., 'school')
        - contact_email: Email address
        - contact_phone: Phone number
        - partner_name: Name of the partner
        - scheduled_job_event_id: Event ID
        - scheduled_job_id: Job ID
        - call_datetime: Scheduled call time
        - system_prompt_id: Prompt ID
        - system_prompt: AI system prompt text
        - ai_model_name: AI model to use
        
        Returns:
            List of call data dictionaries
        """
        try:
            # Call the database function (no parameters needed)
            calls = self.db.call_getcallstobedone()
            
            logger.info(f"Retrieved {len(calls)} calls to be done")
            
            # Log some details about the calls
            for call in calls:
                logger.info(f"Call for {call['contact_person_name']} at {call['partner_name']} "
                           f"scheduled for {call['call_datetime']} using {call['ai_model_name']}")
            
            return calls
            
        except Exception as e:
            logger.error(f"Error getting calls to be done: {e}")
            return []
    
    def get_call_by_event_id(self, event_id: int) -> Dict[str, Any]:
        """
        Get a specific call by its scheduled_job_event_id
        
        Args:
            event_id: The scheduled_job_event_id to look for
            
        Returns:
            Call data dictionary or empty dict if not found
        """
        try:
            all_calls = self.get_all_calls_to_be_done()
            
            for call in all_calls:
                if call['scheduled_job_event_id'] == event_id:
                    logger.info(f"Found call for event ID {event_id}: {call['contact_person_name']}")
                    return call
            
            logger.warning(f"No call found for event ID {event_id}")
            return {}
            
        except Exception as e:
            logger.error(f"Error getting call by event ID {event_id}: {e}")
            return {}
    
    def get_calls_for_partner(self, partner_name: str) -> List[Dict[str, Any]]:
        """
        Get all calls for a specific partner
        
        Args:
            partner_name: Name of the partner to filter by
            
        Returns:
            List of call data dictionaries for the partner
        """
        try:
            all_calls = self.get_all_calls_to_be_done()
            
            partner_calls = [call for call in all_calls if call['partner_name'] == partner_name]
            
            logger.info(f"Found {len(partner_calls)} calls for partner '{partner_name}'")
            return partner_calls
            
        except Exception as e:
            logger.error(f"Error getting calls for partner '{partner_name}': {e}")
            return []
    
    def format_call_for_telecaller(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format call data for use with the existing telecaller system
        
        Args:
            call_data: Raw call data from getcallstobedone function
            
        Returns:
            Formatted call data for telecaller integration
        """
        try:
            formatted_call = {
                # Core contact information
                'contact_name': call_data['contact_person_name'],
                'contact_phone': call_data['contact_phone'].strip() if call_data['contact_phone'] else None,
                'contact_email': call_data['contact_email'],
                'contact_type': call_data['contact_type'],
                
                # Partner information
                'partner_name': call_data['partner_name'],
                
                # Scheduling information
                'scheduled_job_event_id': call_data['scheduled_job_event_id'],
                'scheduled_job_id': call_data['scheduled_job_id'],
                'call_datetime': call_data['call_datetime'],
                
                # AI configuration
                'system_prompt_id': call_data['system_prompt_id'],
                'system_prompt': call_data['system_prompt'],
                'ai_model_name': call_data['ai_model_name'],
                
                # Additional metadata for telecaller
                'call_source': 'getcallstobedone_function',
                'prepared_at': str(datetime.now())
            }
            
            return formatted_call
            
        except Exception as e:
            logger.error(f"Error formatting call data: {e}")
            return {}

# Create a global instance for easy importing
simple_ivr_service = SimpleIVRService()
