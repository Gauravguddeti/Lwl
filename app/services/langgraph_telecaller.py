"""
LangGraph-based Conversation Flow System for AI Telecaller
Manages intelligent conversation states and decision-making
"""

import os
import logging
from typing import Dict, Any, List, Optional, TypedDict, Annotated
from datetime import datetime
from enum import Enum

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langchain_core.tools import tool

from app.services.rag_system import TelecallerRAGSystem

logger = logging.getLogger(__name__)

class ConversationState(str, Enum):
    """Conversation states for the telecaller"""
    INITIAL_GREETING = "initial_greeting"
    PERMISSION_CHECK = "permission_check" 
    SCHOOL_VERIFICATION = "school_verification"
    PROGRAM_INTRODUCTION = "program_introduction"
    BENEFITS_DISCUSSION = "benefits_discussion"
    OBJECTION_HANDLING = "objection_handling"
    PRICING_DISCUSSION = "pricing_discussion"
    NEXT_STEPS = "next_steps"
    CLOSING = "closing"
    ENDED = "ended"

class ConversationContext(TypedDict):
    """Conversation context state"""
    messages: List[Dict[str, Any]]
    current_state: str
    school_info: Dict[str, Any]
    customer_responses: List[str]
    objections_raised: List[str]
    interests_expressed: List[str]
    next_actions: List[str]
    rag_context: List[Dict[str, Any]]
    conversation_metadata: Dict[str, Any]

