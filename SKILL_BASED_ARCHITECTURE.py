#!/usr/bin/env python3
"""
Skill-Based Architecture for Chatty System
Anti-hallucination measures and multi-agent collaboration
"""

import json
import time
import hashlib
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

# Skill categories
class SkillCategory(Enum):
    ANALYSIS = "analysis"
    EXECUTION = "execution"
    RESEARCH = "research"
    COMMUNICATION = "communication"
    CREATION = "creation"
    VALIDATION = "validation"


@dataclass
class Skill:
    """Represents a specific skill an agent can possess"""
    name: str
    category: SkillCategory
    description: str
    confidence_score: float  # 0.0 to 1.0
    validation_methods: List[str]


@dataclass
class Agent:
    """Represents an agent with specific skills and anti-hallucination measures"""
    id: str
    name: str
    skills: List[Skill]
    reliability_score: float  # 0.0 to 1.0
    hallucination_rate: float  # 0.0 to 1.0 (lower is better)
    response_format: str = "structured"


@dataclass
class Task:
    """Represents a task to be completed by agents"""
    id: str
    description: str
    required_skills: List[SkillCategory]
    difficulty: float  # 0.0 to 1.0
    expected_output_format: str
    validation_criteria: List[str]


@dataclass
class TaskResult:
    """Result from an agent completing a task"""
    task_id: str
    agent_id: str
    result: Any
    confidence: float
    validation_scores: Dict[str, float]
    timestamp: float
    hallucination_checks: List[str]


class AntiHallucinationSystem:
    """System to prevent and detect hallucinations in agent responses"""
    
    def __init__(self):
        self.fact_check_database = self._load_fact_check_database()
        self.validation_patterns = self._load_validation_patterns()
    
    def _load_fact_check_database(self) -> Dict[str, Any]:
        """Load fact check database (mock for now)"""
        return {
            "python_version": "3.13.12",
            "operating_system": "Linux 6.17",
            "project_name": "Chatty",
            "primary_language": "Python",
            "fastapi_version": "0.104.1"
        }
    
    def _load_validation_patterns(self) -> List[Dict[str, Any]]:
        """Load validation patterns for different types of responses"""
        return [
            {
                "name": "fact_verification",
                "description": "Check if response contains verifiable facts",
                "method": "fact_check"
            },
            {
                "name": "consistency_check",
                "description": "Check if response is consistent with known information",
                "method": "consistency_analysis"
            },
            {
                "name": "source_verification",
                "description": "Check if claims have valid sources",
                "method": "source_check"
            },
            {
                "name": "plausibility_analysis",
                "description": "Check if response is plausible based on context",
                "method": "plausibility_check"
            }
        ]
    
    def check_hallucination(self, response: str, context: str = "") -> List[str]:
        """Check for hallucinations in a response"""
        hallucinations = []
        
        # Check for inconsistent information
        for fact, value in self.fact_check_database.items():
            if fact in response.lower() and value.lower() not in response.lower():
                hallucinations.append(f"Inconsistent information about {fact}")
        
        # Check for implausible claims
        if "quantum computing" in response.lower() and "without quantum computing" in context.lower():
            hallucinations.append("Contradictory claim about quantum computing")
        
        # Check for unsupported claims
        if "best way" in response.lower() and "research" not in context.lower():
            hallucinations.append("Unsupported claim about 'best way' without research")
        
        return hallucinations
    
    def validate_response(self, response: str, task: Task) -> Dict[str, float]:
        """Validate response against task requirements"""
        scores = {}
        
        for criterion in task.validation_criteria:
            score = 0.0
            
            if criterion == "factually_correct":
                hallucinations = self.check_hallucination(response)
                score = 1.0 - (len(hallucinations) * 0.25)
            
            elif criterion == "complete":
                # Check if response covers all required aspects
                score = 0.8 if len(response.split()) > 50 else 0.3
            
            elif criterion == "structured":
                # Check if response has clear structure
                score = 0.9 if ("#" in response or "##" in response) else 0.4
            
            scores[criterion] = max(0.0, min(1.0, score))
        
        return scores


