import os
import logging
from typing import Dict, Any, Optional
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
from datetime import datetime
import json
import random
from app.models.data_models import TwilioCallResponse, CallStatus

# Configure logging
logger = logging.getLogger(__name__)

class TwilioConfig:
    """Twilio configuration class"""
    
    def __init__(self):
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN') 
        self.phone_number = os.getenv('TWILIO_PHONE_NUMBER')
        self.webhook_url = os.getenv('TWILIO_WEBHOOK_URL', 'https://your-lambda-url.amazonaws.com/call-webhook')
        self.voice_url = os.getenv('TWILIO_VOICE_URL', 'https://your-lambda-url.amazonaws.com/voice-handler')
        
        # AI/TTS Configuration
        self.ai_voice = os.getenv('TWILIO_AI_VOICE', 'alice')  # alice, man, woman
        self.language = os.getenv('TWILIO_LANGUAGE', 'en-IN')  # English India
        self.speech_rate = os.getenv('TWILIO_SPEECH_RATE', '0.9')  # Slightly slower for clarity
        
        # Check if we have real credentials (not placeholders)
        self.is_configured = (
            self.account_sid and 
            self.auth_token and
            not self.account_sid.startswith('your_') and
            not self.auth_token.startswith('your_') and
            self.account_sid.startswith('AC')  # Valid Twilio Account SID format
        )

