#!/usr/bin/env python3
"""
Test NVIDIA Build + Kimi K2.5 Real Data System
Verifies API connection and executes real tasks
"""

import asyncio
import os
import sys

# Check API key first
if not os.getenv('NVIDIA_API_KEY'):
    print("""
❌ NVIDIA_API_KEY not set!

To use this test:
1. Get your free API key at: https://build.nvidia.com/moonshotai/kimi-k2.5
2. Set environment variable:
   export NVIDIA_API_KEY='nvapi-your-key-here'
3. Run this test again

The system requires REAL API access - no demo mode available.
""")
    sys.exit(1)

from NVIDIA_REAL_AI_ORCHESTRATION import (
    get_orchestrator,
    UnifiedTask,
    TaskType,
    RealDataError
)

async def run_tests():
    """Run comprehensive tests with real API"""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║        🔴 NVIDIA BUILD + KIMI K2.5 - REAL DATA TESTS 🔴                     ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
    
    try:
        # Initialize
        print("🚀 Initializing orchestrator...")
        orchestrator = await get_orchestrator()
        print("✅ Orchestrator ready\n")
        
        # Test API connection
        print("🔄 Testing NVIDIA API connection...")
        status = await orchestrator.test_api_connection()
        
        if status['status'] != 'connected':
            print(f"❌ API connection failed: {status.get('error')}")
            return False
        
        print(f"✅ API Connected")
        print(f"   Model: {status['model']}")
        print(f"   Latency: {status['latency_ms']:.0f}ms\n")
        
        tests_passed = 0
        tests_failed = 0
        
        # Test 1: Code Generation
        print("="*70)
        print("📋 TEST 1: Code Generation (OpenClaw)")
        print("="*70)
        try:
            result = await orchestrator.execute_task(
                UnifiedTask(
                    name="Generate Function",
                    description="Create a Python function to calculate fibonacci numbers iteratively",
                    task_type=TaskType.CODE_GENERATION,
                    context={"language": "python"}
                )
            )
            
            if result.status == "completed":
                print(f"✅ PASSED")
                print(f"   Tokens: {result.tokens_used}")
                print(f"   Time: {result.execution_time:.2f}s")
                if result.output.get('code'):
                    code_preview = result.output['code'][:200].replace('\n', ' ')
                    print(f"   Preview: {code_preview}...")
                tests_passed += 1
            else:
                print(f"❌ FAILED: {result.error_message}")
                tests_failed += 1
        except Exception as e:
            print(f"❌ FAILED: {e}")
            tests_failed += 1
        
        # Test 2: Data Analysis
        print("\n" + "="*70)
        print("📋 TEST 2: Data Analysis (Pydantic)")
        print("="*70)
        try:
            result = await orchestrator.execute_task(
                UnifiedTask(
                    name="Analyze Data",
                    description="Analyze sales trends and provide insights",
                    task_type=TaskType.DATA_ANALYSIS,
                    inputs={
                        "data": [
                            {"month": "Jan", "sales": 10000, "costs": 7000},
                            {"month": "Feb", "sales": 12000, "costs": 7500},
                            {"month": "Mar", "sales": 11500, "costs": 7200},
                        ]
                    }
                )
            )
            
            if result.status == "completed":
                print(f"✅ PASSED")
                print(f"   Tokens: {result.tokens_used}")
                print(f"   Time: {result.execution_time:.2f}s")
                tests_passed += 1
            else:
                print(f"❌ FAILED: {result.error_message}")
                tests_failed += 1
        except Exception as e:
            print(f"❌ FAILED: {e}")
            tests_failed += 1
        
        # Test 3: Research
        print("\n" + "="*70)
        print("📋 TEST 3: Research (LangChain)")
        print("="*70)
        try:
            result = await orchestrator.execute_task(
                UnifiedTask(
                    name="Research",
                    description="What are the key principles of REST API design?",
                    task_type=TaskType.RESEARCH
                )
            )
            
            if result.status == "completed":
                print(f"✅ PASSED")
                print(f"   Tokens: {result.tokens_used}")
                print(f"   Time: {result.execution_time:.2f}s")
                tests_passed += 1
            else:
                print(f"❌ FAILED: {result.error_message}")
                tests_failed += 1
        except Exception as e:
            print(f"❌ FAILED: {e}")
            tests_failed += 1
        
        # Test 4: Content Creation
        print("\n" + "="*70)
        print("📋 TEST 4: Content Creation (CrewAI)")
        print("="*70)
        try:
            result = await orchestrator.execute_task(
                UnifiedTask(
                    name="Create Content",
                    description="Write a tweet about AI automation in business",
                    task_type=TaskType.CONTENT_CREATION,
                    inputs={"platform": "twitter"}
                )
            )
            
            if result.status == "completed":
                print(f"✅ PASSED")
                print(f"   Tokens: {result.tokens_used}")
                print(f"   Time: {result.execution_time:.2f}s")
                if result.output.get('content'):
                    content_preview = result.output['content'][:150].replace('\n', ' ')
                    print(f"   Preview: {content_preview}...")
                tests_passed += 1
            else:
                print(f"❌ FAILED: {result.error_message}")
                tests_failed += 1
        except Exception as e:
            print(f"❌ FAILED: {e}")
            tests_failed += 1
        
        # Test 5: Strategic Planning
        print("\n" + "="*70)
        print("📋 TEST 5: Strategic Planning (Archon2)")
        print("="*70)
        try:
            result = await orchestrator.execute_task(
                UnifiedTask(
                    name="Strategic Plan",
                    description="Develop a strategy to increase user engagement by 25%",
                    task_type=TaskType.STRATEGIC_PLANNING,
                    complexity="strategic",
                    scope="strategic"
                )
            )
            
            if result.status == "completed":
                print(f"✅ PASSED")
                print(f"   Tokens: {result.tokens_used}")
                print(f"   Time: {result.execution_time:.2f}s")
                tests_passed += 1
            else:
                print(f"❌ FAILED: {result.error_message}")
                tests_failed += 1
        except Exception as e:
            print(f"❌ FAILED: {e}")
            tests_failed += 1
        
        # Health Check
        print("\n" + "="*70)
        print("🏥 SYSTEM HEALTH")
        print("="*70)
        health = orchestrator.get_health()
        print(f"Overall: {health.overall_status}")
        print(f"Completed: {health.completed_tasks}")
        print(f"Failed: {health.failed_tasks}")
        print(f"API Requests: {health.api_status.get('total_requests', 0)}")
        print(f"Total Tokens: {health.api_status.get('total_tokens', 0)}")
        
        # Summary
        print("\n" + "="*70)
        print("📊 TEST SUMMARY")
        print("="*70)
        total = tests_passed + tests_failed
        print(f"Passed: {tests_passed}/{total}")
        print(f"Failed: {tests_failed}/{total}")
        
        if tests_failed == 0:
            print("\n🎉 ALL TESTS PASSED - REAL DATA CONFIRMED")
        else:
            print(f"\n⚠️ {tests_failed} test(s) failed")
        
        # Close connections
        await orchestrator.close()
        
        return tests_failed == 0
        
    except RealDataError as e:
        print(f"\n❌ Real Data Error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)
