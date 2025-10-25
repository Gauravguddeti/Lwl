"""
RAG Service for AI Telecaller System
Retrieves relevant information about partners, events, and conversation context
"""

import logging
import os
from typing import List, Dict, Any
import chromadb
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import JSONLoader
from app.services.database_service import DatabaseService

logger = logging.getLogger(__name__)

class RAGService:
    """Retrieval-Augmented Generation service for context-aware conversations"""
    
    def __init__(self, openai_api_key: str):
        self.openai_api_key = openai_api_key
        self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        self.db_service = DatabaseService()
        self.vector_store = None
        self.initialize_vector_store()
    
    def initialize_vector_store(self):
        """Initialize vector store with partner and event data"""
        try:
            # Create ChromaDB persistent directory
            persist_directory = "./rag_db"
            os.makedirs(persist_directory, exist_ok=True)
            
            # Initialize vector store
            self.vector_store = Chroma(
                persist_directory=persist_directory,
                embedding_function=self.embeddings
            )
            
            # Load and index data if vector store is empty
            if self.vector_store._collection.count() == 0:
                self.index_partner_data()
                
            logger.info("✅ RAG vector store initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize vector store: {e}")
    
    def index_partner_data(self):
        """Index partner and event data for retrieval"""
        try:
            # Get partners and events from database
            partners = self.db_service.get_all_partners()
            events = self.db_service.get_all_events()
            
            documents = []
            
            # Process partner data
            for partner in partners or []:
                partner_text = f"""
                Partner: {partner.get('name', 'Unknown')}
                Organization: {partner.get('organization', 'Unknown')}
                Phone: {partner.get('phone', 'Unknown')}
                Email: {partner.get('email', 'Unknown')}
                Event: {partner.get('event_name', 'No Event')}
                Event Date: {partner.get('event_date', 'Unknown')}
                Details: {partner.get('details', 'No additional details')}
                """
                
                documents.append({
                    'page_content': partner_text,
                    'metadata': {
                        'type': 'partner',
                        'partner_id': partner.get('id'),
                        'name': partner.get('name'),
                        'phone': partner.get('phone'),
                        'event_id': partner.get('event_id')
                    }
                })
            
            # Process event data
            for event in events or []:
                event_text = f"""
                Event: {event.get('name', 'Unknown Event')}
                Date: {event.get('date', 'Unknown Date')}
                Time: {event.get('time', 'Unknown Time')}
                Location: {event.get('location', 'Unknown Location')}
                Description: {event.get('description', 'No description')}
                Type: {event.get('type', 'Unknown Type')}
                """
                
                documents.append({
                    'page_content': event_text,
                    'metadata': {
                        'type': 'event',
                        'event_id': event.get('id'),
                        'name': event.get('name'),
                        'date': event.get('date')
                    }
                })
            
            # Add conversation templates
            conversation_templates = [
                {
                    'page_content': "Greeting: Hello! This is Global Learning Academy. We're calling about your upcoming event. How are you today?",
                    'metadata': {'type': 'template', 'category': 'greeting'}
                },
                {
                    'page_content': "Event Reminder: We wanted to remind you about the upcoming event. Do you have any questions about the schedule or location?",
                    'metadata': {'type': 'template', 'category': 'reminder'}
                },
                {
                    'page_content': "Follow-up: Thank you for your interest in our programs. Would you like to discuss enrollment or have any specific questions?",
                    'metadata': {'type': 'template', 'category': 'follow_up'}
                }
            ]
            
            documents.extend(conversation_templates)
            
            # Split documents and add to vector store
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50
            )
            
            texts = []
            metadatas = []
            
            for doc in documents:
                chunks = text_splitter.split_text(doc['page_content'])
                for chunk in chunks:
                    texts.append(chunk)
                    metadatas.append(doc['metadata'])
            
            # Add to vector store
            self.vector_store.add_texts(texts=texts, metadatas=metadatas)
            
            logger.info(f"✅ Indexed {len(documents)} documents with {len(texts)} chunks")
            
        except Exception as e:
            logger.error(f"❌ Failed to index partner data: {e}")
    
    def get_relevant_context(self, query: str, phone_number: str = None, k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve relevant context for a query"""
        try:
            if not self.vector_store:
                return []
            
            # Enhance query with phone number if provided
            enhanced_query = query
            if phone_number:
                enhanced_query = f"Phone: {phone_number} {query}"
            
            # Search vector store
            docs = self.vector_store.similarity_search(
                enhanced_query, 
                k=k
            )
            
            # Format results
            context = []
            for doc in docs:
                context.append({
                    'content': doc.page_content,
                    'metadata': doc.metadata,
                    'relevance': 'high'  # Could add scoring here
                })
            
            return context
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve context: {e}")
            return []
    
    def get_partner_by_phone(self, phone_number: str) -> Dict[str, Any]:
        """Get specific partner information by phone number"""
        try:
            if not self.vector_store:
                return {}
            
            # Search for partner with specific phone number
            docs = self.vector_store.similarity_search(
                f"Phone: {phone_number}",
                k=3,
                filter={'type': 'partner'}
            )
            
            for doc in docs:
                if phone_number in doc.page_content:
                    return doc.metadata
            
            return {}
            
        except Exception as e:
            logger.error(f"❌ Failed to get partner by phone: {e}")
            return {}
    
    def update_partner_data(self):
        """Refresh vector store with latest partner data"""
        try:
            # Clear existing data
            if self.vector_store:
                self.vector_store.delete_collection()
            
            # Reinitialize and reindex
            self.initialize_vector_store()
            
            logger.info("✅ Partner data updated in vector store")
            
        except Exception as e:
            logger.error(f"❌ Failed to update partner data: {e}")
    
    def get_conversation_suggestions(self, context: str, phone_number: str = None) -> List[str]:
        """Get conversation suggestions based on context"""
        try:
            # Get relevant context
            relevant_docs = self.get_relevant_context(
                f"conversation {context}", 
                phone_number, 
                k=3
            )
            
            suggestions = []
            for doc in relevant_docs:
                if doc['metadata'].get('type') == 'template':
                    suggestions.append(doc['content'])
            
            # Default suggestions if none found
            if not suggestions:
                suggestions = [
                    "Hello! This is Global Learning Academy calling about your upcoming event.",
                    "Hi there! We wanted to follow up on your inquiry about our programs.",
                    "Good day! This is regarding your enrollment with our academy."
                ]
            
            return suggestions[:3]  # Return top 3 suggestions
            
        except Exception as e:
            logger.error(f"❌ Failed to get conversation suggestions: {e}")
            return ["Hello! This is Global Learning Academy. How can I help you today?"]