class TwilioService:
    """Twilio integration service for voice calls"""
    
    def __init__(self, mock_mode=False, ngrok_url=None):
        self.config = TwilioConfig()
        self.mock_mode = mock_mode or not self.config.is_configured
        self.ngrok_url = ngrok_url
        
        # Update webhook URLs if ngrok URL is provided
        if ngrok_url:
            self.config.webhook_url = f"{ngrok_url}/webhook/voice"
            self.config.voice_url = f"{ngrok_url}/webhook/voice"
            logger.info(f"🌐 Updated webhook URLs to use ngrok: {self.config.webhook_url}")
        
        if self.mock_mode:
            logger.info("🧪 TwilioService running in MOCK MODE")
            self.client = None
        else:
            try:
                self.client = Client(self.config.account_sid, self.config.auth_token)
                logger.info("✅ TwilioService initialized with real credentials")
                logger.info("Twilio client initialized successfully")
            except Exception as e:
                logger.warning(f"⚠️ TwilioService falling back to mock mode: {e}")
                self.mock_mode = True
                self.client = None
    
    def initiate_ai_call(self, to_number: str, ai_prompt: str, call_metadata: Dict[str, Any] = None) -> TwilioCallResponse:
        """
        Initiate an AI-powered outbound voice call
        
        Args:
            to_number: The phone number to call
            ai_prompt: The AI system prompt for the call
            call_metadata: Additional metadata about the call
        
        Returns:
            TwilioCallResponse object with call details
        """
        
        if not self.client:
            # Mock response when Twilio is not configured
            return self._create_mock_call_response(to_number, ai_prompt, call_metadata)
        
        try:
            # Create TwiML for AI-powered call
            twiml_url = self._create_ai_twiml_url(ai_prompt, call_metadata)
            
            # Initiate the call with AI configurations
            call = self.client.calls.create(
                to=to_number,
                from_=self.config.phone_number,
                url=twiml_url,
                method='POST',
                timeout=30,  # Ring for 30 seconds
                record=True,  # Record the call for quality and training
                recording_channels='dual',  # Record both sides of the conversation
                recording_status_callback=self.config.webhook_url,  # Webhook for recording status
                recording_status_callback_event=['completed'],  # Get notified when recording is done
                status_callback=self.config.webhook_url,  # Webhook for call status updates
                status_callback_event=['initiated', 'ringing', 'answered', 'completed', 'busy', 'no-answer', 'failed']
            )
            
            # Create response object
            response = TwilioCallResponse(
                call_sid=call.sid,
                status=call.status,
                direction=call.direction,
                from_number=call.from_formatted if hasattr(call, 'from_formatted') else self.config.phone_number,
                to_number=call.to_formatted if hasattr(call, 'to_formatted') else to_number
            )
            
            logger.info(f"AI call initiated successfully: {call.sid} to {to_number}")
            return response
            
        except TwilioException as e:
            logger.error(f"Failed to initiate AI call to {to_number}: {e}")
            return TwilioCallResponse(
                status="FAILED",
                from_number=self.config.phone_number,
                to_number=to_number,
                error_code=str(e.code) if hasattr(e, 'code') else None,
                error_message=str(e)
            )
    
    def make_call(self, to_number: str, system_prompt: str, call_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Compatibility method for make_call - calls initiate_ai_call
        
        Args:
            to_number: The phone number to call
            system_prompt: The AI system prompt for the call
            call_metadata: Additional metadata about the call
        
        Returns:
            Dictionary with call details
        """
        
        if self.mock_mode:
            return {
                'call_sid': f'mock_call_{random.randint(1000, 9999)}',
                'status': 'initiated',
                'to_number': to_number,
                'from_number': self.config.phone_number,
                'mock_mode': True,
                'message': f'Mock call initiated to {to_number}',
                'prompt_length': len(system_prompt)
            }
        
        # Call the real method
        response = self.initiate_ai_call(to_number, system_prompt, call_metadata)
        
        # Convert to dictionary format
        return {
            'call_sid': response.call_sid,
            'status': response.status,
            'to_number': response.to_number,
            'from_number': response.from_number,
            'error_message': response.error_message
        }
    
    def _create_ai_twiml_url(self, ai_prompt: str, call_metadata: Dict[str, Any] = None) -> str:
        """
        Create TwiML URL for AI-powered voice calls
        
        Args:
            ai_prompt: The AI system prompt for the call
            call_metadata: Additional metadata about the call
        
        Returns:
            TwiML URL for the call
        """
        
        # For now, just use the voice URL directly - the prompt will be handled in the webhook
        # Store the prompt and metadata for later use in the webhook
        if hasattr(self, '_current_prompt_data'):
            self._current_prompt_data = {
                'ai_prompt': ai_prompt,
                'voice_config': {
                    'voice': self.config.ai_voice,
                    'language': self.config.language,
                    'rate': self.config.speech_rate
                },
                'metadata': call_metadata or {}
            }
        
        # Return just the webhook URL without complex query parameters
        return self.config.voice_url
    
    def get_call_status(self, call_sid: str) -> Optional[TwilioCallResponse]:
        """Get the current status of a call"""
        
        if not self.client:
            return self._create_mock_status_response(call_sid)
        
        try:
            call = self.client.calls(call_sid).fetch()
            
            return TwilioCallResponse(
                call_sid=call.sid,
                status=call.status,
                direction=call.direction,
                from_number=call.from_,
                to_number=call.to,
                duration=call.duration,
                price=float(call.price) if call.price else None
            )
            
        except TwilioException as e:
            logger.error(f"Failed to get call status for {call_sid}: {e}")
            return None
    
    def end_call(self, call_sid: str) -> bool:
        """End an active call"""
        
        if not self.client:
            logger.info(f"Mock: Ending call {call_sid}")
            return True
        
        try:
            call = self.client.calls(call_sid).update(status='completed')
            logger.info(f"Call {call_sid} ended successfully")
            return True
            
        except TwilioException as e:
            logger.error(f"Failed to end call {call_sid}: {e}")
            return False
    
    def _create_twiml_url(self, ai_prompt: str, call_metadata: Dict[str, Any] = None) -> str:
        """
        Create TwiML URL for the call
        In a real implementation, this would point to your webhook endpoint
        that serves TwiML based on the AI prompt
        """
        
        # For now, return a placeholder URL
        # In production, this would be your Lambda function URL that handles TwiML generation
        base_url = os.getenv('TWIML_WEBHOOK_URL', 'https://your-lambda-url.amazonaws.com/twiml')
        
        # You could encode the prompt and metadata as URL parameters
        # or store them in a database and pass an ID
        return f"{base_url}?prompt_id={hash(ai_prompt)}&metadata={json.dumps(call_metadata or {})}"
    
    def _create_mock_call_response(self, to_number: str, ai_prompt: str) -> TwilioCallResponse:
        """Create a mock call response for testing"""
        
        mock_sid = f"CA{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        logger.info(f"MOCK CALL: Initiating call to {to_number}")
        logger.info(f"MOCK CALL: Using AI Prompt (first 100 chars): {ai_prompt[:100]}...")
        
        return TwilioCallResponse(
            call_sid=mock_sid,
            status="in-progress",
            direction="outbound-api",
            from_number=self.config.phone_number,
            to_number=to_number
        )

    # Backwards-compatible shim expected by older scripts/tests
    def initiate_call(self, to_number: str, ai_prompt: str, call_metadata: Dict[str, Any] = None) -> TwilioCallResponse:
        """Compatibility wrapper for older code that expects initiate_call"""
        # Mirror behaviour of initiate_ai_call
        return self.initiate_ai_call(to_number, ai_prompt, call_metadata)
    
    def _create_mock_status_response(self, call_sid: str) -> TwilioCallResponse:
        """Create a mock status response for testing"""
        
        logger.info(f"MOCK CALL: Getting status for call {call_sid}")
        
        return TwilioCallResponse(
            call_sid=call_sid,
            status="completed",
            direction="outbound-api", 
            from_number=self.config.phone_number,
            to_number="+91-XX-XXXX-XXXX",
            duration=180  # 3 minutes mock duration
        )

class VoicemailService:
    """Service for handling voicemail scenarios"""
    
    def __init__(self):
        self.twilio_service = TwilioService()
    
    def leave_voicemail(self, to_number: str, voicemail_message: str, call_metadata: Dict[str, Any] = None) -> TwilioCallResponse:
        """
        Leave a voicemail message
        This would typically use Twilio's text-to-speech capabilities
        """

        # Create a special TwiML for voicemail
        voicemail_prompt = f"""
This is a voicemail message call. When connected, please deliver this message:

{voicemail_message}

After delivering the message, end the call politely.
"""

        logger.info(f"Leaving voicemail for {to_number}")
        # Use the compatibility shim on the twilio service to initiate a voicemail-style call
        return self.twilio_service.initiate_call(to_number, voicemail_prompt, call_metadata)

# Service instances
twilio_service = TwilioService()
voicemail_service = VoicemailService()
