#!/usr/bin/env python3
"""
Chatty Conversational Interface
Natural language interface to interact with all enhanced agents as a team
"""

import os
import json
import time
import asyncio
import logging
import re
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from collections import defaultdict
import concurrent.futures

import requests
from pydantic import BaseModel, Field, validator
from sentence_transformers import SentenceTransformer
import networkx as nx
import numpy as np

from server import db, Agent, Task, logger
from learning_system import memory_system, adaptive_learning
from openclaw_integration import MultiLLMRouter

# Import all enhanced components
from enhanced_bmad_agent import enhanced_bmad_agent
from pydantic_n8n_engine import pydantic_n8n_engine
from youtube_learning_system import youtube_learning_system, advanced_scraper

# Import Chatty components
try:
    from SELF_IMPROVING_AGENTS import SelfImprovingAgentSystem
    from AUTOMATED_REVENUE_ENGINE import revenue_engine
    from AUTOMATED_CUSTOMER_ACQUISITION import acquisition_engine
    from INVESTOR_WORKFLOWS import InvestorWorkflows
    from TWITTER_AUTOMATION import twitter_automation
    from VIRAL_GROWTH_ENGINE import ViralGrowthEngine
    from ABSOLUTE_SYSTEM_ENHANCEMENTS import (
        initialize_absolute_enhancements,
        start_absolute_operations,
        get_absolute_system_status
    )
except ImportError as e:
    logger.error(f"Failed to import Chatty components: {e}")

class ConversationContext(BaseModel):
    """Context for ongoing conversations"""
    conversation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    session_start: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    active_agents: List[str] = Field(default_factory=list)
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    current_topic: Optional[str] = None
    pending_tasks: List[Dict[str, Any]] = Field(default_factory=list)
    user_preferences: Dict[str, Any] = Field(default_factory=dict)

class AgentResponse(BaseModel):
    """Response from an agent"""
    agent_name: str
    response: str
    confidence: float = Field(ge=0.0, le=1.0)
    action_taken: Optional[str] = None
    follow_up_questions: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class TaskAssignment(BaseModel):
    """Task assignment to agents"""
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_description: str
    assigned_agents: List[str]
    priority: str = Field(default="medium")  # low, medium, high, critical
    estimated_duration: Optional[int] = None  # in seconds
    dependencies: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="pending")  # pending, in_progress, completed, failed

class IntentClassifier:
    """Classify user intent for task routing"""
    
    def __init__(self):
        self.intent_patterns = {
            'code_analysis': [
                r'analyze.*code', r'check.*code', r'find.*bugs', r'code.*review',
                r'fix.*code', r'optimize.*code', r'security.*scan'
            ],
            'workflow': [
                r'create.*workflow', r'automate.*task', r'workflow.*optimization',
                r'business.*process', r'task.*automation'
            ],
            'learning': [
                r'learn.*from.*video', r'youtube.*learning', r'extract.*insights',
                r'video.*analysis', r'content.*learning'
            ],
            'scraping': [
                r'scrape.*website', r'analyze.*website', r'extract.*content',
                r'web.*analysis', r'content.*extraction'
            ],
            'revenue': [
                r'generate.*revenue', r'business.*automation', r'optimize.*sales',
                r'customer.*management', r'revenue.*growth'
            ],
            'acquisition': [
                r'acquire.*customers', r'marketing.*campaign', r'lead.*generation',
                r'customer.*acquisition', r'growth.*marketing'
            ],
            'investor': [
                r'investor.*update', r'funding.*campaign', r'pitch.*deck',
                r'investor.*relations', r'funding.*round'
            ],
            'social': [
                r'social.*media', r'twitter.*post', r'content.*sharing',
                r'share.*content', r'social.*engagement'
            ],
            'viral': [
                r'viral.*marketing', r'growth.*hacking', r'viral.*content',
                r'optimize.*reach', r'maximize.*engagement'
            ],
            'general': [
                r'help.*me', r'what.*can.*you.*do', r'capabilities', r'features'
            ]
        }
    
    async def classify_intent(self, message: str) -> Dict[str, Any]:
        """Classify user intent from message"""
        message_lower = message.lower()
        
        for intent_type, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    return {
                        'intent': intent_type,
                        'confidence': 0.8,
                        'topic': self._extract_topic(message),
                        'entities': self._extract_entities(message)
                    }
        
        return {
            'intent': 'general',
            'confidence': 0.5,
            'topic': 'general',
            'entities': []
        }
    
    def _extract_topic(self, message: str) -> str:
        """Extract main topic from message"""
        # Simple topic extraction
        topics = ['code', 'workflow', 'learning', 'scraping', 'revenue', 'acquisition', 'investor', 'social', 'viral']
        message_lower = message.lower()
        
        for topic in topics:
            if topic in message_lower:
                return topic
        
        return 'general'
    
    def _extract_entities(self, message: str) -> List[str]:
        """Extract entities from message"""
        entities = []
        
        # Extract URLs
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, message)
        entities.extend(urls)
        
        # Extract file paths
        file_pattern = r'["\']([^"\']*\.(py|js|html|css|json))["\']'
        files = re.findall(file_pattern, message)
        entities.extend(files)
        
        # Extract YouTube URLs
        youtube_pattern = r'(?:youtube\.com/watch\?v=|youtu\.be/)([^&\n?#]+)'
        youtube_matches = re.findall(youtube_pattern, message)
        for match in youtube_matches:
            entities.append(f"https://www.youtube.com/watch?v={match}")
        
        return entities

