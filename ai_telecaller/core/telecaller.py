"""
Core Telecaller System for AI Telecaller
Main system class that orchestrates all components
"""

import os
import sys
import json
import time
import threading
import subprocess
import traceback
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
import asyncio
import websockets
import websocket
import base64
import wave
import audioop

from flask import Flask, request, jsonify
from flask_sock import Sock

# Try to import Twilio (optional for demo) - EXACT MONOLITHIC IMPORT
try:
    from twilio.twiml.voice_response import VoiceResponse, Connect, Stream
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    print("WARNING: Twilio not available - running in demo mode")
    TWILIO_AVAILABLE = False
    VoiceResponse = None
    Client = None
    Connect = None
    Stream = None

# Import modular components
from .config import config
from .conversation import ConversationState
from ..database.data_access import database_access
from ..communication.twilio_handler import twilio_handler
from ..communication.webhooks import WebhookHandler
from ..services.call_storage import call_storage
from ..services.ai_conversation import ai_conversation_service
from ..audio.realtime_handler import RealtimeHandler
from ..audio.processor import audio_processor

# Import existing services
from app.services.smart_timezone_greeting_service import SmartTimezoneGreetingService
from app.services.simple_ivr_service import SimpleIVRService
from app.utils.email_service import email_service

# Import AI/LangGraph modules - EXACT MONOLITHIC IMPORTS
import openai
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from typing_extensions import TypedDict, Annotated
import operator

