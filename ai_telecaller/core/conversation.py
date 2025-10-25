"""
Conversation state management for AI Telecaller System
Handles conversation flow states and LangGraph integration
"""

from typing import List, Dict, Any
from typing_extensions import TypedDict, Annotated
import operator

class ConversationState(TypedDict):
    """State for LangGraph conversation flow with engagement tracking"""
    messages: Annotated[List[Dict[str, str]], operator.add]
    partner_info: Dict[str, Any]
    program_info: Dict[str, Any]
    event_info: Dict[str, Any]
    call_sid: str
    current_context: str
    engagement_level: str  # 'high', 'medium', 'low', 'wrap_up'
    user_interests: List[str]  # Track what user is interested in
    questions_asked: int  # Count of follow-up questions
    sentiment_trend: List[str]  # Track sentiment over conversation
    scheduled_call_data: Dict[str, Any]  # Scheduled call information with timezone data
    
    # Enhanced context tracking
    topics_discussed: List[str]  # Track all topics covered
    repeated_questions: Dict[str, int]  # Track questions asked multiple times
    conversation_summary: str  # Running summary of key points
    last_ai_response: str  # Remember last response for context
    pricing_mentioned: bool  # Track if pricing was discussed
    schedule_mentioned: bool  # Track if schedule was discussed
    features_mentioned: List[str]  # Track which features were mentioned
