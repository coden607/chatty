#!/usr/bin/env python3
"""
Run integration tests for the Chatty Skill-Based Architecture system
"""

import asyncio
import sys
import os

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from SYSTEM_INTEGRATION import ChattySkillIntegration
from SKILL_BASED_ARCHITECTURE import SkillBasedOrchestrator, Task, SkillCategory
from ROBUSTNESS_SYSTEM import RobustnessSystem


async def test_system_health():
    """Test system initialization and health check"""
    print("🧪 Testing System Health...")
    
    try:
        integration = ChattySkillIntegration()
        await integration.initialize()
        
        health = await integration.health_check()
        
        assert health['health']['status'] == 'healthy', "System health status should be healthy"
        assert len(health['agents']) > 0, "System should have at least one agent"
        
        print("✅ System Health Test Passed")
        return health
        
    except Exception as e:
        print(f"❌ System Health Test Failed: {e}")
        raise e
    finally:
        await integration.shutdown()


async def test_task_processing():
    """Test task processing with various task types"""
    print("\n🧪 Testing Task Processing...")
    
    test_tasks = [
        {
            'description': 'Analyze Python code for bugs and security vulnerabilities',
            'type': 'code_analysis'
        },
        {
            'description': 'Optimize business workflow for customer onboarding',
            'type': 'workflow_automation'
        },
        {
            'description': 'Generate investor update report for Q4 2024',
            'type': 'investor'
        },
        {
            'description': 'Create viral marketing campaign for new product launch',
            'type': 'viral'
        }
    ]
    
    results = []
    integration = ChattySkillIntegration()
    
    try:
        await integration.initialize()
        
        for task in test_tasks:
            print(f"🔍 Processing task: {task['description']}")
            result = await integration.process_task(task['description'], task['type'])
            results.append(result)
            
            assert 'processing_result' in result, "Task result should contain processing_result"
            assert 'best_result' in result['processing_result'], "Task processing should produce a best_result"
            assert 'verification_result' in result, "Task result should contain verification_result"
            
            verification = result['verification_result']
            assert 'hallucination_check' in verification, "Verification result should contain hallucination check"
            assert 'consensus_check' in verification, "Verification result should contain consensus check"
            
            print("✅ Task processed successfully")
            
            # Print verification details
            print(f"   Hallucinations detected: {verification['hallucination_check']['total_hallucinations']}")
            print(f"   High severity hallucinations: {verification['hallucination_check']['high_severity_count']}")
            print(f"   Consensus reached: {verification['consensus_check']['consensus_reached']}")
            print(f"   Agreement score: {verification['consensus_check']['agreement_score']:.2f}")
            
            if verification['recommendations']:
                print(f"   Recommendations: {len(verification['recommendations'])}")
        
        return results
        
    except Exception as e:
        print(f"❌ Task Processing Test Failed: {e}")
        raise e
    finally:
        await integration.shutdown()


async def test_skill_system_directly():
    """Test the skill-based system directly"""
    print("\n🧪 Testing Skill-Based System Directly...")
    
    orchestrator = SkillBasedOrchestrator()
    
    test_task = Task(
        id="direct_test_task_1",
        description="Analyze system performance and provide recommendations",
        required_skills=[SkillCategory.ANALYSIS, SkillCategory.RESEARCH],
        difficulty=0.7,
        expected_output_format="markdown",
        validation_criteria=["factually_correct", "complete", "structured"]
    )
    
    result = orchestrator.execute_task_with_ensemble(test_task)
    
    assert 'best_result' in result, "Skill system should return a best result"
    assert 'all_results' in result, "Skill system should return all results"
    
    print(f"✅ Skill System Test Passed:")
    print(f"   Number of results: {len(result['all_results'])}")
    print(f"   Best result score: {result['best_result']['score']:.2f}")
    print(f"   Hallucination count: {result['hallucination_count']}")
    
    return result


async def test_robustness_system():
    """Test the robustness system"""
    print("\n🧪 Testing Robustness System...")
    
    robustness = RobustnessSystem()
    await robustness.initialize()
    
    try:
        status = robustness.get_system_status()
        
        assert status['running'] == True, "Robustness system should be running"
        assert status['health']['status'] == 'healthy', "Health status should be healthy"
        
        # Test hallucination detection
        test_texts = [
            "This is a normal text without any hallucinations.",
            "Everyone says this product is always perfect and never fails!",
            "Studies prove that 95% of people love this product!",
            "According to research, this approach works in 85% of cases."
        ]
        
        print("   Testing hallucination detection:")
        for i, text in enumerate(test_texts):
            result = robustness.hallucination_detector.detect(text)
            print(f"      Text {i+1}: {'✓' if not result.detected else '✗'} Detected")
            if result.detected:
                print(f"        - Severity: {result.severity}")
                print(f"        - Confidence: {result.confidence:.2f}")
                print(f"        - Patterns: {', '.join(result.patterns)}")
        
        print("✅ Robustness System Test Passed")
        return status
        
    except Exception as e:
        print(f"❌ Robustness System Test Failed: {e}")
        raise e
    finally:
        await robustness.shutdown()


async def main():
    """Main test runner"""
    print("🚀 Starting Chatty Skill-Based Architecture Integration Tests")
    print("=" * 60)
    
    all_passed = True
    try:
        await test_system_health()
        await test_skill_system_directly()
        await test_robustness_system()
        await test_task_processing()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        
    except Exception as e:
        all_passed = False
        print(f"\n❌ TESTING FAILED: {e}")
        print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Testing interrupted by user")
        sys.exit(1)