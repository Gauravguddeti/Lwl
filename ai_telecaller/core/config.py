"""
Configuration module for AI Telecaller System
Handles environment variables, imports and system-wide configuration
"""

import os
import sys

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("[OK] Environment variables loaded from .env file")
except ImportError:
    print("[WARNING] python-dotenv not installed - using system environment variables only")

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Try to import Twilio (optional for demo)
try:
    from twilio.twiml.voice_response import VoiceResponse, Connect, Stream
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    print("[WARNING] Twilio not available - running in demo mode")
    TWILIO_AVAILABLE = False
    VoiceResponse = None
    Client = None
    Connect = None
    Stream = None

class Config:
    """System configuration class"""
    
    def __init__(self):
        # OpenAI configuration
        self.openai_api_key = os.getenv('OPENAI_API_KEY', 'your_openai_key_here')
        
        # Twilio configuration  
        self.twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID', 'your_account_sid')
        self.twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN', 'your_auth_token')
        self.twilio_phone_number = os.getenv('TWILIO_PHONE_NUMBER', '+1234567890')
        
        # Flask configuration
        self.flask_port = 3000
        
        # Directory configuration
        self.recordings_dir = "./recordings"
        os.makedirs(self.recordings_dir, exist_ok=True)
        
        # Create recordings directory
        os.makedirs(self.recordings_dir, exist_ok=True)

# Global configuration instance
config = Config()
