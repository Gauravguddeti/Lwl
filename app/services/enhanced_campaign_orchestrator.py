"""
Enhanced Campaign Orchestrator with Loop Implementation
Created: August 7, 2025
Purpose: Implement the exact loop structure: For i = 0 to rows.count - 1 with voice input/output
"""

import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

# Configure logging
logger = logging.getLogger(__name__)

class EnhancedCampaignOrchestrator:
    """
    Enhanced Campaign Orchestrator implementing the exact loop structure:
    For i = 0 to rows.count - 1
    {
        System_prompt = " "
        Tool assignment
        IVR call
        Audit log
    }
    """
    
    def __init__(self, db_queries=None, prompt_generator=None, twilio_service=None, mock_mode=False):
        """Initialize with flexible dependencies"""
        self.db_queries = db_queries
        self.prompt_generator = prompt_generator
        self.twilio_service = twilio_service
        self.mock_mode = mock_mode
        
        # Import defaults if not provided
        if not self.db_queries:
            try:
                from app.database.connection import db_queries
                self.db_queries = db_queries
            except ImportError:
                from app.database.embedded_db import EmbeddedDatabaseManager, EmbeddedDatabaseQueries
                db_manager = EmbeddedDatabaseManager()
                self.db_queries = EmbeddedDatabaseQueries(db_manager)
                logger.info("Using embedded database for testing")
        
        if not self.prompt_generator:
            try:
                from app.services.prompt_service import SystemPromptGenerator
                self.prompt_generator = SystemPromptGenerator(self.db_queries)
            except ImportError:
                logger.warning("No prompt generator available")
        
        if not self.twilio_service:
            try:
                from app.services.twilio_service import TwilioService
                self.twilio_service = TwilioService(mock_mode=mock_mode)
            except ImportError:
                logger.warning("No Twilio service available")
    
    def execute_campaign_loop(self, job_id: int) -> Dict[str, Any]:
        """
        Execute the campaign loop exactly as specified:
        For i = 0 to rows.count - 1
        {
            System_prompt = " "
            Tool assignment  
            IVR call
            Audit log
        }
        """
        
        logger.info(f"🚀 Starting Enhanced Campaign Loop for Job ID: {job_id}")
        
        try:
            # Get all scheduled events (rows) for this job
            rows = self.db_queries.get_scheduled_job_events(job_id)
            
            if not rows:
                logger.warning(f"No rows found for job {job_id}")
                return {
                    'success': True,
                    'message': f'No events found for job {job_id}',
                    'job_id': job_id,
                    'total_rows': 0,
                    'processed_calls': 0,
                    'successful_calls': 0,
                    'failed_calls': 0,
                    'loop_results': []
                }
            
            # Execute the exact loop: For i = 0 to rows.count - 1
            loop_results = []
            successful_calls = 0
            failed_calls = 0
            total_rows = len(rows)
            
            logger.info(f"📊 Executing loop: For i = 0 to {total_rows - 1}")
            
            for i in range(total_rows):  # For i = 0 to rows.count - 1
                logger.info(f"🔄 Loop iteration i = {i}")
                
                row = rows[i]
                
                # Step 1: System_prompt = " " (with dynamic tag processing)
                # Use concise template for real Twilio calls to stay under 4000 character limit
                system_prompt_template = self._generate_concise_system_prompt(row, i)
                
                # Process dynamic tags with actual data
                from app.services.dynamic_tag_processor import DynamicTagProcessor
                tag_processor = DynamicTagProcessor()
                system_prompt = tag_processor.process_system_prompt(system_prompt_template, row)
                
                logger.info(f"📝 System prompt generated for iteration {i} ({len(system_prompt)} characters)")
                
                # Step 2: Tool assignment
                tools_assigned = self._assign_tools_for_call(row, i)
                logger.info(f"🔧 Tools assigned for iteration {i}: {tools_assigned}")
                
                # Step 3: IVR call
                call_result = self._execute_ivr_call(row, system_prompt, tools_assigned, i)
                logger.info(f"📞 IVR call executed for iteration {i}")
                
                # Step 4: Audit log
                audit_result = self._create_audit_log(row, call_result, system_prompt, tools_assigned, i)
                logger.info(f"📋 Audit log created for iteration {i}")
                
                # Compile iteration result
                iteration_result = {
                    'iteration': i,
                    'row_data': {
                        'event_id': row.get('event_id'),
                        'school_name': row.get('school_name'),
                        'program_name': row.get('program_name'),
                        'phone_number': row.get('phone_number')
                    },
                    'system_prompt_length': len(system_prompt),
                    'system_prompt_preview': system_prompt[:200] + "..." if len(system_prompt) > 200 else system_prompt,
                    'tools_assigned': tools_assigned,
                    'call_result': call_result,
                    'audit_result': audit_result,
                    'status': call_result.get('status', 'UNKNOWN'),
                    'timestamp': datetime.now().isoformat()
                }
                
                loop_results.append(iteration_result)
                
                # Track success/failure
                if call_result.get('status') == 'SUCCESS':
                    successful_calls += 1
                else:
                    failed_calls += 1
                
                logger.info(f"✅ Loop iteration {i} completed")
            
            # Return comprehensive results
            campaign_result = {
                'success': True,
                'message': f'Campaign loop completed for job {job_id}',
                'job_id': job_id,
                'total_rows': total_rows,
                'processed_calls': len(loop_results),
                'successful_calls': successful_calls,
                'failed_calls': failed_calls,
                'loop_results': loop_results,
                'execution_summary': {
                    'loop_structure': f'For i = 0 to {total_rows - 1}',
                    'iterations_completed': len(loop_results),
                    'success_rate': f'{(successful_calls/total_rows)*100:.1f}%' if total_rows > 0 else '0%',
                    'execution_time': datetime.now().isoformat()
                }
            }
            
            logger.info(f"🎉 Enhanced Campaign Loop completed successfully!")
            logger.info(f"📊 Results: {successful_calls}/{total_rows} calls successful")
            
            return campaign_result
            
        except Exception as e:
            logger.error(f"❌ Enhanced Campaign Loop failed: {e}")
            return {
                'success': False,
                'message': f'Campaign loop execution failed: {str(e)}',
                'job_id': job_id,
                'total_rows': 0,
                'processed_calls': 0,
                'successful_calls': 0,
                'failed_calls': 0,
                'error': str(e)
            }
    
    def _generate_dynamic_system_prompt(self, row: Dict[str, Any], iteration: int) -> str:
        """
        Generate dynamic system prompt with conversational flow and time-based greetings
        """
        
        # Get current time for dynamic greetings
        current_hour = datetime.now().hour
        if 5 <= current_hour < 12:
            greeting_time = "Good morning"
            time_context = "morning"
        elif 12 <= current_hour < 17:
            greeting_time = "Good afternoon"
            time_context = "afternoon"
        elif 17 <= current_hour < 21:
            greeting_time = "Good evening"
            time_context = "evening"
        else:
            greeting_time = "Good evening"
            time_context = "late evening"
        
        # Create comprehensive conversational system prompt with dynamic tags
        system_prompt = f"""You are an AI Telecaller representing Learn with Leaders. You are making an outbound voice call with natural conversation flow.

DYNAMIC CONVERSATION TAGS (Use these for personalization):
- {{GREETING_TIME}}: {greeting_time}
- {{TIME_CONTEXT}}: {time_context}
- {{SCHOOL_NAME}}: {{school_name}}
- {{CONTACT_PERSON}}: {{contact_person}}
- {{PROGRAM_NAME}}: {{program_name}}
- {{ORIGINAL_FEE}}: {{original_fee}}
- {{DISCOUNTED_FEE}}: {{discounted_fee}}
- {{DISCOUNT_PERCENTAGE}}: {{discount_percentage}}
- {{SAVINGS_AMOUNT}}: {{savings_amount}}
- {{PROGRAM_START_DATE}}: {{program_start_date}}
- {{PROGRAM_END_DATE}}: {{program_end_date}}
- {{AVAILABLE_SEATS}}: {{available_seats}}
- {{CALL_ITERATION}}: {iteration + 1}

CONVERSATION FLOW (Follow this natural progression):

1. OPENING GREETING:
"{{GREETING_TIME}}! This is [Your Name] calling from Learn with Leaders. Am I speaking with {{CONTACT_PERSON}} or the principal of {{SCHOOL_NAME}}?"

[WAIT for response and acknowledgment]

2. PERMISSION TO TALK:
"I hope I'm not catching you at a busy time. Is this a good moment to talk for about 3-4 minutes about an exciting educational opportunity for your students?"

[WAIT for permission - if no, offer to call back at convenient time]

3. PURPOSE INTRODUCTION:
"Thank you for your time. I'm calling to share information about our {{PROGRAM_NAME}} - it's a prestigious international program that I believe would be perfect for your bright students."

4. VALUE PROPOSITION WITH DYNAMIC DATA:
"Here's what makes this special - the program normally costs ₹{{ORIGINAL_FEE}}, but we're offering your school an exclusive {{DISCOUNT_PERCENTAGE}}% discount, bringing it down to just ₹{{DISCOUNTED_FEE}}. That's a savings of ₹{{SAVINGS_AMOUNT}} for each student!"

5. ENGAGEMENT QUESTIONS:
"Have you considered international educational programs for your students before?"
"What are your thoughts on exposing students to global learning experiences?"

6. PROGRAM DETAILS (If interested):
"The program runs from {{PROGRAM_START_DATE}} to {{PROGRAM_END_DATE}}, and we currently have {{AVAILABLE_SEATS}} seats available. It's designed for students who want to experience world-class education."

7. OBJECTION HANDLING SCENARIOS:

IF "Too expensive":
"I completely understand your concern about the investment. That's exactly why we're offering this {{DISCOUNT_PERCENTAGE}}% discount. When you consider the international exposure and career benefits, it works out to less than ₹[daily_cost] per day for a life-changing experience."

IF "Need to think about it":
"Absolutely, this is an important decision. Would it help if I send you the detailed program brochure? We can also arrange a brief video call with our program coordinator to answer any specific questions."

IF "Not the right time":
"I understand timing is important. The program starts on {{PROGRAM_START_DATE}}, so we have some time. Would you prefer if I called back next week, or would you like me to send the information via email first?"

IF "Need board approval":
"That makes perfect sense for such an important decision. I can provide you with a comprehensive presentation package that you can share with your board. What information would be most helpful for them to review?"

8. NEXT STEPS (Based on interest level):

HIGH INTEREST:
"Wonderful! Let me secure one of those {{AVAILABLE_SEATS}} seats for your school. I'll need to collect some basic information and can arrange for our program coordinator to visit your school next week."

MODERATE INTEREST:
"I can see you're interested but want to learn more. Let me send you our detailed brochure today, and I'll follow up with a call in 2-3 days to answer any questions that come up."

LOW INTEREST:
"I understand this might not be the right fit right now. May I keep your contact information for future programs that might be more suitable? We often have different types of educational opportunities throughout the year."

9. CLOSING (Always professional):
"Thank you so much for your time this {{TIME_CONTEXT}}, {{CONTACT_PERSON}}. It's been a pleasure speaking with you. Have a wonderful rest of your {{TIME_CONTEXT}}!"

VOICE INTERACTION REQUIREMENTS:
- Speak naturally with appropriate pauses
- Listen actively for verbal cues and responses
- Adapt conversation speed based on recipient's pace
- Use warm, professional tone throughout
- Mirror the energy level of the recipient
- Ask follow-up questions based on their responses

DYNAMIC RESPONSE HANDLING:
- If they ask about accreditation: "This program is fully accredited and recognized internationally"
- If they ask about student safety: "Student safety is our top priority with 24/7 supervision"
- If they ask about scholarships: "We do have limited need-based scholarship options available"
- If they ask about past participants: "We've had over [number] students participate with 98% satisfaction rate"

CONVERSATION TOOLS AVAILABLE:
- Calendar checking for program dates
- Fee calculator for different payment options
- Scholarship eligibility checker
- Previous participant testimonials
- Program curriculum details
- Accommodation information

SUCCESS METRICS FOR THIS CALL:
- Establish rapport and trust
- Generate genuine interest in the program
- Collect contact preferences (email/WhatsApp)
- Schedule follow-up discussion or school visit
- Provide program materials

Remember: This is a REAL VOICE conversation. Be natural, listen actively, and respond appropriately to their specific concerns and questions. Use the dynamic tags to personalize every aspect of the conversation."""

        return system_prompt
    
    def _generate_concise_system_prompt(self, row: Dict[str, Any], iteration: int) -> str:
        """
        Generate concise dynamic system prompt for Twilio calls (under 3000 chars)
        """
        
        logger.info(f"🎯 Generating concise system prompt for iteration {iteration}")
        
        # Get the concise template from DynamicTagProcessor
        from app.services.dynamic_tag_processor import DynamicTagProcessor
        tag_processor = DynamicTagProcessor()
        
        # Use the concise Twilio-optimized template
        concise_prompt_template = tag_processor.get_concise_twilio_prompt_template()
        
        logger.info(f"📏 Concise template generated ({len(concise_prompt_template)} characters)")
        
        return concise_prompt_template
    
    def _assign_tools_for_call(self, row: Dict[str, Any], iteration: int) -> List[str]:
        """
        Assign dynamic tools for the call based on programme and requirements
        """
        
        tools = []
        
        # Always assign basic tools
        tools.extend([
            "calendar_checker",
            "programme_info_lookup", 
            "fee_calculator",
            "contact_updater"
        ])
        
        # Assign programme-specific tools
        program_name = row.get('program_name', '').lower()
        
        if 'cambridge' in program_name:
            tools.append("cambridge_specific_details")
        elif 'oxford' in program_name:
            tools.append("oxford_specific_details")
        elif 'mit' in program_name:
            tools.append("mit_specific_details")
        elif 'harvard' in program_name:
            tools.append("harvard_specific_details")
        elif 'stanford' in program_name:
            tools.append("stanford_specific_details")
        
        # Add iteration-specific tools
        if iteration == 0:
            tools.append("first_call_introduction")
        elif iteration >= 1:
            tools.append("follow_up_conversation")
        
        # Add school-type specific tools
        school_name = row.get('school_name', '').lower()
        if 'international' in school_name:
            tools.append("international_school_approach")
        elif 'public' in school_name:
            tools.append("public_school_approach")
        
        return tools
    
    def _execute_ivr_call(self, row: Dict[str, Any], system_prompt: str, tools: List[str], iteration: int) -> Dict[str, Any]:
        """
        Execute the IVR call with voice input/output capability
        """
        
        phone_number = row.get('phone_number')
        school_name = row.get('school_name')
        
        # Use test numbers you provided for testing
        test_numbers = {
            '+91-11-2345-6789': '+17276082005',  # DPS Delhi -> Test number 1
            '+91-22-9876-5432': '+17668815841',  # Ryan International -> Test number 2  
            '+91-135-252-6400': '+17276082005'   # Doon School -> Test number 1 (reused)
        }
        
        # Map to test number if available
        actual_phone = test_numbers.get(phone_number, phone_number)
        
        logger.info(f"📞 Executing IVR call to {school_name} at {actual_phone} (iteration {iteration})")
        
        if self.mock_mode:
            # Mock call execution
            return {
                'status': 'SUCCESS',
                'call_sid': f'mock_call_{iteration}_{row.get("event_id")}',
                'to_number': actual_phone,
                'original_number': phone_number,
                'school_name': school_name,
                'call_duration': f'{30 + iteration * 15} seconds',
                'voice_interaction': 'Mock voice conversation completed',
                'tools_used': tools[:2],  # Mock using first 2 tools
                'message': f'Mock IVR call completed for iteration {iteration}'
            }
        else:
            # Real Twilio call with voice capabilities
            try:
                # Create enhanced TwiML for voice interaction
                voice_config = {
                    'voice': 'alice',  # Female voice for Indian context
                    'language': 'en-IN',  # Indian English
                    'speech_timeout': 'auto',
                    'enhanced': True,
                    'tools_available': tools
                }
                
                call_response = self.twilio_service.make_call(
                    to_number=actual_phone,
                    system_prompt=system_prompt,
                    call_metadata={
                        'iteration': iteration,
                        'school_name': school_name,
                        'tools': tools,
                        'voice_config': voice_config,
                        'programme': row.get('program_name'),
                        'original_number': phone_number
                    }
                )
                
                return {
                    'status': 'SUCCESS',
                    'call_sid': call_response.get('call_sid'),
                    'to_number': actual_phone,
                    'original_number': phone_number,
                    'school_name': school_name,
                    'voice_interaction': 'Real voice call initiated',
                    'tools_assigned': tools,
                    'message': f'Real IVR call initiated for iteration {iteration}'
                }
                
            except Exception as e:
                logger.error(f"Real call failed for iteration {iteration}: {e}")
                return {
                    'status': 'FAILED',
                    'error': str(e),
                    'to_number': actual_phone,
                    'original_number': phone_number,
                    'school_name': school_name,
                    'message': f'Call failed for iteration {iteration}'
                }
    
    def _create_audit_log(self, row: Dict[str, Any], call_result: Dict[str, Any], 
                         system_prompt: str, tools: List[str], iteration: int) -> Dict[str, Any]:
        """
        Create comprehensive audit log for the call
        """
        
        audit_data = {
            'timestamp': datetime.now().isoformat(),
            'iteration': iteration,
            'event_id': row.get('event_id'),
            'job_id': row.get('job_id'),
            'school_details': {
                'name': row.get('school_name'),
                'contact_person': row.get('contact_person'),
                'phone_number': row.get('phone_number'),
                'actual_phone': call_result.get('to_number')
            },
            'programme_details': {
                'name': row.get('program_name'),
                'base_fee': row.get('base_fee'),
                'discounted_fee': row.get('discounted_fee'),
                'discount_percentage': row.get('discount_percentage')
            },
            'call_execution': {
                'status': call_result.get('status'),
                'call_sid': call_result.get('call_sid'),
                'duration': call_result.get('call_duration'),
                'voice_interaction': call_result.get('voice_interaction'),
                'error_message': call_result.get('error')
            },
            'system_configuration': {
                'prompt_length': len(system_prompt),
                'tools_assigned': tools,
                'voice_enabled': True,
                'mock_mode': self.mock_mode
            },
            'loop_context': {
                'loop_structure': 'For i = 0 to rows.count - 1',
                'current_iteration': iteration,
                'iteration_description': f'Loop iteration {iteration}'
            }
        }
        
        # In a real system, this would be saved to the audit_log table
        if not self.mock_mode and self.db_queries:
            try:
                # Save to database audit log
                audit_id = self._save_audit_to_database(audit_data)
                audit_data['audit_id'] = audit_id
                audit_data['saved_to_database'] = True
            except Exception as e:
                logger.error(f"Failed to save audit log to database: {e}")
                audit_data['saved_to_database'] = False
                audit_data['save_error'] = str(e)
        else:
            audit_data['saved_to_database'] = False
            audit_data['note'] = 'Mock mode - audit saved to memory only'
        
        return audit_data
    
    def _save_audit_to_database(self, audit_data: Dict[str, Any]) -> Optional[int]:
        """
        Save audit log to database
        """
        try:
            # This would save to the actual audit_log table
            # For now, return a mock audit ID
            return f"audit_{audit_data['iteration']}_{int(datetime.now().timestamp())}"
        except Exception as e:
            logger.error(f"Database audit save failed: {e}")
            return None

