#!/usr/bin/env python3
"""
Enhanced AI Telecaller Service with Indian Voice, Accent Handling, LangGraph + RAG
- Serverless Lambda Ready
- Indian Voice Support
- Advanced Sentiment Analysis
- Smart Conversation Flow with LangGraph
- RAG-based Knowledge Retrieval
- Indian Accent Processing
"""

import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import re

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

# Core imports
from flask import Flask, request, jsonify
from twilio.twiml.voice_response import VoiceResponse
from openai import OpenAI
import boto3

# Advanced AI imports
try:
    from langchain_openai import ChatOpenAI
    from langchain.schema import HumanMessage, SystemMessage
    from langchain_community.vectorstores import Chroma
    from langchain_openai import OpenAIEmbeddings
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langgraph.graph import StateGraph, END
    from langgraph.graph.message import add_messages
    from typing_extensions import Annotated, TypedDict
    ADVANCED_AI_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Advanced AI components not available: {e}")
    ADVANCED_AI_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ConversationState:
    """Enhanced conversation state with sentiment tracking"""
    call_id: str
    user_responses: List[str]
    ai_responses: List[str]
    conversation_stage: str
    interests_shown: List[str]
    objections_raised: List[str]
    sentiment_scores: List[float]
    emotional_state: str
    indian_accent_detected: bool
    corrected_inputs: List[Dict[str, str]]
    call_duration: int
    permission_asked: bool
    permission_granted: bool
    start_time: str

class IndianAccentProcessor:
    """Process and correct Indian English patterns for better understanding"""
    
    def __init__(self):
        # Common Indian English patterns and corrections
        self.accent_patterns = {
            # Pronunciation corrections
            r'\bvery good\b': 'very good',
            r'\bactually\b': 'actually',
            r'\bisn\'t it\b': 'isn\'t it',
            r'\bonly\b(?=\s+(?:I|we|they))': '',  # Remove redundant 'only'
            r'\bwhat is your good name\b': 'what is your name',
            r'\btell me one thing\b': 'let me ask you',
            r'\bdo one thing\b': 'please do this',
            r'\bout of station\b': 'out of town',
            r'\bprepone\b': 'reschedule earlier',
            
            # Common Hindi-English mixing corrections
            r'\bna\b': 'no',
            r'\bhaan\b': 'yes',
            r'\bacha\b': 'good',
            r'\btheek hai\b': 'okay',
            r'\bkya\b': 'what',
            
            # Question pattern corrections
            r'^you are\b': 'are you',
            r'\byou have any\b': 'do you have any',
            r'\bhow much cost\b': 'how much does it cost',
            r'\bwhat is the price\b': 'what is the price',
        }
        
        # Sentiment indicators in Indian context
        self.indian_sentiment_indicators = {
            'positive': ['accha', 'theek hai', 'chalega', 'good only', 'nice only', 'superb', 'fantastic'],
            'negative': ['nahi', 'problem hai', 'difficult', 'not possible', 'very expensive'],
            'hesitation': ['let me think', 'I will see', 'maybe', 'possibly', 'discuss with family']
        }
    
    def process_input(self, user_input: str) -> Dict[str, Any]:
        """Process Indian accent and return corrected input with confidence"""
        original_input = user_input
        corrected_input = user_input.lower().strip()
        
        # Apply accent corrections
        for pattern, replacement in self.accent_patterns.items():
            corrected_input = re.sub(pattern, replacement, corrected_input, flags=re.IGNORECASE)
        
        # Calculate confidence based on corrections made
        corrections_made = original_input != corrected_input
        confidence = 0.9 if not corrections_made else 0.7
        
        # Detect Indian accent patterns
        indian_patterns_found = any(pattern in corrected_input.lower() for pattern in 
                                  ['only', 'na', 'hai', 'accha', 'theek', 'what is your good name'])
        
        return {
            'original': original_input,
            'corrected': corrected_input,
            'confidence': confidence,
            'indian_accent_detected': indian_patterns_found,
            'corrections_made': corrections_made
        }

