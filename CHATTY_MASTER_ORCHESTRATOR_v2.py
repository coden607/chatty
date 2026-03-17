#!/usr/bin/env python3
"""
CHATTY Master Orchestrator v2.0
Unified integration of ALL cutting-edge AI frameworks:
- OpenClaw (file chunking, self-repair)
- Archon2 (hierarchical orchestration)
- LangChain (chains and tools)
- CrewAI (multi-agent collaboration)
- Pydantic AI (structured outputs)
- LangGraph Supervisor (manager-worker patterns)
- smolagents (code-first agents)
- MCP (Model Context Protocol)
- A2A (Agent-to-Agent Protocol)
- BMAD (behavioral modeling)
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Literal, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Types of tasks the orchestrator can handle"""
    CODE_GENERATION = "code_generation"
    CONTENT_CREATION = "content_creation"
    DATA_ANALYSIS = "data_analysis"
    RESEARCH = "research"
    STRATEGIC_PLANNING = "strategic_planning"
    LEAD_GENERATION = "lead_generation"
    EMAIL_OUTREACH = "email_outreach"
    SEO_OPTIMIZATION = "seo_optimization"
    AUTOMATION_BUILDING = "automation_building"
    MARKET_RESEARCH = "market_research"
    UNKNOWN = "unknown"


@dataclass
class UnifiedTask:
    """Standardized task format for the orchestrator"""
    name: str
    description: str
    task_type: TaskType
    context: Dict[str, Any] = field(default_factory=dict)
    priority: int = 3  # 1-5
    timeout_seconds: int = 300
    require_validation: bool = True
    preferred_framework: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "task_type": self.task_type.value,
            "context": self.context,
            "priority": self.priority,
            "timeout_seconds": self.timeout_seconds,
            "require_validation": self.require_validation,
            "preferred_framework": self.preferred_framework
        }


@dataclass
class TaskResult:
    """Standardized result format"""
    task: UnifiedTask
    success: bool
    framework_used: str
    output: Any
    execution_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class FrameworkRouter:
    """
    Intelligent router that selects the best framework for each task
    Based on task type, complexity, and framework strengths
    """
    
    FRAMEWORK_STRENGTHS = {
        "openclaw": ["file_processing", "code_analysis", "context_management", "chunking"],
        "archon2": ["strategic_planning", "complex_coordination", "hierarchical_tasks"],
        "langgraph_supervisor": ["multi_step_workflows", "stateful_orchestration", "agent_teams"],
        "crewai": ["collaborative_content", "role_based_tasks", "team_workflows"],
        "pydantic_ai": ["structured_outputs", "data_extraction", "validation"],
        "smolagents": ["code_generation", "automation", "analysis", "calculations"],
        "mcp": ["tool_integration", "external_apis", "filesystem", "database"],
        "a2a": ["agent_collaboration", "cross_organization", "distributed_tasks"]
    }
    
    TASK_FRAMEWORK_MAPPING = {
        TaskType.CODE_GENERATION: ["smolagents", "openclaw", "langgraph_supervisor"],
        TaskType.CONTENT_CREATION: ["crewai", "langgraph_supervisor", "pydantic_ai"],
        TaskType.DATA_ANALYSIS: ["smolagents", "pydantic_ai", "openclaw"],
        TaskType.RESEARCH: ["mcp", "smolagents", "archon2"],
        TaskType.STRATEGIC_PLANNING: ["archon2", "langgraph_supervisor", "crewai"],
        TaskType.LEAD_GENERATION: ["pydantic_ai", "smolagents", "mcp"],
        TaskType.EMAIL_OUTREACH: ["pydantic_ai", "crewai", "a2a"],
        TaskType.SEO_OPTIMIZATION: ["crewai", "pydantic_ai", "smolagents"],
        TaskType.AUTOMATION_BUILDING: ["smolagents", "mcp", "openclaw"],
        TaskType.MARKET_RESEARCH: ["mcp", "archon2", "pydantic_ai"]
    }
    
    def select_framework(self, task: UnifiedTask) -> str:
        """Select the best framework for a task"""
        
        # Use preferred framework if specified and available
        if task.preferred_framework:
            return task.preferred_framework
        
        # Get ranked frameworks for task type
        candidates = self.TASK_FRAMEWORK_MAPPING.get(task.task_type, ["smolagents", "pydantic_ai"])
        
        # Score each framework based on task context
        best_framework = candidates[0]
        best_score = 0
        
        for framework in candidates:
            score = self._score_framework(framework, task)
            if score > best_score:
                best_score = score
                best_framework = framework
        
        logger.info(f"🎯 Selected framework '{best_framework}' for task '{task.name}'")
        return best_framework
    
    def _score_framework(self, framework: str, task: UnifiedTask) -> int:
        """Score a framework for a specific task"""
        score = 0
        
        # Base score from task type mapping
        candidates = self.TASK_FRAMEWORK_MAPPING.get(task.task_type, [])
        if framework in candidates:
            score += (len(candidates) - candidates.index(framework)) * 10
        
        # Check context requirements
        context = task.context
        
        if "files" in context and framework in ["openclaw", "mcp"]:
            score += 15
        
        if "structured_output" in context and framework == "pydantic_ai":
            score += 20
        
        if "code_execution" in context and framework == "smolagents":
            score += 20
        
        if "multi_agent" in context and framework in ["crewai", "langgraph_supervisor"]:
            score += 15
        
        if "external_tools" in context and framework == "mcp":
            score += 20
        
        return score


