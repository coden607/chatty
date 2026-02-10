#!/usr/bin/env python3
"""
CHATTY Agent Communication System
Real-time inter-agent communication and collaboration framework
"""

import asyncio
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import websockets
import threading
import queue

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class AgentMessage:
    """Represents a message between agents"""
    sender_id: str
    sender_name: str
    receiver_id: str
    message_type: str  # 'request', 'response', 'broadcast', 'collaboration'
    content: str
    context: Dict[str, Any]
    timestamp: float
    workflow_id: Optional[str] = None
    priority: str = 'normal'  # 'low', 'normal', 'high', 'urgent'

@dataclass
class Agent:
    """Represents an AI agent in the system"""
    agent_id: str
    name: str
    role: str
    specialty: str
    status: str = 'idle'  # 'idle', 'busy', 'offline', 'error'
    capabilities: List[str] = None
    message_queue: queue.Queue = None
    response_queue: queue.Queue = None

    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []
        if self.message_queue is None:
            self.message_queue = queue.Queue()
        if self.response_queue is None:
            self.response_queue = queue.Queue()

class AgentCommunicationSystem:
    """Manages real-time communication between AI agents"""

    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        self.message_history: List[AgentMessage] = []
        self.websocket_clients = set()
        self.running = False
        self.communication_thread = None

        self.initialize_agents()

    def initialize_agents(self):
        """Initialize the core AI agents"""
        agent_configs = [
            {
                'agent_id': 'claude',
                'name': 'Claude Agent',
                'role': 'Strategic Planning & Analysis',
                'specialty': 'Business strategy, market analysis, long-term planning',
                'capabilities': ['market_analysis', 'strategic_planning', 'risk_assessment', 'competitive_analysis']
            },
            {
                'agent_id': 'grok',
                'name': 'Grok Agent',
                'role': 'Creative Innovation & Research',
                'specialty': 'Creative content, innovative solutions, research synthesis',
                'capabilities': ['content_creation', 'innovation', 'research', 'creative_solutions']
            },
            {
                'agent_id': 'gemini',
                'name': 'Gemini Agent',
                'role': 'Technical Implementation',
                'specialty': 'Code generation, technical architecture, system integration',
                'capabilities': ['coding', 'architecture', 'integration', 'technical_implementation']
            },
            {
                'agent_id': 'deepseek',
                'name': 'DeepSeek Agent',
                'role': 'Synthesis & Optimization',
                'specialty': 'Final synthesis, optimization, comprehensive solutions',
                'capabilities': ['synthesis', 'optimization', 'final_analysis', 'comprehensive_solutions']
            },
            {
                'agent_id': 'orchestrator',
                'name': 'Orchestrator Agent',
                'role': 'Workflow Coordination',
                'specialty': 'Agent coordination, workflow management, real-time orchestration',
                'capabilities': ['coordination', 'workflow_management', 'orchestration', 'real_time_monitoring']
            }
        ]

        for config in agent_configs:
            agent = Agent(**config)
            self.agents[agent.agent_id] = agent
            logger.info(f"Initialized agent: {agent.name} ({agent.role})")

    async def start_communication_system(self):
        """Start the agent communication system"""
        self.running = True
        logger.info("Starting CHATTY Agent Communication System...")

        # Start WebSocket server for real-time updates
        websocket_task = asyncio.create_task(self.websocket_server())

        # Start agent communication loop
        communication_task = asyncio.create_task(self.agent_communication_loop())

        # Start workflow monitoring
        monitoring_task = asyncio.create_task(self.workflow_monitoring_loop())

        try:
            await asyncio.gather(websocket_task, communication_task, monitoring_task)
        except Exception as e:
            logger.error(f"Communication system error: {e}")
        finally:
            self.running = False

    async def websocket_server(self):
        """WebSocket server for real-time GUI updates"""
        async def handler(websocket, path):
            self.websocket_clients.add(websocket)
            try:
                # Send initial system status
                await self.send_websocket_update({
                    'type': 'system_status',
                    'agents': {aid: {
                        'name': agent.name,
                        'status': agent.status,
                        'role': agent.role
                    } for aid, agent in self.agents.items()},
                    'active_workflows': len(self.active_workflows)
                })

                async for message in websocket:
                    try:
                        data = json.loads(message)
                        await self.handle_websocket_message(data, websocket)
                    except json.JSONDecodeError:
                        logger.error("Invalid WebSocket message format")
            except websockets.exceptions.ConnectionClosed:
                pass
            finally:
                self.websocket_clients.remove(websocket)

        server = await websockets.serve(handler, "localhost", 8765)
        logger.info("WebSocket server started on ws://localhost:8765")
        await server.wait_closed()

    async def handle_websocket_message(self, data, websocket):
        """Handle incoming WebSocket messages"""
        message_type = data.get('type')

        if message_type == 'start_workflow':
            workflow_id = data.get('workflow_id')
            parameters = data.get('parameters', {})
            await self.initiate_workflow(workflow_id, parameters)

        elif message_type == 'send_agent_message':
            sender_id = data.get('sender_id')
            receiver_id = data.get('receiver_id')
            content = data.get('content')
            message_type_msg = data.get('message_type', 'request')

            await self.send_agent_message(sender_id, receiver_id, message_type_msg, content, {})

        elif message_type == 'get_agent_status':
            await self.send_websocket_update({
                'type': 'agent_status_update',
                'agents': {aid: asdict(agent) for aid, agent in self.agents.items()}
            })

    async def send_websocket_update(self, data):
        """Send updates to all connected WebSocket clients"""
        if self.websocket_clients:
            message = json.dumps(data)
            await asyncio.gather(
                *[client.send(message) for client in self.websocket_clients],
                return_exceptions=True
            )

    async def initiate_workflow(self, workflow_type: str, parameters: Dict[str, Any]):
        """Initiate a new workflow execution"""
        workflow_id = f"workflow_{int(time.time() * 1000)}"

        self.active_workflows[workflow_id] = {
            'type': workflow_type,
            'status': 'initializing',
            'parameters': parameters,
            'start_time': time.time(),
            'agents_involved': self.get_workflow_agents(workflow_type),
            'current_step': 0,
            'progress': 0
        }

        logger.info(f"Initiated workflow: {workflow_id} ({workflow_type})")

        # Broadcast workflow start
        await self.send_websocket_update({
            'type': 'workflow_started',
            'workflow_id': workflow_id,
            'workflow_type': workflow_type
        })

        # Start workflow execution
        asyncio.create_task(self.execute_workflow(workflow_id))

    def get_workflow_agents(self, workflow_type: str) -> List[str]:
        """Get the agents involved in a specific workflow"""
        workflow_agents = {
            'business_strategy': ['claude', 'grok', 'deepseek'],
            'creative_content': ['grok', 'claude', 'gemini'],
            'api_development': ['claude', 'gemini', 'grok', 'deepseek'],
            'youtube_automation': ['claude', 'grok', 'gemini', 'deepseek'],
            'blockchain_integration': ['claude', 'gemini', 'grok', 'deepseek'],
            'multimodal_ai': ['gemini', 'claude', 'grok', 'deepseek']
        }
        return workflow_agents.get(workflow_type, ['claude', 'grok', 'deepseek'])

    async def execute_workflow(self, workflow_id: str):
        """Execute a workflow with agent collaboration"""
        workflow = self.active_workflows[workflow_id]
        agents = workflow['agents_involved']

        workflow['status'] = 'executing'

        # Phase 1: Preparation and planning
        await self.send_agent_message('orchestrator', agents[0], 'request',
                                    f"Prepare to analyze: {workflow['parameters'].get('description', 'business requirements')}",
                                    {'workflow_id': workflow_id, 'phase': 'preparation'})

        await asyncio.sleep(2)  # Simulate processing time

        # Phase 2: Sequential agent processing
        for i, agent_id in enumerate(agents):
            workflow['current_step'] = i + 1
            workflow['progress'] = (i / len(agents)) * 100

            # Update agent status
            self.agents[agent_id].status = 'busy'

            # Send processing request
            context = {
                'workflow_id': workflow_id,
                'phase': 'processing',
                'step': i + 1,
                'total_steps': len(agents),
                'parameters': workflow['parameters']
            }

            if i == 0:
                # First agent starts analysis
                await self.send_agent_message('orchestrator', agent_id, 'request',
                                            f"Begin comprehensive analysis of: {workflow['parameters'].get('description', 'requirements')}",
                                            context)
            else:
                # Subsequent agents build on previous work
                prev_agent = agents[i-1]
                await self.send_agent_message(prev_agent, agent_id, 'collaboration',
                                            f"Build upon my analysis and enhance with your {self.agents[agent_id].specialty}",
                                            context)

            # Simulate processing time
            await asyncio.sleep(3)

            # Mark agent as completed
            self.agents[agent_id].status = 'idle'

            # Broadcast progress update
            await self.send_websocket_update({
                'type': 'workflow_progress',
                'workflow_id': workflow_id,
                'progress': workflow['progress'],
                'current_agent': self.agents[agent_id].name,
                'step': i + 1,
                'total_steps': len(agents)
            })

        # Phase 3: Final synthesis
        workflow['status'] = 'synthesizing'
        workflow['progress'] = 90

        await self.send_agent_message('orchestrator', agents[-1], 'request',
                                    "Synthesize all agent outputs into final comprehensive solution",
                                    {'workflow_id': workflow_id, 'phase': 'synthesis'})

        await asyncio.sleep(2)

        # Complete workflow
        workflow['status'] = 'completed'
        workflow['progress'] = 100
        workflow['end_time'] = time.time()

        await self.send_websocket_update({
            'type': 'workflow_completed',
            'workflow_id': workflow_id,
            'results': 'Comprehensive analysis completed successfully'
        })

        logger.info(f"Workflow {workflow_id} completed successfully")

    async def send_agent_message(self, sender_id: str, receiver_id: str, message_type: str,
                               content: str, context: Dict[str, Any]):
        """Send a message from one agent to another"""
        if sender_id not in self.agents or receiver_id not in self.agents:
            logger.error(f"Invalid agent IDs: {sender_id} -> {receiver_id}")
            return

        sender = self.agents[sender_id]
        receiver = self.agents[receiver_id]

        message = AgentMessage(
            sender_id=sender_id,
            sender_name=sender.name,
            receiver_id=receiver_id,
            message_type=message_type,
            content=content,
            context=context,
            timestamp=time.time(),
            workflow_id=context.get('workflow_id')
        )

        # Add to message history
        self.message_history.append(message)

        # Log the communication
        logger.info(f"[{sender.name} → {receiver.name}] {message_type}: {content[:50]}...")

        # Send to WebSocket clients for real-time display
        await self.send_websocket_update({
            'type': 'agent_message',
            'message': {
                'sender': sender.name,
                'receiver': receiver.name,
                'type': message_type,
                'content': content,
                'timestamp': datetime.fromtimestamp(message.timestamp).strftime('%H:%M:%S'),
                'workflow_id': message.workflow_id
            }
        })

        # Simulate agent "thinking" and response
        if message_type in ['request', 'collaboration']:
            asyncio.create_task(self.simulate_agent_response(message))

    async def simulate_agent_response(self, incoming_message: AgentMessage):
        """Simulate an agent processing a message and responding"""
        await asyncio.sleep(1.5)  # Simulate thinking time

        receiver = self.agents[incoming_message.receiver_id]

        # Generate contextual response based on agent specialty
        responses = {
            'claude': [
                "Conducting comprehensive market analysis and strategic assessment...",
                "Evaluating competitive landscape and identifying market opportunities...",
                "Developing detailed business strategy with risk mitigation plans...",
                "Analyzing financial projections and scalability factors..."
            ],
            'grok': [
                "Exploring innovative approaches and creative solutions...",
                "Developing disruptive business models and viral growth strategies...",
                "Identifying unique value propositions and competitive advantages...",
                "Creating innovative monetization strategies and revenue streams..."
            ],
            'gemini': [
                "Designing technical architecture and implementation roadmap...",
                "Developing data analytics and performance monitoring systems...",
                "Creating scalable infrastructure and deployment strategies...",
                "Building comprehensive technical specifications and requirements..."
            ],
            'deepseek': [
                "Synthesizing all inputs into comprehensive strategic recommendations...",
                "Optimizing business model for maximum efficiency and profitability...",
                "Creating detailed implementation plans with measurable KPIs...",
                "Developing risk mitigation strategies and contingency plans..."
            ]
        }

        agent_responses = responses.get(incoming_message.receiver_id, ["Processing request and preparing response..."])
        response_content = agent_responses[incoming_message.timestamp % len(agent_responses)]

        # Send response back
        await self.send_agent_message(
            incoming_message.receiver_id,
            incoming_message.sender_id,
            'response',
            response_content,
            incoming_message.context
        )

    async def agent_communication_loop(self):
        """Main agent communication loop"""
        while self.running:
            # Process any queued messages
            for agent_id, agent in self.agents.items():
                if not agent.message_queue.empty():
                    message = agent.message_queue.get()
                    # Process message
                    pass

            await asyncio.sleep(0.1)

    async def workflow_monitoring_loop(self):
        """Monitor active workflows and system health"""
        while self.running:
            # Check for stuck workflows
            current_time = time.time()
            for workflow_id, workflow in self.active_workflows.items():
                if workflow['status'] == 'executing':
                    elapsed = current_time - workflow['start_time']
                    if elapsed > 300:  # 5 minutes timeout
                        logger.warning(f"Workflow {workflow_id} appears stuck, elapsed: {elapsed}s")
                        workflow['status'] = 'error'

            # Send periodic system status
            await self.send_websocket_update({
                'type': 'system_health',
                'timestamp': current_time,
                'active_workflows': len(self.active_workflows),
                'total_messages': len(self.message_history),
                'agents_online': len([a for a in self.agents.values() if a.status != 'offline'])
            })

            await asyncio.sleep(10)  # Check every 10 seconds

def main():
    """Main function to start the agent communication system"""
    system = AgentCommunicationSystem()

    try:
        logger.info("Starting CHATTY Agent Communication System...")
        asyncio.run(system.start_communication_system())
    except KeyboardInterrupt:
        logger.info("Shutting down CHATTY Agent Communication System...")
    except Exception as e:
        logger.error(f"System error: {e}")
        raise

if __name__ == "__main__":
    main()
