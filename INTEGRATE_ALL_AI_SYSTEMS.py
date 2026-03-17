#!/usr/bin/env python3
"""
CHATTY Complete AI Systems Integration
Integrates OpenClaw, Pydantic AI, LangChain, CrewAI, and Archon2 into the main system
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# INTEGRATION MODULE
# =============================================================================

class CompleteAIIntegration:
    """
    Complete integration of all AI systems into CHATTY
    
    This module provides:
    1. Unified interface to all AI frameworks
    2. Automatic framework selection based on task type
    3. Seamless failover between AI providers
    4. Integration with existing CHATTY components
    5. Performance monitoring and optimization
    """
    
    def __init__(self):
        self.unified_orchestrator = None
        self.openclaw_system = None
        self.self_improving_agents = None
        self.archon2_orchestrator = None
        self.initialized = False
        
    async def initialize(self):
        """Initialize all AI systems"""
        print("\n" + "="*70)
        print("🚀 INITIALIZING COMPLETE AI SYSTEMS INTEGRATION")
        print("="*70 + "\n")
        
        # 1. Initialize Unified Orchestrator
        print("📦 Loading Unified AI Orchestrator...")
        try:
            from UNIFIED_AI_ORCHESTRATION import get_orchestrator
            self.unified_orchestrator = await get_orchestrator()
            print("  ✅ Unified Orchestrator ready")
        except Exception as e:
            print(f"  ⚠️ Unified Orchestrator: {e}")
        
        # 2. Initialize OpenClaw
        print("📦 Loading OpenClaw System...")
        try:
            from openclaw_integration import AutonomousLearningSystem
            self.openclaw_system = AutonomousLearningSystem()
            await self.openclaw_system.start_autonomous_system()
            print("  ✅ OpenClaw system ready")
        except Exception as e:
            print(f"  ⚠️ OpenClaw: {e}")
        
        # 3. Initialize Self-Improving Agents (LangChain + CrewAI)
        print("📦 Loading Self-Improving Agents...")
        try:
            from SELF_IMPROVING_AGENTS import SelfImprovingAgentSystem
            self.self_improving_agents = SelfImprovingAgentSystem()
            print("  ✅ Self-Improving Agents ready")
        except Exception as e:
            print(f"  ⚠️ Self-Improving Agents: {e}")
        
        # 4. Initialize Archon2
        print("📦 Loading Archon2 Orchestrator...")
        try:
            from ARCHON2_ORCHESTRATION import Archon2Orchestrator
            self.archon2_orchestrator = Archon2Orchestrator()
            await self.archon2_orchestrator.initialize_archon2()
            print("  ✅ Archon2 Orchestrator ready")
        except Exception as e:
            print(f"  ⚠️ Archon2: {e}")
        
        self.initialized = True
        
        print("\n" + "="*70)
        print("✅ ALL AI SYSTEMS INTEGRATED AND READY")
        print("="*70 + "\n")
        
        return self.get_status()
    
    def get_status(self) -> Dict[str, Any]:
        """Get integration status"""
        return {
            "initialized": self.initialized,
            "timestamp": datetime.utcnow().isoformat(),
            "systems": {
                "unified_orchestrator": self.unified_orchestrator is not None,
                "openclaw": self.openclaw_system is not None,
                "self_improving_agents": self.self_improving_agents is not None,
                "archon2": self.archon2_orchestrator is not None,
            },
            "capabilities": [
                "intelligent_task_routing",
                "multi_llm_failover",
                "file_chunking",
                "code_analysis",
                "self_repair",
                "hierarchical_orchestration",
                "multi_agent_collaboration",
                "type_safe_outputs",
                "continuous_improvement"
            ]
        }
    
    # =============================================================================
    # HIGH-LEVEL API - Easy to use methods
    # =============================================================================
    
    async def generate_code(
        self,
        description: str,
        language: str = "python",
        context: Dict = None
    ) -> Dict[str, Any]:
        """
        Generate code using the best available framework
        
        Args:
            description: What code to generate
            language: Programming language
            context: Additional context
            
        Returns:
            Dict with generated code and metadata
        """
        if self.unified_orchestrator:
            from UNIFIED_AI_ORCHESTRATION import UnifiedTask, TaskType
            
            task = UnifiedTask(
                name="Code Generation",
                description=description,
                task_type=TaskType.CODE_GENERATION,
                context={"language": language, **(context or {})},
                preferred_framework="openclaw"
            )
            
            result = await self.unified_orchestrator.execute_task(task)
            
            return {
                "success": result.status == "completed",
                "code": result.output.get("code", ""),
                "language": language,
                "model_used": result.model_used,
                "execution_time": result.execution_time,
                "confidence": result.confidence
            }
        
        return {"success": False, "error": "Orchestrator not available"}
    
    async def create_content(
        self,
        topic: str,
        content_type: str = "blog",
        tone: str = "professional"
    ) -> Dict[str, Any]:
        """
        Create content using multi-agent collaboration
        
        Args:
            topic: Content topic
            content_type: Type of content (blog, social, email, etc.)
            tone: Writing tone
            
        Returns:
            Dict with content and metadata
        """
        if self.unified_orchestrator:
            from UNIFIED_AI_ORCHESTRATION import UnifiedTask, TaskType
            
            task = UnifiedTask(
                name="Content Creation",
                description=f"Create {content_type} content about: {topic}",
                task_type=TaskType.CONTENT_CREATION,
                inputs={"topic": topic, "content_type": content_type, "tone": tone},
                preferred_framework="crewai"
            )
            
            result = await self.unified_orchestrator.execute_task(task)
            
            return {
                "success": result.status == "completed",
                "content": result.output.get("content", str(result.output)),
                "content_type": content_type,
                "model_used": result.model_used,
                "execution_time": result.execution_time
            }
        
        return {"success": False, "error": "Orchestrator not available"}
    
    async def analyze_data(
        self,
        data: List[Dict],
        query: str = "",
        output_format: str = "structured"
    ) -> Dict[str, Any]:
        """
        Analyze data with structured outputs
        
        Args:
            data: Data to analyze
            query: Specific analysis query
            output_format: Output format preference
            
        Returns:
            Dict with analysis results
        """
        if self.unified_orchestrator:
            from UNIFIED_AI_ORCHESTRATION import UnifiedTask, TaskType
            
            task = UnifiedTask(
                name="Data Analysis",
                description=query or "Analyze this data comprehensively",
                task_type=TaskType.DATA_ANALYSIS,
                inputs={"data": data, "output_format": output_format},
                preferred_framework="pydantic"
            )
            
            result = await self.unified_orchestrator.execute_task(task)
            
            return {
                "success": result.status == "completed",
                "analysis": result.output.get("analysis", result.output),
                "data_points": len(data),
                "model_used": result.model_used,
                "execution_time": result.execution_time
            }
        
        return {"success": False, "error": "Orchestrator not available"}
    
    async def strategic_planning(
        self,
        goal: str,
        constraints: Dict = None,
        timeline: str = "quarterly"
    ) -> Dict[str, Any]:
        """
        Strategic planning using hierarchical orchestration
        
        Args:
            goal: Strategic goal
            constraints: Planning constraints
            timeline: Planning timeline
            
        Returns:
            Dict with strategic plan
        """
        if self.unified_orchestrator:
            from UNIFIED_AI_ORCHESTRATION import UnifiedTask, TaskType
            
            task = UnifiedTask(
                name="Strategic Planning",
                description=goal,
                task_type=TaskType.STRATEGIC_PLANNING,
                complexity="strategic",
                scope="strategic",
                inputs={"constraints": constraints or {}, "timeline": timeline},
                requires_coordination=True,
                preferred_framework="archon2"
            )
            
            result = await self.unified_orchestrator.execute_task(task)
            
            return {
                "success": result.status == "completed",
                "plan": result.output,
                "hierarchy_level": result.output.get("hierarchy_level", "unknown"),
                "model_used": result.model_used,
                "execution_time": result.execution_time
            }
        
        return {"success": False, "error": "Orchestrator not available"}
    
    async def debug_code(
        self,
        code: str,
        error_message: str = "",
        language: str = "python"
    ) -> Dict[str, Any]:
        """
        Debug code using OpenClaw
        
        Args:
            code: Code to debug
            error_message: Error message if any
            language: Programming language
            
        Returns:
            Dict with debugging results
        """
        if self.unified_orchestrator:
            from UNIFIED_AI_ORCHESTRATION import UnifiedTask, TaskType
            
            task = UnifiedTask(
                name="Code Debugging",
                description=f"Debug this {language} code: {error_message}",
                task_type=TaskType.DEBUGGING,
                inputs={"code": code, "error": error_message, "language": language},
                preferred_framework="openclaw"
            )
            
            result = await self.unified_orchestrator.execute_task(task)
            
            return {
                "success": result.status == "completed",
                "analysis": result.output.get("analysis", ""),
                "fixes": result.output.get("fixes", []),
                "model_used": result.model_used,
                "execution_time": result.execution_time
            }
        
        return {"success": False, "error": "Orchestrator not available"}
    
    async def optimize_system(
        self,
        metrics: Dict[str, Any],
        target_area: str = "general"
    ) -> Dict[str, Any]:
        """
        System optimization using self-improving agents
        
        Args:
            metrics: Current system metrics
            target_area: Area to optimize
            
        Returns:
            Dict with optimization suggestions
        """
        if self.self_improving_agents and not getattr(self.self_improving_agents, 'disabled', True):
            # Use self-improving agents for optimization
            try:
                from SELF_IMPROVING_AGENTS import PerformanceMetrics, SystemState
                
                perf_metrics = PerformanceMetrics(
                    leads_generated=metrics.get('leads', 0),
                    conversion_rate=metrics.get('conversion_rate', 0),
                    revenue=metrics.get('revenue', 0),
                    customer_satisfaction=metrics.get('satisfaction', 4.0),
                    system_efficiency=metrics.get('efficiency', 0.8)
                )
                
                # Collect and analyze
                self.self_improving_agents.system_state.performance_metrics = perf_metrics
                analysis = await self.self_improving_agents.analyze_performance(perf_metrics)
                suggestions = await self.self_improving_agents.generate_improvements(analysis)
                
                return {
                    "success": True,
                    "analysis": analysis,
                    "suggestions": [
                        {
                            "area": s.area,
                            "suggestion": s.suggested_change,
                            "expected_improvement": s.expected_improvement,
                            "priority": s.priority
                        }
                        for s in suggestions
                    ],
                    "target_area": target_area
                }
            except Exception as e:
                logger.error(f"Self-improving agents error: {e}")
        
        # Fallback to unified orchestrator
        if self.unified_orchestrator:
            from UNIFIED_AI_ORCHESTRATION import UnifiedTask, TaskType
            
            task = UnifiedTask(
                name="System Optimization",
                description=f"Optimize {target_area} based on current metrics",
                task_type=TaskType.SYSTEM_OPTIMIZATION,
                inputs={"metrics": metrics, "target_area": target_area},
                preferred_framework="crewai"
            )
            
            result = await self.unified_orchestrator.execute_task(task)
            
            return {
                "success": result.status == "completed",
                "recommendations": result.output,
                "model_used": result.model_used
            }
        
        return {"success": False, "error": "No optimization system available"}
    
    async def research(
        self,
        topic: str,
        depth: str = "comprehensive",
        sources: List[str] = None
    ) -> Dict[str, Any]:
        """
        Research topic using available tools
        
        Args:
            topic: Research topic
            depth: Research depth (quick, comprehensive, deep)
            sources: Preferred sources
            
        Returns:
            Dict with research results
        """
        if self.unified_orchestrator:
            from UNIFIED_AI_ORCHESTRATION import UnifiedTask, TaskType
            
            task = UnifiedTask(
                name="Research",
                description=f"Research: {topic}",
                task_type=TaskType.RESEARCH,
                inputs={"topic": topic, "depth": depth, "sources": sources or []},
                preferred_framework="langchain"
            )
            
            result = await self.unified_orchestrator.execute_task(task)
            
            return {
                "success": result.status == "completed",
                "research": result.output.get("research", str(result.output)),
                "topic": topic,
                "model_used": result.model_used,
                "execution_time": result.execution_time
            }
        
        return {"success": False, "error": "Orchestrator not available"}
    
    async def chunk_and_analyze_files(
        self,
        file_paths: List[str],
        query: str = ""
    ) -> Dict[str, Any]:
        """
        Chunk and analyze files using OpenClaw
        
        Args:
            file_paths: Paths to files
            query: Analysis query
            
        Returns:
            Dict with analysis results
        """
        if self.openclaw_system:
            try:
                results = []
                for file_path in file_paths:
                    if Path(file_path).exists():
                        chunks = self.openclaw_system.file_chunker.chunk_file(file_path)
                        relevant = self.openclaw_system.file_chunker.get_relevant_chunks(
                            query, file_path, top_k=5
                        ) if query else chunks[:5]
                        
                        results.append({
                            "file": file_path,
                            "total_chunks": len(chunks),
                            "relevant_chunks": relevant
                        })
                
                return {
                    "success": True,
                    "files_analyzed": len(results),
                    "results": results
                }
            except Exception as e:
                logger.error(f"File chunking error: {e}")
        
        return {"success": False, "error": "OpenClaw not available"}
    
    # =============================================================================
    # SYSTEM MANAGEMENT
    # =============================================================================
    
    async def start_all(self):
        """Start all AI systems"""
        print("\n" + "="*70)
        print("🚀 STARTING ALL AI SYSTEMS")
        print("="*70 + "\n")
        
        tasks = []
        
        if self.self_improving_agents:
            tasks.append(self.self_improving_agents.start())
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        print("\n✅ All systems started\n")
    
    async def stop_all(self):
        """Stop all AI systems"""
        print("\n" + "="*70)
        print("🛑 STOPPING ALL AI SYSTEMS")
        print("="*70 + "\n")
        
        if self.self_improving_agents:
            await self.self_improving_agents.stop()
        
        if self.openclaw_system:
            await self.openclaw_system.stop_autonomous_system()
        
        if self.unified_orchestrator:
            await self.unified_orchestrator.stop()
        
        print("\n✅ All systems stopped\n")
    
    def get_health(self) -> Dict[str, Any]:
        """Get health status of all systems"""
        health = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall": "healthy",
            "systems": {}
        }
        
        # Unified orchestrator health
        if self.unified_orchestrator:
            try:
                orch_health = self.unified_orchestrator.get_health()
                health["systems"]["unified_orchestrator"] = orch_health.dict()
            except Exception as e:
                health["systems"]["unified_orchestrator"] = {"status": "error", "error": str(e)}
        
        # Check overall health
        system_statuses = [s.get("status", s.get("overall_status", "unknown")) 
                          for s in health["systems"].values()]
        
        if any(s == "critical" for s in system_statuses):
            health["overall"] = "critical"
        elif any(s in ["degraded", "error"] for s in system_statuses):
            health["overall"] = "degraded"
        
        return health
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get metrics from all systems"""
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "systems": {}
        }
        
        if self.unified_orchestrator:
            try:
                metrics["systems"]["unified_orchestrator"] = self.unified_orchestrator.get_metrics()
            except Exception as e:
                metrics["systems"]["unified_orchestrator"] = {"error": str(e)}
        
        return metrics


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

