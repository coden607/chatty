#!/usr/bin/env python3
"""
CHATTY A2A (Agent-to-Agent) Protocol Integration
Google's open standard for horizontal agent communication
Enables agents to discover, collaborate, and delegate across organizational boundaries
"""

import asyncio
import json
import logging
import uuid
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import httpx

logger = logging.getLogger(__name__)


class TaskState(Enum):
    """A2A Task states"""
    SUBMITTED = "submitted"
    WORKING = "working"
    INPUT_REQUIRED = "input-required"
    COMPLETED = "completed"
    CANCELED = "canceled"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass
class AgentCard:
    """
    A2A Agent Card - Discovery metadata for an agent
    Published by each agent for others to discover
    """
    name: str
    description: str
    url: str
    provider: Dict[str, str] = field(default_factory=dict)
    version: str = "1.0.0"
    documentation_url: str = ""
    capabilities: Dict[str, Any] = field(default_factory=dict)
    authentication: Dict[str, Any] = field(default_factory=dict)
    default_input_modes: List[str] = field(default_factory=lambda: ["text"])
    default_output_modes: List[str] = field(default_factory=lambda: ["text"])
    skills: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "url": self.url,
            "provider": self.provider,
            "version": self.version,
            "documentationUrl": self.documentation_url,
            "capabilities": self.capabilities,
            "authentication": self.authentication,
            "defaultInputModes": self.default_input_modes,
            "defaultOutput_modes": self.default_output_modes,
            "skills": self.skills
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentCard":
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            url=data.get("url", ""),
            provider=data.get("provider", {}),
            version=data.get("version", "1.0.0"),
            documentation_url=data.get("documentationUrl", ""),
            capabilities=data.get("capabilities", {}),
            authentication=data.get("authentication", {}),
            default_input_modes=data.get("defaultInputModes", ["text"]),
            default_output_modes=data.get("defaultOutputModes", ["text"]),
            skills=data.get("skills", [])
        )


@dataclass
class Message:
    """A2A Message - Communication between agents"""
    role: str  # user, agent
    parts: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def text(cls, content: str, role: str = "user") -> "Message":
        """Create a text message"""
        return cls(
            role=role,
            parts=[{"type": "text", "text": content}]
        )
    
    @classmethod
    def file(cls, file_path: str, mime_type: str = None, role: str = "user") -> "Message":
        """Create a file message"""
        return cls(
            role=role,
            parts=[{
                "type": "file",
                "file": {
                    "path": file_path,
                    "mimeType": mime_type or "application/octet-stream"
                }
            }]
        )
    
    @classmethod
    def data(cls, data: Dict[str, Any], role: str = "user") -> "Message":
        """Create a structured data message"""
        return cls(
            role=role,
            parts=[{"type": "data", "data": data}]
        )


@dataclass
class Task:
    """A2A Task - Unit of work assigned to an agent"""
    id: str
    session_id: str
    status: TaskState
    history: List[Message] = field(default_factory=list)
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "sessionId": self.session_id,
            "status": self.status.value,
            "history": [asdict(m) for m in self.history],
            "artifacts": self.artifacts,
            "metadata": self.metadata,
            "createdAt": self.created_at
        }


