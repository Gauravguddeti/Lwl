"""
Enhanced Call Storage Manager with sentiment analysis and confidence scoring
Handles local file operations for call data before AWS migration
Includes transcription analysis, sentiment detection, and response classification
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import requests
from pathlib import Path
import re

logger = logging.getLogger(__name__)

class CallStorageManager:
    """Enhanced manager for local storage of call recordings, transcriptions, and analysis"""
    
    def __init__(self):
        self.recordings_path = os.getenv('CALL_RECORDINGS_PATH', './call_recordings')
        self.transcriptions_path = os.getenv('CALL_TRANSCRIPTIONS_PATH', './call_transcriptions')
        self.sentiment_path = os.path.join(self.transcriptions_path, 'sentiment_analysis')
        
        # Create directories if they don't exist
        Path(self.recordings_path).mkdir(parents=True, exist_ok=True)
        Path(self.transcriptions_path).mkdir(parents=True, exist_ok=True)
        Path(self.sentiment_path).mkdir(parents=True, exist_ok=True)
        
        # Response classification patterns
        self.response_patterns = {
            'yes': [
                r'\b(yes|yeah|yep|sure|ok|okay|alright|definitely|absolutely|correct|right|true)\b',
                r'\b(i\'m\s+interested|sounds\s+good|that\s+works|count\s+me\s+in)\b',
                r'\b(i\s+agree|i\s+accept|i\s+want|i\s+would\s+like)\b'
            ],
            'no': [
                r'\b(no|nope|nah|not\s+interested|not\s+really|i\s+don\'t|don\'t\s+want)\b',
                r'\b(maybe\s+later|not\s+now|i\'m\s+busy|can\'t\s+afford|too\s+expensive)\b',
                r'\b(not\s+for\s+me|i\s+decline|i\s+refuse|i\s+pass)\b'
            ],
            'later': [
                r'\b(later|call\s+back|maybe\s+next|in\s+future|some\s+other\s+time)\b',
                r'\b(think\s+about\s+it|consider\s+it|let\s+me\s+think|need\s+time)\b',
                r'\b(not\s+right\s+now|busy\s+right\s+now|can\s+we\s+reschedule)\b'
            ],
            'unclear': [
                r'\b(what|huh|sorry|can\s+you\s+repeat|didn\'t\s+catch|unclear)\b',
                r'\b(speak\s+louder|can\'t\s+hear|bad\s+connection|breaking\s+up)\b'
            ]
        }
        
        logger.info(f"Enhanced Call Storage Manager initialized")
        logger.info(f"Recordings path: {self.recordings_path}")
        logger.info(f"Transcriptions path: {self.transcriptions_path}")
        logger.info(f"Sentiment analysis path: {self.sentiment_path}")
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Simple sentiment analysis based on keyword patterns"""
        try:
            text_lower = text.lower()
            
            # Define positive and negative keywords
            positive_words = [
                'yes', 'great', 'awesome', 'love', 'excellent', 'amazing', 'fantastic',
                'interested', 'excited', 'want', 'like', 'good', 'perfect', 'wonderful'
            ]
            
            negative_words = [
                'no', 'hate', 'terrible', 'awful', 'bad', 'boring', 'expensive',
                'not interested', 'don\'t want', 'refuse', 'decline', 'waste'
            ]
            
            positive_count = sum(1 for word in positive_words if word in text_lower)
            negative_count = sum(1 for word in negative_words if word in text_lower)
            
            # Calculate polarity (-1 to 1)
            total_sentiment_words = positive_count + negative_count
            if total_sentiment_words > 0:
                polarity = (positive_count - negative_count) / total_sentiment_words
            else:
                polarity = 0.0
            
            # Classify sentiment
            if polarity > 0.2:
                sentiment = 'positive'
            elif polarity < -0.2:
                sentiment = 'negative'
            else:
                sentiment = 'neutral'
            
            # Calculate confidence based on how many sentiment words found
            confidence = min(total_sentiment_words / 10.0, 1.0)  # Normalize to 0-1
            
            return {
                'sentiment': sentiment,
                'polarity': polarity,
                'subjectivity': 0.5,  # Default value
                'confidence': confidence,
                'positive_words_found': positive_count,
                'negative_words_found': negative_count
            }
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {str(e)}")
            return {
                'sentiment': 'unknown',
                'polarity': 0.0,
                'subjectivity': 0.0,
                'confidence': 0.0,
                'error': str(e)
            }
    
    def classify_response(self, text: str) -> Dict[str, Any]:
        """Classify caller response as yes/no/later/unclear"""
        try:
            text_lower = text.lower()
            classifications = {}
            
            for response_type, patterns in self.response_patterns.items():
                confidence = 0.0
                matches = []
                
                for pattern in patterns:
                    match = re.search(pattern, text_lower)
                    if match:
                        matches.append(match.group())
                        confidence += 0.3  # Increase confidence for each match
                
                if matches:
                    classifications[response_type] = {
                        'confidence': min(confidence, 1.0),
                        'matches': matches
                    }
            
            # Determine primary classification
            if classifications:
                primary = max(classifications.keys(), key=lambda k: classifications[k]['confidence'])
                primary_confidence = classifications[primary]['confidence']
            else:
                primary = 'unclear'
                primary_confidence = 0.0
            
            return {
                'primary_classification': primary,
                'confidence': primary_confidence,
                'all_classifications': classifications,
                'text_analyzed': text
            }
            
        except Exception as e:
            logger.error(f"Error classifying response: {str(e)}")
            return {
                'primary_classification': 'error',
                'confidence': 0.0,
                'error': str(e),
                'text_analyzed': text
            }
    
    def store_recording(self, call_sid: str, recording_url: str) -> str:
        """Download and store call recording locally"""
        
        try:
            # Download recording from URL
            response = requests.get(recording_url, stream=True)
            response.raise_for_status()
            
            # Save recording file
            recording_filename = f"{call_sid}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
            recording_path = os.path.join(self.recordings_path, recording_filename)
            
            with open(recording_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Recording stored: {recording_path}")
            return recording_path
            
        except Exception as e:
            logger.error(f"Error storing recording for {call_sid}: {str(e)}")
            raise
    
    def store_transcription(self, call_sid: str, speaker: str, text: str, timestamp: str, confidence: float = 0.0) -> str:
        """Store call transcription with sentiment analysis and response classification"""
        
        try:
            # Perform sentiment analysis
            sentiment_data = self.analyze_sentiment(text)
            
            # Classify response if it's from caller
            response_classification = {}
            if speaker == 'caller':
                response_classification = self.classify_response(text)
            
            # Create enhanced transcription entry
            transcription_entry = {
                'call_sid': call_sid,
                'speaker': speaker,  # 'caller' or 'ai'
                'text': text,
                'timestamp': timestamp,
                'transcription_confidence': confidence,
                'sentiment_analysis': sentiment_data,
                'response_classification': response_classification if speaker == 'caller' else None,
                'stored_at': datetime.now().isoformat()
            }
            
            # File path for transcriptions
            transcription_filename = f"{call_sid}_transcription.jsonl"
            transcription_path = os.path.join(self.transcriptions_path, transcription_filename)
            
            # Append to file (JSONL format)
            with open(transcription_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(transcription_entry) + '\n')
            
            # Store detailed analysis if it's a caller response
            if speaker == 'caller' and response_classification:
                self._store_response_analysis(call_sid, text, response_classification, sentiment_data, timestamp)
            
            logger.info(f"Enhanced transcription stored for {call_sid}: {text[:50]}...")
            return transcription_path
            
        except Exception as e:
            logger.error(f"Error storing enhanced transcription for {call_sid}: {str(e)}")
            raise
    
    def _store_response_analysis(self, call_sid: str, text: str, classification: Dict, sentiment: Dict, timestamp: str):
        """Store detailed response analysis in separate file"""
        try:
            analysis_entry = {
                'call_sid': call_sid,
                'timestamp': timestamp,
                'caller_text': text,
                'response_classification': classification['primary_classification'],
                'classification_confidence': classification['confidence'],
                'sentiment': sentiment['sentiment'],
                'sentiment_confidence': sentiment['confidence'],
                'polarity': sentiment['polarity'],
                'subjectivity': sentiment['subjectivity'],
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            # File path for response analysis
            analysis_filename = f"{call_sid}_response_analysis.txt"
            analysis_path = os.path.join(self.sentiment_path, analysis_filename)
            
            # Append human-readable analysis
            with open(analysis_path, 'a', encoding='utf-8') as f:
                f.write(f"\n--- Response Analysis at {timestamp} ---\n")
                f.write(f"Caller said: \"{text}\"\n")
                f.write(f"Classification: {classification['primary_classification']} (confidence: {classification['confidence']:.2f})\n")
                f.write(f"Sentiment: {sentiment['sentiment']} (polarity: {sentiment['polarity']:.2f})\n")
                f.write(f"Confidence: {sentiment['confidence']:.2f}\n")
                
                if classification['all_classifications']:
                    f.write(f"All detected patterns: {classification['all_classifications']}\n")
                
                f.write("-" * 50 + "\n")
            
            # Also store as JSON for programmatic access
            json_filename = f"{call_sid}_response_analysis.jsonl"
            json_path = os.path.join(self.sentiment_path, json_filename)
            
            with open(json_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(analysis_entry) + '\n')
                
        except Exception as e:
            logger.error(f"Error storing response analysis: {str(e)}")
    
    def transcribe_audio_segment(self, audio_path: str, start_time: float = 0, duration: float = None) -> Dict[str, Any]:
        """Placeholder for audio transcription - to be implemented with proper audio libraries"""
        try:
            # For now, return a placeholder response
            # This will be implemented when audio processing libraries are properly installed
            return {
                'text': '[Audio transcription not available - requires audio processing libraries]',
                'confidence': 0.0,
                'engine': 'placeholder',
                'duration': duration or 0.0,
                'start_time': start_time,
                'note': 'Audio transcription requires speech_recognition and pydub libraries'
            }
            
        except Exception as e:
            logger.error(f"Error in audio transcription placeholder: {str(e)}")
            return {
                'text': f"[Transcription error: {str(e)}]",
                'confidence': 0.0,
                'engine': 'error',
                'error': str(e)
            }
    
    def store_call_metadata(self, call_sid: str, metadata: Dict[str, Any]) -> str:
        """Store call metadata locally"""
        
        try:
            # Add timestamp if not present
            if 'stored_at' not in metadata:
                metadata['stored_at'] = datetime.now().isoformat()
            
            # File path for metadata
            metadata_filename = f"{call_sid}_metadata.json"
            metadata_path = os.path.join(self.transcriptions_path, metadata_filename)
            
            # Store metadata
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, default=str)
            
            logger.info(f"Metadata stored for {call_sid}")
            return metadata_path
            
        except Exception as e:
            logger.error(f"Error storing metadata for {call_sid}: {str(e)}")
            raise
    
    def get_transcriptions(self, call_sid: str) -> List[Dict[str, Any]]:
        """Get all transcriptions for a call"""
        
        try:
            transcription_filename = f"{call_sid}_transcription.jsonl"
            transcription_path = os.path.join(self.transcriptions_path, transcription_filename)
            
            if not os.path.exists(transcription_path):
                return []
            
            transcriptions = []
            with open(transcription_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        transcriptions.append(json.loads(line.strip()))
            
            return transcriptions
            
        except Exception as e:
            logger.error(f"Error getting transcriptions for {call_sid}: {str(e)}")
            return []
    
    def get_call_metadata(self, call_sid: str) -> Optional[Dict[str, Any]]:
        """Get call metadata"""
        
        try:
            metadata_filename = f"{call_sid}_metadata.json"
            metadata_path = os.path.join(self.transcriptions_path, metadata_filename)
            
            if not os.path.exists(metadata_path):
                return None
            
            with open(metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Error getting metadata for {call_sid}: {str(e)}")
            return None
    
    def get_recording_path(self, call_sid: str) -> Optional[str]:
        """Get path to recording file if it exists"""
        
        try:
            # Look for recording files with this call_sid
            for filename in os.listdir(self.recordings_path):
                if filename.startswith(call_sid) and filename.endswith('.wav'):
                    return os.path.join(self.recordings_path, filename)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting recording path for {call_sid}: {str(e)}")
            return None
    
    def list_calls(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List recent calls with basic information"""
        
        try:
            calls = []
            
            # Get all metadata files
            for filename in os.listdir(self.transcriptions_path):
                if filename.endswith('_metadata.json'):
                    call_sid = filename.replace('_metadata.json', '')
                    
                    try:
                        metadata = self.get_call_metadata(call_sid)
                        if metadata:
                            # Add recording status
                            has_recording = self.get_recording_path(call_sid) is not None
                            
                            # Add transcription count
                            transcriptions = self.get_transcriptions(call_sid)
                            
                            call_info = {
                                'call_sid': call_sid,
                                'start_time': metadata.get('call_start_time'),
                                'caller_number': metadata.get('caller_number'),
                                'has_recording': has_recording,
                                'transcription_count': len(transcriptions),
                                'last_updated': metadata.get('last_updated')
                            }
                            calls.append(call_info)
                            
                    except Exception as e:
                        logger.warning(f"Error processing call {call_sid}: {str(e)}")
                        continue
            
            # Sort by start time (most recent first)
            calls.sort(key=lambda x: x.get('start_time', ''), reverse=True)
            
            return calls[:limit]
            
        except Exception as e:
            logger.error(f"Error listing calls: {str(e)}")
            return []
    
    def analyze_call_outcome(self, call_sid: str) -> Dict[str, Any]:
        """Analyze entire call to determine outcome and generate summary"""
        try:
            transcriptions = self.get_transcriptions(call_sid)
            if not transcriptions:
                return {'error': 'No transcriptions found for call'}
            
            # Separate caller and AI messages
            caller_messages = [t for t in transcriptions if t['speaker'] == 'caller']
            ai_messages = [t for t in transcriptions if t['speaker'] == 'ai']
            
            # Analyze caller responses
            response_summary = {
                'yes_count': 0,
                'no_count': 0,
                'later_count': 0,
                'unclear_count': 0,
                'total_responses': len(caller_messages)
            }
            
            sentiment_summary = {
                'positive_count': 0,
                'negative_count': 0,
                'neutral_count': 0,
                'average_polarity': 0.0,
                'average_confidence': 0.0
            }
            
            total_polarity = 0.0
            total_confidence = 0.0
            
            for msg in caller_messages:
                # Count response classifications
                if 'response_classification' in msg and msg['response_classification']:
                    classification = msg['response_classification'].get('primary_classification', 'unclear')
                    # Map classification to count key
                    count_key = f"{classification}_count"
                    if count_key in response_summary:
                        response_summary[count_key] += 1
                
                # Aggregate sentiment
                if 'sentiment_analysis' in msg and msg['sentiment_analysis']:
                    sentiment = msg['sentiment_analysis'].get('sentiment', 'neutral')
                    count_key = f"{sentiment}_count"
                    if count_key in sentiment_summary:
                        sentiment_summary[count_key] += 1
                    
                    total_polarity += msg['sentiment_analysis'].get('polarity', 0.0)
                    total_confidence += msg['sentiment_analysis'].get('confidence', 0.0)
            
            # Calculate averages
            if caller_messages:
                sentiment_summary['average_polarity'] = total_polarity / len(caller_messages)
                sentiment_summary['average_confidence'] = total_confidence / len(caller_messages)
            
            # Determine overall call outcome
            if response_summary['yes_count'] > response_summary['no_count']:
                overall_outcome = 'interested'
            elif response_summary['no_count'] > response_summary['yes_count']:
                overall_outcome = 'not_interested'
            elif response_summary['later_count'] > 0:
                overall_outcome = 'follow_up_needed'
            else:
                overall_outcome = 'unclear'
            
            # Calculate outcome confidence
            max_response_count = max(response_summary['yes_count'], response_summary['no_count'], response_summary['later_count'])
            outcome_confidence = max_response_count / max(response_summary['total_responses'], 1)
            
            call_analysis = {
                'call_sid': call_sid,
                'overall_outcome': overall_outcome,
                'outcome_confidence': outcome_confidence,
                'response_summary': response_summary,
                'sentiment_summary': sentiment_summary,
                'call_duration_turns': len(transcriptions),
                'caller_turn_count': len(caller_messages),
                'ai_turn_count': len(ai_messages),
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            # Store analysis summary
            self._store_call_analysis_summary(call_sid, call_analysis)
            
            return call_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing call outcome for {call_sid}: {str(e)}")
            return {'error': str(e)}
    
    def _store_call_analysis_summary(self, call_sid: str, analysis: Dict[str, Any]):
        """Store call analysis summary in human-readable format"""
        try:
            summary_filename = f"{call_sid}_call_summary.txt"
            summary_path = os.path.join(self.sentiment_path, summary_filename)
            
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write(f"CALL ANALYSIS SUMMARY\n")
                f.write(f"=====================\n")
                f.write(f"Call ID: {call_sid}\n")
                f.write(f"Analysis Date: {analysis['analysis_timestamp']}\n\n")
                
                f.write(f"OVERALL OUTCOME: {analysis['overall_outcome'].upper()}\n")
                f.write(f"Confidence: {analysis['outcome_confidence']:.2f}\n\n")
                
                f.write(f"RESPONSE BREAKDOWN:\n")
                f.write(f"- Yes responses: {analysis['response_summary']['yes_count']}\n")
                f.write(f"- No responses: {analysis['response_summary']['no_count']}\n")
                f.write(f"- Later responses: {analysis['response_summary']['later_count']}\n")
                f.write(f"- Unclear responses: {analysis['response_summary']['unclear_count']}\n")
                f.write(f"- Total caller responses: {analysis['response_summary']['total_responses']}\n\n")
                
                f.write(f"SENTIMENT ANALYSIS:\n")
                f.write(f"- Positive: {analysis['sentiment_summary']['positive_count']}\n")
                f.write(f"- Negative: {analysis['sentiment_summary']['negative_count']}\n")
                f.write(f"- Neutral: {analysis['sentiment_summary']['neutral_count']}\n")
                f.write(f"- Average sentiment polarity: {analysis['sentiment_summary']['average_polarity']:.2f}\n")
                f.write(f"- Average confidence: {analysis['sentiment_summary']['average_confidence']:.2f}\n\n")
                
                f.write(f"CALL STATISTICS:\n")
                f.write(f"- Total conversation turns: {analysis['call_duration_turns']}\n")
                f.write(f"- Caller turns: {analysis['caller_turn_count']}\n")
                f.write(f"- AI turns: {analysis['ai_turn_count']}\n")
            
            # Also store as JSON
            json_filename = f"{call_sid}_call_analysis.json"
            json_path = os.path.join(self.sentiment_path, json_filename)
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Error storing call analysis summary: {str(e)}")
    
    def get_call_analysis(self, call_sid: str) -> Optional[Dict[str, Any]]:
        """Get stored call analysis"""
        try:
            json_filename = f"{call_sid}_call_analysis.json"
            json_path = os.path.join(self.sentiment_path, json_filename)
            
            if not os.path.exists(json_path):
                # Generate analysis if it doesn't exist
                return self.analyze_call_outcome(call_sid)
            
            with open(json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Error getting call analysis for {call_sid}: {str(e)}")
            return None
    
    def generate_daily_report(self, date: str = None) -> Dict[str, Any]:
        """Generate daily report of all calls"""
        try:
            if not date:
                date = datetime.now().strftime('%Y-%m-%d')
            
            calls = self.list_calls(limit=1000)  # Get all calls
            daily_calls = []
            
            # Filter calls by date
            for call in calls:
                if call.get('start_time', '').startswith(date):
                    analysis = self.get_call_analysis(call['call_sid'])
                    if analysis:
                        call['analysis'] = analysis
                    daily_calls.append(call)
            
            # Generate summary statistics
            total_calls = len(daily_calls)
            successful_calls = len([c for c in daily_calls if c.get('analysis', {}).get('overall_outcome') == 'interested'])
            follow_up_calls = len([c for c in daily_calls if c.get('analysis', {}).get('overall_outcome') == 'follow_up_needed'])
            unsuccessful_calls = len([c for c in daily_calls if c.get('analysis', {}).get('overall_outcome') == 'not_interested'])
            
            report = {
                'date': date,
                'total_calls': total_calls,
                'successful_calls': successful_calls,
                'follow_up_calls': follow_up_calls,
                'unsuccessful_calls': unsuccessful_calls,
                'success_rate': successful_calls / max(total_calls, 1),
                'calls': daily_calls,
                'report_generated': datetime.now().isoformat()
            }
            
            # Store daily report
            report_filename = f"daily_report_{date}.json"
            report_path = os.path.join(self.sentiment_path, report_filename)
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, default=str)
            
            # Store human-readable report
            txt_filename = f"daily_report_{date}.txt"
            txt_path = os.path.join(self.sentiment_path, txt_filename)
            
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(f"DAILY TELECALLER REPORT - {date}\n")
                f.write(f"=" * 40 + "\n\n")
                f.write(f"SUMMARY:\n")
                f.write(f"- Total calls: {total_calls}\n")
                f.write(f"- Successful (interested): {successful_calls}\n")
                f.write(f"- Follow-up needed: {follow_up_calls}\n")
                f.write(f"- Not interested: {unsuccessful_calls}\n")
                f.write(f"- Success rate: {report['success_rate']:.1%}\n\n")
                
                f.write(f"DETAILED CALL BREAKDOWN:\n")
                for call in daily_calls:
                    analysis = call.get('analysis', {})
                    f.write(f"\nCall {call['call_sid']}:\n")
                    f.write(f"  - Time: {call.get('start_time', 'Unknown')}\n")
                    f.write(f"  - Number: {call.get('caller_number', 'Unknown')}\n")
                    f.write(f"  - Outcome: {analysis.get('overall_outcome', 'Unknown')}\n")
                    f.write(f"  - Confidence: {analysis.get('outcome_confidence', 0):.2f}\n")
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating daily report: {str(e)}")
            return {'error': str(e)}
        """Delete all data for a specific call"""
        
        results = {
            'metadata_deleted': False,
            'transcription_deleted': False,
            'recording_deleted': False
        }
        
        try:
            # Delete metadata
            metadata_filename = f"{call_sid}_metadata.json"
            metadata_path = os.path.join(self.transcriptions_path, metadata_filename)
            if os.path.exists(metadata_path):
                os.remove(metadata_path)
                results['metadata_deleted'] = True
            
            # Delete transcription
            transcription_filename = f"{call_sid}_transcription.jsonl"
            transcription_path = os.path.join(self.transcriptions_path, transcription_filename)
            if os.path.exists(transcription_path):
                os.remove(transcription_path)
                results['transcription_deleted'] = True
            
            # Delete recording
            recording_path = self.get_recording_path(call_sid)
            if recording_path and os.path.exists(recording_path):
                os.remove(recording_path)
                results['recording_deleted'] = True
            
            logger.info(f"Call data deleted for {call_sid}: {results}")
            
        except Exception as e:
            logger.error(f"Error deleting call data for {call_sid}: {str(e)}")
        
        return results
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        
        try:
            stats = {
                'recording_files': 0,
                'total_storage_mb': 0,
                'transcription_files': 0,
                'total_calls': 0,
                'storage_paths': {
                    'recordings': self.recordings_path,
                    'transcriptions': self.transcriptions_path
                }
            }
            
            # Count recordings
            if os.path.exists(self.recordings_path):
                recording_files = [f for f in os.listdir(self.recordings_path) if f.endswith('.wav')]
                stats['recording_files'] = len(recording_files)
                
                # Calculate total size
                total_size = 0
                for filename in recording_files:
                    file_path = os.path.join(self.recordings_path, filename)
                    total_size += os.path.getsize(file_path)
                stats['total_storage_mb'] = round(total_size / (1024 * 1024), 2)
            
            # Count transcriptions and calls
            if os.path.exists(self.transcriptions_path):
                transcription_files = [f for f in os.listdir(self.transcriptions_path) if f.endswith('.jsonl')]
                metadata_files = [f for f in os.listdir(self.transcriptions_path) if f.endswith('_metadata.json')]
                
                stats['transcription_files'] = len(transcription_files)
                stats['total_calls'] = len(metadata_files)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting storage stats: {str(e)}")
            return {'error': str(e)}
    
    def determine_call_outcome(self, messages: List[Dict]) -> str:
        """Determine call outcome from conversation messages"""
        if not messages:
            return 'unsure'
        
        # Check if call had errors or disconnected early
        ai_messages = [msg.get('text', '') for msg in messages if msg.get('speaker') == 'ai']
        caller_messages = [msg.get('text', '') for msg in messages if msg.get('speaker') == 'caller']
        
        # If only AI message and it contains errors, classify as technical issue
        if len(messages) == 1 and len(caller_messages) == 0:
            ai_text = ai_messages[0] if ai_messages else ''
            if any(error_word in ai_text.lower() for error_word in ['error', 'invalid', 'dict', 'exception']):
                return 'technical_error'
        
        # If no caller responses, it's likely a disconnect or no answer
        if not caller_messages:
            return 'no_response'
        
        # Get all caller messages for analysis
        caller_text = ' '.join(caller_messages).lower()
        
        # Check for unsure/uncertain responses FIRST (more specific than negative)
        unsure_indicators = ['not sure', 'unsure', 'uncertain', 'maybe', 'perhaps', 'might be', 'could be', 'let me think']
        if any(word in caller_text for word in unsure_indicators):
            return 'unsure'
        
        # Check for negative indicators (less specific patterns)
        negative_patterns = [
            'not interested', 'no thanks', 'not now', 'not today', 'busy right now',
            'remove me', 'dont call', "don't call", 'no way', 'absolutely not',
            'not for us', 'we are not', 'i am not', "i'm not", "we're not"
        ]
        if any(pattern in caller_text for pattern in negative_patterns):
            return 'no'
        
        # Check for simple "no" responses
        simple_no_indicators = ['no', 'nope', 'nah']
        # But make sure it's not part of a positive phrase
        for word in simple_no_indicators:
            if f" {word} " in f" {caller_text} " or caller_text.startswith(f"{word} ") or caller_text.endswith(f" {word}"):
                return 'no'
        
        # Check for callback requests
        callback_indicators = ['callback', 'call back', 'later', 'next time', 'next week', 'next month', 'maybe later', 'think about it']
        if any(word in caller_text for word in callback_indicators):
            return 'callback'
        
        # Check for positive indicators
        positive_indicators = ['yes', 'interested', 'sounds good', 'tell me more', 'okay', 'im in', 'sign up', 'sounds great', 'love to hear']
        if any(word in caller_text for word in positive_indicators):
            return 'yes'
        
        return 'unsure'
    
    def create_transcription_filename(self, call_sid: str, messages: List[Dict], partner_name: str = None) -> str:
        """Create transcription filename in format: {partner_name}_{outcome}_{DDMMYY}_{call_sid}_summary.txt"""
        outcome = self.determine_call_outcome(messages)
        
        # Get current date in DDMMYY format
        current_date = datetime.now()
        date_str = current_date.strftime('%d%m%y')
        
        # Create safe partner name for filename
        if partner_name:
            safe_partner_name = self._create_safe_filename(partner_name)
        else:
            safe_partner_name = "unknown_partner"
        
        return f"{safe_partner_name}_{outcome}_{date_str}_{call_sid}_summary.txt"
    
    def create_json_filename(self, call_sid: str, messages: List[Dict], partner_name: str = None) -> str:
        """Create JSON filename in format: {partner_name}_{outcome}_{DDMMYY}_{call_sid}_conversation.jsonl"""
        outcome = self.determine_call_outcome(messages)
        
        # Get current date in DDMMYY format
        current_date = datetime.now()
        date_str = current_date.strftime('%d%m%y')
        
        # Create safe partner name for filename
        if partner_name:
            safe_partner_name = self._create_safe_filename(partner_name)
        else:
            safe_partner_name = "unknown_partner"
        
        return f"{safe_partner_name}_{outcome}_{date_str}_{call_sid}_conversation.jsonl"
    
    def _create_safe_filename(self, name: str) -> str:
        """Create a safe filename from partner name by removing/replacing special characters"""
        import re
        
        # Replace spaces with underscores and remove special characters
        safe_name = re.sub(r'[^\w\s-]', '', name)  # Remove special chars except word chars, spaces, hyphens
        safe_name = re.sub(r'[-\s]+', '_', safe_name)  # Replace spaces and hyphens with underscores
        safe_name = safe_name.strip('_')  # Remove leading/trailing underscores
        
        # Limit length and ensure it's not empty
        safe_name = safe_name[:50]  # Limit to 50 characters
        if not safe_name:
            safe_name = "partner"
        
        return safe_name
        outcome = self.determine_call_outcome(messages)
        
        # Get current date in DDMMYY format
        current_date = datetime.now()
        date_str = current_date.strftime('%d%m%y')
        
        return f"to_{outcome}_{date_str}_{call_sid}_conversation.jsonl"
    
    def download_recording(self, recording_url: str, call_sid: str, partner_name: str = None) -> Optional[str]:
        """Download recording file from Twilio and save with enhanced naming format"""
        try:
            if not recording_url:
                logger.warning(f"No recording URL provided for call {call_sid}")
                return None
            
            # Use the exact RecordingUrl provided by Twilio
            # Twilio defaults to mp3, so add mp3 extension if no extension exists
            download_url = recording_url
            if not (recording_url.endswith('.wav') or recording_url.endswith('.mp3')):
                download_url = f"{recording_url}.mp3"
            
            logger.info(f"Downloading recording from: {download_url}")
            
            # Download the recording
            response = requests.get(download_url, auth=(
                os.getenv('TWILIO_ACCOUNT_SID'),
                os.getenv('TWILIO_AUTH_TOKEN')
            ))
            
            if response.status_code == 200:
                # Create enhanced filename matching transcription format
                if partner_name:
                    # Get current date in DDMMYY format
                    current_date = datetime.now()
                    date_str = current_date.strftime('%d%m%y')
                    
                    # Create safe partner name
                    safe_partner_name = self._create_safe_filename(partner_name)
                    
                    # For now, use a default outcome since we don't have messages context
                    # This will be updated when we have conversation context
                    recording_filename = f"{safe_partner_name}_call_{date_str}_{call_sid}_recording.wav"
                else:
                    recording_filename = f"{call_sid}_recording.wav"
                    
                recording_path = os.path.join(self.recordings_path, recording_filename)
                
                # Save the recording
                with open(recording_path, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"Recording downloaded successfully: {recording_filename}")
                return recording_path
            else:
                logger.error(f"Failed to download recording: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading recording for {call_sid}: {e}")
            return None

    def finalize_call_with_sentiment_filename(self, call_sid: str, caller_number: str = "unknown") -> Dict[str, str]:
        """
        Finalize call storage and rename files with sentiment analysis outcome in filename
        Creates descriptive filenames: date_callernumber_sentiment_outcome.ext
        
        Args:
            call_sid: Unique call identifier  
            caller_number: Phone number of the caller
            
        Returns:
            Dictionary with old and new file paths
        """
        try:
            # Analyze call outcome
            call_analysis = self.analyze_call_outcome(call_sid)
            if 'error' in call_analysis:
                logger.error(f"Cannot finalize call {call_sid}: {call_analysis['error']}")
                return {'error': call_analysis['error']}
            
            # Extract sentiment outcome
            overall_outcome = call_analysis.get('overall_outcome', 'unclear')
            outcome_confidence = call_analysis.get('outcome_confidence', 0.0)
            
            # Map outcomes to short codes for filename
            outcome_map = {
                'interested': 'YES',
                'not_interested': 'NO', 
                'follow_up_needed': 'CALLBACK_LATER',
                'unclear': 'UNCLEAR'
            }
            
            outcome_code = outcome_map.get(overall_outcome, 'UNCLEAR')
            confidence_code = f"{int(outcome_confidence * 100)}pct"
            
            # Generate descriptive filename components with unique identifier
            date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            caller_clean = re.sub(r'[^\d]', '', caller_number)[-10:]  # Last 10 digits
            call_unique = call_sid.split('_')[-1] if '_' in call_sid else call_sid[-6:]  # Last part for uniqueness
            
            base_filename = f"{date_str}_{caller_clean}_{outcome_code}_{confidence_code}_{call_unique}"
            
            # Find and rename existing files
            file_renames = {}
            
            # Rename transcription file
            transcription_pattern = f"{call_sid}_*.jsonl"
            transcription_files = list(Path(self.transcriptions_path).glob(transcription_pattern))
            
            if transcription_files:
                old_transcription = transcription_files[0]
                new_transcription = old_transcription.parent / f"{base_filename}_transcription.jsonl"
                old_transcription.rename(new_transcription)
                file_renames['transcription'] = {
                    'old': str(old_transcription),
                    'new': str(new_transcription)
                }
                logger.info(f"Renamed transcription: {old_transcription.name} -> {new_transcription.name}")
            
            # Rename recording file  
            recording_pattern = f"{call_sid}_*.wav"
            recording_files = list(Path(self.recordings_path).glob(recording_pattern))
            
            if recording_files:
                old_recording = recording_files[0]
                new_recording = old_recording.parent / f"{base_filename}_recording.wav"
                old_recording.rename(new_recording)
                file_renames['recording'] = {
                    'old': str(old_recording),
                    'new': str(new_recording)
                }
                logger.info(f"Renamed recording: {old_recording.name} -> {new_recording.name}")
            
            # Rename metadata file
            metadata_pattern = f"{call_sid}_*.json"
            metadata_files = list(Path(self.transcriptions_path).glob(metadata_pattern))
            
            if metadata_files:
                old_metadata = metadata_files[0] 
                new_metadata = old_metadata.parent / f"{base_filename}_metadata.json"
                old_metadata.rename(new_metadata)
                file_renames['metadata'] = {
                    'old': str(old_metadata),
                    'new': str(new_metadata)
                }
                logger.info(f"Renamed metadata: {old_metadata.name} -> {new_metadata.name}")
            
            # Create call summary file
            summary_path = os.path.join(self.transcriptions_path, f"{base_filename}_summary.txt")
            self._create_call_summary_file(summary_path, call_analysis, caller_number)
            
            logger.info(f"Call finalized with sentiment outcome: {outcome_code} ({confidence_code} confidence)")
            
            return {
                'status': 'success',
                'outcome': overall_outcome,
                'outcome_code': outcome_code,
                'confidence': outcome_confidence,
                'base_filename': base_filename,
                'files_renamed': file_renames,
                'summary_file': summary_path
            }
            
        except Exception as e:
            logger.error(f"Error finalizing call with sentiment filename: {str(e)}")
            return {'error': str(e)}
    
    def _create_call_summary_file(self, summary_path: str, call_analysis: Dict[str, Any], caller_number: str):
        """Create human-readable call summary file"""
        try:
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write("="*60 + "\n")
                f.write("CALL SUMMARY WITH SENTIMENT ANALYSIS\n")
                f.write("="*60 + "\n\n")
                
                f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Caller: {caller_number}\n")
                f.write(f"Call ID: {call_analysis['call_sid']}\n\n")
                
                f.write("OUTCOME ANALYSIS:\n")
                f.write("-" * 20 + "\n")
                f.write(f"Overall Outcome: {call_analysis['overall_outcome'].upper()}\n")
                f.write(f"Confidence: {call_analysis['outcome_confidence']:.1%}\n\n")
                
                f.write("RESPONSE BREAKDOWN:\n")
                f.write("-" * 20 + "\n")
                resp = call_analysis['response_summary']
                f.write(f"✅ Positive (Yes): {resp['yes_count']}\n")
                f.write(f"❌ Negative (No): {resp['no_count']}\n")
                f.write(f"⏰ Callback Later: {resp['later_count']}\n")
                f.write(f"❓ Unclear: {resp['unclear_count']}\n")
                f.write(f"Total Responses: {resp['total_responses']}\n\n")
                
                f.write("SENTIMENT ANALYSIS:\n")
                f.write("-" * 20 + "\n")
                sent = call_analysis['sentiment_summary']
                f.write(f"😊 Positive: {sent['positive_count']}\n")
                f.write(f"😐 Neutral: {sent['neutral_count']}\n")
                f.write(f"😞 Negative: {sent['negative_count']}\n")
                f.write(f"Average Polarity: {sent['average_polarity']:.2f}\n")
                f.write(f"Average Confidence: {sent['average_confidence']:.1%}\n\n")
                
                f.write("CALL STATISTICS:\n")
                f.write("-" * 20 + "\n")
                f.write(f"Total Turns: {call_analysis['call_duration_turns']}\n")
                f.write(f"Caller Turns: {call_analysis['caller_turn_count']}\n")
                f.write(f"AI Turns: {call_analysis['ai_turn_count']}\n\n")
                
            logger.info(f"Call summary created: {summary_path}")
            
        except Exception as e:
            logger.error(f"Error creating call summary: {str(e)}")
            raise
    
    def finalize_call_enhanced(self, call_sid: str, messages: List[Dict], recording_url: str = None, partner_name: str = None) -> Dict[str, str]:
        """
        Enhanced call finalization with new naming format and recording download
        Format: {partner_name}_{outcome}_{DDMMYY}_{call_sid}
        """
        try:
            # Download recording if URL provided
            recording_path = None
            if recording_url:
                recording_path = self.download_recording(recording_url, call_sid)
            
            # Create transcription summary
            summary_filename = self.create_transcription_filename(call_sid, messages, partner_name)
            summary_path = os.path.join(self.transcriptions_path, summary_filename)
            
            # Create conversation summary
            self._create_enhanced_summary(summary_path, call_sid, messages)
            
            # Create JSON conversation file
            json_filename = self.create_json_filename(call_sid, messages, partner_name)
            json_path = os.path.join(self.transcriptions_path, 'json_archive', json_filename)
            
            # Ensure json_archive directory exists
            Path(os.path.join(self.transcriptions_path, 'json_archive')).mkdir(exist_ok=True)
            
            # Save conversation as JSONL
            with open(json_path, 'w', encoding='utf-8') as f:
                for message in messages:
                    json.dump(message, f, ensure_ascii=False)
                    f.write('\n')
            
            result = {
                'summary_file': summary_filename,
                'json_file': json_filename,
                'outcome': self.determine_call_outcome(messages)
            }
            
            if recording_path:
                # Rename recording with new format
                outcome = self.determine_call_outcome(messages)
                date_str = datetime.now().strftime('%d%m%y')
                
                # Create safe partner name for filename
                if partner_name:
                    safe_partner_name = self._create_safe_filename(partner_name)
                else:
                    safe_partner_name = "unknown_partner"
                
                new_recording_name = f"{safe_partner_name}_{outcome}_{date_str}_{call_sid}_recording.wav"
                new_recording_path = os.path.join(self.recordings_path, new_recording_name)
                
                if os.path.exists(recording_path):
                    os.rename(recording_path, new_recording_path)
                    result['recording_file'] = new_recording_name
                    logger.info(f"Recording saved as: {new_recording_name}")
            
            logger.info(f"Call finalized with enhanced format: {summary_filename}")
            return result
            
        except Exception as e:
            logger.error(f"Error in enhanced call finalization: {str(e)}")
            return {'error': str(e)}
    
    def _create_enhanced_summary(self, summary_path: str, call_sid: str, messages: List[Dict]):
        """Create enhanced summary file with conversation transcript and business insights"""
        try:
            # Analyze conversation for business insights
            insights = self._analyze_conversation_insights(messages)
            
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write("AI-INITIATED CALL CONVERSATION SUMMARY\n")
                f.write("=" * 60 + "\n\n")
                
                f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Call ID: {call_sid}\n")
                f.write(f"AI Caller: Sarah from Learn with Leaders\n")
                f.write(f"Outcome: {self.determine_call_outcome(messages).upper()}\n\n")
                
                # Add business insights section
                f.write("BUSINESS SUMMARY:\n")
                f.write("-" * 40 + "\n")
                f.write(f"Partner Interest Level: {insights['interest_level']}\n")
                f.write(f"Topics Discussed: {', '.join(insights['topics_discussed']) if insights['topics_discussed'] else 'General inquiry'}\n")
                f.write(f"Questions Asked: {insights['questions_count']}\n")
                f.write(f"User Needs: {insights['user_needs']}\n")
                f.write(f"Next Steps: {insights['next_steps']}\n")
                f.write(f"Follow-up Required: {insights['follow_up_needed']}\n\n")
                
                f.write("CONVERSATION TRANSCRIPT:\n")
                f.write("-" * 40 + "\n\n")
                
                for i, message in enumerate(messages, 1):
                    speaker = "AI (Sarah)" if message.get('speaker') == 'ai' else "Partner"
                    text = message.get('text', '')
                    f.write(f"{i}. {speaker}: {text}\n\n")
                
                f.write("=" * 60 + "\n")
                f.write("END OF CALL SUMMARY\n")
                f.write("=" * 60 + "\n")
            
            logger.info(f"Enhanced summary created: {os.path.basename(summary_path)}")
            
        except Exception as e:
            logger.error(f"Error creating enhanced summary: {str(e)}")
    
    def _analyze_conversation_insights(self, messages: List[Dict]) -> Dict[str, Any]:
        """Analyze conversation to extract business insights"""
        try:
            # Get all partner messages
            partner_messages = [msg.get('text', '').lower() for msg in messages if msg.get('speaker') == 'caller']
            all_partner_text = ' '.join(partner_messages)
            
            # Analyze interests and topics
            topics_discussed = []
            interest_indicators = []
            questions_count = 0
            
            # Topic detection
            topic_keywords = {
                'fees_cost': ['cost', 'fees', 'price', 'expensive', 'cheap', 'budget', 'money'],
                'schedule_timing': ['when', 'time', 'schedule', 'duration', 'how long', 'date'],
                'curriculum_content': ['what', 'curriculum', 'subjects', 'topics', 'learn', 'teach'],
                'registration_process': ['register', 'sign up', 'enroll', 'join', 'apply', 'how to'],
                'location_venue': ['where', 'location', 'venue', 'place', 'address'],
                'testimonials_results': ['reviews', 'feedback', 'results', 'success', 'testimonials'],
                'age_group': ['age', 'grade', 'class', 'students', 'children']
            }
            
            for topic, keywords in topic_keywords.items():
                if any(keyword in all_partner_text for keyword in keywords):
                    topics_discussed.append(topic.replace('_', ' ').title())
            
            # Count questions
            questions_count = sum(1 for msg in partner_messages if '?' in msg or any(
                word in msg.split()[:3] for word in ['what', 'when', 'where', 'how', 'why', 'can', 'do', 'is', 'are']
            ))
            
            # Determine interest level
            positive_signals = ['interested', 'sounds good', 'tell me more', 'yes', 'okay', 'great']
            negative_signals = ['not interested', 'no', 'busy', 'not now', 'expensive']
            neutral_signals = ['maybe', 'think about it', 'let me know', 'send info']
            
            positive_count = sum(1 for signal in positive_signals if signal in all_partner_text)
            negative_count = sum(1 for signal in negative_signals if signal in all_partner_text)
            neutral_count = sum(1 for signal in neutral_signals if signal in all_partner_text)
            
            if positive_count > negative_count and positive_count > 0:
                interest_level = "High - Actively engaged"
            elif negative_count > positive_count:
                interest_level = "Low - Not interested"
            elif neutral_count > 0 or questions_count > 2:
                interest_level = "Medium - Considering options"
            else:
                interest_level = "Unclear - Needs follow-up"
            
            # Determine user needs
            user_needs = []
            if any(word in all_partner_text for word in ['cost', 'fees', 'budget']):
                user_needs.append("Budget/pricing information")
            if any(word in all_partner_text for word in ['time', 'schedule', 'when']):
                user_needs.append("Scheduling details")
            if any(word in all_partner_text for word in ['curriculum', 'what', 'learn']):
                user_needs.append("Program content details")
            if any(word in all_partner_text for word in ['register', 'sign up', 'apply']):
                user_needs.append("Registration process")
            
            # Determine next steps
            outcome = self.determine_call_outcome(messages)
            if outcome == 'yes':
                next_steps = "Send program details and registration information"
            elif outcome == 'callback':
                next_steps = "Schedule follow-up call at requested time"
            elif outcome == 'no':
                next_steps = "Add to newsletter list for future opportunities"
            else:
                next_steps = "Send general information and follow up in 1 week"
            
            # Follow-up needed
            follow_up_needed = "Yes" if outcome in ['yes', 'callback', 'unsure'] else "No"
            
            return {
                'interest_level': interest_level,
                'topics_discussed': topics_discussed,
                'questions_count': questions_count,
                'user_needs': '; '.join(user_needs) if user_needs else 'General program information',
                'next_steps': next_steps,
                'follow_up_needed': follow_up_needed
            }
            
        except Exception as e:
            logger.error(f"Error analyzing conversation insights: {str(e)}")
            return {
                'interest_level': 'Unknown',
                'topics_discussed': [],
                'questions_count': 0,
                'user_needs': 'General inquiry',
                'next_steps': 'Send standard information',
                'follow_up_needed': 'Yes'
            }
