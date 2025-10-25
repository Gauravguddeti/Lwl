"""
Twilio Call Status Webhook Handler
Handles call status updates and downloads recordings/transcriptions
"""

import logging
import requests
import base64
from datetime import datetime
from flask import request
from app.utils.call_storage import CallStorageManager

logger = logging.getLogger(__name__)

class CallStatusHandler:
    """Handle call status updates and recording downloads"""
    
    def __init__(self, twilio_service=None):
        self.twilio_service = twilio_service
        self.call_storage = CallStorageManager()
    
    def handle_call_status(self, request=None):
        """Handle call status updates and download recordings"""
        try:
            # Handle request parameter for modular usage
            if request:
                call_sid = request.form.get('CallSid')
                call_status = request.form.get('CallStatus')
                recording_url = request.form.get('RecordingUrl')
                from_number = request.form.get('From', 'Unknown')
                to_number = request.form.get('To', 'Unknown')
                duration = request.form.get('CallDuration', '0')
            else:
                # Fallback for direct usage
                from flask import request as flask_request
                call_sid = flask_request.form.get('CallSid')
                call_status = flask_request.form.get('CallStatus')
                recording_url = flask_request.form.get('RecordingUrl')
                from_number = flask_request.form.get('From', 'Unknown')
                to_number = flask_request.form.get('To', 'Unknown')
                duration = flask_request.form.get('CallDuration', '0')
            
            logger.info(f"📞 Call status update: {call_sid} - {call_status}")
            
            # Handle completed calls
            if call_status == 'completed' and recording_url:
                try:
                    # Download and store recording
                    partner_name = self._get_partner_name_from_number(from_number)
                    
                    # Download recording
                    recording_filename = self._download_recording(
                        call_sid, recording_url, partner_name, duration
                    )
                    
                    # Transcribe recording if available
                    if recording_filename:
                        self._transcribe_recording(recording_filename, call_sid)
                    
                    logger.info(f"✅ Recording and transcription completed for {call_sid}")
                    
                except Exception as e:
                    logger.error(f"❌ Error processing recording for {call_sid}: {e}")
            
            return {"status": "received", "call_sid": call_sid}
            
        except Exception as e:
            logger.error(f"❌ Call status handler error: {e}")
            return {"error": str(e)}, 500
    
    def _get_partner_name_from_number(self, phone_number):
        """Get partner name from database using phone number"""
        try:
            from app.services.dynamic_data_fetcher import DynamicDataFetcher
            data_fetcher = DynamicDataFetcher()
            
            partner_data = data_fetcher.get_partner_data(contact_number=phone_number)
            if partner_data:
                return partner_data.get('partner_name', 'Unknown_Partner')
            return 'Unknown_Partner'
            
        except Exception as e:
            logger.error(f"Error fetching partner name: {e}")
            return 'Unknown_Partner'
    
    def _download_recording(self, call_sid, recording_url, partner_name, duration):
        """Download recording from Twilio"""
        try:
            # Create filename with timestamp and partner info
            timestamp = datetime.now().strftime('%d%m%y')
            clean_partner = partner_name.replace(' ', '_').replace('-', '_')
            filename = f"{clean_partner}_call_{timestamp}_{call_sid}_recording.wav"
            filepath = f"./call_recordings/{filename}"
            
            # Download recording with Twilio auth
            if self.twilio_service and hasattr(self.twilio_service, 'config'):
                auth = (self.twilio_service.config.account_sid, self.twilio_service.config.auth_token)
                response = requests.get(recording_url, auth=auth, timeout=30)
                
                if response.status_code == 200:
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    
                    logger.info(f"✅ Recording downloaded: {filename}")
                    return filename
                else:
                    logger.error(f"Failed to download recording: {response.status_code}")
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error downloading recording: {e}")
            return None
    
    def _transcribe_recording(self, recording_filename, call_sid):
        """Transcribe recording using OpenAI Whisper"""
        try:
            import openai
            from openai import OpenAI
            import os
            
            openai_api_key = os.getenv('OPENAI_API_KEY')
            if not openai_api_key:
                logger.warning("No OpenAI API key - skipping transcription")
                return
            
            client = OpenAI(api_key=openai_api_key)
            recording_path = f"./call_recordings/{recording_filename}"
            
            if os.path.exists(recording_path):
                with open(recording_path, 'rb') as audio_file:
                    transcript = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="text"
                    )
                
                # Save transcription
                transcript_filename = recording_filename.replace('.wav', '_transcript.txt')
                transcript_path = f"./call_transcriptions/{transcript_filename}"
                
                with open(transcript_path, 'w', encoding='utf-8') as f:
                    f.write(f"Call SID: {call_sid}\n")
                    f.write(f"Recording: {recording_filename}\n")
                    f.write(f"Transcribed: {datetime.now().isoformat()}\n")
                    f.write("="*50 + "\n\n")
                    f.write(transcript)
                
                logger.info(f"✅ Transcription saved: {transcript_filename}")
                
        except Exception as e:
            logger.error(f"❌ Error transcribing recording: {e}")