class SkillBasedOrchestrator:
    """Orchestrator for skill-based multi-agent collaboration"""
    
    def __init__(self):
        self.agents = self._load_agents()
        self.skill_system = AntiHallucinationSystem()
        self.task_history = []
        self.results_cache = {}
    
    def _load_agents(self) -> List[Agent]:
        """Load available agents with their skills"""
        return [
            Agent(
                id="agent_1",
                name="Analyst Agent",
                skills=[
                    Skill(
                        name="Data Analysis",
                        category=SkillCategory.ANALYSIS,
                        description="Analyze data and identify patterns",
                        confidence_score=0.95,
                        validation_methods=["statistical_analysis", "peer_review"]
                    ),
                    Skill(
                        name="Research",
                        category=SkillCategory.RESEARCH,
                        description="Conduct research and gather information",
                        confidence_score=0.90,
                        validation_methods=["source_verification", "fact_checking"]
                    )
                ],
                reliability_score=0.92,
                hallucination_rate=0.03
            ),
            Agent(
                id="agent_2",
                name="Execution Agent",
                skills=[
                    Skill(
                        name="Code Execution",
                        category=SkillCategory.EXECUTION,
                        description="Execute code and run commands",
                        confidence_score=0.98,
                        validation_methods=["output_validation", "error_checking"]
                    ),
                    Skill(
                        name="System Operations",
                        category=SkillCategory.EXECUTION,
                        description="Perform system operations and maintenance",
                        confidence_score=0.93,
                        validation_methods=["status_checking", "logs_analysis"]
                    )
                ],
                reliability_score=0.95,
                hallucination_rate=0.02
            ),
            Agent(
                id="agent_3",
                name="Communication Agent",
                skills=[
                    Skill(
                        name="Documentation",
                        category=SkillCategory.COMMUNICATION,
                        description="Create documentation and reports",
                        confidence_score=0.88,
                        validation_methods=["readability_check", "grammar_check"]
                    ),
                    Skill(
                        name="Presentation",
                        category=SkillCategory.COMMUNICATION,
                        description="Create presentations and visualizations",
                        confidence_score=0.85,
                        validation_methods=["design_check", "content_relevance"]
                    )
                ],
                reliability_score=0.89,
                hallucination_rate=0.05
            ),
            Agent(
                id="agent_4",
                name="Creation Agent",
                skills=[
                    Skill(
                        name="Content Creation",
                        category=SkillCategory.CREATION,
                        description="Create content for various platforms",
                        confidence_score=0.90,
                        validation_methods=["originality_check", "quality_assessment"]
                    ),
                    Skill(
                        name="Code Generation",
                        category=SkillCategory.CREATION,
                        description="Generate code and scripts",
                        confidence_score=0.87,
                        validation_methods=["syntax_check", "testing"]
                    )
                ],
                reliability_score=0.88,
                hallucination_rate=0.06
            ),
            Agent(
                id="agent_5",
                name="Validation Agent",
                skills=[
                    Skill(
                        name="Fact Checking",
                        category=SkillCategory.VALIDATION,
                        description="Verify facts and validate information",
                        confidence_score=0.97,
                        validation_methods=["cross_referencing", "expert_verification"]
                    ),
                    Skill(
                        name="Quality Assurance",
                        category=SkillCategory.VALIDATION,
                        description="Check quality and consistency",
                        confidence_score=0.94,
                        validation_methods=["standards_check", "compliance_verification"]
                    )
                ],
                reliability_score=0.96,
                hallucination_rate=0.01
            )
        ]
    
    def select_agents_for_task(self, task: Task, min_agents: int = 3) -> List[Agent]:
        """Select appropriate agents for a task with minimum number requirement"""
        suitable_agents = []
        
        for agent in self.agents:
            # Check if agent has all required skills
            agent_skills = [skill.category for skill in agent.skills]
            has_required_skills = all(skill in agent_skills for skill in task.required_skills)
            
            if has_required_skills:
                suitable_agents.append(agent)
        
        # Ensure we have at least min_agents
        if len(suitable_agents) < min_agents:
            # Add additional agents with overlapping skills
            additional_agents = []
            for agent in self.agents:
                if agent not in suitable_agents:
                    agent_skills = [skill.category for skill in agent.skills]
                    overlapping_skills = set(agent_skills) & set(task.required_skills)
                    if overlapping_skills and len(additional_agents) < (min_agents - len(suitable_agents)):
                        additional_agents.append(agent)
            suitable_agents.extend(additional_agents)
        
        return suitable_agents
    
    def assign_task(self, task: Task) -> List[TaskResult]:
        """Assign task to selected agents and collect results"""
        agents = self.select_agents_for_task(task)
        results = []
        
        for agent in agents:
            # Simulate agent processing time
            time.sleep(0.5)
            
            # Generate mock result (in real system, this would be actual agent output)
            result = self._generate_mock_result(task, agent)
            
            # Check for hallucinations
            hallucinations = self.skill_system.check_hallucination(str(result), task.description)
            
            # Validate result
            validation_scores = self.skill_system.validate_response(str(result), task)
            
            # Create task result
            task_result = TaskResult(
                task_id=task.id,
                agent_id=agent.id,
                result=result,
                confidence=agent.reliability_score,
                validation_scores=validation_scores,
                timestamp=time.time(),
                hallucination_checks=hallucinations
            )
            
            results.append(task_result)
        
        # Store in history
        self.task_history.append({"task": task, "results": results})
        
        return results
    
    def _generate_mock_result(self, task: Task, agent: Agent) -> Dict[str, Any]:
        """Generate mock result for testing purposes"""
        return {
            "agent": agent.name,
            "response": f"Completed task: {task.description}",
            "skills_used": [skill.name for skill in agent.skills],
            "processing_time": 2.5,
            "additional_info": "Mock data for testing purposes"
        }
    
    def evaluate_results(self, results: List[TaskResult]) -> Dict[str, Any]:
        """Evaluate and rank task results"""
        # Calculate overall scores
        scored_results = []
        for result in results:
            # Weighted average of confidence and validation scores
            validation_avg = sum(result.validation_scores.values()) / len(result.validation_scores)
            overall_score = (result.confidence * 0.6) + (validation_avg * 0.4)
            
            # Penalty for hallucinations
            hallucination_penalty = len(result.hallucination_checks) * 0.1
            overall_score = max(0.0, overall_score - hallucination_penalty)
            
            scored_results.append({
                "result": result,
                "score": overall_score
            })
        
        # Rank results
        scored_results.sort(key=lambda x: x["score"], reverse=True)
        
        return {
            "best_result": scored_results[0] if scored_results else None,
            "all_results": scored_results,
            "average_score": sum(r["score"] for r in scored_results) / len(scored_results) if scored_results else 0,
            "hallucination_count": sum(len(r["result"].hallucination_checks) for r in scored_results)
        }
    
    def execute_task_with_ensemble(self, task: Task) -> Dict[str, Any]:
        """Execute task with ensemble of agents and select best result"""
        # Assign task to multiple agents
        results = self.assign_task(task)
        
        # Evaluate results
        evaluation = self.evaluate_results(results)
        
        return evaluation
    
    def get_agent_performance(self) -> List[Dict[str, Any]]:
        """Get performance metrics for all agents"""
        performance = []
        
        for agent in self.agents:
            agent_results = [r for task_hist in self.task_history for r in task_hist["results"] if r.agent_id == agent.id]
            
            performance.append({
                "agent_id": agent.id,
                "name": agent.name,
                "tasks_completed": len(agent_results),
                "average_score": sum(
                    (r.confidence * 0.6) + (sum(r.validation_scores.values())/len(r.validation_scores)*0.4) 
                    for r in agent_results
                ) / len(agent_results) if agent_results else 0,
                "hallucination_rate": agent.hallucination_rate,
                "skills": [{"name": s.name, "confidence": s.confidence_score} for s in agent.skills]
            })
        
        return performance