@dataclass
class TaskStatusUpdate:
    """A2A Task status update event"""
    id: str
    status: TaskState
    message: Optional[Message] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class A2AAgent:
    """
    A2A-compatible agent base class
    Can participate in A2A ecosystem
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        base_url: str,
        provider_name: str = "CHATTY",
        provider_url: str = "https://github.com/chatty"
    ):
        self.name = name
        self.description = description
        self.base_url = base_url.rstrip("/")
        self.provider_name = provider_name
        self.provider_url = provider_url
        
        # Agent capabilities
        self.capabilities = {
            "streaming": True,
            "pushNotifications": False,
            "stateTransitionCallback": True
        }
        
        # Skills this agent offers
        self.skills: List[Dict[str, Any]] = []
        
        # Active tasks
        self.tasks: Dict[str, Task] = {}
        
        # Handlers
        self._message_handler: Optional[Callable] = None
        self._task_handler: Optional[Callable] = None
        
    @property
    def agent_card(self) -> AgentCard:
        """Generate agent card for discovery"""
        return AgentCard(
            name=self.name,
            description=self.description,
            url=f"{self.base_url}/a2a",
            provider={
                "name": self.provider_name,
                "url": self.provider_url
            },
            capabilities=self.capabilities,
            skills=self.skills
        )
    
    def add_skill(
        self,
        id: str,
        name: str,
        description: str,
        tags: List[str] = None,
        examples: List[str] = None
    ):
        """Add a skill to this agent"""
        self.skills.append({
            "id": id,
            "name": name,
            "description": description,
            "tags": tags or [],
            "examples": examples or []
        })
    
    async def send_task(
        self,
        remote_agent_url: str,
        message: Message,
        session_id: str = None,
        metadata: Dict[str, Any] = None
    ) -> Task:
        """Send a task to a remote agent"""
        task_id = str(uuid.uuid4())
        session_id = session_id or str(uuid.uuid4())
        
        payload = {
            "id": task_id,
            "sessionId": session_id,
            "message": {
                "role": message.role,
                "parts": message.parts
            },
            "metadata": metadata or {}
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{remote_agent_url}/tasks/send",
                json=payload,
                timeout=120.0
            )
            response.raise_for_status()
            
            data = response.json()
            return Task(
                id=data["id"],
                session_id=data["sessionId"],
                status=TaskState(data.get("status", "submitted")),
                history=[Message(**m) for m in data.get("history", [])],
                artifacts=data.get("artifacts", [])
            )
    
    async def send_task_subscribe(
        self,
        remote_agent_url: str,
        message: Message,
        session_id: str = None
    ) -> AsyncGenerator[TaskStatusUpdate, None]:
        """Send a task and subscribe to streaming updates (SSE)"""
        task_id = str(uuid.uuid4())
        session_id = session_id or str(uuid.uuid4())
        
        payload = {
            "id": task_id,
            "sessionId": session_id,
            "message": {
                "role": message.role,
                "parts": message.parts
            }
        }
        
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{remote_agent_url}/tasks/sendSubscribe",
                json=payload,
                timeout=300.0
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = json.loads(line[6:])
                        yield TaskStatusUpdate(
                            id=data.get("id"),
                            status=TaskState(data.get("status", "unknown")),
                            message=Message(**data.get("message")) if "message" in data else None
                        )
    
    async def get_task(self, remote_agent_url: str, task_id: str) -> Task:
        """Get task status from remote agent"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{remote_agent_url}/tasks/{task_id}",
                timeout=30.0
            )
            response.raise_for_status()
            
            data = response.json()
            return Task(
                id=data["id"],
                session_id=data["sessionId"],
                status=TaskState(data.get("status", "unknown")),
                history=[Message(**m) for m in data.get("history", [])],
                artifacts=data.get("artifacts", [])
            )
    
    async def cancel_task(self, remote_agent_url: str, task_id: str) -> Task:
        """Cancel a task on remote agent"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{remote_agent_url}/tasks/{task_id}/cancel",
                timeout=30.0
            )
            response.raise_for_status()
            
            data = response.json()
            return Task(
                id=data["id"],
                session_id=data["sessionId"],
                status=TaskState(data.get("status", "canceled"))
            )
    
    def on_message(self, handler: Callable[[Message], None]):
        """Register message handler"""
        self._message_handler = handler
    
    def on_task(self, handler: Callable[[Task], Task]):
        """Register task handler"""
        self._task_handler = handler
    
    async def handle_task(self, task: Task) -> Task:
        """Override this to handle incoming tasks"""
        if self._task_handler:
            return await asyncio.to_thread(self._task_handler, task)
        
        # Default implementation
        task.status = TaskState.COMPLETED
        task.history.append(Message.text(f"Task {task.id} processed by {self.name}"))
        return task


class A2AFleet:
    """
    Fleet of A2A agents working together
    Manages discovery and collaboration
    """
    
    def __init__(self):
        self.agents: Dict[str, A2AAgent] = {}
        self.remote_agents: Dict[str, AgentCard] = {}
        
    def register_agent(self, agent: A2AAgent):
        """Register a local agent"""
        self.agents[agent.name] = agent
        logger.info(f"✅ Registered A2A agent: {agent.name}")
    
    async def discover_agent(self, agent_url: str) -> Optional[AgentCard]:
        """Discover an agent at a URL"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{agent_url}/.well-known/agent.json",
                    timeout=30.0
                )
                response.raise_for_status()
                
                card = AgentCard.from_dict(response.json())
                self.remote_agents[card.name] = card
                logger.info(f"🔍 Discovered agent: {card.name}")
                return card
                
        except Exception as e:
            logger.error(f"❌ Failed to discover agent at {agent_url}: {e}")
            return None
    
    async def delegate_task(
        self,
        task_description: str,
        required_skill: str = None,
        preferred_agent: str = None
    ) -> Optional[Task]:
        """
        Delegate a task to the best available agent
        """
        # Find suitable agent
        candidates = []
        
        if preferred_agent and preferred_agent in self.remote_agents:
            candidates.append(self.remote_agents[preferred_agent])
        
        if required_skill:
            for card in self.remote_agents.values():
                if any(skill.get("id") == required_skill for skill in card.skills):
                    candidates.append(card)
        
        if not candidates and self.remote_agents:
            candidates = list(self.remote_agents.values())
        
        if not candidates:
            logger.warning("❌ No suitable A2A agent found for task")
            return None
        
        # Try agents in order
        for card in candidates:
            try:
                agent = A2AAgent(card.name, card.description, card.url)
                task = await agent.send_task(
                    card.url,
                    Message.text(task_description)
                )
                logger.info(f"✅ Task delegated to {card.name}: {task.id}")
                return task
            except Exception as e:
                logger.warning(f"⚠️ Failed to delegate to {card.name}: {e}")
                continue
        
        return None
    
    def get_agent_capabilities(self) -> Dict[str, List[str]]:
        """Get capabilities of all known agents"""
        capabilities = {}
        
        for name, agent in self.agents.items():
            capabilities[name] = [s["id"] for s in agent.skills]
        
        for name, card in self.remote_agents.items():
            capabilities[name] = [s["id"] for s in card.skills]
        
        return capabilities


