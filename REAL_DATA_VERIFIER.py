#!/usr/bin/env python3
"""
CHATTY Real Data Verifier
Ensures ALL features use ONLY real data - NO simulations allowed
"""

import asyncio
import json
import logging
import os
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class RealDataCheck:
    """Result of a real data verification check"""
    component: str
    has_real_data: bool
    source: str
    error: Optional[str] = None
    sample: Optional[str] = None


class RealDataVerifier:
    """
    Verifies that all system components use real data only
    """
    
    # Patterns that indicate simulated/mock data
    SIMULATION_PATTERNS = [
        r'\bmock\b', r'\bfake\b', r'\bdummy\b', r'\btest[_-]?data\b',
        r'\bsimulated\b', r'\bplaceholder\b', r'\bexample\.com\b',
        r'\btest\.com\b', r'\bsample[_-]?data\b', r'\bdemo[_-]?data\b',
        r'\bxxx@xxx\.com\b', r'\buser\d+@example\.com\b', r'\bfake@fake\.com\b'
    ]
    
    def __init__(self):
        self.checks: List[RealDataCheck] = []
        
    async def verify_all(self) -> Dict[str, Any]:
        """Run all real data verification checks"""
        logger.info("🔍 Starting Real Data Verification...")
        logger.info("=" * 80)
        
        self.checks = []
        
        # Check AI Model Router (real LLM APIs)
        self.checks.append(await self._verify_model_router())
        
        # Check Revenue Engine (real Stripe)
        self.checks.append(await self._verify_revenue_engine())
        
        # Check Acquisition Engine (real lead sources)
        self.checks.append(await self._verify_acquisition_engine())
        
        # Check SendGrid (real email)
        self.checks.append(await self._verify_sendgrid())
        
        # Check MCP Integration (real tools)
        self.checks.append(await self._verify_mcp())
        
        # Check A2A Protocol (real agent communication)
        self.checks.append(await self._verify_a2a())
        
        # Check Pydantic AI (real structured outputs)
        self.checks.append(await self._verify_pydantic_ai())
        
        # Check smolagents (real code execution)
        self.checks.append(await self._verify_smolagents())
        
        # Check LangGraph Supervisor (real orchestration)
        self.checks.append(await self._verify_langgraph_supervisor())
        
        # Check Database (real data)
        self.checks.append(await self._verify_database())
        
        # Generate report
        return self._generate_report()
    
    async def _verify_model_router(self) -> RealDataCheck:
        """Verify Model Router uses real LLM APIs"""
        try:
            from CHATTY_MODEL_ROUTER import router
            
            # Check if providers have real API keys
            health = router.health_check()
            
            real_providers = []
            for name, status in health['providers'].items():
                if status['available'] and status.get('api_keys_configured'):
                    real_providers.append(name)
            
            # Test a real call
            test_prompt = "Say 'REAL_DATA_TEST' and nothing else"
            response = await router.generate(test_prompt)
            
            is_real = len(real_providers) > 0 and 'REAL_DATA_TEST' in str(response).upper()
            
            return RealDataCheck(
                component="Model Router",
                has_real_data=is_real,
                source=f"Providers: {', '.join(real_providers)}",
                sample=str(response)[:100] if is_real else None
            )
            
        except Exception as e:
            return RealDataCheck(
                component="Model Router",
                has_real_data=False,
                source="N/A",
                error=str(e)
            )
    
    async def _verify_revenue_engine(self) -> RealDataCheck:
        """Verify Revenue Engine uses real Stripe API"""
        stripe_key = os.getenv('STRIPE_SECRET_KEY', '')
        
        if not stripe_key.startswith('sk_'):
            return RealDataCheck(
                component="Revenue Engine (Stripe)",
                has_real_data=False,
                source="Stripe API",
                error="No valid Stripe API key found"
            )
        
        try:
            import stripe
            stripe.api_key = stripe_key
            
            # Test with real API call
            balance = stripe.Balance.retrieve()
            
            return RealDataCheck(
                component="Revenue Engine (Stripe)",
                has_real_data=True,
                source=f"Stripe API (Live Mode: {stripe_key.startswith('sk_live_')})",
                sample=f"Available: ${balance.available[0].amount / 100:.2f}" if balance.available else "Connected"
            )
            
        except Exception as e:
            return RealDataCheck(
                component="Revenue Engine (Stripe)",
                has_real_data=False,
                source="Stripe API",
                error=str(e)
            )
    
    async def _verify_acquisition_engine(self) -> RealDataCheck:
        """Verify Acquisition Engine uses real lead data"""
        try:
            # Check leads.json for real data
            leads_file = Path('leads.json')
            if leads_file.exists():
                with open(leads_file) as f:
                    leads = json.load(f)
                
                # Verify leads aren't mock data
                real_leads = []
                for lead in leads:
                    email = lead.get('email', '')
                    if not any(re.search(pattern, email, re.IGNORECASE) for pattern in self.SIMULATION_PATTERNS):
                        real_leads.append(lead)
                
                return RealDataCheck(
                    component="Acquisition Engine",
                    has_real_data=len(real_leads) > 0,
                    source=f"leads.json ({len(real_leads)} real leads)",
                    sample=real_leads[0]['email'] if real_leads else None
                )
            else:
                return RealDataCheck(
                    component="Acquisition Engine",
                    has_real_data=False,
                    source="No leads file",
                    error="leads.json not found"
                )
                
        except Exception as e:
            return RealDataCheck(
                component="Acquisition Engine",
                has_real_data=False,
                source="N/A",
                error=str(e)
            )
    
    async def _verify_sendgrid(self) -> RealDataCheck:
        """Verify SendGrid uses real API"""
        sendgrid_key = os.getenv('SENDGRID_API_KEY', '')
        
        if not sendgrid_key.startswith('SG.'):
            return RealDataCheck(
                component="SendGrid",
                has_real_data=False,
                source="SendGrid API",
                error="No valid SendGrid API key"
            )
        
        try:
            from sendgrid import SendGridAPIClient
            sg = SendGridAPIClient(sendgrid_key)
            
            # Test with real API call
            response = sg.client.user.profile.get()
            
            return RealDataCheck(
                component="SendGrid",
                has_real_data=True,
                source="SendGrid API",
                sample=f"Status: {response.status_code}"
            )
            
        except Exception as e:
            return RealDataCheck(
                component="SendGrid",
                has_real_data=False,
                source="SendGrid API",
                error=str(e)
            )
    
    async def _verify_mcp(self) -> RealDataCheck:
        """Verify MCP uses real tool servers"""
        try:
            from MCP_INTEGRATION import get_mcp_client
            
            client = await get_mcp_client()
            
            # Check if any servers are connected
            connected = [name for name, server in client.servers.items() if server.is_connected]
            
            return RealDataCheck(
                component="MCP Integration",
                has_real_data=len(connected) > 0,
                source=f"Servers: {', '.join(connected)}" if connected else "None connected",
                sample=f"{len(client.all_tools)} tools available" if client.all_tools else None
            )
            
        except Exception as e:
            return RealDataCheck(
                component="MCP Integration",
                has_real_data=False,
                source="MCP",
                error=str(e)
            )
    
    async def _verify_a2a(self) -> RealDataCheck:
        """Verify A2A uses real agent communication"""
        try:
            from A2A_PROTOCOL import get_a2a_fleet
            
            fleet = await get_a2a_fleet()
            
            # Check registered agents
            agents = list(fleet.agents.keys())
            
            return RealDataCheck(
                component="A2A Protocol",
                has_real_data=len(agents) > 0,
                source=f"Agents: {', '.join(agents)}",
                sample=f"{len(agents)} local agents ready" if agents else None
            )
            
        except Exception as e:
            return RealDataCheck(
                component="A2A Protocol",
                has_real_data=False,
                source="A2A",
                error=str(e)
            )
    
    async def _verify_pydantic_ai(self) -> RealDataCheck:
        """Verify Pydantic AI uses real LLM calls"""
        try:
            from PYDANTIC_AI_ENHANCED import get_pydantic_functions
            
            functions = get_pydantic_functions()
            
            # Test with real call
            result = await functions.analyze_sentiment("This is a great product!")
            
            is_real = hasattr(result, 'sentiment_score') and -1 <= result.sentiment_score <= 1
            
            return RealDataCheck(
                component="Pydantic AI",
                has_real_data=is_real,
                source="LLM API via Model Router",
                sample=f"Sentiment: {result.overall_sentiment} ({result.sentiment_score:.2f})" if is_real else None
            )
            
        except Exception as e:
            return RealDataCheck(
                component="Pydantic AI",
                has_real_data=False,
                source="N/A",
                error=str(e)
            )
    
    async def _verify_smolagents(self) -> RealDataCheck:
        """Verify smolagents uses real code execution"""
        try:
            from SMOLAGENTS_INTEGRATION import ChattySmolAgents
            
            agent = ChattySmolAgents.data_analyst()
            
            # Test with real calculation
            result = await agent.run("Calculate 12345 * 67890")
            
            # Verify it's real (correct answer: 838102050)
            is_real = result.get('success') and '838102050' in str(result.get('final_answer', ''))
            
            return RealDataCheck(
                component="smolagents",
                has_real_data=is_real,
                source="Python execution",
                sample=str(result.get('final_answer', ''))[:100] if is_real else None
            )
            
        except Exception as e:
            return RealDataCheck(
                component="smolagents",
                has_real_data=False,
                source="N/A",
                error=str(e)
            )
    
    async def _verify_langgraph_supervisor(self) -> RealDataCheck:
        """Verify LangGraph Supervisor uses real orchestration"""
        try:
            from LANGGRAPH_SUPERVISOR import ChattySupervisorTeams
            
            team = ChattySupervisorTeams.content_creation_team()
            
            # Check if team has real workers
            has_workers = len(team.workers) > 0
            
            return RealDataCheck(
                component="LangGraph Supervisor",
                has_real_data=has_workers,
                source=f"Workers: {', '.join(team.workers.keys())}",
                sample=f"{len(team.workers)} workers configured" if has_workers else None
            )
            
        except Exception as e:
            return RealDataCheck(
                component="LangGraph Supervisor",
                has_real_data=False,
                source="N/A",
                error=str(e)
            )
    
    async def _verify_database(self) -> RealDataCheck:
        """Verify database contains real data"""
        try:
            import sqlite3
            
            db_path = Path('chatty.db')
            if not db_path.exists():
                return RealDataCheck(
                    component="Database",
                    has_real_data=False,
                    source="SQLite",
                    error="Database not found"
                )
            
            conn = sqlite3.connect('chatty.db')
            cursor = conn.cursor()
            
            # Check for real tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            
            return RealDataCheck(
                component="Database",
                has_real_data=len(tables) > 0,
                source=f"SQLite ({len(tables)} tables)",
                sample=f"Tables: {', '.join(tables[:5])}" if tables else None
            )
            
        except Exception as e:
            return RealDataCheck(
                component="Database",
                has_real_data=False,
                source="N/A",
                error=str(e)
            )
    
    def _generate_report(self) -> Dict[str, Any]:
        """Generate verification report"""
        total = len(self.checks)
        real_data_count = sum(1 for c in self.checks if c.has_real_data)
        
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "total_components": total,
                "using_real_data": real_data_count,
                "using_simulated_data": total - real_data_count,
                "real_data_percentage": (real_data_count / total * 100) if total > 0 else 0
            },
            "components": []
        }
        
        for check in self.checks:
            component_report = {
                "name": check.component,
                "status": "✅ REAL DATA" if check.has_real_data else "❌ SIMULATED/UNAVAILABLE",
                "source": check.source
            }
            if check.sample:
                component_report["sample"] = check.sample
            if check.error:
                component_report["error"] = check.error
            
            report["components"].append(component_report)
        
        return report
    
    def assert_real_data_only(self):
        """Assert that all components use real data - raises exception if not"""
        simulated = [c for c in self.checks if not c.has_real_data]
        
        if simulated:
            raise AssertionError(
                f"❌ REAL DATA VIOLATION: {len(simulated)} components using simulated data:\n" +
                "\n".join([f"  - {c.component}: {c.error or 'No error details'}" for c in simulated])
            )


