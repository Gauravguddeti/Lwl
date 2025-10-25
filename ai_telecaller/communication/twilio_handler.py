"""
Twilio integration and call management for AI Telecaller System
Handles Twilio API calls, call management, and recording downloads
"""

import time
from datetime import datetime
from typing import Dict, Any, List
from ..core.config import config, TWILIO_AVAILABLE, Client

class TwilioHandler:
    """Handles all Twilio-related operations"""
    
    def __init__(self):
        self.client = None
        self.account_sid = config.twilio_account_sid
        self.auth_token = config.twilio_auth_token
        self.phone_number = config.twilio_phone_number
        
        # Add aliases for recording download compatibility
        self.twilio_account_sid = self.account_sid
        self.twilio_auth_token = self.auth_token
        self.twilio_phone_number = self.phone_number
        
        if TWILIO_AVAILABLE and self.account_sid != 'your_account_sid':
            self.client = Client(self.account_sid, self.auth_token)
    
    def make_call(self, to_number: str, partner_name: str = "Unknown", ngrok_url: str = None, active_calls: Dict = None) -> Dict[str, Any]:
        """Make a call to a specific number"""
        if not TWILIO_AVAILABLE:
            print("⚠️ Demo mode: Simulating call to", partner_name, "at", to_number)
            return {
                'status': 'demo',
                'call_sid': f'demo_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
                'to_number': to_number,
                'partner_name': partner_name,
                'message': 'Demo call simulation - Twilio not configured'
            }
        
        if not self.client:
            print("❌ Twilio client not configured")
            return {'status': 'error', 'message': 'Twilio not configured'}
        
        if not ngrok_url:
            print("❌ Ngrok URL not available")
            return {'status': 'error', 'message': 'Ngrok not active'}
        
        try:
            print(f"📞 Calling {partner_name} at {to_number}...")
            print(f"🌐 Using ngrok URL: {ngrok_url}")
            print(f"📱 From number: {self.phone_number}")
            print(f"🔗 Voice webhook: {ngrok_url}/webhook/voice")
            print(f"📊 Status webhook: {ngrok_url}/webhook/call-status")
            
            call = self.client.calls.create(
                to=to_number,
                from_=self.phone_number,
                url=f"{ngrok_url}/webhook/voice",
                status_callback=f"{ngrok_url}/webhook/call-status",
                status_callback_event=['initiated', 'ringing', 'answered', 'completed'],
                record=True  # Enable call recording
            )
            
            print(f"✅ Call initiated: {call.sid}")
            
            # Track the active call
            if active_calls is not None:
                active_calls[call.sid] = {
                    'partner_name': partner_name,
                    'to_number': to_number,
                    'status': 'initiated',
                    'start_time': datetime.now()
                }
            
            return {
                'status': 'success',
                'call_sid': call.sid,
                'to_number': to_number,
                'partner_name': partner_name
            }
            
        except Exception as e:
            print(f"❌ Error making call: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def call_all_partners(self, partners: List[Dict[str, Any]], ngrok_url: str = None, active_calls: Dict = None) -> List[Dict[str, Any]]:
        """Make calls to all partners simultaneously"""
        print(f"📞 Initiating calls to all {len(partners)} partners...")
        
        results = []
        for partner in partners:
            contact = partner.get('contact', '')
            name = partner.get('partner_name', 'Unknown')
            
            if contact and contact.isdigit():
                # Add country code if not present
                if not contact.startswith('+'):
                    contact = '+91' + contact  # Assuming India, adjust as needed
                
                result = self.make_call(contact, name, ngrok_url, active_calls)
                results.append(result)
                
                # Small delay between calls
                time.sleep(1)
            else:
                print(f"⚠️ Invalid contact number for {name}: {contact}")
                results.append({
                    'status': 'error',
                    'partner_name': name,
                    'message': f'Invalid contact number: {contact}'
                })
        
        return results
    
    def download_call_recording(self, call_sid: str, recording_url: str, partner_name: str = None, call_storage=None):
        """Download call recording from Twilio with enhanced naming"""
        try:
            print(f"📥 Downloading recording for call {call_sid}...")
            
            # Use the call storage manager's enhanced download method
            if call_storage:
                call_storage.download_recording(recording_url, call_sid, partner_name)
            
        except Exception as e:
            print(f"❌ Failed to download recording: {e}")

# Global Twilio handler instance
twilio_handler = TwilioHandler()