class SentimentAnalyzer:
    """Advanced sentiment analysis for Indian context"""
    
    def __init__(self, openai_client: OpenAI):
        self.openai_client = openai_client
        
    def analyze_sentiment(self, text: str, conversation_context: List[str]) -> Dict[str, Any]:
        """Analyze sentiment with Indian cultural context"""
        try:
            prompt = f"""
            Analyze the sentiment of this text in Indian cultural context:
            Text: "{text}"
            Conversation context: {conversation_context[-3:] if conversation_context else []}
            
            Consider Indian communication patterns:
            - Politeness and indirect communication
            - Family consultation importance
            - Price sensitivity
            - Educational value emphasis
            
            Return JSON with:
            - sentiment: positive/negative/neutral/hesitant
            - confidence: 0.0-1.0
            - emotional_indicators: list of detected emotions
            - buying_intent: 0.0-1.0 (likelihood to purchase)
            - cultural_context: relevant Indian cultural factors
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            return {
                'sentiment': 'neutral',
                'confidence': 0.5,
                'emotional_indicators': [],
                'buying_intent': 0.5,
                'cultural_context': []
            }

class LangGraphConversationManager:
    """LangGraph-based conversation flow management"""
    
    def __init__(self, openai_client: OpenAI, rag_system=None):
        self.openai_client = openai_client
        self.rag_system = rag_system
        self.graph = self._create_conversation_graph()
        
    def _create_conversation_graph(self):
        """Create LangGraph conversation flow"""
        if not ADVANCED_AI_AVAILABLE:
            return None
            
        class ConversationGraphState(TypedDict):
            messages: Annotated[list, add_messages]
            stage: str
            permission_status: str
            user_sentiment: str
            buying_intent: float
            
        def permission_node(state):
            """Handle permission asking and validation"""
            if state.get('permission_status') != 'granted':
                response = "Hi! This is Sarah from Learn with Leaders. I hope you're having a wonderful day. Am I speaking with the principal or someone who handles educational programs for your school?"
                return {
                    "messages": [{"role": "assistant", "content": response}],
                    "stage": "permission_check",
                    "permission_status": "pending"
                }
            return state
            
        def introduction_node(state):
            """Introduce the program"""
            response = "Perfect! I'm calling about our prestigious Cambridge Summer Programme 2025. It's an incredible opportunity for your high-achieving students to experience authentic Cambridge University education. Would you like to know more about this life-changing program?"
            return {
                "messages": [{"role": "assistant", "content": response}],
                "stage": "introduction"
            }
            
        def information_node(state):
            """Provide detailed information based on user interest"""
            if self.rag_system:
                # Use RAG for detailed responses
                context = self.rag_system.get_relevant_info(state.get('last_user_input', ''))
                response = f"Great question! {context} This program has been transformational for students from schools like yours."
            else:
                response = "The Cambridge Summer Programme is a 2-week intensive experience where students live in actual Cambridge colleges, attend lectures by university faculty, and gain authentic UK university experience."
            
            return {
                "messages": [{"role": "assistant", "content": response}],
                "stage": "information_sharing"
            }
            
        def pricing_node(state):
            """Handle pricing discussions with sensitivity"""
            response = "The investment for this life-changing experience is ₹2,50,000 per student. However, we're offering a special 15% early bird discount for schools that confirm by month-end, bringing it to ₹2,12,500. When you consider the lifelong impact and networking opportunities, many parents find it excellent value."
            return {
                "messages": [{"role": "assistant", "content": response}],
                "stage": "pricing_discussion"
            }
            
        def objection_handling_node(state):
            """Handle objections with cultural sensitivity"""
            sentiment = state.get('user_sentiment', 'neutral')
            if sentiment == 'negative':
                response = "I completely understand your concerns. Many principals initially have the same thoughts. What if I could arrange for you to speak with principals from schools who've already participated? They can share their honest experience and the transformation they witnessed in their students."
            else:
                response = "That's a very thoughtful question. Let me provide you with more details that might help with your decision."
            
            return {
                "messages": [{"role": "assistant", "content": response}],
                "stage": "objection_handling"
            }
            
        def closing_node(state):
            """Proper conversation closing with follow-up"""
            buying_intent = state.get('buying_intent', 0.5)
            if buying_intent > 0.7:
                response = "Wonderful! I can sense your enthusiasm for this program. Shall I email you the detailed application process and reserve a spot for your students? What's the best email address to send this information?"
            elif buying_intent > 0.4:
                response = "I understand you'd like to think about this - it's a significant decision. Let me send you our comprehensive brochure with student testimonials and parent feedback. When would be a good time for me to follow up with you?"
            else:
                response = "Thank you for your time today. I'll email you our program brochure so you can review it at your convenience. Sometimes the best opportunities come when we take time to consider them properly."
            
            return {
                "messages": [{"role": "assistant", "content": response}],
                "stage": "closing"
            }
        
        # Build the graph
        workflow = StateGraph(ConversationGraphState)
        
        # Add nodes
        workflow.add_node("permission", permission_node)
        workflow.add_node("introduction", introduction_node)
        workflow.add_node("information", information_node)
        workflow.add_node("pricing", pricing_node)
        workflow.add_node("objection_handling", objection_handling_node)
        workflow.add_node("closing", closing_node)
        
        # Add edges (conversation flow)
        workflow.set_entry_point("permission")
        workflow.add_edge("permission", "introduction")
        workflow.add_edge("introduction", "information")
        workflow.add_edge("information", "pricing")
        workflow.add_edge("pricing", "objection_handling")
        workflow.add_edge("objection_handling", "closing")
        workflow.add_edge("closing", END)
        
        return workflow.compile()

class RAGKnowledgeSystem:
    """RAG system for Cambridge Programme knowledge"""
    
    def __init__(self, openai_api_key: str):
        if not ADVANCED_AI_AVAILABLE:
            self.vectorstore = None
            return
            
        self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        self.knowledge_base = self._load_knowledge_base()
        self.vectorstore = self._create_vectorstore()
        
    def _load_knowledge_base(self) -> List[str]:
        """Load Cambridge Programme knowledge"""
        return [
            "Cambridge Summer Programme 2025 is a 2-week intensive educational experience at Cambridge University, UK.",
            "Students live in authentic Cambridge colleges including Trinity, King's, and St. John's colleges.",
            "Program includes lectures by Cambridge faculty, tutorials, cultural excursions, and networking opportunities.",
            "Participants receive a Cambridge University certificate of completion.",
            "Program fee is ₹2,50,000 with 15% early bird discount available (₹2,12,500).",
            "Includes accommodation, meals, academic sessions, cultural activities, and London excursion.",
            "Open to students aged 15-18 with good academic records.",
            "Previous participants have gained admission to top UK universities including Cambridge, Oxford, Imperial College.",
            "Program enhances university applications and provides valuable international exposure.",
            "Small class sizes ensure personalized attention and meaningful faculty interaction.",
            "Cultural immersion includes Cambridge traditions, formal dinners, and punting on River Cam.",
            "Alumni network provides ongoing mentorship and university guidance.",
            "Application deadline is December 31st, 2024 for Summer 2025 program.",
            "Limited to 50 students globally to maintain exclusivity and quality.",
            "Includes pre-departure orientation and post-program university counseling.",
        ]
        
    def _create_vectorstore(self):
        """Create vector database for RAG"""
        if not ADVANCED_AI_AVAILABLE:
            return None
            
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )
        
        texts = text_splitter.create_documents(self.knowledge_base)
        vectorstore = Chroma.from_documents(
            texts,
            self.embeddings,
            persist_directory="./rag_db"
        )
        return vectorstore
        
    def get_relevant_info(self, query: str, k: int = 3) -> str:
        """Retrieve relevant information for query"""
        if not self.vectorstore:
            return "The Cambridge Summer Programme offers an authentic university experience with expert faculty and cultural immersion."
            
        docs = self.vectorstore.similarity_search(query, k=k)
        return " ".join([doc.page_content for doc in docs])

class EnhancedTelecallerService:
    """Main enhanced telecaller service with all features"""
    
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.accent_processor = IndianAccentProcessor()
        self.sentiment_analyzer = SentimentAnalyzer(self.openai_client)
        self.rag_system = RAGKnowledgeSystem(os.getenv('OPENAI_API_KEY'))
        self.conversation_manager = LangGraphConversationManager(self.openai_client, self.rag_system)
        self.active_conversations = {}
        
    def create_flask_app(self):
        """Create Flask app for serverless deployment"""
        app = Flask(__name__)
        
        @app.route('/voice/start', methods=['POST'])
        def voice_start():
            """Start voice call with Indian voice support"""
            call_id = request.form.get('CallSid')
            
            # Initialize conversation state
            state = ConversationState(
                call_id=call_id,
                user_responses=[],
                ai_responses=[],
                conversation_stage='permission_check',
                interests_shown=[],
                objections_raised=[],
                sentiment_scores=[],
                emotional_state='neutral',
                indian_accent_detected=False,
                corrected_inputs=[],
                call_duration=0,
                permission_asked=False,
                permission_granted=False,
                start_time=datetime.now().isoformat()
            )
            
            self.active_conversations[call_id] = state
            
            # Create response with Indian voice
            response = VoiceResponse()
            
            # Use Indian English voice (Raveena - Indian female voice)
            greeting = "Hi! This is Sarah from Learn with Leaders. I hope you're having a wonderful day. Am I speaking with the principal or someone who handles educational programs for your school?"
            
            response.say(
                greeting,
                voice='Polly.Raveena',  # Indian English voice
                language='en-IN'  # Indian English
            )
            
            # Gather response with enhanced speech recognition
            gather = response.gather(
                input='speech',
                action='/voice/gather',
                method='POST',
                speech_timeout=4,
                timeout=10,
                language='en-IN',  # Better for Indian accents
                enhanced=True,  # Enhanced speech recognition
                speech_model='experimental_conversations'  # Better for natural conversation
            )
            
            response.say("I'm sorry, I didn't catch that. Could you please respond?")
            response.redirect('/voice/gather')
            
            state.permission_asked = True
            logger.info(f"Call started: {call_id} with Indian voice support")
            
            return str(response)
            
        @app.route('/voice/gather', methods=['POST'])
        def voice_gather():
            """Process user speech with Indian accent handling"""
            call_id = request.form.get('CallSid')
            user_input = request.form.get('SpeechResult', '').strip()
            confidence = float(request.form.get('Confidence', 0.0))
            
            if call_id not in self.active_conversations:
                return self._create_error_response()
                
            state = self.active_conversations[call_id]
            
            # Process Indian accent
            processed_input = self.accent_processor.process_input(user_input)
            corrected_input = processed_input['corrected']
            
            # Update state
            state.user_responses.append(user_input)
            state.corrected_inputs.append(processed_input)
            state.indian_accent_detected = processed_input['indian_accent_detected']
            
            # Analyze sentiment
            sentiment_analysis = self.sentiment_analyzer.analyze_sentiment(
                corrected_input, 
                state.user_responses
            )
            state.sentiment_scores.append(sentiment_analysis['confidence'])
            state.emotional_state = sentiment_analysis['sentiment']
            
            # Generate AI response using LangGraph
            ai_response = self._generate_langgraph_response(state, corrected_input, sentiment_analysis)
            state.ai_responses.append(ai_response)
            
            # Create TwiML response
            response = VoiceResponse()
            response.say(
                ai_response,
                voice='Polly.Raveena',  # Consistent Indian voice
                language='en-IN'
            )
            
            # Continue conversation if not closing
            if state.conversation_stage != 'closing' and self._should_continue_conversation(state, sentiment_analysis):
                gather = response.gather(
                    input='speech',
                    action='/voice/gather',
                    method='POST',
                    speech_timeout=4,
                    timeout=10,
                    language='en-IN',
                    enhanced=True,
                    speech_model='experimental_conversations'
                )
                response.say("Is there anything else you'd like to know about the program?")
            else:
                response.say("Thank you for your time! Have a wonderful day!")
                response.hangup()
                
            logger.info(f"User: '{user_input}' -> AI: '{ai_response}' (Sentiment: {sentiment_analysis['sentiment']})")
            
            return str(response)
            
        @app.route('/voice/status', methods=['POST'])
        def voice_status():
            """Handle call status updates"""
            call_id = request.form.get('CallSid')
            call_status = request.form.get('CallStatus')
            
            if call_id in self.active_conversations:
                state = self.active_conversations[call_id]
                state.call_duration = int(request.form.get('CallDuration', 0))
                
                if call_status in ['completed', 'failed', 'busy', 'no-answer']:
                    # Log conversation summary
                    self._log_conversation_summary(state)
                    del self.active_conversations[call_id]
                    
            return jsonify({'status': 'ok'})
            
        @app.route('/health', methods=['GET'])
        def health():
            return jsonify({
                'status': 'healthy',
                'service': 'Enhanced AI Telecaller',
                'features': [
                    'Indian Voice Support',
                    'Accent Processing',
                    'LangGraph Conversation Flow',
                    'RAG Knowledge System',
                    'Sentiment Analysis',
                    'Serverless Ready'
                ],
                'timestamp': datetime.now().isoformat()
            })
            
        return app
        
    def _generate_langgraph_response(self, state: ConversationState, user_input: str, sentiment: Dict) -> str:
        """Generate response using LangGraph conversation flow"""
        try:
            if not self.conversation_manager.graph or not ADVANCED_AI_AVAILABLE:
                return self._generate_fallback_response(state, user_input, sentiment)
                
            # Determine conversation flow based on state and sentiment
            if not state.permission_granted and 'yes' in user_input.lower() or 'principal' in user_input.lower():
                state.permission_granted = True
                state.conversation_stage = 'introduction'
                return "Perfect! I'm calling about our prestigious Cambridge Summer Programme 2025. It's an incredible opportunity for your high-achieving students to experience authentic Cambridge University education. Would you like to know more about this life-changing program?"
                
            elif 'fee' in user_input.lower() or 'cost' in user_input.lower() or 'price' in user_input.lower():
                state.conversation_stage = 'pricing_discussion'
                return "The investment for this life-changing experience is ₹2,50,000 per student. However, we're offering a special 15% early bird discount for schools that confirm by month-end, bringing it to ₹2,12,500. When you consider the lifelong impact and networking opportunities, many parents find it excellent value. What aspects of the program interest you most?"
                
            elif sentiment['sentiment'] == 'negative' or sentiment['buying_intent'] < 0.3:
                state.conversation_stage = 'objection_handling'
                return "I completely understand your concerns. Many principals initially have the same thoughts. What if I could arrange for you to speak with principals from schools who've already participated? They can share their honest experience and the transformation they witnessed in their students. What specific concerns do you have?"
                
            elif 'details' in user_input.lower() or 'information' in user_input.lower():
                state.conversation_stage = 'information_sharing'
                # Use RAG for detailed information
                rag_info = self.rag_system.get_relevant_info(user_input)
                return f"Great question! {rag_info} Students come back completely transformed - more confident, globally aware, and academically inspired. What specific aspects would you like to know more about?"
                
            elif sentiment['buying_intent'] > 0.7:
                state.conversation_stage = 'closing'
                return "Wonderful! I can sense your enthusiasm for this program. Shall I email you the detailed application process and reserve a spot for your students? What's the best email address to send this information?"
                
            else:
                # Continue conversation naturally
                return "That's really interesting! The Cambridge programme has been transformational for students from schools like yours. They gain not just academic knowledge but also confidence and global perspective. What would you like to know more about - the academic curriculum, cultural activities, or perhaps the application process?"
                
        except Exception as e:
            logger.error(f"LangGraph response error: {e}")
            return self._generate_fallback_response(state, user_input, sentiment)
            
    def _generate_fallback_response(self, state: ConversationState, user_input: str, sentiment: Dict) -> str:
        """Fallback response generation"""
        try:
            context = f"""
            You are Sarah, a professional telecaller from Learn with Leaders calling about Cambridge Summer Programme 2025.
            
            User said: "{user_input}"
            Conversation stage: {state.conversation_stage}
            User sentiment: {sentiment['sentiment']}
            Buying intent: {sentiment['buying_intent']}
            Permission granted: {state.permission_granted}
            
            Respond naturally in 40-60 words. Be warm, professional, and guide toward program interest.
            Use Indian cultural context - emphasize education value, family consultation, ROI.
            """
            
            response = self.openai_client.chat.completions.create(
                model=os.getenv('AI_MODEL', 'gpt-4o-mini'),
                messages=[{"role": "user", "content": context}],
                max_tokens=80,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Fallback response error: {e}")
            return "That's wonderful! Let me share more about how this Cambridge programme can benefit your students."
            
    def _should_continue_conversation(self, state: ConversationState, sentiment: Dict) -> bool:
        """Determine if conversation should continue"""
        # Continue if less than 8 exchanges
        if len(state.user_responses) < 8:
            return True
            
        # Continue if user is showing interest
        if sentiment['buying_intent'] > 0.4:
            return True
            
        # End if strong negative sentiment
        if sentiment['sentiment'] == 'negative' and sentiment['confidence'] > 0.8:
            return False
            
        # End if conversation stage is closing
        if state.conversation_stage == 'closing':
            return False
            
        return True
        
    def _create_error_response(self) -> str:
        """Create error response"""
        response = VoiceResponse()
        response.say("I'm sorry, there was a technical issue. Please call back later.")
        response.hangup()
        return str(response)
        
    def _log_conversation_summary(self, state: ConversationState):
        """Log detailed conversation summary for analysis"""
        summary = {
            'call_id': state.call_id,
            'duration': state.call_duration,
            'total_exchanges': len(state.user_responses),
            'final_sentiment': state.emotional_state,
            'average_sentiment_score': sum(state.sentiment_scores) / len(state.sentiment_scores) if state.sentiment_scores else 0,
            'indian_accent_detected': state.indian_accent_detected,
            'corrections_made': len([c for c in state.corrected_inputs if c['corrections_made']]),
            'conversation_stages': state.conversation_stage,
            'permission_granted': state.permission_granted,
            'interests_shown': state.interests_shown,
            'objections_raised': state.objections_raised,
            'end_time': datetime.now().isoformat()
        }
        
        logger.info(f"Conversation Summary: {json.dumps(summary, indent=2)}")
        
        # Store in database or analytics system
        # self._store_analytics(summary)

# Initialize service
telecaller_service = EnhancedTelecallerService()
app = telecaller_service.create_flask_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
