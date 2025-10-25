"""
Webhook endpoints for AI Telecaller System
Handles Twilio webhooks, status callbacks, and health checks
"""

import json
import threading
import time
from datetime import datetime
from flask import request, jsonify
from ..core.config import TWILIO_AVAILABLE, VoiceResponse, Connect, Stream
from app.services.dynamic_data_fetcher import dynamic_data_fetcher

class WebhookHandler:
    """Handles all webhook endpoints for the telecaller system"""
    
    def __init__(self, app, telecaller_system):
        self.app = app
        self.system = telecaller_system
        self.setup_webhook_routes()
    
    def setup_webhook_routes(self):
        """Setup all webhook routes"""
        
        @self.app.route('/webhook/voice', methods=['POST'])
        def voice_webhook():
            """Handle incoming voice calls - AI initiates conversation"""
            print("🔔 Voice webhook called!")
            print(f"📋 Request data: {dict(request.values)}")
            
            if not TWILIO_AVAILABLE:
                print("❌ Twilio not available")
                return jsonify({'error': 'Twilio not configured'})
            
            response = VoiceResponse()
            
            try:
                # Get call information
                call_sid = request.values.get('CallSid')
                from_number = request.values.get('From')
                to_number = request.values.get('To')
                
                print(f"📞 AI-initiated call: {call_sid} to {to_number}")
                
                # Get dynamic context for this specific partner using phone number
                # Remove the '+' and country code to match database format
                contact_number = to_number.replace('+91', '') if to_number.startswith('+91') else to_number.replace('+', '')
                contact_number = contact_number.replace('+1', '') if contact_number.startswith('+1') else contact_number
                print(f"🔍 Looking up partner data for contact: {contact_number}")
                call_context = dynamic_data_fetcher.get_complete_call_context(contact_number=contact_number)
                
                # Debug: Print what context was fetched
                print(f"📊 Context fetched:")
                print(f"   Partner: {call_context.get('partner_info', {}).get('name', 'None')}")
                print(f"   Program: {call_context.get('program_info', {}).get('name', 'None')}")
                print(f"   Event: {call_context.get('event_info', {}).get('datetime', 'None')}")
                
                # Check if this is a scheduled call with timezone-aware greeting
                # (Only use timezone greeting for scheduled calls, not regular IVR calls)
                is_scheduled_call = hasattr(self.system, 'use_timezone_greeting') and self.system.use_timezone_greeting
                scheduled_call_data = None
                
                if is_scheduled_call:
                    # This is a scheduled call - use timezone-aware greeting
                    try:
                        from app.services.simple_ivr_service import simple_ivr_service
                        all_calls = simple_ivr_service.get_all_calls_to_be_done()
                        
                        # Find the matching call by phone number
                        for call in all_calls:
                            call_phone = call.get('contact_phone', '').strip()
                            if call_phone == contact_number or call_phone == to_number.replace('+', ''):
                                scheduled_call_data = call
                                print(f"📅 Found scheduled call data for {call['contact_person_name']}")
                                break
                                
                        if not scheduled_call_data:
                            print(f"⚠️ No scheduled call data found for {contact_number}, using context data")
                            # Create fallback call data from context
                            scheduled_call_data = {
                                'contact_phone': contact_number,
                                'contact_person_name': call_context.get('partner_info', {}).get('contact_person_name', 'Unknown'),
                                'partner_name': call_context.get('partner_info', {}).get('name', 'Unknown'),
                                'call_datetime': datetime.now()
                            }
                    except Exception as e:
                        print(f"❌ Error fetching scheduled call data: {e}")
                        # Create fallback data
                        scheduled_call_data = {
                            'contact_phone': contact_number,
                            'contact_person_name': call_context.get('partner_info', {}).get('contact_person_name', 'Unknown'),
                            'partner_name': call_context.get('partner_info', {}).get('name', 'Unknown'),
                            'call_datetime': datetime.now()
                        }
                
                # Initialize conversation state  
                from ..core.conversation import ConversationState
                conversation_state = ConversationState(
                    messages=[],
                    partner_info=call_context.get('partner_info', {}),
                    program_info=call_context.get('program_info', {}),
                    event_info=call_context.get('event_info', {}),
                    call_sid=call_sid,
                    current_context="greeting",
                    engagement_level="high",
                    user_interests=[],
                    questions_asked=0,
                    sentiment_trend=[],
                    scheduled_call_data=scheduled_call_data or {},
                    topics_discussed=[],
                    repeated_questions={},
                    conversation_summary="",
                    last_ai_response="",
                    pricing_mentioned=False,
                    schedule_mentioned=False,
                    features_mentioned=[]
                )
                
                # Store the conversation state
                self.system.conversation_states[call_sid] = conversation_state
                
                # Create media stream to handle real-time audio
                connect = Connect()
                connect.stream(url=f'wss://{request.host}/media-stream')
                response.append(connect)
                
                # Connect to OpenAI Realtime WebSocket in background
                self.system.connect_to_openai_realtime_websocket(call_sid)
                
                print(f"✅ Call setup complete for {call_sid}")
                return str(response)
                
            except Exception as e:
                print(f"❌ Error in voice webhook: {e}")
                import traceback
                traceback.print_exc()
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/webhook/call-status', methods=['POST'])
        def call_status():
            """Handle call status updates"""
            try:
                call_sid = request.values.get('CallSid')
                call_status = request.values.get('CallStatus')
                recording_url = request.values.get('RecordingUrl', '')
                
                print(f"📊 Call status update: {call_sid} -> {call_status}")
                
                # Update active call status
                if call_sid in self.system.active_calls:
                    self.system.active_calls[call_sid]['status'] = call_status
                
                # Handle call completion
                if call_status in ['completed', 'busy', 'no-answer', 'failed', 'canceled']:
                    print(f"📞 Call {call_sid} ended with status: {call_status}")
                    
                    # Finalize conversation using enhanced storage
                    self.system.finalize_conversation_with_enhanced_naming(call_sid)
                    
                    # Clean up conversation state
                    if call_sid in self.system.conversation_states:
                        del self.system.conversation_states[call_sid]
                    
                    # Clean up active call tracking
                    if call_sid in self.system.active_calls:
                        partner_name_for_download = self.system.active_calls[call_sid].get('partner_name', 'Unknown')
                        del self.system.active_calls[call_sid]
                    else:
                        partner_name_for_download = "Unknown"
                    
                    # Handle recording download (if available)
                    if recording_url:
                        recording_url_for_download = recording_url
                        
                        def delayed_download():
                            import time
                            time.sleep(10)  # Wait 10 seconds for Twilio to process
                            self.system.download_call_recording(call_sid, recording_url_for_download, partner_name_for_download)
                        
                        # Start download in background thread
                        thread = threading.Thread(target=delayed_download)
                        thread.daemon = True
                        thread.start()
                
                return jsonify({'status': 'received'})
                
            except Exception as e:
                print(f"❌ Error in call status webhook: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'ngrok_url': self.system.ngrok_url,
                'ai_model': 'gpt-4o-mini' if self.system.llm else 'fallback'
            })
        
        @self.app.route('/test', methods=['GET', 'POST'])
        def test_endpoint():
            """Simple test endpoint to verify ngrok connectivity"""
            print(f"🧪 TEST endpoint called - Method: {request.method}")
            if request.method == 'POST':
                print(f"📋 POST data: {dict(request.values)}")
            return jsonify({
                'message': 'Ngrok and Flask are working!',
                'method': request.method,
                'timestamp': datetime.now().isoformat(),
                'data': dict(request.values) if request.method == 'POST' else None
            })
