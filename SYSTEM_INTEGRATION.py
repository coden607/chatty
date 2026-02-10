#!/usr/bin/env python3
"""
System Integration for Skill-Based Architecture
Connects the skill-based system with the existing Chatty ecosystem
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

from SKILL_BASED_ARCHITECTURE import (
    SkillBasedOrchestrator,
    Task,
    SkillCategory
)

from ROBUSTNESS_SYSTEM import RobustnessSystem

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# SYSTEM INTEGRATION
# ============================================================================

class ChattySkillIntegration:
    """Main integration class for Chatty and skill-based architecture"""
    
    def __init__(self):
        self.skill_system = SkillBasedOrchestrator()
        self.robustness_system = RobustnessSystem()
        self.is_initialized = False
    
    async def initialize(self):
        """Initialize all integrated systems"""
        logger.info("🔗 Initializing Chatty Skill Integration...")
        
        # Initialize robustness system
        await self.robustness_system.initialize()
        
        self.is_initialized = True
        logger.info("✅ Chatty Skill Integration initialized")
    
    async def process_task(self, task_description: str, task_type: str = 'general') -> Dict[str, Any]:
        """
        Process a task using the skill-based system with appropriate requirements
        """
        if not self.is_initialized:
            await self.initialize()
        
        # Determine appropriate skills based on task type
        skills = await self._determine_skills_for_task_type(task_type)
        
        # Create task
        task = Task(
            id=f"task_{datetime.now().timestamp()}",
            description=task_description,
            required_skills=skills,
            difficulty=0.7,
            expected_output_format="markdown",
            validation_criteria=["factually_correct", "complete", "structured"]
        )
        
        # Process task with skill-based system
        result = self.skill_system.execute_task_with_ensemble(task)
        
        # Verify results for hallucination and consensus
        verification_result = await self._verify_results(task_description, result)
        
        return {
            'task_description': task_description,
            'task_type': task_type,
            'processing_result': result,
            'verification_result': verification_result
        }
    
    async def _determine_skills_for_task_type(self, task_type: str) -> List[SkillCategory]:
        """
        Determine which skills to use based on task type
        """
        skill_map = {
            'code_analysis': [SkillCategory.ANALYSIS],
            'workflow_automation': [SkillCategory.EXECUTION],
            'learning': [SkillCategory.RESEARCH],
            'web_scraping': [SkillCategory.RESEARCH],
            'revenue': [SkillCategory.ANALYSIS],
            'acquisition': [SkillCategory.COMMUNICATION],
            'investor': [SkillCategory.COMMUNICATION],
            'social': [SkillCategory.COMMUNICATION],
            'viral': [SkillCategory.CREATION],
            'security': [SkillCategory.VALIDATION],
            'performance': [SkillCategory.ANALYSIS],
            'maintenance': [SkillCategory.EXECUTION],
            'general': [SkillCategory.ANALYSIS, SkillCategory.RESEARCH]
        }
        
        return skill_map.get(task_type, [SkillCategory.ANALYSIS, SkillCategory.RESEARCH])
    
    async def _verify_results(self, task_description: str, processing_result: Dict[str, Any]) -> Dict[str, Any]:
        """Verify processing results using robustness system"""
        if 'all_results' in processing_result and processing_result['all_results']:
            # Prepare results for verification
            verification_data = []
            for scored_result in processing_result['all_results']:
                result = scored_result['result']
                verification_data.append({
                    'agent_name': result.agent_id,
                    'result': str(result.result),
                    'confidence': result.confidence
                })
            
            return await self.robustness_system.verify_result(
                task_description,
                verification_data
            )
        
        return {
            'success': False,
            'error': 'No results to verify',
            'hallucination_check': {'total_hallucinations': 0, 'high_severity_count': 0, 'per_agent': []},
            'consensus_check': {'consensus_reached': False, 'agreement_score': 0.0},
            'trust_scores': {},
            'recommendations': ['Task produced no results to verify']
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Get comprehensive system health check"""
        if not self.is_initialized:
            await self.initialize()
        
        robustness_status = self.robustness_system.get_system_status()
        
        # Get agent performance from skill system
        agent_performance = self.skill_system.get_agent_performance()
        
        return {
            'agents': agent_performance,
            'health': robustness_status['health'],
            'hallucination_detector': robustness_status['hallucination_detector_config'],
            'consensus_verifier': robustness_status['consensus_verifier_config'],
            'error_recovery': robustness_status['error_recovery_config']
        }
    
    async def shutdown(self):
        """Shutdown all systems"""
        await self.robustness_system.shutdown()
        self.is_initialized = False
        logger.info("🛑 Chatty Skill Integration shutdown complete")

# ============================================================================
# TASK EXECUTION
# ============================================================================

async def execute_task(task_description: str, task_type: str = 'general') -> Dict[str, Any]:
    """
    Execute a single task using the integrated system
    This is the main entry point for external code
    """
    integration = ChattySkillIntegration()
    
    try:
        await integration.initialize()
        result = await integration.process_task(task_description, task_type)
        return result
    except Exception as e:
        logger.error(f"Task execution failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'task_description': task_description,
            'task_type': task_type
        }
    finally:
        await integration.shutdown()

async def execute_multiple_tasks(tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Execute multiple tasks in parallel
    """
    integration = ChattySkillIntegration()
    await integration.initialize()
    
    results = []
    tasks_to_execute = []
    
    for task in tasks:
        task_coro = integration.process_task(
            task['description'],
            task.get('type', 'general')
        )
        tasks_to_execute.append(task_coro)
    
    try:
        results = await asyncio.gather(*tasks_to_execute, return_exceptions=True)
        
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'success': False,
                    'error': str(result),
                    'task_description': tasks[i]['description'],
                    'task_type': tasks[i].get('type', 'general')
                })
            else:
                processed_results.append(result)
        
        return processed_results
    except Exception as e:
        logger.error(f"Batch task execution failed: {e}")
        return []
    finally:
        await integration.shutdown()

# ============================================================================
# MAIN
# ============================================================================

async def main():
    """Main entry point for testing"""
    logger.info("🚀 Testing Chatty Skill Integration...")
    
    # Create integration instance
    integration = ChattySkillIntegration()
    await integration.initialize()
    
    # Show health status
    logger.info("\n📊 System Health:")
    health = await integration.health_check()
    logger.info(json.dumps(health, indent=2, default=str))
    
    # Test different task types
    logger.info("\n🔍 Testing Task Execution:")
    
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
    
    for task in test_tasks:
        logger.info(f"\n📋 Processing: {task['description']}")
        try:
            result = await integration.process_task(
                task['description'],
                task['type']
            )
            
            logger.info(f"✅ Success: {'best_result' in result['processing_result']}")
            
            if 'verification_result' in result:
                verification = result['verification_result']
                logger.info(f"🔍 Hallucinations detected: {verification['hallucination_check']['total_hallucinations']}")
                logger.info(f"⚖️ Consensus reached: {verification['consensus_check']['consensus_reached']}")
                logger.info(f"🎯 Agreement score: {verification['consensus_check']['agreement_score']:.2f}")
                
                if verification['recommendations']:
                    logger.info(f"💡 Recommendations: {len(verification['recommendations'])}")
        
        except Exception as e:
            logger.error(f"❌ Error: {e}")
    
    await integration.shutdown()
    logger.info("\n✅ All tests completed")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n✅ System shutdown by user")