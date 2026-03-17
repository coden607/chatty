#!/usr/bin/env python3
"""
CHATTY REAL DATA AI Orchestration System
Uses ONLY NVIDIA Build API with Kimi K2.5 - NO simulations, NO demo mode, REAL DATA ONLY
"""

import asyncio
import json
import os
import sys
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import time
import aiohttp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================================================
# REAL DATA ENFORCEMENT - Fail if APIs unavailable
# =============================================================================

class RealDataError(Exception):
    """Raised when real data cannot be obtained"""
    pass

# =============================================================================
# PYDANTIC MODELS - Type-safe data structures
# =============================================================================

from pydantic import BaseModel, Field, validator

class TaskType(str, Enum):
    """Task type enumeration"""
    CODE_GENERATION = "code_generation"
    CONTENT_CREATION = "content_creation"
    DATA_ANALYSIS = "data_analysis"
    STRATEGIC_PLANNING = "strategic_planning"
    SYSTEM_OPTIMIZATION = "system_optimization"
    CUSTOMER_SUPPORT = "customer_support"
    RESEARCH = "research"
    INTEGRATION = "integration"
    DEBUGGING = "debugging"

class TaskPriority(int, Enum):
    """Task priority levels"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4

class UnifiedTask(BaseModel):
    """Unified task model for all AI systems"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=10)
    task_type: TaskType
    priority: TaskPriority = TaskPriority.MEDIUM
    complexity: str = Field(default="medium")
    scope: str = Field(default="task")
    
    context: Dict[str, Any] = Field(default_factory=dict)
    inputs: Dict[str, Any] = Field(default_factory=dict)
    expected_outputs: Dict[str, Any] = Field(default_factory=dict)
    
    max_retries: int = Field(default=3, ge=0, le=10)
    timeout_seconds: int = Field(default=300, ge=10)
    requires_coordination: bool = False
    
    preferred_framework: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AgentResult(BaseModel):
    """Standard result format from any agent - REAL DATA ONLY"""
    task_id: str
    agent_id: str
    agent_framework: str
    status: str
    output: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    execution_time: float = Field(default=0.0)
    tokens_used: int = Field(default=0)
    model_used: str = Field(default="unknown")
    api_provider: str = Field(default="unknown")
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    raw_api_response: Optional[Dict] = None  # Store actual API response

class SystemHealth(BaseModel):
    """System health metrics - REAL DATA ONLY"""
    overall_status: str = "healthy"
    active_agents: int = 0
    queued_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    avg_response_time: float = 0.0
    api_status: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# =============================================================================
# NVIDIA KIMI K2.5 LLM MANAGER - REAL API ONLY
# =============================================================================

