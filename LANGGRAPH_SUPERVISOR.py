#!/usr/bin/env python3
"""
CHATTY LangGraph Supervisor Integration
Hierarchical multi-agent orchestration with manager-worker patterns
Latest LangGraph v0.3+ features for stateful agent workflows
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, TypedDict, Annotated, Literal, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)

# LangGraph-style state management (compatible without full LangGraph import)
class SupervisorState(TypedDict):
    """State for supervisor orchestration"""
    messages: List[Dict[str, Any]]
    next_worker: Optional[str]
    task_queue: List[Dict[str, Any]]
    results: Dict[str, Any]
    iteration_count: int
    is_complete: bool


@dataclass
class WorkerAgent:
    """
    A worker agent in the supervisor hierarchy
    Handles specific tasks delegated by supervisor
    """
    name: str
    description: str
    capabilities: List[str] = field(default_factory=list)
    system_prompt: str = ""
    max_iterations: int = 5
    
    async def execute(self, task: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a delegated task"""
        from CHATTY_MODEL_ROUTER import router
        
        task_description = task.get("description", "")
        
        # Build worker-specific prompt
        prompt = f"""You are {self.name}, a specialized AI agent.
Description: {self.description}
Capabilities: {', '.join(self.capabilities)}

Your task:
{task_description}

Context from previous steps:
{json.dumps(context or {}, indent=2)}

Execute this task to the best of your ability. Provide a clear, actionable result."""

        response = await router.generate(
            prompt=prompt,
            system_prompt=self.system_prompt or f"You are {self.name}. {self.description}"
        )
        
        return {
            "worker": self.name,
            "task": task_description,
            "result": response,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "completed"
        }


@dataclass
class SupervisorConfig:
    """Configuration for supervisor orchestration"""
    name: str = "Supervisor"
    system_prompt: str = """You are a supervisor agent that coordinates multiple specialized workers.
Your job is to:
1. Analyze incoming tasks
2. Break them down into subtasks
3. Assign each subtask to the most appropriate worker
4. Review and synthesize results
5. Determine if the task is complete or needs more work

Be decisive and efficient in your delegation."""
    max_iterations: int = 10
    completion_threshold: float = 0.8