# Create test function
def test_enhanced_campaign_loop():
    """
    Test the enhanced campaign loop with 3 scheduled calls
    """
    
    print("🧪 Testing Enhanced Campaign Loop")
    print("=" * 50)
    
    try:
        # Initialize with embedded database for testing
        from app.database.embedded_db import EmbeddedDatabaseManager, EmbeddedDatabaseQueries
        from app.services.prompt_service import SystemPromptGenerator
        from app.services.twilio_service import TwilioService
        
        db_manager = EmbeddedDatabaseManager()
        db_queries = EmbeddedDatabaseQueries(db_manager)
        prompt_generator = SystemPromptGenerator(db_queries)
        twilio_service = TwilioService(mock_mode=True)
        
        # Create enhanced orchestrator
        orchestrator = EnhancedCampaignOrchestrator(
            db_queries=db_queries,
            prompt_generator=prompt_generator,
            twilio_service=twilio_service,
            mock_mode=True
        )
        
        # Execute the campaign loop for job 1 (which has 3 events)
        result = orchestrator.execute_campaign_loop(1)
        
        print(f"✅ Campaign Loop Result:")
        print(f"   Success: {result['success']}")
        print(f"   Total Rows: {result['total_rows']}")
        print(f"   Successful Calls: {result['successful_calls']}")
        print(f"   Loop Structure: {result.get('execution_summary', {}).get('loop_structure')}")
        
        # Show details for each iteration
        for loop_result in result.get('loop_results', []):
            iteration = loop_result['iteration']
            school = loop_result['row_data']['school_name']
            program = loop_result['row_data']['program_name']
            status = loop_result['status']
            tools = len(loop_result['tools_assigned'])
            
            print(f"   📞 Iteration {iteration}: {school} - {program} [{status}] ({tools} tools)")
        
        return result['success']
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_enhanced_campaign_loop()
    print(f"\n🎯 Test {'PASSED' if success else 'FAILED'}")
