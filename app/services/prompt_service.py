import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from app.models.data_models import AIPromptData, CallEvent

# Configure logging
logger = logging.getLogger(__name__)

class PromptGenerator:
    """AI Prompt generation service for voice calls"""
    
    def __init__(self, db_queries=None):
        """Initialize with flexible database dependency"""
        self.db_queries = db_queries
        self.caller_name = os.getenv('CALLER_NAME', 'AI Telecaller from Learn with Leaders')
        self.company_name = "Learn with Leaders"
        
        # Import default if not provided
        if not self.db_queries:
            try:
                from app.database.connection import db_queries
                self.db_queries = db_queries
            except ImportError:
                logger.warning("No database connection available for prompt generator")

class SystemPromptGenerator(PromptGenerator):
    """System prompt generator - same as PromptGenerator but different name"""
    
    def __init__(self, db_queries=None):
        super().__init__(db_queries)
    
    def generate_prompt(self, call_data: Dict[str, Any]) -> str:
        """Generate prompt from dictionary data"""
        # Convert dict to CallEvent-like object
        call_event = type('CallEvent', (), call_data)()
        return self.generate_system_prompt(call_event)
        
    def generate_system_prompt(self, call_data: CallEvent) -> str:
        """Generate a comprehensive AI system prompt for the voice call"""
        
        # Convert CallEvent to AIPromptData
        prompt_data = self._call_event_to_prompt_data(call_data)
        formatted_dates = prompt_data.get_formatted_dates()
        
        # Calculate savings
        savings_amount = prompt_data.get_savings_amount()
        savings_text = f"You can save ₹{savings_amount:,.0f} with our current discount!" if savings_amount > 0 else ""
        
        # Build the comprehensive prompt
        system_prompt = f"""
You are an AI Telecaller representing {self.company_name}. You are making an outbound voice call to {prompt_data.school_name} to promote the "{prompt_data.program_name}" educational programme.

CALLER IDENTITY:
- Name: {prompt_data.caller_name}
- Company: {self.company_name}
- Purpose: Educational programme promotion

CALL RECIPIENT:
- School: {prompt_data.school_name}
- Contact Person: {prompt_data.contact_person or "School Administrator"}
- This is an educational institution, so speak professionally and respectfully

PROGRAMME DETAILS TO PROMOTE:
- Programme Name: {prompt_data.program_name}
- Description: {prompt_data.program_description}
- Duration: {formatted_dates.get('program_start', 'TBD')} to {formatted_dates.get('program_end', 'TBD')}
- Regular Fee: ₹{prompt_data.base_fee:,.0f}
- Special Discounted Fee: ₹{prompt_data.discounted_fee:,.0f} ({prompt_data.discount_percentage}% discount)
- {savings_text}
- Total Seats Available: {prompt_data.available_seats}
- Remaining Seats: {prompt_data.available_seats}
- Registration Deadline: {formatted_dates.get('registration_deadline', 'TBD')}

ZOOM INFORMATION SESSION:
- Date: {formatted_dates.get('zoom_call_date', 'TBD')}
- Time: {formatted_dates.get('zoom_call_time', 'TBD')}
- Purpose: Detailed program overview and Q&A session

CONVERSATION GUIDELINES:
1. OPENING: Introduce yourself warmly and professionally. Mention you're calling about an exciting educational opportunity.

2. PROGRAMME PRESENTATION: 
   - Highlight the prestige and value of the programme
   - Emphasize the limited-time discount and savings
   - Mention the limited seats available
   - Focus on the educational benefits for students

3. HANDLE COMMON SCENARIOS:
   - INTERESTED: Provide zoom call details, confirm registration deadline, offer to send brochure
   - BUSY: Offer to reschedule at a convenient time, be respectful of their schedule
   - NEEDS APPROVAL: Offer to provide detailed information for decision-makers
   - LANGUAGE BARRIER: Offer to send information via email/WhatsApp in preferred language
   - NOT INTERESTED: Thank them politely and offer to send information for future reference
   - VOICEMAIL: Leave a professional message with key details and callback number

4. RESCHEDULING: If they're busy or unavailable, offer specific alternative time slots from available calendar

5. CLOSING: Always thank them for their time and provide clear next steps

CONVERSATION TONE:
- Professional but friendly
- Educational-focused (not pushy sales)
- Respectful of their time
- Enthusiastic about the educational opportunity
- Clear and concise

IMPORTANT REMINDERS:
- This is a voice call - speak naturally, don't use bullet points
- Keep responses conversational and human-like
- Ask open-ended questions to gauge interest
- Listen to their concerns and address them thoughtfully
- Always provide value and educational benefits
- Maintain professionalism throughout

RESPONSE CATEGORIES TO TRACK:
Based on the conversation, categorize the outcome as:
- INTERESTED: Shows genuine interest, wants more information
- BUSY: Available but currently occupied, requests callback
- NO_ANSWER: No response from recipient
- VOICEMAIL: Call went to voicemail system
- NEEDS_APPROVAL: Interested but needs to consult with others
- LANGUAGE_BARRIER: Communication difficulties due to language
- NOT_INTERESTED: Politely declines the opportunity
- RESCHEDULE_REQUESTED: Wants to discuss at a different time

Remember: You represent a prestigious educational company. Every interaction should reflect our commitment to quality education and professional service.
"""
        
        return system_prompt.strip()
    
    def generate_voicemail_message(self, call_data: CallEvent) -> str:
        """Generate a professional voicemail message"""
        prompt_data = self._call_event_to_prompt_data(call_data)
        formatted_dates = prompt_data.get_formatted_dates()
        savings_amount = prompt_data.get_savings_amount()
        
        voicemail_message = f"""
Hello, this is {prompt_data.caller_name}.

I'm calling {prompt_data.school_name} regarding an exciting educational opportunity - the {prompt_data.program_name}.

This prestigious programme offers exceptional value for your students, and we're currently offering a special {prompt_data.discount_percentage}% discount, saving ₹{savings_amount:,.0f} off the regular fee.

We have an information session scheduled for {formatted_dates.get('zoom_call_date', 'soon')} at {formatted_dates.get('zoom_call_time', 'TBD')} where we'll share complete programme details.

With only {prompt_data.available_seats} seats remaining and registration closing on {formatted_dates.get('registration_deadline', 'soon')}, I'd love to discuss this opportunity with you.

Please call us back or I'll try reaching you again soon. Thank you for your time, and I look forward to speaking with you about this valuable educational programme for your students.

Have a wonderful day!
"""
        
        return voicemail_message.strip()
    
    def _call_event_to_prompt_data(self, call_data: CallEvent) -> AIPromptData:
        """Convert CallEvent to AIPromptData"""
        return AIPromptData(
            school_name=getattr(call_data, 'school_name', 'School'),
            contact_person=getattr(call_data, 'contact_person', 'Administrator'),
            program_name=getattr(call_data, 'program_name', 'Educational Programme'),
            program_description=getattr(call_data, 'program_description', None) or "Premium educational programme",
            base_fee=getattr(call_data, 'base_fee', 15000),
            discounted_fee=getattr(call_data, 'discounted_fee', 12000),
            discount_percentage=getattr(call_data, 'discount_percentage', 20),
            total_seats=getattr(call_data, 'total_seats', 50),
            available_seats=getattr(call_data, 'available_seats', 25),
            zoom_call_slot=getattr(call_data, 'zoom_call_slot', None),
            program_start_date=getattr(call_data, 'start_date', None),
            program_end_date=getattr(call_data, 'end_date', None),
            registration_deadline=getattr(call_data, 'registration_deadline', None),
            caller_name=self.caller_name
        )