class MasterOrchestrator:
    """
    Master orchestrator integrating ALL AI frameworks
    Single entry point for all AI operations
    """
    
    def __init__(self):
        self.router = FrameworkRouter()
        self.execution_history: List[TaskResult] = []
        self.initialized = False
        
        # Framework clients (lazy loaded)
        self._mcp_client = None
        self._a2a_fleet = None
        self._supervisors: Dict[str, Any] = {}
        self._smolagents: Dict[str, Any] = {}
        self._pydantic_functions = None
        
    async def initialize(self):
        """Initialize all framework connections"""
        if self.initialized:
            return
        
        logger.info("🚀 Initializing CHATTY Master Orchestrator v2.0...")
        
        # Initialize MCP
        try:
            from MCP_INTEGRATION import get_mcp_client
            self._mcp_client = await get_mcp_client()
            logger.info("✅ MCP client initialized")
        except Exception as e:
            logger.warning(f"⚠️ MCP initialization: {e}")
        
        # Initialize A2A
        try:
            from A2A_PROTOCOL import get_a2a_fleet
            self._a2a_fleet = await get_a2a_fleet()
            logger.info("✅ A2A fleet initialized")
        except Exception as e:
            logger.warning(f"⚠️ A2A initialization: {e}")
        
        # Initialize LangGraph Supervisors
        try:
            from LANGGRAPH_SUPERVISOR import get_supervisor
            self._supervisors["content"] = await get_supervisor("content")
            self._supervisors["sales"] = await get_supervisor("sales")
            self._supervisors["rd"] = await get_supervisor("rd")
            logger.info("✅ LangGraph supervisors initialized")
        except Exception as e:
            logger.warning(f"⚠️ LangGraph initialization: {e}")
        
        # Initialize smolagents
        try:
            from SMOLAGENTS_INTEGRATION import ChattySmolAgents
            self._smolagents["analyst"] = ChattySmolAgents.data_analyst()
            self._smolagents["researcher"] = ChattySmolAgents.content_researcher()
            self._smolagents["coder"] = ChattySmolAgents.code_assistant()
            logger.info("✅ smolagents initialized")
        except Exception as e:
            logger.warning(f"⚠️ smolagents initialization: {e}")
        
        # Initialize Pydantic AI
        try:
            from PYDANTIC_AI_ENHANCED import get_pydantic_functions
            self._pydantic_functions = get_pydantic_functions()
            logger.info("✅ Pydantic AI initialized")
        except Exception as e:
            logger.warning(f"⚠️ Pydantic AI initialization: {e}")
        
        self.initialized = True
        logger.info("✅ Master Orchestrator v2.0 ready!")
    
    async def execute(self, task: UnifiedTask) -> TaskResult:
        """
        Execute a task using the optimal framework
        """
        if not self.initialized:
            await self.initialize()
        
        start_time = asyncio.get_event_loop().time()
        
        # Select framework
        framework = self.router.select_framework(task)
        
        try:
            # Route to appropriate handler
            if framework == "smolagents":
                output = await self._execute_smolagents(task)
            elif framework == "pydantic_ai":
                output = await self._execute_pydantic_ai(task)
            elif framework == "langgraph_supervisor":
                output = await self._execute_supervisor(task)
            elif framework == "mcp":
                output = await self._execute_mcp(task)
            elif framework == "a2a":
                output = await self._execute_a2a(task)
            elif framework == "archon2":
                output = await self._execute_archon2(task)
            elif framework == "crewai":
                output = await self._execute_crewai(task)
            elif framework == "openclaw":
                output = await self._execute_openclaw(task)
            else:
                output = await self._execute_fallback(task)
            
            execution_time = asyncio.get_event_loop().time() - start_time
            
            result = TaskResult(
                task=task,
                success=True,
                framework_used=framework,
                output=output,
                execution_time=execution_time,
                metadata={"framework": framework, "routed_at": datetime.utcnow().isoformat()}
            )
            
        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            logger.error(f"❌ Task '{task.name}' failed: {e}")
            
            result = TaskResult(
                task=task,
                success=False,
                framework_used=framework,
                output=None,
                execution_time=execution_time,
                error=str(e),
                metadata={"framework": framework, "error_type": type(e).__name__}
            )
        
        self.execution_history.append(result)
        return result
    
    async def _execute_smolagents(self, task: UnifiedTask) -> Any:
        """Execute using smolagents"""
        agent_type = task.context.get("agent_type", "analyst")
        agent = self._smolagents.get(agent_type, self._smolagents.get("analyst"))
        
        if not agent:
            raise RuntimeError("No smolagents available")
        
        return await agent.run(task.description)
    
    async def _execute_pydantic_ai(self, task: UnifiedTask) -> Any:
        """Execute using Pydantic AI structured outputs"""
        func_name = task.context.get("function", "plan_task")
        
        if not self._pydantic_functions:
            raise RuntimeError("Pydantic AI not initialized")
        
        func = getattr(self._pydantic_functions, func_name, None)
        if not func:
            raise ValueError(f"Unknown Pydantic AI function: {func_name}")
        
        # Extract parameters from context
        params = {k: v for k, v in task.context.items() if k != "function"}
        return await func(**params)
    
    async def _execute_supervisor(self, task: UnifiedTask) -> Any:
        """Execute using LangGraph Supervisor"""
        team = task.context.get("team", "content")
        supervisor = self._supervisors.get(team)
        
        if not supervisor:
            raise RuntimeError(f"Supervisor team '{team}' not available")
        
        return await supervisor.orchestrate({"description": task.description, **task.context})
    
    async def _execute_mcp(self, task: UnifiedTask) -> Any:
        """Execute using MCP tools"""
        if not self._mcp_client:
            raise RuntimeError("MCP client not initialized")
        
        tool_name = task.context.get("tool")
        arguments = task.context.get("arguments", {})
        
        return await self._mcp_client.call_tool(tool_name, arguments)
    
    async def _execute_a2a(self, task: UnifiedTask) -> Any:
        """Execute using A2A protocol"""
        if not self._a2a_fleet:
            raise RuntimeError("A2A fleet not initialized")
        
        return await self._a2a_fleet.delegate_task(
            task.description,
            required_skill=task.context.get("skill"),
            preferred_agent=task.context.get("agent")
        )
    
    async def _execute_archon2(self, task: UnifiedTask) -> Any:
        """Execute using Archon2"""
        # Use existing ARCHON2_ORCHESTRATION
        from ARCHON2_ORCHESTRATION import Archon2Orchestrator
        
        archon = Archon2Orchestrator()
        return await archon.process_request({"request": task.description, **task.context})
    
    async def _execute_crewai(self, task: UnifiedTask) -> Any:
        """Execute using CrewAI"""
        # Use existing SELF_IMPROVING_AGENTS
        from SELF_IMPROVING_AGENTS import SelfImprovingAgentSystem
        
        agent_system = SelfImprovingAgentSystem()
        return await agent_system.execute_task(task.description, task.context)
    
    async def _execute_openclaw(self, task: UnifiedTask) -> Any:
        """Execute using OpenClaw"""
        from openclaw_integration import AutonomousLearningSystem
        
        openclaw = AutonomousLearningSystem()
        
        if "file" in task.context:
            return openclaw.chunk_and_analyze(task.context["file"])
        else:
            return await openclaw.self_improve(task.description)
    
    async def _execute_fallback(self, task: UnifiedTask) -> Any:
        """Fallback execution using Model Router"""
        from CHATTY_MODEL_ROUTER import router
        
        return await router.generate(
            prompt=task.description,
            system_prompt=f"You are an AI assistant helping with: {task.task_type.value}"
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get orchestration statistics"""
        if not self.execution_history:
            return {"total_tasks": 0}
        
        total = len(self.execution_history)
        successful = sum(1 for r in self.execution_history if r.success)
        
        framework_usage = {}
        for r in self.execution_history:
            fw = r.framework_used
            framework_usage[fw] = framework_usage.get(fw, 0) + 1
        
        avg_execution_time = sum(r.execution_time for r in self.execution_history) / total
        
        return {
            "total_tasks": total,
            "successful": successful,
            "failed": total - successful,
            "success_rate": successful / total,
            "avg_execution_time": avg_execution_time,
            "framework_usage": framework_usage
        }


# Convenience functions
_orchestrator: Optional[MasterOrchestrator] = None


async def get_orchestrator() -> MasterOrchestrator:
    """Get or create global orchestrator"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = MasterOrchestrator()
        await _orchestrator.initialize()
    return _orchestrator


async def execute_task(
    name: str,
    description: str,
    task_type: Union[TaskType, str],
    **kwargs
) -> TaskResult:
    """
    Quick execution of a task
    
    Example:
        result = await execute_task(
            name="Generate blog post",
            description="Write about AI in healthcare",
            task_type=TaskType.CONTENT_CREATION
        )
    """
    if isinstance(task_type, str):
        task_type = TaskType(task_type)
    
    orchestrator = await get_orchestrator()
    task = UnifiedTask(
        name=name,
        description=description,
        task_type=task_type,
        context=kwargs
    )
    return await orchestrator.execute(task)


# Quick helper functions for common tasks
async def quick_code_generation(description: str, language: str = "python") -> str:
    """Quick code generation"""
    result = await execute_task(
        name="Code Generation",
        description=description,
        task_type=TaskType.CODE_GENERATION,
        language=language,
        agent_type="coder"
    )
    return result.output.get("final_answer", "") if result.success else str(result.error)


async def quick_content_creation(topic: str, content_type: str = "blog") -> str:
    """Quick content creation"""
    result = await execute_task(
        name="Content Creation",
        description=f"Create {content_type} about {topic}",
        task_type=TaskType.CONTENT_CREATION,
        topic=topic,
        content_type=content_type,
        function="create_content"
    )
    return result.output.content if result.success and hasattr(result.output, 'content') else str(result.output)


async def quick_data_analysis(data: Any, analysis_type: str = "summary") -> Dict[str, Any]:
    """Quick data analysis"""
    result = await execute_task(
        name="Data Analysis",
        description=f"Analyze data: {analysis_type}",
        task_type=TaskType.DATA_ANALYSIS,
        data=data,
        agent_type="analyst"
    )
    return result.output if result.success else {"error": result.error}


async def quick_strategic_planning(objective: str) -> Dict[str, Any]:
    """Quick strategic planning"""
    result = await execute_task(
        name="Strategic Planning",
        description=objective,
        task_type=TaskType.STRATEGIC_PLANNING,
        objective=objective,
        function="plan_task"
    )
    return result.output.model_dump() if result.success and hasattr(result.output, 'model_dump') else result.output


if __name__ == "__main__":
    async def test():
        print("🧪 Testing CHATTY Master Orchestrator v2.0...")
        print()
        
        orchestrator = await get_orchestrator()
        
        # Test different task types
        tests = [
            ("Code Generation", TaskType.CODE_GENERATION, "Create a function to calculate fibonacci numbers"),
            ("Content Creation", TaskType.CONTENT_CREATION, "Write a tweet about AI automation"),
            ("Strategic Planning", TaskType.STRATEGIC_PLANNING, "Plan a product launch for a SaaS tool"),
        ]
        
        for name, task_type, description in tests:
            print(f"\n📝 Testing: {name}")
            result = await orchestrator.execute(UnifiedTask(
                name=name,
                description=description,
                task_type=task_type
            ))
            print(f"   Framework: {result.framework_used}")
            print(f"   Success: {result.success}")
            print(f"   Time: {result.execution_time:.2f}s")
            if result.success:
                output_preview = str(result.output)[:100] if result.output else "None"
                print(f"   Output: {output_preview}...")
        
        print("\n📊 Orchestrator Stats:")
        stats = orchestrator.get_stats()
        print(f"   Total tasks: {stats['total_tasks']}")
        print(f"   Success rate: {stats['success_rate']:.1%}")
        print(f"   Framework usage: {stats['framework_usage']}")
        
        print("\n✅ Master Orchestrator v2.0 test complete!")
    
    asyncio.run(test())
