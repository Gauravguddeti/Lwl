#!/usr/bin/env python3
"""
Production Integration: getcallstobedone with AI Telecaller System
Shows how to integrate the DBA function with your existing telecaller
"""

import logging
from datetime import datetime
from typing import Dict, Any, List
from app.services.ivr_service import ivr_service
from app.database.postgres_data_access import db_access

logger = logging.getLogger(__name__)

class ProductionIVRIntegration:
    """Production-ready integration of getcallstobedone with AI telecaller"""
    
    def __init__(self):
        self.ivr_service = ivr_service
        self.db = db_access
    
    def execute_scheduled_calls(self, scheduled_job_id: int) -> Dict[str, Any]:
        """
        Execute all calls for a scheduled job using getcallstobedone
        
        Args:
            scheduled_job_id: ID of the scheduled job to process
            
        Returns:
            Summary of call execution results
        """
        try:
            logger.info(f"Starting execution of scheduled job {scheduled_job_id}")
            
            # Get all job events for this scheduled job
            job_events = self.db.get_scheduled_job_events(job_id=scheduled_job_id)
            
            if not job_events:
                logger.warning(f"No job events found for scheduled_job_id: {scheduled_job_id}")
                return {
                    'status': 'no_events',
                    'scheduled_job_id': scheduled_job_id,
                    'total_events': 0,
                    'calls_processed': 0,
                    'errors': []
                }
            
            results = {
                'status': 'processing',
                'scheduled_job_id': scheduled_job_id,
                'total_events': len(job_events),
                'calls_processed': 0,
                'successful_calls': [],
                'failed_calls': [],
                'errors': []
            }
            
            # Process each job event
            for event in job_events:
                try:
                    call_result = self._process_single_call_event(event, scheduled_job_id)
                    
                    if call_result['success']:
                        results['successful_calls'].append(call_result)
                        results['calls_processed'] += 1
                    else:
                        results['failed_calls'].append(call_result)
                        results['errors'].append(call_result.get('error'))
                        
                except Exception as e:
                    error_msg = f"Error processing event {event.get('scheduled_job_event_id')}: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
                    results['failed_calls'].append({
                        'event_id': event.get('scheduled_job_event_id'),
                        'error': error_msg,
                        'success': False
                    })
            
            # Update final status
            if results['calls_processed'] == results['total_events']:
                results['status'] = 'completed'
            elif results['calls_processed'] > 0:
                results['status'] = 'partial_success'
            else:
                results['status'] = 'failed'
            
            logger.info(f"Completed scheduled job {scheduled_job_id}: {results['calls_processed']}/{results['total_events']} calls processed")
            return results
            
        except Exception as e:
            logger.error(f"Error executing scheduled calls: {str(e)}")
            return {
                'status': 'error',
                'scheduled_job_id': scheduled_job_id,
                'error': str(e),
                'calls_processed': 0
            }
    
    def _process_single_call_event(self, event: Dict[str, Any], scheduled_job_id: int) -> Dict[str, Any]:
        """
        Process a single call event using getcallstobedone
        
        Args:
            event: Job event data from scheduled_job_events
            scheduled_job_id: ID of the scheduled job
            
        Returns:
            Result of call processing
        """
        try:
            # Extract event details
            contact_name = event.get('contact', 'Unknown Contact')
            partner_name = event.get('partner_name', 'Unknown Partner')
            scheduled_job_event_id = event.get('scheduled_job_event_id')
            callback_time = event.get('job_datetime', datetime.now())
            
            logger.info(f"Processing call for {contact_name} at {partner_name}")
            
            # Get system prompts
            prompts = self.db.get_system_prompts(is_active=True)
            if not prompts:
                raise Exception("No active system prompts found")
            
            system_prompt = prompts[0]  # Use first active prompt
            
            # Format callback time
            if isinstance(callback_time, datetime):
                callback_time_str = callback_time.strftime('%Y-%m-%d %H:%M:%S')
            else:
                callback_time_str = str(callback_time)
            
            # Call getcallstobedone function
            function_results = self.db.call_getcallstobedone(
                contact_name=contact_name,
                partner_name=partner_name,
                scheduled_job_event_id=scheduled_job_event_id,
                scheduled_job_id=scheduled_job_id,
                callback_time=callback_time_str,
                system_prompt_id=system_prompt['system_prompt_id'],
                system_prompt=system_prompt['system_prompt'],
                ai_model_name='gpt-4'
            )
            
            # Process the function results
            if function_results:
                # Get the first result (assuming function returns one row per call)
                call_data = function_results[0]
                
                # Get full IVR context for AI telecaller
                ivr_context = self.ivr_service.get_ivr_context_for_call(call_data)
                
                # Here you would integrate with your AI telecaller system
                # For now, we'll just log the prepared context
                logger.info(f"IVR context prepared for {contact_name}")
                
                # This is where you would call your actual AI telecaller
                # ai_call_result = self._make_ai_call(ivr_context)
                
                return {
                    'success': True,
                    'contact_name': contact_name,
                    'partner_name': partner_name,
                    'scheduled_job_event_id': scheduled_job_event_id,
                    'function_results': function_results,
                    'ivr_context': ivr_context,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                logger.warning(f"No results from getcallstobedone for {contact_name}")
                return {
                    'success': False,
                    'contact_name': contact_name,
                    'error': 'No results from getcallstobedone function',
                    'scheduled_job_event_id': scheduled_job_event_id
                }
                
        except Exception as e:
            logger.error(f"Error processing call event: {str(e)}")
            return {
                'success': False,
                'contact_name': event.get('contact', 'Unknown'),
                'error': str(e),
                'scheduled_job_event_id': event.get('scheduled_job_event_id')
            }
    
    def _make_ai_call(self, ivr_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make the actual AI call using your existing telecaller system
        This is where you would integrate with ai_ivr_telecaller_system.py
        
        Args:
            ivr_context: Complete context for the call
            
        Returns:
            Result of the AI call
        """
        # This is a placeholder for your actual AI telecaller integration
        # You would import and use your AI telecaller here
        
        try:
            # Example integration (you would adapt this to your actual system):
            # from ai_ivr_telecaller_system import AITelecaller
            # telecaller = AITelecaller()
            # call_result = telecaller.make_call(ivr_context)
            
            # For now, just return a mock result
            return {
                'success': True,
                'call_id': f"CALL_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'duration': '00:02:45',
                'status': 'completed',
                'transcript': 'Mock call transcript...',
                'sentiment': 'positive'
            }
            
        except Exception as e:
            logger.error(f"Error making AI call: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_upcoming_scheduled_jobs(self, hours_ahead: int = 24) -> List[Dict[str, Any]]:
        """
        Get scheduled jobs that need to be executed in the next N hours
        
        Args:
            hours_ahead: How many hours ahead to look for scheduled jobs
            
        Returns:
            List of upcoming scheduled jobs
        """
        try:
            # Get all scheduled jobs
            all_jobs = self.db.get_scheduled_jobs()
            
            # Filter for upcoming jobs (this would depend on your schema)
            upcoming_jobs = []
            current_time = datetime.now()
            
            for job in all_jobs:
                job_datetime = job.get('datetime')
                if isinstance(job_datetime, datetime):
                    time_diff = (job_datetime - current_time).total_seconds() / 3600
                    if 0 <= time_diff <= hours_ahead:
                        upcoming_jobs.append(job)
            
            logger.info(f"Found {len(upcoming_jobs)} upcoming jobs in next {hours_ahead} hours")
            return upcoming_jobs
            
        except Exception as e:
            logger.error(f"Error getting upcoming scheduled jobs: {str(e)}")
            return []

# Global instance for production use
production_ivr = ProductionIVRIntegration()
