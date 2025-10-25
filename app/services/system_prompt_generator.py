"""
AI Telecaller System Prompt Generator
Created: August 7, 2025
Purpose: Generate dynamic AI prompts with database-injected data for telecaller campaigns
"""

import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class SystemPromptGenerator:
    """Generates dynamic system prompts for AI telecaller with database data injection"""
    
    def __init__(self):
        self.base_prompt_template = self._get_base_prompt_template()
    
    def generate_prompt(self, call_data: Dict[str, Any]) -> str:
        """
        Generate a complete system prompt with dynamic data injection
        
        Args:
            call_data: Dictionary containing school, program, and event details from database
            
        Returns:
            Complete system prompt string ready for AI telecaller
        """
        try:
            # Extract data from database result
            school_name = call_data.get('school_name', 'the school')
            contact_person = call_data.get('contact_person', 'the coordinator')
            program_name = call_data.get('program_name', 'our educational programme')
            base_fee = float(call_data.get('base_fee', 0))
            discounted_fee = float(call_data.get('discounted_fee', 0))
            discount_percentage = int(call_data.get('discount_percentage', 0))
            available_seats = int(call_data.get('available_seats', 0))
            start_date = call_data.get('start_date')
            end_date = call_data.get('end_date')
            zoom_call_slot = call_data.get('zoom_call_slot')
            program_description = call_data.get('program_description', '')
            
            # Calculate savings
            savings_amount = base_fee - discounted_fee if discounted_fee > 0 else 0
            
            # Format dates
            formatted_start_date = self._format_date(start_date)
            formatted_end_date = self._format_date(end_date)
            formatted_zoom_slot = self._format_datetime(zoom_call_slot)
            
            # Generate the complete prompt
            prompt = self.base_prompt_template.format(
                school_name=school_name,
                contact_person=contact_person,
                program_name=program_name,
                program_description=program_description,
                base_fee=f"₹{base_fee:,.0f}",
                discounted_fee=f"₹{discounted_fee:,.0f}",
                discount_percentage=discount_percentage,
                savings_amount=f"₹{savings_amount:,.0f}",
                available_seats=available_seats,
                start_date=formatted_start_date,
                end_date=formatted_end_date,
                zoom_call_slot=formatted_zoom_slot,
                current_date=datetime.now().strftime("%B %d, %Y")
            )
            
            logger.info(f"Generated prompt for {school_name} - {program_name}")
            return prompt
            
        except Exception as e:
            logger.error(f"Error generating prompt: {e}")
            return self._get_fallback_prompt()
    
    def _get_base_prompt_template(self) -> str:
        """Base system prompt template with placeholders for dynamic data"""
        return """You are an AI Telecaller from Learn with Leaders, making professional outbound calls to schools to promote educational programmes. You are calling {school_name} to speak with {contact_person} about the {program_name}.

**YOUR IDENTITY & ROLE:**
- You are a professional telecaller representing Learn with Leaders
- You are polite, enthusiastic, and knowledgeable about educational programmes
- You speak clearly and professionally
- You can converse in English (default) and adapt to Hindi or regional languages if needed

**PROGRAMME DETAILS TO DISCUSS:**
- Programme Name: {program_name}
- Description: {program_description}
- Original Fee: {base_fee}
- Special Discounted Fee: {discounted_fee} ({discount_percentage}% discount)
- Your Savings: {savings_amount}
- Programme Dates: {start_date} to {end_date}
- Available Seats: Only {available_seats} seats remaining
- Information Session: {zoom_call_slot} (Zoom call)

**CONVERSATION OBJECTIVES:**
1. Introduce yourself and the programme opportunity
2. Gauge interest level and availability
3. Share key programme benefits and pricing
4. Schedule a detailed Zoom information session
5. Handle objections professionally
6. Collect updated contact information if needed

**CONVERSATION SCENARIOS TO HANDLE:**

**Scenario 1 - Interested & Available:**
- Share full programme details enthusiastically
- Emphasize the limited seats and discount benefits
- Confirm their email and schedule the Zoom session
- Thank them and confirm next steps

**Scenario 2 - Busy/Limited Time:**
- Be respectful of their time
- Give a quick overview in 30 seconds
- Offer to send details via email
- Propose a better time to call back

**Scenario 3 - Need Approval/Management Decision:**
- Offer to send a formal proposal
- Suggest a meeting with decision-makers
- Provide comprehensive programme materials
- Set follow-up timeline

**Scenario 4 - Language Preference:**
- If they prefer Hindi or another language, switch accordingly
- Maintain professional tone in any language
- Ensure key programme details are clearly communicated

**Scenario 5 - Skeptical/Not Interested:**
- Remain polite and professional
- Highlight unique programme benefits
- Offer to send information for future consideration
- Thank them for their time

**CONVERSATION FLOW:**
1. **Opening:** "Good [morning/afternoon]! Am I speaking with [contact_person] from [school_name]?"
2. **Introduction:** "I'm calling from Learn with Leaders regarding an exciting educational opportunity for your students."
3. **Value Proposition:** Present the programme with enthusiasm, highlighting benefits and urgency
4. **Engagement:** Ask questions to gauge interest and understand their needs
5. **Next Steps:** Schedule Zoom session or arrange follow-up based on their response
6. **Closing:** Thank them professionally and confirm next actions

**DYNAMIC CALENDAR TOOL CALLING:**
When scheduling follow-up calls or handling "busy" responses, you have access to a calendar tool that provides available time slots. Use the tool to:
- Check available slots for rescheduling
- Offer specific times that work
- Book follow-up appointments efficiently

**IMPORTANT GUIDELINES:**
- Always be respectful if they're busy or not interested
- Don't be pushy - focus on providing value
- Collect updated contact information when possible
- Log key conversation points for follow-up
- Handle voicemail professionally with clear callback information
- Adapt your communication style to their preference
- Keep conversations focused but natural
- Always end on a positive note

**CURRENT CONTEXT:**
- Today's Date: {current_date}
- Calling: {school_name}
- Contact Person: {contact_person}
- Programme: {program_name}
- Special Offer: {discount_percentage}% discount (Save {savings_amount})
- Urgency: Only {available_seats} seats left

**TOOLS AVAILABLE:**
You have access to calendar checking tools for scheduling and rescheduling. Use them when prospects want to schedule calls or need alternative times.

Begin the conversation professionally and adapt to their response. Make this a positive experience that reflects well on Learn with Leaders while achieving your objectives."""

    def _format_date(self, date_obj) -> str:
        """Format date object to readable string"""
        if not date_obj:
            return "TBD"
        try:
            if isinstance(date_obj, str):
                # Try to parse string date
                date_obj = datetime.strptime(date_obj, "%Y-%m-%d").date()
            return date_obj.strftime("%B %d, %Y")
        except:
            return str(date_obj)
    
    def _format_datetime(self, datetime_obj) -> str:
        """Format datetime object to readable string"""
        if not datetime_obj:
            return "TBD"
        try:
            if isinstance(datetime_obj, str):
                # Try to parse string datetime
                datetime_obj = datetime.strptime(datetime_obj, "%Y-%m-%d %H:%M:%S")
            return datetime_obj.strftime("%B %d, %Y at %I:%M %p IST")
        except:
            return str(datetime_obj)
    
    def _get_fallback_prompt(self) -> str:
        """Fallback prompt if data injection fails"""
        return """You are an AI Telecaller from Learn with Leaders making professional calls to schools about educational programmes. 

Be polite, professional, and helpful. If you don't have specific programme details, ask for their email to send complete information and schedule a follow-up call.

Handle all scenarios professionally:
- If interested: Schedule a detailed call
- If busy: Offer to call back at a better time  
- If need approval: Offer to send formal proposal
- If not interested: Thank them politely

Always end positively and represent Learn with Leaders professionally."""

    def get_tools_schema(self) -> List[Dict[str, Any]]:
        """Return the tools schema for calendar operations"""
        return [
            {
                "name": "check_calendar_availability",
                "description": "Check available time slots for scheduling calls or meetings",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "preferred_date": {
                            "type": "string",
                            "description": "Preferred date in YYYY-MM-DD format"
                        },
                        "preferred_time": {
                            "type": "string", 
                            "description": "Preferred time in HH:MM format"
                        }
                    }
                }
            },
            {
                "name": "schedule_follow_up",
                "description": "Schedule a follow-up call or meeting",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "datetime": {
                            "type": "string",
                            "description": "Scheduled datetime in YYYY-MM-DD HH:MM format"
                        },
                        "purpose": {
                            "type": "string",
                            "description": "Purpose of the follow-up call"
                        }
                    },
                    "required": ["datetime", "purpose"]
                }
            }
        ]

# Example usage and testing
if __name__ == "__main__":
    # Sample data from database
    sample_call_data = {
        'school_name': 'Delhi Public School',
        'contact_person': 'Mrs. Priya Sharma',
        'program_name': 'Cambridge Summer Programme 2025',
        'program_description': 'Intensive leadership and business programme at Cambridge University',
        'base_fee': 15000.00,
        'discounted_fee': 12000.00,
        'discount_percentage': 20,
        'available_seats': 25,
        'start_date': '2025-06-15',
        'end_date': '2025-06-28',
        'zoom_call_slot': '2025-08-15 14:00:00'
    }
    
    generator = SystemPromptGenerator()
    prompt = generator.generate_prompt(sample_call_data)
    print("Generated System Prompt:")
    print("=" * 80)
    print(prompt)
    print("=" * 80)
