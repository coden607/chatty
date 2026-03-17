#!/usr/bin/env python3
"""
Integration Script for New CHATTY Systems
Patches existing CHATTY components to use the new enhanced systems
Run this once to upgrade your CHATTY installation
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SystemIntegrator:
    """Integrates new systems into existing CHATTY"""
    
    def __init__(self):
        self.backup_dir = Path("backups") / datetime.now().strftime("%Y%m%d_%H%M%S")
        self.changes_made = []
    
    def backup_file(self, file_path: Path) -> Path:
        """Create a backup of a file before modifying"""
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = self.backup_dir / file_path.name
        
        if file_path.exists():
            import shutil
            shutil.copy2(file_path, backup_path)
            logger.info(f"📦 Backed up: {file_path} -> {backup_path}")
        
        return backup_path
    
    async def integrate_model_router(self):
        """Ensure Model Router is integrated"""
        logger.info("\n🧠 Integrating Model Router...")
        
        try:
            from CHATTY_MODEL_ROUTER import router
            health = router.health_check()
            
            available = sum(
                1 for p in health.get("providers", {}).values()
                if p.get("available")
            )
            
            logger.info(f"✅ Model Router ready with {available} available providers")
            self.changes_made.append("Model Router initialized and ready")
            return True
            
        except Exception as e:
            logger.error(f"❌ Model Router integration failed: {e}")
            return False
    
    async def integrate_unified_intelligence(self):
        """Ensure Unified Intelligence is integrated"""
        logger.info("\n🧩 Integrating Unified Intelligence...")
        
        try:
            from CHATTY_UNIFIED_INTELLIGENCE import unified_intelligence
            status = await unified_intelligence.get_system_status()
            
            subsystems = list(status.get("subsystems", {}).keys())
            logger.info(f"✅ Unified Intelligence ready with subsystems: {subsystems}")
            self.changes_made.append(f"Unified Intelligence active: {', '.join(subsystems)}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Unified Intelligence integration failed: {e}")
            return False
    
    async def integrate_enhanced_layer(self):
        """Ensure Enhanced Integration layer is ready"""
        logger.info("\n🚀 Integrating Enhanced Integration Layer...")
        
        try:
            from CHATTY_ENHANCED_INTEGRATION import enhanced_integration
            health = await enhanced_integration.get_health_status()
            
            logger.info(f"✅ Enhanced Integration ready")
            logger.info(f"   Real Data Mode: {health.get('real_data_mode')}")
            logger.info(f"   Guardrails: {health.get('guardrails_enabled')}")
            
            self.changes_made.append("Enhanced Integration Layer active")
            return True
            
        except Exception as e:
            logger.error(f"❌ Enhanced Integration failed: {e}")
            return False
    
    def create_integration_config(self):
        """Create integration configuration file"""
        config = {
            "version": "3.0",
            "integrated_at": datetime.now().isoformat(),
            "systems": {
                "model_router": {"enabled": True, "auto_failover": True},
                "unified_intelligence": {"enabled": True, "guardrails": True},
                "enhanced_integration": {"enabled": True, "real_data_mode": True},
                "openclaw": {"enabled": True, "chunking": True},
                "archon2": {"enabled": True, "hierarchy": True},
                "agent_zero": {"enabled": True, "fleet_management": True},
                "bmad": {"enabled": True, "behavioral_modeling": True},
                "deepcode": {"enabled": True, "security_scanning": True},
                "dockling": {"enabled": True, "semantic_chunking": True},
            },
            "features": {
                "auto_model_failover": True,
                "hallucination_guardrails": True,
                "real_data_enforcement": True,
                "circuit_breaker": True,
                "confidence_scoring": True,
            },
        }
        
        config_path = Path("generated_content") / "integration_config.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"📝 Integration config saved: {config_path}")
        return config_path
    
    def update_environment_variables(self):
        """Update .env with new configuration options"""
        env_path = Path(".env")
        
        new_vars = """
# ============================================================================
# CHATTY ENHANCED SYSTEM CONFIGURATION
# ============================================================================

# Real Data Enforcement
CHATTY_REAL_DATA_MODE=true

# Guardrails Configuration
CHATTY_GUARDRAILS=true
CHATTY_CONFIDENCE_THRESHOLD=0.7

# Model Router Configuration
CHATTY_MODEL_FAILOVER=true
CHATTY_CIRCUIT_BREAKER_THRESHOLD=5
CHATTY_CIRCUIT_BREAKER_TIMEOUT=300

