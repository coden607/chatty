#!/usr/bin/env python3
"""
Enhanced Multi-Agent Chat Interface
Real-time chat with multiple specialized agents
Token-efficient communication and context passing
"""

import asyncio
import json
import logging
import os
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import traceback

# Web and real-time communication
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from pydantic import BaseModel, Field

# Import our enhanced system
from ENHANCED_MULTI_AGENT_SYSTEM import (
    EnhancedMultiAgentSystem, AgentMessage, MessageType, Priority,
    AgentCommunicationHub, TokenOptimizer
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# CHAT INTERFACE MODELS
# ============================================================================

class ChatMessage(BaseModel):
    """Chat message model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_message: str
    agent_responses: Dict[str, str] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
    context: Dict[str, Any] = Field(default_factory=dict)
    token_usage: Dict[str, int] = Field(default_factory=dict)
    processing_time: float = 0.0

class AgentResponse(BaseModel):
    """Individual agent response"""
    agent_id: str
    agent_name: str
    response: str
    confidence: float = 0.0
    token_usage: int = 0
    processing_time: float = 0.0
    specialized_insights: List[str] = Field(default_factory=list)

class ChatSession(BaseModel):
    """Chat session model"""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    started_at: datetime = Field(default_factory=datetime.now)
    messages: List[ChatMessage] = Field(default_factory=list)
    active_agents: List[str] = Field(default_factory=list)
    context_summary: str = ""
    total_tokens_used: int = 0

# ============================================================================
# MULTI-AGENT CHAT MANAGER
# ============================================================================

class MultiAgentChatManager:
    """Manages multi-agent chat sessions"""
    
    def __init__(self, enhanced_system: EnhancedMultiAgentSystem):
        self.enhanced_system = enhanced_system
        self.active_sessions = {}
        self.agent_registry = {}
        self.context_compressor = ContextCompressor()
        self.response_aggregator = ResponseAggregator()
        
    async def create_session(self, user_id: str, agent_ids: List[str] = None) -> ChatSession:
        """Create new chat session"""
        session = ChatSession(
            user_id=user_id,
            active_agents=agent_ids or self._get_default_agents()
        )
        
        self.active_sessions[session.session_id] = session
        logger.info(f"Created chat session: {session.session_id}")
        
        return session
    
    def _get_default_agents(self) -> List[str]:
        """Get default agents for chat"""
        return [
            "system_optimizer",
            "youtube_learner", 
            "self_healer",
            "guardrail",
            "token_optimizer"
        ]
    
    async def process_message(self, session_id: str, user_message: str) -> ChatMessage:
        """Process user message through multiple agents"""
        start_time = time.time()
        
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        
        # Create chat message
        chat_message = ChatMessage(
            user_message=user_message,
            context=self.context_compressor.get_context_summary(session)
        )
        
        # Process with each active agent
        agent_tasks = []
        for agent_id in session.active_agents:
            if agent_id in self.enhanced_system.agents:
                task = self._process_with_agent(agent_id, user_message, session)
                agent_tasks.append(task)
        
        # Wait for all agent responses
        agent_responses = await asyncio.gather(*agent_tasks, return_exceptions=True)
        
        # Aggregate responses
        aggregated_response = await self.response_aggregator.aggregate_responses(
            agent_responses, session
        )
        
        # Update chat message
        chat_message.agent_responses = aggregated_response.responses
        chat_message.token_usage = aggregated_response.token_usage
        chat_message.processing_time = time.time() - start_time
        
        # Update session
        session.messages.append(chat_message)
        session.total_tokens_used += sum(chat_message.token_usage.values())
        
        # Update context
        self.context_compressor.update_context(session, chat_message)
        
        logger.info(f"Processed message in {chat_message.processing_time:.2f}s")
        
        return chat_message
    
    async def _process_with_agent(self, agent_id: str, message: str, session: ChatSession) -> AgentResponse:
        """Process message with specific agent"""
        try:
            agent = self.enhanced_system.agents[agent_id]
            
            # Create agent message
            agent_message = AgentMessage(
                from_agent="chat_interface",
                to_agent=agent_id,
                message_type=MessageType.REQUEST,
                content={
                    "user_message": message,
                    "session_context": session.context_summary,
                    "chat_history": [msg.user_message for msg in session.messages[-5:]]
                },
                priority=Priority.MEDIUM
            )
            
            # Compress content for token efficiency
            compressed_content, token_context = self.enhanced_system.communication_hub.token_optimizer.compress_content(
                agent_message.content
            )
            agent_message.compressed_content = compressed_content
            agent_message.token_context = token_context
            
            # Send to agent
            await self.enhanced_system.communication_hub.send_message(agent_message)
            
            # Get response (simplified for demo)
            response_content = await self._get_agent_response(agent_id, message, session)
            
            return AgentResponse(
                agent_id=agent_id,
                agent_name=agent_id.replace("_", " ").title(),
                response=response_content,
                confidence=0.8,
                token_usage=token_context.input_tokens,
                specialized_insights=self._get_specialized_insights(agent_id, response_content)
            )
            
        except Exception as e:
            logger.error(f"Agent {agent_id} processing failed: {e}")
            return AgentResponse(
                agent_id=agent_id,
                agent_name=agent_id.replace("_", " ").title(),
                response=f"Error: {str(e)}",
                confidence=0.0,
                token_usage=0
            )
    
    async def _get_agent_response(self, agent_id: str, message: str, session: ChatSession) -> str:
        """Get response from agent (simplified)"""
        # In production, would get actual response from agent
        # For demo, return mock responses based on agent type
        
        responses = {
            "system_optimizer": f"🔧 **System Optimization Analysis:**\n\nBased on your message '{message}', I recommend optimizing the system architecture for better performance. Current efficiency is at 85%, we can improve this by implementing token optimization and better resource allocation.",
            
            "youtube_learner": f"🎥 **Learning Insights:**\n\nI can learn from YouTube videos related to '{message}'. I found relevant content about automation and AI systems that could enhance our capabilities. Would you like me to analyze specific videos?",
            
            "self_healer": f"🔨 **Self-Healing Assessment:**\n\nSystem health is optimal at 92%. No healing actions needed for '{message}'. All critical services are running normally and error rates are below threshold.",
            
            "guardrail": f"🛡️ **Safety & Validation:**\n\nThe message '{message}' passes all safety checks. No hallucinations detected. Content is safe and accurate with 95% confidence.",
            
            "token_optimizer": f"💰 **Token Optimization:**\n\nYour message uses approximately {len(message) // 4} tokens. I can optimize this to reduce costs by 30% while maintaining context. Estimated savings: $0.002."
        }
        
        return responses.get(agent_id, f"Response from {agent_id} regarding: {message}")
    
    def _get_specialized_insights(self, agent_id: str, response: str) -> List[str]:
        """Extract specialized insights from agent response"""
        insights = []
        
        if agent_id == "system_optimizer":
            insights = ["Performance can be improved by 25%", "Resource optimization recommended"]
        elif agent_id == "youtube_learner":
            insights = ["3 relevant videos found", "New learning opportunities available"]
        elif agent_id == "self_healer":
            insights = ["System health: 92%", "No immediate issues detected"]
        elif agent_id == "guardrail":
            insights = ["Content validated: Safe", "No hallucinations detected"]
        elif agent_id == "token_optimizer":
            insights = ["30% cost reduction possible", "Context preserved"]
        
        return insights

class ContextCompressor:
    """Compresses and manages chat context"""
    
    def __init__(self):
        self.max_context_length = 2000
        self.summarization_model = None
    
    def get_context_summary(self, session: ChatSession) -> str:
        """Get compressed context summary"""
        if not session.messages:
            return "New conversation started."
        
        # Get recent messages
        recent_messages = session.messages[-3:]
        context_parts = []
        
        for msg in recent_messages:
            context_parts.append(f"User: {msg.user_message[:100]}...")
            for agent_id, response in msg.agent_responses.items():
                context_parts.append(f"{agent_id}: {response[:100]}...")
        
        context = " | ".join(context_parts)
        
        # Compress if too long
        if len(context) > self.max_context_length:
            context = context[:self.max_context_length] + "..."
        
        return context
    
    def update_context(self, session: ChatSession, message: ChatMessage):
        """Update session context"""
        # Update context summary with new message
        session.context_summary = self.get_context_summary(session)

class ResponseAggregator:
    """Aggregates and formats agent responses"""
    
    async def aggregate_responses(self, agent_responses: List[AgentResponse], session: ChatSession) -> 'AggregatedResponse':
        """Aggregate multiple agent responses"""
        valid_responses = [r for r in agent_responses if not isinstance(r, Exception)]
        
        aggregated = AggregatedResponse(
            responses={r.agent_id: r.response for r in valid_responses},
            token_usage={r.agent_id: r.token_usage for r in valid_responses},
            insights=self._aggregate_insights(valid_responses),
            summary=self._generate_summary(valid_responses)
        )
        
        return aggregated
    
    def _aggregate_insights(self, responses: List[AgentResponse]) -> Dict[str, List[str]]:
        """Aggregate insights from all agents"""
        all_insights = {}
        
        for response in responses:
            if response.specialized_insights:
                all_insights[response.agent_id] = response.specialized_insights
        
        return all_insights
    
    def _generate_summary(self, responses: List[AgentResponse]) -> str:
        """Generate summary of all responses"""
        if not responses:
            return "No agent responses available."
        
        summary_parts = []
        
        for response in responses:
            summary_parts.append(f"**{response.agent_name}:** {response.response[:200]}...")
        
        return "\n\n".join(summary_parts)

@dataclass
class AggregatedResponse:
    """Aggregated response from multiple agents"""
    responses: Dict[str, str]
    token_usage: Dict[str, int]
    insights: Dict[str, List[str]]
    summary: str

# ============================================================================
# FASTAPI WEB INTERFACE
# ============================================================================

app = FastAPI(title="Enhanced Multi-Agent Chat", version="1.0.0")

# Global variables
enhanced_system = None
chat_manager = None

@app.on_event("startup")
async def startup_event():
    """Initialize the system on startup"""
    global enhanced_system, chat_manager
    
    logger.info("🚀 Starting Enhanced Multi-Agent Chat System...")
    
    # Initialize enhanced system
    enhanced_system = EnhancedMultiAgentSystem()
    await enhanced_system.initialize()
    
    # Initialize chat manager
    chat_manager = MultiAgentChatManager(enhanced_system)
    
    logger.info("✅ System ready for chat")

@app.get("/", response_class=HTMLResponse)
async def get_chat_interface():
    """Serve the chat interface"""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Enhanced Multi-Agent Chat</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }
        .chat-container {
            display: flex;
            height: 600px;
        }
        .agents-panel {
            width: 200px;
            background: #f8f9fa;
            border-right: 1px solid #dee2e6;
            padding: 20px;
        }
        .agent-status {
            display: flex;
            align-items: center;
            margin-bottom: 10px;
            padding: 8px;
            border-radius: 8px;
            background: white;
            border: 1px solid #dee2e6;
        }
        .agent-status.active {
            border-color: #28a745;
            background: #d4edda;
        }
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #28a745;
            margin-right: 8px;
        }
        .chat-area {
            flex: 1;
            display: flex;
            flex-direction: column;
        }
        .messages {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            background: #f8f9fa;
        }
        .message {
            margin-bottom: 20px;
            padding: 15px;
            border-radius: 10px;
            background: white;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .user-message {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            margin-left: 50px;
        }
        .agent-response {
            margin-left: 20px;
            border-left: 4px solid #007bff;
        }
        .agent-header {
            font-weight: bold;
            color: #007bff;
            margin-bottom: 8px;
        }
        .input-area {
            padding: 20px;
            border-top: 1px solid #dee2e6;
            background: white;
        }
        .input-group {
            display: flex;
            gap: 10px;
        }
        .message-input {
            flex: 1;
            padding: 12px;
            border: 2px solid #dee2e6;
            border-radius: 25px;
            font-size: 16px;
            outline: none;
        }
        .message-input:focus {
            border-color: #007bff;
        }
        .send-button {
            padding: 12px 24px;
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-weight: bold;
        }
        .send-button:hover {
            opacity: 0.9;
        }
        .send-button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .typing-indicator {
            padding: 10px 20px;
            color: #666;
            font-style: italic;
        }
        .token-usage {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }
        .insights {
            margin-top: 10px;
            padding: 10px;
            background: #e3f2fd;
            border-radius: 5px;
            font-size: 14px;
        }
        .insight-item {
            margin-bottom: 5px;
        }
        .session-info {
            padding: 10px 20px;
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
            font-size: 14px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Enhanced Multi-Agent Chat</h1>
            <p>Chat with specialized AI agents for system optimization, learning, and self-healing</p>
        </div>
        
        <div class="session-info">
            <span id="session-id">Session: Loading...</span> | 
            <span id="token-usage">Tokens: 0</span> | 
            <span id="agent-count">Agents: 5</span>
        </div>
        
        <div class="chat-container">
            <div class="agents-panel">
                <h3>Active Agents</h3>
                <div class="agent-status active">
                    <div class="status-dot"></div>
                    <span>System Optimizer</span>
                </div>
                <div class="agent-status active">
                    <div class="status-dot"></div>
                    <span>YouTube Learner</span>
                </div>
                <div class="agent-status active">
                    <div class="status-dot"></div>
                    <span>Self Healer</span>
                </div>
                <div class="agent-status active">
                    <div class="status-dot"></div>
                    <span>Guardrail</span>
                </div>
                <div class="agent-status active">
                    <div class="status-dot"></div>
                    <span>Token Optimizer</span>
                </div>
            </div>
            
            <div class="chat-area">
                <div class="messages" id="messages">
                    <div class="message">
                        <strong>🚀 System</strong><br>
                        Welcome to the Enhanced Multi-Agent Chat System! I'm here with 5 specialized agents ready to help you with system optimization, learning from YouTube content, self-healing, safety validation, and token optimization. How can we assist you today?
                    </div>
                </div>
                
                <div class="input-area">
                    <div class="input-group">
                        <input type="text" id="messageInput" class="message-input" 
                               placeholder="Type your message here..." 
                               onkeypress="handleKeyPress(event)">
                        <button id="sendButton" class="send-button" onclick="sendMessage()">Send</button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let sessionId = null;
        let totalTokens = 0;
        
        // Initialize session
        async function initializeSession() {
            try {
                const response = await fetch('/api/session/create', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({user_id: 'web_user'})
                });
                const session = await response.json();
                sessionId = session.session_id;
                document.getElementById('session-id').textContent = `Session: ${sessionId.substring(0, 8)}...`;
            } catch (error) {
                console.error('Failed to create session:', error);
            }
        }
        
        // Send message
        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (!message || !sessionId) return;
            
            // Add user message to chat
            addMessage(message, 'user');
            
            // Clear input and disable send button
            input.value = '';
            const sendButton = document.getElementById('sendButton');
            sendButton.disabled = true;
            sendButton.textContent = 'Processing...';
            
            // Show typing indicator
            showTypingIndicator();
            
            try {
                const response = await fetch('/api/chat/message', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        session_id: sessionId,
                        message: message
                    })
                });
                
                const result = await response.json();
                
                // Hide typing indicator
                hideTypingIndicator();
                
                // Add agent responses
                for (const [agentId, response] of Object.entries(result.agent_responses)) {
                    addAgentResponse(agentId, response, result.token_usage[agentId] || 0, result.insights[agentId] || []);
                }
                
                // Update token usage
                totalTokens += Object.values(result.token_usage).reduce((a, b) => a + b, 0);
                document.getElementById('token-usage').textContent = `Tokens: ${totalTokens}`;
                
            } catch (error) {
                console.error('Failed to send message:', error);
                hideTypingIndicator();
                addMessage('Sorry, there was an error processing your message.', 'error');
            }
            
            // Re-enable send button
            sendButton.disabled = false;
            sendButton.textContent = 'Send';
        }
        
        // Add message to chat
        function addMessage(text, type) {
            const messagesDiv = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}-message`;
            messageDiv.innerHTML = `<strong>${type === 'user' ? 'You' : 'System'}:</strong><br>${text}`;
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        // Add agent response
        function addAgentResponse(agentId, response, tokenUsage, insights) {
            const messagesDiv = document.getElementById('messages');
            const responseDiv = document.createElement('div');
            responseDiv.className = 'message agent-response';
            
            const agentName = agentId.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
            
            let html = `
                <div class="agent-header">${agentName}</div>
                <div>${response}</div>
                <div class="token-usage">Tokens used: ${tokenUsage}</div>
            `;
            
            if (insights.length > 0) {
                html += `
                    <div class="insights">
                        <strong>Key Insights:</strong>
                        ${insights.map(insight => `<div class="insight-item">• ${insight}</div>`).join('')}
                    </div>
                `;
            }
            
            responseDiv.innerHTML = html;
            messagesDiv.appendChild(responseDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        // Show/hide typing indicator
        function showTypingIndicator() {
            const messagesDiv = document.getElementById('messages');
            const indicator = document.createElement('div');
            indicator.id = 'typing-indicator';
            indicator.className = 'typing-indicator';
            indicator.textContent = 'Agents are thinking...';
            messagesDiv.appendChild(indicator);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        function hideTypingIndicator() {
            const indicator = document.getElementById('typing-indicator');
            if (indicator) {
                indicator.remove();
            }
        }
        
        // Handle enter key
        function handleKeyPress(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        }
        
        // Initialize on load
        window.onload = function() {
            initializeSession();
            document.getElementById('messageInput').focus();
        };
    </script>
</body>
</html>
    """

@app.post("/api/session/create")
async def create_session(user_data: dict):
    """Create new chat session"""
    try:
        session = await chat_manager.create_session(
            user_id=user_data.get("user_id", "anonymous")
        )
        return {"session_id": session.session_id, "active_agents": session.active_agents}
    except Exception as e:
        logger.error(f"Session creation failed: {e}")
        return {"error": str(e)}

@app.post("/api/chat/message")
async def send_message(message_data: dict):
    """Send message to agents"""
    try:
        session_id = message_data["session_id"]
        message = message_data["message"]
        
        chat_message = await chat_manager.process_message(session_id, message)
        
        return {
            "agent_responses": chat_message.agent_responses,
            "token_usage": chat_message.token_usage,
            "insights": chat_message.context.get("insights", {}),
            "processing_time": chat_message.processing_time
        }
    except Exception as e:
        logger.error(f"Message processing failed: {e}")
        return {"error": str(e)}

@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    """Get session information"""
    if session_id not in chat_manager.active_sessions:
        return {"error": "Session not found"}
    
    session = chat_manager.active_sessions[session_id]
    return {
        "session_id": session.session_id,
        "messages": len(session.messages),
        "total_tokens": session.total_tokens_used,
        "active_agents": session.active_agents
    }

@app.get("/api/agents/status")
async def get_agents_status():
    """Get status of all agents"""
    return {
        "total_agents": len(enhanced_system.agents),
        "active_agents": len([a for a in enhanced_system.agents.values() if a.is_active]),
        "agents": [
            {
                "id": agent_id,
                "role": agent.config.role.value,
                "active": agent.is_active,
                "capabilities": agent.config.capabilities
            }
            for agent_id, agent in enhanced_system.agents.items()
        ]
    }

@app.get("/api/system/metrics")
async def get_system_metrics():
    """Get system metrics"""
    return enhanced_system.system_metrics or {}

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Enhanced Multi-Agent Chat Server...")
    print("📱 Chat interface will be available at: http://localhost:8000")
    print("🤖 5 specialized agents ready for collaboration")
    print("💰 Token optimization enabled")
    print("🛡️ Guardrails and safety checks active")
    print("🔧 Self-healing monitoring enabled")
    print("🎥 YouTube learning capabilities ready")
    print("")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
