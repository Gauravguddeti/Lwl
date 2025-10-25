"""
LangGraph-based AI Telecaller Service with RAG and Tool Calling
Uses GPT-4 mini with dynamic tool calling and knowledge retrieval
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, TypedDict, Annotated
from pathlib import Path

# LangGraph imports
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.tools import tool
from langchain_core.documents import Document

# Local imports
from app.database.postgres_models import telecaller_db, pg_manager
from app.services.twilio_service import TwilioService
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConversationState(TypedDict):
    """State for conversation flow"""
    messages: Annotated[List, "Messages in conversation"]
    call_context: Dict[str, Any]
    current_step: str
    tools_used: List[str]
    program_info: Optional[Dict[str, Any]]
    partner_info: Optional[Dict[str, Any]]
    call_outcome: Optional[str]
    follow_up_required: bool
    recording_path: Optional[str]
    transcription_path: Optional[str]

class LangGraphTelecallerService:
    """AI Telecaller Service using LangGraph orchestration"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model_name=os.getenv('AI_MODEL', 'gpt-4o-mini'),
            temperature=float(os.getenv('AI_TEMPERATURE', '0.7')),
            max_tokens=int(os.getenv('AI_MAX_TOKENS', '1500'))
        )
        
        # Initialize services
        self.twilio_service = TwilioService()
        self.embeddings = OpenAIEmbeddings()
        
        # Setup RAG
        self.vector_store = self._setup_rag_database()
        
        # Setup LangGraph
        self.workflow = self._create_workflow()
        self.checkpointer = MemorySaver()
        self.app = self.workflow.compile(checkpointer=self.checkpointer)
        
        # Setup local storage paths
        self.setup_local_storage()
        
        logger.info("LangGraph AI Telecaller Service initialized")
    
    def setup_local_storage(self):
        """Setup local directories for call recordings and transcriptions"""
        self.recordings_path = Path(os.getenv('CALL_RECORDINGS_PATH', './call_recordings'))
        self.transcriptions_path = Path(os.getenv('CALL_TRANSCRIPTIONS_PATH', './call_transcriptions'))
        
        # Create directories if they don't exist
        self.recordings_path.mkdir(exist_ok=True)
        self.transcriptions_path.mkdir(exist_ok=True)
        
        logger.info(f"Local storage setup - Recordings: {self.recordings_path}, Transcriptions: {self.transcriptions_path}")
    
    def _setup_rag_database(self) -> Chroma:
        """Setup RAG vector database with program and educational content"""
        persist_directory = os.getenv('RAG_PERSIST_DIRECTORY', './rag_db')
        
        # Create educational content documents
        documents = self._create_knowledge_documents()
        
        # Split documents
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=int(os.getenv('RAG_CHUNK_SIZE', '1000')),
            chunk_overlap=int(os.getenv('RAG_CHUNK_OVERLAP', '200'))
        )
        
        splits = text_splitter.split_documents(documents)
        
        # Create vector store
        vector_store = Chroma.from_documents(
            documents=splits,
            embedding=self.embeddings,
            persist_directory=persist_directory
        )
        
        logger.info(f"RAG database setup with {len(splits)} document chunks")
        return vector_store
    
    def _create_knowledge_documents(self) -> List[Document]:
        """Create knowledge base documents from database and static content"""
        documents = []
        
        # Get programs from database
        try:
            programs = telecaller_db.get_programs()
            for program in programs:
                doc = Document(
                    page_content=f"""
                    Program: {program['program_name']}
                    Description: {program['description']}
                    Base Fee: ₹{program['base_fees']}
                    Category: {program['category']}
                    
                    This program offers comprehensive training and certification.
                    Industry-relevant curriculum with hands-on projects.
                    Expert instructors with real-world experience.
                    Job placement assistance and career support.
                    """,
                    metadata={
                        "type": "program",
                        "program_id": program['program_id'],
                        "category": program['category']
                    }
                )
                documents.append(doc)
        except Exception as e:
            logger.warning(f"Could not load programs from database: {e}")
        
        # Add general educational content
        general_content = [
            {
                "content": """
                Our educational programs are designed to meet industry standards and provide practical skills.
                We offer flexible learning schedules, online and offline modes, and personalized mentoring.
                All programs include certification, portfolio development, and job placement support.
                Student satisfaction rate is over 95% with successful career transitions.
                """,
                "metadata": {"type": "general", "topic": "program_benefits"}
            },
            {
                "content": """
                Enrollment process is simple: 
                1. Choose your program
                2. Schedule a counseling session
                3. Complete registration with payment
                4. Receive welcome kit and course materials
                5. Start your learning journey
                
                We offer installment options and scholarship programs for eligible students.
                """,
                "metadata": {"type": "general", "topic": "enrollment_process"}
            }
        ]
        
        for content in general_content:
            documents.append(Document(
                page_content=content["content"],
                metadata=content["metadata"]
            ))
        
        return documents
    
    @tool
    def get_program_details(program_id: int) -> Dict[str, Any]:
        """Get detailed information about a specific program"""
        try:
            program = telecaller_db.get_program_by_id(program_id)
            if program:
                return {
                    "success": True,
                    "program": program
                }
            return {"success": False, "message": "Program not found"}
        except Exception as e:
            return {"success": False, "message": f"Error fetching program: {str(e)}"}
    
    @tool
    def get_program_events(program_id: Optional[int] = None) -> Dict[str, Any]:
        """Get upcoming program events"""
        try:
            events = telecaller_db.get_program_events(program_id)
            return {
                "success": True,
                "events": events
            }
        except Exception as e:
            return {"success": False, "message": f"Error fetching events: {str(e)}"}
    
    @tool
    def get_partner_info(partner_id: int) -> Dict[str, Any]:
        """Get partner/school information"""
        try:
            partner = telecaller_db.get_partner_by_id(partner_id)
            if partner:
                return {
                    "success": True,
                    "partner": partner
                }
            return {"success": False, "message": "Partner not found"}
        except Exception as e:
            return {"success": False, "message": f"Error fetching partner: {str(e)}"}
    
    @tool
    def search_knowledge_base(query: str) -> Dict[str, Any]:
        """Search the knowledge base for relevant information"""
        try:
            # This would be implemented with the actual vector store search
            docs = self.vector_store.similarity_search(query, k=3)
            results = [{"content": doc.page_content, "metadata": doc.metadata} for doc in docs]
            return {
                "success": True,
                "results": results
            }
        except Exception as e:
            return {"success": False, "message": f"Error searching knowledge base: {str(e)}"}
    
    def _create_workflow(self) -> StateGraph:
        """Create LangGraph workflow for conversation management"""
        workflow = StateGraph(ConversationState)
        
        # Add nodes
        workflow.add_node("initialize_call", self._initialize_call)
        workflow.add_node("understand_intent", self._understand_intent)
        workflow.add_node("provide_information", self._provide_information)
        workflow.add_node("handle_objections", self._handle_objections)
        workflow.add_node("schedule_follow_up", self._schedule_follow_up)
        workflow.add_node("conclude_call", self._conclude_call)
        
        # Add edges
        workflow.set_entry_point("initialize_call")
        workflow.add_edge("initialize_call", "understand_intent")
        workflow.add_conditional_edges(
            "understand_intent",
            self._route_conversation,
            {
                "provide_info": "provide_information",
                "handle_objection": "handle_objections", 
                "schedule": "schedule_follow_up",
                "conclude": "conclude_call"
            }
        )
        workflow.add_edge("provide_information", "understand_intent")
        workflow.add_edge("handle_objections", "understand_intent")
        workflow.add_edge("schedule_follow_up", "conclude_call")
        workflow.add_edge("conclude_call", END)
        
        return workflow
    
    def _initialize_call(self, state: ConversationState) -> ConversationState:
        """Initialize the call with context and greeting"""
        call_context = state.get("call_context", {})
        
        # Get program and partner information
        program_info = None
        partner_info = None
        
        if "program_event_id" in call_context:
            try:
                program_event = telecaller_db.get_program_event_by_id(call_context["program_event_id"])
                if program_event:
                    program_info = program_event
            except Exception as e:
                logger.error(f"Error fetching program event: {e}")
        
        if "partner_id" in call_context:
            try:
                partner = telecaller_db.get_partner_by_id(call_context["partner_id"])
                if partner:
                    partner_info = partner
            except Exception as e:
                logger.error(f"Error fetching partner: {e}")
        
        # Create personalized greeting
        greeting = self._create_personalized_greeting(program_info, partner_info)
        
        state["messages"] = [SystemMessage(content=self._get_system_prompt())]
        state["messages"].append(AIMessage(content=greeting))
        state["current_step"] = "greeting"
        state["program_info"] = program_info
        state["partner_info"] = partner_info
        state["tools_used"] = []
        state["follow_up_required"] = False
        
        return state
    
    def _understand_intent(self, state: ConversationState) -> ConversationState:
        """Understand user intent and context"""
        if not state.get("messages"):
            return state
        
        # Get the latest user message
        user_messages = [msg for msg in state["messages"] if isinstance(msg, HumanMessage)]
        if not user_messages:
            return state
        
        latest_message = user_messages[-1].content
        
        # Use LLM to understand intent
        intent_prompt = f"""
        Analyze the following response from a potential student/parent: "{latest_message}"
        
        Current context:
        - Program: {state.get('program_info', {}).get('program_name', 'Unknown')}
        - Partner: {state.get('partner_info', {}).get('partner_name', 'Unknown')}
        
        Classify the intent as one of:
        - information_request: They want more details about the program
        - price_inquiry: They're asking about costs, fees, or discounts
        - objection: They have concerns or objections
        - interest: They show positive interest
        - schedule_request: They want to schedule something
        - end_call: They want to end the conversation
        
        Return only the classification.
        """
        
        try:
            response = self.llm.invoke([HumanMessage(content=intent_prompt)])
            intent = response.content.strip().lower()
            state["current_step"] = intent
        except Exception as e:
            logger.error(f"Error understanding intent: {e}")
            state["current_step"] = "information_request"
        
        return state
    
    def _provide_information(self, state: ConversationState) -> ConversationState:
        """Provide relevant information using RAG and tools"""
        user_message = [msg for msg in state["messages"] if isinstance(msg, HumanMessage)][-1].content
        
        # Search knowledge base
        try:
            docs = self.vector_store.similarity_search(user_message, k=3)
            context = "\n".join([doc.page_content for doc in docs])
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            context = "General program information available."
        
        # Generate response using context
        response_prompt = f"""
        Based on the user's question: "{user_message}"
        
        Context from knowledge base:
        {context}
        
        Program info: {state.get('program_info', {})}
        Partner info: {state.get('partner_info', {})}
        
        Provide a helpful, personalized response that addresses their question.
        Be enthusiastic but not pushy. Focus on value and benefits.
        Keep the response conversational and under 100 words.
        """
        
        try:
            response = self.llm.invoke([HumanMessage(content=response_prompt)])
            ai_response = response.content
            
            state["messages"].append(AIMessage(content=ai_response))
            state["tools_used"].append("knowledge_search")
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            fallback_response = "I'd be happy to provide more information about our programs. Could you please be more specific about what you'd like to know?"
            state["messages"].append(AIMessage(content=fallback_response))
        
        return state
    
    def _handle_objections(self, state: ConversationState) -> ConversationState:
        """Handle objections and concerns"""
        user_message = [msg for msg in state["messages"] if isinstance(msg, HumanMessage)][-1].content
        
        objection_response_prompt = f"""
        The user has expressed a concern or objection: "{user_message}"
        
        Program: {state.get('program_info', {}).get('program_name', 'Our program')}
        
        Address their concern empathetically and provide reassurance.
        Offer specific solutions or alternatives if possible.
        Be understanding and not argumentative.
        Keep response under 80 words.
        """
        
        try:
            response = self.llm.invoke([HumanMessage(content=objection_response_prompt)])
            ai_response = response.content
            
            state["messages"].append(AIMessage(content=ai_response))
            state["tools_used"].append("objection_handling")
        except Exception as e:
            logger.error(f"Error handling objection: {e}")
            fallback_response = "I understand your concern. Let me connect you with our counselor who can address this in detail and find the best solution for you."
            state["messages"].append(AIMessage(content=fallback_response))
        
        return state
    
    def _schedule_follow_up(self, state: ConversationState) -> ConversationState:
        """Schedule follow-up or next steps"""
        follow_up_response = """
        I'd be happy to schedule a follow-up call or send you more detailed information. 
        Would you prefer a call tomorrow or would you like me to email you our complete program brochure? 
        I can also arrange a demo session for you to experience our teaching methodology.
        """
        
        state["messages"].append(AIMessage(content=follow_up_response))
        state["follow_up_required"] = True
        state["tools_used"].append("scheduling")
        
        return state
    
    def _conclude_call(self, state: ConversationState) -> ConversationState:
        """Conclude the call professionally"""
        conclusion_response = """
        Thank you for your time today. I'll make sure you receive all the information we discussed. 
        If you have any questions in the meantime, please don't hesitate to reach out. 
        Have a wonderful day!
        """
        
        state["messages"].append(AIMessage(content=conclusion_response))
        state["current_step"] = "completed"
        state["call_outcome"] = "completed"
        
        # Save call data
        self._save_call_data(state)
        
        return state
    
    def _route_conversation(self, state: ConversationState) -> str:
        """Route conversation based on current step and context"""
        current_step = state.get("current_step", "")
        
        if "information_request" in current_step or "price_inquiry" in current_step:
            return "provide_info"
        elif "objection" in current_step:
            return "handle_objection"
        elif "schedule" in current_step:
            return "schedule"
        else:
            return "conclude"
    
    def _create_personalized_greeting(self, program_info: Optional[Dict], partner_info: Optional[Dict]) -> str:
        """Create personalized greeting based on context"""
        program_name = program_info.get('program_name', 'our program') if program_info else 'our program'
        partner_name = partner_info.get('partner_name', 'your institution') if partner_info else 'your institution'
        
        greeting = f"""
        Hello! I'm calling from our education team regarding the {program_name} that we discussed with {partner_name}. 
        I hope I'm speaking at a convenient time. I wanted to share some exciting updates about this program 
        and see if you have any questions about the curriculum or enrollment process.
        """
        
        return greeting.strip()
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for the AI telecaller"""
        return """
        You are a professional AI telecaller for an educational institution. Your role is to:
        
        1. Be friendly, professional, and helpful
        2. Provide accurate information about programs and courses
        3. Address concerns and objections empathetically
        4. Guide conversations toward positive outcomes
        5. Schedule follow-ups when appropriate
        6. Never be pushy or aggressive
        7. Always maintain a positive tone
        
        Guidelines:
        - Keep responses concise (under 100 words)
        - Ask clarifying questions when needed
        - Use the person's name when possible
        - Focus on value and benefits
        - Be patient with objections
        - Offer alternatives when someone seems hesitant
        
        Remember: Your goal is to help people find the right educational path, not just make sales.
        """
    
    def _save_call_data(self, state: ConversationState):
        """Save call data to database and local storage"""
        try:
            # Prepare call data
            call_context = state.get("call_context", {})
            
            # Save transcription locally
            transcription_data = {
                "call_id": call_context.get("call_sid", "unknown"),
                "timestamp": datetime.now().isoformat(),
                "messages": [
                    {
                        "type": type(msg).__name__,
                        "content": msg.content,
                        "timestamp": datetime.now().isoformat()
                    }
                    for msg in state.get("messages", [])
                ],
                "context": call_context,
                "outcome": state.get("call_outcome"),
                "tools_used": state.get("tools_used", [])
            }
            
            # Save to local file
            transcription_file = self.transcriptions_path / f"call_{call_context.get('call_sid', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(transcription_file, 'w') as f:
                json.dump(transcription_data, f, indent=2)
            
            # Save to database
            call_log_data = {
                "program_event_id": call_context.get("program_event_id"),
                "partner_id": call_context.get("partner_id"),
                "call_sid": call_context.get("call_sid"),
                "caller_number": call_context.get("caller_number"),
                "recipient_number": call_context.get("recipient_number"),
                "call_start_time": call_context.get("call_start_time"),
                "call_end_time": datetime.now(),
                "call_duration_seconds": call_context.get("call_duration_seconds", 0),
                "call_status": "completed",
                "conversation_summary": self._generate_summary(state),
                "outcome": state.get("call_outcome", "completed"),
                "recording_url": call_context.get("recording_url"),
                "transcription_path": str(transcription_file),
                "ai_prompt_used": "LangGraph AI Telecaller with RAG"
            }
            
            call_log_id = telecaller_db.create_call_log(call_log_data)
            logger.info(f"Call data saved - Log ID: {call_log_id}, Transcription: {transcription_file}")
            
        except Exception as e:
            logger.error(f"Error saving call data: {e}")
    
    def _generate_summary(self, state: ConversationState) -> str:
        """Generate conversation summary"""
        messages = state.get("messages", [])
        if not messages:
            return "No conversation recorded"
        
        try:
            conversation_text = "\n".join([
                f"{'AI' if isinstance(msg, AIMessage) else 'Human'}: {msg.content}"
                for msg in messages
            ])
            
            summary_prompt = f"""
            Summarize this conversation in 2-3 sentences:
            {conversation_text}
            
            Include: main topics discussed, user's level of interest, next steps if any.
            """
            
            response = self.llm.invoke([HumanMessage(content=summary_prompt)])
            return response.content
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return "Conversation completed - summary generation failed"
    
    def process_call(self, call_context: Dict[str, Any], user_input: str = None) -> Dict[str, Any]:
        """Process a call using the LangGraph workflow"""
        try:
            # Initialize state
            initial_state = {
                "messages": [],
                "call_context": call_context,
                "current_step": "initialize",
                "tools_used": [],
                "program_info": None,
                "partner_info": None,
                "call_outcome": None,
                "follow_up_required": False,
                "recording_path": None,
                "transcription_path": None
            }
            
            # Add user input if provided
            if user_input:
                initial_state["messages"].append(HumanMessage(content=user_input))
            
            # Run the workflow
            config = {"configurable": {"thread_id": call_context.get("call_sid", "default")}}
            result = self.app.invoke(initial_state, config)
            
            # Extract AI response
            ai_messages = [msg for msg in result["messages"] if isinstance(msg, AIMessage)]
            latest_response = ai_messages[-1].content if ai_messages else "Hello! How can I help you today?"
            
            return {
                "success": True,
                "response": latest_response,
                "state": result,
                "tools_used": result.get("tools_used", []),
                "follow_up_required": result.get("follow_up_required", False)
            }
            
        except Exception as e:
            logger.error(f"Error processing call: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": "I apologize, but I'm experiencing technical difficulties. Let me transfer you to a human representative."
            }

# Initialize the service
langgraph_telecaller = LangGraphTelecallerService()