# Integration Settings
CHATTY_AUTO_INTEGRATE=true
CHATTY_ENHANCED_LOGGING=true
"""
        
        if env_path.exists():
            content = env_path.read_text()
            if "CHATTY_REAL_DATA_MODE" not in content:
                with open(env_path, 'a') as f:
                    f.write(new_vars)
                logger.info("✅ Updated .env with new configuration")
                self.changes_made.append("Environment variables updated")
            else:
                logger.info("ℹ️ Environment variables already up to date")
        else:
            env_path.write_text(new_vars)
            logger.info("✅ Created .env with new configuration")
            self.changes_made.append("Created .env configuration")
    
    def create_launcher_script(self):
        """Create an enhanced launcher script"""
        launcher_content = '''#!/bin/bash
# CHATTY Enhanced Launcher
# Automatically uses the new integrated systems

echo "🚀 CHATTY Enhanced System Launcher"
echo "======================================"

# Check if virtual environment is activated
if [[ -z "${VIRTUAL_ENV}" ]]; then
    echo "🔧 Activating virtual environment..."
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
    else
        echo "❌ Virtual environment not found at .venv/"
        exit 1
    fi
fi

# Use the virtual environment's Python
PYTHON_CMD="${VIRTUAL_ENV}/bin/python3"

echo "🔍 Running system validation..."
${PYTHON_CMD} CHATTY_SYSTEM_VALIDATOR.py
VALIDATION_STATUS=$?

if [ $VALIDATION_STATUS -eq 2 ]; then
    echo "❌ System validation failed critically"
    echo "Please check the validation report in generated_content/system_validation_report.json"
    exit 1
elif [ $VALIDATION_STATUS -eq 1 ]; then
    echo "⚠️ System validation shows warnings"
    echo "Continuing with degraded functionality..."
fi

# Start the system with enhanced integration
echo "🚀 Starting CHATTY with enhanced integration..."
export CHATTY_REAL_DATA_MODE=true
export CHATTY_GUARDRAILS=true
export CHATTY_MODEL_FAILOVER=true

# Run the main automation system
${PYTHON_CMD} START_COMPLETE_AUTOMATION.py "$@"
'''
        
        launcher_path = Path("launch_chatty_enhanced.sh")
        launcher_path.write_text(launcher_content)
        launcher_path.chmod(0o755)
        
        logger.info(f"✅ Created enhanced launcher: {launcher_path}")
        self.changes_made.append("Enhanced launcher script created")
    
    def create_api_integration(self):
        """Create API endpoints documentation for new systems"""
        api_doc = """# CHATTY Enhanced API Endpoints

## Model Router
- `POST /api/v1/generate` - Generate content with auto-failover
- `GET /api/v1/models/health` - Get model health status
- `GET /api/v1/models/providers` - List available providers

## Unified Intelligence
- `POST /api/v1/intelligence/analyze` - Analyze code/content
- `POST /api/v1/intelligence/learn` - Learn from file
- `GET /api/v1/intelligence/status` - Get system status

## Real Data
- `GET /api/v1/data/revenue` - Get real revenue data
- `GET /api/v1/data/transactions` - Get real transactions
- `GET /api/v1/data/leads` - Get real leads data

## Agent Management
- `POST /api/v1/agents/fleet/deploy` - Deploy Agent Zero fleet
- `POST /api/v1/agents/task/submit` - Submit Archon2 task
- `GET /api/v1/agents/status` - Get agent hierarchy status

## System Health
- `GET /api/v1/health` - Overall system health
- `GET /api/v1/health/diagnostics` - Full diagnostics
- `GET /api/v1/health/validation` - Validation report
"""
        
        api_path = Path("ENHANCED_API_ENDPOINTS.md")
        api_path.write_text(api_doc)
        
        logger.info(f"✅ Created API documentation: {api_path}")
        self.changes_made.append("API documentation created")
    
    async def run_integration(self):
        """Run full integration process"""
        logger.info("\n" + "=" * 80)
        logger.info("🔧 CHATTY SYSTEM INTEGRATION")
        logger.info("=" * 80)
        logger.info(f"Started at: {datetime.now().isoformat()}")
        logger.info("=" * 80)
        
        # Run integrations
        results = []
        results.append(("Model Router", await self.integrate_model_router()))
        results.append(("Unified Intelligence", await self.integrate_unified_intelligence()))
        results.append(("Enhanced Integration", await self.integrate_enhanced_layer()))
        
        # Create configuration files
        self.create_integration_config()
        self.update_environment_variables()
        self.create_launcher_script()
        self.create_api_integration()
        
        # Print summary
        logger.info("\n" + "=" * 80)
        logger.info("📊 INTEGRATION SUMMARY")
        logger.info("=" * 80)
        
        for name, success in results:
            status = "✅" if success else "❌"
            logger.info(f"{status} {name}")
        
        logger.info("\nChanges Made:")
        for change in self.changes_made:
            logger.info(f"  • {change}")
        
        logger.info("\n" + "=" * 80)
        logger.info("Next Steps:")
        logger.info("  1. Run validation: ./python3 CHATTY_SYSTEM_VALIDATOR.py")
        logger.info("  2. Test the system: ./launch_chatty_enhanced.sh")
        logger.info("  3. Check API docs: ENHANCED_API_ENDPOINTS.md")
        logger.info("=" * 80)
        
        # Return overall success
        return all(r[1] for r in results)


async def main():
    """Main entry point"""
    integrator = SystemIntegrator()
    success = await integrator.run_integration()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
