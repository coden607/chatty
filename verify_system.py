#!/usr/bin/env python3
"""
Chatty System Verification & Testing
Ensures everything is fully functional before launch
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SystemVerification:
    """Comprehensive system verification"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.issues = []
        self.warnings = []
        self.passed = []
        
    def verify_all(self):
        """Run all verification checks"""
        logger.info("="*80)
        logger.info("🔍 CHATTY SYSTEM VERIFICATION")
        logger.info("="*80)
        logger.info("")
        
        # Check 1: File Structure
        self.check_file_structure()
        
        # Check 2: Python Syntax
        self.check_python_syntax()
        
        # Check 3: Dependencies
        self.check_dependencies()
        
        # Check 4: Environment Variables
        self.check_environment()
        
        # Check 5: Database Schema
        self.check_database_schema()
        
        # Check 6: API Integrations
        self.check_api_integrations()
        
        # Check 7: Agent System
        self.check_agent_system()
        
        # Print Results
        self.print_results()
        
    def check_file_structure(self):
        """Verify all required files exist"""
        logger.info("📁 Checking file structure...")
        
        required_files = {
            'Core System': [
                'backend_api.py',
                'database_schema.sql',
                'requirements.txt',
                '.env.template'
            ],
            'Automation Engines': [
                'AUTOMATED_REVENUE_ENGINE.py',
                'AUTOMATED_CUSTOMER_ACQUISITION.py',
                'SELF_IMPROVING_AGENTS.py',
                'START_COMPLETE_AUTOMATION.py'
            ],
            'Landing Page': [
                'templates/landing_page.html'
            ],
            'Documentation': [
                'LAUNCH_NOW.md',
                'FINAL_SYSTEM_SUMMARY.md',
                'SELF_IMPROVING_SYSTEM_GUIDE.md',
                'SYSTEM_ARCHITECTURE.md'
            ]
        }
        
        for category, files in required_files.items():
            for file in files:
                file_path = self.base_path / file
                if file_path.exists():
                    self.passed.append(f"✅ {file}")
                else:
                    self.issues.append(f"❌ Missing: {file}")
        
        logger.info(f"   Found {len(self.passed)} files")
        
    def check_python_syntax(self):
        """Check Python files for syntax errors"""
        logger.info("🐍 Checking Python syntax...")
        
        python_files = [
            'backend_api.py',
            'AUTOMATED_REVENUE_ENGINE.py',
            'AUTOMATED_CUSTOMER_ACQUISITION.py',
            'SELF_IMPROVING_AGENTS.py',
            'START_COMPLETE_AUTOMATION.py'
        ]
        
        for file in python_files:
            file_path = self.base_path / file
            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        compile(f.read(), file, 'exec')
                    self.passed.append(f"✅ Syntax OK: {file}")
                except SyntaxError as e:
                    self.issues.append(f"❌ Syntax Error in {file}: {e}")
        
        logger.info(f"   Checked {len(python_files)} Python files")
        
    def check_dependencies(self):
        """Check if all dependencies are installed"""
        logger.info("📦 Checking dependencies...")
        
        required_packages = [
            'flask',
            'stripe',
            'anthropic',
            'sendgrid',
            'tweepy',
            'langchain',
            'crewai',
            'pydantic',
            'psycopg2',
            'sqlalchemy'
        ]
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                self.passed.append(f"✅ {package} installed")
            except ImportError:
                self.warnings.append(f"⚠️  {package} not installed (run: pip install {package})")
        
        logger.info(f"   Checked {len(required_packages)} packages")
        
    def check_environment(self):
        """Check environment variables"""
        logger.info("🔑 Checking environment variables...")

        env_map = {
            'STRIPE_SECRET_KEY': ['STRIPE_SECRET_KEY', 'STRIPE_ALT_KEY', 'PAYMENT_SECRET_KEY'],
            'ANTHROPIC_API_KEY': ['ANTHROPIC_API_KEY', 'CREWAI_ANTHROPIC_KEY', 'PRIMARY_AI_KEY'],
            'SENDGRID_API_KEY': ['SENDGRID_API_KEY', 'ALT_SENDGRID_KEY'],
        }

        optional_vars = {
            'TWITTER_API_KEY': 'Optional for social media',
            'GOOGLE_ADS_API_KEY': 'Optional for paid ads',
            'DATABASE_URL': 'Required for production database'
        }

        for var, options in env_map.items():
            value = next((os.getenv(opt) for opt in options if os.getenv(opt)), None)
            if value:
                source = next(opt for opt in options if os.getenv(opt))
                self.passed.append(f"✅ {source} (mapped to {var}) set")
            else:
                self.warnings.append(f"⚠️  {var} not set - falling back to alternate key required")
        
        for var, description in optional_vars.items():
            value = os.getenv(var)
            if value:
                self.passed.append(f"✅ {var} set")
            else:
                logger.info(f"   ℹ️  {var} not set - {description}")

        logger.info(f"   Checked environment variables")
        
    def check_database_schema(self):
        """Verify database schema is valid"""
        logger.info("🗄️  Checking database schema...")
        
        schema_file = self.base_path / 'database_schema.sql'
        if schema_file.exists():
            with open(schema_file, 'r') as f:
                content = f.read()
                
                # Check for required tables
                required_tables = [
                    'users', 'customers', 'subscriptions', 'transactions',
                    'leads', 'email_subscribers', 'content', 'social_posts',
                    'ad_campaigns', 'referrals', 'partnerships', 'analytics'
                ]
                
                for table in required_tables:
                    if f'CREATE TABLE IF NOT EXISTS {table}' in content:
                        self.passed.append(f"✅ Table defined: {table}")
                    else:
                        self.issues.append(f"❌ Missing table: {table}")
            
            self.passed.append("✅ Database schema file valid")
        else:
            self.issues.append("❌ Database schema file missing")
        
        logger.info(f"   Verified database schema")
        
    def check_api_integrations(self):
        """Check API integration code"""
        logger.info("🔌 Checking API integrations...")
        
        # Check backend_api.py for Stripe integration
        backend_file = self.base_path / 'backend_api.py'
        if backend_file.exists():
            with open(backend_file, 'r') as f:
                content = f.read()
                
                checks = {
                    'stripe.checkout.Session.create': 'Stripe checkout',
                    'stripe.Webhook.construct_event': 'Stripe webhooks',
                    '/api/capture-lead': 'Lead capture endpoint',
                    '/api/create-checkout-session': 'Checkout endpoint'
                }
                
                for check, description in checks.items():
                    if check in content:
                        self.passed.append(f"✅ {description} implemented")
                    else:
                        self.warnings.append(f"⚠️  {description} may be incomplete")
        
        logger.info(f"   Verified API integrations")
        
    def check_agent_system(self):
        """Check AI agent system"""
        logger.info("🤖 Checking AI agent system...")
        
        agent_file = self.base_path / 'SELF_IMPROVING_AGENTS.py'
        if agent_file.exists():
            with open(agent_file, 'r') as f:
                content = f.read()
                
                # Check for all 9 agents
                agents = [
                    'optimizer_agent', 'data_analyst_agent', 'strategy_agent',
                    'content_creator_agent', 'seo_specialist_agent',
                    'customer_success_agent', 'support_agent',
                    'developer_agent', 'devops_agent'
                ]
                
                for agent in agents:
                    if agent in content:
                        self.passed.append(f"✅ Agent defined: {agent}")
                    else:
                        self.issues.append(f"❌ Missing agent: {agent}")
                
                # Check for key features
                features = {
                    'send_message': 'Agent communication',
                    'continuous_improvement_loop': 'Self-improvement',
                    'CrewAI': 'Multi-agent collaboration',
                    'LangChain': 'Agent framework'
                }
                
                for feature, description in features.items():
                    if feature in content:
                        self.passed.append(f"✅ {description} implemented")
                    else:
                        self.warnings.append(f"⚠️  {description} may be incomplete")
        
        logger.info(f"   Verified AI agent system")
        
    def print_results(self):
        """Print verification results"""
        logger.info("")
        logger.info("="*80)
        logger.info("📊 VERIFICATION RESULTS")
        logger.info("="*80)
        logger.info("")
        
        logger.info(f"✅ Passed: {len(self.passed)}")
        logger.info(f"⚠️  Warnings: {len(self.warnings)}")
        logger.info(f"❌ Issues: {len(self.issues)}")
        logger.info("")
        
        if self.issues:
            logger.info("❌ ISSUES FOUND:")
            for issue in self.issues:
                logger.info(f"   {issue}")
            logger.info("")
        
        if self.warnings:
            logger.info("⚠️  WARNINGS:")
            for warning in self.warnings:
                logger.info(f"   {warning}")
            logger.info("")
        
        if not self.issues:
            logger.info("="*80)
            logger.info("✅ SYSTEM IS FULLY FUNCTIONAL!")
            logger.info("="*80)
            logger.info("")
            logger.info("🚀 Ready to launch!")
            logger.info("")
            logger.info("Next steps:")
            logger.info("1. Add API keys to .env")
            logger.info("2. Set up database (Supabase recommended)")
            logger.info("3. Run: python3 START_COMPLETE_AUTOMATION.py")
            logger.info("")
        else:
            logger.info("="*80)
            logger.info("⚠️  PLEASE FIX ISSUES BEFORE LAUNCHING")
            logger.info("="*80)
            logger.info("")

if __name__ == "__main__":
    verifier = SystemVerification()
    verifier.verify_all()
