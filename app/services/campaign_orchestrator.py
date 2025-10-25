"""
AI Telecaller Campaign Orchestrator
Created: August 7, 2025
Purpose: Orchestrate AI telecaller campaigns with database integration and loop execution
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json

from app.database.connection import DatabaseManager, DatabaseQueries
from app.services.system_prompt_generator import SystemPromptGenerator
from app.services.twilio_service import TwilioService
from app.models.data_models import TwilioCallResponse, CallStatus

logger = logging.getLogger(__name__)

class CampaignOrchestrator:
    """Orchestrates AI telecaller campaigns with database integration"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.db_queries = DatabaseQueries(self.db_manager)
        self.prompt_generator = SystemPromptGenerator()
        self.twilio_service = TwilioService()
        
    def execute_scheduled_job(self, job_id: int) -> Dict[str, Any]:
        """
        Execute a complete scheduled job campaign
        
        Args:
            job_id: The scheduled job ID to execute
            
        Returns:
            Campaign execution results
        """
        logger.info(f"Starting execution of scheduled job {job_id}")
        
        try:
            # Get all scheduled job events for this job
            job_events = self.db_queries.get_scheduled_job_events(job_id)
            
            if not job_events:
                logger.warning(f"No pending events found for job {job_id}")
                return {
                    "success": False,
                    "message": f"No pending events found for job {job_id}",
                    "job_id": job_id,
                    "total_calls": 0,
                    "results": []
                }
            
            logger.info(f"Found {len(job_events)} events to process for job {job_id}")
            
            # Update job status to RUNNING
            self._update_job_status(job_id, "RUNNING")
            
            # Execute calls for each event
            results = []
            success_count = 0
            
            for i, event in enumerate(job_events):
                logger.info(f"Processing event {i + 1}/{len(job_events)}: {event['school_name']} - {event['program_name']}")
                
                try:
                    # Generate AI prompt with dynamic data
                    ai_prompt = self.prompt_generator.generate_prompt(event)
                    
                    # Create call metadata
                    call_metadata = {
                        "event_id": event["event_id"],
                        "job_id": job_id,
                        "school_name": event["school_name"],
                        "program_name": event["program_name"],
                        "contact_person": event["contact_person"]
                    }
                    
                    # Initiate the call
                    call_response = self.twilio_service.initiate_ai_call(
                        to_number=event["phone_number"],
                        ai_prompt=ai_prompt,
                        call_metadata=call_metadata
                    )
                    
                    # Log the call attempt
                    audit_result = self._log_call_attempt(event, call_response, ai_prompt)
                    
                    # Update event status
                    if call_response.status in ["queued", "initiated", "ringing"]:
                        self._update_event_status(event["event_id"], "IN_PROGRESS")
                        success_count += 1
                    else:
                        self._update_event_status(event["event_id"], "FAILED")
                    
                    results.append({
                        "event_id": event["event_id"],
                        "school_name": event["school_name"],
                        "phone_number": event["phone_number"],
                        "call_sid": call_response.call_sid,
                        "status": call_response.status,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # Small delay between calls to avoid overwhelming
                    import time
                    time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error processing event {event['event_id']}: {e}")
                    self._update_event_status(event["event_id"], "FAILED")
                    results.append({
                        "event_id": event["event_id"],
                        "school_name": event["school_name"],
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    })
            
            # Update job completion status
            final_status = "COMPLETED" if success_count > 0 else "FAILED"
            self._update_job_completion(job_id, final_status, len(job_events), success_count)
            
            campaign_result = {
                "success": True,
                "job_id": job_id,
                "total_calls": len(job_events),
                "successful_calls": success_count,
                "failed_calls": len(job_events) - success_count,
                "completion_time": datetime.now().isoformat(),
                "results": results
            }
            
            logger.info(f"Completed job {job_id}: {success_count}/{len(job_events)} calls successful")
            return campaign_result
            
        except Exception as e:
            logger.error(f"Fatal error executing job {job_id}: {e}")
            self._update_job_status(job_id, "FAILED")
            return {
                "success": False,
                "job_id": job_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def execute_single_call(self, event_id: int) -> Dict[str, Any]:
        """
        Execute a single call event
        
        Args:
            event_id: The scheduled job event ID to execute
            
        Returns:
            Call execution result
        """
        logger.info(f"Executing single call for event {event_id}")
        
        try:
            # Get the specific event
            events = self.db_queries.get_scheduled_job_events()
            event = next((e for e in events if e["event_id"] == event_id), None)
            
            if not event:
                return {
                    "success": False,
                    "message": f"Event {event_id} not found or not pending",
                    "event_id": event_id
                }
            
            # Generate AI prompt
            ai_prompt = self.prompt_generator.generate_prompt(event)
            
            # Create call metadata
            call_metadata = {
                "event_id": event["event_id"],
                "job_id": event["job_id"],
                "school_name": event["school_name"],
                "program_name": event["program_name"],
                "contact_person": event["contact_person"]
            }
            
            # Initiate the call
            call_response = self.twilio_service.initiate_ai_call(
                to_number=event["phone_number"],
                ai_prompt=ai_prompt,
                call_metadata=call_metadata
            )
            
            # Log the call
            self._log_call_attempt(event, call_response, ai_prompt)
            
            # Update status
            if call_response.status in ["queued", "initiated", "ringing"]:
                self._update_event_status(event_id, "IN_PROGRESS")
            else:
                self._update_event_status(event_id, "FAILED")
            
            return {
                "success": True,
                "event_id": event_id,
                "school_name": event["school_name"],
                "call_sid": call_response.call_sid,
                "status": call_response.status,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error executing single call {event_id}: {e}")
            return {
                "success": False,
                "event_id": event_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def handle_call_completion(self, call_sid: str, call_status: str, call_outcome: str = None) -> Dict[str, Any]:
        """
        Handle call completion webhook from Twilio
        
        Args:
            call_sid: Twilio call SID
            call_status: Final call status
            call_outcome: AI conversation outcome (INTERESTED, BUSY, etc.)
            
        Returns:
            Processing result
        """
        logger.info(f"Handling call completion for {call_sid}: {call_status}")
        
        try:
            # Find the event associated with this call
            # This would typically be done by querying audit_log for the call_sid
            # For now, we'll update based on the call_sid
            
            # Update event status based on call result
            if call_status == "completed":
                if call_outcome == "BUSY":
                    # Schedule a reschedule for busy contacts
                    next_slot = self._get_next_available_slot()
                    if next_slot:
                        self._schedule_reschedule(call_sid, next_slot)
                        logger.info(f"Rescheduled busy contact {call_sid} to {next_slot}")
                
                # Log the completion
                self._log_call_completion(call_sid, call_status, call_outcome)
            
            return {
                "success": True,
                "call_sid": call_sid,
                "status": call_status,
                "outcome": call_outcome,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error handling call completion {call_sid}: {e}")
            return {
                "success": False,
                "call_sid": call_sid,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_campaign_status(self, job_id: int) -> Dict[str, Any]:
        """Get the status of a campaign"""
        try:
            # Get job details and events
            events = self.db_queries.get_scheduled_job_events(job_id)
            
            if not events:
                return {"success": False, "message": "Job not found"}
            
            # Calculate statistics
            total_events = len(events)
            pending_events = len([e for e in events if e["call_status"] == "PENDING"])
            in_progress_events = len([e for e in events if e["call_status"] == "IN_PROGRESS"])
            completed_events = len([e for e in events if e["call_status"] == "COMPLETED"])
            failed_events = len([e for e in events if e["call_status"] == "FAILED"])
            
            return {
                "success": True,
                "job_id": job_id,
                "total_events": total_events,
                "pending": pending_events,
                "in_progress": in_progress_events,
                "completed": completed_events,
                "failed": failed_events,
                "events": events
            }
            
        except Exception as e:
            logger.error(f"Error getting campaign status {job_id}: {e}")
            return {"success": False, "error": str(e)}
    
    # Private helper methods
    
    def _update_job_status(self, job_id: int, status: str):
        """Update scheduled job status"""
        query = f"""
        UPDATE {self.db_queries.schema}.scheduled_jobs 
        SET status = %s, updated_at = NOW() 
        WHERE id = %s
        """
        self.db_manager.execute_query(query, (status, job_id), fetch='none')
    
    def _update_job_completion(self, job_id: int, status: str, total_calls: int, success_calls: int):
        """Update job completion details"""
        query = f"""
        UPDATE {self.db_queries.schema}.scheduled_jobs 
        SET status = %s, total_calls = %s, completed_calls = %s, 
            success_calls = %s, updated_at = NOW() 
        WHERE id = %s
        """
        self.db_manager.execute_query(query, (status, total_calls, total_calls, success_calls, job_id), fetch='none')
    
    def _update_event_status(self, event_id: int, status: str):
        """Update scheduled job event status"""
        query = f"""
        UPDATE {self.db_queries.schema}.scheduled_job_events 
        SET call_status = %s, updated_at = NOW() 
        WHERE id = %s
        """
        self.db_manager.execute_query(query, (status, event_id), fetch='none')
    
    def _log_call_attempt(self, event: Dict[str, Any], call_response: TwilioCallResponse, ai_prompt: str) -> bool:
        """Log call attempt to audit table"""
        try:
            query = f"""
            INSERT INTO {self.db_queries.schema}.audit_log 
            (scheduled_job_event_id, action, details, call_sid, phone_number, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
            """
            
            details = {
                "school_name": event["school_name"],
                "program_name": event["program_name"],
                "ai_prompt_length": len(ai_prompt),
                "call_metadata": {
                    "contact_person": event["contact_person"],
                    "discounted_fee": str(event.get("discounted_fee", 0)),
                    "available_seats": event.get("available_seats", 0)
                }
            }
            
            self.db_manager.execute_query(
                query, 
                (event["event_id"], "CALL_INITIATED", json.dumps(details), 
                 call_response.call_sid, event["phone_number"], call_response.status),
                fetch='none'
            )
            return True
            
        except Exception as e:
            logger.error(f"Error logging call attempt: {e}")
            return False
    
    def _log_call_completion(self, call_sid: str, status: str, outcome: str):
        """Log call completion"""
        try:
            query = f"""
            INSERT INTO {self.db_queries.schema}.audit_log 
            (call_sid, action, details, status, created_at)
            VALUES (%s, %s, %s, %s, NOW())
            """
            
            details = {
                "call_outcome": outcome,
                "completion_time": datetime.now().isoformat()
            }
            
            self.db_manager.execute_query(
                query,
                (call_sid, "CALL_COMPLETED", json.dumps(details), status),
                fetch='none'
            )
            
        except Exception as e:
            logger.error(f"Error logging call completion: {e}")
    
    def _get_next_available_slot(self) -> Optional[str]:
        """Get next available calendar slot"""
        try:
            slots = self.db_queries.get_available_slots(1)
            return slots[0]["slot_datetime"].isoformat() if slots else None
        except Exception as e:
            logger.error(f"Error getting next available slot: {e}")
            return None
    
    def _schedule_reschedule(self, call_sid: str, reschedule_slot: str):
        """Schedule a reschedule for a busy contact"""
        try:
            query = f"""
            UPDATE {self.db_queries.schema}.scheduled_job_events 
            SET reschedule_slot = %s, outcome = 'BUSY_RESCHEDULED', updated_at = NOW()
            WHERE id = (
                SELECT scheduled_job_event_id FROM {self.db_queries.schema}.audit_log 
                WHERE call_sid = %s LIMIT 1
            )
            """
            self.db_manager.execute_query(query, (reschedule_slot, call_sid), fetch='none')
            
        except Exception as e:
            logger.error(f"Error scheduling reschedule: {e}")

# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_campaign():
        orchestrator = CampaignOrchestrator()
        
        # Test executing a campaign
        result = await orchestrator.execute_scheduled_job(1)
        print("Campaign Result:")
        print(json.dumps(result, indent=2))
    
    # Run test
    # asyncio.run(test_campaign())