class LangGraphSupervisor:
    """
    LangGraph-style Supervisor for hierarchical agent orchestration
    Manages a team of worker agents with stateful execution
    """
    
    def __init__(self, config: SupervisorConfig = None):
        self.config = config or SupervisorConfig()
        self.workers: Dict[str, WorkerAgent] = {}
        self.execution_history: List[Dict[str, Any]] = []
        
    def add_worker(self, worker: WorkerAgent):
        """Add a worker agent to the team"""
        self.workers[worker.name] = worker
        logger.info(f"✅ Added worker: {worker.name}")
    
    def create_worker(
        self,
        name: str,
        description: str,
        capabilities: List[str] = None,
        system_prompt: str = ""
    ) -> WorkerAgent:
        """Create and add a new worker"""
        worker = WorkerAgent(
            name=name,
            description=description,
            capabilities=capabilities or [],
            system_prompt=system_prompt
        )
        self.add_worker(worker)
        return worker
    
    async def orchestrate(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main orchestration loop - delegates tasks and manages state
        """
        # Initialize state
        state: SupervisorState = {
            "messages": [{"role": "user", "content": task.get("description", "")}],
            "next_worker": None,
            "task_queue": [],
            "results": {},
            "iteration_count": 0,
            "is_complete": False
        }
        
        logger.info(f"🎯 Supervisor '{self.config.name}' starting orchestration")
        
        # Initial task analysis
        plan = await self._analyze_task(task)
        state["task_queue"] = plan.get("subtasks", [])
        
        logger.info(f"📋 Plan created: {len(state['task_queue'])} subtasks")
        
        # Execute workflow
        while state["iteration_count"] < self.config.max_iterations and not state["is_complete"]:
            state["iteration_count"] += 1
            
            # Get next task
            if not state["task_queue"]:
                state["is_complete"] = True
                break
            
            current_task = state["task_queue"].pop(0)
            
            # Route to appropriate worker
            worker_name = await self._route_task(current_task)
            state["next_worker"] = worker_name
            
            if worker_name and worker_name in self.workers:
                worker = self.workers[worker_name]
                logger.info(f"🔄 Iteration {state['iteration_count']}: Delegating to {worker_name}")
                
                # Execute
                result = await worker.execute(
                    current_task,
                    context=state["results"]
                )
                
                # Store result
                task_id = current_task.get("id", f"task_{state['iteration_count']}")
                state["results"][task_id] = result
                state["messages"].append({
                    "role": "assistant",
                    "content": f"Worker {worker_name} completed: {json.dumps(result, indent=2)}",
                    "worker": worker_name
                })
                
                self.execution_history.append({
                    "iteration": state["iteration_count"],
                    "worker": worker_name,
                    "task": current_task,
                    "result": result
                })
            else:
                logger.warning(f"⚠️ No suitable worker found for task: {current_task}")
        
        # Final synthesis
        final_result = await self._synthesize_results(state)
        
        return {
            "supervisor": self.config.name,
            "task": task,
            "iterations": state["iteration_count"],
            "results": state["results"],
            "final_output": final_result,
            "execution_history": self.execution_history,
            "status": "completed" if state["is_complete"] else "max_iterations_reached"
        }
    
    async def _analyze_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze task and create execution plan"""
        from CHATTY_MODEL_ROUTER import router
        
        task_description = task.get("description", "")
        available_workers = [
            {"name": w.name, "capabilities": w.capabilities}
            for w in self.workers.values()
        ]
        
        prompt = f"""Analyze this task and create an execution plan:

TASK: {task_description}

AVAILABLE WORKERS:
{json.dumps(available_workers, indent=2)}

Create a plan by breaking this task into subtasks. For each subtask:
1. Give it a clear description
2. Specify which worker should handle it (by name)
3. Define expected output

Respond in JSON format:
{{
    "analysis": "brief task analysis",
    "subtasks": [
        {{
            "id": "task_1",
            "description": "what needs to be done",
            "assigned_worker": "worker_name",
            "expected_output": "what result should look like"
        }}
    ]
}}"""

        response = await router.generate(
            prompt=prompt,
            system_prompt="You are a task planning expert. Create clear, actionable plans."
        )
        
        try:
            # Extract JSON from response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response
            
            plan = json.loads(json_str)
            return plan
        except json.JSONDecodeError:
            # Fallback: create single subtask
            return {
                "analysis": "Simple task",
                "subtasks": [{
                    "id": "task_1",
                    "description": task_description,
                    "assigned_worker": list(self.workers.keys())[0] if self.workers else None,
                    "expected_output": "Task completion"
                }]
            }
    
    async def _route_task(self, task: Dict[str, Any]) -> Optional[str]:
        """Route task to most appropriate worker"""
        # Check if task specifies a worker
        assigned = task.get("assigned_worker")
        if assigned and assigned in self.workers:
            return assigned
        
        # Find best match by capabilities
        task_description = task.get("description", "").lower()
        best_match = None
        best_score = 0
        
        for name, worker in self.workers.items():
            score = 0
            for cap in worker.capabilities:
                if cap.lower() in task_description:
                    score += 1
            
            if score > best_score:
                best_score = score
                best_match = name
        
        # Fallback to first worker
        if best_match is None and self.workers:
            best_match = list(self.workers.keys())[0]
        
        return best_match
    
    async def _synthesize_results(self, state: SupervisorState) -> str:
        """Synthesize all worker results into final output"""
        from CHATTY_MODEL_ROUTER import router
        
        if not state["results"]:
            return "No results to synthesize"
        
        prompt = f"""Synthesize these worker results into a coherent final output:

ORIGINAL TASK:
{state['messages'][0]['content']}

WORKER RESULTS:
{json.dumps(state['results'], indent=2)}

Provide a clear, comprehensive final output that addresses the original task."""

        return await router.generate(
            prompt=prompt,
            system_prompt="You synthesize multiple worker outputs into cohesive final deliverables."
        )


class SwarmCoordinator:
    """
    Swarm-style coordination for decentralized agent collaboration
    Agents collaborate peer-to-peer without strict hierarchy
    """
    
    def __init__(self):
        self.agents: Dict[str, WorkerAgent] = {}
        self.shared_memory: Dict[str, Any] = {}
        
    def add_agent(self, agent: WorkerAgent):
        """Add agent to swarm"""
        self.agents[agent.name] = agent
    
    async def swarm_execute(
        self,
        task: Dict[str, Any],
        collaboration_mode: Literal["parallel", "sequential", "round_robin"] = "parallel"
    ) -> Dict[str, Any]:
        """
        Execute task using swarm collaboration
        
        Modes:
        - parallel: All agents work on different aspects simultaneously
        - sequential: Agents pass work to each other in order
        - round_robin: Agents take turns contributing
        """
        logger.info(f"🐝 Swarm executing in {collaboration_mode} mode")
        
        if collaboration_mode == "parallel":
            return await self._parallel_execution(task)
        elif collaboration_mode == "sequential":
            return await self._sequential_execution(task)
        else:
            return await self._round_robin_execution(task)
    
    async def _parallel_execution(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """All agents work in parallel on different aspects"""
        coroutines = [
            agent.execute({
                "description": f"{task.get('description', '')} [Focus on your specialty: {agent.description}]"
            })
            for agent in self.agents.values()
        ]
        
        results = await asyncio.gather(*coroutines, return_exceptions=True)
        
        return {
            "mode": "parallel",
            "results": {
                name: result if not isinstance(result, Exception) else {"error": str(result)}
                for name, result in zip(self.agents.keys(), results)
            }
        }
    
    async def _sequential_execution(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Agents pass work to each other sequentially"""
        results = {}
        context = {}
        
        for name, agent in self.agents.items():
            result = await agent.execute(task, context)
            results[name] = result
            context[f"{name}_output"] = result.get("result", "")
        
        return {
            "mode": "sequential",
            "results": results,
            "final_output": context.get(f"{list(self.agents.keys())[-1]}_output", "")
        }
    
    async def _round_robin_execution(self, task: Dict[str, Any], rounds: int = 3) -> Dict[str, Any]:
        """Agents take turns contributing to the task"""
        results = {}
        accumulated = task.get("description", "")
        
        for round_num in range(rounds):
            for name, agent in self.agents.items():
                result = await agent.execute({
                    "description": f"Round {round_num + 1}: Build upon this work:\n{accumulated}"
                })
                
                if round_num not in results:
                    results[round_num] = {}
                results[round_num][name] = result
                
                accumulated = result.get("result", accumulated)
        
        return {
            "mode": "round_robin",
            "rounds": rounds,
            "results": results,
            "final_output": accumulated
        }


# Pre-configured supervisor teams for CHATTY
class ChattySupervisorTeams:
    """Factory for CHATTY's LangGraph supervisor teams"""
    
    @staticmethod
    def content_creation_team() -> LangGraphSupervisor:
        """Team for creating marketing content"""
        supervisor = LangGraphSupervisor(config=SupervisorConfig(
            name="ContentDirector",
            system_prompt="You coordinate content creation from strategy to final output."
        ))
        
        # Researcher
        supervisor.create_worker(
            name="researcher",
            description="Researches topics and gathers information",
            capabilities=["research", "data_gathering", "analysis"],
            system_prompt="You are a research specialist. Find accurate, relevant information."
        )
        
        # Writer
        supervisor.create_worker(
            name="writer",
            description="Writes engaging content",
            capabilities=["writing", "copywriting", "storytelling"],
            system_prompt="You are a professional writer. Create engaging, clear content."
        )
        
        # Editor
        supervisor.create_worker(
            name="editor",
            description="Edits and polishes content",
            capabilities=["editing", "proofreading", "seo_optimization"],
            system_prompt="You are an editor. Improve clarity, grammar, and SEO."
        )
        
        # Designer
        supervisor.create_worker(
            name="designer",
            description="Creates visual content and formatting",
            capabilities=["design", "formatting", "visualization"],
            system_prompt="You are a content designer. Optimize formatting and visual appeal."
        )
        
        return supervisor
    
    @staticmethod
    def sales_team() -> LangGraphSupervisor:
        """Team for sales and lead conversion"""
        supervisor = LangGraphSupervisor(config=SupervisorConfig(
            name="SalesManager",
            system_prompt="You coordinate the entire sales process from lead to close."
        ))
        
        # Lead Qualifier
        supervisor.create_worker(
            name="qualifier",
            description="Qualifies leads and scores prospects",
            capabilities=["lead_scoring", "research", "qualification"],
            system_prompt="You evaluate leads for sales potential."
        )
        
        # Outreach Specialist
        supervisor.create_worker(
            name="outreach",
            description="Handles initial contact and outreach",
            capabilities=["email_writing", "calling_scripts", "linkedin"],
            system_prompt="You craft compelling outreach messages."
        )
        
        # Demo Specialist
        supervisor.create_worker(
            name="demo",
            description="Conducts product demos and presentations",
            capabilities=["presentations", "product_knowledge", "objection_handling"],
            system_prompt="You deliver persuasive product demonstrations."
        )
        
        # Closer
        supervisor.create_worker(
            name="closer",
            description="Negotiates and closes deals",
            capabilities=["negotiation", "closing", "contract_handling"],
            system_prompt="You close deals effectively."
        )
        
        return supervisor
    
    @staticmethod
    def research_development_team() -> LangGraphSupervisor:
        """Team for R&D and innovation"""
        supervisor = LangGraphSupervisor(config=SupervisorConfig(
            name="R_D_Director",
            system_prompt="You coordinate research and development efforts."
        ))
        
        # Market Analyst
        supervisor.create_worker(
            name="market_analyst",
            description="Analyzes market trends and opportunities",
            capabilities=["market_analysis", "competitive_intelligence", "trend_forecasting"],
            system_prompt="You identify market opportunities and threats."
        )
        
        # Technical Architect
        supervisor.create_worker(
            name="architect",
            description="Designs technical solutions",
            capabilities=["system_design", "architecture", "technology_evaluation"],
            system_prompt="You design robust technical architectures."
        )
        
        # Innovation Scout
        supervisor.create_worker(
            name="innovation_scout",
            description="Finds emerging technologies and methods",
            capabilities=["tech_scouting", "research", "experimentation"],
            system_prompt="You discover cutting-edge technologies."
        )
        
        return supervisor


# Global supervisor instances
_supervisors: Dict[str, LangGraphSupervisor] = {}


async def get_supervisor(name: str = "default") -> LangGraphSupervisor:
    """Get or create a supervisor"""
    if name not in _supervisors:
        if name == "content":
            _supervisors[name] = ChattySupervisorTeams.content_creation_team()
        elif name == "sales":
            _supervisors[name] = ChattySupervisorTeams.sales_team()
        elif name == "rd":
            _supervisors[name] = ChattySupervisorTeams.research_development_team()
        else:
            _supervisors[name] = LangGraphSupervisor()
    
    return _supervisors[name]


if __name__ == "__main__":
    async def test():
        print("🧪 Testing LangGraph Supervisor Integration...")
        
        # Test content team
        content_team = ChattySupervisorTeams.content_creation_team()
        print(f"✅ Content team created with {len(content_team.workers)} workers")
        
        result = await content_team.orchestrate({
            "description": "Create a blog post about AI in healthcare"
        })
        
        print(f"\n📊 Execution completed in {result['iterations']} iterations")
        print(f"✅ Status: {result['status']}")
        print(f"\n📝 Final Output:\n{result['final_output'][:500]}...")
        
        print("\n✅ LangGraph Supervisor test complete")
    
    asyncio.run(test())
