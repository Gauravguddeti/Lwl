from flask import Flask, request, jsonify, render_template
from flask_sock import Sock
import logging
from app.services.database_service import DatabaseService
from app.services.twilio_service import TwilioService
from app.services.rag_service import RAGService
from app.services.conversation_flow import ConversationFlow
from app.services.ses_templated_email_service import SESTemplatedEmailService
from app.config.settings import AppConfig
import json
from datetime import datetime
import base64

logger = logging.getLogger(__name__)

def create_flask_app(ngrok_url=None):
    """Create and configure Flask application with enhanced dashboard"""
    app = Flask(__name__, template_folder='../templates')
    sock = Sock(app)
    
    # Initialize services
    config = AppConfig()
    db_service = DatabaseService()
    twilio_service = TwilioService(ngrok_url=ngrok_url)
    templated_email_service = SESTemplatedEmailService()
    
    # Initialize AI services with proper error handling
    try:
        if config.openai_api_key:
            logger.info("🤖 Initializing AI services...")
            rag_service = RAGService(config.openai_api_key)
            conversation_flow = ConversationFlow(config.openai_api_key)
            logger.info("✅ AI services initialized successfully")
        else:
            rag_service = None
            conversation_flow = None
            logger.warning("⚠️ OpenAI API key not found - RAG and conversation flow disabled")
    except Exception as e:
        logger.error(f"❌ Error initializing AI services: {e}")
        rag_service = None
        conversation_flow = None
        logger.warning("🔄 Continuing without AI services")
    
    @app.route('/')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'service': 'AI Telecaller System',
            'version': '2.0.0',
            'ngrok_url': ngrok_url,
            'dashboard_url': f'{ngrok_url}/dashboard' if ngrok_url else '/dashboard'
        })
    
    @app.route('/dashboard')
    def dashboard():
        """Enhanced dashboard with partner, program, and event data from database"""
        try:
            # Get data from database
            partners = db_service.get_all_partners() or []
            programs = db_service.get_all_programs() or []
            events = db_service.get_program_events() or []
            
            # Get recent calls and database stats
            recent_calls = db_service.get_call_records(10) or []
            db_stats = db_service.get_database_stats()
            
            # System status
            system_status = {
                'total_partners': len(partners),
                'total_programs': len(programs), 
                'total_events': len(events),
                'twilio_connected': True,
                'database_connected': True
            }
            
            return render_template('dashboard.html',
                                 partners=partners,
                                 programs=programs,
                                 events=events,
                                 recent_calls=recent_calls,
                                 system_status=system_status,
                                 ngrok_url=ngrok_url)
            
        except Exception as e:
            logger.error(f"❌ Dashboard error: {e}")
            return f"<h1>Dashboard Error</h1><p>{str(e)}</p>"

    @app.route('/dashboard/program/<int:program_id>/events')
    def get_program_events_api(program_id):
        """Get events for a specific program"""
        try:
            logger.info(f"🔍 Fetching events for program ID: {program_id}")
            events = db_service.get_program_events(program_id)
            logger.info(f"📅 Found {len(events)} events for program {program_id}")
            return jsonify({
                'success': True,
                'events': events
            })
        except Exception as e:
            logger.error(f"Error fetching program events: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/dashboard/event/<int:event_id>/participants')
    def get_event_participants_api(event_id):
        """Get participants for a specific event"""
        try:
            participants = db_service.get_event_participants(event_id)
            return jsonify({
                'success': True,
                'participants': participants
            })
        except Exception as e:
            logger.error(f"Error fetching event participants: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/debug/verified-numbers')
    def get_verified_numbers():
        """Debug endpoint to check verified phone numbers in Twilio account"""
        try:
            # Try to get verified numbers from Twilio
            from twilio.rest import Client
            import os
            
            account_sid = os.getenv('TWILIO_ACCOUNT_SID')
            auth_token = os.getenv('TWILIO_AUTH_TOKEN')
            
            client = Client(account_sid, auth_token)
            verified_numbers = []
            
            # Get outgoing caller IDs (verified numbers)
            caller_ids = client.outgoing_caller_ids.list()
            
            for caller_id in caller_ids:
                verified_numbers.append({
                    'phone_number': caller_id.phone_number,
                    'friendly_name': caller_id.friendly_name
                })
            
            return jsonify({
                'success': True,
                'verified_numbers': verified_numbers,
                'count': len(verified_numbers),
                'message': 'These numbers can be used for testing calls with trial account'
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e),
                'message': 'Could not retrieve verified numbers'
            }), 500

    @app.route('/dashboard/call-with-program', methods=['POST'])
    def make_call_with_program():
        """Make calls to all participants of a specific event"""
        try:
            data = request.get_json()
            program_id = data.get('program_id')
            event_id = data.get('event_id')
            
            if not program_id or not event_id:
                return jsonify({
                    'success': False,
                    'error': 'Program ID and Event ID are required'
                }), 400
            
            # Get event details
            events = db_service.get_program_events(program_id)
            event = next((e for e in events if e.get('id') == event_id), None)
            
            if not event:
                return jsonify({
                    'success': False,
                    'error': 'Event not found'
                }), 404
            
            # Get participants
            participants = db_service.get_event_participants(event_id)
            call_sids = []
            
            if participants:
                for participant in participants:
                    if participant.get('phone'):
                        try:
                            program_name = event.get('program_name', 'Our Program')
                            event_name = event.get('name', 'Event')
                            
                            system_prompt = f"""You are calling {participant.get('name', 'Partner')} from Global Learning Academy about the {program_name} program.
Event: {event_name}
Event Date: {event.get('event_date', '')}
Organization: {participant.get('organization', '')}

Be professional, friendly, and provide information about the program and event. Ask if they have any questions."""
                            
                            call_response = twilio_service.make_call(
                                to_number=participant['phone'],
                                system_prompt=system_prompt,
                                call_metadata={
                                    'partner_name': participant.get('name', 'Partner'),
                                    'program_name': program_name,
                                    'event_name': event_name,
                                    'event_date': event.get('event_date', ''),
                                    'program_id': program_id,
                                    'event_id': event_id,
                                    'partner_id': participant.get('id'),
                                    'organization': participant.get('organization', '')
                                }
                            )
                            
                            if call_response and call_response.get('call_sid'):
                                call_sids.append(call_response['call_sid'])
                                logger.info(f"✅ Call initiated to {participant['phone']}: {call_response['call_sid']}")
                            else:
                                logger.error(f"❌ Failed to get call SID for {participant['phone']}")
                            
                        except Exception as call_error:
                            logger.error(f"❌ Failed to call {participant['phone']}: {call_error}")
                            continue
                
                return jsonify({
                    'success': True,
                    'total_calls': len(call_sids),
                    'call_sids': call_sids,
                    'message': f'Successfully initiated {len(call_sids)} calls for {event_name}'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'No participants found for this event'
                }), 404
                
        except Exception as e:
            logger.error(f"❌ Error making calls with program: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/dashboard/call', methods=['POST'])
    def make_individual_call():
        """Make individual call with enhanced context"""
        try:
            data = request.get_json()
            phone = data.get('phone_number')
            
            # Format phone number with Indian country code if needed
            def format_indian_phone(phone_number):
                """Format phone number with +91 country code for India"""
                if not phone_number:
                    return phone_number
                    
                # Remove any spaces, dashes, or parentheses
                clean_phone = ''.join(c for c in str(phone_number) if c.isdigit())
                
                # If it's a 10-digit number, add +91
                if len(clean_phone) == 10:
                    return f"+91{clean_phone}"
                # If it already has +91, keep it
                elif phone_number.startswith('+91'):
                    return phone_number
                # If it has 91 prefix but no +, add +
                elif len(clean_phone) == 12 and clean_phone.startswith('91'):
                    return f"+{clean_phone}"
                else:
                    return phone_number
            
            # Format the phone number properly
            phone = format_indian_phone(phone)
            partner_id = data.get('partner_id')
            event_id = data.get('event_id')
            program_id = data.get('program_id')
            
            if not phone:
                return jsonify({'error': 'Phone number is required'}), 400
            
            # Create AI context based on available information
            partner_name = "Partner"
            program_name = "Our Program"
            event_name = ""
            
            if partner_id:
                partners = db_service.get_all_partners()
                partner = next((p for p in partners if p.get('id') == partner_id), None)
                if partner:
                    partner_name = partner.get('name', 'Partner')
            
            if program_id:
                programs = db_service.get_all_programs()
                program = next((p for p in programs if p.get('id') == program_id), None)
                if program:
                    program_name = program.get('name', 'Our Program')
            
            if event_id:
                events = db_service.get_program_events()
                event = next((e for e in events if e.get('id') == event_id), None)
                if event:
                    event_name = event.get('name', '')
            
            system_prompt = f"""You are calling {partner_name} from Global Learning Academy about the {program_name} program.
{f'Event: {event_name}' if event_name else ''}

Be professional, friendly, and provide information about the program. Ask if they have any questions."""
            
            # For Twilio trial account testing, we need to use a verified number
            # Since trial accounts can only call verified numbers, let's use a verified number for testing
            
            # Use the properly formatted phone number for now
            verified_number = phone  # This is now +917276082005 thanks to format_indian_phone()
            
            # IMPORTANT: To actually make calls work, you need to verify +917276082005 in your Twilio Console
            # OR use your own verified number by uncommenting and setting below:
            # YOUR_VERIFIED_NUMBER = "+919876543210"  # Replace with your actual verified number
            # verified_number = YOUR_VERIFIED_NUMBER
            
            logger.info(f"📞 Attempting to call: {verified_number}")
            logger.info(f"🔧 If call fails with 'unverified number' error:")
            logger.info(f"   1. Verify {verified_number} in your Twilio Console")
            logger.info(f"   2. Or replace the YOUR_VERIFIED_NUMBER above with your verified number")
            
            # Make the call
            call_response = twilio_service.make_call(
                to_number=verified_number,
                system_prompt=system_prompt,
                call_metadata={
                    'partner_name': partner_name,
                    'program_name': program_name,
                    'event_name': event_name,
                    'phone': phone,
                    'partner_id': partner_id,
                    'event_id': event_id,
                    'program_id': program_id
                }
            )
            
            if call_response and call_response.get('call_sid'):
                logger.info(f"✅ Call initiated successfully - SID: {call_response['call_sid']}")
                return jsonify({
                    'success': True,
                    'message': f'Call initiated to {partner_name} ({phone}) about {program_name}',
                    'call_sid': call_response['call_sid']
                })
            else:
                logger.error("❌ Failed to initiate call - no SID returned")
                return jsonify({'error': 'Failed to initiate call'}), 500
                    
        except Exception as e:
            logger.error(f"❌ Call error: {e}")
            return jsonify({'error': str(e)}), 500

    # ==========================================
    # REAL-TIME VOICE STREAMING WEBHOOKS
    # ==========================================
    
    @app.route('/webhook/voice', methods=['GET', 'POST'])
    def voice_webhook():
        """Handle incoming Twilio voice webhook with real-time streaming"""
        try:
            logger.info("📞 Voice webhook received")
            logger.info(f"Request method: {request.method}")
            logger.info(f"Request data: {request.values}")
            
            # Create TwiML response for real-time streaming
            from twilio.twiml import VoiceResponse, Stream
            response = VoiceResponse()
            
            # Get call information
            call_sid = request.values.get('CallSid')
            from_number = request.values.get('From')
            to_number = request.values.get('To')
            
            logger.info(f"📞 Call details - SID: {call_sid}, From: {from_number}, To: {to_number}")
            
            # Get call context from database if available
            call_context = get_call_context(call_sid, to_number, from_number)
            
            # Start with a brief greeting while setting up streaming
            response.say(
                "Hello! Please hold while I connect you to our AI assistant.",
                voice='alice',
                language='en'
            )
            
            # Start media streaming for real-time AI conversation
            start_stream = Stream()
            start_stream.url = f"{request.url_root.rstrip('/')}/stream"
            start_stream.track = "both_tracks"  # Capture both inbound and outbound audio
            start_stream.name = f"call_{call_sid}"
            
            response.append(start_stream)
            
            # Keep the call alive for streaming
            response.pause(length=60)  # Allow up to 60 seconds of conversation
            
            logger.info("✅ Real-time streaming TwiML response generated")
            return str(response), 200, {'Content-Type': 'text/xml'}
            
        except Exception as e:
            logger.error(f"❌ Voice webhook error: {e}")
            # Fallback response
            from twilio.twiml import VoiceResponse
            response = VoiceResponse()
            response.say("Sorry, there was an error connecting. Please try again later.", voice='alice')
            response.hangup()
            return str(response), 200, {'Content-Type': 'text/xml'}
    
    def get_call_context(call_sid, to_number, from_number):
        """Get context for the call from database"""
        try:
            # Try to find call metadata from recent calls
            # This would contain partner info, program info, etc.
            call_context = {
                'call_sid': call_sid,
                'to_number': to_number,
                'from_number': from_number,
                'timestamp': datetime.now().isoformat()
            }
            
            # Try to get partner information based on phone number
            try:
                partners = db_service.get_all_partners()
                partner = None
                
                # Match by phone number (try both directions)
                for p in partners:
                    partner_phone = p.get('phone', '')
                    if partner_phone in [to_number, from_number]:
                        partner = p
                        break
                
                if partner:
                    call_context.update({
                        'partner_id': partner.get('id'),
                        'partner_name': partner.get('name'),
                        'partner_email': partner.get('email')
                    })
                    logger.info(f"📋 Found partner context: {partner.get('name')}")
                
            except Exception as e:
                logger.warning(f"Could not get partner context: {e}")
            
            return call_context
            
        except Exception as e:
            logger.error(f"Error getting call context: {e}")
            return {'call_sid': call_sid, 'to_number': to_number, 'from_number': from_number}
    
    @sock.route('/stream')
    def handle_media_stream(sock):
        """Handle real-time media streaming WebSocket"""
        logger.info("🎵 Media stream WebSocket connected")
        
        # Initialize conversation state
        conversation_state = {
            'call_sid': None,
            'context': {},
            'conversation_history': [],
            'audio_buffer': [],
            'is_speaking': False
        }
        
        try:
            while True:
                message = sock.receive()
                if message:
                    data = json.loads(message)
                    event_type = data.get('event')
                    
                    if event_type == 'connected':
                        logger.info("📡 Media stream connected")
                        
                    elif event_type == 'start':
                        call_sid = data.get('start', {}).get('callSid')
                        conversation_state['call_sid'] = call_sid
                        logger.info(f"🎬 Media stream started for call: {call_sid}")
                        
                        # Get call context
                        stream_data = data.get('start', {})
                        conversation_state['context'] = get_stream_context(stream_data)
                        
                        # Send initial AI greeting
                        initial_response = generate_ai_response(
                            "",  # No user input yet
                            conversation_state['context'],
                            conversation_state['conversation_history']
                        )
                        
                        if initial_response:
                            send_ai_audio_response(sock, initial_response, conversation_state)
                        
                    elif event_type == 'media':
                        # Handle incoming audio from caller
                        handle_incoming_audio(data, conversation_state, sock)
                        
                    elif event_type == 'stop':
                        logger.info("🛑 Media stream stopped")
                        break
                        
        except Exception as e:
            logger.error(f"❌ Media stream error: {e}")
        finally:
            logger.info("📴 Media stream WebSocket disconnected")
    
    def get_stream_context(stream_data):
        """Extract context from stream start data"""
        try:
            custom_parameters = stream_data.get('customParameters', {})
            call_sid = stream_data.get('callSid')
            
            # Get additional context from our database
            context = {
                'call_sid': call_sid,
                'timestamp': datetime.now().isoformat(),
                'stream_sid': stream_data.get('streamSid'),
                'account_sid': stream_data.get('accountSid')
            }
            
            # Add any custom parameters passed from the call
            context.update(custom_parameters)
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting stream context: {e}")
            return {}
    
    def handle_incoming_audio(media_data, conversation_state, sock):
        """Process incoming audio from the caller"""
        try:
            payload = media_data.get('media', {}).get('payload')
            if not payload:
                return
            
            # Add audio to buffer
            conversation_state['audio_buffer'].append(payload)
            
            # Process audio when we have enough data or silence is detected
            if should_process_audio(conversation_state):
                audio_text = transcribe_audio(conversation_state['audio_buffer'])
                
                if audio_text and audio_text.strip():
                    logger.info(f"👤 Caller said: {audio_text}")
                    
                    # Add to conversation history
                    conversation_state['conversation_history'].append({
                        'role': 'user',
                        'content': audio_text,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    # Generate AI response
                    ai_response = generate_ai_response(
                        audio_text,
                        conversation_state['context'],
                        conversation_state['conversation_history']
                    )
                    
                    if ai_response:
                        send_ai_audio_response(sock, ai_response, conversation_state)
                
                # Clear audio buffer
                conversation_state['audio_buffer'] = []
                
        except Exception as e:
            logger.error(f"Error handling incoming audio: {e}")
    
    def should_process_audio(conversation_state):
        """Determine if we should process the buffered audio"""
        # Simple implementation - process every N chunks or after silence
        buffer_size = len(conversation_state['audio_buffer'])
        return buffer_size >= 10  # Process every 10 audio chunks
    
    def transcribe_audio(audio_buffer):
        """Transcribe audio buffer to text using speech recognition"""
        try:
            if not audio_buffer:
                return ""
            
            # For now, return a placeholder - you would implement actual STT here
            # This could use OpenAI Whisper, Google Speech-to-Text, etc.
            logger.info("🎤 Transcribing audio...")
            
            # Placeholder implementation
            # In real implementation, you would:
            # 1. Decode base64 audio payload
            # 2. Convert to proper audio format
            # 3. Send to STT service
            # 4. Return transcribed text
            
            return "I am interested in your programs"  # Placeholder
            
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return ""
    
    def generate_ai_response(user_input, context, conversation_history):
        """Generate AI response based on user input and context"""
        try:
            # Build dynamic system prompt based on context
            system_prompt = build_dynamic_system_prompt(context)
            
            # Prepare conversation for AI
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history
            for msg in conversation_history[-5:]:  # Last 5 messages for context
                messages.append(msg)
            
            # Add current user input if provided
            if user_input.strip():
                messages.append({"role": "user", "content": user_input})
            
            logger.info("🤖 Generating AI response...")
            
            # For now, return dynamic response based on context
            # In real implementation, this would call OpenAI API
            partner_name = context.get('partner_name', 'valued partner')
            
            if not user_input.strip():
                # Initial greeting
                return f"Hello! I'm calling from Global Learning Academy. Is this a good time to talk about our educational programs, {partner_name}?"
            else:
                # Dynamic response based on input
                return f"Thank you for your interest, {partner_name}. I'd be happy to provide more information about our programs. What specific area would you like to know more about?"
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return "I apologize, but I'm having some technical difficulties. Let me transfer you to a human representative."
    
    def build_dynamic_system_prompt(context):
        """Build dynamic system prompt based on call context"""
        partner_name = context.get('partner_name', 'valued partner')
        partner_email = context.get('partner_email', '')
        
        base_prompt = f"""You are an AI assistant calling on behalf of Global Learning Academy. 

Call Context:
- Partner: {partner_name}
- Email: {partner_email}
- Call Purpose: Educational program outreach

Instructions:
- Be professional, friendly, and helpful
- Focus on understanding their educational needs
- Provide information about relevant programs
- Ask engaging questions to understand their interests
- Keep responses concise and conversational
- If they're not interested, politely end the call
- If they want more information, offer to send details via email

Remember: This is a live phone conversation, so keep responses natural and brief."""
        
        return base_prompt
    
    def send_ai_audio_response(sock, text_response, conversation_state):
        """Convert AI text response to audio and send via WebSocket"""
        try:
            logger.info(f"🤖 AI responding: {text_response}")
            
            # Add to conversation history
            conversation_state['conversation_history'].append({
                'role': 'assistant',
                'content': text_response,
                'timestamp': datetime.now().isoformat()
            })
            
            # Convert text to speech
            audio_data = text_to_speech(text_response)
            
            if audio_data:
                # Send audio via WebSocket
                media_message = {
                    "event": "media",
                    "streamSid": conversation_state['context'].get('stream_sid'),
                    "media": {
                        "payload": audio_data
                    }
                }
                
                sock.send(json.dumps(media_message))
                logger.info("📤 AI audio response sent")
            
        except Exception as e:
            logger.error(f"Error sending AI audio response: {e}")
    
    def text_to_speech(text):
        """Convert text to speech audio data"""
        try:
            # Placeholder implementation
            # In real implementation, you would:
            # 1. Use a TTS service (OpenAI TTS, Google TTS, etc.)
            # 2. Convert text to audio
            # 3. Encode as base64
            # 4. Return encoded audio data
            
            logger.info("🗣️ Converting text to speech...")
            
            # For now, return None to use Twilio's built-in TTS via fallback
            return None
            
        except Exception as e:
            logger.error(f"Error in text-to-speech: {e}")
            return None
    
    @app.route('/webhook/status', methods=['POST'])
    def call_status_webhook():
        """Handle call status updates from Twilio"""
        try:
            call_sid = request.values.get('CallSid')
            call_status = request.values.get('CallStatus')
            duration = request.values.get('CallDuration', '0')
            
            logger.info(f"📊 Call status update - SID: {call_sid}, Status: {call_status}, Duration: {duration}s")
            
            # Log different call statuses
            if call_status == 'completed':
                logger.info(f"✅ Call {call_sid} completed successfully after {duration} seconds")
            elif call_status == 'busy':
                logger.warning(f"📞 Call {call_sid} was busy")
            elif call_status == 'no-answer':
                logger.warning(f"📞 Call {call_sid} - no answer")
            elif call_status == 'failed':
                logger.error(f"❌ Call {call_sid} failed")
            
            return '', 200
            
        except Exception as e:
            logger.error(f"❌ Status webhook error: {e}")
            return '', 500

    # ===============================
    # SES TEMPLATED EMAIL API ROUTES
    # ===============================
    
    @app.route('/api/templated-email/create-templates', methods=['POST'])
    def create_email_templates():
        """Create all SES email templates"""
        try:
            logger.info("Creating SES email templates...")
            result = templated_email_service.create_ses_templates()
            
            success_count = sum(1 for r in result.values() if r.get('success'))
            total_count = len(result)
            
            if success_count == total_count:
                status_code = 200
                message = f"All {total_count} SES email templates created successfully"
            elif success_count > 0:
                status_code = 207  # Multi-status
                message = f"{success_count} of {total_count} templates created successfully"
            else:
                status_code = 500
                message = "Failed to create any templates"
            
            return jsonify({
                'success': success_count == total_count,
                'message': message,
                'templates_created': success_count,
                'total_templates': total_count,
                'results': result
            }), status_code
            
        except Exception as e:
            logger.error(f"Error creating templates: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/templated-email/send-signup', methods=['POST'])
    def send_signup_email():
        """Send account signup email"""
        try:
            data = request.get_json()
            
            if not data.get('to_email'):
                return jsonify({
                    'success': False,
                    'error': 'to_email is required'
                }), 400
            
            result = templated_email_service.send_account_signup_email(data)
            status_code = 200 if result.get('success') else 500
            
            return jsonify(result), status_code
            
        except Exception as e:
            logger.error(f"Error sending signup email: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/templated-email/send-forgot-password', methods=['POST'])
    def send_forgot_password_email():
        """Send forgot password email"""
        try:
            data = request.get_json()
            
            if not data.get('to_email'):
                return jsonify({
                    'success': False,
                    'error': 'to_email is required'
                }), 400
            
            result = templated_email_service.send_forgot_password_email(data)
            status_code = 200 if result.get('success') else 500
            
            return jsonify(result), status_code
            
        except Exception as e:
            logger.error(f"Error sending forgot password email: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/templated-email/send-otp', methods=['POST'])
    def send_otp_email():
        """Send OTP email"""
        try:
            data = request.get_json()
            
            if not data.get('to_email') or not data.get('otp'):
                return jsonify({
                    'success': False,
                    'error': 'to_email and otp are required'
                }), 400
            
            result = templated_email_service.send_otp_email(data)
            status_code = 200 if result.get('success') else 500
            
            return jsonify(result), status_code
            
        except Exception as e:
            logger.error(f"Error sending OTP email: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/templated-email/send-order-confirmation', methods=['POST'])
    def send_order_confirmation_email():
        """Send order confirmation email"""
        try:
            data = request.get_json()
            
            if not data.get('to_email') or not data.get('orderId'):
                return jsonify({
                    'success': False,
                    'error': 'to_email and orderId are required'
                }), 400
            
            result = templated_email_service.send_order_confirmation_email(data)
            status_code = 200 if result.get('success') else 500
            
            return jsonify(result), status_code
            
        except Exception as e:
            logger.error(f"Error sending order confirmation email: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/templated-email/send-welcome-pack', methods=['POST'])
    def send_welcome_pack_email():
        """Send welcome pack email with PDF attachment"""
        try:
            data = request.get_json()
            
            if not data.get('to_email'):
                return jsonify({
                    'success': False,
                    'error': 'to_email is required'
                }), 400
            
            result = templated_email_service.send_welcome_pack_email(data)
            status_code = 200 if result.get('success') else 500
            
            return jsonify(result), status_code
            
        except Exception as e:
            logger.error(f"Error sending welcome pack email: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/templated-email/status', methods=['GET'])
    def templated_email_status():
        """Get templated email service status"""
        try:
            return jsonify({
                'success': True,
                'service': 'SES Templated Email Service',
                'status': 'healthy',
                'available_templates': [
                    'AccountSignupTemplate',
                    'ForgotPasswordTemplate',
                    'OTPTemplate',
                    'OrderConfirmationTemplate'
                ],
                'special_endpoints': [
                    'WelcomePackWithPDF (uses SendRawEmail)'
                ],
                'version': '1.0.0',
                'endpoints': {
                    'POST /api/templated-email/create-templates': 'Create all SES email templates',
                    'POST /api/templated-email/send-signup': 'Send account signup email',
                    'POST /api/templated-email/send-forgot-password': 'Send password reset email',
                    'POST /api/templated-email/send-otp': 'Send OTP verification email',
                    'POST /api/templated-email/send-order-confirmation': 'Send order confirmation email',
                    'POST /api/templated-email/send-welcome-pack': 'Send welcome pack email with PDF',
                    'GET /api/templated-email/status': 'Get templated email service status'
                }
            })
        except Exception as e:
            logger.error(f"Error getting templated email status: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    logger.info("Flask application configured")
    return app

if __name__ == '__main__':
    app = create_flask_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
