"""
Dynamic Tag Processor for AI Telecaller System Prompts
Created: August 7, 2025
Purpose: Process dynamic tags in system prompts with real database data
"""

import logging
from typing import Dict, Any
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class DynamicTagProcessor:
    """
    Process dynamic tags in system prompts and replace with actual data
    """
    
    def __init__(self):
        """Initialize the tag processor"""
        self.current_time = datetime.now()
        
    def process_system_prompt(self, prompt_template: str, data: Dict[str, Any]) -> str:
        """
        Process system prompt template and replace all dynamic tags with actual data
        
        Args:
            prompt_template: Template with {{tag}} placeholders
            data: Database row data
            
        Returns:
            Processed prompt with all tags replaced
        """
        
        try:
            # Create tag mapping with actual data
            tag_mapping = self._create_tag_mapping(data)
            
            # Replace all tags in the template
            processed_prompt = prompt_template
            for tag, value in tag_mapping.items():
                tag_pattern = f"{{{{{tag}}}}}"
                processed_prompt = processed_prompt.replace(tag_pattern, str(value))
            
            # Log successful processing
            logger.info(f"Processed system prompt with {len(tag_mapping)} dynamic tags")
            
            return processed_prompt
            
        except Exception as e:
            logger.error(f"Error processing system prompt tags: {e}")
            return prompt_template  # Return original if processing fails
    
    def _create_tag_mapping(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create mapping of tags to actual values from database data
        """
        
        # Extract data with fallbacks
        school_name = data.get('school_name', 'your school')
        contact_person = data.get('contact_person', 'the principal')
        program_name = data.get('program_name', 'our educational program')
        base_fee = data.get('base_fee', 0) or 0
        discounted_fee = data.get('discounted_fee', 0) or 0
        discount_percentage = data.get('discount_percentage', 0) or 0
        start_date = data.get('start_date', 'TBD')
        end_date = data.get('end_date', 'TBD')
        available_seats = data.get('available_seats', 'limited')
        
        # Calculate savings
        savings_amount = base_fee - discounted_fee if base_fee and discounted_fee else 0
        
        # Format dates nicely
        formatted_start_date = self._format_date(start_date)
        formatted_end_date = self._format_date(end_date)
        
        # Format fees with Indian formatting
        formatted_original_fee = f"{base_fee:,.0f}" if base_fee else "0"
        formatted_discounted_fee = f"{discounted_fee:,.0f}" if discounted_fee else "0"
        formatted_savings = f"{savings_amount:,.0f}" if savings_amount else "0"
        
        # Time-based greetings
        greeting_time, time_context = self._get_time_based_greeting()
        
        # Create comprehensive tag mapping
        tag_mapping = {
            # Time-based tags
            'GREETING_TIME': greeting_time,
            'TIME_CONTEXT': time_context,
            
            # School and contact tags
            'school_name': school_name,
            'contact_person': contact_person,
            
            # Program tags
            'program_name': program_name,
            'original_fee': formatted_original_fee,
            'discounted_fee': formatted_discounted_fee,
            'discount_percentage': discount_percentage,
            'savings_amount': formatted_savings,
            'program_start_date': formatted_start_date,
            'program_end_date': formatted_end_date,
            'available_seats': available_seats,
            
            # Calculated tags
            'daily_cost': self._calculate_daily_cost(discounted_fee, start_date, end_date),
            'program_duration': self._calculate_duration(start_date, end_date),
            'urgency_message': self._create_urgency_message(available_seats),
            
            # Dynamic content tags
            'school_type': self._determine_school_type(school_name),
            'program_category': self._determine_program_category(program_name),
            'fee_bracket': self._determine_fee_bracket(discounted_fee),
            
            # Social proof tags
            'testimonial': self._get_relevant_testimonial(program_name),
            'participant_count': self._get_participant_count(program_name),
            'success_rate': '98%',  # Could be dynamic based on program
            
            # Location tags
            'program_location': self._get_program_location(program_name),
            'nearest_airport': self._get_nearest_airport(program_name)
        }
        
        return tag_mapping
    
    def _get_time_based_greeting(self) -> tuple:
        """Get appropriate greeting based on current time"""
        current_hour = self.current_time.hour
        
        if 5 <= current_hour < 12:
            return "Good morning", "morning"
        elif 12 <= current_hour < 17:
            return "Good afternoon", "afternoon"
        elif 17 <= current_hour < 21:
            return "Good evening", "evening"
        else:
            return "Good evening", "late evening"
    
    def _format_date(self, date_str: str) -> str:
        """Format date string nicely"""
        if not date_str or date_str == 'TBD':
            return 'TBD'
        
        try:
            # Try to parse and format the date
            if isinstance(date_str, str):
                # Assume format is YYYY-MM-DD
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                return date_obj.strftime('%B %d, %Y')
        except:
            pass
        
        return str(date_str)
    
    def _calculate_daily_cost(self, total_fee: float, start_date: str, end_date: str) -> str:
        """Calculate daily cost of the program"""
        try:
            if not total_fee or start_date == 'TBD' or end_date == 'TBD':
                return "competitive"
            
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            duration_days = (end - start).days + 1
            
            if duration_days > 0:
                daily_cost = total_fee / duration_days
                return f"₹{daily_cost:,.0f}"
            
        except:
            pass
        
        return "competitive"
    
    def _calculate_duration(self, start_date: str, end_date: str) -> str:
        """Calculate program duration"""
        try:
            if start_date == 'TBD' or end_date == 'TBD':
                return "flexible duration"
            
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            duration_days = (end - start).days + 1
            
            if duration_days <= 7:
                return f"{duration_days} days"
            elif duration_days <= 14:
                return f"{duration_days // 7} week{'s' if duration_days > 7 else ''}"
            else:
                return f"{duration_days} days"
            
        except:
            return "flexible duration"
    
    def _create_urgency_message(self, available_seats) -> str:
        """Create urgency message based on available seats"""
        try:
            seats = int(available_seats)
            if seats <= 5:
                return f"Only {seats} seats remaining!"
            elif seats <= 10:
                return f"Limited seats available - only {seats} left"
            else:
                return f"{seats} seats available"
        except:
            return "Limited seats available"
    
    def _determine_school_type(self, school_name: str) -> str:
        """Determine school type from name"""
        name_lower = school_name.lower()
        
        if 'international' in name_lower:
            return 'international'
        elif 'public' in name_lower:
            return 'public'
        elif 'private' in name_lower:
            return 'private'
        elif 'convent' in name_lower:
            return 'convent'
        else:
            return 'prestigious'
    
    def _determine_program_category(self, program_name: str) -> str:
        """Determine program category"""
        name_lower = program_name.lower()
        
        if 'cambridge' in name_lower:
            return 'Cambridge University'
        elif 'oxford' in name_lower:
            return 'Oxford University'
        elif 'mit' in name_lower:
            return 'MIT'
        elif 'harvard' in name_lower:
            return 'Harvard'
        elif 'stanford' in name_lower:
            return 'Stanford'
        else:
            return 'international'
    
    def _determine_fee_bracket(self, fee: float) -> str:
        """Determine fee bracket for messaging"""
        if fee < 10000:
            return 'budget-friendly'
        elif fee < 20000:
            return 'mid-range'
        else:
            return 'premium'
    
    def _get_relevant_testimonial(self, program_name: str) -> str:
        """Get relevant testimonial based on program"""
        testimonials = {
            'cambridge': "One of our students from DPS Delhi said: 'The Cambridge program changed my perspective on global education completely!'",
            'oxford': "A student from Ryan International shared: 'Oxford program gave me confidence to pursue international opportunities!'",
            'mit': "A participant mentioned: 'The MIT innovation program sparked my interest in technology and entrepreneurship!'",
            'harvard': "A student told us: 'Harvard program taught me leadership skills I use every day!'",
            'stanford': "One participant said: 'Stanford program connected me with like-minded innovators from around the world!'"
        }
        
        program_lower = program_name.lower()
        for key, testimonial in testimonials.items():
            if key in program_lower:
                return testimonial
        
        return "Our students consistently rate these programs 4.8/5 stars for life-changing experiences!"
    
    def _get_participant_count(self, program_name: str) -> str:
        """Get participant count for social proof"""
        counts = {
            'cambridge': '2,500+',
            'oxford': '1,800+',
            'mit': '1,200+',
            'harvard': '2,000+',
            'stanford': '1,500+'
        }
        
        program_lower = program_name.lower()
        for key, count in counts.items():
            if key in program_lower:
                return count
        
        return '10,000+'
    
    def _get_program_location(self, program_name: str) -> str:
        """Get program location"""
        locations = {
            'cambridge': 'Cambridge, UK',
            'oxford': 'Oxford, UK',
            'mit': 'Boston, USA',
            'harvard': 'Boston, USA',
            'stanford': 'California, USA'
        }
        
        program_lower = program_name.lower()
        for key, location in locations.items():
            if key in program_lower:
                return location
        
        return 'international location'
    
    def _get_nearest_airport(self, program_name: str) -> str:
        """Get nearest airport for travel planning"""
        airports = {
            'cambridge': 'London Heathrow',
            'oxford': 'London Heathrow',
            'mit': 'Boston Logan',
            'harvard': 'Boston Logan',
            'stanford': 'San Francisco'
        }
        
        program_lower = program_name.lower()
        for key, airport in airports.items():
            if key in program_lower:
                return airport
        
        return 'major international airport'

    def get_concise_twilio_prompt_template(self) -> str:
        """Get concise system prompt template for Twilio calls (under 3000 characters)"""
        
        template = """
{greeting}, this is {caller_name} from {organization_name}.

I hope you're having a wonderful {time_period}! Am I speaking with {contact_person} from {school_name}?

Is this a good time to talk for 2-3 minutes about {program_name} - a prestigious {program_duration} {program_category} program at Cambridge University?

[PROGRAM OVERVIEW]
Our {program_name} has helped {success_metric} students experience authentic Cambridge University academic life. Given {school_name}'s excellent reputation, I believe your students would be perfect candidates.

Key Details:
- Duration: {program_duration}
- Dates: {program_start_date} to {program_end_date}
- Investment: {total_fee} ({early_bird_discount} available)
- Deadline: {application_deadline}

[CONVERSATION FLOW]
1. "{greeting}, is this {contact_person}? I hope I'm not catching you at a busy time?"
2. "I'm calling because {school_name} has such an excellent reputation for {school_strength}."
3. "This {program_duration} program includes {program_benefits} and students return with {program_outcomes}."
4. "The program fee is {total_fee}, with {discount_available} for early enrollment."
5. "Would you like me to send detailed information to {email_address}?"

[OBJECTION RESPONSES]
Budget: "We offer {payment_plan} and find schools see excellent {roi_statement}."
Timing: "We have {flexible_dates} and work with your academic calendar."
Need Discussion: "I'll send information today and we can talk {callback_time}."

[OBJECTIVES]
- Build rapport and assess interest
- Share key benefits and address concerns
- Secure follow-up agreement
- Schedule future conversation if needed

Voice: Friendly, professional, consultative. Focus on educational value for {school_name} students.
""".strip()
        
        return template


# Test function
def test_dynamic_tag_processor():
    """Test the dynamic tag processor"""
    
    print("🧪 Testing Dynamic Tag Processor")
    print("=" * 40)
    
    # Sample data
    sample_data = {
        'school_name': 'Delhi Public School',
        'contact_person': 'Mrs. Priya Sharma',
        'program_name': 'Cambridge Summer Programme 2025',
        'base_fee': 15000,
        'discounted_fee': 12000,
        'discount_percentage': 20,
        'start_date': '2025-06-15',
        'end_date': '2025-06-28',
        'available_seats': 25
    }
    
    # Sample template
    template = """{{GREETING_TIME}}! This is calling from Learn with Leaders. 
Am I speaking with {{contact_person}} or the principal of {{school_name}}?

I'm calling about our {{program_name}} - normally ₹{{original_fee}}, 
but now just ₹{{discounted_fee}} ({{discount_percentage}}% off = ₹{{savings_amount}} savings!).

The program runs from {{program_start_date}} to {{program_end_date}} at {{program_location}}.
{{urgency_message}}

{{testimonial}}"""
    
    # Process the template
    processor = DynamicTagProcessor()
    processed = processor.process_system_prompt(template, sample_data)
    
    print("📝 Processed Prompt:")
    print("-" * 20)
    print(processed)
    print()
    
    return True

if __name__ == "__main__":
    test_dynamic_tag_processor()
