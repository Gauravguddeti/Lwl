"""
OpenAI Realtime API Service for fast, conversational AI responses
Handles real-time voice conversations with contextual greetings and program explanations
"""

import asyncio
import websockets
import json
import base64
import logging
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class OpenAIRealtimeService:
    """Service for handling OpenAI Realtime API conversations"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.websocket_url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01"
        self.active_connections: Dict[str, Any] = {}
        
    async def create_session(self, call_sid: str, context: Dict[str, Any]) -> bool:
        """Create a new realtime conversation session"""
        try:
            # Connect to OpenAI Realtime API
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "OpenAI-Beta": "realtime=v1"
            }
            
            # Try to connect with headers (websockets version compatibility)
            try:
                websocket = await websockets.connect(
                    self.websocket_url,
                    extra_headers=headers
                )
            except TypeError:
                # Fallback for older websockets versions
                logger.warning("Using fallback WebSocket connection without custom headers")
                websocket = await websockets.connect(self.websocket_url)
            
            # Store connection
            self.active_connections[call_sid] = {
                'websocket': websocket,
                'context': context,
                'conversation_state': 'greeting'
            }
            
            # Initialize session with conversation instructions
            await self._initialize_session(call_sid, context)
            
            logger.info(f"✅ OpenAI Realtime session created for call {call_sid}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create OpenAI Realtime session: {e}")
            return False
    
    async def _initialize_session(self, call_sid: str, context: Dict[str, Any]):
        """Initialize the conversation with context and instructions"""
        
        # Get current time for greeting
        current_hour = datetime.now().hour
        if current_hour < 12:
            greeting = "Good morning"
        elif current_hour < 17:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"
        
        # Build conversation instructions
        partner_name = context.get('partner_name', 'valued customer')
        program_name = context.get('program_name', 'our program')
        program_description = context.get('program_description', 'our educational program')
        event_details = context.get('event_details', 'upcoming events')
        
        instructions = f"""You are an AI telecaller for educational programs. Your conversation flow should be:

1. GREETING: Start with "{greeting}! This is an AI assistant calling from the education team."

2. IDENTITY CONFIRMATION: "Am I speaking with {partner_name}? I'm calling to discuss {program_name}."

3. PROGRAM EXPLANATION: If confirmed, explain: "{program_description}. {event_details}"

4. ENGAGEMENT: Ask if they have questions and provide helpful information about enrollment, schedules, or benefits.

IMPORTANT RULES:
- Keep responses SHORT and CONVERSATIONAL (1-2 sentences max)
- Speak FAST with natural pace
- If they say no/wrong person, apologize and end call politely
- If they show interest, provide specific details about programs and events
- Always sound professional but friendly
- End call within 2-3 minutes maximum

