"""
LangGraph Conversation Flow for AI Telecaller
Manages conversation state and intelligent routing
"""

import logging
from typing import Dict, Any, List, TypedDict
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from app.services.rag_service import RAGService

logger = logging.getLogger(__name__)

class ConversationState(TypedDict):
    """State for conversation flow"""
    messages: List[Dict[str, str]]
    phone_number: str
    partner_info: Dict[str, Any]
    conversation_stage: str
    intent: str
    context: List[Dict[str, Any]]
    call_duration: int
    sentiment: str

class ConversationFlow:
    """LangGraph-based conversation flow manager"""
    
    def __init__(self, openai_api_key: str):
        self.openai_api_key = openai_api_key
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            openai_api_key=openai_api_key
        )
        self.rag_service = RAGService(openai_api_key)
        self.graph = self._build_conversation_graph()
        self.memory = MemorySaver()
    
    def _build_conversation_graph(self) -> StateGraph:
        """Build the conversation flow graph"""
        
        workflow = StateGraph(ConversationState)
        
        # Add nodes
        workflow.add_node("identify_caller", self._identify_caller)
        workflow.add_node("greeting", self._greeting_stage)
        workflow.add_node("information_gathering", self._information_gathering)
        workflow.add_node("event_discussion", self._event_discussion)
        workflow.add_node("closing", self._closing_stage)
        workflow.add_node("fallback", self._fallback_handler)
        
        # Add edges
        workflow.add_edge("identify_caller", "greeting")
        workflow.add_conditional_edges(
            "greeting",
            self._route_conversation,
            {
                "information_gathering": "information_gathering",
                "event_discussion": "event_discussion",
                "closing": "closing",
                "fallback": "fallback"
            }
        )
        workflow.add_conditional_edges(
            "information_gathering",
            self._route_conversation,
            {
                "event_discussion": "event_discussion",
                "closing": "closing",
                "fallback": "fallback"
            }
        )
        workflow.add_conditional_edges(
            "event_discussion",
            self._route_conversation,
            {
                "closing": "closing",
                "information_gathering": "information_gathering",
                "fallback": "fallback"
            }
        )
        workflow.add_edge("closing", END)
        workflow.add_edge("fallback", "closing")
        
        # Set entry point
        workflow.set_entry_point("identify_caller")
        
        return workflow.compile(checkpointer=self.memory)
    
    def _identify_caller(self, state: ConversationState) -> ConversationState:
        """Identify caller and get relevant context"""
        try:
            phone_number = state.get("phone_number", "")
            
            # Get partner information using RAG
            partner_info = self.rag_service.get_partner_by_phone(phone_number)
            context = self.rag_service.get_relevant_context(
                f"partner information phone {phone_number}",
                phone_number,
                k=5
            )
            
            state["partner_info"] = partner_info
            state["context"] = context
            state["conversation_stage"] = "greeting"
            
            logger.info(f"📞 Identified caller: {partner_info.get('name', 'Unknown')}")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Error identifying caller: {e}")
            state["conversation_stage"] = "fallback"
            return state
    
    def _greeting_stage(self, state: ConversationState) -> ConversationState:
        """Handle greeting and initial interaction"""
        try:
            partner_info = state.get("partner_info", {})
            partner_name = partner_info.get("name", "")
            event_name = partner_info.get("event_name", "")
            
            # Create personalized greeting
            system_prompt = f"""
            You are an AI assistant for Global Learning Academy. You are calling {partner_name}.
            Context: {partner_info}
            
            Create a warm, professional greeting. If you know the partner's name and event, personalize it.
            Keep it concise and friendly. Ask how they are doing and mention why you're calling.
            """
            
            # Get conversation suggestions from RAG
            suggestions = self.rag_service.get_conversation_suggestions("greeting", state.get("phone_number"))
            
            # Generate response
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Generate a greeting for {partner_name} regarding {event_name}")
            ]
            
            response = self.llm.invoke(messages)
            
            # Update state
            state["messages"].append({
                "role": "assistant",
                "content": response.content,
                "stage": "greeting",
                "suggestions": suggestions
            })
            
            state["conversation_stage"] = "information_gathering"
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Error in greeting stage: {e}")
            state["conversation_stage"] = "fallback"
            return state
    
    def _information_gathering(self, state: ConversationState) -> ConversationState:
        """Gather information and understand caller intent"""
        try:
            context = state.get("context", [])
            partner_info = state.get("partner_info", {})
            recent_messages = state.get("messages", [])[-3:]  # Last 3 messages
            
            system_prompt = f"""
            You are gathering information about the caller's needs. Based on:
            Partner Info: {partner_info}
            Recent conversation: {recent_messages}
            Context: {context}
            
            Ask relevant questions to understand their intent. Are they:
            - Asking about an upcoming event?
            - Wanting to enroll in a program?
            - Needing technical support?
            - Other inquiry?
            
            Be conversational and helpful.
            """
            
            # This would typically process the user's response
            # For now, we'll simulate determining intent
            
            # Analyze intent from context
            intent = "event_inquiry"  # This would be determined from user input
            if any("enroll" in str(ctx).lower() for ctx in context):
                intent = "enrollment"
            elif any("support" in str(ctx).lower() for ctx in context):
                intent = "support"
            
            state["intent"] = intent
            state["conversation_stage"] = "event_discussion"
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Error in information gathering: {e}")
            state["conversation_stage"] = "fallback"
            return state
    
    def _event_discussion(self, state: ConversationState) -> ConversationState:
        """Discuss specific events or programs"""
        try:
            partner_info = state.get("partner_info", {})
            intent = state.get("intent", "general")
            context = state.get("context", [])
            
            # Get event-specific context
            event_context = self.rag_service.get_relevant_context(
                f"event {partner_info.get('event_name', '')} {intent}",
                state.get("phone_number"),
                k=3
            )
            
            system_prompt = f"""
            Discuss the event or program with the caller. 
            Partner: {partner_info.get('name', 'Unknown')}
            Event: {partner_info.get('event_name', 'General Program')}
            Intent: {intent}
            Context: {event_context}
            
            Provide helpful information about:
            - Event details (date, time, location)
            - What to expect
            - How to prepare
            - Answer any questions
            
            Be informative and encouraging.
            """
            
            # Generate response based on event context
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Discuss {partner_info.get('event_name', 'our program')} with the caller")
            ]
            
            response = self.llm.invoke(messages)
            
            state["messages"].append({
                "role": "assistant",
                "content": response.content,
                "stage": "event_discussion",
                "event_context": event_context
            })
            
            state["conversation_stage"] = "closing"
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Error in event discussion: {e}")
            state["conversation_stage"] = "fallback"
            return state
    
    def _closing_stage(self, state: ConversationState) -> ConversationState:
        """Handle conversation closing"""
        try:
            partner_info = state.get("partner_info", {})
            
            system_prompt = f"""
            Conclude the conversation professionally and warmly.
            Partner: {partner_info.get('name', 'Unknown')}
            
            - Thank them for their time
            - Summarize key points discussed
            - Provide next steps if any
            - Offer additional assistance
            - End with a professional closing
            """
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content="Generate a professional closing for this conversation")
            ]
            
            response = self.llm.invoke(messages)
            
            state["messages"].append({
                "role": "assistant",
                "content": response.content,
                "stage": "closing"
            })
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Error in closing stage: {e}")
            return state
    
    def _fallback_handler(self, state: ConversationState) -> ConversationState:
        """Handle fallback scenarios"""
        try:
            fallback_message = """
            I apologize, but I'm having some technical difficulties. 
            Let me transfer you to one of our human representatives who can better assist you.
            Thank you for your patience, and have a great day!
            """
            
            state["messages"].append({
                "role": "assistant",
                "content": fallback_message,
                "stage": "fallback"
            })
            
            return state
            
        except Exception as e:
            logger.error(f"❌ Error in fallback handler: {e}")
            return state
    
    def _route_conversation(self, state: ConversationState) -> str:
        """Route conversation to next stage"""
        current_stage = state.get("conversation_stage", "greeting")
        call_duration = state.get("call_duration", 0)
        
        # Simple routing logic (can be made more sophisticated)
        if call_duration > 300:  # 5 minutes
            return "closing"
        elif current_stage == "greeting":
            return "information_gathering"
        elif current_stage == "information_gathering":
            return "event_discussion"
        elif current_stage == "event_discussion":
            return "closing"
        else:
            return "fallback"
    
    def process_conversation(self, phone_number: str, user_input: str = None) -> Dict[str, Any]:
        """Process a conversation turn"""
        try:
            # Create initial state
            initial_state = ConversationState(
                messages=[],
                phone_number=phone_number,
                partner_info={},
                conversation_stage="identify_caller",
                intent="unknown",
                context=[],
                call_duration=0,
                sentiment="neutral"
            )
            
            # Run the graph
            config = {"configurable": {"thread_id": phone_number}}
            result = self.graph.invoke(initial_state, config)
            
            # Get the latest assistant message
            assistant_messages = [msg for msg in result.get("messages", []) if msg.get("role") == "assistant"]
            latest_response = assistant_messages[-1] if assistant_messages else {"content": "Hello! How can I help you today?"}
            
            return {
                "response": latest_response.get("content", ""),
                "stage": result.get("conversation_stage", "greeting"),
                "partner_info": result.get("partner_info", {}),
                "suggestions": latest_response.get("suggestions", []),
                "context": result.get("context", [])
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing conversation: {e}")
            return {
                "response": "I'm sorry, I'm experiencing technical difficulties. Please try again.",
                "stage": "fallback",
                "partner_info": {},
                "suggestions": [],
                "context": []
            }