class PromptTemplateManager:
    """Manages different prompt templates for various scenarios"""
    
    def __init__(self):
        self.templates = {
            'interested': self._interested_follow_up,
            'busy': self._busy_reschedule,
            'needs_approval': self._needs_approval_follow_up,
            'language_barrier': self._language_barrier_response,
            'voicemail': self._voicemail_template,
            'not_interested': self._not_interested_closing
        }
    
    def get_scenario_prompt(self, scenario: str, call_data: CallEvent) -> str:
        """Get specific prompt for different call scenarios"""
        template_func = self.templates.get(scenario)
        if template_func:
            return template_func(call_data)
        return "Please continue the conversation professionally."
    
    def _interested_follow_up(self, call_data: CallEvent) -> str:
        prompt_data = self._call_event_to_prompt_data(call_data)
        formatted_dates = prompt_data.get_formatted_dates()
        
        return f"""
Great! I'm delighted to hear about your interest in the {prompt_data.program_name}. 

Here are the immediate next steps:
1. Join our information session on {formatted_dates.get('zoom_call_date', 'TBD')} at {formatted_dates.get('zoom_call_time', 'TBD')}
2. I'll send you a detailed brochure with all programme information
3. Remember, registration closes on {formatted_dates.get('registration_deadline', 'soon')}

Would you like me to reserve a spot for your school in the information session? I can also answer any immediate questions you might have.
"""
    
    def _busy_reschedule(self, call_data: CallEvent) -> str:
        return f"""
I completely understand that you're busy. Thank you for taking my call.

Would it be more convenient if I called back at a specific time? I have availability:
- Tomorrow morning between 10 AM - 12 PM
- Tomorrow afternoon between 2 PM - 4 PM
- Any other time that works better for you?

This is regarding an excellent educational opportunity for {call_data.school_name} students, and I'd love to share the details when you have just 5 minutes.

When would be the best time to reach you?
"""
    
    def _needs_approval_follow_up(self, call_data: CallEvent) -> str:
        prompt_data = self._call_event_to_prompt_data(call_data)
        formatted_dates = prompt_data.get_formatted_dates()
        
        return f"""
Absolutely! I understand that educational programme decisions require proper consideration.

I'll send you a comprehensive information packet that includes:
- Complete programme details and curriculum
- Pricing information with current discount details
- Student testimonials and success stories
- Information session details for {formatted_dates.get('zoom_call_date', 'TBD')}

Would you prefer this information via email or WhatsApp? Also, when should I follow up with you after you've had a chance to review everything with your team?
"""
    
    def _language_barrier_response(self, call_data: CallEvent) -> str:
        return f"""
No problem at all! I completely understand.

I can arrange to send all information about the {call_data.program_name} in your preferred language via:
- WhatsApp message
- Email with detailed brochure
- Have a colleague who speaks your language call you back

We want to ensure you have all the information you need to make the best decision for your students. What would work best for you?
"""
    
    def _voicemail_template(self, call_data: CallEvent) -> str:
        generator = PromptGenerator()
        return generator.generate_voicemail_message(call_data)
    
    def _not_interested_closing(self, call_data: CallEvent) -> str:
        return f"""
Thank you so much for your time, and I completely respect your decision.

I'll still send you a brief information packet about the {call_data.program_name} for your records. Educational opportunities like this might be relevant in the future.

If anything changes or if you have any questions down the line, please don't hesitate to reach out to us.

Thank you again for speaking with me today, and have a wonderful day!
"""
    
    def _call_event_to_prompt_data(self, call_data: CallEvent) -> AIPromptData:
        """Convert CallEvent to AIPromptData"""
        return AIPromptData(
            school_name=call_data.school_name,
            contact_person=call_data.contact_person,
            program_name=call_data.program_name,
            program_description=call_data.program_description or "Premium educational programme",
            base_fee=call_data.base_fee,
            discounted_fee=call_data.discounted_fee,
            discount_percentage=call_data.discount_percentage,
            zoom_call_slot=call_data.zoom_call_slot,
            start_date=call_data.start_date,
            end_date=call_data.end_date,
            registration_deadline=call_data.registration_deadline
        )

# Service instances
# Expose a generator that implements the full system API expected by tests
prompt_generator = SystemPromptGenerator()
template_manager = PromptTemplateManager()
