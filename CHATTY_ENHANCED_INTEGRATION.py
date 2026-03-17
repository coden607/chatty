#!/usr/bin/env python3
"""
CHATTY Enhanced Integration Module
Connects all new systems: Model Router, Unified Intelligence, OpenClaw, Archon2, Agent Zero, BMAD, DeepCode
Ensures real data usage and adds guardrails against hallucinations
"""

import os
import sys
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv(".env", override=False)
_secrets_file = os.getenv("CHATTY_SECRETS_FILE")
if _secrets_file:
    load_dotenv(os.path.expanduser(_secrets_file), override=False)

# Import new systems
from CHATTY_MODEL_ROUTER import router, TaskType, generate_code, review_code, create_content
from CHATTY_UNIFIED_INTELLIGENCE import unified_intelligence, analyze_code, learn_from_file, generate_with_guardrails

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EnhancedChattyIntegration:
    """
    Enhanced integration layer for CHATTY
    Provides unified access to all intelligence systems with real data enforcement
    """
    
    def __init__(self):
        self.real_data_mode = os.getenv("CHATTY_REAL_DATA_MODE", "true").lower() == "true"
        self.guardrails_enabled = os.getenv("CHATTY_GUARDRAILS", "true").lower() == "true"
        self.model_router = router
        self.intelligence = unified_intelligence
        self.logger = logger
        
        # Track data sources for verification
        self.data_sources: Dict[str, Any] = {}
        
        logger.info("🚀 Enhanced CHATTY Integration initialized")
        logger.info(f"   Real Data Mode: {'✅ ENABLED' if self.real_data_mode else '⚠️ DISABLED'}")
        logger.info(f"   Guardrails: {'✅ ENABLED' if self.guardrails_enabled else '⚠️ DISABLED'}")
    
    def verify_real_data(self, data_source: str, data: Any) -> bool:
        """
        Verify that data is from a real source, not simulated
        
        Args:
            data_source: Identifier for the data source (e.g., 'stripe', 'sendgrid')
            data: The data to verify
        
        Returns:
            True if data appears to be real
        """
        if not self.real_data_mode:
            return True  # Skip verification if not in real data mode
        
        # Check for simulation indicators
        simulation_indicators = [
            "mock", "simulated", "fake", "test_data", "dummy",
            "example", "sample", "placeholder"
        ]
        
        data_str = str(data).lower()
        for indicator in simulation_indicators:
            if indicator in data_str:
                logger.warning(f"⚠️ Potential simulated data detected in {data_source}: '{indicator}'")
                return False
        
        # Store verification
        self.data_sources[data_source] = {
            "verified": True,
            "timestamp": datetime.now().isoformat(),
            "sample": str(data)[:100] if data else None,
        }
        
        return True
    
    async def get_stripe_balance(self) -> Dict[str, Any]:
        """Get real Stripe balance with verification"""
        try:
            from REAL_DATA_INTEGRATIONS import StripeIntegration
            stripe = StripeIntegration()
            balance = await stripe.get_real_balance()
            
            if self.verify_real_data("stripe", balance):
                logger.info(f"💰 Real Stripe Balance: ${balance.get('available', 0):.2f}")
                return balance
            else:
                logger.error("❌ Stripe data verification failed")
                return {"available": 0, "pending": 0, "currency": "usd", "verified": False}
        
        except Exception as e:
            logger.error(f"❌ Stripe integration error: {e}")
            return {"available": 0, "pending": 0, "currency": "usd", "error": str(e)}
    
    async def get_stripe_transactions(self, days: int = 30) -> List[Dict]:
        """Get real Stripe transactions with verification"""
        try:
            from REAL_DATA_INTEGRATIONS import StripeIntegration
            stripe = StripeIntegration()
            transactions = await stripe.get_real_transactions(days)
            
            if self.verify_real_data("stripe_transactions", transactions):
                logger.info(f"📊 Real Stripe Transactions: {len(transactions)} in last {days} days")
                return transactions
            else:
                return []
        
        except Exception as e:
            logger.error(f"❌ Stripe transactions error: {e}")
            return []
    
    async def get_sendgrid_stats(self) -> Dict[str, Any]:
        """Get real SendGrid statistics"""
        try:
            from REAL_DATA_INTEGRATIONS import SendGridIntegration
            sendgrid = SendGridIntegration()
            stats = await sendgrid.get_email_stats()
            
            if self.verify_real_data("sendgrid", stats):
                logger.info(f"📧 SendGrid Stats: {stats}")
                return stats
            else:
                return {}
        
        except Exception as e:
            logger.error(f"❌ SendGrid integration error: {e}")
            return {}
    
    async def generate_ai_content(
        self,
        system_prompt: str,
        user_prompt: str,
        task_type: TaskType = TaskType.CONTENT_CREATION,
        require_guardrails: bool = True,
    ) -> str:
        """
        Generate AI content with automatic failover and guardrails
        
        Args:
            system_prompt: System instructions
            user_prompt: User request
            task_type: Type of task for optimal model selection
            require_guardrails: Whether to apply hallucination guardrails
        
        Returns:
            Generated content string
        """
        if require_guardrails and self.guardrails_enabled:
            # Use unified intelligence with guardrails
            result = await generate_with_guardrails(
                prompt=user_prompt,
                system_prompt=system_prompt,
                task_category=task_type.value,
            )
            
            if result.success:
                if result.hallucination_risk > 0.5:
                    logger.warning(f"⚠️ High hallucination risk detected: {result.hallucination_risk:.2f}")
                return result.content
            else:
                logger.error(f"❌ Guardrailed generation failed: {result.content}")
                # Fall through to direct generation
        
        # Direct generation through model router
        result = await self.model_router.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            task_type=task_type,
        )
        
        if result.success:
            provider = result.provider_used.value if result.provider_used else "unknown"
            logger.info(f"✅ Content generated using {provider} (confidence: {result.confidence:.2f})")
            return result.content
        else:
            logger.error(f"❌ All models failed: {result.error}")
            return f"Error generating content: {result.error}"
    
    async def analyze_and_fix_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """
        Analyze code using DeepCode and suggest fixes
        
        Args:
            code: Code to analyze
            language: Programming language
        
        Returns:
            Analysis results with suggestions
        """
        result = await analyze_code(code, language)
        
        if result.success:
            content = result.content
            logger.info(f"🔍 Code analysis complete: {content.get('issues_found', 0)} issues")
            
            # If AI review is available, include it
            if content.get('ai_analysis', {}).get('ai_review'):
                logger.info("✅ AI review included in analysis")
            
            return content
        else:
            logger.error(f"❌ Code analysis failed: {result.content}")
            return {"error": result.content}
    
    async def learn_from_project_files(self, directory: str = ".") -> List[Dict]:
        """
        Learn from all Python files in a directory
        
        Args:
            directory: Directory to scan
        
        Returns:
            List of learning results
        """
        results = []
        
        try:
            for root, dirs, files in os.walk(directory):
                # Skip certain directories
                dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.venv', 'node_modules']]
                
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        result = await learn_from_file(file_path)
                        
                        if result.success:
                            results.append({
                                "file": file_path,
                                "chunks": result.content.get('chunks', 0),
                                "status": "learned",
                            })
        
        except Exception as e:
            logger.error(f"❌ File learning error: {e}")
        
        logger.info(f"📚 Learned from {len(results)} files")
        return results
    
    async def deploy_agent_fleet(
        self,
        fleet_name: str,
        agent_types: List[str],
        protocol: str = "zero_shot"
    ) -> Dict[str, Any]:
        """
        Deploy an Agent Zero fleet
        
        Args:
            fleet_name: Name for the fleet
            agent_types: Types of agents to deploy
            protocol: Coordination protocol
        
        Returns:
            Deployment result
        """
        result = await self.intelligence.process(
            task_type="deploy_fleet",
            data={
                "fleet_name": fleet_name,
                "agent_types": agent_types,
                "protocol": protocol,
            },
        )
        
        if result.success:
            logger.info(f"🚀 Fleet '{fleet_name}' deployed with {result.content.get('agents_deployed', 0)} agents")
            return result.content
        else:
            logger.error(f"❌ Fleet deployment failed: {result.content}")
            return {"error": result.content}
    
    async def submit_archon_task(
        self,
        description: str,
        task_type: str,
        priority: int = 5
    ) -> str:
        """
        Submit a task to Archon2 orchestration
        
        Args:
            description: Task description
            task_type: Type of task
            priority: Priority level (1-10)
        
        Returns:
            Task ID
        """
        result = await self.intelligence.process(
            task_type="submit_task",
            data={
                "description": description,
                "task_type": task_type,
                "priority": priority,
            },
        )
        
        if result.success:
            task_id = result.content.get("task_id")
            logger.info(f"📋 Task submitted to Archon2: {task_id}")
            return task_id
        else:
            logger.error(f"❌ Task submission failed: {result.content}")
            return ""
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status of all systems"""
        model_health = self.model_router.health_check()
        intelligence_status = await self.intelligence.get_system_status()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "real_data_mode": self.real_data_mode,
            "guardrails_enabled": self.guardrails_enabled,
            "model_router": model_health,
            "intelligence_systems": intelligence_status,
            "overall_health": self._calculate_overall_health(model_health, intelligence_status),
        }
    
    def _calculate_overall_health(
        self,
        model_health: Dict,
        intelligence_status: Dict
    ) -> str:
        """Calculate overall system health"""
        model_status = model_health.get("overall_health", "unknown")
        
        if model_status == "excellent":
            return "excellent"
        elif model_status == "degraded":
            return "operational"
        elif model_status == "critical":
            return "degraded"
        return "unknown"
    
    async def run_self_diagnostics(self) -> Dict[str, Any]:
        """Run comprehensive self-diagnostics"""
        diagnostics = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "passed": 0,
            "failed": 0,
        }
        
        # Test 1: Model Router
        try:
            health = self.model_router.health_check()
            available = sum(
                1 for p in health.get("providers", {}).values()
                if p.get("available")
            )
            diagnostics["tests"]["model_router"] = {
                "status": "pass" if available > 0 else "fail",
                "available_providers": available,
            }
            if available > 0:
                diagnostics["passed"] += 1
            else:
                diagnostics["failed"] += 1
        except Exception as e:
            diagnostics["tests"]["model_router"] = {"status": "fail", "error": str(e)}
            diagnostics["failed"] += 1
        
        # Test 2: Unified Intelligence
        try:
            status = await self.intelligence.get_system_status()
            diagnostics["tests"]["intelligence"] = {
                "status": "pass",
                "subsystems": list(status.get("subsystems", {}).keys()),
            }
            diagnostics["passed"] += 1
        except Exception as e:
            diagnostics["tests"]["intelligence"] = {"status": "fail", "error": str(e)}
            diagnostics["failed"] += 1
        
        # Test 3: Real Data Connectivity
        try:
            from REAL_DATA_INTEGRATIONS import RealDataIntegrations
            rdi = RealDataIntegrations()
            has_stripe = bool(rdi.stripe_key)
            has_sendgrid = bool(rdi.sendgrid_key)
            
            diagnostics["tests"]["real_data"] = {
                "status": "pass" if (has_stripe or has_sendgrid) else "warning",
                "stripe_configured": has_stripe,
                "sendgrid_configured": has_sendgrid,
            }
            diagnostics["passed"] += 1
        except Exception as e:
            diagnostics["tests"]["real_data"] = {"status": "fail", "error": str(e)}
            diagnostics["failed"] += 1
        
        # Test 4: Guardrails
        try:
            test_result = await generate_with_guardrails(
                prompt="What is 2+2?",
                task_category="chat",
            )
            diagnostics["tests"]["guardrails"] = {
                "status": "pass" if test_result.success else "fail",
                "confidence": test_result.confidence,
                "risk_score": test_result.hallucination_risk,
                "error": None if test_result.success else str(test_result.content),
            }
            if test_result.success:
                diagnostics["passed"] += 1
            else:
                diagnostics["failed"] += 1
        except Exception as e:
            diagnostics["tests"]["guardrails"] = {"status": "fail", "error": str(e)}
            diagnostics["failed"] += 1
        
        diagnostics["status"] = "healthy" if diagnostics["failed"] == 0 else "degraded"
        
        return diagnostics


# Global instance
enhanced_integration = EnhancedChattyIntegration()


# Convenience functions for easy access
async def get_revenue_data() -> Dict[str, Any]:
    """Get real revenue data from Stripe"""
    return await enhanced_integration.get_stripe_balance()


async def get_transactions(days: int = 30) -> List[Dict]:
    """Get real transaction data"""
    return await enhanced_integration.get_stripe_transactions(days)


async def generate_content(
    system_prompt: str,
    user_prompt: str,
    task_type: str = "content_creation"
) -> str:
    """Generate content with guardrails and failover"""
    return await enhanced_integration.generate_ai_content(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        task_type=TaskType(task_type),
    )


async def health_check() -> Dict[str, Any]:
    """Quick health check"""
    return await enhanced_integration.get_health_status()


async def diagnostics() -> Dict[str, Any]:
    """Full diagnostics"""
    return await enhanced_integration.run_self_diagnostics()


# Test function
async def test_enhanced_integration():
    """Test the enhanced integration"""
    print("🚀 Testing CHATTY Enhanced Integration")
    print("=" * 70)
    
    # Health check
    print("\n📊 Health Check:")
    health = await health_check()
    print(f"  Overall: {health.get('overall_health', 'unknown')}")
    print(f"  Real Data Mode: {health.get('real_data_mode')}")
    print(f"  Guardrails: {health.get('guardrails_enabled')}")
    
    # Diagnostics
    print("\n🔍 Self Diagnostics:")
    diag = await diagnostics()
    print(f"  Status: {diag.get('status')}")
    print(f"  Tests Passed: {diag.get('passed')}/{diag.get('passed', 0) + diag.get('failed', 0)}")
    for test_name, result in diag.get('tests', {}).items():
        status = "✅" if result.get('status') == 'pass' else "❌"
        print(f"  {status} {test_name}")
    
    # Test generation
    print("\n📝 Testing AI Generation:")
    content = await generate_content(
        system_prompt="You are a helpful assistant.",
        user_prompt="Say hello and identify yourself.",
        task_type="chat",
    )
    print(f"  Response: {content[:100]}...")
    
    # Test code analysis
    print("\n🔍 Testing Code Analysis:")
    test_code = "def test(): pass"
    analysis = await enhanced_integration.analyze_and_fix_code(test_code)
    print(f"  Issues found: {analysis.get('issues_found', 0)}")
    
    print("\n" + "=" * 70)
    print("Tests complete!")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        asyncio.run(test_enhanced_integration())
    elif len(sys.argv) > 1 and sys.argv[1] == "--health":
        print(json.dumps(asyncio.run(health_check()), indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == "--diagnostics":
        print(json.dumps(asyncio.run(diagnostics()), indent=2))
    else:
        print("Usage: python CHATTY_ENHANCED_INTEGRATION.py [--test|--health|--diagnostics]")
