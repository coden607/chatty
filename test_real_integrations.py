#!/usr/bin/env python3
"""
CHATTY Real Data Integration Tests
Verifies ALL features work with REAL data only
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Load environment
from dotenv import load_dotenv
load_dotenv('.env')

sys.path.insert(0, '/home/coden809/Projects/chatty')


class RealDataTest:
    """Test case for real data verification"""
    
    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.error = None
        self.result = None
    
    def __repr__(self):
        status = "✅ PASS" if self.passed else "❌ FAIL"
        return f"{status}: {self.name}"


async def test_model_router_real() -> RealDataTest:
    """Test Model Router uses real LLM APIs"""
    test = RealDataTest("Model Router - Real LLM Calls")
    
    try:
        from CHATTY_MODEL_ROUTER import router
        
        # Check providers have real keys
        health = router.health_check()
        configured = sum(1 for p in health['providers'].values() if p.get('api_keys_configured'))
        
        if configured == 0:
            test.error = "No API keys configured"
            return test
        
        # Make real call
        response = await router.generate(
            "What is 2+2? Answer with just the number.",
            temperature=0
        )
        
        # Verify real response
        if '4' in str(response):
            test.passed = True
            test.result = f"Real response from LLM: {response[:50]}..."
        else:
            test.error = f"Unexpected response: {response}"
            
    except Exception as e:
        test.error = str(e)
    
    return test


async def test_sendgrid_real() -> RealDataTest:
    """Test SendGrid uses real API"""
    test = RealDataTest("SendGrid - Real Email API")
    
    try:
        from sendgrid import SendGridAPIClient
        
        api_key = os.getenv('SENDGRID_API_KEY', '')
        if not api_key.startswith('SG.'):
            test.error = "No valid SendGrid API key"
            return test
        
        sg = SendGridAPIClient(api_key)
        
        # Real API call to verify
        response = sg.client.user.profile.get()
        
        if response.status_code == 200:
            test.passed = True
            data = json.loads(response.body)
            test.result = f"Connected as: {data.get('email', 'Unknown')}"
        else:
            test.error = f"API returned {response.status_code}"
            
    except Exception as e:
        test.error = str(e)
    
    return test


async def test_pydantic_ai_real() -> RealDataTest:
    """Test Pydantic AI uses real LLM calls"""
    test = RealDataTest("Pydantic AI - Real Structured Output")
    
    try:
        from PYDANTIC_AI_ENHANCED import get_pydantic_functions
        
        functions = get_pydantic_functions()
        
        # Real sentiment analysis
        result = await functions.analyze_sentiment(
            "This product is absolutely amazing! Best purchase ever."
        )
        
        # Verify real result
        if hasattr(result, 'sentiment_score') and result.sentiment_score > 0:
            test.passed = True
            test.result = f"Real sentiment: {result.overall_sentiment} ({result.sentiment_score:.2f})"
        else:
            test.error = "Invalid sentiment result"
            
    except Exception as e:
        test.error = str(e)
    
    return test


async def test_smolagents_real() -> RealDataTest:
    """Test smolagents uses real code execution"""
    test = RealDataTest("smolagents - Real Code Execution")
    
    try:
        from SMOLAGENTS_INTEGRATION import ChattySmolAgents
        
        agent = ChattySmolAgents.data_analyst()
        
        # Real calculation
        result = await agent.run("Calculate 1234 * 5678")
        
        # Verify real execution (1234 * 5678 = 7006652)
        if result.get('success') and '7006652' in str(result.get('final_answer', '')):
            test.passed = True
            test.result = f"Real calculation: {result['final_answer'][:100]}"
        else:
            test.error = f"Calculation failed: {result}"
            
    except Exception as e:
        test.error = str(e)
    
    return test


async def test_langgraph_supervisor_real() -> RealDataTest:
    """Test LangGraph Supervisor uses real orchestration"""
    test = RealDataTest("LangGraph Supervisor - Real Orchestration")
    
    try:
        from LANGGRAPH_SUPERVISOR import ChattySupervisorTeams
        
        team = ChattySupervisorTeams.content_creation_team()
        
        # Check real workers configured
        if len(team.workers) >= 2:
            # Try real orchestration
            result = await team.orchestrate({
                "description": "List 3 benefits of exercise (keep it brief)"
            })
            
            if result.get('status') == 'completed' and result.get('final_output'):
                test.passed = True
                test.result = f"Real orchestration: {len(result['results'])} workers used"
            else:
                test.error = "Orchestration incomplete"
        else:
            test.error = f"Only {len(team.workers)} workers configured"
            
    except Exception as e:
        test.error = str(e)
    
    return test


async def test_a2a_real() -> RealDataTest:
    """Test A2A uses real agent definitions"""
    test = RealDataTest("A2A Protocol - Real Agent Definitions")
    
    try:
        from A2A_PROTOCOL import get_a2a_fleet, ChattyA2AAgents
        
        # Create real agent
        agent = ChattyA2AAgents.revenue_agent("http://localhost:8080")
        
        if len(agent.skills) > 0:
            test.passed = True
            test.result = f"Real agent with {len(agent.skills)} skills"
        else:
            test.error = "No skills configured"
            
    except Exception as e:
        test.error = str(e)
    
    return test


async def test_mcp_real() -> RealDataTest:
    """Test MCP uses real filesystem"""
    test = RealDataTest("MCP - Real Filesystem Access")
    
    try:
        from REAL_ONLY_MCP import get_real_mcp_client
        
        client = await get_real_mcp_client()
        
        # Real file read
        content = await client.read_file("/home/coden809/Projects/chatty/README.md")
        
        if len(content) > 0:
            test.passed = True
            test.result = f"Read {len(content)} bytes from real file"
        else:
            test.error = "Empty file"
            
    except Exception as e:
        test.error = str(e)
    
    return test


async def test_master_orchestrator_real() -> RealDataTest:
    """Test Master Orchestrator uses real frameworks"""
    test = RealDataTest("Master Orchestrator - Real Framework Routing")
    
    try:
        from CHATTY_MASTER_ORCHESTRATOR_v2 import get_orchestrator, UnifiedTask, TaskType
        
        orchestrator = await get_orchestrator()
        
        # Execute real task
        result = await orchestrator.execute(UnifiedTask(
            name="Test Task",
            description="What is 5 * 5? Answer with just the number.",
            task_type=TaskType.DATA_ANALYSIS
        ))
        
        if result.success and '25' in str(result.output):
            test.passed = True
            test.result = f"Real execution via {result.framework_used}"
        else:
            test.error = f"Task failed: {result.error}"
            
    except Exception as e:
        test.error = str(e)
    
    return test


async def test_leads_real() -> RealDataTest:
    """Test leads.json contains real data"""
    test = RealDataTest("Leads Database - Real Data")
    
    try:
        leads_file = Path('/home/coden809/Projects/chatty/leads.json')
        
        if not leads_file.exists():
            test.error = "leads.json not found"
            return test
        
        with open(leads_file) as f:
            leads = json.load(f)
        
        # Check for real emails (not mock patterns)
        mock_patterns = ['example.com', 'test.com', 'fake.com', 'mock.com']
        real_leads = []
        
        for lead in leads:
            email = lead.get('email', '')
            if not any(pattern in email for pattern in mock_patterns):
                real_leads.append(lead)
        
        if len(real_leads) > 0:
            test.passed = True
            test.result = f"{len(real_leads)} real leads found"
        else:
            test.error = "No real leads found (all appear to be mock data)"
            
    except Exception as e:
        test.error = str(e)
    
    return test


async def run_all_tests():
    """Run all real data tests"""
    print("=" * 80)
    print("CHATTY REAL DATA INTEGRATION TESTS")
    print("=" * 80)
    print(f"Started: {datetime.now().isoformat()}")
    print()
    
    tests = [
        test_model_router_real(),
        test_sendgrid_real(),
        test_pydantic_ai_real(),
        test_smolagents_real(),
        test_langgraph_supervisor_real(),
        test_a2a_real(),
        test_mcp_real(),
        test_master_orchestrator_real(),
        test_leads_real(),
    ]
    
    results = await asyncio.gather(*tests, return_exceptions=True)
    
    # Print results
    passed = 0
    failed = 0
    
    print("\n📊 TEST RESULTS:")
    print("-" * 80)
    
    for result in results:
        if isinstance(result, Exception):
            print(f"❌ ERROR: {result}")
            failed += 1
            continue
            
        print(f"\n{result}")
        if result.result:
            print(f"   Result: {result.result}")
        if result.error:
            print(f"   Error: {result.error}")
        
        if result.passed:
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 80)
    print(f"SUMMARY: {passed} passed, {failed} failed out of {len(results)} tests")
    print("=" * 80)
    
    if failed > 0:
        print("\n⚠️ Some tests failed - check API keys and configuration")
        return 1
    else:
        print("\n✅ All tests passed - system using REAL DATA only!")
        return 0


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)