Current context:
- Partner: {partner_name}
- Program: {program_name}
- Description: {program_description}
- Events: {event_details}
"""

        # Send minimal session configuration
        session_config = {
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "instructions": instructions,
                "voice": "alloy",
                "temperature": 0.8
            }
        }
        
        websocket = self.active_connections[call_sid]['websocket']
        await websocket.send(json.dumps(session_config))
        
        # Wait a moment for session to be configured
        await asyncio.sleep(0.5)
        
        # Start the conversation with immediate greeting
        greeting_message = f"{greeting}! This is an AI assistant calling from the education team. Am I speaking with {partner_name}? I'm calling to discuss {program_name}."
        
        # Create a conversation item to start the call
        conversation_item = {
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": greeting_message
                    }
                ]
            }
        }
        await websocket.send(json.dumps(conversation_item))
        
        # Trigger response generation
        response_create = {
            "type": "response.create"
        }
        await websocket.send(json.dumps(response_create))
        
        logger.info(f"✅ Session initialized and conversation started for call {call_sid}")
    
    async def handle_audio_input(self, call_sid: str, audio_data: bytes):
        """Handle incoming audio from the call"""
        if call_sid not in self.active_connections:
            logger.warning(f"No active connection for call {call_sid}")
            return
        
        try:
            # Convert audio to base64
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            # Send audio to OpenAI
            audio_message = {
                "type": "input_audio_buffer.append",
                "audio": audio_base64
            }
            
            websocket = self.active_connections[call_sid]['websocket']
            await websocket.send(json.dumps(audio_message))
            
        except Exception as e:
            logger.error(f"❌ Error handling audio input: {e}")
    
    async def handle_messages(self, call_sid: str, audio_callback):
        """Handle incoming messages from OpenAI and route audio responses"""
        if call_sid not in self.active_connections:
            return
        
        try:
            websocket = self.active_connections[call_sid]['websocket']
            
            async for message in websocket:
                data = json.loads(message)
                message_type = data.get('type')
                
                if message_type == 'response.audio.delta':
                    # Stream audio response back to call
                    audio_base64 = data.get('delta', '')
                    if audio_base64:
                        audio_data = base64.b64decode(audio_base64)
                        await audio_callback(audio_data)
                
                elif message_type == 'response.audio_transcript.delta':
                    # Log what AI is saying for debugging
                    transcript = data.get('delta', '')
                    logger.info(f"🤖 AI saying: {transcript}")
                
                elif message_type == 'conversation.item.input_audio_transcription.completed':
                    # Log what user said
                    transcript = data.get('transcript', '')
                    logger.info(f"👤 User said: {transcript}")
                
                elif message_type == 'response.done':
                    # Response completed
                    logger.info("✅ AI response completed")
                
                elif message_type == 'error':
                    logger.error(f"❌ OpenAI Realtime error: {data}")
                
        except Exception as e:
            logger.error(f"❌ Error handling OpenAI messages: {e}")
        finally:
            # Clean up connection
            if call_sid in self.active_connections:
                del self.active_connections[call_sid]
    
    async def end_conversation(self, call_sid: str):
        """End the conversation and clean up"""
        if call_sid in self.active_connections:
            try:
                websocket = self.active_connections[call_sid]['websocket']
                await websocket.close()
                logger.info(f"✅ Ended OpenAI Realtime session for call {call_sid}")
            except Exception as e:
                logger.error(f"❌ Error ending conversation: {e}")
            finally:
                del self.active_connections[call_sid]
    
    def get_conversation_context(self, partner_id: int, program_id: int, event_id: Optional[int] = None, db_service=None) -> Dict[str, Any]:
        """Get conversation context from database"""
        try:
            # Return defaults if no database service provided
            if db_service is None:
                logger.warning("No database service provided, using defaults")
                return {
                    'partner_name': 'valued customer',
                    'partner_email': '',
                    'partner_phone': '',
                    'program_name': 'our educational program',
                    'program_description': 'comprehensive learning experience',
                    'program_duration': '',
                    'event_name': 'upcoming sessions',
                    'event_date': 'soon',
                    'event_time': 'flexible timing',
                    'event_location': 'convenient locations',
                    'event_details': 'We have several exciting sessions planned. Our team will be happy to discuss the details with you.'
                }
            
            # Get partner details
            partner = db_service.get_partner_by_id(partner_id)
            if not partner:
                logger.warning(f"Partner {partner_id} not found, using defaults")
                partner = {'name': 'valued customer', 'email': '', 'phone_number': ''}
            
            # Get program details
            program = db_service.get_program_by_id(program_id)
            if not program:
                logger.warning(f"Program {program_id} not found, using defaults")
                program = {'name': 'our educational program', 'description': 'comprehensive learning experience', 'duration': ''}
            
            # For events, use general information since we removed event selection
            event_details = f"We have several upcoming sessions for {program.get('name', 'this program')}. Our team will be happy to discuss the schedule and enrollment details with you."
            
            return {
                'partner_name': partner.get('name', 'valued customer'),
                'partner_email': partner.get('email', ''),
                'partner_phone': partner.get('phone_number', ''),
                'program_name': program.get('name', 'our educational program'),
                'program_description': program.get('description', 'comprehensive learning experience'),
                'program_duration': program.get('duration', ''),
                'event_name': 'upcoming sessions',
                'event_date': 'soon',
                'event_time': 'flexible timing',
                'event_location': 'convenient locations',
                'event_details': event_details
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting conversation context: {e}")
            return {
                'partner_name': 'valued customer',
                'partner_email': '',
                'partner_phone': '',
                'program_name': 'our educational program',
                'program_description': 'comprehensive learning experience',
                'program_duration': '',
                'event_name': 'upcoming sessions',
                'event_date': 'soon',
                'event_time': 'flexible timing',
                'event_location': 'convenient locations',
                'event_details': 'We have several exciting sessions planned. Our team will be happy to discuss the details with you.'
            }
