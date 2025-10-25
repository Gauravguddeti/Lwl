"""
IVR Service for handling calls using the getcallstobedone database function
Integrates with the existing AI telecaller system
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from app.database.postgres_data_access import db_access

logger = logging.getLogger(__name__)

class IVRService:
    """Service class for IVR operations using getcallstobedone function"""
    
    def __init__(self):
        self.db = db_access
    
    def get_calls_to_be_done(self, 
                           contact_name: str,
                           partner_name: str,
                           scheduled_job_event_id: int,
                           scheduled_job_id: int,
                           callback_time: Optional[datetime] = None,
                           system_prompt_id: Optional[int] = None,
                           ai_model_name: str = "gpt-4") -> List[Dict[str, Any]]:
        """
        Get calls to be done using the DBA-created function
        
        Args:
            contact_name: Name of contact to call
            partner_name: Partner name (e.g., "Bright Future Training Institute")
            scheduled_job_event_id: Event ID from scheduled_job_events table
            scheduled_job_id: Job ID from scheduled_jobs table
            callback_time: When to callback (defaults to now + 1 hour)
            system_prompt_id: Which prompt to use (defaults to active prompt)
            ai_model_name: AI model to use
        """
        try:
            # Set default callback time if not provided
            if callback_time is None:
                callback_time = datetime.now() + timedelta(hours=1)
            
            # Get default system prompt if not provided
            if system_prompt_id is None:
                prompts = self.db.get_system_prompts(is_active=True)
                if prompts:
                    system_prompt_id = prompts[0]['system_prompt_id']
                    system_prompt_text = prompts[0]['system_prompt']
                else:
                    logger.error("No active system prompts found")
                    return []
            else:
                # Get the specific system prompt text
                prompts = self.db.get_system_prompts(is_active=True)
                prompt_dict = {p['system_prompt_id']: p['system_prompt'] for p in prompts}
                system_prompt_text = prompt_dict.get(system_prompt_id, "Default IVR prompt")
            
            # Format callback time as string
            callback_time_str = callback_time.strftime('%Y-%m-%d %H:%M:%S')
            
            logger.info(f"Calling getcallstobedone for {contact_name} at {partner_name}")
            
            # Call the database function
            results = self.db.call_getcallstobedone(
                contact_name=contact_name,
                partner_name=partner_name,
                scheduled_job_event_id=scheduled_job_event_id,
                scheduled_job_id=scheduled_job_id,
                callback_time=callback_time_str,
                system_prompt_id=system_prompt_id,
                system_prompt=system_prompt_text,
                ai_model_name=ai_model_name
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error in get_calls_to_be_done: {str(e)}")
            return []
    
    def process_scheduled_calls(self, scheduled_job_id: int) -> List[Dict[str, Any]]:
        """
        Process all calls for a specific scheduled job
        Gets job events and processes each one
        """
        try:
            # Get scheduled job events for this job
            job_events = self.db.get_scheduled_job_events(job_id=scheduled_job_id)
            
            if not job_events:
                logger.warning(f"No job events found for scheduled_job_id: {scheduled_job_id}")
                return []
            
            all_calls = []
            
            for event in job_events:
                # Extract data from the joined result
                contact_name = event.get('contact', 'Unknown Contact')
                partner_name = event.get('partner_name', 'Unknown Partner')
                scheduled_job_event_id = event.get('scheduled_job_event_id')
                callback_time = event.get('job_datetime')  # Use the scheduled datetime
                
                logger.info(f"Processing call for {contact_name} at {partner_name}")
                
                # Get calls to be done for this event
                calls = self.get_calls_to_be_done(
                    contact_name=contact_name,
                    partner_name=partner_name,
                    scheduled_job_event_id=scheduled_job_event_id,
                    scheduled_job_id=scheduled_job_id,
                    callback_time=callback_time
                )
                
                all_calls.extend(calls)
            
            logger.info(f"Processed {len(all_calls)} total calls for job {scheduled_job_id}")
            return all_calls
            
        except Exception as e:
            logger.error(f"Error processing scheduled calls: {str(e)}")
            return []
    
    def get_ivr_context_for_call(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare context for IVR call using the call data from getcallstobedone
        Integrates with existing dynamic data fetcher
        """
        try:
            from app.services.dynamic_data_fetcher import dynamic_data_fetcher
            
            # Extract partner and contact info from call data
            partner_name = call_data.get('partner_name')
            contact_name = call_data.get('contact_name')
            
            # Get dynamic context (program, event, pricing data)
            context = dynamic_data_fetcher.get_complete_call_context(
                contact_number=None,  # We have contact_name instead
                partner_id=None
            )
            
            # Enhance context with IVR-specific data
            context.update({
                'ivr_call_data': call_data,
                'contact_name': contact_name,
                'partner_name': partner_name,
                'system_prompt': call_data.get('system_prompt'),
                'ai_model': call_data.get('ai_model_name'),
                'callback_time': call_data.get('callback_time'),
                'scheduled_job_id': call_data.get('scheduled_job_id'),
                'scheduled_job_event_id': call_data.get('scheduled_job_event_id')
            })
            
            return context
            
        except Exception as e:
            logger.error(f"Error preparing IVR context: {str(e)}")
            return {}

# Global IVR service instance
ivr_service = IVRService()
