"""
AI Conversation logic for AI Telecaller System
Handles conversation flow, response generation, and context management
"""

import time
import re
from typing import Dict, Any, List
from datetime import datetime
from ..core.conversation import ConversationState
from app.config.system_prompts import get_advanced_system_prompt

class AIConversationService:
    """Handles all AI conversation logic and response generation"""
    
    def __init__(self, llm=None):
        self.llm = llm
    
    def generate_intelligent_response(self, user_input: str, state: ConversationState) -> str:
        """Generate intelligent response using GPT-4 Mini with smart, contextual conversation flow"""
        
        # Start response time monitoring for performance optimization
        start_time = time.time()
        
        if not self.llm:
            # Fallback response if OpenAI not configured
            return "I'd love to share more details about our educational programs. Could you tell me a bit about your institution and your students' current needs?"
        
        try:
            # Build dynamic conversation context
            conversation_history = self.build_enhanced_context(state)
            repeated_question_status = self.detect_repeated_question(user_input.lower(), state)
            
            print(f"🧠 AI processing input: {user_input[:50]}...")
            print(f"🔍 Conversation history length: {len(state.get('messages', []))}")
            
            # Get dynamic data from state
            partner_info = state.get("partner_info", {})
            program_info = state.get("program_info", {})
            event_info = state.get("event_info", {})
            
            print(f"📊 Context - Partner: {partner_info.get('partner_name', 'Unknown')}, Program: {program_info.get('program_name', 'Unknown')}")
            
            # Build comprehensive system prompt with all context
            system_prompt = get_advanced_system_prompt(partner_info, program_info, event_info)
            
            # Add conversation context and repeated question analysis
            enhanced_context = f"""
{system_prompt}

CURRENT CONVERSATION CONTEXT:
{conversation_history}

QUESTION ANALYSIS:
{repeated_question_status}

CONVERSATION FLOW GUIDANCE:
- If this is early in conversation: Focus on building rapport and understanding their institution
- If they're showing interest: Provide specific details about programs and benefits  
- If they ask about costs: Present pricing as excellent value with clear benefits
- If they want to end: Graciously offer to send information via email
- If they ask for callback: Schedule appropriately and confirm timing
- Always be contextually relevant to what they just said

CRITICAL RESPONSE RULES:
1. ALWAYS respond directly to what they just said - never give generic responses
2. Build on previous conversation topics naturally
3. Use the specific partner/program/event data provided above
4. Sound naturally enthusiastic about educational opportunities
5. Keep responses conversational and human-like (premium quality)
6. Ask relevant follow-up questions to keep conversation flowing
7. If they confirmed they are the principal/decision maker, acknowledge that and proceed with program details
8. Be quick and efficient - don't over-explain unless they ask for more details

Current user input to respond to: "{user_input}"
"""
            
            # Create messages for AI
            messages = [
                {"role": "system", "content": enhanced_context},
                {"role": "user", "content": f"Please respond naturally and contextually to: {user_input}"}
            ]
            
            print("🚀 Calling OpenAI API for lightning-speed response...")
            api_start_time = time.time()
            
            # Call OpenAI with optimized settings for speed
            response = self.llm.invoke(messages)
            ai_response = response.content.strip()
            
            api_end_time = time.time()
            api_response_time = api_end_time - api_start_time
            total_response_time = api_end_time - start_time
            
            print(f"⚡ OpenAI API call: {api_response_time:.2f}s | Total processing: {total_response_time:.2f}s")
            print(f"🎯 Target: <2s (professional standard) | Actual: {total_response_time:.2f}s")
            print(f"🤖 AI Response: {ai_response[:100]}...")
            
            # Update conversation state for better context tracking
            self.update_conversation_state(state, user_input, ai_response)
            
            return ai_response
            
        except Exception as e:
            print(f"❌ AI response generation failed: {e}")
            # NO FALLBACK - Use only GPT-4o-mini Realtime API as requested
            return "I'm having trouble processing that. Could you please repeat what you said?"
    
    def build_enhanced_context(self, state: ConversationState) -> str:
        """Build enhanced conversation context for AI"""
        messages = state.get('messages', [])
        partner_info = state.get('partner_info', {})
        engagement_level = state.get('engagement_level', 'high')
        topics_discussed = state.get('topics_discussed', [])
        
        context_parts = []
        
        # Add recent conversation history (last 8 messages to match monolithic)
        if messages:
            context_parts.append("RECENT CONVERSATION:")
            recent_messages = messages[-8:]  # Last 8 messages (match monolithic)
            for msg in recent_messages:
                speaker = msg.get('speaker', 'Unknown')
                content = msg.get('content', msg.get('text', ''))
                context_parts.append(f"  {speaker.upper()}: {content}")
        
        # Add topics discussed (match monolithic format)
        if topics_discussed:
            context_parts.append(f"\nTOPICS ALREADY COVERED: {', '.join(topics_discussed)}")
        
        # Add pricing and schedule mentions (match monolithic boolean flags)
        if state.get("pricing_mentioned"):
            context_parts.append("\n💰 PRICING: Already discussed pricing details")
        if state.get("schedule_mentioned"):
            context_parts.append("\n📅 SCHEDULE: Already discussed timing/schedule")
        
        # Add features mentioned (match monolithic)
        if state.get("features_mentioned"):
            context_parts.append(f"\n🎯 FEATURES COVERED: {', '.join(state['features_mentioned'])}")
        
        # Add conversation summary (match monolithic)
        if state.get("conversation_summary"):
            context_parts.append(f"\n📝 CONVERSATION SUMMARY: {state['conversation_summary']}")
        
        return "\n".join(context_parts) if context_parts else "NEW CONVERSATION - First interaction"
    
    def detect_repeated_question(self, user_input_lower: str, state: ConversationState) -> str:
        """Detect if user is asking a question they've asked before"""
        if "repeated_questions" not in state:
            state["repeated_questions"] = {}
        
        # Common question patterns (match monolithic exactly)
        question_patterns = {
            'pricing': ['cost', 'price', 'fee', 'expensive', 'budget', 'money'],
            'schedule': ['when', 'time', 'schedule', 'date', 'timing'],
            'duration': ['how long', 'duration', 'weeks', 'months'],
            'location': ['where', 'location', 'venue', 'place'],
            'curriculum': ['what', 'learn', 'curriculum', 'subjects', 'topics'],
            'benefits': ['benefit', 'advantage', 'value', 'worth', 'good']
        }
        
        # Check which question type this is (match monolithic logic exactly)
        for question_type, keywords in question_patterns.items():
            if any(keyword in user_input_lower for keyword in keywords):
                if question_type in state["repeated_questions"]:
                    state["repeated_questions"][question_type] += 1
                    return f"REPEATED QUESTION DETECTED: This is the {state['repeated_questions'][question_type]} time they're asking about {question_type}. Provide MORE detailed and exciting information!"
                else:
                    state["repeated_questions"][question_type] = 1
                    return f"NEW QUESTION: First time asking about {question_type}."
        
        return "NEW GENERAL QUESTION: Respond with maximum excitement!"
    
    def update_conversation_state(self, state: ConversationState, user_input: str, ai_response: str):
        """Update conversation state with latest interaction for better context tracking"""
        user_input_lower = user_input.lower()
        
        # Initialize tracking fields if they don't exist (match monolithic)
        if "topics_discussed" not in state:
            state["topics_discussed"] = []
        if "features_mentioned" not in state:
            state["features_mentioned"] = []
        
        # Track topics discussed with boolean flags (match monolithic exactly)
        if any(word in user_input_lower for word in ['price', 'cost', 'fee', 'budget']):
            state["pricing_mentioned"] = True
            if "pricing" not in state["topics_discussed"]:
                state["topics_discussed"].append("pricing")
        
        if any(word in user_input_lower for word in ['when', 'schedule', 'time', 'date']):
            state["schedule_mentioned"] = True
            if "schedule" not in state["topics_discussed"]:
                state["topics_discussed"].append("schedule")
        
        if any(word in user_input_lower for word in ['curriculum', 'learn', 'subjects', 'topics']):
            if "curriculum" not in state["topics_discussed"]:
                state["topics_discussed"].append("curriculum")
        
        # Update last AI response for context (match monolithic)
        state["last_ai_response"] = ai_response
        
        # Update conversation summary (keep it brief for speed - match monolithic)
        recent_topics = state["topics_discussed"][-3:]  # Last 3 topics
        state["conversation_summary"] = f"Discussed: {', '.join(recent_topics)}" if recent_topics else "Initial conversation"
    
    def generate_response_with_context(self, prompt: str, state: ConversationState) -> str:
        """Generate dynamic AI response with current conversation context (EXACT MONOLITHIC MATCH)"""
        
        if not self.llm:
            return "I'm excited to share more details with you! Let me gather the specific information you need."

        try:
            # Get conversation history for context (EXACT MONOLITHIC LOGIC)
            conversation_context = "\n".join([
                f"{msg['speaker'].upper()}: {msg['text']}" 
                for msg in state["messages"][-3:]  # Last 3 messages for context
            ])
            
            # Enhanced prompt with conversation context (EXACT MONOLITHIC)
            enhanced_prompt = f"""
            CONVERSATION CONTEXT:
            {conversation_context}
            
            {prompt}
            
            Generate a natural, engaging response that sounds conversational and exciting. 
            Keep it concise (1-2 sentences max) but compelling.
            """
            
            from langchain_core.messages import SystemMessage, HumanMessage
            messages = [
                SystemMessage(content=enhanced_prompt),
                HumanMessage(content="Generate the response")
            ]
            
            response = self.llm.invoke(messages)
            return response.content
            
        except Exception as e:
            print(f"❌ Error generating dynamic response: {e}")
            return "I'm so excited to share this opportunity with you! Let me provide you with all the details."
    
    def analyze_engagement_and_sentiment(self, user_input: str, conversation_history: List[Dict]) -> Dict[str, Any]:
        """Quickly analyze user engagement and sentiment without delays (EXACT MONOLITHIC MATCH)"""
        try:
            user_input_lower = user_input.lower()
            
            # Quick sentiment analysis (no API calls for speed) - EXACT MONOLITHIC SIGNALS
            engagement_signals = {
                'high': [
                    'tell me more', 'interested', 'sounds good', 'how much', 'when', 'where',
                    'what about', 'can you explain', 'fees', 'cost', 'register', 'sign up',
                    'details', 'more information', 'curriculum', 'schedule', 'duration'
                ],
                'medium': [
                    'maybe', 'possibly', 'let me think', 'sounds okay', 'not bad',
                    'could be', 'might work', 'depends'
                ],
                'wrap_up': [
                    'email me', 'send details', 'call later', 'busy now', 'schedule meeting',
                    'no more questions', 'think about it', 'discuss with team', 'get back to you',
                    'thank you', 'thanks', 'thats all', 'no questions', 'all good'
                ],
                'negative': [
                    'not interested', 'no thanks', 'too expensive', 'not for us',
                    'waste of time', 'busy', 'not now', 'remove me'
                ]
            }
            
            # Detect user interests/topics mentioned (EXACT MONOLITHIC KEYWORDS)
            interests = []
            topic_keywords = {
                'fees': ['cost', 'fees', 'price', 'expensive', 'cheap', 'budget'],
                'schedule': ['when', 'time', 'schedule', 'duration', 'how long'],
                'curriculum': ['what', 'curriculum', 'subjects', 'topics', 'learn'],
                'registration': ['register', 'sign up', 'enroll', 'join', 'apply'],
                'location': ['where', 'location', 'venue', 'place'],
                'testimonials': ['reviews', 'feedback', 'results', 'success']
            }
            
            for topic, keywords in topic_keywords.items():
                if any(keyword in user_input_lower for keyword in keywords):
                    interests.append(topic)
            
            # Determine engagement level
            engagement_level = 'medium'  # default
            for level, signals in engagement_signals.items():
                if any(signal in user_input_lower for signal in signals):
                    engagement_level = level
                    break
            
            # Quick question detection (EXACT MONOLITHIC LOGIC)
            is_question = '?' in user_input or any(word in user_input_lower.split()[:3] for word in ['what', 'when', 'where', 'how', 'why', 'can', 'do', 'is', 'are'])
            
            return {
                'engagement_level': engagement_level,
                'interests': interests,
                'is_question': is_question,
                'sentiment': engagement_level,  # Simplified for speed (EXACT MONOLITHIC)
                'should_continue': engagement_level in ['high', 'medium'] or is_question
            }
            
        except Exception as e:
            print(f"❌ Error in engagement analysis: {e}")
            return {
                'engagement_level': 'medium',
                'interests': [],
                'is_question': False,
                'sentiment': 'neutral',
                'should_continue': True
            }
    
    def generate_contextual_response(self, current_state: ConversationState, analysis: Dict[str, Any]) -> str:
        """Generate response based on engagement analysis and conversation context (EXACT MONOLITHIC MATCH)"""
        try:
            # Get the latest user message
            latest_message = current_state["messages"][-1]["text"] if current_state["messages"] else ""
            
            # Create contextual prompt based on engagement (EXACT MONOLITHIC LOGIC)
            if analysis['engagement_level'] == 'high':
                if analysis['interests']:
                    context_instruction = f"User is highly engaged and specifically interested in: {', '.join(analysis['interests'])}. Provide detailed information about these topics and ask if they want to know anything else."
                else:
                    context_instruction = "User is highly engaged. Continue the conversation with detailed information and ask if they have any questions."
            
            elif analysis['engagement_level'] == 'wrap_up':
                context_instruction = "User seems ready to wrap up. Offer to send details via email, schedule a follow-up, or ask if they have any final questions before ending."
            
            elif analysis['engagement_level'] == 'negative':
                context_instruction = "User seems disinterested. Politely try one more brief value proposition or gracefully end the call."
            
            else:  # medium engagement
                if analysis['is_question']:
                    context_instruction = "User asked a question. Answer it clearly and ask if they have any other questions."
                else:
                    context_instruction = "User shows moderate interest. Provide relevant information and gauge their interest level."
            
            # Enhanced system prompt with engagement context (EXACT MONOLITHIC)
            enhanced_prompt = f"""
You are Sarah, a professional educational consultant from Learn with Leaders. 

CURRENT SITUATION ANALYSIS:
- Engagement Level: {analysis['engagement_level']}
- User Interests: {analysis['interests'] if analysis['interests'] else 'General inquiry'}
- Conversation Stage: {'Question Answering' if analysis['is_question'] else 'Information Sharing'}

RESPONSE INSTRUCTIONS: {context_instruction}

CONVERSATION GUIDELINES:
1. Be conversational and natural - avoid robotic responses
2. If user asks about fees, schedule, curriculum, or registration - provide specific details
3. If user says "tell me about X again" - re-explain that topic clearly
4. After answering questions, always ask "Do you have any other questions?" or "Is there anything else you'd like to know?"
5. If user seems ready to end (mentions email, scheduling, no more questions), offer next steps
6. Keep responses concise but informative
7. Do not repeat information already covered unless specifically asked

PROGRAM CONTEXT:
{self._get_program_context_summary(current_state)}

Latest user message: "{latest_message}"

Respond naturally and helpfully:
"""
            
            # Generate response using GPT
            from langchain_core.messages import SystemMessage, HumanMessage
            response = self.llm.invoke([
                SystemMessage(content=enhanced_prompt),
                HumanMessage(content=latest_message)
            ])
            
            return response.content.strip()
            
        except Exception as e:
            print(f"❌ Error generating contextual response: {e}")
            return "I appreciate your interest! Do you have any questions about our educational programs that I can help answer?"
    
    def _get_program_context_summary(self, state: ConversationState) -> str:
        """Get a brief summary of program context for prompts (EXACT MONOLITHIC MATCH)"""
        try:
            program_info = state.get("program_info", {})
            event_info = state.get("event_info", {})
            
            summary = "Educational Leadership Programs:\n"
            
            if program_info:
                summary += f"- Program: {program_info.get('name', 'Leadership Development')}\n"
                summary += f"- Focus: {program_info.get('description', 'Student leadership and life skills')}\n"
            
            if event_info:
                summary += f"- Upcoming Event: {event_info.get('name', 'Student Workshop')}\n"
            
            return summary
            
        except Exception as e:
            return "Educational Programs focused on student development and leadership skills."

# Global AI conversation service instance  
ai_conversation_service = AIConversationService()