class TaskRouter:
    """Route tasks to appropriate agents"""
    
    def __init__(self):
        self.agent_capabilities = {
            'bmad': ['code_analysis', 'security_scanning', 'performance_optimization', 'auto_fixes'],
            'n8n': ['workflow_management', 'self_optimization', 'task_execution', 'performance_monitoring'],
            'youtube': ['video_analysis', 'transcript_processing', 'content_generation', 'knowledge_integration'],
            'scraper': ['content_extraction', 'semantic_analysis', 'insight_generation', 'quality_assessment'],
            'revenue': ['revenue_generation', 'business_automation', 'customer_management'],
            'acquisition': ['customer_acquisition', 'marketing_automation', 'lead_generation'],
            'investor': ['investor_management', 'funding_campaigns', 'reporting'],
            'twitter': ['social_media', 'content_sharing', 'engagement'],
            'viral': ['viral_marketing', 'growth_hacking', 'content_optimization']
        }
    
    async def route_task(self, message: str, intent: Dict[str, Any], 
                        conversation: ConversationContext) -> TaskAssignment:
        """Route task to appropriate agents based on intent"""
        intent_type = intent['intent']
        entities = intent.get('entities', [])
        
        # Determine which agents can handle this intent
        suitable_agents = []
        
        for agent_name, capabilities in self.agent_capabilities.items():
            if intent_type in capabilities:
                suitable_agents.append(agent_name)
        
        # If no specific agents found, use general agents
        if not suitable_agents:
            suitable_agents = ['bmad', 'n8n', 'youtube']  # Default agents
        
        # Determine priority based on message urgency
        priority = self._determine_priority(message)
        
        # Create task assignment
        task = TaskAssignment(
            task_description=message,
            assigned_agents=suitable_agents,
            priority=priority,
            dependencies=[]
        )
        
        return task
    
    def _determine_priority(self, message: str) -> str:
        """Determine task priority based on message content"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['urgent', 'immediately', 'asap', 'critical', 'emergency']):
            return 'critical'
        elif any(word in message_lower for word in ['important', 'need', 'required', 'must']):
            return 'high'
        elif any(word in message_lower for word in ['please', 'would like', 'could you']):
            return 'medium'
        else:
            return 'low'

class ResponseGenerator:
    """Generate consolidated responses from multiple agents"""
    
    def __init__(self):
        self.multi_llm_router = MultiLLMRouter()
    
    async def generate_response(self, user_message: str, responses: List[AgentResponse], 
                              conversation: ConversationContext) -> str:
        """Generate consolidated response from agent responses"""
        if not responses:
            return "I'm sorry, but none of the agents were able to process your request. Could you please rephrase or provide more details?"
        
        # Group responses by agent
        agent_responses = {}
        for response in responses:
            agent_responses[response.agent_name] = response
        
        # Generate consolidated response
        consolidated_text = self._create_consolidated_response(agent_responses, user_message)
        
        # Add follow-up suggestions
        follow_up = self._generate_follow_up_suggestions(agent_responses, user_message)
        
        return f"{consolidated_text}\n\n{follow_up}"
    
    def _create_consolidated_response(self, agent_responses: Dict[str, AgentResponse], 
                                    user_message: str) -> str:
        """Create a consolidated response from multiple agent responses"""
        if len(agent_responses) == 1:
            # Single agent response
            agent_name, response = list(agent_responses.items())[0]
            return f"**{agent_name}**: {response.response}"
        
        # Multiple agent responses
        response_text = "Here's what our team found:\n\n"
        
        for agent_name, response in agent_responses.items():
            response_text += f"**{agent_name}**: {response.response}\n\n"
        
        return response_text
    
    def _generate_follow_up_suggestions(self, agent_responses: Dict[str, AgentResponse], 
                                      user_message: str) -> str:
        """Generate follow-up suggestions based on agent responses"""
        suggestions = []
        
        for response in agent_responses.values():
            suggestions.extend(response.follow_up_questions)
        
        if suggestions:
            return f"**Follow-up suggestions:**\n{chr(10).join([f"• {suggestion}" for suggestion in suggestions[:3]])}"
        
        return "Is there anything else I can help you with?"

class ChattyConversationalInterface:
    """Natural language interface to interact with Chatty's team of agents"""
    
    def __init__(self):
        self.name = "Chatty Conversational Interface"
        self.version = "1.0.0"
        
        # Agent registry
        self.agents = {}
        self.agent_descriptions = {}
        
        # Conversation management
        self.active_conversations: Dict[str, ConversationContext] = {}
        self.user_sessions: Dict[str, str] = {}  # user_id -> conversation_id
        
        # Task management
        self.active_tasks: Dict[str, TaskAssignment] = {}
        self.task_results: Dict[str, List[AgentResponse]] = {}
        
        # AI components
        self.intent_classifier = IntentClassifier()
        self.task_router = TaskRouter()
        self.response_generator = ResponseGenerator()
        
        # Configuration
        self.max_concurrent_tasks = 10
        self.response_timeout = 30  # seconds
        self.conversation_timeout = 3600  # 1 hour
        
        # Initialize all agents
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize all available agents"""
        # Enhanced BMAD Agent
        self.agents['bmad'] = enhanced_bmad_agent
        self.agent_descriptions['bmad'] = {
            'name': 'Enhanced BMAD Agent',
            'capabilities': ['code_analysis', 'security_scanning', 'performance_optimization', 'auto_fixes'],
            'description': 'AI-powered bug management and detection agent for code analysis and optimization'
        }
        
        # Pydantic AI n8n Engine
        self.agents['n8n'] = pydantic_n8n_engine
        self.agent_descriptions['n8n'] = {
            'name': 'Pydantic AI n8n Engine',
            'capabilities': ['workflow_management', 'self_optimization', 'task_execution', 'performance_monitoring'],
            'description': 'Self-optimizing workflow management system with Pydantic validation'
        }
        
        # YouTube Learning System
        self.agents['youtube'] = youtube_learning_system
        self.agent_descriptions['youtube'] = {
            'name': 'YouTube Learning System',
            'capabilities': ['video_analysis', 'transcript_processing', 'content_generation', 'knowledge_integration'],
            'description': 'Video-based learning and content generation system'
        }
        
        # Advanced Website Scraper
        self.agents['scraper'] = advanced_scraper
        self.agent_descriptions['scraper'] = {
            'name': 'Advanced Website Scraper',
            'capabilities': ['content_extraction', 'semantic_analysis', 'insight_generation', 'quality_assessment'],
            'description': 'Semantic web content analysis and actionable insight generation'
        }
        
        # Chatty Core Agents
        try:
            self.agents['revenue'] = revenue_engine
            self.agent_descriptions['revenue'] = {
                'name': 'Revenue Engine',
                'capabilities': ['revenue_generation', 'business_automation', 'customer_management'],
                'description': 'Automated revenue generation and business process optimization'
            }
            
            self.agents['acquisition'] = acquisition_engine
            self.agent_descriptions['acquisition'] = {
                'name': 'Customer Acquisition Engine',
                'capabilities': ['customer_acquisition', 'marketing_automation', 'lead_generation'],
                'description': 'Automated customer acquisition and marketing campaign management'
            }
            
            self.agents['investor'] = InvestorWorkflows()
            self.agent_descriptions['investor'] = {
                'name': 'Investor Workflows',
                'capabilities': ['investor_management', 'funding_campaigns', 'reporting'],
                'description': 'Investor relations and funding campaign automation'
            }
            
            self.agents['twitter'] = twitter_automation
            self.agent_descriptions['twitter'] = {
                'name': 'Twitter/X Automation',
                'capabilities': ['social_media', 'content_sharing', 'engagement'],
                'description': 'Automated social media management and content sharing'
            }
            
            self.agents['viral'] = ViralGrowthEngine(revenue_engine)
            self.agent_descriptions['viral'] = {
                'name': 'Viral Growth Engine',
                'capabilities': ['viral_marketing', 'growth_hacking', 'content_optimization'],
                'description': 'Viral marketing and growth optimization engine'
            }
            
        except Exception as e:
            logger.warning(f"Failed to initialize some Chatty agents: {e}")
    
    async def process_user_message(self, user_id: str, message: str) -> Dict[str, Any]:
        """Process a user message and return responses from relevant agents"""
        try:
            # Get or create conversation context
            conversation = self._get_or_create_conversation(user_id)
            conversation.last_activity = datetime.utcnow()
            
            # Add user message to history
            conversation.conversation_history.append({
                'role': 'user',
                'content': message,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            # Classify intent
            intent = await self.intent_classifier.classify_intent(message)
            
            # Route task to appropriate agents
            task_assignment = await self.task_router.route_task(message, intent, conversation)
            
            # Execute task with assigned agents
            responses = await self._execute_task(task_assignment, conversation)
            
            # Generate consolidated response
            consolidated_response = await self.response_generator.generate_response(
                message, responses, conversation
            )
            
            # Update conversation context
            conversation.current_topic = intent.get('topic', 'general')
            conversation.active_agents = task_assignment.assigned_agents
            
            # Add system response to history
            conversation.conversation_history.append({
                'role': 'system',
                'content': consolidated_response,
                'timestamp': datetime.utcnow().isoformat(),
                'agents_responded': [r.agent_name for r in responses]
            })
            
            return {
                'success': True,
                'response': consolidated_response,
                'agents_responded': [r.agent_name for r in responses],
                'task_id': task_assignment.task_id,
                'intent': intent,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing user message: {str(e)}")
            return {
                'success': False,
                'response': f"Sorry, I encountered an error: {str(e)}",
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def _get_or_create_conversation(self, user_id: str) -> ConversationContext:
        """Get existing conversation or create new one"""
        if user_id in self.user_sessions:
            conversation_id = self.user_sessions[user_id]
            conversation = self.active_conversations[conversation_id]
            
            # Check if conversation is still active
            if (datetime.utcnow() - conversation.last_activity).total_seconds() > self.conversation_timeout:
                # Create new conversation
                conversation = ConversationContext(user_id=user_id)
                self.active_conversations[conversation.conversation_id] = conversation
                self.user_sessions[user_id] = conversation.conversation_id
        else:
            # Create new conversation
            conversation = ConversationContext(user_id=user_id)
            self.active_conversations[conversation.conversation_id] = conversation
            self.user_sessions[user_id] = conversation.conversation_id
        
        return conversation
    
    async def _execute_task(self, task: TaskAssignment, conversation: ConversationContext) -> List[AgentResponse]:
        """Execute task with assigned agents"""
        responses = []
        
        # Execute with each assigned agent
        for agent_name in task.assigned_agents:
            try:
                agent = self.agents.get(agent_name)
                if agent:
                    # Get agent-specific response
                    agent_response = await self._get_agent_response(agent, agent_name, task.task_description, conversation)
                    responses.append(agent_response)
                else:
                    responses.append(AgentResponse(
                        agent_name=agent_name,
                        response=f"Agent {agent_name} is not available",
                        confidence=0.0
                    ))
            except Exception as e:
                responses.append(AgentResponse(
                    agent_name=agent_name,
                    response=f"Error with agent {agent_name}: {str(e)}",
                    confidence=0.0
                ))
        
        # Store task results
        self.task_results[task.task_id] = responses
        
        return responses
    
    async def _get_agent_response(self, agent, agent_name: str, task_description: str, 
                                conversation: ConversationContext) -> AgentResponse:
        """Get response from a specific agent"""
        try:
            # Route to appropriate agent method based on agent type
            if agent_name == 'bmad':
                return await self._handle_bmad_request(agent, task_description, conversation)
            elif agent_name == 'n8n':
                return await self._handle_n8n_request(agent, task_description, conversation)
            elif agent_name == 'youtube':
                return await self._handle_youtube_request(agent, task_description, conversation)
            elif agent_name == 'scraper':
                return await self._handle_scraper_request(agent, task_description, conversation)
            elif agent_name in ['revenue', 'acquisition', 'investor', 'twitter', 'viral']:
                return await self._handle_chatty_agent_request(agent, agent_name, task_description, conversation)
            else:
                return AgentResponse(
                    agent_name=agent_name,
                    response=f"Unknown agent type: {agent_name}",
                    confidence=0.5
                )
                
        except Exception as e:
            return AgentResponse(
                agent_name=agent_name,
                                         conversation: ConversationContext) -> AgentResponse:
        """Handle request to Chatty core agents"""
        try:
            # Route to appropriate Chatty agent method
            if agent_name == 'revenue':
                return await self._handle_revenue_request(agent, task_description, conversation)
            elif agent_name == 'acquisition':
                return await self._handle_acquisition_request(agent, task_description, conversation)
            elif agent_name == 'investor':
                return await self._handle_investor_request(agent, task_description, conversation)
            elif agent_name == 'twitter':
                return await self._handle_twitter_request(agent, task_description, conversation)
            elif agent_name == 'viral':
                return await self._handle_viral_request(agent, task_description, conversation)
            else:
                return AgentResponse(
                    agent_name=agent_name,
                    response=f"Chatty agent {agent_name} is available but needs specific task details.",
                    confidence=0.7
                )
                
        except Exception as e:
            return AgentResponse(
                agent_name=agent_name,
                response=f"Chatty agent {agent_name} failed: {str(e)}",
                confidence=0.3
            )
    
    async def _handle_revenue_request(self, agent, task_description: str, 
                                    conversation: ConversationContext) -> AgentResponse:
        """Handle revenue engine request"""
        # This would integrate with the actual revenue engine
        return AgentResponse(
            agent_name='Revenue Engine',
            response="Revenue engine is ready to optimize your business automation and revenue generation. Please specify what revenue-related task you need help with.",
            confidence=0.8,
            follow_up_questions=['Would you like to analyze current revenue streams?', 'Should I optimize pricing strategies?', 'Need help with customer retention?']
        )
    
    async def _handle_acquisition_request(self, agent, task_description: str, 
                                        conversation: ConversationContext) -> AgentResponse:
        """Handle customer acquisition request"""
        # This would integrate with the actual acquisition engine
        return AgentResponse(
            agent_name='Customer Acquisition Engine',
            response="Customer acquisition engine is ready to help grow your customer base. Please specify what acquisition strategy you need.",
            confidence=0.8,
            follow_up_questions=['Would you like to create a new marketing campaign?', 'Should I analyze your target audience?', 'Need help with lead generation?']
        )
    
    async def _handle_investor_request(self, agent, task_description: str, 
                                     conversation: ConversationContext) -> AgentResponse:
        """Handle investor workflows request"""
        # This would integrate with the actual investor workflows
        return AgentResponse(
            agent_name='Investor Workflows',
            response="Investor workflows system is ready to manage your funding campaigns and investor relations. Please specify what investor-related task you need.",
            confidence=0.8,
            follow_up_questions=['Would you like to create an investor update?', 'Should I prepare funding materials?', 'Need help with investor outreach?']
        )
    
    async def _handle_twitter_request(self, agent, task_description: str, 
                                    conversation: ConversationContext) -> AgentResponse:
        """Handle Twitter automation request"""
        # This would integrate with the actual Twitter automation
        return AgentResponse(
            agent_name='Twitter/X Automation',
            response="Twitter automation is ready to manage your social media presence. Please specify what content you'd like to share or what social media task you need.",
            confidence=0.8,
            follow_up_questions=['Would you like to schedule posts?', 'Should I analyze engagement metrics?', 'Need help with content strategy?']
        )
    
    async def _handle_viral_request(self, agent, task_description: str, 
                                  conversation: ConversationContext) -> AgentResponse:
        """Handle viral growth request"""
        # This would integrate with the actual viral growth engine
        return AgentResponse(
            agent_name='Viral Growth Engine',
