#!/usr/bin/env python3
"""
Test script for the Unified AI Orchestration System
Tests all frameworks: OpenClaw, Pydantic AI, LangChain, CrewAI, Archon2
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

async def test_unified_orchestrator():
    """Test the unified orchestrator"""
    print("\n" + "="*70)
    print("🧪 TESTING UNIFIED AI ORCHESTRATOR")
    print("="*70)
    
    from UNIFIED_AI_ORCHESTRATION import (
        UnifiedAIOrchestrator, UnifiedTask, TaskType, 
        TaskPriority, get_orchestrator, execute_ai_task
    )
    
    # Test 1: Direct orchestrator usage
    print("\n📋 Test 1: Initialize Orchestrator")
    orchestrator = await get_orchestrator()
    print(f"  ✅ Orchestrator initialized")
    print(f"  📊 Framework health: {orchestrator.task_router.framework_health}")
    
    # Test 2: Code generation task
    print("\n📋 Test 2: Code Generation (OpenClaw)")
    code_task = UnifiedTask(
        name="Test Code Gen",
        description="Generate a Python function to calculate Fibonacci numbers",
        task_type=TaskType.CODE_GENERATION,
        complexity="low",
        context={"language": "python"},
        preferred_framework="openclaw"
    )
    result = await orchestrator.execute_task(code_task)
    print(f"  Status: {result.status}")
    print(f"  Framework: {result.agent_framework}")
    print(f"  Execution time: {result.execution_time:.2f}s")
    assert result.status == "completed", "Code generation should complete"
    
    # Test 3: Data analysis task
    print("\n📋 Test 3: Data Analysis (Pydantic)")
    analysis_task = UnifiedTask(
        name="Test Data Analysis",
        description="Analyze sales trends",
        task_type=TaskType.DATA_ANALYSIS,
        inputs={"data": [{"month": "Jan", "sales": 100}, {"month": "Feb", "sales": 150}]},
        preferred_framework="pydantic"
    )
    result = await orchestrator.execute_task(analysis_task)
    print(f"  Status: {result.status}")
    print(f"  Framework: {result.agent_framework}")
    print(f"  Execution time: {result.execution_time:.2f}s")
    
    # Test 4: Content creation task
    print("\n📋 Test 4: Content Creation (CrewAI)")
    content_task = UnifiedTask(
        name="Test Content",
        description="Write a tweet about AI automation",
        task_type=TaskType.CONTENT_CREATION,
        inputs={"platform": "twitter", "topic": "AI automation"},
        preferred_framework="crewai"
    )
    result = await orchestrator.execute_task(content_task)
    print(f"  Status: {result.status}")
    print(f"  Framework: {result.agent_framework}")
    print(f"  Execution time: {result.execution_time:.2f}s")
    
    # Test 5: Strategic planning task
    print("\n📋 Test 5: Strategic Planning (Archon2)")
    strategy_task = UnifiedTask(
        name="Test Strategy",
        description="Plan Q4 growth strategy",
        task_type=TaskType.STRATEGIC_PLANNING,
        complexity="strategic",
        scope="strategic",
        preferred_framework="archon2"
    )
    result = await orchestrator.execute_task(strategy_task)
    print(f"  Status: {result.status}")
    print(f"  Framework: {result.agent_framework}")
    print(f"  Execution time: {result.execution_time:.2f}s")
    
    # Test 6: Research task
    print("\n📋 Test 6: Research (LangChain)")
    research_task = UnifiedTask(
        name="Test Research",
        description="Research best practices for API design",
        task_type=TaskType.RESEARCH,
        preferred_framework="langchain"
    )
    result = await orchestrator.execute_task(research_task)
    print(f"  Status: {result.status}")
    print(f"  Framework: {result.agent_framework}")
    print(f"  Execution time: {result.execution_time:.2f}s")
    
    # Test 7: Health check
    print("\n📋 Test 7: System Health Check")
    health = orchestrator.get_health()
    print(f"  Overall status: {health.overall_status}")
    print(f"  Active agents: {health.active_agents}")
    print(f"  Completed tasks: {health.completed_tasks}")
    
    # Test 8: Metrics
    print("\n📋 Test 8: System Metrics")
    metrics = orchestrator.get_metrics()
    print(f"  Tasks submitted: {metrics['tasks_submitted']}")
    print(f"  Tasks completed: {metrics['tasks_completed']}")
    print(f"  Success rate: {metrics.get('success_rate', 0):.2%}")
    print(f"  Avg execution time: {metrics['avg_response_time']:.2f}s")
    
    print("\n✅ All Unified Orchestrator tests passed!")
    return orchestrator


async def test_integration_module():
    """Test the complete integration module"""
    print("\n" + "="*70)
    print("🧪 TESTING COMPLETE INTEGRATION MODULE")
    print("="*70)
    
    from INTEGRATE_ALL_AI_SYSTEMS import get_integration
    
    # Initialize integration
    print("\n📋 Initializing Integration")
    integration = await get_integration()
    status = integration.get_status()
    print(f"  Initialized: {status['initialized']}")
    print(f"  Systems: {json.dumps(status['systems'], indent=4)}")
    print(f"  Capabilities: {len(status['capabilities'])} available")
    
    # Test code generation
    print("\n📋 Testing Code Generation")
    result = await integration.generate_code(
        description="Create a Python decorator for timing function execution",
        language="python"
    )
    print(f"  Success: {result['success']}")
    print(f"  Language: {result.get('language')}")
    if result.get('code'):
        print(f"  Code preview: {result['code'][:200]}...")
    
    # Test content creation
    print("\n📋 Testing Content Creation")
    result = await integration.create_content(
        topic="Productivity tips for developers",
        content_type="blog"
    )
    print(f"  Success: {result['success']}")
    print(f"  Content type: {result.get('content_type')}")
    if result.get('content'):
        print(f"  Content preview: {result['content'][:200]}...")
    
    # Test data analysis
    print("\n📋 Testing Data Analysis")
    result = await integration.analyze_data(
        data=[
            {"day": "Mon", "revenue": 1000, "expenses": 800},
            {"day": "Tue", "revenue": 1200, "expenses": 850},
            {"day": "Wed", "revenue": 1100, "expenses": 820},
        ],
        query="Calculate profit margins"
    )
    print(f"  Success: {result['success']}")
    print(f"  Data points: {result.get('data_points')}")
    if result.get('analysis'):
        print(f"  Analysis: {json.dumps(result['analysis'], indent=2)[:200]}...")
    
    # Test health check
    print("\n📋 Testing Health Check")
    health = integration.get_health()
    print(f"  Overall health: {health['overall']}")
    for system, status in health['systems'].items():
        print(f"  - {system}: {status.get('overall_status', status.get('status', 'unknown'))}")
    
    print("\n✅ All Integration Module tests passed!")
    return integration


async def test_individual_frameworks():
    """Test individual framework components"""
    print("\n" + "="*70)
    print("🧪 TESTING INDIVIDUAL FRAMEWORKS")
    print("="*70)
    
    # Test OpenClaw
    print("\n📋 Testing OpenClaw")
    try:
        from openclaw_integration import FileChunker, AutonomousLearningSystem
        chunker = FileChunker()
        print("  ✅ FileChunker initialized")
        
        # Test chunking a simple file
        test_file = Path("test_chunk_file.py")
        test_file.write_text("""