class LangGraphTelecaller:
    """
    LangGraph-based conversation flow manager for intelligent telecalling
    """
    
    def __init__(self, openai_api_key: Optional[str] = None):
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        self.llm = None
        self.rag_system = None
        self.conversation_graph = None
        self._initialize_system()
    
    def _initialize_system(self):
        """Initialize the LangGraph system with enhanced prompting"""
        try:
            logger.info("🔧 Initializing Enhanced LangGraph Telecaller System...")
            
            # Initialize LLM with GPT-4 mini
            if self.openai_api_key:
                self.llm = ChatOpenAI(
                    model="gpt-4o-mini",
                    temperature=0.7,
                    api_key=self.openai_api_key
                )
                logger.info("✅ GPT-4 mini initialized for conversations")
            else:
                logger.warning("⚠️ No OpenAI API key provided. Using mock LLM.")
                self.llm = MockLLM()
            
            # Import and initialize advanced system prompts
            try:
                from app.config.system_prompts import (
                    get_advanced_system_prompt, 
                    get_conversation_starters, 
                    get_response_templates,
                    get_objection_handling
                )
                self.get_system_prompt = get_advanced_system_prompt
                self.conversation_starters = get_conversation_starters()
                self.response_templates = get_response_templates()
                self.objection_handlers = get_objection_handling()
                logger.info("✅ Advanced system prompts loaded")
            except ImportError as e:
                logger.warning(f"⚠️ Could not load advanced prompts: {e}")
                self.get_system_prompt = self._get_basic_system_prompt
                self.conversation_starters = {}
                self.response_templates = {}
                self.objection_handlers = {}
            
            # Initialize RAG system
            self.rag_system = TelecallerRAGSystem()
            self.rag_system.populate_default_knowledge()
            
            # Build conversation graph
            self._build_conversation_graph()
            
            logger.info("✅ Enhanced LangGraph Telecaller System initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize LangGraph system: {e}")
            raise
    
    def _get_basic_system_prompt(self, partner_info=None, program_info=None):
        """Basic system prompt fallback"""
        from app.config.system_prompts import get_time_greeting
        
        time_greeting = get_time_greeting()
        
        return f"""You are a professional telecaller representing Learn with Leaders. 
        
Start with: "{time_greeting}! Am I speaking with the school leader or coordinator?"

You are calling about the Cambridge University Summer Programme 2025 with exclusive scholarships.
Be professional, respectful, and adaptive to the conversation flow.
Always confirm email addresses and offer to schedule follow-up calls.
"""

    def _build_conversation_graph(self):
        """Build the conversation flow graph using LangGraph"""
        
        # Define the graph
        workflow = StateGraph(ConversationContext)
        
        # Add nodes (conversation states)
        workflow.add_node("initial_greeting", self._handle_initial_greeting)
        workflow.add_node("permission_check", self._handle_permission_check)
        workflow.add_node("school_verification", self._handle_school_verification)
        workflow.add_node("program_introduction", self._handle_program_introduction)
        workflow.add_node("benefits_discussion", self._handle_benefits_discussion)
        workflow.add_node("objection_handling", self._handle_objection_handling)
        workflow.add_node("pricing_discussion", self._handle_pricing_discussion)
        workflow.add_node("next_steps", self._handle_next_steps)
        workflow.add_node("closing", self._handle_closing)
        
        # Add edges (conversation flow)
        workflow.add_edge("initial_greeting", "permission_check")
        workflow.add_edge("permission_check", "school_verification")
        workflow.add_edge("school_verification", "program_introduction")
        workflow.add_edge("program_introduction", "benefits_discussion")
        workflow.add_edge("benefits_discussion", "pricing_discussion")
        workflow.add_edge("pricing_discussion", "next_steps")
        workflow.add_edge("next_steps", "closing")
        workflow.add_edge("closing", END)
        
        # Conditional edges for objection handling
        workflow.add_conditional_edges(
            "benefits_discussion",
            self._should_handle_objections,
            {
                "handle_objections": "objection_handling",
                "continue": "pricing_discussion"
            }
        )
        
        workflow.add_conditional_edges(
            "pricing_discussion", 
            self._should_handle_objections,
            {
                "handle_objections": "objection_handling",
                "continue": "next_steps"
            }
        )
        
        workflow.add_edge("objection_handling", "benefits_discussion")
        
        # Set entry point
        workflow.set_entry_point("initial_greeting")
        
        # Compile the graph
        self.conversation_graph = workflow.compile()
        
        logger.info("🔀 Conversation graph built successfully")
    
    def _should_handle_objections(self, state: ConversationContext) -> str:
        """Determine if objections need to be handled"""
        if state.get("objections_raised"):
            return "handle_objections"
        return "continue"
    
    async def _handle_initial_greeting(self, state: ConversationContext) -> ConversationContext:
        """Handle initial greeting"""
        logger.info("👋 Handling initial greeting")
        
        school_info = state["school_info"]
        
        # Get time-based greeting
        current_hour = datetime.now().hour
        if 5 <= current_hour < 12:
            greeting = "Good morning"
        elif 12 <= current_hour < 17:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"
        
        # Create greeting message
        greeting_message = f"{greeting}! This is {school_info.get('caller_name', 'Sarah')} calling from Learn with Leaders. I hope you're having a wonderful day!"
        
        state["messages"].append({
            "role": "assistant",
            "content": greeting_message,
            "state": ConversationState.INITIAL_GREETING.value,
            "timestamp": datetime.now().isoformat()
        })
        
        state["current_state"] = ConversationState.PERMISSION_CHECK.value
        
        return state
    
    async def _handle_permission_check(self, state: ConversationContext) -> ConversationContext:
        """Handle permission to continue conversation"""
        logger.info("🤝 Handling permission check")
        
        school_info = state["school_info"]
        
        permission_message = f"Am I speaking with {school_info.get('contact_person', 'the principal')} from {school_info.get('school_name', 'your school')}? Do you have 2-3 minutes to discuss an exciting educational opportunity for your students?"
        
        state["messages"].append({
            "role": "assistant", 
            "content": permission_message,
            "state": ConversationState.PERMISSION_CHECK.value,
            "timestamp": datetime.now().isoformat()
        })
        
        state["current_state"] = ConversationState.SCHOOL_VERIFICATION.value
        
        return state
    
    async def _handle_school_verification(self, state: ConversationContext) -> ConversationContext:
        """Handle school verification"""
        logger.info("🏫 Handling school verification")
        
        school_info = state["school_info"]
        
        # Get school-specific knowledge from RAG
        school_knowledge = self.rag_system.get_school_specific_knowledge(
            school_info.get('school_name', ''),
            "school reputation academic excellence"
        )
        
        state["rag_context"].extend(school_knowledge)
        
        verification_message = f"Perfect! I'm calling because {school_info.get('school_name', 'your school')} has such an excellent reputation for academic excellence, and I believe your students would be perfect candidates for our Cambridge University summer program."
        
        state["messages"].append({
            "role": "assistant",
            "content": verification_message,
            "state": ConversationState.SCHOOL_VERIFICATION.value,
            "timestamp": datetime.now().isoformat()
        })
        
        state["current_state"] = ConversationState.PROGRAM_INTRODUCTION.value
        
        return state
    
    async def _handle_program_introduction(self, state: ConversationContext) -> ConversationContext:
        """Handle program introduction"""
        logger.info("📚 Handling program introduction")
        
        school_info = state["school_info"]
        
        # Get program knowledge from RAG
        program_knowledge = self.rag_system.get_program_knowledge(
            school_info.get('program_name', 'Cambridge Summer Programme')
        )
        
        state["rag_context"].extend(program_knowledge)
        
        intro_message = f"I'm calling about our {school_info.get('program_name', 'Cambridge Summer Programme 2025')} - a prestigious 2-week program where students experience authentic Cambridge University academic life. They attend lectures by renowned professors, stay in historic college accommodations, and build global networks with peers from around the world."
        
        state["messages"].append({
            "role": "assistant",
            "content": intro_message,
            "state": ConversationState.PROGRAM_INTRODUCTION.value,
            "timestamp": datetime.now().isoformat()
        })
        
        state["current_state"] = ConversationState.BENEFITS_DISCUSSION.value
        
        return state
    
    async def _handle_benefits_discussion(self, state: ConversationContext) -> ConversationContext:
        """Handle benefits discussion"""
        logger.info("🎯 Handling benefits discussion")
        
        benefits_message = "The program offers incredible benefits: students gain confidence in international settings, receive Cambridge University certificates that strengthen university applications, and develop global perspectives that last a lifetime. We've seen students return with dramatically improved leadership skills and clearer career direction."
        
        state["messages"].append({
            "role": "assistant",
            "content": benefits_message,
            "state": ConversationState.BENEFITS_DISCUSSION.value,
            "timestamp": datetime.now().isoformat()
        })
        
        state["current_state"] = ConversationState.PRICING_DISCUSSION.value
        
        return state
    
    async def _handle_objection_handling(self, state: ConversationContext) -> ConversationContext:
        """Handle objections intelligently using RAG"""
        logger.info("🛡️ Handling objections")
        
        objections = state.get("objections_raised", [])
        
        if objections:
            latest_objection = objections[-1]
            
            # Get objection handling knowledge from RAG
            objection_knowledge = self.rag_system.get_objection_handling_knowledge(latest_objection)
            state["rag_context"].extend(objection_knowledge)
            
            # Generate response based on objection type
            if "budget" in latest_objection.lower() or "cost" in latest_objection.lower():
                response = "I completely understand that budget is an important consideration. That's exactly why we offer flexible payment plans and partial scholarships for deserving students. Many schools find that the long-term benefits - increased university acceptances and student confidence - provide excellent return on investment."
            elif "time" in latest_objection.lower():
                response = "I understand timing can be challenging. We have multiple program dates throughout the year and can work with your academic calendar. Many schools prefer to plan 6-12 months ahead to integrate this into their curriculum planning."
            else:
                response = "I appreciate you sharing that concern with me. Let me address that specifically and see how we can find a solution that works for your school."
            
            state["messages"].append({
                "role": "assistant",
                "content": response,
                "state": ConversationState.OBJECTION_HANDLING.value,
                "timestamp": datetime.now().isoformat()
            })
        
        state["current_state"] = ConversationState.BENEFITS_DISCUSSION.value
        
        return state
    
    async def _handle_pricing_discussion(self, state: ConversationContext) -> ConversationContext:
        """Handle pricing discussion"""
        logger.info("💰 Handling pricing discussion")
        
        school_info = state["school_info"]
        
        pricing_message = f"The program investment is {school_info.get('total_fee', '₹4,50,000')} per student, which includes everything - accommodation, meals, academic sessions, cultural activities, and insurance. We're currently offering an early bird discount of {school_info.get('early_bird_discount', '₹50,000')} for schools that enroll before December 31st."
        
        state["messages"].append({
            "role": "assistant",
            "content": pricing_message,
            "state": ConversationState.PRICING_DISCUSSION.value,
            "timestamp": datetime.now().isoformat()
        })
        
        state["current_state"] = ConversationState.NEXT_STEPS.value
        
        return state
    
    async def _handle_next_steps(self, state: ConversationContext) -> ConversationContext:
        """Handle next steps"""
        logger.info("📋 Handling next steps")
        
        school_info = state["school_info"]
        
        next_steps_message = f"Would you like me to send you our detailed program brochure and application forms? I can email them to you within the hour. Also, would you prefer to schedule a follow-up call to discuss this further, or would you like me to arrange a presentation for your team?"
        
        state["messages"].append({
            "role": "assistant",
            "content": next_steps_message,
            "state": ConversationState.NEXT_STEPS.value,
            "timestamp": datetime.now().isoformat()
        })
        
        state["next_actions"] = [
            "Send program brochure",
            "Send application forms", 
            "Schedule follow-up call",
            "Arrange school presentation"
        ]
        
        state["current_state"] = ConversationState.CLOSING.value
        
        return state
    
    async def _handle_closing(self, state: ConversationContext) -> ConversationContext:
        """Handle conversation closing"""
        logger.info("👋 Handling closing")
        
        school_info = state["school_info"]
        
        closing_message = f"Thank you so much for your time today, {school_info.get('contact_person', '')}. I'm excited about the possibility of {school_info.get('school_name', 'your school')} students participating in this life-changing program. I'll send you those materials right away, and please don't hesitate to call me if you have any questions. Have a wonderful rest of your day!"
        
        state["messages"].append({
            "role": "assistant",
            "content": closing_message,
            "state": ConversationState.CLOSING.value,
            "timestamp": datetime.now().isoformat()
        })
        
        state["current_state"] = ConversationState.ENDED.value
        state["conversation_metadata"]["end_time"] = datetime.now().isoformat()
        
        return state
    
    def start_conversation(self, school_info: Dict[str, Any]) -> ConversationContext:
        """Start a new conversation"""
        logger.info(f"🚀 Starting conversation with {school_info.get('school_name', 'Unknown School')}")
        
        initial_state = ConversationContext(
            messages=[],
            current_state=ConversationState.INITIAL_GREETING.value,
            school_info=school_info,
            customer_responses=[],
            objections_raised=[],
            interests_expressed=[],
            next_actions=[],
            rag_context=[],
            conversation_metadata={
                "start_time": datetime.now().isoformat(),
                "school_name": school_info.get('school_name'),
                "contact_person": school_info.get('contact_person'),
                "phone_number": school_info.get('phone_number')
            }
        )
        
        return initial_state
    
    async def process_conversation_step(self, state: ConversationContext, customer_input: Optional[str] = None) -> ConversationContext:
        """Process one step of the conversation"""
        
        if customer_input:
            # Add customer response
            state["customer_responses"].append(customer_input)
            state["messages"].append({
                "role": "human",
                "content": customer_input,
                "timestamp": datetime.now().isoformat()
            })
            
            # Analyze for objections or interests
            if any(word in customer_input.lower() for word in ['expensive', 'budget', 'cost', 'money', 'afford']):
                state["objections_raised"].append("budget_concern")
            
            if any(word in customer_input.lower() for word in ['busy', 'time', 'schedule', 'timing']):
                state["objections_raised"].append("timing_concern")
            
            if any(word in customer_input.lower() for word in ['interested', 'sounds good', 'tell me more', 'yes']):
                state["interests_expressed"].append("positive_response")
        
        # Process through the graph
        result = await self.conversation_graph.ainvoke(state)
        
        return result

class MockLLM:
    """Mock LLM for testing without OpenAI API"""
    
    def invoke(self, messages):
        return AIMessage(content="This is a mock response for testing purposes.")

def test_langgraph_system():
    """Test the LangGraph conversation system"""
    print("🧪 Testing LangGraph Conversation System")
    print("=" * 50)
    
    # Initialize system
    telecaller = LangGraphTelecaller()
    
    # Test school info
    school_info = {
        'school_name': 'Delhi Public School',
        'contact_person': 'Dr. Sharma',
        'phone_number': '+17276082005',
        'program_name': 'Cambridge Summer Programme 2025',
        'total_fee': '₹4,50,000',
        'early_bird_discount': '₹50,000',
        'caller_name': 'Sarah'
    }
    
    # Start conversation
    conversation_state = telecaller.start_conversation(school_info)
    
    print(f"📞 Started conversation with {school_info['school_name']}")
    print(f"🎯 Initial state: {conversation_state['current_state']}")
    print(f"📊 Conversation metadata: {conversation_state['conversation_metadata']}")
    
    print("\n✅ LangGraph system test completed!")
    return True

if __name__ == "__main__":
    test_langgraph_system()
