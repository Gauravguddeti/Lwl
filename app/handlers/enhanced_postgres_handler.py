"""
Enhanced Main Handler for AI Telecaller with PostgreSQL Integration
Combines LangGraph conversation flow with database tool calling
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from flask import Flask, request, jsonify, send_file
import base64

from app.services.langgraph_telecaller import LangGraphTelecaller
from app.services.ai_tools import get_database_tools
from app.database.postgres_data_access import db_access
from app.utils.call_storage import CallStorageManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedTelecallerHandler:
    """Enhanced handler with PostgreSQL integration and local storage"""
    
    def __init__(self):
        self.langgraph_telecaller = LangGraphTelecaller()
        self.database_tools = get_database_tools()
        self.call_storage = CallStorageManager()
        
        # Initialize directories for local storage
        self._init_storage_directories()
        
        logger.info("Enhanced Telecaller Handler initialized")
    
    def _init_storage_directories(self):
        """Initialize local storage directories"""
        recordings_path = os.getenv('CALL_RECORDINGS_PATH', './call_recordings')
        transcriptions_path = os.getenv('CALL_TRANSCRIPTIONS_PATH', './call_transcriptions')
        
        os.makedirs(recordings_path, exist_ok=True)
        os.makedirs(transcriptions_path, exist_ok=True)
        
        logger.info(f"Storage directories initialized: {recordings_path}, {transcriptions_path}")
    
    def handle_incoming_call(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming voice call with AI telecaller"""
        
        call_sid = call_data.get('CallSid', 'unknown')
        caller_number = call_data.get('From', 'unknown')
        
        logger.info(f"Handling incoming call: {call_sid} from {caller_number}")
        
        try:
            # Initialize conversation context
            conversation_context = {
                'call_sid': call_sid,
                'caller_number': caller_number,
                'call_start_time': datetime.now().isoformat(),
                'conversation_state': 'greeting',
                'database_context': {}
            }
            
            # Generate initial greeting with database context
            initial_response = self._generate_contextual_greeting(caller_number)
            
            # Store call metadata
            self.call_storage.store_call_metadata(call_sid, conversation_context)
            
            return {
                'status': 'success',
                'call_sid': call_sid,
                'response': initial_response,
                'context': conversation_context
            }
            
        except Exception as e:
            logger.error(f"Error handling incoming call: {str(e)}")
            return {
                'status': 'error',
                'message': str(e),
                'call_sid': call_sid
            }
    
    def _generate_contextual_greeting(self, caller_number: str) -> str:
        """Generate greeting with database context"""
        
        try:
            # Try to find caller in database (if number matches any partner contact)
            partners = db_access.get_partners()
            matching_partner = None
            
            for partner in partners:
                if partner.get('contact') and caller_number in partner.get('contact', ''):
                    matching_partner = partner
                    break
            
            if matching_partner:
                return f"Hello! Thank you for calling. I see you're calling from {matching_partner.get('partner_name', 'your institution')}. How can I help you today with our educational programs?"
            else:
                return "Hello! Thank you for calling our educational services. I'm here to help you learn about our programs and find the best options for your needs. How can I assist you today?"
                
        except Exception as e:
            logger.error(f"Error generating contextual greeting: {str(e)}")
            return "Hello! Thank you for calling our educational services. How can I help you today?"
    
    def process_voice_input(self, voice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process voice input from caller"""
        
        call_sid = voice_data.get('CallSid', 'unknown')
        speech_result = voice_data.get('SpeechResult', '')
        session_id = voice_data.get('session_id', call_sid)
        
        logger.info(f"Processing voice input for call {call_sid}: {speech_result[:50]}...")
        
        try:
            # Store transcription locally
            self.call_storage.store_transcription(
                call_sid=call_sid,
                speaker='caller',
                text=speech_result,
                timestamp=datetime.now().isoformat()
            )
            
            # Process with LangGraph telecaller
            ai_response = self.langgraph_telecaller.process_input(
                user_input=speech_result,
                session_id=session_id
            )
            
            # Store AI response transcription
            self.call_storage.store_transcription(
                call_sid=call_sid,
                speaker='ai',
                text=ai_response.get('response', ''),
                timestamp=datetime.now().isoformat()
            )
            
            # Update call context with database information
            if 'context' in ai_response:
                self._update_call_context(call_sid, ai_response['context'])
            
            return {
                'status': 'success',
                'call_sid': call_sid,
                'ai_response': ai_response.get('response', ''),
                'tools_used': ai_response.get('tools_used', []),
                'context': ai_response.get('context', {}),
                'session_id': session_id
            }
            
        except Exception as e:
            logger.error(f"Error processing voice input: {str(e)}")
            return {
                'status': 'error',
                'message': str(e),
                'call_sid': call_sid
            }
    
    def _update_call_context(self, call_sid: str, new_context: Dict[str, Any]):
        """Update call context with new information"""
        
        try:
            # Get existing context
            existing_context = self.call_storage.get_call_metadata(call_sid)
            
            if existing_context:
                # Merge new context
                existing_context['database_context'].update(new_context)
                existing_context['last_updated'] = datetime.now().isoformat()
                
                # Store updated context
                self.call_storage.store_call_metadata(call_sid, existing_context)
                
        except Exception as e:
            logger.error(f"Error updating call context: {str(e)}")
    
    def handle_call_recording(self, recording_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle and store call recording locally"""
        
        call_sid = recording_data.get('CallSid', 'unknown')
        recording_url = recording_data.get('RecordingUrl', '')
        
        logger.info(f"Handling call recording for {call_sid}")
        
        try:
            if recording_url:
                # Download and store recording locally
                recording_path = self.call_storage.store_recording(call_sid, recording_url)
                
                return {
                    'status': 'success',
                    'call_sid': call_sid,
                    'recording_path': recording_path
                }
            else:
                return {
                    'status': 'error',
                    'message': 'No recording URL provided',
                    'call_sid': call_sid
                }
                
        except Exception as e:
            logger.error(f"Error handling call recording: {str(e)}")
            return {
                'status': 'error',
                'message': str(e),
                'call_sid': call_sid
            }
    
    def process_voice_input(self, voice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process voice input and return structured response"""
        try:
            call_sid = voice_data.get('CallSid', 'unknown')
            speech_result = voice_data.get('SpeechResult', '')
            confidence = float(voice_data.get('Confidence', 0.0))
            
            # Create speech result data
            speech_data = {
                'text': speech_result,
                'confidence': confidence,
                'call_sid': call_sid
            }
            
            # Process with the speech result handler
            result = self.handle_speech_result(call_sid, speech_data)
            
            return {
                'status': 'success',
                'ai_response': result.get('message', 'I understand. Can you tell me more?'),
                'end_call': result.get('end_call', False),
                'call_sid': call_sid
            }
            
        except Exception as e:
            logger.error(f"Error processing voice input: {str(e)}")
            return {
                'status': 'error',
                'ai_response': 'I am having trouble understanding. Could you please repeat that?',
                'end_call': False,
                'error': str(e)
            }

    def handle_speech_result(self, call_sid: str, speech_result: dict) -> dict:
        """Enhanced speech result handling with sentiment analysis"""
        try:
            logger.info(f"Processing speech result for call {call_sid}: {speech_result}")
            
            # Extract speech text and confidence
            speech_text = speech_result.get('text', '').strip()
            confidence = speech_result.get('confidence', 0.0)
            
            if not speech_text:
                return self._create_response("I didn't catch that. Could you please repeat?")
            
            # Store enhanced transcription with sentiment analysis
            self.call_storage.store_transcription(
                call_sid=call_sid,
                speaker='caller',
                text=speech_text,
                timestamp=datetime.now().isoformat(),
                confidence=confidence
            )
            
            # Use LangGraph AI service to process the speech and generate response
            ai_response = self.langgraph_telecaller.process_conversation(
                user_input=speech_text,
                call_sid=call_sid,
                context={'database_tools': self.database_tools}
            )
            
            # Store AI response transcription
            self.call_storage.store_transcription(
                call_sid=call_sid,
                speaker='ai',
                text=ai_response.get('message', ''),
                timestamp=datetime.now().isoformat(),
                confidence=1.0  # AI responses have high confidence
            )
            
            # Update call metadata with latest interaction
            metadata = {
                'last_interaction': datetime.now().isoformat(),
                'last_user_input': speech_text,
                'last_ai_response': ai_response.get('message', ''),
                'speech_confidence': confidence
            }
            
            self.call_storage.store_call_metadata(call_sid, metadata)
            
            # Check if call should end based on AI decision
            if ai_response.get('end_call', False):
                # Analyze the entire call before ending
                call_analysis = self.call_storage.analyze_call_outcome(call_sid)
                logger.info(f"Call analysis for {call_sid}: {call_analysis}")
                
                return self._create_response(
                    ai_response.get('message', 'Thank you for your time. Goodbye!'),
                    end_call=True
                )
            
            return self._create_response(ai_response.get('message', 'Could you please repeat that?'))
            
        except Exception as e:
            logger.error(f"Error in handle_speech_result: {str(e)}")
            return self._create_response("I'm having trouble understanding. Could you please repeat?")
    
    def handle_call_status_update(self, call_sid: str, status_data: dict) -> dict:
        """Enhanced call status update with analysis trigger"""
        try:
            call_status = status_data.get('CallStatus', '')
            logger.info(f"Call status update for {call_sid}: {call_status}")
            
            # Store status in metadata
            metadata = {
                'call_status': call_status,
                'status_update_time': datetime.now().isoformat(),
                'call_duration': status_data.get('CallDuration', 0)
            }
            
            self.call_storage.store_call_metadata(call_sid, metadata)
            
            # If call is completed, perform final analysis
            if call_status in ['completed', 'busy', 'no-answer', 'failed', 'canceled']:
                try:
                    # Generate comprehensive call analysis
                    call_analysis = self.call_storage.analyze_call_outcome(call_sid)
                    logger.info(f"Final call analysis for {call_sid}: {call_analysis}")
                    
                    # Log the outcome for monitoring
                    outcome = call_analysis.get('overall_outcome', 'unknown')
                    confidence = call_analysis.get('outcome_confidence', 0)
                    logger.info(f"Call {call_sid} ended with outcome: {outcome} (confidence: {confidence:.2f})")
                    
                except Exception as analysis_error:
                    logger.error(f"Error analyzing completed call {call_sid}: {str(analysis_error)}")
            
            return {"status": "received"}
            
        except Exception as e:
            logger.error(f"Error in handle_call_status_update: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def _create_response(self, message: str, end_call: bool = False) -> dict:
        """Create standardized response for Twilio"""
        return {
            'message': message,
            'end_call': end_call,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_call_analysis(self, call_sid: str) -> Dict[str, Any]:
        """Get detailed call analysis including sentiment and outcomes"""
        try:
            analysis = self.call_storage.get_call_analysis(call_sid)
            if analysis:
                return {
                    'status': 'success',
                    'call_sid': call_sid,
                    'analysis': analysis
                }
            else:
                return {
                    'status': 'not_found',
                    'message': f'No analysis found for call {call_sid}'
                }
        except Exception as e:
            logger.error(f"Error getting call analysis: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def generate_daily_report(self, date: str = None) -> Dict[str, Any]:
        """Generate daily report with all call outcomes"""
        try:
            report = self.call_storage.generate_daily_report(date)
            return {
                'status': 'success',
                'report': report
            }
        except Exception as e:
            logger.error(f"Error generating daily report: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def get_database_info(self, query_type: str, **kwargs) -> Dict[str, Any]:
        """Get information from database using available tools"""
        
        try:
            if query_type == 'partners':
                partners = db_access.get_partners(kwargs.get('partner_type'))
                return {'status': 'success', 'data': partners}
                
            elif query_type == 'programs':
                programs = db_access.get_programs(kwargs.get('partner_id'))
                return {'status': 'success', 'data': programs}
                
            elif query_type == 'events':
                events = db_access.get_program_events(kwargs.get('program_id'))
                return {'status': 'success', 'data': events}
                
            elif query_type == 'upcoming_events':
                events = db_access.get_upcoming_events(kwargs.get('days_ahead', 30))
                return {'status': 'success', 'data': events}
                
            elif query_type == 'search_programs':
                programs = db_access.search_programs_by_name(kwargs.get('search_term', ''))
                return {'status': 'success', 'data': programs}
                
            else:
                return {'status': 'error', 'message': f'Unknown query type: {query_type}'}
                
        except Exception as e:
            logger.error(f"Error getting database info: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def test_connections(self) -> Dict[str, Any]:
        """Test all system connections"""
        
        try:
            # Test database connection
            db_connected = db_access.test_connection()
            
            # Test LangGraph telecaller
            langgraph_connected = self.langgraph_telecaller.test_connection()
            
            # Test storage directories
            recordings_path = os.getenv('CALL_RECORDINGS_PATH', './call_recordings')
            transcriptions_path = os.getenv('CALL_TRANSCRIPTIONS_PATH', './call_transcriptions')
            
            storage_ok = os.path.exists(recordings_path) and os.path.exists(transcriptions_path)
            
            return {
                'status': 'success',
                'connections': {
                    'database': db_connected,
                    'langgraph': langgraph_connected,
                    'local_storage': storage_ok
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error testing connections: {str(e)}")
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_call_summary(self, call_sid: str) -> Dict[str, Any]:
        """Get complete call summary including transcriptions and context"""
        
        try:
            # Get call metadata
            call_metadata = self.call_storage.get_call_metadata(call_sid)
            
            # Get transcriptions
            transcriptions = self.call_storage.get_transcriptions(call_sid)
            
            # Get recording path if available
            recordings_path = os.getenv('CALL_RECORDINGS_PATH', './call_recordings')
            recording_file = os.path.join(recordings_path, f"{call_sid}.wav")
            has_recording = os.path.exists(recording_file)
            
            return {
                'status': 'success',
                'call_sid': call_sid,
                'metadata': call_metadata,
                'transcriptions': transcriptions,
                'has_recording': has_recording,
                'recording_path': recording_file if has_recording else None
            }
            
        except Exception as e:
            logger.error(f"Error getting call summary: {str(e)}")
            return {
                'status': 'error',
                'message': str(e),
                'call_sid': call_sid
            }

# Global handler instance
enhanced_handler = EnhancedTelecallerHandler()
