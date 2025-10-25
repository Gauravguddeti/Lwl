"""
Call storage and recording management for AI Telecaller System
Handles call recordings, transcriptions, and storage operations
"""

from app.utils.call_storage import CallStorageManager

class CallStorage:
    """Call storage wrapper for telecaller system"""
    
    def __init__(self):
        self.call_storage = CallStorageManager()
    
    def save_call_recording(self, call_sid, audio_buffer):
        """Save call recording to storage"""
        return self.call_storage.save_call_recording(call_sid, audio_buffer)
    
    def transcribe_recording(self, wav_filename, call_sid, timestamp):
        """Transcribe call recording"""
        return self.call_storage.transcribe_recording(wav_filename, call_sid, timestamp)
    
    def store_conversation_turn(self, call_sid: str, speaker: str, text: str):
        """Store a conversation turn"""
        return self.call_storage.store_conversation_turn(call_sid, speaker, text)

# Global call storage instance
call_storage = CallStorage()
