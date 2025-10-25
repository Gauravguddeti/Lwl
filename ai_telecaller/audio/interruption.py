"""
Interruption handling for AI Telecaller System
Manages conversation interruptions and appropriate responses
"""

from typing import Dict, Any
from ..core.conversation import ConversationState

class InterruptionHandler:
    """Handles conversation interruptions and generates appropriate responses"""
    
    def __init__(self):
        self.interruption_patterns = {
            'stop': ['stop', 'enough', 'not interested', 'no thanks'],
            'wait': ['wait', 'hold', 'slow', 'pause'],
            'busy': ['busy', 'time', 'later', 'call back'],
            'negative': ['no', 'not now', 'not good time'],
            'positive': ['yes', 'continue', 'go ahead', 'okay'],
            'question': ['what', 'how', 'when', 'where', 'why', 'tell me']
        }
    
    def handle_interruption_response(self, user_input: str, state: ConversationState) -> str:
        """Generate appropriate response when user interrupts the telecaller"""
        user_lower = user_input.lower()
        
        # Detect interruption type
        interruption_type = self.detect_interruption_type(user_lower)
        
        # Generate appropriate response based on interruption type
        if interruption_type == 'stop':
            return "I completely understand! Let me quickly share one key benefit that might interest you, and then I can send you information via email if you'd prefer?"
        
        elif interruption_type == 'wait':
            return "Of course! I'll slow down. What specific question can I answer for you right now?"
        
        elif interruption_type == 'busy':
            return "I understand you're busy! Would it be better if I quickly send you the key details via email, or would you prefer I call back at a better time?"
        
        elif interruption_type == 'negative':
            return "No problem at all! Just so you don't miss out, can I quickly email you the information about these exciting opportunities for your students?"
        
        elif interruption_type == 'positive':
            return "Wonderful! Let me share the most exciting details about these programs that could really benefit your students."
        
        elif interruption_type == 'question':
            return "Great question! Let me address that specifically for you."
        
        else:
            # User interrupted but it's unclear why - be accommodating
            return "Sorry, I didn't want to interrupt you! What would you like to know about these educational opportunities?"
    
    def detect_interruption_type(self, user_input_lower: str) -> str:
        """Detect the type of interruption based on user input"""
        for interruption_type, keywords in self.interruption_patterns.items():
            if any(keyword in user_input_lower for keyword in keywords):
                return interruption_type
        
        return 'unclear'
    
    def should_handle_as_interruption(self, user_input: str, conversation_context: Dict[str, Any]) -> bool:
        """Determine if input should be handled as an interruption"""
        user_lower = user_input.lower()
        
        # Short, abrupt responses often indicate interruptions
        if len(user_input.strip()) < 10:
            return True
        
        # Check for common interruption phrases
        interruption_indicators = [
            'wait', 'stop', 'hold on', 'excuse me', 'sorry',
            'no no', 'actually', 'but', 'however'
        ]
        
        return any(indicator in user_lower for indicator in interruption_indicators)
    
    def get_interruption_recovery_strategy(self, interruption_type: str, state: ConversationState) -> Dict[str, Any]:
        """Get strategy for recovering from interruption"""
        strategies = {
            'stop': {
                'approach': 'acknowledge_and_offer_value',
                'next_action': 'offer_email_or_callback',
                'tone': 'understanding'
            },
            'wait': {
                'approach': 'slow_down_and_clarify',
                'next_action': 'ask_specific_question',
                'tone': 'patient'
            },
            'busy': {
                'approach': 'respect_time_constraints',
                'next_action': 'offer_alternatives',
                'tone': 'respectful'
            },
            'negative': {
                'approach': 'soft_persistence',
                'next_action': 'minimal_value_proposition',
                'tone': 'understanding'
            },
            'positive': {
                'approach': 'continue_with_enthusiasm',
                'next_action': 'share_key_benefits',
                'tone': 'excited'
            }
        }
        
        return strategies.get(interruption_type, {
            'approach': 'clarify_and_adapt',
            'next_action': 'ask_open_question',
            'tone': 'flexible'
        })

# Global interruption handler instance
interruption_handler = InterruptionHandler()
