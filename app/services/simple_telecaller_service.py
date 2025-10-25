#!/usr/bin/env python3
"""
Simplified Enhanced AI Telecaller for Testing
Core features working, advanced features optional
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import re

# Core imports
from flask import Flask, request, jsonify
from twilio.twiml.voice_response import VoiceResponse
from openai import OpenAI
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ConversationState:
    """Simple conversation state tracking"""
    call_id: str
    user_responses: List[str]
    ai_responses: List[str]
    stage: str
    start_time: str

class IndianAccentProcessor:
    """Process Indian English patterns"""
    
    def __init__(self):
        self.accent_patterns = {
            r'\bwhat is your good name\b': 'what is your name',
            r'\btell me one thing\b': 'let me ask you',
            r'\bdo one thing\b': 'please do this',
            r'\bout of station\b': 'out of town',
            r'\bonly\b(?=\s+(?:I|we|they))': '',
            r'\bna\b': 'no',
            r'\bhaan\b': 'yes',
            r'\btheek hai\b': 'okay',
        }
    
    def process_input(self, user_input: str) -> Dict[str, Any]:
        """Process and correct Indian accent patterns"""
        original = user_input
        corrected = user_input.lower().strip()
        
        for pattern, replacement in self.accent_patterns.items():
            corrected = re.sub(pattern, replacement, corrected, flags=re.IGNORECASE)
        
        return {
            'original': original,
            'corrected': corrected,
            'indian_accent_detected': original != corrected
        }

class SimpleTelecallerService:
    """Simplified AI Telecaller with core features"""
    
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.accent_processor = IndianAccentProcessor()
        self.active_conversations = {}
        
    def create_flask_app(self):
        """Create Flask app"""
        app = Flask(__name__)
        
        @app.route('/voice/start', methods=['POST'])
        def voice_start():
            """Start voice call with Indian voice"""
            call_id = request.form.get('CallSid', 'test_call')
            
            # Initialize conversation
            state = ConversationState(
                call_id=call_id,
                user_responses=[],
                ai_responses=[],
                stage='greeting',
                start_time=datetime.now().isoformat()
            )
            
            self.active_conversations[call_id] = state
            
            # Create Indian voice response
            response = VoiceResponse()
            greeting = "Namaste! This is Sarah from Learn with Leaders. I hope you're having a wonderful day. Am I speaking with the principal or someone who handles educational programs for your school?"
            
            response.say(
                greeting,
                voice='Polly.Raveena',  # Indian English voice
                language='en-IN'
            )
            
            response.gather(
                input='speech',
                action='/voice/gather',
                method='POST',
                speech_timeout=4,
                timeout=10,
                language='en-IN',
                enhanced=True
            )
            
            logger.info(f"Call started: {call_id} with Indian voice")
            return str(response)
            
        @app.route('/voice/gather', methods=['POST'])
        def voice_gather():
            """Process user speech with accent handling"""
            call_id = request.form.get('CallSid', 'test_call')
            user_input = request.form.get('SpeechResult', '').strip()
            
            if call_id not in self.active_conversations:
                return self._create_error_response()
                
            state = self.active_conversations[call_id]
            
            # Process Indian accent
            processed = self.accent_processor.process_input(user_input)
            corrected_input = processed['corrected']
            
            # Update state
            state.user_responses.append(user_input)
            
            # Generate AI response
            ai_response = self._generate_response(state, corrected_input)
            state.ai_responses.append(ai_response)
            
            # Create response with Indian voice
            response = VoiceResponse()
            response.say(
                ai_response,
                voice='Polly.Raveena',
                language='en-IN'
            )
            
            # Continue conversation
            if len(state.user_responses) < 6:
                response.gather(
                    input='speech',
                    action='/voice/gather',
                    method='POST',
                    speech_timeout=4,
                    timeout=10,
                    language='en-IN',
                    enhanced=True
                )
            else:
                response.say("Thank you for your time! Have a wonderful day!")
                response.hangup()
                
            logger.info(f"User: '{user_input}' -> AI: '{ai_response}'")
            return str(response)
            
        @app.route('/health', methods=['GET'])
        def health():
            return jsonify({
                'status': 'healthy',
                'service': 'Enhanced AI Telecaller (Simplified)',
                'features': [
                    'Indian Voice Support ✅',
                    'Accent Processing ✅', 
                    'OpenAI Integration ✅',
                    'Cost-Optimized ✅'
                ],
                'timestamp': datetime.now().isoformat()
            })
            
        @app.route('/test/accent', methods=['POST'])
        def test_accent():
            """Test accent processing"""
            data = request.get_json()
            test_input = data.get('test_input', '')
            
            result = self.accent_processor.process_input(test_input)
            
            return jsonify({
                'test_input': test_input,
                'corrected_output': result['corrected'],
                'accent_detected': result['indian_accent_detected'],
                'timestamp': datetime.now().isoformat()
            })
            
        return app
        
    def _generate_response(self, state: ConversationState, user_input: str) -> str:
        """Generate AI response using OpenAI"""
        try:
            context = f"""
            You are Sarah, a professional telecaller from Learn with Leaders calling about Cambridge Summer Programme 2025.
            
            User said: "{user_input}"
            Conversation stage: {state.stage}
            Previous responses: {len(state.user_responses)}
            
            Respond warmly in 40-60 words. Use Indian cultural context - emphasize education value, family consultation importance.
            
            Key points about Cambridge Programme:
            - 2-week intensive at Cambridge University
            - ₹2,50,000 (₹2,12,500 with 15% early discount)
            - Students live in actual Cambridge colleges
            - Faculty lectures, cultural activities, certificate
            - Life-changing experience for students
            """
            
            response = self.openai_client.chat.completions.create(
                model=os.getenv('AI_MODEL', 'gpt-4o-mini'),
                messages=[{"role": "user", "content": context}],
                max_tokens=80,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"AI response error: {e}")
            
            # Fallback responses
            fallbacks = [
                "That's wonderful! The Cambridge Summer Programme is truly a life-changing opportunity for students. Let me share more details with you.",
                "I completely understand your interest. This programme has transformed students from schools like yours. What specific aspects would you like to know about?",
                "Perfect! Many principals have found this programme invaluable for their top students. Shall I explain the curriculum and benefits?",
                "Thank you for considering this. The programme offers authentic Cambridge University experience. When would be good to discuss further?"
            ]
            
            return fallbacks[len(state.user_responses) % len(fallbacks)]
            
    def _create_error_response(self) -> str:
        """Create error response"""
        response = VoiceResponse()
        response.say("I'm sorry, there was a technical issue. Please call back later.")
        response.hangup()
        return str(response)

# Initialize service
telecaller_service = SimpleTelecallerService()
app = telecaller_service.create_flask_app()

if __name__ == '__main__':
    print("🇮🇳 Enhanced AI Telecaller (Simplified) Starting...")
    print("Features: Indian Voice ✅ | Accent Processing ✅ | OpenAI ✅")
    app.run(host='0.0.0.0', port=5000, debug=True)
