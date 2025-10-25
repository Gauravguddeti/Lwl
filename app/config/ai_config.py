"""
AI Configuration for LangGraph and RAG Integration
"""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class AIConfig:
    """Configuration for AI components"""
    
    # OpenAI Configuration
    OPENAI_API_KEY: Optional[str] = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_TEMPERATURE: float = 0.7
    OPENAI_MAX_TOKENS: int = 1000
    
    # RAG Configuration
    RAG_EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    RAG_CHUNK_SIZE: int = 1000
    RAG_CHUNK_OVERLAP: int = 200
    RAG_SIMILARITY_THRESHOLD: float = 0.7
    RAG_MAX_RESULTS: int = 5
    RAG_PERSIST_DIRECTORY: str = "./data/rag_db"
    
    # LangGraph Configuration
    CONVERSATION_MAX_STEPS: int = 20
    OBJECTION_DETECTION_KEYWORDS: list = [
        'expensive', 'budget', 'cost', 'money', 'afford', 'price',
        'busy', 'time', 'schedule', 'timing', 'not now',
        'not interested', 'no thanks', 'already have'
    ]
    INTEREST_KEYWORDS: list = [
        'interested', 'sounds good', 'tell me more', 'yes', 'great',
        'perfect', 'excellent', 'wonderful', 'impressive'
    ]
    
    # Voice Configuration for AI Calls
    VOICE_SETTINGS: Dict[str, Any] = {
        'voice': 'alice',
        'language': 'en-IN',
        'speech_rate': '1.0',
        'speech_pitch': '0',
        'ai_enhanced': True
    }
    
    # Conversation Quality Scoring
    QUALITY_SCORING: Dict[str, int] = {
        'message_exchange_weight': 30,
        'objection_handling_weight': 25,
        'interest_generation_weight': 25,
        'knowledge_utilization_weight': 20
    }

    @classmethod
    def get_ai_config(cls) -> Dict[str, Any]:
        """Get complete AI configuration"""
        return {
            'openai': {
                'api_key': cls.OPENAI_API_KEY,
                'model': cls.OPENAI_MODEL,
                'temperature': cls.OPENAI_TEMPERATURE,
                'max_tokens': cls.OPENAI_MAX_TOKENS
            },
            'rag': {
                'embedding_model': cls.RAG_EMBEDDING_MODEL,
                'chunk_size': cls.RAG_CHUNK_SIZE,
                'chunk_overlap': cls.RAG_CHUNK_OVERLAP,
                'similarity_threshold': cls.RAG_SIMILARITY_THRESHOLD,
                'max_results': cls.RAG_MAX_RESULTS,
                'persist_directory': cls.RAG_PERSIST_DIRECTORY
            },
            'langgraph': {
                'max_steps': cls.CONVERSATION_MAX_STEPS,
                'objection_keywords': cls.OBJECTION_DETECTION_KEYWORDS,
                'interest_keywords': cls.INTEREST_KEYWORDS
            },
            'voice': cls.VOICE_SETTINGS,
            'quality_scoring': cls.QUALITY_SCORING
        }
    
    @classmethod
    def is_ai_enabled(cls) -> bool:
        """Check if AI features are enabled"""
        return cls.OPENAI_API_KEY is not None
    
    @classmethod
    def validate_config(cls) -> Dict[str, bool]:
        """Validate AI configuration"""
        validation = {
            'openai_configured': cls.OPENAI_API_KEY is not None,
            'rag_directory_exists': os.path.exists(os.path.dirname(cls.RAG_PERSIST_DIRECTORY)),
            'embedding_model_valid': len(cls.RAG_EMBEDDING_MODEL) > 0,
            'conversation_settings_valid': cls.CONVERSATION_MAX_STEPS > 0
        }
        
        return validation