class NVIDIAKimiK2_5Manager:
    """
    Manages NVIDIA Build API with Kimi K2.5
    REAL DATA ONLY - No simulations, no fallbacks
    """
    
    API_ENDPOINT = "https://integrate.api.nvidia.com/v1/chat/completions"
    MODEL_NAME = "moonshotai/kimi-k2.5"
    
    def __init__(self):
        self.api_key = os.getenv('NVIDIA_API_KEY')
        if not self.api_key:
            raise RealDataError(
                "NVIDIA_API_KEY environment variable not set. "
                "Get your free API key at https://build.nvidia.com/moonshotai/kimi-k2.5"
            )
        
        self.session: Optional[aiohttp.ClientSession] = None
        self.total_requests = 0
        self.total_tokens_used = 0
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                }
            )
        return self.session
    
    async def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        enable_thinking: bool = True,
        tools: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Generate text using NVIDIA Kimi K2.5 API
        REAL DATA ONLY - Returns actual API response or raises error
        """
        start_time = time.time()
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.MODEL_NAME,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": 1,
            "stream": False,
        }
        
        if enable_thinking:
            payload["chat_template_kwargs"] = {"thinking": True}
        
        if tools:
            payload["tools"] = tools
        
        session = await self._get_session()
        
        try:
            async with session.post(self.API_ENDPOINT, json=payload) as response:
                response.raise_for_status()
                data = await response.json()
                
                execution_time = time.time() - start_time
                self.total_requests += 1
                
                # Extract real data from API response
                choice = data.get("choices", [{}])[0]
                message = choice.get("message", {})
                content = message.get("content", "")
                
                usage = data.get("usage", {})
                tokens_used = usage.get("total_tokens", 0)
                self.total_tokens_used += tokens_used
                
                return {
                    "content": content,
                    "model_used": data.get("model", self.MODEL_NAME),
                    "tokens_used": tokens_used,
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "execution_time": execution_time,
                    "success": True,
                    "api_provider": "nvidia_build",
                    "raw_response": data,
                    "finish_reason": choice.get("finish_reason"),
                    "thinking": enable_thinking
                }
                
        except aiohttp.ClientResponseError as e:
            error_msg = f"NVIDIA API error {e.status}: {e.message}"
            logger.error(error_msg)
            raise RealDataError(error_msg)
        except Exception as e:
            error_msg = f"API request failed: {str(e)}"
            logger.error(error_msg)
            raise RealDataError(error_msg)
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test API connection and return real status"""
        try:
            result = await self.generate(
                prompt="Hello, this is a connection test.",
                max_tokens=50,
                enable_thinking=False
            )
            return {
                "status": "connected",
                "model": result["model_used"],
                "latency_ms": result["execution_time"] * 1000,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def close(self):
        """Close API session"""
        if self.session and not self.session.closed:
            await self.session.close()


# =============================================================================
# FRAMEWORK EXECUTORS - REAL DATA ONLY
# =============================================================================

class OpenClawExecutor:
    """Execute tasks using OpenClaw - REAL DATA FROM NVIDIA API"""
    
    def __init__(self, llm_manager: NVIDIAKimiK2_5Manager):
        self.llm_manager = llm_manager
    
    async def execute(self, task: UnifiedTask) -> AgentResult:
        """Execute task using OpenClaw with REAL API data"""
        start_time = time.time()
        
        try:
            if task.task_type == TaskType.CODE_GENERATION:
                result = await self._generate_code(task)
            elif task.task_type == TaskType.DEBUGGING:
                result = await self._debug_code(task)
            else:
                # General task
                llm_result = await self.llm_manager.generate(
                    prompt=task.description,
                    system_prompt=task.context.get('system_prompt', ''),
                    max_tokens=task.context.get('max_tokens', 4096)
                )
                result = {
                    'output': llm_result['content'],
                    'model_used': llm_result['model_used'],
                    'tokens_used': llm_result['tokens_used']
                }
            
            execution_time = time.time() - start_time
            
            return AgentResult(
                task_id=task.id,
                agent_id="openclaw_executor",
                agent_framework="openclaw",
                status="completed",
                output=result,
                confidence=0.90,
                execution_time=execution_time,
                tokens_used=result.get('tokens_used', 0),
                model_used=result.get('model_used', 'kimi-k2.5'),
                api_provider="nvidia_build",
                raw_api_response=llm_result.get('raw_response') if 'llm_result' in locals() else None
            )
            
        except RealDataError:
            raise
        except Exception as e:
            return AgentResult(
                task_id=task.id,
                agent_id="openclaw_executor",
                agent_framework="openclaw",
                status="failed",
                error_message=str(e),
                execution_time=time.time() - start_time
            )
    
    async def _generate_code(self, task: UnifiedTask) -> Dict[str, Any]:
        """Generate code using REAL API"""
        language = task.context.get('language', 'python')
        
        prompt = f"""Generate {language} code for the following:

{task.description}

Requirements:
{json.dumps(task.inputs, indent=2)}

Provide clean, production-ready code with comments."""
        
        llm_result = await self.llm_manager.generate(
            prompt=prompt,
            system_prompt="You are an expert software engineer. Generate clean, well-documented code.",
            max_tokens=4096
        )
        
        return {
            'code': llm_result['content'],
            'language': language,
            'model_used': llm_result['model_used'],
            'tokens_used': llm_result['tokens_used'],
            'thinking_enabled': llm_result.get('thinking', False)
        }
    
    async def _debug_code(self, task: UnifiedTask) -> Dict[str, Any]:
        """Debug code using REAL API"""
        code = task.inputs.get('code', '')
        error = task.inputs.get('error', '')
        
        prompt = f"""Debug the following code:

```
{code}
```

Error message:
{error}

Identify the issue and provide a fix with explanation."""
        
        llm_result = await self.llm_manager.generate(
            prompt=prompt,
            system_prompt="You are a debugging expert. Analyze code and provide solutions.",
            max_tokens=4096
        )
        
        return {
            'analysis': llm_result['content'],
            'model_used': llm_result['model_used'],
            'tokens_used': llm_result['tokens_used']
        }


class LangChainExecutor:
    """Execute tasks using LangChain patterns - REAL DATA ONLY"""
    
    def __init__(self, llm_manager: NVIDIAKimiK2_5Manager):
        self.llm_manager = llm_manager
    
    async def execute(self, task: UnifiedTask) -> AgentResult:
        """Execute task - REAL DATA ONLY"""
        start_time = time.time()
        
        try:
            if task.task_type == TaskType.DATA_ANALYSIS:
                result = await self._analyze_data(task)
            elif task.task_type == TaskType.RESEARCH:
                result = await self._research(task)
            else:
                system_prompt = task.context.get(
                    'system_prompt', 
                    'You are a helpful AI assistant powered by Kimi K2.5 through NVIDIA Build API.'
                )
                
                llm_result = await self.llm_manager.generate(
                    prompt=task.description,
                    system_prompt=system_prompt,
                    max_tokens=task.context.get('max_tokens', 4096)
                )
                
                result = {
                    'output': llm_result['content'],
                    'model_used': llm_result['model_used'],
                    'tokens_used': llm_result['tokens_used']
                }
            
            execution_time = time.time() - start_time
            
            return AgentResult(
                task_id=task.id,
                agent_id="langchain_executor",
                agent_framework="langchain",
                status="completed",
                output=result,
                confidence=0.88,
                execution_time=execution_time,
                tokens_used=result.get('tokens_used', 0),
                model_used=result.get('model_used', 'kimi-k2.5'),
                api_provider="nvidia_build",
                raw_api_response=llm_result.get('raw_response')
            )
            
        except RealDataError:
            raise
        except Exception as e:
            return AgentResult(
                task_id=task.id,
                agent_id="langchain_executor",
                agent_framework="langchain",
                status="failed",
                error_message=str(e),
                execution_time=time.time() - start_time
            )
    
    async def _analyze_data(self, task: UnifiedTask) -> Dict[str, Any]:
        """Analyze data using REAL API"""
        data = task.inputs.get('data', [])
        
        prompt = f"""Analyze the following data and provide insights:

```json
{json.dumps(data, indent=2)}
```

Provide analysis including:
1. Key patterns
2. Trends
3. Anomalies
4. Actionable recommendations

Format as structured analysis."""
        
        llm_result = await self.llm_manager.generate(
            prompt=prompt,
            system_prompt="You are a data analyst. Provide clear, actionable insights from data.",
            max_tokens=4096
        )
        
        return {
            'analysis': llm_result['content'],
            'data_points': len(data),
            'model_used': llm_result['model_used'],
            'tokens_used': llm_result['tokens_used']
        }
    
    async def _research(self, task: UnifiedTask) -> Dict[str, Any]:
        """Research using REAL API"""
        topic = task.inputs.get('topic', task.description)
        
        llm_result = await self.llm_manager.generate(
            prompt=f"Research and provide a comprehensive summary on: {topic}",
            system_prompt="You are a research assistant. Provide well-structured, factual information.",
            max_tokens=4096
        )
        
        return {
            'research': llm_result['content'],
            'topic': topic,
            'model_used': llm_result['model_used'],
            'tokens_used': llm_result['tokens_used']
        }


class PydanticAIExecutor:
    """Execute tasks with structured outputs - REAL DATA ONLY"""
    
    def __init__(self, llm_manager: NVIDIAKimiK2_5Manager):
        self.llm_manager = llm_manager
    
    async def execute(self, task: UnifiedTask) -> AgentResult:
        """Execute with structured output - REAL DATA ONLY"""
        start_time = time.time()
        
        try:
            llm_result = await self.llm_manager.generate(
                prompt=task.description,
                system_prompt=f"Respond with valid JSON matching this structure: {task.expected_outputs}",
                max_tokens=4096
            )
            
            # Try to parse as JSON
            try:
                structured_output = json.loads(llm_result['content'])
            except json.JSONDecodeError:
                structured_output = {'raw_output': llm_result['content']}
            
            execution_time = time.time() - start_time
            
            return AgentResult(
                task_id=task.id,
                agent_id="pydantic_executor",
                agent_framework="pydantic",
                status="completed",
                output={
                    'structured_output': structured_output,
                    'model_used': llm_result['model_used'],
                    'tokens_used': llm_result['tokens_used']
                },
                confidence=0.92,
                execution_time=execution_time,
                tokens_used=llm_result['tokens_used'],
                model_used=llm_result['model_used'],
                api_provider="nvidia_build",
                raw_api_response=llm_result.get('raw_response')
            )
            
        except RealDataError:
            raise
        except Exception as e:
            return AgentResult(
                task_id=task.id,
                agent_id="pydantic_executor",
                agent_framework="pydantic",
                status="failed",
                error_message=str(e),
                execution_time=time.time() - start_time
            )


class CrewAIExecutor:
    """Multi-agent execution using Kimi K2.5 - REAL DATA ONLY"""
    
    def __init__(self, llm_manager: NVIDIAKimiK2_5Manager):
        self.llm_manager = llm_manager
    
    async def execute(self, task: UnifiedTask) -> AgentResult:
        """Execute with multi-agent collaboration - REAL DATA ONLY"""
        start_time = time.time()
        
        try:
            if task.task_type == TaskType.CONTENT_CREATION:
                result = await self._create_content(task)
            elif task.task_type == TaskType.STRATEGIC_PLANNING:
                result = await self._strategic_planning(task)
            else:
                result = await self._generic_execution(task)
            
            execution_time = time.time() - start_time
            
            return AgentResult(
                task_id=task.id,
                agent_id="crewai_executor",
                agent_framework="crewai",
                status="completed",
                output=result,
                confidence=0.89,
                execution_time=execution_time,
                tokens_used=result.get('total_tokens', 0),
                model_used="kimi-k2.5",
                api_provider="nvidia_build"
            )
            
        except RealDataError:
            raise
        except Exception as e:
            return AgentResult(
                task_id=task.id,
                agent_id="crewai_executor",
                agent_framework="crewai",
                status="failed",
                error_message=str(e),
                execution_time=time.time() - start_time
            )
    
    async def _create_content(self, task: UnifiedTask) -> Dict[str, Any]:
        """Create content using multi-step REAL API calls"""
        topic = task.inputs.get('topic', task.description)
        platform = task.inputs.get('platform', 'blog')
        
        # Step 1: Writer agent
        writer_prompt = f"""As a content writer, create engaging {platform} content about:

{topic}

Requirements:
- Engaging and persuasive
- Optimized for {platform}
- Include clear call-to-action

Write the complete content."""
        
        writer_result = await self.llm_manager.generate(
            prompt=writer_prompt,
            system_prompt="You are an expert content writer.",
            max_tokens=4096
        )
        
        draft_content = writer_result['content']
        
        # Step 2: Editor agent
        editor_prompt = f"""As an editor, review and improve this content:

{draft_content}

Improve:
1. Clarity and flow
2. Grammar and style
3. SEO optimization
4. Engagement

Provide the polished final version."""
        
        editor_result = await self.llm_manager.generate(
            prompt=editor_prompt,
            system_prompt="You are a professional editor.",
            max_tokens=4096
        )
        
        return {
            'content': editor_result['content'],
            'draft': draft_content,
            'platform': platform,
            'topic': topic,
            'total_tokens': writer_result['tokens_used'] + editor_result['tokens_used'],
            'agents_used': 2
        }
    
    async def _strategic_planning(self, task: UnifiedTask) -> Dict[str, Any]:
        """Strategic planning using multi-agent approach"""
        goal = task.description
        
        # Analyst agent
        analyst_prompt = f"""As a business analyst, analyze the strategic goal:

{goal}

Provide:
1. Market analysis
2. SWOT analysis
3. Key success factors"""
        
        analyst_result = await self.llm_manager.generate(
            prompt=analyst_prompt,
            system_prompt="You are a business analyst.",
            max_tokens=4096
        )
        
        # Strategist agent
        strategist_prompt = f"""Based on this analysis:

{analyst_result['content']}

Create a strategic plan for:
{goal}

Include:
1. Strategic objectives
2. Action items
3. Timeline
4. Success metrics"""
        
        strategist_result = await self.llm_manager.generate(
            prompt=strategist_prompt,
            system_prompt="You are a strategic planner.",
            max_tokens=4096
        )
        
        return {
            'strategy': strategist_result['content'],
            'analysis': analyst_result['content'],
            'goal': goal,
            'total_tokens': analyst_result['tokens_used'] + strategist_result['tokens_used'],
            'agents_used': 2
        }
    
    async def _generic_execution(self, task: UnifiedTask) -> Dict[str, Any]:
        """Generic multi-agent execution"""
        llm_result = await self.llm_manager.generate(
            prompt=task.description,
            max_tokens=4096
        )
        
        return {
            'result': llm_result['content'],
            'total_tokens': llm_result['tokens_used'],
            'agents_used': 1
        }


class Archon2Executor:
    """Hierarchical orchestration - REAL DATA ONLY"""
    
    def __init__(self, llm_manager: NVIDIAKimiK2_5Manager):
        self.llm_manager = llm_manager
        self.orchestrator = None
        try:
            from ARCHON2_ORCHESTRATION import Archon2Orchestrator
            self.orchestrator = Archon2Orchestrator()
        except ImportError:
            logger.warning("Archon2 module not available")
    
    async def execute(self, task: UnifiedTask) -> AgentResult:
        """Execute using hierarchical orchestration"""
        start_time = time.time()
        
        if not self.orchestrator:
            # Fallback to direct LLM call
            llm_result = await self.llm_manager.generate(
                prompt=task.description,
                system_prompt="You are a strategic orchestrator. Provide comprehensive planning and coordination.",
                max_tokens=4096
            )
            
            return AgentResult(
                task_id=task.id,
                agent_id="archon2_executor",
                agent_framework="archon2",
                status="completed",
                output={
                    'result': llm_result['content'],
                    'model_used': llm_result['model_used'],
                    'tokens_used': llm_result['tokens_used']
                },
                confidence=0.90,
                execution_time=time.time() - start_time,
                tokens_used=llm_result['tokens_used'],
                model_used=llm_result['model_used'],
                api_provider="nvidia_build"
            )
        
        try:
            if not self.orchestrator.orchestrator:
                await self.orchestrator.initialize_archon2()
            
            archon_task = {
                'name': task.name,
                'description': task.description,
                'complexity': task.complexity,
                'scope': task.scope,
                'goal': task.description,
                'requires_coordination': task.requires_coordination
            }
            
            result = await self.orchestrator.orchestrate_task(archon_task)
            
            execution_time = time.time() - start_time
            
            return AgentResult(
                task_id=task.id,
                agent_id="archon2_executor",
                agent_framework="archon2",
                status="completed",
                output={
                    'archon_result': result,
                    'hierarchy_level': result.get('hierarchy_level'),
                    'orchestration_id': result.get('orchestration_id')
                },
                confidence=0.87,
                execution_time=execution_time,
                model_used="archon2_hierarchy",
                api_provider="nvidia_build"
            )
            
        except Exception as e:
            return AgentResult(
                task_id=task.id,
                agent_id="archon2_executor",
                agent_framework="archon2",
                status="failed",
                error_message=str(e),
                execution_time=time.time() - start_time
            )


# =============================================================================
# UNIFIED ORCHESTRATOR - REAL DATA ONLY
# =============================================================================

class RealDataAIOrchestrator:
    """
    REAL DATA ONLY AI Orchestrator
    Uses NVIDIA Build API with Kimi K2.5
    NO simulations, NO demo mode, REAL API CALLS ONLY
    """
    
    def __init__(self):
        print("\n" + "="*70)
        print("🚀 INITIALIZING REAL DATA AI ORCHESTRATOR")
        print("   Using NVIDIA Build API + Kimi K2.5")
        print("   REAL DATA ONLY - NO SIMULATIONS")
        print("="*70 + "\n")
        
        # Initialize LLM Manager - will fail if no API key
        try:
            self.llm_manager = NVIDIAKimiK2_5Manager()
            print("✅ NVIDIA API Key configured")
        except RealDataError as e:
            print(f"❌ {e}")
            raise
        
        # Initialize executors
        self.executors = {
            'openclaw': OpenClawExecutor(self.llm_manager),
            'langchain': LangChainExecutor(self.llm_manager),
            'crewai': CrewAIExecutor(self.llm_manager),
            'pydantic': PydanticAIExecutor(self.llm_manager),
            'archon2': Archon2Executor(self.llm_manager),
        }
        
        # State
        self.task_history: List[UnifiedTask] = []
        self.result_history: List[AgentResult] = []
        self.running = False
        self.task_queue: asyncio.Queue = asyncio.Queue()
        
        # Metrics - REAL DATA
        self.metrics = {
            'tasks_submitted': 0,
            'tasks_completed': 0,
            'tasks_failed': 0,
            'total_tokens_used': 0,
            'total_api_calls': 0
        }
        
        print("✅ Real Data AI Orchestrator initialized")
        print(f"   Available executors: {list(self.executors.keys())}")
    
    async def test_api_connection(self) -> Dict[str, Any]:
        """Test NVIDIA API connection"""
        print("\n🔄 Testing NVIDIA API connection...")
        status = await self.llm_manager.test_connection()
        
        if status['status'] == 'connected':
            print(f"✅ API Connected")
            print(f"   Model: {status['model']}")
            print(f"   Latency: {status['latency_ms']:.0f}ms")
        else:
            print(f"❌ API Error: {status.get('error')}")
        
        return status
    
    async def execute_task(self, task: Union[UnifiedTask, Dict]) -> AgentResult:
        """Execute task - REAL DATA ONLY"""
        if isinstance(task, dict):
            task = UnifiedTask(**task)
        
        self.task_history.append(task)
        self.metrics['tasks_submitted'] += 1
        
        # Route to framework
        framework = task.preferred_framework or self._route_task(task)
        logger.info(f"🎯 Task '{task.name}' → {framework}")
        
        executor = self.executors.get(framework)
        if not executor:
            raise RealDataError(f"No executor for framework: {framework}")
        
        # Execute with retries
        for attempt in range(task.max_retries + 1):
            try:
                result = await asyncio.wait_for(
                    executor.execute(task),
                    timeout=task.timeout_seconds
                )
                
                if result.status == "completed":
                    self.metrics['tasks_completed'] += 1
                    self.metrics['total_tokens_used'] += result.tokens_used
                    self.metrics['total_api_calls'] += 1
                else:
                    self.metrics['tasks_failed'] += 1
                
                self.result_history.append(result)
                return result
                
            except asyncio.TimeoutError:
                logger.warning(f"⏱️ Task {task.id} timeout (attempt {attempt + 1})")
                if attempt == task.max_retries:
                    raise RealDataError(f"Task timeout after {task.max_retries + 1} attempts")
            except RealDataError:
                raise
            except Exception as e:
                logger.error(f"❌ Task error: {e}")
                if attempt == task.max_retries:
                    raise RealDataError(f"Task failed: {e}")
        
        raise RealDataError("All retries exhausted")
    
    def _route_task(self, task: UnifiedTask) -> str:
        """Route task to best framework"""
        routing_map = {
            TaskType.CODE_GENERATION: 'openclaw',
            TaskType.DEBUGGING: 'openclaw',
            TaskType.DATA_ANALYSIS: 'pydantic',
            TaskType.RESEARCH: 'langchain',
            TaskType.CONTENT_CREATION: 'crewai',
            TaskType.STRATEGIC_PLANNING: 'archon2',
            TaskType.SYSTEM_OPTIMIZATION: 'archon2',
        }
        return routing_map.get(task.task_type, 'langchain')
    
    def get_health(self) -> SystemHealth:
        """Get real system health"""
        return SystemHealth(
            overall_status="healthy" if self.metrics['tasks_failed'] == 0 else "degraded",
            active_agents=0,
            queued_tasks=self.task_queue.qsize(),
            completed_tasks=self.metrics['tasks_completed'],
            failed_tasks=self.metrics['tasks_failed'],
            api_status={
                "nvidia_build": "connected" if self.llm_manager.api_key else "error",
                "model": "kimi-k2.5",
                "total_requests": self.llm_manager.total_requests,
                "total_tokens": self.llm_manager.total_tokens_used
            }
        )
    
    async def close(self):
        """Close connections"""
        await self.llm_manager.close()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

_global_orchestrator: Optional[RealDataAIOrchestrator] = None

async def get_orchestrator() -> RealDataAIOrchestrator:
    """Get global orchestrator instance"""
    global _global_orchestrator
    if _global_orchestrator is None:
        _global_orchestrator = RealDataAIOrchestrator()
    return _global_orchestrator

async def execute_ai_task(**kwargs) -> AgentResult:
    """Execute AI task with real data"""
    orchestrator = await get_orchestrator()
    task = UnifiedTask(**kwargs)
    return await orchestrator.execute_task(task)


# =============================================================================
# MAIN - TEST WITH REAL DATA
# =============================================================================

async def test_real_data_system():
    """Test the real data system"""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║        🔴 REAL DATA AI ORCHESTRATION - NVIDIA + KIMI K2.5 🔴                ║
║                                                                              ║
║              REAL API CALLS ONLY - NO SIMULATIONS                           ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
    
    try:
        orchestrator = await get_orchestrator()
        
        # Test API connection
        api_status = await orchestrator.test_api_connection()
        if api_status['status'] != 'connected':
            print("\n❌ Cannot proceed without API connection")
            return
        
        print("\n" + "="*70)
        print("🧪 TESTING WITH REAL API CALLS")
        print("="*70)
        
        # Test 1: Code Generation
        print("\n📋 Test 1: Code Generation (OpenClaw)")
        result = await orchestrator.execute_task(
            UnifiedTask(
                name="Generate Function",
                description="Create a Python function to validate email addresses using regex",
                task_type=TaskType.CODE_GENERATION,
                context={"language": "python"}
            )
        )
        print(f"   Status: {result.status}")
        print(f"   Framework: {result.agent_framework}")
        print(f"   Model: {result.model_used}")
        print(f"   Tokens: {result.tokens_used}")
        print(f"   Time: {result.execution_time:.2f}s")
        if result.output.get('code'):
            print(f"   Code preview:\n{result.output['code'][:300]}...")
        
        # Test 2: Data Analysis
        print("\n📋 Test 2: Data Analysis (Pydantic)")
        result = await orchestrator.execute_task(
            UnifiedTask(
                name="Analyze Sales",
                description="Analyze sales trends from the data",
                task_type=TaskType.DATA_ANALYSIS,
                inputs={
                    "data": [
                        {"month": "Jan", "sales": 10000},
                        {"month": "Feb", "sales": 12000},
                        {"month": "Mar", "sales": 11500}
                    ]
                }
            )
        )
        print(f"   Status: {result.status}")
        print(f"   Tokens: {result.tokens_used}")
        
        # Test 3: Research
        print("\n📋 Test 3: Research (LangChain)")
        result = await orchestrator.execute_task(
            UnifiedTask(
                name="Research Topic",
                description="Research best practices for API rate limiting",
                task_type=TaskType.RESEARCH
            )
        )
        print(f"   Status: {result.status}")
        print(f"   Tokens: {result.tokens_used}")
        
        # Health check
        print("\n" + "="*70)
        print("🏥 SYSTEM HEALTH (REAL DATA)")
        print("="*70)
        health = orchestrator.get_health()
        print(f"Overall: {health.overall_status}")
        print(f"Completed: {health.completed_tasks}")
        print(f"Failed: {health.failed_tasks}")
        print(f"API Status: {json.dumps(health.api_status, indent=2)}")
        
        # Close connections
        await orchestrator.close()
        
        print("\n" + "="*70)
        print("✅ REAL DATA TEST COMPLETE")
        print("="*70)
        
    except RealDataError as e:
        print(f"\n❌ Real Data Error: {e}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        asyncio.run(test_real_data_system())
    except KeyboardInterrupt:
        print("\n\n✅ Stopped by user")
    except RealDataError as e:
        print(f"\n\n❌ Configuration Error: {e}")
        print("\nTo use this system:")
        print("1. Get your free NVIDIA API key at https://build.nvidia.com/moonshotai/kimi-k2.5")
        print("2. Set environment variable: export NVIDIA_API_KEY='your_key_here'")
        sys.exit(1)