# Pre-configured A2A agents for CHATTY
class ChattyA2AAgents:
    """Factory for CHATTY's A2A agent network"""
    
    @staticmethod
    def revenue_agent(base_url: str) -> A2AAgent:
        """Revenue optimization agent"""
        agent = A2AAgent(
            name="chatty-revenue-agent",
            description="Optimizes pricing, revenue streams, and financial operations",
            base_url=base_url
        )
        agent.add_skill(
            id="pricing_optimization",
            name="Pricing Optimization",
            description="Optimize product/service pricing for maximum revenue",
            tags=["revenue", "pricing", "finance"]
        )
        agent.add_skill(
            id="revenue_forecast",
            name="Revenue Forecasting",
            description="Forecast revenue based on historical data and trends",
            tags=["revenue", "forecasting", "analytics"]
        )
        return agent
    
    @staticmethod
    def acquisition_agent(base_url: str) -> A2AAgent:
        """Customer acquisition agent"""
        agent = A2AAgent(
            name="chatty-acquisition-agent",
            description="Manages lead generation and customer acquisition",
            base_url=base_url
        )
        agent.add_skill(
            id="lead_generation",
            name="Lead Generation",
            description="Discover and qualify new leads",
            tags=["acquisition", "leads", "outreach"]
        )
        agent.add_skill(
            id="campaign_optimization",
            name="Campaign Optimization",
            description="Optimize marketing campaigns for conversion",
            tags=["acquisition", "marketing", "optimization"]
        )
        return agent
    
    @staticmethod
    def content_agent(base_url: str) -> A2AAgent:
        """Content generation agent"""
        agent = A2AAgent(
            name="chatty-content-agent",
            description="Creates SEO-optimized content and marketing materials",
            base_url=base_url
        )
        agent.add_skill(
            id="seo_content",
            name="SEO Content Creation",
            description="Generate SEO-optimized blog posts and articles",
            tags=["content", "seo", "writing"]
        )
        agent.add_skill(
            id="social_content",
            name="Social Media Content",
            description="Create engaging social media posts",
            tags=["content", "social", "marketing"]
        )
        return agent
    
    @staticmethod
    def research_agent(base_url: str) -> A2AAgent:
        """Research and analysis agent"""
        agent = A2AAgent(
            name="chatty-research-agent",
            description="Conducts market research and competitive analysis",
            base_url=base_url
        )
        agent.add_skill(
            id="market_research",
            name="Market Research",
            description="Analyze market trends and opportunities",
            tags=["research", "analysis", "market"]
        )
        agent.add_skill(
            id="competitive_analysis",
            name="Competitive Analysis",
            description="Analyze competitors and their strategies",
            tags=["research", "competitive", "analysis"]
        )
        return agent


# Global A2A fleet instance
_a2a_fleet: Optional[A2AFleet] = None


async def get_a2a_fleet() -> A2AFleet:
    """Get or create global A2A fleet"""
    global _a2a_fleet
    if _a2a_fleet is None:
        _a2a_fleet = A2AFleet()
        
        # Register CHATTY's built-in agents
        base_url = "http://localhost:8080"
        _a2a_fleet.register_agent(ChattyA2AAgents.revenue_agent(base_url))
        _a2a_fleet.register_agent(ChattyA2AAgents.acquisition_agent(base_url))
        _a2a_fleet.register_agent(ChattyA2AAgents.content_agent(base_url))
        _a2a_fleet.register_agent(ChattyA2AAgents.research_agent(base_url))
    
    return _a2a_fleet


if __name__ == "__main__":
    async def test():
        print("🧪 Testing A2A Protocol Integration...")
        
        fleet = await get_a2a_fleet()
        print(f"✅ A2A Fleet initialized with {len(fleet.agents)} agents")
        
        # Show agent capabilities
        print("\n🤖 Registered Agents:")
        for name, agent in fleet.agents.items():
            print(f"  • {name}")
            for skill in agent.skills:
                print(f"    - {skill['id']}: {skill['name']}")
        
        print("\n✅ A2A test complete")
    
    asyncio.run(test())