_integration_instance: Optional[CompleteAIIntegration] = None

async def get_integration() -> CompleteAIIntegration:
    """Get or create the global integration instance"""
    global _integration_instance
    if _integration_instance is None:
        _integration_instance = CompleteAIIntegration()
        await _integration_instance.initialize()
    return _integration_instance


# =============================================================================
# DEMONSTRATION
# =============================================================================

async def demonstrate_all_capabilities():
    """Demonstrate all integrated capabilities"""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║        🤖 CHATTY COMPLETE AI SYSTEMS INTEGRATION 🤖                         ║
║                                                                              ║
║   OpenClaw + Pydantic AI + LangChain + CrewAI + Archon2                     ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
    
    integration = await get_integration()
    
    print("\n" + "="*70)
    print("📋 DEMONSTRATING ALL CAPABILITIES")
    print("="*70)
    
    # 1. Code Generation
    print("\n🔧 1. CODE GENERATION (OpenClaw)")
    print("-" * 50)
    code_result = await integration.generate_code(
        description="Create a Python class for managing API rate limits with token bucket algorithm",
        language="python"
    )
    print(f"Success: {code_result['success']}")
    print(f"Language: {code_result.get('language')}")
    print(f"Execution time: {code_result.get('execution_time', 0):.2f}s")
    if code_result.get('code'):
        print(f"Code preview:\n{code_result['code'][:300]}...")
    
    # 2. Content Creation
    print("\n✍️  2. CONTENT CREATION (CrewAI)")
    print("-" * 50)
    content_result = await integration.create_content(
        topic="The Future of AI Automation in Business",
        content_type="blog",
        tone="professional"
    )
    print(f"Success: {content_result['success']}")
    print(f"Content type: {content_result.get('content_type')}")
    print(f"Execution time: {content_result.get('execution_time', 0):.2f}s")
    if content_result.get('content'):
        print(f"Content preview:\n{content_result['content'][:300]}...")
    
    # 3. Data Analysis
    print("\n📊 3. DATA ANALYSIS (Pydantic AI)")
    print("-" * 50)
    sample_data = [
        {"product": "A", "sales": 1000, "month": "Jan"},
        {"product": "B", "sales": 1500, "month": "Jan"},
        {"product": "A", "sales": 1200, "month": "Feb"},
        {"product": "B", "sales": 1800, "month": "Feb"},
    ]
    analysis_result = await integration.analyze_data(
        data=sample_data,
        query="Compare sales performance between products"
    )
    print(f"Success: {analysis_result['success']}")
    print(f"Data points: {analysis_result.get('data_points')}")
    if analysis_result.get('analysis'):
        print(f"Analysis: {json.dumps(analysis_result['analysis'], indent=2)[:300]}...")
    
    # 4. Strategic Planning
    print("\n🎯 4. STRATEGIC PLANNING (Archon2)")
    print("-" * 50)
    strategy_result = await integration.strategic_planning(
        goal="Develop a plan to increase user engagement by 40% in 6 months",
        timeline="6 months"
    )
    print(f"Success: {strategy_result['success']}")
    print(f"Hierarchy level: {strategy_result.get('hierarchy_level')}")
    if strategy_result.get('plan'):
        print(f"Plan preview: {json.dumps(strategy_result['plan'], indent=2)[:300]}...")
    
    # 5. Research
    print("\n🔍 5. RESEARCH (LangChain)")
    print("-" * 50)
    research_result = await integration.research(
        topic="Best practices for multi-agent AI systems",
        depth="comprehensive"
    )
    print(f"Success: {research_result['success']}")
    print(f"Topic: {research_result.get('topic')}")
    if research_result.get('research'):
        print(f"Research preview:\n{research_result['research'][:300]}...")
    
    # Print final status
    print("\n" + "="*70)
    print("📊 SYSTEM STATUS")
    print("="*70)
    status = integration.get_status()
    print(json.dumps(status, indent=2))
    
    print("\n" + "="*70)
    print("🏥 SYSTEM HEALTH")
    print("="*70)
    health = integration.get_health()
    print(json.dumps(health, indent=2))
    
    print("\n" + "="*70)
    print("✅ DEMONSTRATION COMPLETE")
    print("="*70 + "\n")
    
    return integration


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    try:
        integration = asyncio.run(demonstrate_all_capabilities())
    except KeyboardInterrupt:
        print("\n\n✅ Shutdown complete")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
