"""
Application Configuration Settings
Centralized configuration for AI Telecaller system
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class AppConfig:
    """Application configuration class"""
    
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.twilio_phone_number = os.getenv('TWILIO_PHONE_NUMBER')
        
        # Database configuration
        self.database_url = os.getenv('DATABASE_URL')
        
        # Ngrok configuration
        self.ngrok_auth_token = os.getenv('NGROK_AUTH_TOKEN')
        self.webhook_base_url = os.getenv('WEBHOOK_BASE_URL')
        
        # Recording storage
        self.recordings_dir = 'call_recordings'
        self.transcriptions_dir = 'call_transcriptions'
        
        # Flask configuration
        self.flask_host = '0.0.0.0'
        self.flask_port = 5000
        self.flask_debug = True
    
    def validate_required_config(self) -> bool:
        """Validate that required configuration is present"""
        required_vars = [
            ('OPENAI_API_KEY', self.openai_api_key),
            ('TWILIO_AUTH_TOKEN', self.twilio_auth_token)
        ]
        
        missing_vars = []
        for var_name, var_value in required_vars:
            if not var_value:
                missing_vars.append(var_name)
        
        if missing_vars:
            print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
            return False
        
        return True
    
    def get_webhook_urls(self, base_url: Optional[str] = None) -> dict:
        """Get webhook URLs for Twilio configuration"""
        base = base_url or self.webhook_base_url
        if not base:
            return {}
        
        return {
            'voice_webhook': f"{base}/webhook/voice",
            'call_status_webhook': f"{base}/webhook/call-status",
            'media_stream_websocket': f"{base.replace('http', 'ws')}/media-stream"
        }
