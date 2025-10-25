"""
Twilio Voice Webhook Handler
Handles incoming voice calls and initiates OpenAI Realtime API connection
"""

import logging
from flask import request
from twilio.twiml.voice_response import VoiceResponse, Connect, Stream

logger = logging.getLogger(__name__)

class VoiceWebhookHandler:
    """Handle Twilio voice webhook calls"""
    
    def __init__(self, ngrok_url=None):
        """Initialize voice webhook handler with optional ngrok URL"""
        self.ngrok_url = ngrok_url
        logger.info(f"VoiceWebhookHandler initialized with ngrok URL: {ngrok_url}")
    
    def handle_voice_webhook(self):
        """Handle incoming voice calls with OpenAI Realtime API"""
        try:
            logger.info("Voice webhook called")
            
            # Get call information from Twilio
            call_sid = request.form.get('CallSid')
            from_number = request.form.get('From')
            to_number = request.form.get('To')
            
            logger.info(f"Call details - SID: {call_sid}, From: {from_number}, To: {to_number}")
            
            # Create TwiML response for OpenAI Realtime API
            response = VoiceResponse()
            
            # Add greeting
            response.say(
                "Hello! I am your AI assistant from Global Learning Academy. Please hold while I connect you to our advanced system.",
                voice='alice'
            )
            
            # Connect to WebSocket stream for real-time conversation
            connect = Connect()
            
            # Determine the correct ngrok host for WebSocket
            if self.ngrok_url:
                # Parse ngrok URL to get the host
                ngrok_host = self.ngrok_url.replace('https://', '').replace('http://', '')
                stream_url = f'wss://{ngrok_host}/stream'
                logger.info(f"Using ngrok WebSocket URL: {stream_url}")
            else:
                # Fallback to request host
                stream_url = f'wss://{request.host}/stream'
                logger.warning(f"No ngrok URL provided, using fallback: {stream_url}")
            
            stream = Stream(url=stream_url)
            connect.append(stream)
            response.append(connect)
            
            logger.info(f"Voice webhook processed for call {call_sid}")
            return str(response)
            
        except Exception as e:
            logger.error(f"Voice webhook error: {e}")
            
            # Return error response
            response = VoiceResponse()
            response.say(
                "I am sorry, but I am experiencing technical difficulties. Please try again later or contact support.",
                voice='alice'
            )
            response.hangup()
            return str(response)
