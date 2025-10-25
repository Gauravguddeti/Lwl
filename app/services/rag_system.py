"""
RAG (Retrieval-Augmented Generation) System for AI Telecaller
Provides intelligent knowledge retrieval for smarter conversations
"""

import os
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings

logger = logging.getLogger(__name__)

@dataclass
class KnowledgeDocument:
    """Represents a knowledge document in the RAG system"""
    content: str
    metadata: Dict[str, Any]
    doc_type: str  # 'school_info', 'program_details', 'faq', 'objection_handling'
    source: str
    created_at: datetime

class TelecallerRAGSystem:
    """
    RAG System for AI Telecaller providing intelligent knowledge retrieval
    """
    
    def __init__(self, persist_directory: str = "./data/rag_db"):
        self.persist_directory = persist_directory
        self.embedding_model_name = "all-MiniLM-L6-v2"
        self.embeddings = None
        self.vectorstore = None
        self.text_splitter = None
        self.embedding_model = None
        self._initialize_rag_system()
    
    def _initialize_rag_system(self):
        """Initialize the RAG system components"""
        try:
            logger.info("🔧 Initializing RAG System...")
            
            # Initialize embedding model
            self.embedding_model = SentenceTransformer(self.embedding_model_name)
            self.embeddings = SentenceTransformerEmbeddings(model_name=self.embedding_model_name)
            
            # Initialize text splitter
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
            )
            
            # Initialize vector store
            self.vectorstore = Chroma(
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory
            )
            
            logger.info("✅ RAG System initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize RAG system: {e}")
            raise
    
    def add_knowledge_documents(self, documents: List[KnowledgeDocument]):
        """Add knowledge documents to the RAG system"""
        try:
            logger.info(f"📚 Adding {len(documents)} knowledge documents...")
            
            langchain_docs = []
            for doc in documents:
                # Split document into chunks
                chunks = self.text_splitter.split_text(doc.content)
                
                for i, chunk in enumerate(chunks):
                    metadata = {
                        **doc.metadata,
                        'doc_type': doc.doc_type,
                        'source': doc.source,
                        'created_at': doc.created_at.isoformat(),
                        'chunk_id': i,
                        'total_chunks': len(chunks)
                    }
                    
                    langchain_docs.append(Document(
                        page_content=chunk,
                        metadata=metadata
                    ))
            
            # Add to vector store
            self.vectorstore.add_documents(langchain_docs)
            
            logger.info(f"✅ Added {len(langchain_docs)} document chunks to RAG system")
            
        except Exception as e:
            logger.error(f"❌ Failed to add documents: {e}")
            raise
    
    def retrieve_relevant_knowledge(self, query: str, doc_types: Optional[List[str]] = None, k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve relevant knowledge for a query"""
        try:
            logger.info(f"🔍 Retrieving knowledge for query: '{query[:100]}...'")
            
            # Build filter for document types
            filter_dict = {}
            if doc_types:
                filter_dict['doc_type'] = {'$in': doc_types}
            
            # Retrieve relevant documents
            results = self.vectorstore.similarity_search_with_score(
                query=query,
                k=k,
                filter=filter_dict if filter_dict else None
            )
            
            # Format results
            knowledge_items = []
            for doc, score in results:
                knowledge_items.append({
                    'content': doc.page_content,
                    'metadata': doc.metadata,
                    'relevance_score': score,
                    'doc_type': doc.metadata.get('doc_type', 'unknown'),
                    'source': doc.metadata.get('source', 'unknown')
                })
            
            logger.info(f"📖 Retrieved {len(knowledge_items)} relevant knowledge items")
            return knowledge_items
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve knowledge: {e}")
            return []
    
    def get_school_specific_knowledge(self, school_name: str, query: str) -> List[Dict[str, Any]]:
        """Get school-specific knowledge"""
        return self.retrieve_relevant_knowledge(
            query=f"{school_name} {query}",
            doc_types=['school_info', 'program_details'],
            k=3
        )
    
    def get_objection_handling_knowledge(self, objection_type: str) -> List[Dict[str, Any]]:
        """Get objection handling knowledge"""
        return self.retrieve_relevant_knowledge(
            query=objection_type,
            doc_types=['objection_handling'],
            k=3
        )
    
    def get_program_knowledge(self, program_name: str) -> List[Dict[str, Any]]:
        """Get program-specific knowledge"""
        return self.retrieve_relevant_knowledge(
            query=program_name,
            doc_types=['program_details', 'faq'],
            k=5
        )
    
    def populate_default_knowledge(self):
        """Populate the system with default telecaller knowledge"""
        logger.info("📚 Populating default telecaller knowledge...")
        
        default_documents = [
            # School Information
            KnowledgeDocument(
                content="""Delhi Public School (DPS) is one of India's premier educational institutions with a strong focus on academic excellence and holistic development. They have multiple branches across India and internationally. DPS schools are known for their rigorous academic programs, excellent faculty, and strong alumni network. They typically have students from grades K-12 and follow CBSE curriculum with international program options.""",
                metadata={'school_name': 'Delhi Public School', 'type': 'overview'},
                doc_type='school_info',
                source='school_database',
                created_at=datetime.now()
            ),
            
            KnowledgeDocument(
                content="""Ryan International School is a network of schools known for their innovative teaching methodologies and international outlook. They emphasize technology integration, global perspectives, and student-centered learning. Ryan schools often have partnerships with international educational institutions and offer various international curricula options alongside Indian boards.""",
                metadata={'school_name': 'Ryan International School', 'type': 'overview'},
                doc_type='school_info',
                source='school_database',
                created_at=datetime.now()
            ),
            
            # Program Details
            KnowledgeDocument(
                content="""Cambridge Summer Programme 2025 is a prestigious 2-week academic program designed for high-achieving students aged 15-18. The program offers authentic Cambridge University experience with lectures by renowned professors, interactive seminars, and cultural immersion. Students stay in historic college accommodations, participate in formal dinners, and engage with peers from around the world. The program includes subjects like Economics, Computer Science, Medicine, Law, and Engineering. Total fee is ₹4,50,000 with early bird discount of ₹50,000 available until December 31st.""",
                metadata={'program_name': 'Cambridge Summer Programme 2025', 'duration': '2 weeks', 'fee': '₹4,50,000'},
                doc_type='program_details',
                source='program_database',
                created_at=datetime.now()
            ),
            
            # FAQ
            KnowledgeDocument(
                content="""Frequently Asked Questions about International Programs:
                
Q: What is included in the program fee?
A: The fee includes accommodation in Cambridge college, all meals, academic sessions, cultural activities, airport transfers, and comprehensive insurance.

Q: Are there scholarship opportunities?
A: Yes, we offer merit-based scholarships of up to 25% for exceptional students. We also have need-based financial assistance available.

Q: What is the application process?
A: Students need to submit academic transcripts, English proficiency proof, a personal statement, and teacher recommendations. The process typically takes 2-3 weeks.

Q: Is this program recognized by universities?
A: Yes, participants receive a Cambridge University certificate that is highly regarded by universities worldwide for admissions.""",
                metadata={'category': 'general_faq'},
                doc_type='faq',
                source='faq_database',
                created_at=datetime.now()
            ),
            
            # Objection Handling
            KnowledgeDocument(
                content="""Budget Objection Handling:

When schools express budget concerns:
1. Acknowledge the concern: "I completely understand that budget is an important consideration for any school."
2. Emphasize ROI: "Many schools find that the long-term benefits - increased university acceptances, student confidence, global perspectives - provide excellent return on investment."
3. Offer payment plans: "We offer flexible payment options including 3-month installment plans to help manage cash flow."
4. Highlight scholarships: "We also have partial scholarships available for deserving students, which can reduce the overall cost."
5. Compare value: "When you consider this is a 2-week Cambridge University experience with accommodation, meals, and expert instruction, the cost per day is very reasonable."
6. Success stories: "Schools like [similar school] saw 40% increase in international university applications after sending students to our program."
""",
                metadata={'objection_type': 'budget', 'category': 'cost_concerns'},
                doc_type='objection_handling',
                source='sales_training',
                created_at=datetime.now()
            ),
            
            KnowledgeDocument(
                content="""Timing Objection Handling:

When schools say it's not the right time:
1. Understand their timing: "I understand timing is crucial. Can you help me understand what would be better timing for your school?"
2. Flexibility: "We have multiple program dates throughout the year - summer, winter, and spring break options."
3. Planning advantage: "Many schools prefer to plan 6-12 months ahead to integrate this into their curriculum and budget planning."
4. Early bird benefits: "Booking early gives you access to our early bird discounts and preferred accommodation options."
5. Academic calendar: "We can work with your academic calendar to find dates that don't interfere with important school events."
6. Start small: "We could begin with a smaller group of 5-10 students this time and expand in future years."
""",
                metadata={'objection_type': 'timing', 'category': 'scheduling_concerns'},
                doc_type='objection_handling',
                source='sales_training',
                created_at=datetime.now()
            )
        ]
        
        self.add_knowledge_documents(default_documents)
        logger.info("✅ Default knowledge populated successfully")

def test_rag_system():
    """Test the RAG system functionality"""
    print("🧪 Testing RAG System")
    print("=" * 50)
    
    # Initialize RAG system
    rag = TelecallerRAGSystem()
    
    # Populate with default knowledge
    rag.populate_default_knowledge()
    
    # Test queries
    test_queries = [
        "What can you tell me about Delhi Public School?",
        "How much does the Cambridge program cost?",
        "What should I say if they say it's too expensive?",
        "What is included in the program fee?",
        "Tell me about Ryan International School"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: {query}")
        print("-" * 30)
        
        results = rag.retrieve_relevant_knowledge(query, k=2)
        
        for i, result in enumerate(results, 1):
            print(f"Result {i}:")
            print(f"Content: {result['content'][:200]}...")
            print(f"Type: {result['doc_type']}")
            print(f"Score: {result['relevance_score']:.4f}")
            print()
    
    print("✅ RAG System test completed!")
    return True

if __name__ == "__main__":
    test_rag_system()