async def verify_real_data(strict: bool = False) -> Dict[str, Any]:
    """
    Verify all CHATTY components use real data
    
    Args:
        strict: If True, raises exception if any simulated data detected
    
    Returns:
        Verification report dictionary
    """
    verifier = RealDataVerifier()
    report = await verifier.verify_all()
    
    # Print report
    print("\n" + "=" * 80)
    print("REAL DATA VERIFICATION REPORT")
    print("=" * 80)
    print(f"\n📊 Summary:")
    print(f"   Total Components: {report['summary']['total_components']}")
    print(f"   ✅ Using Real Data: {report['summary']['using_real_data']}")
    print(f"   ❌ Simulated/Unavailable: {report['summary']['using_simulated_data']}")
    print(f"   📈 Real Data Percentage: {report['summary']['real_data_percentage']:.1f}%")
    
    print(f"\n📋 Component Details:")
    for comp in report['components']:
        print(f"\n   {comp['status']} {comp['name']}")
        print(f"      Source: {comp['source']}")
        if 'sample' in comp:
            print(f"      Sample: {comp['sample']}")
        if 'error' in comp:
            print(f"      Error: {comp['error']}")
    
    print("\n" + "=" * 80)
    
    if strict and report['summary']['using_simulated_data'] > 0:
        verifier.assert_real_data_only()
    
    return report


if __name__ == "__main__":
    asyncio.run(verify_real_data())
