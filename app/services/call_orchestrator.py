"""
Call Orchestrator for Database-Driven AI Telecalls
Manages the complete call workflow with database integration
"""

import logging
import time
from app.services.twilio_service import TwilioService
from app.services.dynamic_data_fetcher import DynamicDataFetcher

logger = logging.getLogger(__name__)

class CallOrchestrator:
    """Orchestrates database-driven AI telecalls"""
    
    def __init__(self):
        self.twilio_service = TwilioService()
        self.data_fetcher = DynamicDataFetcher()
    
    def start_database_driven_calls(self):
        """Start making calls based on database data"""
        try:
            logger.info("📞 Starting database-driven AI telecalls...")
            
            # Get calls to be made from database
            try:
                calls_data = self.data_fetcher.get_partner_data()
                if not calls_data:
                    calls_data = []
                else:
                    # Convert single partner to list format
                    calls_data = [calls_data] if isinstance(calls_data, dict) else calls_data
            except AttributeError:
                # Fallback if method doesn't exist
                logger.warning("get_calls_to_be_done method not found, using partner data")
                calls_data = []
            
            if not calls_data:
                logger.info("📭 No calls to be made at this time")
                return True
            
            logger.info(f"📋 Found {len(calls_data)} calls to make")
            
            # Process each call
            for call_data in calls_data:
                try:
                    partner_phone = call_data.get('partner_phone')
                    partner_name = call_data.get('partner_name')
                    
                    if partner_phone:
                        logger.info(f"📞 Calling {partner_name} at {partner_phone}")
                        
                        # Make the call using Twilio
                        system_prompt = f"Call {partner_name} about Learn with Leaders programs"
                        call_result = self.twilio_service.make_call(
                            to_number=partner_phone,
                            system_prompt=system_prompt
                        )
                        
                        if call_result:
                            logger.info(f"✅ Call initiated successfully: {call_result}")
                        else:
                            logger.error(f"❌ Failed to initiate call to {partner_phone}")
                    
                    time.sleep(2)  # Brief pause between calls
                    
                except Exception as e:
                    logger.error(f"❌ Error making call: {e}")
                    continue
            
            logger.info("✅ Database-driven calls completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error in database-driven calls: {e}")
            return False
