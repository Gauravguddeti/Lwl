"""
Enhanced Campaign Orchestrator with LangGraph and RAG Integration
Combines the existing campaign system with intelligent conversation flow
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.services.enhanced_campaign_orchestrator import EnhancedCampaignOrchestrator
from app.services.langgraph_telecaller import LangGraphTelecaller, ConversationContext
from app.services.rag_system import TelecallerRAGSystem
from app.services.dynamic_tag_processor import DynamicTagProcessor

logger = logging.getLogger(__name__)

class SmartTelecallerOrchestrator(EnhancedCampaignOrchestrator):
    """
    Enhanced Campaign Orchestrator with LangGraph and RAG intelligence
    """
    
    def __init__(self, db_queries, twilio_service, openai_api_key: Optional[str] = None):
        super().__init__(db_queries, twilio_service)
        self.langgraph_telecaller = None
        self.rag_system = None
        self.openai_api_key = openai_api_key
        self._initialize_ai_components()
    
    def _initialize_ai_components(self):
        """Initialize LangGraph and RAG components"""
        try:
            logger.info("🤖 Initializing AI components (LangGraph + RAG)...")
            
            # Initialize LangGraph conversation system
            self.langgraph_telecaller = LangGraphTelecaller(self.openai_api_key)
            
            # Initialize RAG system
            self.rag_system = TelecallerRAGSystem()
            
            logger.info("✅ AI components initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize AI components: {e}")
            # Fall back to basic mode
            self.langgraph_telecaller = None
            self.rag_system = None
            logger.warning("⚠️ Falling back to basic conversation mode")
    
    def execute_smart_campaign_loop(self, job_id: int) -> Dict[str, Any]:
        """
        Execute campaign loop with LangGraph conversation intelligence
        """
        
        logger.info(f"🚀 Starting Smart Campaign Loop with AI for Job ID: {job_id}")
        
        try:
            # Get all scheduled events (rows) for this job
            rows = self.db_queries.get_scheduled_job_events(job_id)
            
            if not rows:
                logger.warning(f"No rows found for job {job_id}")
                return {
                    'success': True,
                    'message': f'No events found for job {job_id}',
                    'job_id': job_id,
                    'total_rows': 0,
                    'processed_calls': 0,
                    'successful_calls': 0,
                    'failed_calls': 0,
                    'loop_results': []
                }
            
            # Execute the smart loop: For i = 0 to rows.count - 1
            loop_results = []
            successful_calls = 0
            failed_calls = 0
            total_rows = len(rows)
            
            logger.info(f"📊 Executing Smart AI Loop: For i = 0 to {total_rows - 1}")
            
            for i in range(total_rows):  # For i = 0 to rows.count - 1
                logger.info(f"🔄 Smart Loop iteration i = {i}")
                
                row = rows[i]
                
                # Step 1: Initialize AI conversation context
                conversation_context = self._initialize_ai_conversation(row, i)
                
                # Step 2: Generate intelligent system prompt using RAG
                intelligent_prompt = self._generate_intelligent_system_prompt(row, conversation_context, i)
                
                # Step 3: Smart tool assignment with AI reasoning
                smart_tools = self._assign_smart_tools(row, conversation_context, i)
                
                # Step 4: Execute AI-powered IVR call
                call_result = self._execute_ai_enhanced_call(row, intelligent_prompt, smart_tools, conversation_context, i)
                
                # Step 5: AI-enhanced audit log with conversation analysis
                audit_result = self._create_ai_audit_log(row, call_result, conversation_context, i)
                
                # Compile iteration result with AI insights
                iteration_result = {
                    'iteration': i,
                    'row_data': {
                        'event_id': row.get('event_id'),
                        'school_name': row.get('school_name'),
                        'program_name': row.get('program_name'),
                        'phone_number': row.get('phone_number')
                    },
                    'ai_conversation_context': {
                        'conversation_states': len(conversation_context.get('messages', [])),
                        'objections_detected': len(conversation_context.get('objections_raised', [])),
                        'interests_expressed': len(conversation_context.get('interests_expressed', [])),
                        'rag_knowledge_used': len(conversation_context.get('rag_context', []))
                    },
                    'intelligent_prompt_length': len(intelligent_prompt),
                    'smart_tools_assigned': smart_tools,
                    'call_result': call_result,
                    'audit_result': audit_result,
                    'status': call_result.get('status', 'UNKNOWN'),
                    'ai_insights': self._extract_ai_insights(conversation_context),
                    'timestamp': datetime.now().isoformat()
                }
                
                loop_results.append(iteration_result)
                
                # Track success/failure
                if call_result.get('status') == 'SUCCESS':
                    successful_calls += 1
                else:
                    failed_calls += 1
                
                logger.info(f"✅ Smart Loop iteration {i} completed with AI insights")
            
            # Return comprehensive results with AI analytics
            campaign_result = {
                'success': True,
                'message': f'Smart AI Campaign loop completed for job {job_id}',
                'job_id': job_id,
                'total_rows': total_rows,
                'processed_calls': len(loop_results),
                'successful_calls': successful_calls,
                'failed_calls': failed_calls,
                'loop_results': loop_results,
                'ai_analytics': self._generate_campaign_ai_analytics(loop_results),
                'execution_summary': {
                    'loop_structure': f'Smart AI Loop: For i = 0 to {total_rows - 1}',
                    'iterations_completed': len(loop_results),
                    'success_rate': f'{(successful_calls/total_rows)*100:.1f}%' if total_rows > 0 else '0%',
                    'ai_enhancement': 'Enabled' if self.langgraph_telecaller else 'Disabled',
                    'rag_knowledge_base': 'Active' if self.rag_system else 'Inactive',
                    'execution_time': datetime.now().isoformat()
                }
            }
            
            logger.info(f"🎉 Smart AI Campaign Loop completed successfully!")
            logger.info(f"📊 Results: {successful_calls}/{total_rows} calls successful with AI enhancement")
            
            return campaign_result
            
        except Exception as e:
            logger.error(f"❌ Smart AI Campaign Loop failed: {e}")
            return {
                'success': False,
                'message': f'Smart campaign loop execution failed: {str(e)}',
                'job_id': job_id,
                'total_rows': 0,
                'processed_calls': 0,
                'successful_calls': 0,
                'failed_calls': 0,
                'error': str(e),
                'ai_enhancement': 'Failed'
            }
    
    def _initialize_ai_conversation(self, row: Dict[str, Any], iteration: int) -> ConversationContext:
        """Initialize AI conversation context for this call"""
        
        if not self.langgraph_telecaller:
            return {}
        
        logger.info(f"🤖 Initializing AI conversation for iteration {iteration}")
        
        school_info = {
            'school_name': row.get('school_name', 'Unknown School'),
            'contact_person': row.get('contact_person', 'Principal'),
            'phone_number': row.get('phone_number', ''),
            'program_name': row.get('program_name', 'Cambridge Summer Programme 2025'),
            'total_fee': row.get('original_fee', '₹4,50,000'),
            'early_bird_discount': row.get('discount_amount', '₹50,000'),
            'caller_name': 'Sarah Johnson',
            'email_address': row.get('email_address', 'info@school.edu')
        }
        
        conversation_context = self.langgraph_telecaller.start_conversation(school_info)
        
        logger.info(f"✅ AI conversation context initialized for {school_info['school_name']}")
        
        return conversation_context
    
    def _generate_intelligent_system_prompt(self, row: Dict[str, Any], conversation_context: ConversationContext, iteration: int) -> str:
        """Generate intelligent system prompt using RAG and conversation context"""
        
        logger.info(f"🧠 Generating intelligent system prompt for iteration {iteration}")
        
        if not self.rag_system:
            # Fall back to basic prompt generation
            return self._generate_concise_system_prompt(row, iteration)
        
        # Get relevant knowledge from RAG
        school_name = row.get('school_name', '')
        program_name = row.get('program_name', '')
        
        # Retrieve multiple types of knowledge
        school_knowledge = self.rag_system.get_school_specific_knowledge(school_name, "school information academic reputation")
        program_knowledge = self.rag_system.get_program_knowledge(program_name)
        
        # Build intelligent prompt with RAG context
        base_template = self._generate_concise_system_prompt(row, iteration)
        
        # Enhance with RAG knowledge
        rag_context = ""
        if school_knowledge:
            rag_context += f"\n[SCHOOL INSIGHTS]\n{school_knowledge[0]['content'][:300]}\n"
        
        if program_knowledge:
            rag_context += f"\n[PROGRAM INSIGHTS]\n{program_knowledge[0]['content'][:300]}\n"
        
        # Process with dynamic tags
        from app.services.dynamic_tag_processor import DynamicTagProcessor
        tag_processor = DynamicTagProcessor()
        enhanced_prompt = tag_processor.process_system_prompt(base_template + rag_context, row)
        
        logger.info(f"✅ Intelligent prompt generated ({len(enhanced_prompt)} characters)")
        
        return enhanced_prompt
    
    def _assign_smart_tools(self, row: Dict[str, Any], conversation_context: ConversationContext, iteration: int) -> List[str]:
        """Assign tools intelligently based on conversation context and school type"""
        
        logger.info(f"🔧 Assigning smart tools for iteration {iteration}")
        
        # Base tools from parent class
        base_tools = self._assign_tools_for_call(row, iteration)
        
        # Add AI-specific tools
        smart_tools = base_tools.copy()
        
        # Add conversation intelligence tools
        smart_tools.extend([
            'rag_knowledge_retrieval',
            'conversation_state_management',
            'objection_detection_and_handling',
            'interest_level_analysis'
        ])
        
        # Add school-specific intelligent tools
        school_name = row.get('school_name', '').lower()
        if 'international' in school_name:
            smart_tools.append('international_school_intelligence')
        elif 'public' in school_name or 'dps' in school_name:
            smart_tools.append('public_school_intelligence')
        
        # Add program-specific tools
        program_name = row.get('program_name', '').lower()
        if 'cambridge' in program_name:
            smart_tools.append('cambridge_specific_intelligence')
        
        logger.info(f"🎯 Smart tools assigned: {len(smart_tools)} tools")
        
        return smart_tools
    
    def _execute_ai_enhanced_call(self, row: Dict[str, Any], intelligent_prompt: str, smart_tools: List[str], conversation_context: ConversationContext, iteration: int) -> Dict[str, Any]:
        """Execute IVR call with AI enhancement"""
        
        logger.info(f"📞 Executing AI-enhanced call for iteration {iteration}")
        
        school_name = row.get('school_name', 'Unknown School')
        phone_number = row.get('phone_number', '')
        
        # Prepare AI-enhanced call data
        enhanced_call_data = {
            'to_number': phone_number,
            'system_prompt': intelligent_prompt,
            'conversation_context': conversation_context,
            'smart_tools': smart_tools,
            'school_info': row,
            'ai_enabled': True
        }
        
        try:
            # Execute the call with AI enhancement
            call_response = self.twilio_service.initiate_ai_call(
                to_number=phone_number,
                system_prompt=intelligent_prompt,
                voice_settings={
                    'voice': 'alice',
                    'language': 'en-IN',
                    'ai_enhanced': True
                }
            )
            
            result = {
                'status': 'SUCCESS',
                'call_sid': call_response.sid if hasattr(call_response, 'sid') else 'MOCK_SID',
                'phone_number': phone_number,
                'school_name': school_name,
                'conversation_context': conversation_context,
                'ai_enhanced': True,
                'smart_tools_used': smart_tools,
                'call_duration': 'TBD',
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"✅ AI-enhanced call executed successfully for {school_name}")
            
        except Exception as e:
            logger.error(f"❌ AI-enhanced call failed for {school_name}: {e}")
            result = {
                'status': 'FAILED',
                'error': str(e),
                'phone_number': phone_number,
                'school_name': school_name,
                'ai_enhanced': True,
                'timestamp': datetime.now().isoformat()
            }
        
        return result
    
    def _create_ai_audit_log(self, row: Dict[str, Any], call_result: Dict[str, Any], conversation_context: ConversationContext, iteration: int) -> Dict[str, Any]:
        """Create AI-enhanced audit log"""
        
        logger.info(f"📋 Creating AI-enhanced audit log for iteration {iteration}")
        
        # Base audit from parent class
        base_audit = self._create_audit_log(row, call_result, call_result.get('system_prompt', ''), call_result.get('smart_tools_used', []), iteration)
        
        # Enhance with AI insights
        ai_audit = {
            **base_audit,
            'ai_conversation_analysis': {
                'total_messages': len(conversation_context.get('messages', [])),
                'conversation_states_traversed': conversation_context.get('current_state', 'unknown'),
                'objections_raised': conversation_context.get('objections_raised', []),
                'interests_expressed': conversation_context.get('interests_expressed', []),
                'rag_knowledge_items_used': len(conversation_context.get('rag_context', [])),
                'next_actions_recommended': conversation_context.get('next_actions', [])
            },
            'ai_enhancement_status': 'enabled',
            'smart_tools_effectiveness': self._analyze_tool_effectiveness(call_result.get('smart_tools_used', [])),
            'conversation_quality_score': self._calculate_conversation_quality_score(conversation_context),
            'ai_audit_timestamp': datetime.now().isoformat()
        }
        
        return ai_audit
    
    def _extract_ai_insights(self, conversation_context: ConversationContext) -> Dict[str, Any]:
        """Extract AI insights from conversation context"""
        
        insights = {
            'conversation_flow_quality': 'good' if len(conversation_context.get('messages', [])) > 2 else 'needs_improvement',
            'objection_handling_required': len(conversation_context.get('objections_raised', [])) > 0,
            'customer_engagement_level': 'high' if len(conversation_context.get('interests_expressed', [])) > 0 else 'moderate',
            'knowledge_utilization': len(conversation_context.get('rag_context', [])),
            'recommended_follow_up_actions': conversation_context.get('next_actions', []),
            'conversation_completion_status': conversation_context.get('current_state', 'incomplete')
        }
        
        return insights
    
    def _analyze_tool_effectiveness(self, tools_used: List[str]) -> Dict[str, Any]:
        """Analyze the effectiveness of tools used"""
        
        effectiveness = {
            'total_tools_used': len(tools_used),
            'ai_tools_ratio': len([t for t in tools_used if 'intelligence' in t or 'ai' in t.lower()]) / max(len(tools_used), 1),
            'conversation_tools_active': 'conversation_state_management' in tools_used,
            'rag_tools_active': 'rag_knowledge_retrieval' in tools_used,
            'objection_handling_active': 'objection_detection_and_handling' in tools_used
        }
        
        return effectiveness
    
    def _calculate_conversation_quality_score(self, conversation_context: ConversationContext) -> float:
        """Calculate conversation quality score based on AI metrics"""
        
        score = 0.0
        
        # Message exchange quality (0-30 points)
        message_count = len(conversation_context.get('messages', []))
        score += min(message_count * 3, 30)
        
        # Objection handling (0-25 points)
        objections = conversation_context.get('objections_raised', [])
        if objections:
            score += 25  # Bonus for handling objections
        
        # Interest level (0-25 points)
        interests = conversation_context.get('interests_expressed', [])
        score += len(interests) * 12.5
        
        # Knowledge utilization (0-20 points)
        rag_items = len(conversation_context.get('rag_context', []))
        score += min(rag_items * 4, 20)
        
        return min(score, 100.0)
    
    def _generate_campaign_ai_analytics(self, loop_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate AI analytics for the entire campaign"""
        
        analytics = {
            'total_calls_with_ai': len(loop_results),
            'average_conversation_quality': 0.0,
            'total_objections_handled': 0,
            'total_interests_generated': 0,
            'rag_knowledge_utilization': 0,
            'ai_tool_effectiveness': 0.0,
            'conversation_completion_rate': 0.0
        }
        
        if loop_results:
            # Calculate averages
            quality_scores = []
            total_objections = 0
            total_interests = 0
            total_rag_usage = 0
            completed_conversations = 0
            
            for result in loop_results:
                ai_insights = result.get('ai_insights', {})
                ai_context = result.get('ai_conversation_context', {})
                
                # Quality scores
                if 'conversation_quality_score' in result.get('audit_result', {}):
                    quality_scores.append(result['audit_result']['conversation_quality_score'])
                
                # Objections and interests
                total_objections += ai_context.get('objections_detected', 0)
                total_interests += ai_context.get('interests_expressed', 0)
                total_rag_usage += ai_context.get('rag_knowledge_used', 0)
                
                # Completion rate
                if ai_insights.get('conversation_completion_status') in ['completed', 'closing']:
                    completed_conversations += 1
            
            analytics.update({
                'average_conversation_quality': sum(quality_scores) / len(quality_scores) if quality_scores else 0.0,
                'total_objections_handled': total_objections,
                'total_interests_generated': total_interests,
                'rag_knowledge_utilization': total_rag_usage,
                'conversation_completion_rate': (completed_conversations / len(loop_results)) * 100 if loop_results else 0.0
            })
        
        return analytics