class TelecallerSystem:
    """Complete AI Telecaller System with modular architecture"""
    
    def __init__(self):
        print("[STARTING] AI IVR Telecaller System Starting...")
        print("=" * 60)
        
        # Initialize Flask app
        self.app = Flask(__name__)
        
        # Add WebSocket support for Twilio Media Streams
        try:
            self.sock = Sock(self.app)
        except:
            print("WARNING: Flask-Sock not available - installing via pip...")
            self.sock = None
        
        # Initialize configuration
        self.config = config
        self.flask_port = self.config.flask_port
        self.recordings_dir = self.config.recordings_dir
        
        # Recordings directory for local storage (exact match with monolithic system)
        os.makedirs(self.recordings_dir, exist_ok=True)
        
        # Initialize storage and services
        self.call_storage = call_storage
        
        # Initialize services for scheduled calls and timezone greetings
        self.timezone_service = SmartTimezoneGreetingService()
        self.ivr_service = SimpleIVRService()
        
        # Store conversation states for active calls
        self.conversation_states = {}
        
        # Store OpenAI WebSocket connections (like monolithic system)
        self.openai_connections = {}
        
        # Track active calls
        self.active_calls = {}
        
        # Store scheduled calls data for demonstration
        self.scheduled_calls_cache = []
        
        # Initialize Twilio handler
        self.twilio_handler = twilio_handler
        
        # Initialize AI services
        self.openai_api_key = self.config.openai_api_key
        
        # Initialize OpenAI Realtime handler
        self.realtime_handler = RealtimeHandler(self.openai_api_key)
        
        # Deprecated: replaced with OpenAI Realtime WebSocket
        print("Using OpenAI Realtime API instead of ChatOpenAI")
        self.llm = None  # Deprecated - using OpenAI Realtime WebSocket instead
        
        # Initialize AI conversation service
        self.ai_conversation = ai_conversation_service
        self.ai_conversation.llm = self.llm
        
        # Build LangGraph conversation flow
        self.conversation_graph = self.build_conversation_graph()
        
        # Twilio configuration (exact match with monolithic system)
        self.twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID', 'your_account_sid')
        self.twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN', 'your_auth_token')
        self.twilio_phone_number = os.getenv('TWILIO_PHONE_NUMBER', '+1234567890')
        
        # Add aliases for recording download compatibility
        self.account_sid = self.twilio_account_sid
        self.auth_token = self.twilio_auth_token
        
        self.client = None
        if TWILIO_AVAILABLE and self.twilio_account_sid != 'your_account_sid':
            self.client = Client(self.twilio_account_sid, self.twilio_auth_token)
        
        # Ngrok configuration
        self.ngrok_process = None
        self.ngrok_url = None
        
        # Setup Flask routes and webhooks
        self.webhook_handler = WebhookHandler(self.app, self)
        self.setup_flask_routes()
        self.setup_websocket_routes()
        
        print("SUCCESS: System initialization complete")
    
    def build_conversation_graph(self):
        """Build LangGraph conversation flow"""
        graph = StateGraph(ConversationState)
        
        # Define conversation nodes
        graph.add_node("greeting", self.greeting_node)
        # Note: Other nodes (authority_check, program_introduction, etc.) are handled
        # directly in process_conversation_turn method for more dynamic flow
        
        # Define conversation flow
        graph.set_entry_point("greeting")
        graph.add_edge("greeting", END)  # End after greeting - subsequent responses handled by process_conversation_turn
        
        return graph.compile()
    
    def greeting_node(self, state: ConversationState) -> ConversationState:
        """Generate dynamic, engaging greeting using AI"""
        import datetime
        
        # Get current time for appropriate greeting
        current_hour = datetime.datetime.now().hour
        if current_hour < 12:
            time_greeting = "Good morning"
        elif current_hour < 17:
            time_greeting = "Good afternoon"
        else:
            time_greeting = "Good evening"
        
        partner_info = state["partner_info"]
        partner_name = partner_info.get("partner_name", "your institution")
        partnership_type = partner_info.get("partnership_type", "institution")
        
        # Determine the decision-maker title based on partnership type
        if "school" in partnership_type.lower():
            decision_maker = "principal or academic director"
        elif "institute" in partnership_type.lower():
            decision_maker = "director or head of academics"
        elif "college" in partnership_type.lower():
            decision_maker = "dean or academic coordinator" 
        else:
            decision_maker = "person in charge of academic programs"
        
        # Generate dynamic greeting using AI with HIGH ENERGY
        greeting_prompt = f"""
        Create an INCREDIBLY EXCITED and energetic greeting for Sarah, a telecaller from Learn with Leaders calling {partner_name}.
        
        CRITICAL - Sarah must sound THRILLED and EXCITED:
        - Start with "{time_greeting}! This is Sarah from Learn with Leaders and I am SO excited to call you!"
        - Sound GENUINELY THRILLED and enthusiastic - use words like "incredible", "amazing", "exciting"
        - Express authentic excitement about the educational opportunities
        - Ask energetically to speak with the {decision_maker}
        - Use high-energy language: "I have some absolutely incredible news to share!"
        - Keep it conversational but FULL OF ENERGY (2-3 sentences max)
        - Sound like you can barely contain your excitement about what you're sharing
        - Use exclamation points naturally in speech patterns
        - Make them feel like they're about to hear the most amazing opportunity ever!
        
        Make Sarah sound like she's bursting with excitement to share this incredible opportunity!
        """
        
        greeting = self.ai_conversation.generate_response_with_context(greeting_prompt, state)
        
        return {"messages": [{"speaker": "ai", "text": greeting}]}
    
    def authority_check_node(self, state: ConversationState) -> ConversationState:
        """Handle authority verification and proceed to program introduction"""
        # This will be called after the caller responds to greeting
        program_introduction_response = self.program_introduction_node(state)
        return program_introduction_response
    
    def program_introduction_node(self, state: ConversationState) -> ConversationState:
        """Generate engaging program introduction using AI for dynamic, human-like presentation"""
        program_info = state["program_info"]
        event_info = state["event_info"]
        
        # Get detailed event information from database
        program_name = program_info.get('name', 'Professional Training Program')
        program_description = program_info.get('description', 'A comprehensive professional development program')
        
        # Get event details
        event_duration = event_info.get('duration_weeks', 'flexible')
        event_start_date = event_info.get('start_date', 'upcoming sessions')
        event_end_date = event_info.get('end_date', '')
        available_seats = event_info.get('seats', 'limited')
        
        # Format dates if available
        date_info = ""
        if event_start_date and event_start_date != 'upcoming sessions':
            if event_end_date:
                date_info = f"running from {event_start_date} to {event_end_date}"
            else:
                date_info = f"starting from {event_start_date}"
        else:
            date_info = "with multiple upcoming batches available"
        
        # Get comprehensive pricing information  
        try:
            from ...app.services import dynamic_data_fetcher
            pricing = dynamic_data_fetcher.format_pricing_info(program_info, event_info)
        except:
            # Fallback pricing if dynamic_data_fetcher not available
            pricing = {
                'formatted_final': 'Contact for pricing',
                'discount_percentage': '20',
                'formatted_original': 'Regular fee'
            }
        
        # Create dynamic, engaging program presentation using AI
        program_intro_prompt = f"""
        You are Sarah, speaking naturally on a phone call. Create an exciting presentation of this program:
        
        PROGRAM DETAILS:
        - Program: {program_name}
        - Description: {program_description}
        - Duration: {event_duration} weeks
        - Schedule: {date_info}
        - Available spots: {available_seats} participants
        - Investment: {pricing['formatted_final']} per student 
        - Discount: {pricing['discount_percentage']}% off regular fee of {pricing['formatted_original']}
        - Target: Educational institution professionals
        
        SPEAKING GUIDELINES (This will be read aloud by text-to-speech):
        - Sound like you're actually talking to someone on the phone
        - Use natural, conversational language
        - Sound enthusiastic but not overly excited
        - Present information in a flowing, natural way
        - Make it sound like great value and opportunity
        - Keep it concise (2-3 sentences max)
        - End with a natural question to continue conversation
        - Use simple, clear language that sounds good when spoken
        - Avoid complex formatting or punctuation
        
        Generate a natural, spoken response that gets them excited!
        """
        
        intro = self.ai_conversation.generate_response_with_context(program_intro_prompt, state)
        
        return {"messages": [{"speaker": "ai", "text": intro}]}
    
    def handle_query_node(self, state: ConversationState) -> ConversationState:
        """Handle user queries using RAG and database information"""
        if not state["messages"] or state["messages"][-1]["speaker"] != "caller":
            return {"messages": []}

        user_query = state["messages"][-1]["text"]

        # Use GPT-4 Mini with dynamic system prompt and RAG
        response = self.generate_intelligent_response(user_query, state)

        return {"messages": [{"speaker": "ai", "text": response}], "current_context": "query_handled"}
    
    def conclude_call_node(self, state: ConversationState) -> ConversationState:
        """Conclude the call"""
        return state
    
    def provide_details_node(self, state: ConversationState) -> ConversationState:
        """Provide detailed information based on database data"""
        # This node is triggered when more details are requested
        return state
    
    def schedule_followup_node(self, state: ConversationState) -> ConversationState:
        """Schedule follow-up if requested"""
        if "callback" in state["current_context"].lower() or "later" in state["current_context"].lower():
            followup = "I'd be happy to schedule a follow-up call. What time would work best for you? I can call back tomorrow or later this week at your convenience."
            return {"messages": [{"speaker": "ai", "text": followup}]}
        
        return {"messages": []}
    
    def conclude_call_node(self, state: ConversationState) -> ConversationState:
        """Conclude the call appropriately"""
        conclusion = "Thank you for your time today. I'll send you the program details via email, and please feel free to contact us if you have any questions. Have a wonderful day!"
        
        return {"messages": [{"speaker": "ai", "text": conclusion}]}

    def add_natural_pauses(self, text: str) -> str:
        """Add natural pauses and breathing patterns using proper speech timing, not SSML"""
        
        # Instead of SSML tags, use natural punctuation and spacing for pauses
        # Twilio's AI voice will naturally pause at these points
        
        # Add natural pauses with ellipses and commas
        text = text.replace('. ', '... ')  # Natural pause after sentences
        text = text.replace('! ', '! ')    # Keep exclamation natural
        text = text.replace('? ', '? ')    # Keep questions natural
        text = text.replace(', ', ', ')    # Natural comma pause
        
        # Add natural speech patterns for breathing
        breathing_phrases = [
            ('Here\'s what makes this special', 'Here\'s what makes this special...'),
            ('The exciting part is', 'The exciting part is...'),
            ('What\'s incredible is', 'What\'s incredible is...'),
            ('The best part is', 'The best part is...'),
            ('I\'m excited to share', 'I\'m so excited to share'),
            ('Let me tell you', 'Let me tell you...'),
            ('Here\'s the thing', 'Here\'s the thing...')
        ]
        
        for original, natural in breathing_phrases:
            if original in text:
                text = text.replace(original, natural)
        
        # Remove any accidental SSML tags that might have been added
        import re
        text = re.sub(r'<[^>]+>', '', text)  # Remove any XML/SSML tags
        
        return text
    
    def generate_response_with_context(self, prompt: str, state: ConversationState) -> str:
        """Generate AI response with context (delegation to AI service)"""
        return self.ai_conversation.generate_response_with_context(prompt, state)
    
    def generate_intelligent_response(self, user_input: str, state: ConversationState) -> str:
        """Generate intelligent AI response (delegation to AI service)"""
        return self.ai_conversation.generate_intelligent_response(user_input, state)
    
    def process_conversation_turn(self, call_sid: str, user_input: str) -> str:
        """FAST conversation processing with EXCITEMENT and CONTEXT MEMORY"""
        try:
            # Get existing conversation state or create new one
            if call_sid in self.conversation_states:
                current_state = self.conversation_states[call_sid]
                if current_state is None:
                    print("WARNING: Found None conversation state, creating new one")
                    current_state = self._create_fallback_state(call_sid, user_input)
                else:
                    # Create new state with caller's message added
                    current_state = {
                        **current_state,
                        "messages": current_state.get("messages", []) + [{"speaker": "caller", "text": user_input}],
                        "current_context": "user_response"
                    }
            else:
                # Fallback: create new state if not found
                current_state = self._create_fallback_state(call_sid, user_input)
            
            print(f"🎯 Processing: {user_input[:50]}...")
            
            # For all responses, use AI for natural, contextual responses
            print("AI: Using AI for contextual response...")
            ai_response = self.generate_intelligent_response(user_input, current_state)
            
            # Update conversation state with AI response
            if "messages" not in current_state:
                current_state["messages"] = []
                
            # Ensure ai_response is not None - use AI for fallback too
            if ai_response is None:
                # Let AI handle the fallback naturally
                ai_response = self.generate_intelligent_response("Could you please tell me more about that?", current_state)
                if ai_response is None:  # Final fallback if AI fails
                    ai_response = "Could you please tell me more about that? I want to make sure I provide you with the most relevant information for your institution."
                
            current_state["messages"].append({"speaker": "ai", "text": ai_response})
            self.conversation_states[call_sid] = current_state
            
            print(f"SUCCESS: Response generated: {ai_response[:50] if ai_response else 'None'}...")
            return ai_response
            
        except Exception as e:
            print(f"ERROR: Error processing conversation: {e}")
            import traceback
            traceback.print_exc()
            return "I'm absolutely THRILLED to be talking with you! Could you please repeat that? I want to make sure I give you the most exciting information possible!"

    def _create_fallback_state(self, call_sid: str, user_input: str) -> Dict[str, Any]:
        """Create a fallback conversation state when none exists"""
        try:
            call_context = self.get_call_context_for_sid(call_sid)
        except:
            call_context = {}
            
        return {
            "messages": [{"speaker": "caller", "text": user_input}],
            "partner_info": call_context.get('partner_info', {}),
            "program_info": call_context.get('program_info', {}),
            "event_info": call_context.get('event_info', {}),
            "call_sid": call_sid,
            "current_context": "user_response",
            "engagement_level": "medium",
            "user_interests": [],
            "questions_asked": 0,
            "sentiment_trend": [],
            "scheduled_call_data": {},
            "topics_discussed": [],
            "repeated_questions": {},
            "conversation_summary": "",
            "last_ai_response": "",
            "pricing_mentioned": False,
            "schedule_mentioned": False,
            "features_mentioned": []
        }
    
    def _generate_contextual_fallback(self, user_input: str) -> str:
        """Generate contextual fallback response based on user input keywords"""
        user_lower = user_input.lower()
        
        # Contextual responses based on what user said
        if any(word in user_lower for word in ['yes', 'principal', 'director', 'head']):
            return "Perfect! I'm excited to share details about our educational programs. We have some fantastic opportunities that could really benefit your students. What type of programs are you most interested in for your institution?"
        
        elif any(word in user_lower for word in ['cost', 'price', 'fee', 'budget', 'expensive']):
            return "Great question about pricing! Our programs are designed to provide exceptional value. The investment varies depending on the specific program, but we often have scholarships and discounts available. Which program were you most interested in learning about?"
        
        elif any(word in user_lower for word in ['when', 'schedule', 'timing', 'date']):
            return "Excellent question about timing! We have multiple program dates throughout the year to accommodate different schedules. When would work best for your students - during school breaks or integrated into the academic year?"
        
        elif any(word in user_lower for word in ['email', 'send', 'information']):
            return "Absolutely! I'd be happy to send you detailed information via email. Could you please confirm your email address so I can send you comprehensive program details right away?"
        
        elif any(word in user_lower for word in ['no', 'not interested', 'busy', 'later']):
            return "I completely understand. Would it be helpful if I sent you some information via email that you could review when convenient? That way you'll have all the details about these valuable opportunities for your students."
        
        elif any(word in user_lower for word in ['callback', 'call back', 'later']):
            return "Of course! I'd be happy to call you back at a more convenient time. When would work better for you - perhaps later today or tomorrow?"
        
        else:
            return "I'd love to learn more about your institution and how we can best support your students. Could you tell me a bit about what type of educational programs or opportunities you're currently looking for?"

    def detect_repeated_question(self, user_input_lower: str, state: ConversationState) -> str:
        """Detect if user is asking a question they've asked before"""
        if "repeated_questions" not in state:
            state["repeated_questions"] = {}
        
        # Common question patterns
        question_patterns = {
            'pricing': ['cost', 'price', 'fee', 'expensive', 'budget', 'money'],
            'schedule': ['when', 'time', 'schedule', 'date', 'timing'],
            'duration': ['how long', 'duration', 'weeks', 'months'],
            'location': ['where', 'location', 'venue', 'place'],
            'curriculum': ['what', 'learn', 'curriculum', 'subjects', 'topics'],
            'benefits': ['benefit', 'advantage', 'value', 'worth', 'good']
        }
        
        # Check which question type this is
        for question_type, keywords in question_patterns.items():
            if any(keyword in user_input_lower for keyword in keywords):
                if question_type in state["repeated_questions"]:
                    state["repeated_questions"][question_type] += 1
                    return f"REPEATED QUESTION DETECTED: This is the {state['repeated_questions'][question_type]} time they're asking about {question_type}. Provide MORE detailed and exciting information!"
                else:
                    state["repeated_questions"][question_type] = 1
                    return f"NEW QUESTION: First time asking about {question_type}."
        
        return "NEW GENERAL QUESTION: Respond with maximum excitement!"
    
    def handle_interruption_response(self, user_input: str, state: ConversationState) -> str:
        """Generate appropriate response when user interrupts the telecaller (EXACT MONOLITHIC MATCH)"""
        user_lower = user_input.lower()
        
        # Specific interruption handling patterns (EXACT MONOLITHIC LOGIC)
        if any(word in user_lower for word in ['stop', 'enough', 'not interested']):
            return "I completely understand! Let me quickly share one key benefit that might interest you, and then I can send you information via email if you'd prefer?"
        
        elif any(word in user_lower for word in ['wait', 'hold', 'slow']):
            return "Of course! I'll slow down. What specific question can I answer for you right now?"
        
        elif any(word in user_lower for word in ['busy', 'time', 'later', 'call back']):
            return "I understand you're busy! Would it be better if I quickly send you the key details via email, or would you prefer I call back at a better time?"
        
        elif any(word in user_lower for word in ['no', 'not now']):
            return "No problem at all! Just so you don't miss out, can I quickly email you the information about these exciting opportunities for your students?"
        
        elif any(word in user_lower for word in ['yes', 'continue', 'go ahead']):
            return "Wonderful! Let me share the most exciting details about these programs that could really benefit your students."
        
        else:
            # User interrupted but it's unclear why - be accommodating (EXACT MONOLITHIC)
            return "Sorry, I didn't want to interrupt you! What would you like to know about these educational opportunities?"
    
    def twilio_to_openai_loop(self, twilio_ws, openai_ws, call_sid, openai_loop):
        """Handle Twilio to OpenAI audio forwarding (delegation to realtime handler)"""
        return self.realtime_handler.twilio_to_openai_loop(twilio_ws, openai_ws, call_sid, openai_loop)
    
    def openai_to_twilio_loop(self, openai_ws, twilio_ws, stream_sid, call_sid, openai_loop):
        """Handle OpenAI to Twilio audio playback (delegation to realtime handler)"""
        return self.realtime_handler.openai_to_twilio_loop(openai_ws, twilio_ws, stream_sid, call_sid, openai_loop)
    
    def handle_email_request(self, call_sid: str, user_email: str = None):
        """Handle user request to send details via email"""
        try:
            # Get call context
            call_context = self.get_call_context_for_sid(call_sid)
            partner_info = call_context.get('partner_info', {})
            program_info = call_context.get('program_info', {})
            event_info = call_context.get('event_info', {})
            
            # Use provided email or get from partner info
            recipient_email = user_email or partner_info.get('contact_email')
            
            if not recipient_email:
                return "I'd be happy to send you the details! Could you please confirm your email address?"
            
            # Validate email format (basic validation)
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, recipient_email):
                return "The email address doesn't seem to be in the correct format. Could you please provide it again?"
            
            # For now, just confirm email will be sent (actual email service would be integrated separately)
            return f"Perfect! I've noted your email as {recipient_email}. Our team will send you comprehensive program details within the next hour. You'll receive detailed information about our educational programs, pricing, and available dates. Please feel free to contact us if you have any questions after reviewing the information."
                
        except Exception as e:
            print(f"ERROR: Error handling email request: {e}")
            return "I apologize, but there was a technical issue with sending the email. Let me take down your contact information and have our team follow up with you directly."
    
    def save_call_recording(self, call_sid, audio_buffer):
        """Save call recording (delegation to call storage)"""
        return self.call_storage.save_call_recording(call_sid, audio_buffer)
    
    def transcribe_recording(self, wav_filename, call_sid, timestamp):
        """Transcribe recording (delegation to call storage)"""
        return self.call_storage.transcribe_recording(wav_filename, call_sid, timestamp)
    
    def build_enhanced_context(self, state: ConversationState) -> str:
        """Build comprehensive conversation context for AI memory"""
        context_parts = []
        
        # Recent conversation history
        recent_messages = state["messages"][-8:]  # Last 8 messages
        if recent_messages:
            context_parts.append("RECENT CONVERSATION:")
            for msg in recent_messages:
                context_parts.append(f"  {msg['speaker'].upper()}: {msg['text']}")
        
        # Topics discussed
        if "topics_discussed" in state and state["topics_discussed"]:
            context_parts.append(f"\nTOPICS ALREADY COVERED: {', '.join(state['topics_discussed'])}")
        
        # Pricing and schedule mentions
        if state.get("pricing_mentioned"):
            context_parts.append("\n💰 PRICING: Already discussed pricing details")
        if state.get("schedule_mentioned"):
            context_parts.append("\n📅 SCHEDULE: Already discussed timing/schedule")
        
        # Features mentioned
        if state.get("features_mentioned"):
            context_parts.append(f"\n🎯 FEATURES COVERED: {', '.join(state['features_mentioned'])}")
        
        # Conversation summary
        if state.get("conversation_summary"):
            context_parts.append(f"\n📝 CONVERSATION SUMMARY: {state['conversation_summary']}")
        
        return "\n".join(context_parts) if context_parts else "NEW CONVERSATION - First interaction"
    
    def update_conversation_state(self, state: ConversationState, user_input: str, ai_response: str):
        """Update conversation state with latest interaction for better context tracking"""
        user_input_lower = user_input.lower()
        
        # Initialize tracking fields if they don't exist
        if "topics_discussed" not in state:
            state["topics_discussed"] = []
        if "features_mentioned" not in state:
            state["features_mentioned"] = []
        
        # Track topics discussed
        if any(word in user_input_lower for word in ['price', 'cost', 'fee', 'budget']):
            state["pricing_mentioned"] = True
            if "pricing" not in state["topics_discussed"]:
                state["topics_discussed"].append("pricing")
        
        if any(word in user_input_lower for word in ['when', 'schedule', 'timing', 'date']):
            state["schedule_mentioned"] = True
            if "schedule" not in state["topics_discussed"]:
                state["topics_discussed"].append("schedule")
        
        # Track features mentioned
        feature_keywords = ['curriculum', 'program', 'course', 'workshop', 'training', 'certification']
        for keyword in feature_keywords:
            if keyword in user_input_lower and keyword not in state["features_mentioned"]:
                state["features_mentioned"].append(keyword)
        
        # Update conversation summary (keep last 3 interactions summary)
        state["conversation_summary"] = f"User: {user_input[:100]}... | AI: {ai_response[:100]}..."
        state["last_ai_response"] = ai_response
    
    def generate_excited_fallback_response(self, user_input: str) -> str:
        """Fallback response that uses AI system instead of hardcoded responses"""
        try:
            # Create a basic state for the AI call
            fallback_state = {
                "messages": [{"speaker": "caller", "text": user_input}],
                "partner_info": {},
                "program_info": {},
                "event_info": {},
                "call_sid": "fallback",
                "current_context": "user_response",
                "engagement_level": "medium",
                "user_interests": [],
                "questions_asked": 0,
                "sentiment_trend": [],
                "scheduled_call_data": {},
                "topics_discussed": [],
                "repeated_questions": {},
                "conversation_summary": "",
                "last_ai_response": "",
                "pricing_mentioned": False,
                "schedule_mentioned": False,
                "features_mentioned": []
            }
            
            # Use the AI to generate natural response
            return self.generate_intelligent_response(user_input, fallback_state)
            
        except Exception as e:
            print(f"ERROR: Error in fallback response: {e}")
            return "Thank you for sharing that with me. Could you tell me a bit more about what would be most helpful for your institution?"
    
    def generate_fallback_response(self, user_input: str) -> str:
        """Database-driven fallback responses - NO HARDCODED TEXT (exact copy from monolithic)"""
        try:
            # Try to use LLM with database context first (EXACT MONOLITHIC LOGIC)
            if self.llm:
                from langchain_core.messages import HumanMessage, SystemMessage
                
                # Create a minimal context for fallback responses
                fallback_prompt = f"""
You are Sarah from Learn with Leaders, a professional telecaller. Generate a natural response to: "{user_input}"

Be warm, professional, and ask a relevant follow-up question. Keep it conversational and helpful.
Respond directly to what they said without being generic. Use 1-2 sentences maximum.

Generate ONLY the response text:"""
                
                response = self.llm.invoke([HumanMessage(content=fallback_prompt)])
                return response.content.strip()
            
            # If LLM unavailable, create minimal database-driven response (EXACT MONOLITHIC LOGIC)
            user_input_lower = user_input.lower()
            
            if any(word in user_input_lower for word in ['interested', 'yes', 'tell me more', 'sounds good']):
                return "That's wonderful! What specifically would you like to know more about?"
            elif any(word in user_input_lower for word in ['price', 'cost', 'fee', 'budget']):
                return "I'd be happy to discuss the investment details. What's your main concern about the costs?"
            elif any(word in user_input_lower for word in ['when', 'schedule', 'dates', 'timing']):
                return "Great question about timing! When would work best for your institution?"
            elif any(word in user_input_lower for word in ['not interested', 'no', 'not now', 'busy']):
                return "I understand. Would it be helpful if I sent you some brief information instead?"
            elif any(word in user_input_lower for word in ['callback', 'later', 'call back']):
                return "Of course! When would be a better time to reach you?"
            else:
                return "I want to make sure I give you the right information. What's most important to you?"
                
        except Exception as e:
            print(f"ERROR: Error in fallback response: {e}")
            return "Thank you for that. Could you tell me more about what you're looking for?"
    
    def get_decision_maker_title(self, partner_info: Dict[str, Any]) -> str:
        """Get appropriate decision maker title based on partnership type"""
        partnership_type = partner_info.get("partnership_type", "institution")
        
        if "school" in partnership_type.lower():
            return "principal or academic director"
        elif "institute" in partnership_type.lower():
            return "director or head of academics"
        elif "college" in partnership_type.lower():
            return "dean or academic coordinator" 
        else:
            return "person in charge of academic programs"
    
    def analyze_engagement_and_sentiment(self, user_input: str, conversation_history: List[Dict]) -> Dict[str, Any]:
        """Analyze user engagement and sentiment (delegation to AI service)"""
        return self.ai_conversation.analyze_engagement_and_sentiment(user_input, conversation_history)
    
    def generate_contextual_response(self, current_state: ConversationState, analysis: Dict[str, Any]) -> str:
        """Generate contextual response (delegation to AI service)"""
        return self.ai_conversation.generate_contextual_response(current_state, analysis)
    
    def _get_program_context_summary(self, state: ConversationState) -> str:
        """Get program context summary for responses"""
        program_info = state.get("program_info", {})
        partner_info = state.get("partner_info", {})
        
        summary_parts = []
        
        if program_info.get("program_name"):
            summary_parts.append(f"Program: {program_info['program_name']}")
        
        if program_info.get("duration"):
            summary_parts.append(f"Duration: {program_info['duration']}")
        
        if partner_info.get("partner_name"):
            summary_parts.append(f"Institution: {partner_info['partner_name']}")
        
        return " | ".join(summary_parts) if summary_parts else "Educational program discussion"
    
    def get_scheduled_calls_from_database(self) -> List[Dict[str, Any]]:
        """Get scheduled calls from database (delegation to IVR service)"""
        return self.ivr_service.get_all_calls_to_be_done()
    
    def demonstrate_getcallstobedone_function(self):
        """Demonstrate scheduled calls functionality"""
        calls = self.get_scheduled_calls_from_database()
        print(f" Found {len(calls)} scheduled calls")
        for i, call in enumerate(calls[:3], 1):  # Show first 3
            print(f"{i}. {call.get('contact_person_name', 'Unknown')} at {call.get('partner_name', 'Unknown')}")
    
    def get_scheduled_call_data(self, call_sid: str) -> Optional[Dict[str, Any]]:
        """Get scheduled call data for a specific call SID"""
        calls = self.get_scheduled_calls_from_database()
        for call in calls:
            if call.get('call_sid') == call_sid:
                return call
        return None
    
    def call_scheduled_contact(self, call_index: int) -> Dict[str, Any]:
        """Call a scheduled contact by index"""
        calls = self.get_scheduled_calls_from_database()
        if 0 <= call_index < len(calls):
            call_data = calls[call_index]
            contact_phone = call_data.get('contact_phone', '')
            partner_name = call_data.get('partner_name', 'Unknown')
            
            if contact_phone:
                return self.make_call(contact_phone, partner_name)
            else:
                return {'status': 'error', 'message': 'No contact phone available'}
        else:
            return {'status': 'error', 'message': 'Invalid call index'}
    
    def select_and_call_partner(self, partners: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Interactive partner selection and calling"""
        if not partners:
            print("ERROR: No partners available")
            return None
        
        print(" Available partners:")
        for i, partner in enumerate(partners):
            name = partner.get('partner_name', 'Unknown')
            contact = partner.get('contact', 'No contact')
            print(f"{i+1:2d}. {name} - {contact}")
        
        try:
            choice = input("Enter partner number to call (or 'q' to quit): ").strip()
            if choice.lower() == 'q':
                return None
            
            partner_index = int(choice) - 1
            return self.call_specific_partner(partners, partner_index)
        except (ValueError, IndexError):
            print("ERROR: Invalid selection")
            return None
    
    def display_menu(self, partners: List[Dict[str, Any]]):
        """Display interactive menu"""
        print("\\n" + "="*50)
        print("AI: AI TELECALLER SYSTEM - MAIN MENU")
        print("="*50)
        print("1. Call All Partners")
        print("2. Select and Call Specific Partner")
        print("3. Show Scheduled Calls")
        print("4. Refresh Partner List")
        print("5. Exit")
        print("="*50)
    
    def simulate_demo_conversation(self):
        """Simulate a demo conversation for testing"""
        print("🎭 Starting demo conversation simulation...")
        
        # Create mock conversation state
        demo_state = {
            "messages": [],
            "partner_info": {"partner_name": "Demo School", "partnership_type": "school"},
            "program_info": {"program_name": "Leadership Development Program"},
            "event_info": {},
            "call_sid": "demo_call",
            "current_context": "greeting",
            "engagement_level": "high",
            "user_interests": [],
            "questions_asked": 0,
            "sentiment_trend": [],
            "scheduled_call_data": {},
            "topics_discussed": [],
            "repeated_questions": {},
            "conversation_summary": "",
            "last_ai_response": "",
            "features_mentioned": []
        }
        
        # Simulate conversation turns
        demo_inputs = [
            "Hello, this is the principal speaking",
            "Tell me more about the program",
            "What is the cost?",
            "When can we schedule this?",
            "Please send me more information"
        ]
        
        for user_input in demo_inputs:
            print(f"\\nUSER: {user_input}")
            response = self.process_conversation_turn("demo_call", user_input)
            print(f"AI: {response}")
        
        print("\\nSUCCESS: Demo conversation completed")
    
    def listen_for_openai_responses_separate(self, openai_ws, twilio_ws, stream_sid, call_sid):
        """Listen for OpenAI responses (delegation to realtime handler)"""
        return self.realtime_handler.listen_for_openai_responses_separate(openai_ws, twilio_ws, stream_sid, call_sid)
    
    def handle_openai_response(self, openai_ws, ws, response_data):
        """Handle OpenAI response (delegation to realtime handler)"""
        return self.realtime_handler.handle_openai_response(openai_ws, ws, response_data)
    
    def listen_to_openai_responses(self, openai_conn, twilio_ws, call_sid):
        """Listen to OpenAI responses (delegation to realtime handler)"""
        return self.realtime_handler.listen_to_openai_responses(openai_conn, twilio_ws, call_sid)

    def setup_websocket_routes(self):
        """Setup WebSocket routes for media streaming"""
        if not self.sock:
            print("WARNING: WebSocket not available - media streaming disabled")
            return
        
        @self.sock.route('/media-stream')
        def webhook_stream_handler(ws):
            """Handle Twilio Media Stream WebSocket"""
            print(" Media stream WebSocket connected!")
            
            call_sid = None
            stream_sid = None
            openai_connection = None
            
            try:
                while True:
                    message = ws.receive()
                    data = json.loads(message)
                    event = data.get('event')
                    
                    if event == 'connected':
                        print(" Twilio Media Stream connected")
                    
                    elif event == 'start':
                        call_sid = data.get('start', {}).get('callSid')
                        stream_sid = data.get('start', {}).get('streamSid')
                        print(f" Media stream started for call: {call_sid}")
                        
                        # Get OpenAI connection for this call (check both connection storages)
                        if call_sid in self.openai_connections:
                            openai_connection = self.openai_connections[call_sid]
                            print(f"🤝 Connected to existing OpenAI connection for {call_sid}")
                            
                            # Start audio forwarding loops
                            self.start_audio_loops(ws, openai_connection, stream_sid, call_sid)
                        elif call_sid in self.realtime_handler.connections:
                            openai_connection = self.realtime_handler.connections[call_sid]
                            print(f"🤝 Connected to existing OpenAI connection for {call_sid} (fallback)")
                            
                            # Start audio forwarding loops
                            self.start_audio_loops(ws, openai_connection, stream_sid, call_sid)
                        else:
                            print(f"WARNING: No OpenAI connection found for call: {call_sid}")
                            print(f"🔍 Available connections: {list(self.openai_connections.keys())}")
                            print(f"🔍 Handler connections: {list(self.realtime_handler.connections.keys())}")
                    
                    elif event == 'media' and openai_connection:
                        # Audio forwarding is handled in separate loops
                        pass
                    
                    elif event == 'stop':
                        print(f"STOP: Media stream stopped for call: {call_sid}")
                        break
                        
            except Exception as e:
                print(f"ERROR: WebSocket error: {e}")
                import traceback
                traceback.print_exc()
            finally:
                print(f"🔌 WebSocket disconnected for call: {call_sid}")
    
    def start_audio_loops(self, twilio_ws, openai_connection, stream_sid, call_sid):
        """Start audio forwarding loops between Twilio and OpenAI (exact copy from original threading approach)"""
        try:
            openai_ws = openai_connection['websocket']
            openai_loop = openai_connection['loop']
            
            print(" STARTING PURE OPENAI REALTIME SYSTEM...")
            
            # Start DUAL CONCURRENT LOOPS with proper async handling (like original)
            import threading
            
            # Loop 1: Twilio → OpenAI (caller audio only) - keep as thread (like original)
            twilio_to_openai_thread = threading.Thread(
                target=self.realtime_handler.twilio_to_openai_loop,
                args=(twilio_ws, openai_ws, call_sid, openai_loop),
                daemon=True,
                name=f"TwilioToOpenAI-{call_sid}"
            )
            twilio_to_openai_thread.start()
            print("🎤 Started Twilio→OpenAI thread")
            
            # Loop 2: OpenAI → Twilio (AI audio only) - use direct method call like original
            print("🔊 Starting OpenAI→Twilio loop...")
            print(f"🔍 OpenAI loop running: {openai_loop.is_running()}")
            print(f"🔍 OpenAI WebSocket state: {openai_ws}")
            
            # Start OpenAI to Twilio loop (exact approach from original)
            self.realtime_handler.openai_to_twilio_loop(openai_ws, twilio_ws, stream_sid, call_sid, openai_loop)
            
            print("SUCCESS: Call setup complete - audio loops running")
            
        except Exception as e:
            print(f"ERROR: Error starting audio loops: {e}")
            import traceback
            traceback.print_exc()
    
    def connect_to_openai_realtime_websocket(self, call_sid):
        """Connect to OpenAI Realtime WebSocket"""
        # Get call context to pass to greeting
        context = self.get_call_context_for_sid(call_sid)
        
        return self.realtime_handler.connect_to_openai_realtime_websocket(
            call_sid, 
            system_prompt_func=self.get_realtime_system_prompt,
            call_context=context,
            connection_storage=self.openai_connections  # Pass connection storage like monolithic
        )
    
    def get_realtime_system_prompt(self, call_sid):
        """Generate system prompt for OpenAI Realtime API with PURE TELECALLER BEHAVIOR (exact copy from monolithic)"""
        try:
            # Get call context
            call_context = self.get_call_context_for_sid(call_sid)
            partner_info = call_context.get('partner_info', {})
            program_info = call_context.get('program_info', {})
            
            partner_name = partner_info.get('partner_name', 'Learn with Leaders')
            contact_person = partner_info.get('contact_person_name', 'there')
            program_name = program_info.get('program_name', 'our educational programs')
            
            current_hour = datetime.now().hour
            time_greeting = "Good morning" if current_hour < 12 else "Good afternoon" if current_hour < 17 else "Good evening"
            
            return f"""You are Sarah, a professional telecaller from Learn with Leaders. You are calling {partner_name} about {program_name}.

CRITICAL CONVERSATION FLOW - FOLLOW EXACTLY:

1. GREETING & TIME CHECK:
   Start with: "{time_greeting}! This is Sarah calling from Learn with Leaders. I hope I'm not catching you at a busy time."

2. AUTHORITY CHECK:
   "I'm calling about our {program_name} opportunity for {partner_name}. Am I speaking with {contact_person} or the person in charge of educational programs?"

3. TIME CONFIRMATION:
   "Is this a good time for a quick 3-4 minute chat about this exciting educational opportunity?"

4. PROGRAM PRESENTATION (if yes to good time):
   "Wonderful! We have an incredible {program_name} that I believe would be perfect for your students. Let me quickly share the key details..."
   - Present program benefits from database
   - Include pricing with discount from database
   - Mention duration and schedule from database
   - Sound excited and enthusiastic

5. QUERY HANDLING:
   "Do you have any questions about the program, pricing, or how it would work for your students?"
   - Answer ALL questions using database information ONLY
   - Be thorough and helpful
   - Ask follow-up questions to gauge interest

6. EMAIL OFFER:
   "Would you like me to send you comprehensive details via email so you can review everything at your convenience?"
   - If YES: "Perfect! Could you confirm your email address?"
   - If they provide email: "Excellent! I'll send detailed information to [email] right after our call."

7. WRAP UP:
   "Thank you so much for your time! You'll receive the detailed information within a few minutes. Please feel free to contact us with any questions after reviewing. Have a wonderful day!"

CRITICAL RULES:
- Stay enthusiastic and professional throughout
- Only use database information for program details
- Never make up pricing or program information
- If asked about email sending, use the handle_email_request function
- Keep responses natural and conversational
- Guide conversation toward enrollment interest
- Handle interruptions gracefully

EMAIL HANDLING:
- When user asks for email details, call self.handle_email_request(call_sid, user_email)
- Confirm email address before sending
- Be enthusiastic about sending comprehensive details

DATABASE CONTEXT:
- Partner: {partner_name}
- Contact: {contact_person}  
- Program: {program_name}
- Use ONLY database information for ALL program details

Start immediately with the greeting above and follow the exact flow!"""
            
        except Exception as e:
            print(f"ERROR: Error generating system prompt: {e}")
            return "You are Sarah, a professional telecaller from Learn with Leaders. Be enthusiastic about educational opportunities and follow the conversation flow naturally."
    
    def get_call_context_for_sid(self, call_sid):
        """Get call context for a specific call SID"""
        if call_sid in self.conversation_states:
            state = self.conversation_states[call_sid]
            return {
                'partner_info': state.get('partner_info', {}),
                'program_info': state.get('program_info', {}),
                'event_info': state.get('event_info', {}),
                'scheduled_call_data': state.get('scheduled_call_data', {})
            }
        return {}
    
    def get_partners_from_database(self) -> List[Dict[str, Any]]:
        """Get all active partners from database"""
        return database_access.get_partners_from_database()
    
    def make_call(self, to_number: str, partner_name: str = "Unknown") -> Dict[str, Any]:
        """Make a call to a specific number"""
        return self.twilio_handler.make_call(to_number, partner_name, self.ngrok_url, self.active_calls)
    
    def call_all_partners(self, partners: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Make calls to all partners simultaneously"""
        return self.twilio_handler.call_all_partners(partners, self.ngrok_url, self.active_calls)
    
    def download_call_recording(self, call_sid: str, recording_url: str, partner_name: str = None):
        """Download call recording"""
        return self.twilio_handler.download_call_recording(call_sid, recording_url, partner_name, self.call_storage.call_storage)
    
    def finalize_conversation_with_enhanced_naming(self, call_sid: str):
        """Finalize conversation using enhanced call storage with proper naming"""
        try:
            print(f"📝 Finalizing call with enhanced naming: {call_sid}")
            
            # Get conversation messages from the stored JSONL file
            conversation_file = os.path.join(
                self.call_storage.call_storage.transcriptions_path,
                f"{call_sid}_conversation.jsonl"
            )
            
            messages = []
            if os.path.exists(conversation_file):
                with open(conversation_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            data = json.loads(line.strip())
                            messages.append({
                                'speaker': data.get('speaker', 'unknown'),
                                'text': data.get('text', ''),
                                'timestamp': data.get('timestamp', '')
                            })
                        except json.JSONDecodeError:
                            continue
            
            # Get recording URL and partner name if available (like monolithic)
            recording_url = None
            partner_name = None
            if call_sid in self.active_calls:
                recording_url = self.active_calls[call_sid].get('recording_url')
                partner_name = self.active_calls[call_sid].get('partner_name')
            
            # Use enhanced call storage to finalize with proper naming format (EXACT MONOLITHIC METHOD)
            result = self.call_storage.finalize_call_enhanced(call_sid, messages, recording_url, partner_name)
            
            if 'error' not in result:
                print(f"SUCCESS: Call finalized with enhanced format:")
                print(f"   📄 Summary: {result.get('summary_file', 'N/A')}")
                print(f"   📝 JSON: {result.get('json_file', 'N/A')}")
                print(f"   🎤 Recording: {result.get('recording_file', 'N/A')}")
                print(f"    Outcome: {result.get('outcome', 'N/A')}")
                
                # Clean up old conversation file
                if os.path.exists(conversation_file):
                    os.remove(conversation_file)
                    print(f"🧹 Cleaned up temporary conversation file")
            else:
                print(f"ERROR: Error in enhanced finalization: {result['error']}")
                
        except Exception as e:
            print(f"ERROR: Error finalizing conversation: {e}")
            import traceback
            traceback.print_exc()
    
    def store_conversation_turn(self, call_sid: str, speaker: str, text: str):
        """Store conversation turn"""
        return self.call_storage.store_conversation_turn(call_sid, speaker, text)
    
    def start_ngrok(self):
        """Start ngrok tunnel"""
        print("[STARTING] Starting ngrok tunnel...")
        
        try:
            # Start ngrok process
            self.ngrok_process = subprocess.Popen(
                ['ngrok', 'http', str(self.flask_port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for ngrok to start
            time.sleep(3)
            
            # Get ngrok URL
            try:
                import requests
                response = requests.get('http://localhost:4040/api/tunnels')
                tunnels = response.json()['tunnels']
                
                if tunnels:
                    self.ngrok_url = tunnels[0]['public_url']
                    print(f"SUCCESS: Ngrok tunnel active: {self.ngrok_url}")
                    return True
                else:
                    print("ERROR: No ngrok tunnels found")
                    return False
                    
            except Exception as e:
                print(f"ERROR: Error getting ngrok URL: {e}")
                return False
                
        except Exception as e:
            print(f"ERROR: Error starting ngrok: {e}")
            return False
    
    def start_flask_server(self):
        """Start Flask server in a separate thread"""
        print(f"🌐 Starting Flask server on port {self.flask_port}...")
        
        def run_flask():
            try:
                self.app.run(host='0.0.0.0', port=self.flask_port, debug=False, use_reloader=False)
            except Exception as e:
                print(f"ERROR: Flask server error: {e}")
        
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        time.sleep(2)  # Give Flask time to start
        print(f"SUCCESS: Flask server running on http://localhost:{self.flask_port}")
    
    def run_interactive_menu(self):
        """Run the interactive menu"""
        try:
            partners = self.get_partners_from_database()
            
            if not partners:
                print("ERROR: No partners found in database")
                return
            
            print(f" Found {len(partners)} partners in database")
            
            # Display partners
            for i, partner in enumerate(partners, 1):
                contact_person = partner.get('contact_person_name', 'Unknown')
                contact_phone = partner.get('contact', 'No phone')
                partner_name = partner.get('partner_name', 'Unknown')
                partner_type = partner.get('partner_type', 'unknown')
                
                print(f"   {i}. {partner_name}")
                print(f"      USER: {contact_person} •  {contact_phone} • 🏢 {partner_type}")
            
            print("\n" + "=" * 60)
            print("CALLING OPTIONS:")
            print("=" * 60)
            print("1.  Call specific partner (enter partner number)")
            print("2.  Call ALL partners simultaneously")
            print("3.  Refresh partner list from database")
            print("4.  View call storage statistics")
            print("\n" + "=" * 60)
            print("7. 🔍 Demonstrate getcallstobedone function LIVE")
            print("8.  Call scheduled contacts with timezone greetings")
            print("9. 🧪 Test timezone greeting system")
            print("\n" + "=" * 60)
            print("10. 🚪 Exit system")
            print("=" * 60)
            
            while True:
                try:
                    choice = input("\n🎯 Enter your choice: ").strip()
                    
                    if choice == "10":
                        break
                    elif choice == "1":
                        partner_num = input("Enter partner number: ").strip()
                        try:
                            idx = int(partner_num) - 1
                            if 0 <= idx < len(partners):
                                result = self.call_specific_partner(partners, idx)
                                print(f" Call result: {result}")
                            else:
                                print("ERROR: Invalid partner number")
                        except ValueError:
                            print("ERROR: Please enter a valid number")
                    
                    elif choice == "2":
                        results = self.call_all_partners(partners)
                        print(f" Called {len(results)} partners")
                        for result in results:
                            status = result.get('status', 'unknown')
                            partner = result.get('partner_name', 'Unknown')
                            print(f"  {partner}: {status}")
                    
                    elif choice == "3":
                        partners = self.get_partners_from_database()
                        print(f" Refreshed: {len(partners)} partners loaded")
                    
                    else:
                        print("ERROR: Invalid choice. Please try again.")
                        
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"ERROR: Error: {e}")
        
        except Exception as e:
            print(f"ERROR: Menu error: {e}")
    
    def call_specific_partner(self, partners: List[Dict[str, Any]], partner_index: int) -> Dict[str, Any]:
        """Call a specific partner by index"""
        try:
            partner = partners[partner_index]
            contact = partner.get('contact', '')
            name = partner.get('partner_name', 'Unknown')
            
            if contact and contact.isdigit():
                # Add country code if not present
                if not contact.startswith('+'):
                    contact = '+91' + contact  # Assuming India, adjust as needed
                
                return self.make_call(contact, name)
            else:
                return {'status': 'error', 'message': f'Invalid contact number: {contact}'}
                
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def shutdown(self):
        """Shutdown the system"""
        print("STOP: Shutting down system...")
        
        # Close ngrok tunnel
        if self.ngrok_process:
            self.ngrok_process.terminate()
            print("SUCCESS: Ngrok tunnel closed")
        
        # Clean up OpenAI connections
        for call_sid in list(self.realtime_handler.connections.keys()):
            self.realtime_handler.cleanup_connection(call_sid)
        
        print("SUCCESS: System shutdown complete")
    
    def setup_flask_routes(self):
        """Setup Flask routes (compatibility method - actual routes handled by WebhookHandler)"""
        # In the modular system, Flask routes are handled by WebhookHandler
        # This method exists for compatibility with the monolithic system interface
        print(" Flask routes handled by WebhookHandler")
        pass

# Create system instance
def create_system():
    """Create and return a new telecaller system instance"""
    return TelecallerSystem()
