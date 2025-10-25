"""
Audio processing utilities for AI Telecaller System
Handles audio format conversion, validation, and preprocessing
"""

import base64
import wave
import audioop
import os

class AudioProcessor:
    """Handles audio processing and format conversion"""
    
    def __init__(self):
        self.supported_formats = ['wav', 'g711']
    
    def validate_audio_payload(self, audio_payload: str) -> bool:
        """Validate audio payload format"""
        try:
            # Check if it's valid base64
            base64.b64decode(audio_payload)
            return True
        except Exception as e:
            print(f"❌ Invalid audio payload: {e}")
            return False
    
    def convert_audio_format(self, audio_data: bytes, from_format: str, to_format: str) -> bytes:
        """Convert audio between different formats"""
        try:
            if from_format == to_format:
                return audio_data
            
            # TODO: Implement format conversion if needed
            # For now, return as-is since Twilio provides g711 μ-law which OpenAI accepts
            return audio_data
            
        except Exception as e:
            print(f"❌ Error converting audio format: {e}")
            return audio_data
    
    def save_audio_buffer(self, call_sid: str, audio_buffer: list, recordings_dir: str) -> str:
        """Save audio buffer to WAV file"""
        try:
            if not audio_buffer:
                print(f"⚠️ No audio buffer to save for call {call_sid}")
                return None
            
            wav_filename = os.path.join(recordings_dir, f"{call_sid}_recording.wav")
            
            with wave.open(wav_filename, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(8000)  # 8kHz (Twilio standard)
                
                # Combine all audio chunks
                combined_audio = b''.join(audio_buffer)
                wav_file.writeframes(combined_audio)
            
            print(f"📁 Audio saved: {wav_filename}")
            return wav_filename
            
        except Exception as e:
            print(f"❌ Error saving audio buffer: {e}")
            return None
    
    def process_twilio_audio(self, audio_payload: str) -> bytes:
        """Process audio payload from Twilio Media Stream"""
        try:
            # Decode base64 audio payload
            audio_data = base64.b64decode(audio_payload)
            
            # Twilio sends g711 μ-law format, which is already compatible with OpenAI
            # No conversion needed in most cases
            return audio_data
            
        except Exception as e:
            print(f"❌ Error processing Twilio audio: {e}")
            return b''

# Global audio processor instance
audio_processor = AudioProcessor()