class RailsIntegration:
    """Integration with Ruby on Rails applications"""
    
    def __init__(self, rails_app_path: str = "./rails_app"):
        self.rails_app_path = rails_app_path
        self.setup_complete = False
    
    def setup_rails_app(self) -> bool:
        """Set up a new Rails application for integration"""
        import subprocess
        
        try:
            # Check if rails command is available
            rails_check = subprocess.run(["rails", "--version"], capture_output=True, text=True)
            if rails_check.returncode != 0:
                raise Exception("Rails command not found")
            
            # Create new Rails app if not exists
            import os
            if not os.path.exists(self.rails_app_path):
                subprocess.run(["rails", "new", self.rails_app_path], check=True)
            
            # Add necessary gems to Gemfile
            gemfile_path = os.path.join(self.rails_app_path, "Gemfile")
            if os.path.exists(gemfile_path):
                with open(gemfile_path, "r") as f:
                    gemfile_content = f.read()
                
                # Add JSON and HTTParty gems for API integration
                if "gem 'json'" not in gemfile_content:
                    gemfile_content += "\ngem 'json'\n"
                if "gem 'httparty'" not in gemfile_content:
                    gemfile_content += "gem 'httparty'\n"
                
                with open(gemfile_path, "w") as f:
                    f.write(gemfile_content)
            
            # Install dependencies
            subprocess.run(["bundle", "install"], cwd=self.rails_app_path, check=True)
            
            self.setup_complete = True
            return True
        
        except Exception as e:
            print(f"Error setting up Rails app: {e}")
            return False
    
    def create_api_controller(self, name: str) -> bool:
        """Create a new API controller in Rails app"""
        import subprocess
        
        try:
            if not self.setup_complete:
                raise Exception("Rails app not set up")
            
            # Generate API controller
            subprocess.run(
                ["rails", "generate", "controller", f"{name}_api", "index", "show", "create", "update", "destroy"],
                cwd=self.rails_app_path,
                check=True
            )
            
            return True
        
        except Exception as e:
            print(f"Error creating API controller: {e}")
            return False
    
    def generate_api_route(self, controller: str, resource: str) -> bool:
        """Generate API routes in Rails"""
        import subprocess
        
        try:
            if not self.setup_complete:
                raise Exception("Rails app not set up")
            
            # Add resource route to config/routes.rb
            routes_path = os.path.join(self.rails_app_path, "config", "routes.rb")
            with open(routes_path, "r") as f:
                routes_content = f.read()
            
            api_route = f"  namespace :api, defaults: {{ format: :json }} do\n    resources :{resource.pluralize}\n  end\n"
            
            if api_route not in routes_content:
                routes_content = routes_content.replace("end", api_route + "end")
                
                with open(routes_path, "w") as f:
                    f.write(routes_content)
            
            return True
        
        except Exception as e:
            print(f"Error generating API route: {e}")
            return False
    
    def start_rails_server(self, port: int = 3000) -> bool:
        """Start Rails server"""
        import subprocess
        
        try:
            if not self.setup_complete:
                raise Exception("Rails app not set up")
            
            # Start server in background
            subprocess.Popen(
                ["rails", "server", "-p", str(port)],
                cwd=self.rails_app_path,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Wait for server to start
            import time
            time.sleep(3)
            
            return True
        
        except Exception as e:
            print(f"Error starting Rails server: {e}")
            return False
    
    def test_api_connection(self, port: int = 3000) -> bool:
        """Test connection to Rails API"""
        import requests
        
        try:
            response = requests.get(f"http://localhost:{port}/api/v1/health")
            return response.status_code == 200
        
        except Exception as e:
            print(f"Error testing API connection: {e}")
            return False


# Example usage
if __name__ == "__main__":
    print("=== Chatty Skill-Based Architecture ===")
    
    # Initialize orchestrator
    orchestrator = SkillBasedOrchestrator()
    
    # Example task
    test_task = Task(
        id="test_task_1",
        description="Analyze current system performance and provide recommendations",
        required_skills=[SkillCategory.ANALYSIS, SkillCategory.RESEARCH],
        difficulty=0.7,
        expected_output_format="markdown",
        validation_criteria=["factually_correct", "complete", "structured"]
    )
    
    # Execute task with ensemble of agents
    print("\nExecuting task with 3+ agents...")
    evaluation = orchestrator.execute_task_with_ensemble(test_task)
    
    # Display results
    print(f"\nBest Result (Score: {evaluation['best_result']['score']:.2f}):")
    print(f"  Agent: {evaluation['best_result']['result'].agent_id}")
    print(f"  Result: {evaluation['best_result']['result'].result}")
    
    print(f"\nHallucinations: {evaluation['hallucination_count']}")
    print(f"Average Score: {evaluation['average_score']:.2f}")
    
    # Display agent performance
    print("\n=== Agent Performance ===")
    performance = orchestrator.get_agent_performance()
    for agent in performance:
        print(f"{agent['name']}: {agent['tasks_completed']} tasks, {agent['average_score']:.2f} avg score")
    
    # Test Rails integration
    print("\n=== Rails Integration ===")
    rails_integration = RailsIntegration()
    
    if rails_integration.setup_rails_app():
        print("✓ Rails app setup complete")
        
        if rails_integration.create_api_controller("system_status"):
            print("✓ API controller created")
        
        if rails_integration.generate_api_route("system_status", "system_status"):
            print("✓ API routes generated")
        
        if rails_integration.start_rails_server():
            print("✓ Rails server started")
        
        if rails_integration.test_api_connection():
            print("✓ API connection successful")
        else:
            print("⚠️  API connection failed (server might still be starting)")
    else:
        print("⚠️  Rails app setup failed")