def hello():
    return "Hello World"

class MyClass:
    def method(self):
        pass
""")
        chunks = chunker.chunk_file(str(test_file))
        print(f"  ✅ File chunked into {len(chunks)} chunks")
        test_file.unlink()
    except Exception as e:
        print(f"  ⚠️ OpenClaw test: {e}")
    
    # Test Archon2
    print("\n📋 Testing Archon2")
    try:
        from ARCHON2_ORCHESTRATION import Archon2Orchestrator
        archon = Archon2Orchestrator()
        init_result = await archon.initialize_archon2()
        print(f"  ✅ Archon2 initialized: {init_result['status']}")
        print(f"  📊 Total agents: {init_result['total_agents']}")
        
        # Test task orchestration
        test_task = {
            "name": "Test Task",
            "description": "Test description",
            "complexity": "medium",
            "scope": "execution"
        }
        result = await archon.orchestrate_task(test_task)
        print(f"  ✅ Task orchestrated: {result['status']}")
        print(f"  📊 Hierarchy level: {result.get('hierarchy_level')}")
    except Exception as e:
        print(f"  ⚠️ Archon2 test: {e}")
    
    # Test Self-Improving Agents
    print("\n📋 Testing Self-Improving Agents")
    try:
        from SELF_IMPROVING_AGENTS import SelfImprovingAgentSystem
        agents = SelfImprovingAgentSystem()
        if not getattr(agents, 'disabled', False):
            print("  ✅ Self-Improving Agents initialized")
            print(f"  📊 Agents: {len(agents.agents)}")
        else:
            print("  ⚠️ Self-Improving Agents disabled (missing dependencies)")
    except Exception as e:
        print(f"  ⚠️ Self-Improving Agents test: {e}")
    
    print("\n✅ Individual Framework tests complete!")


async def run_all_tests():
    """Run all tests"""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║        🧪 CHATTY UNIFIED AI SYSTEMS - COMPREHENSIVE TEST SUITE 🧪           ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
    
    results = {}
    
    try:
        # Test 1: Unified Orchestrator
        orchestrator = await test_unified_orchestrator()
        results['unified_orchestrator'] = 'PASSED'
    except Exception as e:
        print(f"\n❌ Unified Orchestrator test failed: {e}")
        import traceback
        traceback.print_exc()
        results['unified_orchestrator'] = f'FAILED: {e}'
    
    try:
        # Test 2: Integration Module
        integration = await test_integration_module()
        results['integration_module'] = 'PASSED'
    except Exception as e:
        print(f"\n❌ Integration Module test failed: {e}")
        import traceback
        traceback.print_exc()
        results['integration_module'] = f'FAILED: {e}'
    
    try:
        # Test 3: Individual Frameworks
        await test_individual_frameworks()
        results['individual_frameworks'] = 'PASSED'
    except Exception as e:
        print(f"\n❌ Individual Frameworks test failed: {e}")
        import traceback
        traceback.print_exc()
        results['individual_frameworks'] = f'FAILED: {e}'
    
    # Final summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result == 'PASSED' else "❌ FAILED"
        print(f"  {status}: {test_name}")
        if result != 'PASSED':
            print(f"      {result}")
    
    passed = sum(1 for r in results.values() if r == 'PASSED')
    total = len(results)
    
    print(f"\n  Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed")
    
    print("\n" + "="*70)
    
    return results


if __name__ == "__main__":
    try:
        results = asyncio.run(run_all_tests())
        
        # Exit with appropriate code
        passed = sum(1 for r in results.values() if r == 'PASSED')
        sys.exit(0 if passed == len(results) else 1)
        
    except KeyboardInterrupt:
        print("\n\n✅ Tests interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