def test_smart_telecaller_orchestrator():
    """Test the smart telecaller orchestrator"""
    print("🧪 Testing Smart Telecaller Orchestrator with LangGraph and RAG")
    print("=" * 70)
    
    # Mock dependencies for testing
    from app.database.embedded_db import EmbeddedDatabase
    from app.services.twilio_service import TwilioService
    
    # Initialize services
    embedded_db = EmbeddedDatabase()
    twilio_service = TwilioService()
    
    # Initialize smart orchestrator (without OpenAI key for testing)
    orchestrator = SmartTelecallerOrchestrator(
        db_queries=embedded_db,
        twilio_service=twilio_service,
        openai_api_key=None  # Will use mock LLM
    )
    
    print("✅ Smart Telecaller Orchestrator initialized")
    
    # Test the smart campaign loop
    result = orchestrator.execute_smart_campaign_loop(job_id=1)
    
    print(f"\n📊 Smart Campaign Results:")
    print(f"✅ Success: {result['success']}")
    print(f"📞 Total Calls: {result['total_rows']}")
    print(f"✅ Successful: {result['successful_calls']}")
    print(f"🤖 AI Enhancement: {result['execution_summary']['ai_enhancement']}")
    print(f"📚 RAG Knowledge Base: {result['execution_summary']['rag_knowledge_base']}")
    
    if result.get('ai_analytics'):
        analytics = result['ai_analytics']
        print(f"\n🧠 AI Analytics:")
        print(f"   Average Conversation Quality: {analytics['average_conversation_quality']:.1f}/100")
        print(f"   Total Objections Handled: {analytics['total_objections_handled']}")
        print(f"   RAG Knowledge Utilization: {analytics['rag_knowledge_utilization']} items")
        print(f"   Conversation Completion Rate: {analytics['conversation_completion_rate']:.1f}%")
    
    print(f"\n🎉 Smart Telecaller test {'PASSED' if result['success'] else 'FAILED'}!")
    
    return result['success']

if __name__ == "__main__":
    test_smart_telecaller_orchestrator()
