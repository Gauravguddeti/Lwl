"""
OpenAI Realtime API integration for AI Telecaller System
Handles WebSocket connections, audio streaming, and real-time conversation
"""

import os
import json
import asyncio
import websockets
import threading
import time
from typing import Dict, Any, Optional

class RealtimeHandler:
    """Handles OpenAI Realtime API WebSocket connections and streaming"""
    
    def __init__(self, openai_api_key: str):
        self.openai_api_key = openai_api_key
        self.connections = {}  # Store active connections
    
    def connect_to_openai_realtime_websocket(self, call_sid: str, system_prompt_func=None, call_context=None, connection_storage=None):
        """Connect to OpenAI Realtime WebSocket - EXACT API from monolithic"""
        return self.create_realtime_connection(call_sid, system_prompt_func, call_context, connection_storage)
    
    def create_realtime_connection(self, call_sid: str, system_prompt_func=None, call_context=None, connection_storage=None):
        """Connect to OpenAI Realtime API via WebSocket - ASYNC IMPLEMENTATION"""
        print(f"🔗 Connecting to OpenAI Realtime API for call: {call_sid}")
        
        try:
            # OpenAI Realtime API WebSocket URL - MODEL FROM ENVIRONMENT
            openai_model = os.getenv('OPENAI_REALTIME_MODEL', 'gpt-4o-mini-realtime-preview-2024-12-17')
            url = f"wss://api.openai.com/v1/realtime?model={openai_model}"
            
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "OpenAI-Beta": "realtime=v1"
            }
            
            print("🌐 Establishing WebSocket connection to OpenAI Realtime...")
            print(f"📡 Model: {openai_model}")
            
            # Create real WebSocket connection (async context)
            loop = asyncio.new_event_loop()
            
            async def create_connection_and_keep_running():
                try:
                    # Set this loop as the running loop for this thread
                    asyncio.set_event_loop(loop)
                    
                    ws = await websockets.connect(url, additional_headers=headers)
                    print("✅ OpenAI WebSocket connection established!")
                    
                    # Wait for session.created response first
                    print("🔄 Waiting for session.created...")
                    initial_response = await asyncio.wait_for(ws.recv(), timeout=10.0)
                    response_data = json.loads(initial_response)
                    print(f"📥 Initial response: {response_data.get('type', 'unknown')}")
                    
                    # Configure session with voice and instructions
                    openai_voice = os.getenv('OPENAI_REALTIME_VOICE', 'alloy')
                    system_instructions = system_prompt_func(call_sid) if system_prompt_func else "You are a helpful assistant."
                    
                    session_config = {
                        "type": "session.update",
                        "session": {
                            "modalities": ["text", "audio"],
                            "instructions": system_instructions,
                            "voice": openai_voice,  # Voice from environment
                            "input_audio_format": "g711_ulaw",
                            "output_audio_format": "g711_ulaw",
                            "input_audio_transcription": {
                                "model": "whisper-1"
                            },
                            "turn_detection": {
                                "type": "server_vad",
                                "threshold": 0.7,  # Less sensitive to prevent false interruptions (EXACT MONOLITHIC SETTING)
                                "prefix_padding_ms": 300,  # Add padding for better capture
                                "silence_duration_ms": 1200  # Longer pause before stopping (1.2 seconds) (EXACT MONOLITHIC SETTING)
                            },
                            "temperature": 0.7,  # More natural responses (original setting)
                            "max_response_output_tokens": 800  # Allow complete responses without cutting off (original setting)
                        }
                    }
                    
                    await ws.send(json.dumps(session_config))
                    print(f"⚙️ Configured OpenAI session with {openai_voice} voice and improved VAD settings")
                    
                    # Wait for session.updated response (EXACT MONOLITHIC TIMEOUT)
                    print("🔄 Waiting for session.updated...")
                    update_response = await asyncio.wait_for(ws.recv(), timeout=10.0)  # EXACT MONOLITHIC SETTING
                    update_data = json.loads(update_response)
                    print(f"📥 Update response: {update_data.get('type', 'unknown')}")
                    
                    # CRITICAL: Send initial greeting immediately (like original system)
                    await self.send_initial_greeting(ws, call_sid, system_prompt_func, call_context)
                    
                    return ws  # Return the WebSocket for dictionary creation
                except Exception as conn_error:
                    print(f"❌ Connection setup error: {conn_error}")
                    import traceback
                    traceback.print_exc()
                    raise
            
            # Run the connection setup and start the loop
            def run_loop():
                """Run the event loop in a separate thread"""
                asyncio.set_event_loop(loop)
                # Start the connection
                openai_ws = loop.run_until_complete(create_connection_and_keep_running())
                
                # Store the WebSocket (use external storage if provided, like monolithic system)
                if connection_storage is not None:
                    connection_storage[call_sid] = {
                        'websocket': openai_ws,
                        'loop': loop,
                        'call_sid': call_sid,
                        'connected': True
                    }
                else:
                    self.connections[call_sid] = {
                        'websocket': openai_ws,
                        'loop': loop,
                        'call_sid': call_sid,
                        'connected': True
                    }
                
                print(f"✅ OpenAI Realtime connection fully established for {call_sid}")
                
                # KEEP THE LOOP RUNNING FOREVER (until call ends)
                try:
                    loop.run_forever()
                except Exception as e:
                    print(f"❌ Event loop error: {e}")
                finally:
                    print(f"🔄 Event loop stopped for call {call_sid}")
            
            # Start the loop in a thread
            loop_thread = threading.Thread(target=run_loop, daemon=True)
            loop_thread.start()
            
            # Wait for connection to be established (check both storages like monolithic)
            max_wait = 15  # 15 seconds max
            waited = 0
            connection_store = connection_storage if connection_storage is not None else self.connections
            while call_sid not in connection_store and waited < max_wait:
                time.sleep(0.1)
                waited += 0.1
            
            if call_sid in connection_store:
                return connection_store[call_sid]
            else:
                print("❌ Timeout waiting for OpenAI connection")
                return None
                
        except Exception as e:
            print(f"❌ Failed to connect to OpenAI Realtime: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def forward_caller_audio_to_openai_async(self, openai_ws, audio_payload: str):
        """Forward ONLY caller audio to OpenAI with proper async handling - NO FEEDBACK LOOP (exact copy from original)"""
        if not openai_ws:
            return
            
        try:
            # Audio is already in g711 μ-law format from Twilio - no conversion needed
            # ONLY append - let OpenAI's server VAD handle speech detection
            audio_message = {
                "type": "input_audio_buffer.append",
                "audio": audio_payload
            }
            
            # Send to OpenAI (append only, no commit) - ASYNC SEND
            await openai_ws.send(json.dumps(audio_message))
            
            # DO NOT COMMIT - let OpenAI's server VAD detect speech boundaries
            # The turn_detection: server_vad will automatically commit when appropriate
            
        except Exception as e:
            print(f"❌ Error forwarding caller audio to OpenAI: {e}")
            import traceback
            traceback.print_exc()
    
    def openai_to_twilio_loop(self, openai_ws, twilio_ws, stream_sid: str, call_sid: str, openai_loop):
        """SEPARATE LOOP: Handle OpenAI to Twilio audio streaming ONLY - OPTIMIZED PERFORMANCE (exact copy from original)"""
        print(f"🔊 Starting OpenAI to Twilio loop for call: {call_sid}")
        
        async def async_listener():
            try:
                import base64
                
                print("🔊 Starting async OpenAI listener...")
                print(f"🔗 WebSocket state: {openai_ws}")
                response_count = 0
                active_response_id = None  # Track active response to prevent invalid cancellation
                
                # Test if WebSocket is actually working (like original)
                try:
                    print("🧪 Testing WebSocket connection...")
                    # Don't ping - OpenAI Realtime doesn't support ping
                    print("✅ WebSocket ready for messages")
                except Exception as ping_error:
                    print(f"❌ WebSocket setup failed: {ping_error}")
                    return
                
                while True:
                    try:
                        print("🔄 Waiting for OpenAI message...")
                        # ASYNC RECEIVE with timeout to prevent hanging (EXACT MONOLITHIC TIMEOUT)
                        message = await asyncio.wait_for(openai_ws.recv(), timeout=30.0)  # EXACT MONOLITHIC SETTING
                        if not message:
                            print("🔌 OpenAI WebSocket closed in audio loop")
                            break
                            
                        print(f"📨 Received message from OpenAI: {len(message) if message else 0} characters")
                        response_data = json.loads(message)
                        response_type = response_data.get('type')
                        response_count += 1
                        
                        print(f"� OpenAI Response #{response_count}: {response_type}")
                        
                        # DEBUG: Print all response details for audio-related events (like original)
                        if 'audio' in response_type or 'delta' in response_type:
                            print(f"🎧 AUDIO DEBUG - Type: {response_type}, Data keys: {list(response_data.keys())}")
                            if 'delta' in response_data:
                                delta_data = response_data.get('delta', '')
                                print(f"🎧 AUDIO DEBUG - Delta length: {len(delta_data) if delta_data else 0}")
                        
                        # Enhanced logging for debugging (exact copy from original)
                        if response_type == 'response.audio.delta':
                            audio_b64 = response_data.get('delta', '')
                            if audio_b64:
                                print(f"🔊 AI SPEAKING: Sending audio chunk (length: {len(audio_b64)}) to Twilio")
                                try:
                                    # Audio is already in g711 μ-law format - no conversion needed
                                    twilio_audio = {
                                        "event": "media",
                                        "streamSid": stream_sid,
                                        "media": {
                                            "payload": audio_b64
                                        }
                                    }
                                    
                                    twilio_ws.send(json.dumps(twilio_audio))
                                    print(f"✅ Sent audio chunk to Twilio successfully")
                                    
                                except Exception as e:
                                    print(f"❌ Error sending AI audio: {e}")
                                    import traceback
                                    traceback.print_exc()
                            else:
                                print("⚠️ Empty audio delta received")
                        
                        elif response_type == 'response.audio_transcript.delta':
                            transcript = response_data.get('delta', '')
                            if transcript:
                                print(f"�️ AI saying: {transcript}")
                        
                        elif response_type == 'conversation.item.input_audio_transcription.completed':
                            transcript = response_data.get('transcript', '')
                            if transcript:
                                print(f"📝 Caller said: {transcript}")
                        
                        elif response_type == 'response.created':
                            print("🎤 OpenAI creating response...")
                            active_response_id = response_data.get('response', {}).get('id', None)
                            print(f"📝 Response ID: {active_response_id}")
                        
                        elif response_type == 'response.done':
                            print("✅ OpenAI response completed")
                            response_status = response_data.get('response', {}).get('status', 'unknown')
                            print(f"📊 Response status: {response_status}")
                            active_response_id = None  # Clear active response
                        
                        elif response_type == 'input_audio_buffer.speech_started':
                            print("⚡ INTERRUPTION: Caller started speaking")
                            # Only send cancel if there's an active response (improved from monolithic)
                            if active_response_id:
                                print(f"🛑 Cancelling active response: {active_response_id}")
                                try:
                                    interrupt_signal = {
                                        "type": "response.cancel"
                                    }
                                    await openai_ws.send(json.dumps(interrupt_signal))
                                    print("✅ Sent interruption signal to OpenAI")
                                    # Reset state immediately to prevent duplicate cancellations
                                    active_response_id = None
                                except Exception as e:
                                    print(f"❌ Error sending interrupt: {e}")
                            else:
                                print("ℹ️ No active response to cancel - caller speaking normally")
                        
                        elif response_type == 'input_audio_buffer.speech_stopped':
                            print("🔇 Speech stopped - processing caller input")
                        
                        elif response_type == 'input_audio_buffer.committed':
                            print("📝 Audio buffer committed - OpenAI processing speech")
                        
                        elif response_type == 'error':
                            error_details = response_data.get('error', {})
                            error_code = error_details.get('code', 'unknown')
                            print(f"❌ OpenAI Error: {error_details}")
                            
                            # Don't break on expected cancellation errors (from monolithic)
                            if error_code == 'response_cancel_not_active':
                                print("ℹ️ Ignoring expected cancellation error")
                            elif error_code == 'input_audio_buffer_commit_empty':
                                print("ℹ️ Ignoring empty audio buffer error")
                            else:
                                print("🔄 Continuing despite error...")
                        
                        else:
                            print(f"ℹ️ Other OpenAI event: {response_type}")
                            # Print full response for debugging unknown events (like original)
                            if response_type not in ['session.created', 'session.updated', 'response.output_item.added', 'response.output_item.done']:
                                print(f"🔍 Full response: {response_data}")
                    
                    except asyncio.TimeoutError:
                        print("⏰ OpenAI listener timeout - checking connection")
                        continue
                    except Exception as inner_e:
                        print(f"❌ Error in OpenAI listener inner loop: {inner_e}")
                        break
                        
            except RuntimeError as runtime_error:
                if "Event loop is closed" in str(runtime_error):
                    print("⚠️ Event loop closed - gracefully stopping OpenAI listener")
                else:
                    print(f"❌ Runtime error in OpenAI listener: {runtime_error}")
            except Exception as e:
                print(f"❌ Error in OpenAI→Twilio loop: {e}")
                import traceback
                traceback.print_exc()
        
        # Run the async listener in the OpenAI event loop (like original)
        try:
            future = asyncio.run_coroutine_threadsafe(async_listener(), openai_loop)
            print("🔊 Async OpenAI listener started successfully")
            # DON'T WAIT - let it run in background (like original)
            # The future will complete when the call ends or WebSocket closes
        except Exception as e:
            print(f"❌ Failed to start async listener: {e}")
            import traceback
            traceback.print_exc()
    
    def twilio_to_openai_loop(self, twilio_ws, openai_ws, call_sid: str, openai_loop):
        """SEPARATE LOOP: Handle Twilio to OpenAI audio forwarding ONLY - FIXED INFINITE LOOP (exact copy from original)"""
        print(f"🎤 Starting Twilio to OpenAI loop for call: {call_sid}")
        
        try:
            audio_count = 0
            while True:
                # Listen ONLY for Twilio audio events with timeout to prevent hanging
                try:
                    message = twilio_ws.receive(timeout=10)  # 10 second timeout (like original)
                    if message is None:
                        print("🔌 Twilio WebSocket closed or timeout in audio loop")
                        break
                        
                    data = json.loads(message)
                    event_type = data.get('event')
                    
                    if event_type == 'media':
                        # ONLY caller audio - forward to OpenAI
                        payload = data.get('media', {}).get('payload', '')
                        
                        if payload and openai_ws:
                            audio_count += 1
                            # Throttle audio logging to prevent spam (like original)
                            if audio_count % 100 == 0:  # Log every 100th audio packet
                                print(f"🎤 CALLER→OPENAI: Processed {audio_count} audio packets")
                            
                            # Run the async send in the OpenAI event loop (exact copy from original)
                            try:
                                future = asyncio.run_coroutine_threadsafe(
                                    self.forward_caller_audio_to_openai_async(openai_ws, payload),
                                    openai_loop
                                )
                                # Don't wait for completion - async fire-and-forget for performance
                            except Exception as audio_error:
                                print(f"❌ Error forwarding audio: {audio_error}")
                    
                    elif event_type == 'stop':
                        print("🛑 Twilio stream stopped - committing final audio buffer")
                        # Only commit if we have audio to commit
                        if audio_count > 5:  # Only commit if we processed meaningful audio
                            try:
                                commit_message = {"type": "input_audio_buffer.commit"}
                                future = asyncio.run_coroutine_threadsafe(
                                    openai_ws.send(json.dumps(commit_message)),
                                    openai_loop
                                )
                                future.result(timeout=2)  # Wait max 2 seconds for commit
                                print("📝 Final audio buffer committed to OpenAI")
                            except Exception as commit_error:
                                print(f"⚠️ Error committing final audio: {commit_error}")
                        else:
                            print("ℹ️ Insufficient audio to commit - skipping final commit")
                        break
                        
                    elif event_type == 'connected':
                        print("� Twilio connection confirmed in audio loop")
                        
                    else:
                        # Log other events but don't process them (like original)
                        print(f"📋 Twilio event (ignored): {event_type}")
                        
                except Exception as e:
                    error_message = str(e)
                    if "Connection closed" in error_message:
                        print(f"🔌 Twilio WebSocket connection closed normally for call: {call_sid}")
                        break
                    else:
                        print(f"❌ Error in Twilio→OpenAI loop iteration: {e}")
                        # Don't break on single error - continue processing (like original)
                        continue
                    
        except Exception as e:
            print(f"❌ Twilio→OpenAI loop error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            print(f"🎤 Twilio→OpenAI loop stopped for call: {call_sid} (processed {audio_count} audio packets)")
            # Signal OpenAI that audio input is done (like original) - only if we processed audio
            try:
                if openai_ws and openai_loop and audio_count > 0:
                    final_commit = {"type": "input_audio_buffer.commit"}
                    asyncio.run_coroutine_threadsafe(
                        openai_ws.send(json.dumps(final_commit)),
                        openai_loop
                    )
                    print("📝 Sent final audio commit signal")
                elif audio_count == 0:
                    print("ℹ️ No audio to commit - skipping final commit")
            except:
                pass
    
    async def send_initial_greeting(self, ws, call_sid: str, system_prompt_func=None, call_context=None):
        """Send initial greeting to start the conversation immediately (from original system)"""
        try:
            print("🚀 STARTING initial greeting process...")
            
            # Get call context for personalized greeting (exactly like original)
            partner_name = "your institution"
            contact_person = "there"
            
            # Get partner info from call context (like original system)
            if call_context:
                partner_info = call_context.get('partner_info', {})
                partner_name = partner_info.get('partner_name', 'your institution')  # FIXED: use 'partner_name' like monolithic
                contact_person = partner_info.get('contact_person_name', 'there')
                print(f"📋 Using personalized greeting for {partner_name}, contact: {contact_person}")
            else:
                print("⚠️ No call context available - using generic greeting")
            
            # Get appropriate time greeting
            from datetime import datetime
            current_hour = datetime.now().hour
            time_greeting = "Good morning" if current_hour < 12 else "Good afternoon" if current_hour < 17 else "Good evening"
            
            # DIRECT APPROACH: Send personalized greeting (exact copy from original)
            greeting_text = f"Start the call immediately. Say: '{time_greeting}! This is Sarah calling from Learn with Leaders. I hope I'm not catching you at a busy time. I'm calling about some exciting educational opportunities for {partner_name}. Am I speaking with {contact_person}?'"
            
            greeting_message = {
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text", 
                            "text": greeting_text
                        }
                    ]
                }
            }
            
            await ws.send(json.dumps(greeting_message))
            print("📝 Sent greeting message to conversation")
            
            # Immediately trigger response (exact copy from original)
            response_create = {
                "type": "response.create",
                "response": {
                    "modalities": ["audio", "text"],
                    "instructions": "Speak the greeting immediately as Sarah the telecaller. Be enthusiastic and professional. Complete your full response without cutting off.",
                    "max_output_tokens": 800  # Allow complete responses
                }
            }
            
            await ws.send(json.dumps(response_create))
            print("✅ Triggered AI response - should start speaking now!")
            
            # Log that we've attempted to start
            print("🎯 Greeting sequence completed - waiting for OpenAI audio response")
            
        except Exception as e:
            print(f"❌ CRITICAL ERROR in initial greeting: {e}")
            import traceback
            traceback.print_exc()

    def cleanup_connection(self, call_sid: str):
        """Clean up OpenAI connection for a call (improved cleanup like original)"""
        try:
            if call_sid in self.connections:
                connection = self.connections[call_sid]
                
                # Simple cleanup approach (like original)
                loop = connection.get('loop')
                if loop and not loop.is_closed():
                    try:
                        # Stop the loop gracefully
                        loop.call_soon_threadsafe(loop.stop)
                    except Exception as loop_error:
                        print(f"⚠️ Error stopping event loop: {loop_error}")
                
                del self.connections[call_sid]
                print(f"🧹 Cleaned up OpenAI connection for call: {call_sid}")
        except Exception as e:
            print(f"❌ Error cleaning up connection: {e}")

# Global realtime handler instance will be created by the main system
realtime_handler = None
