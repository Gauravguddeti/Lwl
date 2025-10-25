"""
WebSocket Handler for Twilio Media Streams + OpenAI Realtime API
Handles real-time audio streaming between Twilio and OpenAI
"""

import json
import logging
import asyncio
import websockets
from typing import Dict, Any

logger = logging.getLogger(__name__)

class MediaStreamHandler:
    """Handle Twilio Media Stream WebSocket connections with OpenAI Realtime"""
    
    def __init__(self, openai_api_key=None):
        self.openai_api_key = openai_api_key
        self.openai_realtime_url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01"
        self.active_connections = {}
    
    def handle_media_stream(self, ws):
        """Handle Twilio Media Stream WebSocket connections"""
        logger.info("🎙️ New Media Stream connection established")
        
        call_sid = None
        stream_sid = None
        openai_ws = None
        
        try:
            while True:
                message = ws.receive()
                if message is None:
                    break
                
                try:
                    data = json.loads(message)
                    event_type = data.get('event')
                    
                    if event_type == 'connected':
                        logger.info("📞 Twilio Media Stream connected")
                        
                    elif event_type == 'start':
                        call_sid = data.get('start', {}).get('callSid')
                        stream_sid = data.get('start', {}).get('streamSid')
                        logger.info(f"🎯 Stream started: {stream_sid} for call: {call_sid}")
                        
                        # Initialize OpenAI Realtime connection
                        openai_ws = asyncio.run(self._connect_to_openai_realtime(call_sid, ws))
                        if openai_ws:
                            self.active_connections[call_sid] = {
                                'openai_ws': openai_ws,
                                'twilio_ws': ws,
                                'stream_sid': stream_sid
                            }
                            logger.info(f"✅ OpenAI Realtime connected for call: {call_sid}")
                    
                    elif event_type == 'media':
                        # Forward audio to OpenAI Realtime
                        if call_sid and call_sid in self.active_connections:
                            audio_payload = data.get('media', {}).get('payload', '')
                            asyncio.run(self._forward_audio_to_openai(call_sid, audio_payload))
                    
                    elif event_type == 'stop':
                        logger.info(f"🛑 Stream stopped for call: {call_sid}")
                        if call_sid:
                            asyncio.run(self._cleanup_openai_connection(call_sid))
                
                except json.JSONDecodeError:
                    logger.error("❌ Invalid JSON received from Twilio")
                except Exception as e:
                    logger.error(f"❌ Error processing media stream message: {e}")
        
        except Exception as e:
            logger.error(f"❌ Media stream error: {e}")
        finally:
            if call_sid:
                asyncio.run(self._cleanup_openai_connection(call_sid))
            logger.info("🔚 Media stream connection closed")
    
    async def _connect_to_openai_realtime(self, call_sid: str, twilio_ws):
        """Connect to OpenAI Realtime API"""
        if not self.openai_api_key:
            logger.error("❌ OpenAI API key not configured")
            return None
        
        try:
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "OpenAI-Beta": "realtime=v1"
            }
            
            ws = await websockets.connect(self.openai_realtime_url, additional_headers=headers)
            
            # Configure session with database-driven system prompt
            system_prompt = self._get_database_driven_prompt(call_sid)
            
            session_config = {
                "type": "session.update",
                "session": {
                    "modalities": ["text", "audio"],
                    "instructions": system_prompt,
                    "voice": "alloy",
                    "input_audio_format": "g711_ulaw",
                    "output_audio_format": "g711_ulaw",
                    "input_audio_transcription": {
                        "model": "whisper-1"
                    }
                }
            }
            
            await ws.send(json.dumps(session_config))
            
            # Start listening for responses
            asyncio.create_task(self._listen_to_openai_responses(call_sid, ws, twilio_ws))
            
            return ws
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to OpenAI Realtime: {e}")
            return None
    
    def _get_database_driven_prompt(self, call_sid: str) -> str:
        """Get system prompt with database context"""
        try:
            from app.services.dynamic_data_fetcher import DynamicDataFetcher
            data_fetcher = DynamicDataFetcher()
            
            # Get partner and program data from database
            partner_data = data_fetcher.get_partner_data()
            program_data = data_fetcher.get_program_data()
            event_data = data_fetcher.get_event_data()
            
            if partner_data and program_data:
                partner_name = partner_data.get('partner_name', 'Educational Institution')
                contact_person = partner_data.get('contact_person', 'the decision maker')
                program_name = program_data.get('program_name', 'Professional Training Program')
                
                if event_data:
                    pricing_info = data_fetcher.format_pricing_info(program_data, event_data)
                    pricing_text = f"{pricing_info['formatted_final']} per participant with {pricing_info['discount_percentage']}% discount"
                else:
                    pricing_text = 'competitive pricing with special discounts available'
            else:
                partner_name = 'Educational Institution'
                contact_person = 'the decision maker'
                program_name = 'Professional Training Program'
                pricing_text = 'competitive pricing'
            
            return f"""You are Sarah, an enthusiastic telecaller from Learn with Leaders calling {partner_name}.

PERSONALITY: Sound excited and energetic about our {program_name}. Be conversational and natural.

OBJECTIVES:
1. Confirm you're speaking with {contact_person}
2. Introduce our {program_name} with enthusiasm  
3. Highlight educational benefits
4. Mention our special pricing: {pricing_text}
5. Schedule follow-up or send information

Keep responses short (1-2 sentences) and always ask engaging questions to continue the conversation."""
            
        except Exception as e:
            logger.error(f"Error getting database context: {e}")
            return "You are Sarah from Learn with Leaders calling about educational programs. Be enthusiastic and helpful!"
    
    async def _forward_audio_to_openai(self, call_sid: str, audio_payload: str):
        """Forward audio from Twilio to OpenAI"""
        if call_sid not in self.active_connections:
            return
        
        try:
            openai_ws = self.active_connections[call_sid]['openai_ws']
            
            audio_append = {
                "type": "input_audio_buffer.append",
                "audio": audio_payload
            }
            
            await openai_ws.send(json.dumps(audio_append))
            
        except Exception as e:
            logger.error(f"❌ Error forwarding audio to OpenAI: {e}")
    
    async def _listen_to_openai_responses(self, call_sid: str, openai_ws, twilio_ws):
        """Listen for OpenAI responses and forward to Twilio"""
        try:
            async for message in openai_ws:
                data = json.loads(message)
                
                if data.get("type") == "response.audio.delta":
                    # Forward audio response back to Twilio
                    audio_data = data.get("delta", "")
                    if audio_data and call_sid in self.active_connections:
                        await self._send_audio_to_twilio(call_sid, audio_data, twilio_ws)
                
                elif data.get("type") == "response.text.done":
                    # Log AI response for debugging
                    text = data.get("response", {}).get("output", [{}])[0].get("content", [{}])[0].get("text", "")
                    logger.info(f"🤖 AI Response: {text}")
        
        except Exception as e:
            logger.error(f"❌ Error listening to OpenAI responses: {e}")
    
    async def _send_audio_to_twilio(self, call_sid: str, audio_data: str, twilio_ws):
        """Send audio response back to Twilio"""
        try:
            if call_sid in self.active_connections:
                stream_sid = self.active_connections[call_sid]['stream_sid']
                
                media_message = {
                    "event": "media",
                    "streamSid": stream_sid,
                    "media": {
                        "payload": audio_data
                    }
                }
                
                # Send to Twilio WebSocket
                twilio_ws.send(json.dumps(media_message))
                
        except Exception as e:
            logger.error(f"❌ Error sending audio to Twilio: {e}")
    
    async def _cleanup_openai_connection(self, call_sid: str):
        """Cleanup OpenAI connection"""
        if call_sid in self.active_connections:
            try:
                connection = self.active_connections[call_sid]
                if 'openai_ws' in connection:
                    await connection['openai_ws'].close()
                del self.active_connections[call_sid]
                logger.info(f"🧹 Cleaned up connections for call: {call_sid}")
            except Exception as e:
                logger.error(f"❌ Error cleaning up connection: {e}")
